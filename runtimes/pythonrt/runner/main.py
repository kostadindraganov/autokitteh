import builtins
import json
import os
import pickle
import sys
from base64 import b64decode
from concurrent.futures import Future, ThreadPoolExecutor
from io import StringIO
from multiprocessing import cpu_count
from pathlib import Path
from threading import Lock, Thread
from time import sleep
from traceback import TracebackException, format_exception

import grpc
import loader
import log
import pb.autokitteh.user_code.v1.handler_svc_pb2 as pb_handler
import pb.autokitteh.user_code.v1.handler_svc_pb2_grpc as handler_rpc
import pb.autokitteh.user_code.v1.runner_svc_pb2 as pb_runner
import pb.autokitteh.user_code.v1.runner_svc_pb2_grpc as runner_rpc
import pb.autokitteh.user_code.v1.user_code_pb2 as pb_user_code
import pb.autokitteh.values.v1.values_pb2 as pb_values
import values
from call import AKCall, full_func_name
from grpc_reflection.v1alpha import reflection
from syscalls import SysCalls

from autokitteh import AttrDict, connections

SERVER_GRACE_TIMEOUT = 3  # seconds


class ActivityError(Exception):
    pass


def parse_entry_point(entry_point):
    """
    >>> parse_entry_point('review.py:on_github_pull_request')
    ('review', 'on_github_pull_request')
    """
    if ":" not in entry_point:
        raise ValueError(f"{entry_point!r} - missing :")

    file_name, func_name = entry_point.split(":", 1)
    if not file_name.endswith(".py"):
        raise ValueError(f"{entry_point!r} - not a Python file")

    return file_name[:-3], func_name


def exc_traceback(err):
    """Format traceback to JSONable list."""
    te = TracebackException.from_exception(err)
    return [
        pb_user_code.Frame(
            filename=frame.filename,
            lineno=frame.lineno,
            code=frame.line,
            name=frame.name,
        )
        for frame in te.stack
    ]


pickle_help = """
=======================================================================================================
The below error means you need to use the @autokitteh.activity decorator.
See https://docs.autokitteh.com/develop/python/#function-arguments-and-return-values-must-be-pickleable
for more details.
=======================================================================================================
"""


def display_err(fn, err):
    func_name = full_func_name(fn)
    log.exception("calling %s: %s", func_name, err)

    if "pickle" in str(err):
        print(pickle_help, file=sys.stderr)

    exc = "".join(format_exception(err))

    # Print the error to stderr so it'll show in session logs
    print(f"error: {err}\n\n{exc}", file=sys.stderr)


# Go passes HTTP event.data.body.bytes as base64 encode string
def fix_http_body(event):
    data = event.get("data")
    if not isinstance(data, dict):
        return

    body = data.get("body")
    if not isinstance(body, dict):
        return

    payload = body.get("bytes")
    if isinstance(payload, str):
        try:
            body["bytes"] = b64decode(payload)
        except ValueError:
            pass


def killIfStartWasntCalled(runner):
    if not runner.did_start:
        print("Start was not called, killing self")
        os._exit(1)


class Runner(runner_rpc.RunnerService):
    def __init__(self, id, worker, code_dir, server):
        self.id = id
        self.worker: handler_rpc.HandlerServiceStub = worker
        self.code_dir = code_dir
        self.server: grpc.Server = server

        self.executor = ThreadPoolExecutor()

        self.lock = Lock()
        self.calls = {}  # id -> (fn, args, kw)
        self.replies = {}  # id -> future
        self._next_id = 0
        self._orig_print = print
        self._start_called = False

    def Exports(self, request: pb_runner.ExportsRequest, context: grpc.ServicerContext):
        if request.file_name == "":
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "missing file name",
            )

        try:
            exports = list(loader.exports(self.code_dir, request.file_name))
        except OSError as err:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(err))

        return pb_runner.ExportsResponse(exports=exports)

    def should_keep_running(self, initial_delay=10, period=10):
        sleep(initial_delay)
        if not self._start_called:
            log.error("Start not called after %dsec", initial_delay)
            self.server.stop(SERVER_GRACE_TIMEOUT)
            return

        # Check that we are still active
        while True:
            try:
                req = pb_handler.IsActiveRunnerRequest(runner_id=self.id)
                res = self.worker.IsActiveRunner(req)
                if res.error:
                    break
            except grpc.RpcError:
                break
            sleep(period)

        log.error("could not verify if should keep running, killing self")
        self.server.stop(SERVER_GRACE_TIMEOUT)

    def Start(self, request: pb_runner.StartRequest, context: grpc.ServicerContext):
        if self._start_called:
            log.error("already called start before")
            return pb_runner.StartResponse(error="start already called")

        self._start_called = True
        log.info("start request: %r", request)

        self.syscalls = SysCalls(self.id, self.worker)
        mod_name, fn_name = parse_entry_point(request.entry_point)

        # Monkey patch some functions, should come before we import user code.
        builtins.print = self.ak_print
        connections.encode_jwt = self.syscalls.ak_encode_jwt
        connections.refresh_oauth = self.syscalls.ak_refresh_oauth

        ak_call = AKCall(self, self.code_dir)
        mod = loader.load_code(self.code_dir, ak_call, mod_name)
        ak_call.set_module(mod)

        fn = getattr(mod, fn_name, None)
        if not callable(fn):
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"function {fn_name!r} not found",
            )

        event = json.loads(request.event.data)

        fix_http_body(event)
        event = AttrDict(event)
        self.executor.submit(self.on_event, fn, event)

        return pb_runner.StartResponse()

    def Execute(self, request: pb_runner.ExecuteRequest, context: grpc.ServicerContext):
        call_id = request.data.decode()
        with self.lock:
            call_info = self.calls.pop(call_id, None)

        if call_info is None:
            error = f"call_id {call_id!r} not found"
            with self.lock:
                fut = self.replies.pop(call_id, None)
                if fut:
                    fut.set_exception(ActivityError(error))

            context.abort(grpc.StatusCode.INVALID_ARGUMENT, error)

        fn, args, kw = call_info
        log.info("calling %s, args=%r, kw=%r", full_func_name(fn), args, kw)
        result = err = None
        try:
            result = fn(*args, **kw)
        except Exception as e:
            # NOPE: display_err(fn, e)
            # This emits wierd additional data that the users will not want
            # to see and confuse them.
            err = e

        resp = pb_runner.ExecuteResponse(
            result=pb_values.Value(
                custom=pb_values.Custom(
                    data=pickle.dumps((call_id, result), protocol=0),
                    value=safe_wrap(result),
                ),
            )
        )

        if err:
            resp.error = str(err)
            tb = exc_traceback(err)
            resp.traceback.extend(tb)

        return resp

    def ActivityReply(
        self, request: pb_runner.ActivityReplyRequest, context: grpc.ServicerContext
    ):
        resp = request.result.custom
        try:
            call_id, result = pickle.loads(resp.data)
        except Exception as err:
            log.exception(f"can't decode data: pickle: {err}")
            context.abort(grpc.StatusCode.INTERNAL, f"result pickle: {err}")

        with self.lock:
            fut = self.replies.pop(call_id, None)

        if fut is None:
            log.error("call_id %r not found", call_id)
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, "call_id {call_id!r} not found"
            )

        if request.error:
            fut.set_exception(ActivityError(request.error))
            context.abort(
                grpc.StatusCode.ABORTED,
                f"call_id {call_id!r}: activity error: {request.error}",
            )

        fut.set_result(result)
        return pb_runner.ActivityReplyResponse()

    def Health(
        self,
        request: pb_runner.RunnerHealthRequest,
        context: grpc.ServicerContext,
    ):
        return pb_runner.RunnerHealthResponse()

    def call_in_activity(self, fn, args, kw):
        fut = self.start_activity(fn, args, kw)
        return fut.result()

    def start_activity(self, fn, args, kw) -> Future:
        fn_name = full_func_name(fn)
        log.info("calling %s, args=%r, kw=%r", fn_name, args, kw)
        call_id = self.next_call_id()
        log.info("call_id %r", call_id)
        with self.lock:
            self.replies[call_id] = fut = Future()
            self.calls[call_id] = (fn, args, kw)

        req = pb_handler.ActivityRequest(
            runner_id=self.id,
            data=call_id.encode(),
            call_info=pb_handler.CallInfo(
                function=fn.__name__,  # AK rejects __qualname__ such as "json.loads"
                args=[safe_wrap(a) for a in args],
                kwargs={k: safe_wrap(v) for k, v in kw.items()},
            ),
        )
        log.info("activity: sending %r", req)
        resp = self.worker.Activity(req)
        if resp.error:
            raise ActivityError(resp.error)
        log.info("activity request ended")
        return fut

    def on_event(self, fn, event):
        log.info("on_event: start: %r", event)

        # TODO: This is similar to Execute, merge?
        err = result = None
        try:
            result = fn(event)
        except Exception as e:
            display_err(fn, e)
            err = e

        log.info("on_event: end: result=%r, err=%r", result, err)
        req = pb_handler.DoneRequest(
            runner_id=self.id,
        )

        log.info("on_event: end: result=%r, err=%r", result, err)
        if err:
            req.error = str(err)
            tb = exc_traceback(err)
            req.traceback.extend(tb)
        else:
            req.result.custom.data = pickle.dumps(result, protocol=0)
            req.result.custom.value.CopyFrom(safe_wrap(result))

        log.info("DONE: sending")
        resp = self.worker.Done(req)
        log.info("DONE: sent")
        if resp.Error:
            log.error("on_event: done error: %r", resp.error)

    def syscall(self, fn, args, kw):
        return self.syscalls.call(fn, args, kw)

    def next_call_id(self) -> str:
        with self.lock:
            self._next_id += 1
            return f"call_id_{self._next_id:03d}"

    def ak_print(self, *objects, sep=" ", end="\n", file=None, flush=False):
        io = StringIO()
        self._orig_print(*objects, sep=sep, end=end, flush=flush, file=io)
        text = io.getvalue()
        self._orig_print(text, file=file)  # Print also to original destination

        req = pb_handler.PrintRequest(
            runner_id=self.id,
            message=text,
        )

        try:
            self.worker.Print(req)
        except grpc.RpcError as err:
            if err.code() == grpc.StatusCode.UNAVAILABLE or grpc.StatusCode.CANCELLED:
                log.error("grpc canclled or unavailable, killing self")
                self.server.stop(SERVER_GRACE_TIMEOUT)
            log.error("print: %s", err)


def safe_wrap(v):
    try:
        return values.wrap(v)
    except TypeError:
        return pb_values.Value(string=pb_values.String(v=repr(v)))


def is_valid_port(port):
    return port >= 0 and port <= 65535


def validate_args(args):
    if not is_valid_port(args.port):
        raise ValueError(f"invalid port: {args.port!r}")

    if ":" not in args.worker_address:
        raise ValueError("worker address must be in the form host:port")
    host, port = args.worker_address.split(":")
    if host == "":
        raise ValueError(f"empty host in {args.worker_address!r}")

    port = int(port)
    if not is_valid_port(port):
        raise ValueError(f"invalid port in {args.worker_address!r}")

    if args.runner_id == "":
        raise ValueError("runner ID cannot be empty")


class LoggingInterceptor(grpc.ServerInterceptor):
    runner_id = None

    def intercept_service(self, continuation, handler_call_details):
        log.info("runner_id %s, call %s", self.runner_id, handler_call_details.method)
        return continuation(handler_call_details)

    def __init__(self, runner_id) -> None:
        self.runner_id = runner_id
        super().__init__()


def dir_type(value):
    path = Path(value)
    if not path.is_dir():
        raise ValueError(f"{value!r} is not a directory")

    return path


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Python runner")
    parser.add_argument(
        "--worker-address", help="Worker address (host:port)", default="localhost:9292"
    )
    parser.add_argument(
        "--skip-check-worker",
        help="do not check connection to worker on startup",
        action="store_true",
    )
    parser.add_argument("--port", help="port to listen on", default=9293, type=int)
    parser.add_argument("--runner-id", help="runner ID", default="runner-1")
    parser.add_argument(
        "--code-dir",
        help="directory of user code",
        default="/workflow",
        type=dir_type,
    )
    args = parser.parse_args()

    try:
        validate_args(args)
    except ValueError as err:
        raise SystemExit(f"error: {err}")

    # Support importing local files
    # sys.path.append(str(args.code_dir))

    chan = grpc.insecure_channel(args.worker_address)
    worker = handler_rpc.HandlerServiceStub(chan)
    if not args.skip_check_worker:
        req = pb_handler.HandlerHealthRequest()
        try:
            resp = worker.Health(req)
        except grpc.RpcError as err:
            raise SystemExit(f"error: worker not available - {err}")

    log.info("connected to worker at %r", args.worker_address)

    server = grpc.server(
        thread_pool=ThreadPoolExecutor(max_workers=cpu_count() * 8),
        interceptors=[LoggingInterceptor(args.runner_id)],
    )
    runner = Runner(args.runner_id, worker, args.code_dir, server)
    # rpc.add_RunnerServicer_to_server(runner, server)
    runner_rpc.add_RunnerServiceServicer_to_server(runner, server)
    services = (
        # pb.DESCRIPTOR.services_by_name["Runner"].full_name,
        pb_runner.DESCRIPTOR.services_by_name["RunnerService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(services, server)

    server.add_insecure_port(f"[::]:{args.port}")
    server.start()
    log.info("server running on port %d", args.port)

    if not args.skip_check_worker:
        Thread(target=runner.should_keep_running, daemon=True).start()
    log.info("setup should keep running thread")

    server.wait_for_termination()
