from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ErrorReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ERROR_REASON_UNSPECIFIED: _ClassVar[ErrorReason]
    USER_NOT_FOUND: _ClassVar[ErrorReason]
    USER_ALREADY_EXISTS: _ClassVar[ErrorReason]
    USER_LOCKED: _ClassVar[ErrorReason]
    MAX_USERS_REACHED: _ClassVar[ErrorReason]
    DEVICE_NOT_FOUND: _ClassVar[ErrorReason]
    MAX_DEVICES_REACHED: _ClassVar[ErrorReason]
    DEVICE_BANNED: _ClassVar[ErrorReason]
    CHALLENGE_NOT_FOUND: _ClassVar[ErrorReason]
    CHALLENGE_ALREADY_TERMINAL: _ClassVar[ErrorReason]
    NO_ACTIVE_DEVICE_FOR_USER: _ClassVar[ErrorReason]
    CHALLENGE_ALREADY_EXISTS: _ClassVar[ErrorReason]
    MIN_STRENGTH_REQUIRED: _ClassVar[ErrorReason]
    DEVICE_INCAPABLE: _ClassVar[ErrorReason]
    AUTH_STRENGTH_REQUIRED: _ClassVar[ErrorReason]
    AUTH_STRENGTH_INSUFFICIENT: _ClassVar[ErrorReason]
    CHALLENGE_TOO_SOON: _ClassVar[ErrorReason]
    TOTP_NOT_ENROLLED: _ClassVar[ErrorReason]
    TOTP_SECRET_KEY_UNAVAILABLE: _ClassVar[ErrorReason]
    TOTP_LOCKED: _ClassVar[ErrorReason]
    ENROLLMENT_INVITE_EXPIRED: _ClassVar[ErrorReason]
    ENROLLMENT_INVITE_ALREADY_EXISTS: _ClassVar[ErrorReason]
    RECOVERY_INVITE_ALREADY_EXISTS: _ClassVar[ErrorReason]
    LICENSE_USER_CAP_REACHED: _ClassVar[ErrorReason]
    LICENSE_EXPIRED: _ClassVar[ErrorReason]
    LICENSE_VIOLATED: _ClassVar[ErrorReason]
    RATE_LIMIT_EXCEEDED: _ClassVar[ErrorReason]
    MTLS_CERT_REFUSED: _ClassVar[ErrorReason]
    MTLS_CERT_EXPIRED: _ClassVar[ErrorReason]
    PERMISSION_DENIED: _ClassVar[ErrorReason]
    INVALID_ARGUMENT: _ClassVar[ErrorReason]
    NOT_IMPLEMENTED: _ClassVar[ErrorReason]
    SERVER_INTERNAL: _ClassVar[ErrorReason]
    SERVER_UNAVAILABLE: _ClassVar[ErrorReason]
    SERVER_TIMEOUT: _ClassVar[ErrorReason]
    APP_VERSION_TOO_OLD: _ClassVar[ErrorReason]
ERROR_REASON_UNSPECIFIED: ErrorReason
USER_NOT_FOUND: ErrorReason
USER_ALREADY_EXISTS: ErrorReason
USER_LOCKED: ErrorReason
MAX_USERS_REACHED: ErrorReason
DEVICE_NOT_FOUND: ErrorReason
MAX_DEVICES_REACHED: ErrorReason
DEVICE_BANNED: ErrorReason
CHALLENGE_NOT_FOUND: ErrorReason
CHALLENGE_ALREADY_TERMINAL: ErrorReason
NO_ACTIVE_DEVICE_FOR_USER: ErrorReason
CHALLENGE_ALREADY_EXISTS: ErrorReason
MIN_STRENGTH_REQUIRED: ErrorReason
DEVICE_INCAPABLE: ErrorReason
AUTH_STRENGTH_REQUIRED: ErrorReason
AUTH_STRENGTH_INSUFFICIENT: ErrorReason
CHALLENGE_TOO_SOON: ErrorReason
TOTP_NOT_ENROLLED: ErrorReason
TOTP_SECRET_KEY_UNAVAILABLE: ErrorReason
TOTP_LOCKED: ErrorReason
ENROLLMENT_INVITE_EXPIRED: ErrorReason
ENROLLMENT_INVITE_ALREADY_EXISTS: ErrorReason
RECOVERY_INVITE_ALREADY_EXISTS: ErrorReason
LICENSE_USER_CAP_REACHED: ErrorReason
LICENSE_EXPIRED: ErrorReason
LICENSE_VIOLATED: ErrorReason
RATE_LIMIT_EXCEEDED: ErrorReason
MTLS_CERT_REFUSED: ErrorReason
MTLS_CERT_EXPIRED: ErrorReason
PERMISSION_DENIED: ErrorReason
INVALID_ARGUMENT: ErrorReason
NOT_IMPLEMENTED: ErrorReason
SERVER_INTERNAL: ErrorReason
SERVER_UNAVAILABLE: ErrorReason
SERVER_TIMEOUT: ErrorReason
APP_VERSION_TOO_OLD: ErrorReason

class ErrorDetail(_message.Message):
    __slots__ = ("reason", "trace_id", "field", "subject", "auto_expires_at_unix_ms")
    REASON_FIELD_NUMBER: _ClassVar[int]
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    AUTO_EXPIRES_AT_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    reason: ErrorReason
    trace_id: str
    field: str
    subject: str
    auto_expires_at_unix_ms: int
    def __init__(self, reason: _Optional[_Union[ErrorReason, str]] = ..., trace_id: _Optional[str] = ..., field: _Optional[str] = ..., subject: _Optional[str] = ..., auto_expires_at_unix_ms: _Optional[int] = ...) -> None: ...
