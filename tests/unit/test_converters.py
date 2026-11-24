"""The request and result types, and their conversion to and from protocol messages."""

from __future__ import annotations

import dataclasses
import datetime as dt

import pytest

import ydentifi
from ydentifi import _converters as convert
from ydentifi._protogen.protos.identity import identity_pb2
from ydentifi._protogen.protos.identity import identity_service_pb2 as pb


def test_a_request_is_frozen_and_keyword_only() -> None:
    req = ydentifi.IssueAuthChallengeRequest(
        opaque_id="a" * 64,
        context=b"x" * 16,
        min_strength=ydentifi.AuthStrength.BIOMETRIC,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.ttl_seconds = 30  # type: ignore[misc]
    with pytest.raises(TypeError):
        ydentifi.IssueEnrollmentInviteRequest("a" * 64)  # type: ignore[misc]


def test_a_challenge_request_needs_its_text_and_strength() -> None:
    with pytest.raises(TypeError):
        ydentifi.IssueAuthChallengeRequest(opaque_id="a" * 64)  # type: ignore[call-arg]


def test_a_challenge_request_carries_every_field() -> None:
    req = ydentifi.IssueAuthChallengeRequest(
        opaque_id="a" * 64,
        context=b"Approve the transfer",
        min_strength=ydentifi.AuthStrength.BIOMETRIC,
        ttl_seconds=120,
        location_constraint=ydentifi.LocationConstraint(
            latitude=42.7,
            longitude=23.3,
            radius_meters=500,
            enforcement=ydentifi.LocationEnforcement.REQUIRED,
        ),
        match_code=42,
        challenge_id="01JD0000000000000000000000",
    )
    out = convert.auth_challenge_request(req)
    assert out == pb.IssueAuthChallengeRequest(
        opaque_id="a" * 64,
        context=b"Approve the transfer",
        min_strength=identity_pb2.AUTH_STRENGTH_BIOMETRIC,
        ttl_seconds=120,
        location_constraint=identity_pb2.LocationConstraint(
            latitude=42.7,
            longitude=23.3,
            radius_m=500,
            enforcement=identity_pb2.LOCATION_ENFORCEMENT_REQUIRED,
        ),
        match_code=42,
        challenge_id="01JD0000000000000000000000",
    )
    assert not convert.auth_challenge_request(
        dataclasses.replace(req, location_constraint=None),
    ).HasField("location_constraint")


def test_a_user_reads_its_times_and_leaves_absent_ones_none() -> None:
    u = convert.user(
        pb.GetUserResponse(
            opaque_id="a" * 64,
            status=identity_pb2.USER_STATUS_LOCKED,
            created_at="2026-11-16T10:00:00Z",
            last_activity_at="2026-11-16T00:00:00Z",
            totp_locked=True,
        ),
    )
    assert u == ydentifi.User(
        opaque_id="a" * 64,
        status=ydentifi.UserStatus.LOCKED,
        created_at=dt.datetime(2026, 11, 16, 10, tzinfo=dt.UTC),
        last_authenticated_at=None,
        last_activity_at=dt.datetime(2026, 11, 16, tzinfo=dt.UTC),
        totp_locked=True,
    )


def test_a_frame_has_a_location_result_only_when_the_phone_reported_one() -> None:
    bare = convert.challenge_result(
        pb.AwaitChallengeFrame(status=identity_pb2.AUTH_CHALLENGE_STATUS_PENDING)
    )
    assert bare.location_result is None
    assert bare.emitted_at is None
    reported = convert.challenge_result(
        pb.AwaitChallengeFrame(
            status=identity_pb2.AUTH_CHALLENGE_STATUS_APPROVED,
            location_result=identity_pb2.LocationResult(
                bucket=identity_pb2.LOCATION_BUCKET_NEAR,
                accuracy=identity_pb2.LOCATION_ACCURACY_HIGH,
            ),
            emitted_at="2026-11-16T10:00:00.123456789Z",
        ),
    )
    assert reported.location_result == ydentifi.LocationResult(
        bucket=ydentifi.LocationBucket.NEAR,
        accuracy=ydentifi.LocationAccuracy.HIGH,
    )
    assert reported.emitted_at == dt.datetime(2026, 11, 16, 10, 0, 0, 123456, tzinfo=dt.UTC)


def test_a_frames_repr_leaves_out_the_signature() -> None:
    frame = ydentifi.ChallengeResult(
        status=ydentifi.ChallengeStatus.APPROVED, signature=b"\x01" * 3309
    )
    assert "signature" not in repr(frame)
    assert frame.signature == b"\x01" * 3309


def test_an_enum_value_newer_than_the_sdk_keeps_its_number() -> None:
    status = ydentifi.ChallengeStatus(42)
    assert status == 42
    assert status.name == "UNKNOWN_42"
    assert not status.is_terminal


def test_an_enum_refuses_a_value_that_is_not_a_number() -> None:
    with pytest.raises(ValueError, match="is not a valid ChallengeStatus"):
        ydentifi.ChallengeStatus("APPROVED")  # type: ignore[arg-type]
