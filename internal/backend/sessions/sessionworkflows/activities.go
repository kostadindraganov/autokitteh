package sessionworkflows

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"go.temporal.io/api/serviceerror"
	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
	"go.uber.org/zap"

	"go.autokitteh.dev/autokitteh/internal/backend/db"
	"go.autokitteh.dev/autokitteh/internal/backend/temporalclient"
	"go.autokitteh.dev/autokitteh/internal/backend/types"
	"go.autokitteh.dev/autokitteh/sdk/sdkerrors"
	"go.autokitteh.dev/autokitteh/sdk/sdkservices"
	"go.autokitteh.dev/autokitteh/sdk/sdktypes"
)

const (
	updateSessionStateActivityName          = "update_session_state"
	terminateWorkflowActivityName           = "terminate_workflow"
	saveSignalActivityName                  = "save_signal"
	getLastEventSequenceActivityName        = "get_last_event_sequence"
	getSessionStopReasonActivityName        = "get_session_stop_reason"
	getSignalEventActivityName              = "get_signal_event"
	removeSignalActivityName                = "remove_signal"
	addSessionPrintActivityName             = "add_session_print"
	deactivateDrainedDeploymentActivityName = "deactivate_drained_deployment"
)

func (ws *workflows) registerActivities() {
	ws.worker.RegisterActivityWithOptions(
		ws.updateSessionStateActivity,
		activity.RegisterOptions{Name: updateSessionStateActivityName},
	)

	ws.worker.RegisterActivityWithOptions(
		ws.terminateWorkflowActivity,
		activity.RegisterOptions{Name: terminateWorkflowActivityName},
	)

	ws.worker.RegisterActivityWithOptions(
		ws.saveSignalActivity,
		activity.RegisterOptions{Name: saveSignalActivityName},
	)

	ws.worker.RegisterActivityWithOptions(
		ws.getLatestEventSequenceActivity,
		activity.RegisterOptions{Name: getLastEventSequenceActivityName},
	)

	ws.worker.RegisterActivityWithOptions(
		ws.getSessionStopReasonActivity,
		activity.RegisterOptions{Name: getSessionStopReasonActivityName},
	)

	ws.worker.RegisterActivityWithOptions(
		ws.getSignalEventActivity,
		activity.RegisterOptions{Name: getSignalEventActivityName},
	)

	ws.worker.RegisterActivityWithOptions(
		ws.removeSignalActivity,
		activity.RegisterOptions{Name: removeSignalActivityName},
	)

	ws.worker.RegisterActivityWithOptions(
		ws.addSessionPrintActivity,
		activity.RegisterOptions{Name: addSessionPrintActivityName},
	)

	ws.worker.RegisterActivityWithOptions(
		ws.deactivateDrainedDeploymentActivity,
		activity.RegisterOptions{Name: deactivateDrainedDeploymentActivityName},
	)
}

func (ws *workflows) updateSessionStateActivity(ctx context.Context, sid sdktypes.SessionID, state sdktypes.SessionState) error {
	return temporalclient.TranslateError(ws.svcs.DB.UpdateSessionState(ctx, sid, state), "%v: update session state", sid)
}

func (ws *workflows) addSessionPrintActivity(ctx context.Context, sid sdktypes.SessionID, print string) error {
	return temporalclient.TranslateError(ws.svcs.DB.AddSessionPrint(ctx, sid, print), "%v: add session print", sid)
}

func (ws *workflows) removeSignalActivity(ctx context.Context, sigid uuid.UUID) error {
	return temporalclient.TranslateError(ws.svcs.DB.RemoveSignal(ctx, sigid), "%v: remove signal", sigid)
}

func (ws *workflows) getLatestEventSequenceActivity(ctx context.Context) (uint64, error) {
	seq, err := ws.svcs.DB.GetLatestEventSequence(ctx)
	err = temporalclient.TranslateError(err, "get latest event sequence")
	return seq, err
}

func (ws *workflows) deactivateDrainedDeploymentActivity(ctx context.Context, did sdktypes.DeploymentID) error {
	sl := ws.l.Sugar().With("deployment_id", did)

	return temporalclient.TranslateError(ws.svcs.DB.Transaction(ctx, func(tx db.DB) error {
		d, err := tx.GetDeployment(ctx, did)
		if err != nil {
			return fmt.Errorf("get: %w", err)
		}

		if d.State() != sdktypes.DeploymentStateDraining {
			return nil
		}

		active, err := tx.DeploymentHasActiveSessions(ctx, did)
		if err != nil {
			return fmt.Errorf("check active sessions: %w", err)
		}

		if active {
			sl.Infof("deployment %v is draining, but still has active sessions", did)
			return nil
		}

		if _, err := tx.UpdateDeploymentState(ctx, did, sdktypes.DeploymentStateInactive); err != nil {
			return fmt.Errorf("update: %w", err)
		}

		sl.Info("deactivated drained deployment %v", did)

		return nil
	}), "%v: deactivate drained deployment", did)
}

func (ws *workflows) getSignalEventActivity(ctx context.Context, sigid uuid.UUID, minSeq uint64) (sdktypes.Event, error) {
	sl := ws.l.Sugar().With("signal_id", sigid, "seq", minSeq)

	signal, err := ws.svcs.DB.GetSignal(ctx, sigid)
	if err != nil {
		if errors.Is(err, sdkerrors.ErrNotFound) {
			return sdktypes.InvalidEvent, nil
		}

		return sdktypes.InvalidEvent, temporalclient.TranslateError(err, "get signal %v", sigid)
	}

	filter := sdkservices.ListEventsFilter{
		DestinationID:     signal.DestinationID,
		Limit:             1,
		MinSequenceNumber: minSeq + 1,
		Order:             sdkservices.ListOrderAscending,
	}

	for {
		evs, err := ws.svcs.DB.ListEvents(ctx, filter)
		if err != nil {
			return sdktypes.InvalidEvent, temporalclient.TranslateError(err, "list events for %v minSeq: %v", signal.DestinationID, minSeq)
		}

		if len(evs) == 0 {
			sl.Debug("no events found")
			return sdktypes.InvalidEvent, nil
		}

		eid := evs[0].ID()

		event, err := ws.svcs.DB.GetEventByID(ctx, eid)
		if err != nil {
			if errors.Is(err, sdkerrors.ErrNotFound) {
				sl.With("event_id", eid).Warnf("event %v not found", eid)
				continue
			}

			return sdktypes.InvalidEvent, temporalclient.TranslateError(err, "get event %v", eid)
		}

		filter.MinSequenceNumber = event.Seq() + 1

		match, err := event.Matches(signal.Filter)
		if err != nil {
			// TODO(ENG-566): inform user.
			sl.Info("invalid signal filter", zap.Error(err), zap.String("filter", signal.Filter))
			continue
		}

		if match {
			return event, nil
		}
	}
}

func (ws *workflows) getSessionStopReasonActivity(ctx context.Context, sid sdktypes.SessionID) (string, error) {
	log, err := ws.svcs.DB.GetSessionLog(ctx, sdkservices.ListSessionLogRecordsFilter{SessionID: sid})
	if err != nil {
		return "", temporalclient.TranslateError(err, "get session log for %v", sid)
	}

	for _, rec := range log.Log.Records() {
		if r, ok := rec.GetStopRequest(); ok {
			return r, nil
		}
	}

	return "<unknown>", nil
}

func (ws *workflows) saveSignalActivity(ctx context.Context, signal *types.Signal) error {
	if err := ws.svcs.DB.SaveSignal(ctx, signal); err != nil {
		if errors.Is(err, sdkerrors.ErrAlreadyExists) {
			// ignore error: since siganlID is unique - this means we got replayed/retried here and the signal was already saved prior.
			ws.l.Sugar().With("signal_id", signal.ID).Warnf("signal %v already saved", signal.ID)
			return nil
		}
		return temporalclient.TranslateError(err, "save signal %v", signal.ID)
	}

	return nil
}

func (ws *workflows) terminateSessionWorkflow(wctx workflow.Context, sid sdktypes.SessionID, reason string) error {
	sl := ws.l.Sugar().With("session_id", sid)

	sl.Infof("terminating session workflow %s", sid)

	wctx = workflow.WithActivityOptions(wctx, ws.cfg.Activity.ToOptions(taskQueueName))

	// this is fine if it runs multiple times and should be short.
	if err := workflow.ExecuteActivity(wctx, terminateWorkflowActivityName, sid, reason).Get(wctx, nil); err != nil {
		sl.With("err", err).Errorf("terminate workflow %v activity: %v", sid, err)
		return temporalclient.TranslateError(err, "terminate workflow %v", sid)
	}

	// the terminated workflow should not be active at this point. in this case there should be no concurrent
	// updates with the below.

	if err := ws.updateSessionState(wctx, sid, sdktypes.NewSessionStateStopped(reason)); err != nil {
		sl.With("err", err).Errorf("update session %v state error: %w", sid, err)
	}

	sl.Infof("terminated session workflow %s", sid)

	return nil
}

func (ws *workflows) terminateWorkflowActivity(ctx context.Context, sid sdktypes.SessionID, reason string) error {
	err := ws.svcs.Temporal().TerminateWorkflow(ctx, workflowID(sid), "", reason)
	if err != nil {
		// might happen multiple times for some reason, give it a chance to update the state later on.
		var notFound *serviceerror.NotFound
		if errors.As(err, &notFound) {
			err = nil
		}
	}

	return err
}
