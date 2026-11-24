"""The request and result types.

Each is a frozen dataclass. Times are timezone-aware ``datetime`` values in UTC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ydentifi._enums import (
    AuthStrength,
    ChallengeExpression,
    ChallengeStatus,
    DeclineReason,
    DevicePlatform,
    DeviceStatus,
    LocationAccuracy,
    LocationBucket,
    LocationEnforcement,
    UserStatus,
    VerificationFailure,
)


@dataclass(frozen=True, slots=True)
class User:
    """An anonymous user of the calling relying party.

    Attributes:
        opaque_id: The user's ID: 64 lowercase hex characters.
        status: ``ACTIVE`` or ``LOCKED``.
        created_at: When the user was created.
        last_authenticated_at: The UTC day, at midnight, of the user's last
            approved challenge, or ``None``.
        last_activity_at: The UTC day, at midnight, of the user's last
            activity, or ``None``.
        totp_locked: Whether the user's TOTP codes are locked after 100 wrong
            codes in a row. ``status`` is not changed by the lock.
    """

    opaque_id: str
    status: UserStatus
    created_at: datetime
    last_authenticated_at: datetime | None = None
    last_activity_at: datetime | None = None
    totp_locked: bool = False


@dataclass(frozen=True, slots=True)
class Device:
    """An enrolled phone.

    Attributes:
        device_id: One enrollment of one phone, a UUID.
        permanent_id: The phone itself, the same under every relying party
            and every deployment. Relying parties that compare their lists
            can link one phone's users.
        platform: ``IOS`` or ``ANDROID``.
        status: ``ACTIVE``, ``INACTIVE`` or ``BANNED``.
        created_at: When the phone was enrolled.
        last_authenticated_at: The UTC day, at midnight, of the device's last
            approval, or ``None``.
        name: The device's display name, or empty.
        model: The hardware model the phone declared at enrollment, or empty.
            The server does not check it.
    """

    device_id: str
    permanent_id: str
    platform: DevicePlatform
    status: DeviceStatus
    created_at: datetime
    last_authenticated_at: datetime | None = None
    name: str = ""
    model: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class LocationConstraint:
    """A geofence the phone evaluates itself.

    The phone reports only a :class:`LocationBucket` and a
    :class:`LocationAccuracy`, never coordinates.

    Attributes:
        latitude: The centre's latitude, in degrees: -90 to 90.
        longitude: The centre's longitude, in degrees: -180 to 180.
        radius_meters: The radius, in metres: 50 to 500,000.
        enforcement: ``ADVISORY`` reports the result only; ``REQUIRED`` turns
            an approval from outside the radius into ``REJECTED`` with
            ``LOCATION_MISMATCH``.
    """

    latitude: float
    longitude: float
    radius_meters: int
    enforcement: LocationEnforcement


@dataclass(frozen=True, slots=True)
class LocationResult:
    """The phone's evaluation of a :class:`LocationConstraint`.

    Attributes:
        bucket: Where the phone was, relative to the radius.
        accuracy: How precise the phone's own fix was.
    """

    bucket: LocationBucket
    accuracy: LocationAccuracy


@dataclass(frozen=True, slots=True)
class EnrollmentInvite:
    """An invite to enroll a phone, shown as a QR code.

    ``invite_token`` and ``qr_payload`` are secrets: they enroll a phone for
    the user. ``repr`` leaves them out.

    Attributes:
        invite_token: The invite's token, for a deep link.
        qr_payload: The invite, to be rendered as a QR code exactly as given.
        expires_at: When the invite stops working.
    """

    invite_token: bytes = field(repr=False)
    qr_payload: bytes = field(repr=False)
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RecoveryInvite:
    """An :class:`EnrollmentInvite` that also says how many devices the call revoked.

    Attributes:
        invite_token: The invite's token, for a deep link. Left out of ``repr``.
        qr_payload: The invite, to be rendered as a QR code exactly as given.
            Left out of ``repr``.
        expires_at: When the invite stops working.
        revoked_device_count: How many active devices the call revoked.
    """

    invite_token: bytes = field(repr=False)
    qr_payload: bytes = field(repr=False)
    expires_at: datetime
    revoked_device_count: int


@dataclass(frozen=True, slots=True)
class Challenge:
    """A challenge ``issue_auth_challenge`` issued.

    Attributes:
        challenge_id: The challenge's ID, a 26-character ULID.
        qr_encoded: A link to the challenge, to be rendered as a QR code
            exactly as given.
        expires_at: When the challenge expires unanswered.
    """

    challenge_id: str
    qr_encoded: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ChallengeResult:
    """One frame of a challenge: its state when the frame was sent.

    Only ``APPROVED`` lets anyone in. ``expression`` records what the user
    answered, apart from the checks that followed.

    Attributes:
        status: The challenge's state.
        expression: The user's answer.
        signature: The phone's signature over the challenge, set on
            ``APPROVED``, ``DENIED`` and ``REJECTED``. The server checked it;
            no call returns the phone's key.
        decline_reason: The reason the user gave, set only on ``DENIED``.
        verification_failure: The check that refused an approval, set only
            on ``REJECTED``.
        location_result: The phone's evaluation of the geofence, set only
            when the phone reported one.
        emitted_at: When the server sent the frame.
        auth_strength: The unlock the phone used, set when the phone
            answered and ``UNSPECIFIED`` otherwise. It meets the challenge's
            ``min_strength`` only on ``APPROVED``.
    """

    status: ChallengeStatus
    expression: ChallengeExpression = ChallengeExpression.UNSPECIFIED
    signature: bytes = field(default=b"", repr=False)
    decline_reason: DeclineReason = DeclineReason.UNSPECIFIED
    verification_failure: VerificationFailure = VerificationFailure.UNSPECIFIED
    location_result: LocationResult | None = None
    emitted_at: datetime | None = None
    auth_strength: AuthStrength = AuthStrength.UNSPECIFIED


@dataclass(frozen=True, slots=True)
class ActiveChallenge:
    """A challenge that is still open.

    Attributes:
        challenge_id: The challenge's ID.
        status: ``PENDING`` or ``DELIVERED``.
        context: The challenge text, as issued.
        location_constraint: The challenge's geofence, or ``None``.
        issued_at: When the challenge was issued.
        expires_at: When it expires unanswered.
        delivered_at: When a phone first received it, or ``None``.
    """

    challenge_id: str
    status: ChallengeStatus
    context: bytes
    location_constraint: LocationConstraint | None
    issued_at: datetime
    expires_at: datetime
    delivered_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TOTPEnrollment:
    """A user's TOTP secret, in three forms.

    Each field carries the secret, so ``repr`` leaves all three out.

    Attributes:
        qr_code_png_base64: ``totp_url`` as a 255 by 255 pixel QR code, a
            base64 PNG, for an authenticator app to scan.
        totp_url: The ``otpauth://totp/`` URL. Its label may be changed, for
            example to show the user's name.
        secret_base32: The secret in base32, for manual entry.
    """

    qr_code_png_base64: str = field(repr=False)
    totp_url: str = field(repr=False)
    secret_base32: str = field(repr=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class IssueAuthChallengeRequest:
    """What ``issue_auth_challenge`` sends.

    Attributes:
        opaque_id: The user.
        context: What the user is asked to approve: 16 to 256 bytes of UTF-8
            text, which the phone shows and the user's signature covers.
        min_strength: The weakest unlock an approval may use.
            ``AuthStrength.UNSPECIFIED`` is refused.
        ttl_seconds: How long the challenge stays open: 30 to 300 seconds;
            ``0`` means 60.
        location_constraint: An optional geofence.
        match_code: An optional number from 10 to 99 that the user types on
            the phone; ``0`` turns number matching off.
        challenge_id: An optional ULID chosen before the call. When it is
            empty, the server creates the ID.
    """

    opaque_id: str
    context: bytes
    min_strength: AuthStrength
    ttl_seconds: int = 0
    location_constraint: LocationConstraint | None = None
    match_code: int = 0
    challenge_id: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class IssueEnrollmentInviteRequest:
    """What ``issue_enrollment_invite`` sends.

    Attributes:
        opaque_id: The user.
        ttl_seconds: How long the invite can be scanned: 60 to 600 seconds;
            ``0`` means 300.
        context: A note kept with the invite, at most 256 bytes. The phone
            does not show it.
    """

    opaque_id: str
    ttl_seconds: int = 0
    context: bytes = b""


@dataclass(frozen=True, slots=True, kw_only=True)
class IssueRecoveryInviteRequest:
    """What ``issue_recovery_invite`` sends.

    Attributes:
        opaque_id: The user.
        ttl_seconds: How long the invite can be scanned: 60 to 600 seconds;
            ``0`` means 300.
        context: A note kept with the invite, at most 256 bytes. The phone
            does not show it.
    """

    opaque_id: str
    ttl_seconds: int = 0
    context: bytes = b""
