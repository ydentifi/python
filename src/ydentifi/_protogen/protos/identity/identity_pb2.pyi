from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DevicePlatform(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_PLATFORM_UNSPECIFIED: _ClassVar[DevicePlatform]
    DEVICE_PLATFORM_IOS: _ClassVar[DevicePlatform]
    DEVICE_PLATFORM_ANDROID: _ClassVar[DevicePlatform]

class KeyAlgorithm(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    KEY_ALGORITHM_UNSPECIFIED: _ClassVar[KeyAlgorithm]
    KEY_ALGORITHM_ED25519: _ClassVar[KeyAlgorithm]
    KEY_ALGORITHM_P256: _ClassVar[KeyAlgorithm]
    KEY_ALGORITHM_ML_DSA_65: _ClassVar[KeyAlgorithm]
    KEY_ALGORITHM_HYBRID_ES256_MLDSA65: _ClassVar[KeyAlgorithm]

class DeviceStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_STATUS_UNSPECIFIED: _ClassVar[DeviceStatus]
    DEVICE_STATUS_ACTIVE: _ClassVar[DeviceStatus]
    DEVICE_STATUS_INACTIVE: _ClassVar[DeviceStatus]
    DEVICE_STATUS_BANNED: _ClassVar[DeviceStatus]

class DeviceLifecycleEventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_LIFECYCLE_EVENT_TYPE_UNSPECIFIED: _ClassVar[DeviceLifecycleEventType]
    DEVICE_LIFECYCLE_EVENT_TYPE_ENROLLED: _ClassVar[DeviceLifecycleEventType]
    DEVICE_LIFECYCLE_EVENT_TYPE_DEACTIVATED_SELF: _ClassVar[DeviceLifecycleEventType]
    DEVICE_LIFECYCLE_EVENT_TYPE_REVOKED_ADMIN: _ClassVar[DeviceLifecycleEventType]
    DEVICE_LIFECYCLE_EVENT_TYPE_BANNED: _ClassVar[DeviceLifecycleEventType]
    DEVICE_LIFECYCLE_EVENT_TYPE_UNBANNED: _ClassVar[DeviceLifecycleEventType]
    DEVICE_LIFECYCLE_EVENT_TYPE_DELETED_VIA_USER_CASCADE: _ClassVar[DeviceLifecycleEventType]
    DEVICE_LIFECYCLE_EVENT_TYPE_ENROLLED_VIA_RECOVERY: _ClassVar[DeviceLifecycleEventType]
    DEVICE_LIFECYCLE_EVENT_TYPE_REPLACED: _ClassVar[DeviceLifecycleEventType]

class UserStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    USER_STATUS_UNSPECIFIED: _ClassVar[UserStatus]
    USER_STATUS_ACTIVE: _ClassVar[UserStatus]
    USER_STATUS_LOCKED: _ClassVar[UserStatus]

class AuthChallengeStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AUTH_CHALLENGE_STATUS_UNSPECIFIED: _ClassVar[AuthChallengeStatus]
    AUTH_CHALLENGE_STATUS_PENDING: _ClassVar[AuthChallengeStatus]
    AUTH_CHALLENGE_STATUS_DELIVERED: _ClassVar[AuthChallengeStatus]
    AUTH_CHALLENGE_STATUS_APPROVED: _ClassVar[AuthChallengeStatus]
    AUTH_CHALLENGE_STATUS_DENIED: _ClassVar[AuthChallengeStatus]
    AUTH_CHALLENGE_STATUS_EXPIRED: _ClassVar[AuthChallengeStatus]
    AUTH_CHALLENGE_STATUS_SUPERSEDED: _ClassVar[AuthChallengeStatus]
    AUTH_CHALLENGE_STATUS_DISMISSED: _ClassVar[AuthChallengeStatus]
    AUTH_CHALLENGE_STATUS_REJECTED: _ClassVar[AuthChallengeStatus]

class LocationEnforcement(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LOCATION_ENFORCEMENT_UNSPECIFIED: _ClassVar[LocationEnforcement]
    LOCATION_ENFORCEMENT_ADVISORY: _ClassVar[LocationEnforcement]
    LOCATION_ENFORCEMENT_REQUIRED: _ClassVar[LocationEnforcement]

class LocationBucket(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LOCATION_BUCKET_UNSPECIFIED: _ClassVar[LocationBucket]
    LOCATION_BUCKET_WITHIN_RADIUS: _ClassVar[LocationBucket]
    LOCATION_BUCKET_NEAR: _ClassVar[LocationBucket]
    LOCATION_BUCKET_FAR: _ClassVar[LocationBucket]
    LOCATION_BUCKET_UNAVAILABLE: _ClassVar[LocationBucket]
    LOCATION_BUCKET_DENIED_BY_USER: _ClassVar[LocationBucket]

class LocationAccuracy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LOCATION_ACCURACY_UNSPECIFIED: _ClassVar[LocationAccuracy]
    LOCATION_ACCURACY_HIGH: _ClassVar[LocationAccuracy]
    LOCATION_ACCURACY_MEDIUM: _ClassVar[LocationAccuracy]
    LOCATION_ACCURACY_LOW: _ClassVar[LocationAccuracy]

class AuthChallengeExpression(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AUTH_CHALLENGE_EXPRESSION_UNSPECIFIED: _ClassVar[AuthChallengeExpression]
    AUTH_CHALLENGE_EXPRESSION_APPROVED: _ClassVar[AuthChallengeExpression]
    AUTH_CHALLENGE_EXPRESSION_DECLINED: _ClassVar[AuthChallengeExpression]
    AUTH_CHALLENGE_EXPRESSION_DISMISSED: _ClassVar[AuthChallengeExpression]

class DeclineReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DECLINE_REASON_UNSPECIFIED: _ClassVar[DeclineReason]
    DECLINE_REASON_NOT_ME: _ClassVar[DeclineReason]
    DECLINE_REASON_SECURITY_CONCERN: _ClassVar[DeclineReason]
    DECLINE_REASON_WRONG_DETAILS: _ClassVar[DeclineReason]
    DECLINE_REASON_CANCELLED: _ClassVar[DeclineReason]

class VerificationFailure(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    VERIFICATION_FAILURE_UNSPECIFIED: _ClassVar[VerificationFailure]
    VERIFICATION_FAILURE_LOCATION_MISMATCH: _ClassVar[VerificationFailure]
    VERIFICATION_FAILURE_WRONG_MATCH_CODE: _ClassVar[VerificationFailure]

class AuthStrength(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    AUTH_STRENGTH_UNSPECIFIED: _ClassVar[AuthStrength]
    AUTH_STRENGTH_DEVICE_ACCESS: _ClassVar[AuthStrength]
    AUTH_STRENGTH_BIOMETRIC: _ClassVar[AuthStrength]

class DeviceCapability(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DEVICE_CAPABILITY_UNSPECIFIED: _ClassVar[DeviceCapability]
    DEVICE_CAPABILITY_DEVICE_ACCESS: _ClassVar[DeviceCapability]
    DEVICE_CAPABILITY_BIOMETRIC: _ClassVar[DeviceCapability]
    DEVICE_CAPABILITY_LOCATION_PRECISE: _ClassVar[DeviceCapability]
    DEVICE_CAPABILITY_LOCATION_COARSE: _ClassVar[DeviceCapability]

class UserLimitsTier(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    USER_LIMITS_TIER_UNSPECIFIED: _ClassVar[UserLimitsTier]
    USER_LIMITS_TIER_CONSERVATIVE: _ClassVar[UserLimitsTier]
    USER_LIMITS_TIER_STANDARD: _ClassVar[UserLimitsTier]
    USER_LIMITS_TIER_PERMISSIVE: _ClassVar[UserLimitsTier]

class TOTPAlgorithm(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    TOTP_ALGORITHM_UNSPECIFIED: _ClassVar[TOTPAlgorithm]
    TOTP_ALGORITHM_SHA1: _ClassVar[TOTPAlgorithm]
    TOTP_ALGORITHM_SHA256: _ClassVar[TOTPAlgorithm]
    TOTP_ALGORITHM_SHA512: _ClassVar[TOTPAlgorithm]
DEVICE_PLATFORM_UNSPECIFIED: DevicePlatform
DEVICE_PLATFORM_IOS: DevicePlatform
DEVICE_PLATFORM_ANDROID: DevicePlatform
KEY_ALGORITHM_UNSPECIFIED: KeyAlgorithm
KEY_ALGORITHM_ED25519: KeyAlgorithm
KEY_ALGORITHM_P256: KeyAlgorithm
KEY_ALGORITHM_ML_DSA_65: KeyAlgorithm
KEY_ALGORITHM_HYBRID_ES256_MLDSA65: KeyAlgorithm
DEVICE_STATUS_UNSPECIFIED: DeviceStatus
DEVICE_STATUS_ACTIVE: DeviceStatus
DEVICE_STATUS_INACTIVE: DeviceStatus
DEVICE_STATUS_BANNED: DeviceStatus
DEVICE_LIFECYCLE_EVENT_TYPE_UNSPECIFIED: DeviceLifecycleEventType
DEVICE_LIFECYCLE_EVENT_TYPE_ENROLLED: DeviceLifecycleEventType
DEVICE_LIFECYCLE_EVENT_TYPE_DEACTIVATED_SELF: DeviceLifecycleEventType
DEVICE_LIFECYCLE_EVENT_TYPE_REVOKED_ADMIN: DeviceLifecycleEventType
DEVICE_LIFECYCLE_EVENT_TYPE_BANNED: DeviceLifecycleEventType
DEVICE_LIFECYCLE_EVENT_TYPE_UNBANNED: DeviceLifecycleEventType
DEVICE_LIFECYCLE_EVENT_TYPE_DELETED_VIA_USER_CASCADE: DeviceLifecycleEventType
DEVICE_LIFECYCLE_EVENT_TYPE_ENROLLED_VIA_RECOVERY: DeviceLifecycleEventType
DEVICE_LIFECYCLE_EVENT_TYPE_REPLACED: DeviceLifecycleEventType
USER_STATUS_UNSPECIFIED: UserStatus
USER_STATUS_ACTIVE: UserStatus
USER_STATUS_LOCKED: UserStatus
AUTH_CHALLENGE_STATUS_UNSPECIFIED: AuthChallengeStatus
AUTH_CHALLENGE_STATUS_PENDING: AuthChallengeStatus
AUTH_CHALLENGE_STATUS_DELIVERED: AuthChallengeStatus
AUTH_CHALLENGE_STATUS_APPROVED: AuthChallengeStatus
AUTH_CHALLENGE_STATUS_DENIED: AuthChallengeStatus
AUTH_CHALLENGE_STATUS_EXPIRED: AuthChallengeStatus
AUTH_CHALLENGE_STATUS_SUPERSEDED: AuthChallengeStatus
AUTH_CHALLENGE_STATUS_DISMISSED: AuthChallengeStatus
AUTH_CHALLENGE_STATUS_REJECTED: AuthChallengeStatus
LOCATION_ENFORCEMENT_UNSPECIFIED: LocationEnforcement
LOCATION_ENFORCEMENT_ADVISORY: LocationEnforcement
LOCATION_ENFORCEMENT_REQUIRED: LocationEnforcement
LOCATION_BUCKET_UNSPECIFIED: LocationBucket
LOCATION_BUCKET_WITHIN_RADIUS: LocationBucket
LOCATION_BUCKET_NEAR: LocationBucket
LOCATION_BUCKET_FAR: LocationBucket
LOCATION_BUCKET_UNAVAILABLE: LocationBucket
LOCATION_BUCKET_DENIED_BY_USER: LocationBucket
LOCATION_ACCURACY_UNSPECIFIED: LocationAccuracy
LOCATION_ACCURACY_HIGH: LocationAccuracy
LOCATION_ACCURACY_MEDIUM: LocationAccuracy
LOCATION_ACCURACY_LOW: LocationAccuracy
AUTH_CHALLENGE_EXPRESSION_UNSPECIFIED: AuthChallengeExpression
AUTH_CHALLENGE_EXPRESSION_APPROVED: AuthChallengeExpression
AUTH_CHALLENGE_EXPRESSION_DECLINED: AuthChallengeExpression
AUTH_CHALLENGE_EXPRESSION_DISMISSED: AuthChallengeExpression
DECLINE_REASON_UNSPECIFIED: DeclineReason
DECLINE_REASON_NOT_ME: DeclineReason
DECLINE_REASON_SECURITY_CONCERN: DeclineReason
DECLINE_REASON_WRONG_DETAILS: DeclineReason
DECLINE_REASON_CANCELLED: DeclineReason
VERIFICATION_FAILURE_UNSPECIFIED: VerificationFailure
VERIFICATION_FAILURE_LOCATION_MISMATCH: VerificationFailure
VERIFICATION_FAILURE_WRONG_MATCH_CODE: VerificationFailure
AUTH_STRENGTH_UNSPECIFIED: AuthStrength
AUTH_STRENGTH_DEVICE_ACCESS: AuthStrength
AUTH_STRENGTH_BIOMETRIC: AuthStrength
DEVICE_CAPABILITY_UNSPECIFIED: DeviceCapability
DEVICE_CAPABILITY_DEVICE_ACCESS: DeviceCapability
DEVICE_CAPABILITY_BIOMETRIC: DeviceCapability
DEVICE_CAPABILITY_LOCATION_PRECISE: DeviceCapability
DEVICE_CAPABILITY_LOCATION_COARSE: DeviceCapability
USER_LIMITS_TIER_UNSPECIFIED: UserLimitsTier
USER_LIMITS_TIER_CONSERVATIVE: UserLimitsTier
USER_LIMITS_TIER_STANDARD: UserLimitsTier
USER_LIMITS_TIER_PERMISSIVE: UserLimitsTier
TOTP_ALGORITHM_UNSPECIFIED: TOTPAlgorithm
TOTP_ALGORITHM_SHA1: TOTPAlgorithm
TOTP_ALGORITHM_SHA256: TOTPAlgorithm
TOTP_ALGORITHM_SHA512: TOTPAlgorithm

class LocationConstraint(_message.Message):
    __slots__ = ("latitude", "longitude", "radius_m", "enforcement")
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    RADIUS_M_FIELD_NUMBER: _ClassVar[int]
    ENFORCEMENT_FIELD_NUMBER: _ClassVar[int]
    latitude: float
    longitude: float
    radius_m: int
    enforcement: LocationEnforcement
    def __init__(self, latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., radius_m: _Optional[int] = ..., enforcement: _Optional[_Union[LocationEnforcement, str]] = ...) -> None: ...

class LocationResult(_message.Message):
    __slots__ = ("bucket", "accuracy")
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    ACCURACY_FIELD_NUMBER: _ClassVar[int]
    bucket: LocationBucket
    accuracy: LocationAccuracy
    def __init__(self, bucket: _Optional[_Union[LocationBucket, str]] = ..., accuracy: _Optional[_Union[LocationAccuracy, str]] = ...) -> None: ...

class TOTPMaterial(_message.Message):
    __slots__ = ("secret", "algorithm", "digits", "period", "secret_id")
    SECRET_FIELD_NUMBER: _ClassVar[int]
    ALGORITHM_FIELD_NUMBER: _ClassVar[int]
    DIGITS_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    SECRET_ID_FIELD_NUMBER: _ClassVar[int]
    secret: bytes
    algorithm: TOTPAlgorithm
    digits: int
    period: int
    secret_id: bytes
    def __init__(self, secret: _Optional[bytes] = ..., algorithm: _Optional[_Union[TOTPAlgorithm, str]] = ..., digits: _Optional[int] = ..., period: _Optional[int] = ..., secret_id: _Optional[bytes] = ...) -> None: ...
