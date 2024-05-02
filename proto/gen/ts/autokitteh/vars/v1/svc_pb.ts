// @generated by protoc-gen-es v1.5.1 with parameter "target=ts"
// @generated from file autokitteh/vars/v1/svc.proto (package autokitteh.vars.v1, syntax proto3)
/* eslint-disable */
// @ts-nocheck

import type { BinaryReadOptions, FieldList, JsonReadOptions, JsonValue, PartialMessage, PlainMessage } from "@bufbuild/protobuf";
import { Message, proto3 } from "@bufbuild/protobuf";
import { Var } from "./var_pb.js";

/**
 * @generated from message autokitteh.vars.v1.SetRequest
 */
export class SetRequest extends Message<SetRequest> {
  /**
   * @generated from field: repeated autokitteh.vars.v1.Var vars = 1;
   */
  vars: Var[] = [];

  constructor(data?: PartialMessage<SetRequest>) {
    super();
    proto3.util.initPartial(data, this);
  }

  static readonly runtime: typeof proto3 = proto3;
  static readonly typeName = "autokitteh.vars.v1.SetRequest";
  static readonly fields: FieldList = proto3.util.newFieldList(() => [
    { no: 1, name: "vars", kind: "message", T: Var, repeated: true },
  ]);

  static fromBinary(bytes: Uint8Array, options?: Partial<BinaryReadOptions>): SetRequest {
    return new SetRequest().fromBinary(bytes, options);
  }

  static fromJson(jsonValue: JsonValue, options?: Partial<JsonReadOptions>): SetRequest {
    return new SetRequest().fromJson(jsonValue, options);
  }

  static fromJsonString(jsonString: string, options?: Partial<JsonReadOptions>): SetRequest {
    return new SetRequest().fromJsonString(jsonString, options);
  }

  static equals(a: SetRequest | PlainMessage<SetRequest> | undefined, b: SetRequest | PlainMessage<SetRequest> | undefined): boolean {
    return proto3.util.equals(SetRequest, a, b);
  }
}

/**
 * @generated from message autokitteh.vars.v1.SetResponse
 */
export class SetResponse extends Message<SetResponse> {
  constructor(data?: PartialMessage<SetResponse>) {
    super();
    proto3.util.initPartial(data, this);
  }

  static readonly runtime: typeof proto3 = proto3;
  static readonly typeName = "autokitteh.vars.v1.SetResponse";
  static readonly fields: FieldList = proto3.util.newFieldList(() => [
  ]);

  static fromBinary(bytes: Uint8Array, options?: Partial<BinaryReadOptions>): SetResponse {
    return new SetResponse().fromBinary(bytes, options);
  }

  static fromJson(jsonValue: JsonValue, options?: Partial<JsonReadOptions>): SetResponse {
    return new SetResponse().fromJson(jsonValue, options);
  }

  static fromJsonString(jsonString: string, options?: Partial<JsonReadOptions>): SetResponse {
    return new SetResponse().fromJsonString(jsonString, options);
  }

  static equals(a: SetResponse | PlainMessage<SetResponse> | undefined, b: SetResponse | PlainMessage<SetResponse> | undefined): boolean {
    return proto3.util.equals(SetResponse, a, b);
  }
}

/**
 * @generated from message autokitteh.vars.v1.DeleteRequest
 */
export class DeleteRequest extends Message<DeleteRequest> {
  /**
   * @generated from field: string scope_id = 1;
   */
  scopeId = "";

  /**
   * If empty, remove all for scope.
   *
   * @generated from field: repeated string names = 2;
   */
  names: string[] = [];

  constructor(data?: PartialMessage<DeleteRequest>) {
    super();
    proto3.util.initPartial(data, this);
  }

  static readonly runtime: typeof proto3 = proto3;
  static readonly typeName = "autokitteh.vars.v1.DeleteRequest";
  static readonly fields: FieldList = proto3.util.newFieldList(() => [
    { no: 1, name: "scope_id", kind: "scalar", T: 9 /* ScalarType.STRING */ },
    { no: 2, name: "names", kind: "scalar", T: 9 /* ScalarType.STRING */, repeated: true },
  ]);

  static fromBinary(bytes: Uint8Array, options?: Partial<BinaryReadOptions>): DeleteRequest {
    return new DeleteRequest().fromBinary(bytes, options);
  }

  static fromJson(jsonValue: JsonValue, options?: Partial<JsonReadOptions>): DeleteRequest {
    return new DeleteRequest().fromJson(jsonValue, options);
  }

  static fromJsonString(jsonString: string, options?: Partial<JsonReadOptions>): DeleteRequest {
    return new DeleteRequest().fromJsonString(jsonString, options);
  }

  static equals(a: DeleteRequest | PlainMessage<DeleteRequest> | undefined, b: DeleteRequest | PlainMessage<DeleteRequest> | undefined): boolean {
    return proto3.util.equals(DeleteRequest, a, b);
  }
}

/**
 * @generated from message autokitteh.vars.v1.DeleteResponse
 */
export class DeleteResponse extends Message<DeleteResponse> {
  constructor(data?: PartialMessage<DeleteResponse>) {
    super();
    proto3.util.initPartial(data, this);
  }

  static readonly runtime: typeof proto3 = proto3;
  static readonly typeName = "autokitteh.vars.v1.DeleteResponse";
  static readonly fields: FieldList = proto3.util.newFieldList(() => [
  ]);

  static fromBinary(bytes: Uint8Array, options?: Partial<BinaryReadOptions>): DeleteResponse {
    return new DeleteResponse().fromBinary(bytes, options);
  }

  static fromJson(jsonValue: JsonValue, options?: Partial<JsonReadOptions>): DeleteResponse {
    return new DeleteResponse().fromJson(jsonValue, options);
  }

  static fromJsonString(jsonString: string, options?: Partial<JsonReadOptions>): DeleteResponse {
    return new DeleteResponse().fromJsonString(jsonString, options);
  }

  static equals(a: DeleteResponse | PlainMessage<DeleteResponse> | undefined, b: DeleteResponse | PlainMessage<DeleteResponse> | undefined): boolean {
    return proto3.util.equals(DeleteResponse, a, b);
  }
}

/**
 * @generated from message autokitteh.vars.v1.GetRequest
 */
export class GetRequest extends Message<GetRequest> {
  /**
   * @generated from field: string scope_id = 1;
   */
  scopeId = "";

  /**
   * if empty, get all.
   *
   * @generated from field: repeated string names = 2;
   */
  names: string[] = [];

  /**
   * if true, returns secret values. if false, secret values are omitted.
   *
   * @generated from field: bool reveal = 3;
   */
  reveal = false;

  constructor(data?: PartialMessage<GetRequest>) {
    super();
    proto3.util.initPartial(data, this);
  }

  static readonly runtime: typeof proto3 = proto3;
  static readonly typeName = "autokitteh.vars.v1.GetRequest";
  static readonly fields: FieldList = proto3.util.newFieldList(() => [
    { no: 1, name: "scope_id", kind: "scalar", T: 9 /* ScalarType.STRING */ },
    { no: 2, name: "names", kind: "scalar", T: 9 /* ScalarType.STRING */, repeated: true },
    { no: 3, name: "reveal", kind: "scalar", T: 8 /* ScalarType.BOOL */ },
  ]);

  static fromBinary(bytes: Uint8Array, options?: Partial<BinaryReadOptions>): GetRequest {
    return new GetRequest().fromBinary(bytes, options);
  }

  static fromJson(jsonValue: JsonValue, options?: Partial<JsonReadOptions>): GetRequest {
    return new GetRequest().fromJson(jsonValue, options);
  }

  static fromJsonString(jsonString: string, options?: Partial<JsonReadOptions>): GetRequest {
    return new GetRequest().fromJsonString(jsonString, options);
  }

  static equals(a: GetRequest | PlainMessage<GetRequest> | undefined, b: GetRequest | PlainMessage<GetRequest> | undefined): boolean {
    return proto3.util.equals(GetRequest, a, b);
  }
}

/**
 * @generated from message autokitteh.vars.v1.GetResponse
 */
export class GetResponse extends Message<GetResponse> {
  /**
   * @generated from field: repeated autokitteh.vars.v1.Var vars = 1;
   */
  vars: Var[] = [];

  constructor(data?: PartialMessage<GetResponse>) {
    super();
    proto3.util.initPartial(data, this);
  }

  static readonly runtime: typeof proto3 = proto3;
  static readonly typeName = "autokitteh.vars.v1.GetResponse";
  static readonly fields: FieldList = proto3.util.newFieldList(() => [
    { no: 1, name: "vars", kind: "message", T: Var, repeated: true },
  ]);

  static fromBinary(bytes: Uint8Array, options?: Partial<BinaryReadOptions>): GetResponse {
    return new GetResponse().fromBinary(bytes, options);
  }

  static fromJson(jsonValue: JsonValue, options?: Partial<JsonReadOptions>): GetResponse {
    return new GetResponse().fromJson(jsonValue, options);
  }

  static fromJsonString(jsonString: string, options?: Partial<JsonReadOptions>): GetResponse {
    return new GetResponse().fromJsonString(jsonString, options);
  }

  static equals(a: GetResponse | PlainMessage<GetResponse> | undefined, b: GetResponse | PlainMessage<GetResponse> | undefined): boolean {
    return proto3.util.equals(GetResponse, a, b);
  }
}

/**
 * @generated from message autokitteh.vars.v1.FindConnectionIDsRequest
 */
export class FindConnectionIDsRequest extends Message<FindConnectionIDsRequest> {
  /**
   * @generated from field: string integration_id = 1;
   */
  integrationId = "";

  /**
   * if empty, return all for scope.
   *
   * @generated from field: string name = 2;
   */
  name = "";

  /**
   * if set, name must be set.
   *
   * @generated from field: string value = 3;
   */
  value = "";

  constructor(data?: PartialMessage<FindConnectionIDsRequest>) {
    super();
    proto3.util.initPartial(data, this);
  }

  static readonly runtime: typeof proto3 = proto3;
  static readonly typeName = "autokitteh.vars.v1.FindConnectionIDsRequest";
  static readonly fields: FieldList = proto3.util.newFieldList(() => [
    { no: 1, name: "integration_id", kind: "scalar", T: 9 /* ScalarType.STRING */ },
    { no: 2, name: "name", kind: "scalar", T: 9 /* ScalarType.STRING */ },
    { no: 3, name: "value", kind: "scalar", T: 9 /* ScalarType.STRING */ },
  ]);

  static fromBinary(bytes: Uint8Array, options?: Partial<BinaryReadOptions>): FindConnectionIDsRequest {
    return new FindConnectionIDsRequest().fromBinary(bytes, options);
  }

  static fromJson(jsonValue: JsonValue, options?: Partial<JsonReadOptions>): FindConnectionIDsRequest {
    return new FindConnectionIDsRequest().fromJson(jsonValue, options);
  }

  static fromJsonString(jsonString: string, options?: Partial<JsonReadOptions>): FindConnectionIDsRequest {
    return new FindConnectionIDsRequest().fromJsonString(jsonString, options);
  }

  static equals(a: FindConnectionIDsRequest | PlainMessage<FindConnectionIDsRequest> | undefined, b: FindConnectionIDsRequest | PlainMessage<FindConnectionIDsRequest> | undefined): boolean {
    return proto3.util.equals(FindConnectionIDsRequest, a, b);
  }
}

/**
 * @generated from message autokitteh.vars.v1.FindConnectionIDsResponse
 */
export class FindConnectionIDsResponse extends Message<FindConnectionIDsResponse> {
  /**
   * @generated from field: repeated string connection_ids = 1;
   */
  connectionIds: string[] = [];

  constructor(data?: PartialMessage<FindConnectionIDsResponse>) {
    super();
    proto3.util.initPartial(data, this);
  }

  static readonly runtime: typeof proto3 = proto3;
  static readonly typeName = "autokitteh.vars.v1.FindConnectionIDsResponse";
  static readonly fields: FieldList = proto3.util.newFieldList(() => [
    { no: 1, name: "connection_ids", kind: "scalar", T: 9 /* ScalarType.STRING */, repeated: true },
  ]);

  static fromBinary(bytes: Uint8Array, options?: Partial<BinaryReadOptions>): FindConnectionIDsResponse {
    return new FindConnectionIDsResponse().fromBinary(bytes, options);
  }

  static fromJson(jsonValue: JsonValue, options?: Partial<JsonReadOptions>): FindConnectionIDsResponse {
    return new FindConnectionIDsResponse().fromJson(jsonValue, options);
  }

  static fromJsonString(jsonString: string, options?: Partial<JsonReadOptions>): FindConnectionIDsResponse {
    return new FindConnectionIDsResponse().fromJsonString(jsonString, options);
  }

  static equals(a: FindConnectionIDsResponse | PlainMessage<FindConnectionIDsResponse> | undefined, b: FindConnectionIDsResponse | PlainMessage<FindConnectionIDsResponse> | undefined): boolean {
    return proto3.util.equals(FindConnectionIDsResponse, a, b);
  }
}
