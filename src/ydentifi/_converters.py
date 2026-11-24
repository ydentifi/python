"""Conversion between the protocol messages and the public types.

Both clients build their requests and read their responses through these
functions.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import cast

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
from ydentifi._errors import MalformedResponseError
from ydentifi._protogen.protos.identity import identity_pb2
from ydentifi._protogen.protos.identity import identity_service_pb2 as pb
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

# An RFC 3339 date and time, its "T" and its offset required.
# datetime.fromisoformat alone also takes a date alone, a time without an
# offset, an offset without its colon, and the basic format.
_RFC3339 = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})"
)


def _required_time(field: str, s: str) -> datetime:
    """Returns an RFC 3339 time of the server's answer.

    Raises:
        MalformedResponseError: ``s`` is not an RFC 3339 time.
    """
    error = MalformedResponseError(f"{field}: {s!r} is not an RFC 3339 time")
    if not _RFC3339.fullmatch(s):
        raise error
    try:
        return datetime.fromisoformat(s)
    except ValueError as e:
        raise error from e


def _time(field: str, s: str) -> datetime | None:
    """Returns an RFC 3339 time, or ``None`` for the empty string the server sends for no time."""
    return _required_time(field, s) if s else None


def update_user_status_request(opaque_id: str, status: UserStatus) -> pb.UpdateUserStatusRequest:
    """Returns the protocol request of ``update_user_status``."""
    # Each public enum holds the protocol enum's numbers; the casts say so to
    # the type checker.
    return pb.UpdateUserStatusRequest(
        opaque_id=opaque_id,
        status=cast("identity_pb2.UserStatus", status),
    )


def auth_challenge_request(req: IssueAuthChallengeRequest) -> pb.IssueAuthChallengeRequest:
    """Returns the protocol request of ``issue_auth_challenge``."""
    lc = req.location_constraint
    constraint = None
    if lc is not None:
        constraint = identity_pb2.LocationConstraint(
            latitude=lc.latitude,
            longitude=lc.longitude,
            radius_m=lc.radius_meters,
            enforcement=cast("identity_pb2.LocationEnforcement", lc.enforcement),
        )
    return pb.IssueAuthChallengeRequest(
        opaque_id=req.opaque_id,
        context=req.context,
        min_strength=cast("identity_pb2.AuthStrength", req.min_strength),
        ttl_seconds=req.ttl_seconds,
        location_constraint=constraint,
        match_code=req.match_code,
        challenge_id=req.challenge_id,
    )


def enrollment_invite_request(
    req: IssueEnrollmentInviteRequest,
) -> pb.IssueEnrollmentInviteRequest:
    """Returns the protocol request of ``issue_enrollment_invite``."""
    return pb.IssueEnrollmentInviteRequest(
        opaque_id=req.opaque_id,
        ttl_seconds=req.ttl_seconds,
        context=req.context,
    )


def recovery_invite_request(req: IssueRecoveryInviteRequest) -> pb.IssueRecoveryInviteRequest:
    """Returns the protocol request of ``issue_recovery_invite``."""
    return pb.IssueRecoveryInviteRequest(
        opaque_id=req.opaque_id,
        ttl_seconds=req.ttl_seconds,
        context=req.context,
    )


def user(r: pb.GetUserResponse) -> User:
    """Returns the :class:`User` a response or an export page carries."""
    return User(
        opaque_id=r.opaque_id,
        status=UserStatus(r.status),
        created_at=_required_time("created_at", r.created_at),
        last_authenticated_at=_time("last_authenticated_at", r.last_authenticated_at),
        last_activity_at=_time("last_activity_at", r.last_activity_at),
        totp_locked=r.totp_locked,
    )


def device(d: pb.DeviceSummary) -> Device:
    """Returns the :class:`Device` of a device summary."""
    return Device(
        device_id=d.device_id,
        permanent_id=d.permanent_id,
        platform=DevicePlatform(d.platform),
        status=DeviceStatus(d.status),
        created_at=_required_time("created_at", d.created_at),
        last_authenticated_at=_time("last_authenticated_at", d.last_authenticated_at),
        name=d.name,
        model=d.device_model,
    )


def challenge(r: pb.IssueAuthChallengeResponse) -> Challenge:
    """Returns the :class:`Challenge` an issued challenge's response carries."""
    return Challenge(
        challenge_id=r.challenge_id,
        qr_encoded=r.qr_encoded,
        expires_at=_required_time("expires_at", r.expires_at),
    )


def challenge_result(f: pb.AwaitChallengeFrame) -> ChallengeResult:
    """Returns the :class:`ChallengeResult` of one challenge frame."""
    location = None
    if f.HasField("location_result"):
        location = LocationResult(
            bucket=LocationBucket(f.location_result.bucket),
            accuracy=LocationAccuracy(f.location_result.accuracy),
        )
    return ChallengeResult(
        status=ChallengeStatus(f.status),
        expression=ChallengeExpression(f.expression),
        signature=f.signature,
        decline_reason=DeclineReason(f.decline_reason),
        verification_failure=VerificationFailure(f.verification_failure),
        location_result=location,
        emitted_at=_time("emitted_at", f.emitted_at),
        auth_strength=AuthStrength(f.auth_strength),
    )


def active_challenge(s: pb.ActiveChallengeSummary) -> ActiveChallenge:
    """Returns the :class:`ActiveChallenge` of an open challenge's summary."""
    constraint = None
    if s.HasField("location_constraint"):
        lc = s.location_constraint
        constraint = LocationConstraint(
            latitude=lc.latitude,
            longitude=lc.longitude,
            radius_meters=lc.radius_m,
            enforcement=LocationEnforcement(lc.enforcement),
        )
    return ActiveChallenge(
        challenge_id=s.challenge_id,
        status=ChallengeStatus(s.status),
        context=s.context,
        location_constraint=constraint,
        issued_at=_required_time("issued_at", s.issued_at),
        expires_at=_required_time("expires_at", s.expires_at),
        delivered_at=_time("delivered_at", s.delivered_at),
    )


def totp_enrollment(r: pb.IssueUserTotpEnrollmentResponse) -> TOTPEnrollment:
    """Returns the :class:`TOTPEnrollment` of a TOTP enrollment's response."""
    return TOTPEnrollment(
        qr_code_png_base64=r.qr_code_png_base64,
        totp_url=r.totp_url,
        secret_base32=r.secret_base32,
    )


def enrollment_invite(r: pb.IssueEnrollmentInviteResponse) -> EnrollmentInvite:
    """Returns the :class:`EnrollmentInvite` of an enrollment invite's response."""
    return EnrollmentInvite(
        invite_token=r.invite_token,
        qr_payload=r.qr_payload,
        expires_at=_required_time("expires_at", r.expires_at),
    )


def recovery_invite(r: pb.IssueRecoveryInviteResponse) -> RecoveryInvite:
    """Returns the :class:`RecoveryInvite` of a recovery invite's response."""
    return RecoveryInvite(
        invite_token=r.invite_token,
        qr_payload=r.qr_payload,
        expires_at=_required_time("expires_at", r.expires_at),
        revoked_device_count=r.revoked_device_count,
    )
