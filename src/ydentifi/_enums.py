"""The enumerations of the public types.

Each is an :class:`enum.IntEnum` whose values are the protocol's numbers.
"""

from __future__ import annotations

from enum import IntEnum


class _OpenIntEnum(IntEnum):
    """An ``IntEnum`` that keeps a value it has no member for.

    An unknown value becomes a member named ``UNKNOWN_<n>`` that is equal to
    the number. ``_missing_`` is the standard library's hook for this.
    """

    @classmethod
    def _missing_(cls, value: object) -> _OpenIntEnum | None:
        if not isinstance(value, int) or isinstance(value, bool):
            return None
        member = int.__new__(cls, value)
        member._name_ = f"UNKNOWN_{value}"
        member._value_ = value
        return member


class UserStatus(_OpenIntEnum):
    """The state of a user."""

    UNSPECIFIED = 0
    ACTIVE = 1
    LOCKED = 2


class DevicePlatform(_OpenIntEnum):
    """The operating system of an enrolled phone."""

    UNSPECIFIED = 0
    IOS = 1
    ANDROID = 2


class DeviceStatus(_OpenIntEnum):
    """The state of an enrolled device."""

    UNSPECIFIED = 0
    ACTIVE = 1
    #: A revoked or replaced device; ``revoke_device`` leaves a device here.
    INACTIVE = 3
    BANNED = 4


class ChallengeStatus(_OpenIntEnum):
    """The state of an authentication challenge.

    The states ``3`` to ``8`` end the challenge; :attr:`ChallengeStatus.is_terminal`
    says whether a state does.
    """

    UNSPECIFIED = 0
    PENDING = 1
    DELIVERED = 2
    APPROVED = 3
    #: The user refused.
    DENIED = 4
    EXPIRED = 5
    SUPERSEDED = 6
    DISMISSED = 7
    #: The user approved, but a location or match-code check failed.
    #: ChallengeResult.verification_failure identifies the failed check.
    #: This result must not be recorded as a user decline.
    REJECTED = 8

    @property
    def is_terminal(self) -> bool:
        """Whether the state ends the challenge.

        The terminal statuses are ``APPROVED``, ``DENIED``, ``REJECTED``,
        ``EXPIRED``, ``SUPERSEDED`` and ``DISMISSED``.
        """
        return self in _TERMINAL_CHALLENGE_STATUSES


_TERMINAL_CHALLENGE_STATUSES: frozenset[ChallengeStatus] = frozenset(
    {
        ChallengeStatus.APPROVED,
        ChallengeStatus.DENIED,
        ChallengeStatus.REJECTED,
        ChallengeStatus.EXPIRED,
        ChallengeStatus.SUPERSEDED,
        ChallengeStatus.DISMISSED,
    }
)


class ChallengeExpression(_OpenIntEnum):
    """The user's response, recorded separately from verification.

    User approval that fails verification has status ``REJECTED`` and
    expression ``APPROVED``.
    """

    #: Nobody answered — the challenge expired, or is still in flight.
    UNSPECIFIED = 0
    APPROVED = 1
    DECLINED = 2
    DISMISSED = 3


class DeclineReason(_OpenIntEnum):
    """The user-selected reason for a declined challenge.

    This field is set only on ``DENIED``. A failed check after user approval
    is reported separately as a :class:`VerificationFailure` on ``REJECTED``.
    """

    UNSPECIFIED = 0
    NOT_ME = 1
    SECURITY_CONCERN = 2
    WRONG_DETAILS = 3
    CANCELLED = 4
    # Values 5 through 10 are reserved and must not be reused.


class VerificationFailure(_OpenIntEnum):
    """A verification check that rejected user approval.

    The value is set only on ``REJECTED`` results.
    """

    UNSPECIFIED = 0
    #: The challenge required a place and the device did not report
    #: being in it. Reporting no place at all counts as not satisfying.
    LOCATION_MISMATCH = 1
    #: The submitted number differs from the issued number. This may indicate
    #: approval of a request originating from another session.
    WRONG_MATCH_CODE = 2


class AuthStrength(_OpenIntEnum):
    """The unlock a phone used, or the weakest one a challenge accepts.

    The server refuses a challenge whose ``min_strength`` is ``UNSPECIFIED``.
    """

    UNSPECIFIED = 0
    DEVICE_ACCESS = 1
    #: Biometric authentication is the highest supported strength.
    BIOMETRIC = 2
    # Value 3 is reserved and must not be reused.


class LocationBucket(_OpenIntEnum):
    """Where the phone was, relative to a geofence, as the phone reported it."""

    UNSPECIFIED = 0
    WITHIN_RADIUS = 1
    NEAR = 2
    FAR = 3
    UNAVAILABLE = 4
    DENIED_BY_USER = 5


class LocationAccuracy(_OpenIntEnum):
    """How precise the phone's own location fix was."""

    UNSPECIFIED = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class LocationEnforcement(_OpenIntEnum):
    """How a geofence is applied."""

    UNSPECIFIED = 0
    ADVISORY = 1
    REQUIRED = 2


__all__ = [
    "AuthStrength",
    "ChallengeExpression",
    "ChallengeStatus",
    "DeclineReason",
    "DevicePlatform",
    "DeviceStatus",
    "LocationAccuracy",
    "LocationBucket",
    "LocationEnforcement",
    "UserStatus",
    "VerificationFailure",
]


class ErrorReason(_OpenIntEnum):
    """The server's domain reason for an error, carried by :attr:`StatusError.reason`.

    The error tables in the README say which call sends which. A reason
    newer than this SDK is kept as ``UNKNOWN_<n>``.
    """

    UNSPECIFIED = 0
    USER_NOT_FOUND = 1
    USER_ALREADY_EXISTS = 2
    USER_LOCKED = 3
    MAX_USERS_REACHED = 4
    DEVICE_NOT_FOUND = 20
    MAX_DEVICES_REACHED = 21
    DEVICE_BANNED = 22
    CHALLENGE_NOT_FOUND = 40
    CHALLENGE_ALREADY_TERMINAL = 41
    NO_ACTIVE_DEVICE_FOR_USER = 42
    CHALLENGE_ALREADY_EXISTS = 43
    MIN_STRENGTH_REQUIRED = 44
    DEVICE_INCAPABLE = 45
    AUTH_STRENGTH_REQUIRED = 46
    AUTH_STRENGTH_INSUFFICIENT = 47
    CHALLENGE_TOO_SOON = 48
    TOTP_NOT_ENROLLED = 60
    TOTP_SECRET_KEY_UNAVAILABLE = 61
    TOTP_LOCKED = 62
    ENROLLMENT_INVITE_EXPIRED = 80
    ENROLLMENT_INVITE_ALREADY_EXISTS = 81
    RECOVERY_INVITE_ALREADY_EXISTS = 82
    LICENSE_USER_CAP_REACHED = 100
    LICENSE_EXPIRED = 101
    LICENSE_VIOLATED = 102
    RATE_LIMIT_EXCEEDED = 120
    MTLS_CERT_REFUSED = 140
    MTLS_CERT_EXPIRED = 141
    PERMISSION_DENIED = 142
    INVALID_ARGUMENT = 160
    NOT_IMPLEMENTED = 180
    SERVER_INTERNAL = 181
    SERVER_UNAVAILABLE = 182
    APP_VERSION_TOO_OLD = 200
