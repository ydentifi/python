from ydentifi._protogen.protos.identity import identity_pb2 as _identity_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BulkCreateCappedReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BULK_CREATE_CAPPED_REASON_UNSPECIFIED: _ClassVar[BulkCreateCappedReason]
    BULK_CREATE_CAPPED_REASON_MAX_USERS: _ClassVar[BulkCreateCappedReason]

class TotpSkew(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TOTP_SKEW_UNSPECIFIED: _ClassVar[TotpSkew]
    TOTP_SKEW_0: _ClassVar[TotpSkew]
    TOTP_SKEW_1: _ClassVar[TotpSkew]
    TOTP_SKEW_2: _ClassVar[TotpSkew]
    TOTP_SKEW_3: _ClassVar[TotpSkew]
    TOTP_SKEW_4: _ClassVar[TotpSkew]
    TOTP_SKEW_5: _ClassVar[TotpSkew]
BULK_CREATE_CAPPED_REASON_UNSPECIFIED: BulkCreateCappedReason
BULK_CREATE_CAPPED_REASON_MAX_USERS: BulkCreateCappedReason
TOTP_SKEW_UNSPECIFIED: TotpSkew
TOTP_SKEW_0: TotpSkew
TOTP_SKEW_1: TotpSkew
TOTP_SKEW_2: TotpSkew
TOTP_SKEW_3: TotpSkew
TOTP_SKEW_4: TotpSkew
TOTP_SKEW_5: TotpSkew

class CreateUserRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class CreateUserResponse(_message.Message):
    __slots__ = ("opaque_id",)
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    def __init__(self, opaque_id: _Optional[str] = ...) -> None: ...

class BulkCreateUsersRequest(_message.Message):
    __slots__ = ("count", "idempotency_key")
    COUNT_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    count: int
    idempotency_key: str
    def __init__(self, count: _Optional[int] = ..., idempotency_key: _Optional[str] = ...) -> None: ...

class BulkCreateUsersFrame(_message.Message):
    __slots__ = ("chunk", "summary")
    CHUNK_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    chunk: BulkCreateUsersChunk
    summary: BulkCreateUsersSummary
    def __init__(self, chunk: _Optional[_Union[BulkCreateUsersChunk, _Mapping]] = ..., summary: _Optional[_Union[BulkCreateUsersSummary, _Mapping]] = ...) -> None: ...

class BulkCreateUsersChunk(_message.Message):
    __slots__ = ("opaque_ids", "created_total")
    OPAQUE_IDS_FIELD_NUMBER: _ClassVar[int]
    CREATED_TOTAL_FIELD_NUMBER: _ClassVar[int]
    opaque_ids: _containers.RepeatedScalarFieldContainer[str]
    created_total: int
    def __init__(self, opaque_ids: _Optional[_Iterable[str]] = ..., created_total: _Optional[int] = ...) -> None: ...

class BulkCreateUsersSummary(_message.Message):
    __slots__ = ("requested", "created", "capped", "capped_reason")
    REQUESTED_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    CAPPED_FIELD_NUMBER: _ClassVar[int]
    CAPPED_REASON_FIELD_NUMBER: _ClassVar[int]
    requested: int
    created: int
    capped: int
    capped_reason: BulkCreateCappedReason
    def __init__(self, requested: _Optional[int] = ..., created: _Optional[int] = ..., capped: _Optional[int] = ..., capped_reason: _Optional[_Union[BulkCreateCappedReason, str]] = ...) -> None: ...

class GetUserRequest(_message.Message):
    __slots__ = ("opaque_id",)
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    def __init__(self, opaque_id: _Optional[str] = ...) -> None: ...

class GetUserResponse(_message.Message):
    __slots__ = ("opaque_id", "status", "created_at", "last_authenticated_at", "last_activity_at", "totp_locked")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_AUTHENTICATED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_ACTIVITY_AT_FIELD_NUMBER: _ClassVar[int]
    TOTP_LOCKED_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    status: _identity_pb2.UserStatus
    created_at: str
    last_authenticated_at: str
    last_activity_at: str
    totp_locked: bool
    def __init__(self, opaque_id: _Optional[str] = ..., status: _Optional[_Union[_identity_pb2.UserStatus, str]] = ..., created_at: _Optional[str] = ..., last_authenticated_at: _Optional[str] = ..., last_activity_at: _Optional[str] = ..., totp_locked: _Optional[bool] = ...) -> None: ...

class ExportUsersRequest(_message.Message):
    __slots__ = ("start_after_user_id",)
    START_AFTER_USER_ID_FIELD_NUMBER: _ClassVar[int]
    start_after_user_id: str
    def __init__(self, start_after_user_id: _Optional[str] = ...) -> None: ...

class ExportUsersResponse(_message.Message):
    __slots__ = ("users",)
    USERS_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedCompositeFieldContainer[GetUserResponse]
    def __init__(self, users: _Optional[_Iterable[_Union[GetUserResponse, _Mapping]]] = ...) -> None: ...

class UpdateUserStatusRequest(_message.Message):
    __slots__ = ("opaque_id", "status")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    status: _identity_pb2.UserStatus
    def __init__(self, opaque_id: _Optional[str] = ..., status: _Optional[_Union[_identity_pb2.UserStatus, str]] = ...) -> None: ...

class UpdateUserStatusResponse(_message.Message):
    __slots__ = ("new_status",)
    NEW_STATUS_FIELD_NUMBER: _ClassVar[int]
    new_status: _identity_pb2.UserStatus
    def __init__(self, new_status: _Optional[_Union[_identity_pb2.UserStatus, str]] = ...) -> None: ...

class DeleteUserRequest(_message.Message):
    __slots__ = ("opaque_id",)
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    def __init__(self, opaque_id: _Optional[str] = ...) -> None: ...

class DeleteUserResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: _Optional[bool] = ...) -> None: ...

class UnlockUserRequestLimitsRequest(_message.Message):
    __slots__ = ("opaque_id",)
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    def __init__(self, opaque_id: _Optional[str] = ...) -> None: ...

class UnlockUserRequestLimitsResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: _Optional[bool] = ...) -> None: ...

class ListDevicesForUserRequest(_message.Message):
    __slots__ = ("opaque_id",)
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    def __init__(self, opaque_id: _Optional[str] = ...) -> None: ...

class ListDevicesForUserResponse(_message.Message):
    __slots__ = ("devices",)
    DEVICES_FIELD_NUMBER: _ClassVar[int]
    devices: _containers.RepeatedCompositeFieldContainer[DeviceSummary]
    def __init__(self, devices: _Optional[_Iterable[_Union[DeviceSummary, _Mapping]]] = ...) -> None: ...

class RevokeDeviceRequest(_message.Message):
    __slots__ = ("opaque_id", "device_id")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    device_id: str
    def __init__(self, opaque_id: _Optional[str] = ..., device_id: _Optional[str] = ...) -> None: ...

class RevokeDeviceResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: _Optional[bool] = ...) -> None: ...

class BanDeviceRequest(_message.Message):
    __slots__ = ("opaque_id", "device_id", "reason")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    device_id: str
    reason: str
    def __init__(self, opaque_id: _Optional[str] = ..., device_id: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class BanDeviceResponse(_message.Message):
    __slots__ = ("success", "cascaded_device_count")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    CASCADED_DEVICE_COUNT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    cascaded_device_count: int
    def __init__(self, success: _Optional[bool] = ..., cascaded_device_count: _Optional[int] = ...) -> None: ...

class UnbanDeviceRequest(_message.Message):
    __slots__ = ("opaque_id", "device_id", "permanent_id")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    PERMANENT_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    device_id: str
    permanent_id: str
    def __init__(self, opaque_id: _Optional[str] = ..., device_id: _Optional[str] = ..., permanent_id: _Optional[str] = ...) -> None: ...

class UnbanDeviceResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: _Optional[bool] = ...) -> None: ...

class ListActiveChallengesRequest(_message.Message):
    __slots__ = ("opaque_id",)
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    def __init__(self, opaque_id: _Optional[str] = ...) -> None: ...

class ListActiveChallengesResponse(_message.Message):
    __slots__ = ("challenges",)
    CHALLENGES_FIELD_NUMBER: _ClassVar[int]
    challenges: _containers.RepeatedCompositeFieldContainer[ActiveChallengeSummary]
    def __init__(self, challenges: _Optional[_Iterable[_Union[ActiveChallengeSummary, _Mapping]]] = ...) -> None: ...

class ActiveChallengeSummary(_message.Message):
    __slots__ = ("challenge_id", "status", "context", "location_constraint", "issued_at", "expires_at", "delivered_at")
    CHALLENGE_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    LOCATION_CONSTRAINT_FIELD_NUMBER: _ClassVar[int]
    ISSUED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    DELIVERED_AT_FIELD_NUMBER: _ClassVar[int]
    challenge_id: str
    status: _identity_pb2.AuthChallengeStatus
    context: bytes
    location_constraint: _identity_pb2.LocationConstraint
    issued_at: str
    expires_at: str
    delivered_at: str
    def __init__(self, challenge_id: _Optional[str] = ..., status: _Optional[_Union[_identity_pb2.AuthChallengeStatus, str]] = ..., context: _Optional[bytes] = ..., location_constraint: _Optional[_Union[_identity_pb2.LocationConstraint, _Mapping]] = ..., issued_at: _Optional[str] = ..., expires_at: _Optional[str] = ..., delivered_at: _Optional[str] = ...) -> None: ...

class DeviceSummary(_message.Message):
    __slots__ = ("device_id", "permanent_id", "platform", "status", "created_at", "last_authenticated_at", "name", "device_model")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    PERMANENT_ID_FIELD_NUMBER: _ClassVar[int]
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_AUTHENTICATED_AT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEVICE_MODEL_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    permanent_id: str
    platform: _identity_pb2.DevicePlatform
    status: _identity_pb2.DeviceStatus
    created_at: str
    last_authenticated_at: str
    name: str
    device_model: str
    def __init__(self, device_id: _Optional[str] = ..., permanent_id: _Optional[str] = ..., platform: _Optional[_Union[_identity_pb2.DevicePlatform, str]] = ..., status: _Optional[_Union[_identity_pb2.DeviceStatus, str]] = ..., created_at: _Optional[str] = ..., last_authenticated_at: _Optional[str] = ..., name: _Optional[str] = ..., device_model: _Optional[str] = ...) -> None: ...

class IssueUserTotpEnrollmentRequest(_message.Message):
    __slots__ = ("opaque_id", "reuse_existing")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    REUSE_EXISTING_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    reuse_existing: bool
    def __init__(self, opaque_id: _Optional[str] = ..., reuse_existing: _Optional[bool] = ...) -> None: ...

class IssueUserTotpEnrollmentResponse(_message.Message):
    __slots__ = ("qr_code_png_base64", "totp_url", "secret_base32")
    QR_CODE_PNG_BASE64_FIELD_NUMBER: _ClassVar[int]
    TOTP_URL_FIELD_NUMBER: _ClassVar[int]
    SECRET_BASE32_FIELD_NUMBER: _ClassVar[int]
    qr_code_png_base64: str
    totp_url: str
    secret_base32: str
    def __init__(self, qr_code_png_base64: _Optional[str] = ..., totp_url: _Optional[str] = ..., secret_base32: _Optional[str] = ...) -> None: ...

class VerifyUserTotpRequest(_message.Message):
    __slots__ = ("opaque_id", "totp_code", "skew")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    TOTP_CODE_FIELD_NUMBER: _ClassVar[int]
    SKEW_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    totp_code: str
    skew: TotpSkew
    def __init__(self, opaque_id: _Optional[str] = ..., totp_code: _Optional[str] = ..., skew: _Optional[_Union[TotpSkew, str]] = ...) -> None: ...

class VerifyUserTotpResponse(_message.Message):
    __slots__ = ("valid",)
    VALID_FIELD_NUMBER: _ClassVar[int]
    valid: bool
    def __init__(self, valid: _Optional[bool] = ...) -> None: ...

class IssueEnrollmentInviteRequest(_message.Message):
    __slots__ = ("opaque_id", "ttl_seconds", "context")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    TTL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    ttl_seconds: int
    context: bytes
    def __init__(self, opaque_id: _Optional[str] = ..., ttl_seconds: _Optional[int] = ..., context: _Optional[bytes] = ...) -> None: ...

class IssueEnrollmentInviteResponse(_message.Message):
    __slots__ = ("invite_token", "qr_payload", "expires_at")
    INVITE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    QR_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    invite_token: bytes
    qr_payload: bytes
    expires_at: str
    def __init__(self, invite_token: _Optional[bytes] = ..., qr_payload: _Optional[bytes] = ..., expires_at: _Optional[str] = ...) -> None: ...

class IssueRecoveryInviteRequest(_message.Message):
    __slots__ = ("opaque_id", "ttl_seconds", "context")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    TTL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    ttl_seconds: int
    context: bytes
    def __init__(self, opaque_id: _Optional[str] = ..., ttl_seconds: _Optional[int] = ..., context: _Optional[bytes] = ...) -> None: ...

class IssueRecoveryInviteResponse(_message.Message):
    __slots__ = ("invite_token", "qr_payload", "expires_at", "revoked_device_count")
    INVITE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    QR_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    REVOKED_DEVICE_COUNT_FIELD_NUMBER: _ClassVar[int]
    invite_token: bytes
    qr_payload: bytes
    expires_at: str
    revoked_device_count: int
    def __init__(self, invite_token: _Optional[bytes] = ..., qr_payload: _Optional[bytes] = ..., expires_at: _Optional[str] = ..., revoked_device_count: _Optional[int] = ...) -> None: ...

class IssueAuthChallengeRequest(_message.Message):
    __slots__ = ("opaque_id", "ttl_seconds", "context", "location_constraint", "min_strength", "match_code", "challenge_id")
    OPAQUE_ID_FIELD_NUMBER: _ClassVar[int]
    TTL_SECONDS_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    LOCATION_CONSTRAINT_FIELD_NUMBER: _ClassVar[int]
    MIN_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    MATCH_CODE_FIELD_NUMBER: _ClassVar[int]
    CHALLENGE_ID_FIELD_NUMBER: _ClassVar[int]
    opaque_id: str
    ttl_seconds: int
    context: bytes
    location_constraint: _identity_pb2.LocationConstraint
    min_strength: _identity_pb2.AuthStrength
    match_code: int
    challenge_id: str
    def __init__(self, opaque_id: _Optional[str] = ..., ttl_seconds: _Optional[int] = ..., context: _Optional[bytes] = ..., location_constraint: _Optional[_Union[_identity_pb2.LocationConstraint, _Mapping]] = ..., min_strength: _Optional[_Union[_identity_pb2.AuthStrength, str]] = ..., match_code: _Optional[int] = ..., challenge_id: _Optional[str] = ...) -> None: ...

class IssueAuthChallengeResponse(_message.Message):
    __slots__ = ("challenge_id", "qr_encoded", "expires_at")
    CHALLENGE_ID_FIELD_NUMBER: _ClassVar[int]
    QR_ENCODED_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    challenge_id: str
    qr_encoded: str
    expires_at: str
    def __init__(self, challenge_id: _Optional[str] = ..., qr_encoded: _Optional[str] = ..., expires_at: _Optional[str] = ...) -> None: ...

class AwaitChallengeRequest(_message.Message):
    __slots__ = ("challenge_id",)
    CHALLENGE_ID_FIELD_NUMBER: _ClassVar[int]
    challenge_id: str
    def __init__(self, challenge_id: _Optional[str] = ...) -> None: ...

class AwaitChallengeFrame(_message.Message):
    __slots__ = ("status", "signature", "location_result", "decline_reason", "expression", "verification_failure", "emitted_at", "auth_strength")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_RESULT_FIELD_NUMBER: _ClassVar[int]
    DECLINE_REASON_FIELD_NUMBER: _ClassVar[int]
    EXPRESSION_FIELD_NUMBER: _ClassVar[int]
    VERIFICATION_FAILURE_FIELD_NUMBER: _ClassVar[int]
    EMITTED_AT_FIELD_NUMBER: _ClassVar[int]
    AUTH_STRENGTH_FIELD_NUMBER: _ClassVar[int]
    status: _identity_pb2.AuthChallengeStatus
    signature: bytes
    location_result: _identity_pb2.LocationResult
    decline_reason: _identity_pb2.DeclineReason
    expression: _identity_pb2.AuthChallengeExpression
    verification_failure: _identity_pb2.VerificationFailure
    emitted_at: str
    auth_strength: _identity_pb2.AuthStrength
    def __init__(self, status: _Optional[_Union[_identity_pb2.AuthChallengeStatus, str]] = ..., signature: _Optional[bytes] = ..., location_result: _Optional[_Union[_identity_pb2.LocationResult, _Mapping]] = ..., decline_reason: _Optional[_Union[_identity_pb2.DeclineReason, str]] = ..., expression: _Optional[_Union[_identity_pb2.AuthChallengeExpression, str]] = ..., verification_failure: _Optional[_Union[_identity_pb2.VerificationFailure, str]] = ..., emitted_at: _Optional[str] = ..., auth_strength: _Optional[_Union[_identity_pb2.AuthStrength, str]] = ...) -> None: ...
