"""The Python client of the Ydentifi identity server.

A relying party creates anonymous users, enrolls their phones and asks them
to approve sign-ins and actions, over gRPC with mutual TLS::

    import ydentifi

    with ydentifi.Client(
        server_addr="auth.example.com:443",
        cert_path="/etc/ydentifi/rp.crt",
        key_path="/etc/ydentifi/rp.key",
    ) as client:
        opaque_id = client.create_user()

:class:`Client` is synchronous; :class:`AsyncClient` has the same methods
under asyncio. The README holds the reference of every method.
"""

from __future__ import annotations

from ydentifi._async_client import AsyncClient
from ydentifi._client import Client
from ydentifi._enums import (
    AuthStrength,
    ChallengeExpression,
    ChallengeStatus,
    DeclineReason,
    DevicePlatform,
    DeviceStatus,
    ErrorReason,
    LocationAccuracy,
    LocationBucket,
    LocationEnforcement,
    UserStatus,
    VerificationFailure,
)
from ydentifi._errors import (
    AbortedError,
    AlreadyExistsError,
    CancelledError,
    ChallengeTooSoonError,
    ConfigurationError,
    DeadlineExceededError,
    DeviceLimitReachedError,
    FailedPreconditionError,
    InternalError,
    InvalidArgumentError,
    MalformedResponseError,
    NotFoundError,
    PermissionDeniedError,
    ResourceExhaustedError,
    StatusError,
    TOTPLockedError,
    UnauthenticatedError,
    UnavailableError,
    YdentifiError,
)
from ydentifi._types import (
    ActiveChallenge,
    Challenge,
    ChallengeResult,
    Device,
    EnrollmentInvite,
    IssueAuthChallengeRequest,
    IssueEnrollmentInviteRequest,
    IssueRecoveryInviteRequest,
    LocationConstraint,
    LocationResult,
    RecoveryInvite,
    TOTPEnrollment,
    User,
)
from ydentifi._version import __version__

__all__ = [
    "AbortedError",
    "ActiveChallenge",
    "AlreadyExistsError",
    "AsyncClient",
    "AuthStrength",
    "CancelledError",
    "Challenge",
    "ChallengeExpression",
    "ChallengeResult",
    "ChallengeStatus",
    "ChallengeTooSoonError",
    "Client",
    "ConfigurationError",
    "DeadlineExceededError",
    "DeclineReason",
    "Device",
    "DeviceLimitReachedError",
    "DevicePlatform",
    "DeviceStatus",
    "EnrollmentInvite",
    "ErrorReason",
    "FailedPreconditionError",
    "InternalError",
    "InvalidArgumentError",
    "IssueAuthChallengeRequest",
    "IssueEnrollmentInviteRequest",
    "IssueRecoveryInviteRequest",
    "LocationAccuracy",
    "LocationBucket",
    "LocationConstraint",
    "LocationEnforcement",
    "LocationResult",
    "MalformedResponseError",
    "NotFoundError",
    "PermissionDeniedError",
    "RecoveryInvite",
    "ResourceExhaustedError",
    "StatusError",
    "TOTPEnrollment",
    "TOTPLockedError",
    "UnauthenticatedError",
    "UnavailableError",
    "User",
    "UserStatus",
    "VerificationFailure",
    "YdentifiError",
    "__version__",
]
