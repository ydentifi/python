"""The exception classes: their hierarchy, their text and pickling."""

from __future__ import annotations

import datetime as dt
import pickle

import grpc
import pytest

import ydentifi
from ydentifi._protogen.protos.identity import errors_pb2

_STATUS_ERRORS = [
    ydentifi.NotFoundError,
    ydentifi.AlreadyExistsError,
    ydentifi.UnauthenticatedError,
    ydentifi.PermissionDeniedError,
    ydentifi.ResourceExhaustedError,
    ydentifi.ChallengeTooSoonError,
    ydentifi.UnavailableError,
    ydentifi.InvalidArgumentError,
    ydentifi.InternalError,
    ydentifi.AbortedError,
    ydentifi.DeadlineExceededError,
    ydentifi.CancelledError,
    ydentifi.FailedPreconditionError,
    ydentifi.DeviceLimitReachedError,
    ydentifi.TOTPLockedError,
]


@pytest.mark.parametrize("cls", _STATUS_ERRORS)
def test_py_007_every_status_error_survives_pickle(cls: type[ydentifi.StatusError]) -> None:
    err = cls(
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        ydentifi.ErrorReason.RATE_LIMIT_EXCEEDED,
        "spent",
        "4bf92f3577b34da6a3ce929d0e0e4736",
        "field",
        "subject",
        dt.datetime(2026, 1, 1, tzinfo=dt.UTC),
    )
    back = pickle.loads(pickle.dumps(err))
    assert type(back) is cls
    assert (back.code, back.reason, back.message, back.trace_id) == (
        err.code,
        err.reason,
        err.message,
        err.trace_id,
    )
    assert (back.field, back.subject, back.auto_expires_at) == (
        err.field,
        err.subject,
        err.auto_expires_at,
    )
    assert isinstance(back, ydentifi.YdentifiError)


def test_the_text_is_the_message_and_the_trace_id() -> None:
    err = ydentifi.NotFoundError(grpc.StatusCode.NOT_FOUND, 1, "no entity found")
    assert str(err) == "no entity found"
    traced = ydentifi.InternalError(grpc.StatusCode.INTERNAL, 0, "failed", "abc")
    assert str(traced) == "failed (trace_id=abc)"


def test_an_unavailable_error_with_no_reason_points_at_the_handshake() -> None:
    message = "failed to connect to all addresses; last error: Network is unreachable"
    err = ydentifi.UnavailableError(grpc.StatusCode.UNAVAILABLE, 0, message)
    assert err.message == message
    assert str(err) == (
        message + "; if the server is reachable, the TLS handshake may have failed: "
        "check the CA bundle, the server name and the client certificate"
    )
    refused = ydentifi.UnavailableError(
        grpc.StatusCode.UNAVAILABLE, ydentifi.ErrorReason.SERVER_UNAVAILABLE, "server unavailable"
    )
    assert str(refused) == "server unavailable"


def test_a_deadline_is_also_the_builtin_timeout_error() -> None:
    err = ydentifi.DeadlineExceededError(grpc.StatusCode.DEADLINE_EXCEEDED, 0, "Deadline Exceeded")
    assert isinstance(err, TimeoutError)
    assert isinstance(err, ydentifi.StatusError)


def test_sdk_070_the_reason_narrowed_classes_keep_their_code_class() -> None:
    assert issubclass(ydentifi.DeviceLimitReachedError, ydentifi.FailedPreconditionError)
    assert issubclass(ydentifi.TOTPLockedError, ydentifi.FailedPreconditionError)
    assert issubclass(ydentifi.ChallengeTooSoonError, ydentifi.ResourceExhaustedError)


def test_a_configuration_error_is_not_a_status() -> None:
    assert issubclass(ydentifi.ConfigurationError, ydentifi.YdentifiError)
    assert not issubclass(ydentifi.ConfigurationError, ydentifi.StatusError)


def test_the_reasons_are_the_protocols() -> None:
    protocol = {
        errors_pb2.ErrorReason.Name(v).removeprefix("ERROR_REASON_"): v
        for v in errors_pb2.ErrorReason.values()
    }
    assert {m.name: int(m) for m in ydentifi.ErrorReason} == protocol


def test_a_reason_newer_than_the_sdk_keeps_its_number() -> None:
    err = ydentifi.StatusError(grpc.StatusCode.UNKNOWN, 999, "newer")
    assert err.reason == 999
    assert err.reason.name == "UNKNOWN_999"
