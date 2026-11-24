"""The exceptions the client raises.

A gRPC status, from the server or from the transport, becomes the
:class:`StatusError` subclass of its code. Three reasons narrow that class
further. A configuration that cannot be used raises :class:`ConfigurationError`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import grpc
from google.protobuf.message import DecodeError
from grpc_status import rpc_status

from ydentifi._enums import ErrorReason
from ydentifi._protogen.protos.identity import errors_pb2

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class YdentifiError(Exception):
    """The base class of every exception the client raises."""


class StatusError(YdentifiError):
    """A gRPC status, with the server's reason and details when the server sent them.

    Attributes:
        code: The gRPC status code.
        reason: The server's reason, or ``ErrorReason.UNSPECIFIED`` when the
            status carries none.
        message: The status message.
        trace_id: The call's W3C trace ID, or empty.
        field: The request field that failed a check, or empty.
        subject: What the call referred to, or empty.
        auto_expires_at: When a spent limit admits the call again, or ``None``.
    """

    # Every field is positional, so that pickle rebuilds the error from its args.
    def __init__(  # noqa: PLR0917
        self,
        code: grpc.StatusCode,
        reason: int,
        message: str,
        trace_id: str = "",
        field: str = "",
        subject: str = "",
        auto_expires_at: datetime | None = None,
    ) -> None:
        super().__init__(code, reason, message, trace_id, field, subject, auto_expires_at)
        self.code = code
        self.reason = ErrorReason(reason)
        self.message = message
        self.trace_id = trace_id
        self.field = field
        self.subject = subject
        self.auto_expires_at = auto_expires_at

    def __str__(self) -> str:
        if self.trace_id:
            return f"{self.message} (trace_id={self.trace_id})"
        return self.message


class NotFoundError(StatusError):
    """The user, device or challenge does not exist for the calling relying party.

    Another relying party's user, device or challenge gets the same answer.
    """


class AlreadyExistsError(StatusError):
    """What the call would create already exists, as on a retry with the same ``challenge_id``."""


class UnauthenticatedError(StatusError):
    """The certificate passed the TLS handshake, but the server refused it.

    The certificate names no relying party the server knows, or it expired
    after the connection opened. A certificate the handshake refuses raises
    :class:`UnavailableError` instead, since no gRPC status is sent.
    """


class PermissionDeniedError(StatusError):
    """The deployment's operator has disabled the relying party."""


class ResourceExhaustedError(StatusError):
    """A per-user limit is spent, or the relying party's user cap is reached.

    A spent limit has reason ``RATE_LIMIT_EXCEEDED``; the cap has reason
    ``MAX_USERS_REACHED``.
    """


class UnavailableError(StatusError):
    """The server could not be reached, the TLS handshake failed, or the server refuses every call.

    The server refuses every call while the deployment holds more users than
    its licence allows (``LICENSE_USER_CAP_REACHED``), or while it cannot read
    its own seat counts (``SERVER_UNAVAILABLE``).
    """


class InvalidArgumentError(StatusError):
    """A request field failed the server's checks; :attr:`StatusError.field` names it."""


class InternalError(StatusError):
    """The server failed; :attr:`StatusError.trace_id` finds the call in the server's logs."""


class AbortedError(StatusError):
    """A concurrent call held a lock too long; nothing changed, and a retry may succeed."""


class DeadlineExceededError(StatusError, TimeoutError):
    """The call ran past its deadline or past the server's own limit.

    It is also the builtin :class:`TimeoutError`.
    """


class CancelledError(StatusError):
    """The call was cancelled, or it was made after the client was closed.

    This is not :class:`asyncio.CancelledError`, which the cancellation of an
    asyncio task raises.
    """


class FailedPreconditionError(StatusError):
    """The call is valid, but the user or the deployment is not in a state that allows it."""


class DeviceLimitReachedError(FailedPreconditionError):
    """An enrollment invite was refused because the user already has three active devices."""


class ChallengeTooSoonError(ResourceExhaustedError):
    """A challenge was refused because the user's newest challenge is open and under 15 seconds old.

    The refusal spends no try. The call is admitted again at
    :attr:`StatusError.auto_expires_at`, or as soon as the open challenge ends.
    """


class TOTPLockedError(FailedPreconditionError):
    """The user's TOTP codes are locked after 100 wrong codes in a row.

    Only a new secret, issued by ``issue_user_totp_enrollment`` with
    ``reuse_existing=False``, unlocks them.
    """


class ConfigurationError(YdentifiError):
    """The client configuration is missing, cannot be read, or cannot be used."""


class MalformedResponseError(YdentifiError):
    """An answer of the server could not be read, such as a time that is not RFC 3339."""


_ERROR_BY_CODE: dict[grpc.StatusCode, type[StatusError]] = {
    grpc.StatusCode.NOT_FOUND: NotFoundError,
    grpc.StatusCode.ALREADY_EXISTS: AlreadyExistsError,
    grpc.StatusCode.UNAUTHENTICATED: UnauthenticatedError,
    grpc.StatusCode.PERMISSION_DENIED: PermissionDeniedError,
    grpc.StatusCode.RESOURCE_EXHAUSTED: ResourceExhaustedError,
    grpc.StatusCode.UNAVAILABLE: UnavailableError,
    grpc.StatusCode.INVALID_ARGUMENT: InvalidArgumentError,
    grpc.StatusCode.INTERNAL: InternalError,
    grpc.StatusCode.ABORTED: AbortedError,
    grpc.StatusCode.DEADLINE_EXCEEDED: DeadlineExceededError,
    grpc.StatusCode.CANCELLED: CancelledError,
    grpc.StatusCode.FAILED_PRECONDITION: FailedPreconditionError,
}

_ERROR_BY_REASON: dict[tuple[grpc.StatusCode, ErrorReason], type[StatusError]] = {
    (grpc.StatusCode.FAILED_PRECONDITION, ErrorReason.MAX_DEVICES_REACHED): DeviceLimitReachedError,
    (grpc.StatusCode.FAILED_PRECONDITION, ErrorReason.TOTP_LOCKED): TOTPLockedError,
    (grpc.StatusCode.RESOURCE_EXHAUSTED, ErrorReason.CHALLENGE_TOO_SOON): ChallengeTooSoonError,
}


def map_rpc_error(exc: grpc.RpcError) -> StatusError:
    """Returns the :class:`StatusError` for a gRPC error.

    The class follows the status code, and the reason narrows it under that
    code only. The server's ``ErrorDetail``, when the status carries one,
    supplies the reason, the trace ID, the field, the subject and the retry time.
    Details that cannot be read are ignored: details whose code or message
    differs from the status's, details that do not decode, and a retry time
    past the last :class:`~datetime.datetime`.
    """
    code: grpc.StatusCode = exc.code()  # type: ignore[attr-defined]
    message: str = exc.details() or ""  # type: ignore[attr-defined]
    try:
        detail = _error_detail(exc)
        retry_at = _retry_at(detail)
    except (ValueError, DecodeError, OverflowError):
        detail = None
    if detail is None:
        return _ERROR_BY_CODE.get(code, StatusError)(code, ErrorReason.UNSPECIFIED, message)
    reason = ErrorReason(detail.reason)
    cls = _ERROR_BY_REASON.get((code, reason)) or _ERROR_BY_CODE.get(code, StatusError)
    return cls(code, reason, message, detail.trace_id, detail.field, detail.subject, retry_at)


def _retry_at(detail: errors_pb2.ErrorDetail | None) -> datetime | None:
    """Returns the retry time of a detail, or ``None`` for a detail without one.

    Raises:
        OverflowError: The time is past the last :class:`~datetime.datetime`.
    """
    if detail is None or detail.auto_expires_at_unix_ms <= 0:
        return None
    return _EPOCH + timedelta(milliseconds=detail.auto_expires_at_unix_ms)


def _error_detail(exc: grpc.RpcError) -> errors_pb2.ErrorDetail | None:
    """Returns the first ``ErrorDetail`` of a status, or ``None`` for a status without one.

    A status from the server that carries details carries its ``ErrorDetail``
    first; a licence refusal adds a second detail after it. The first
    ``ErrorDetail`` is read wherever it stands, as the Go SDK reads it.
    """
    status = rpc_status.from_call(exc)  # type: ignore[arg-type]
    if status is None:
        return None
    for packed in status.details:
        out = errors_pb2.ErrorDetail()
        if packed.Unpack(out):
            return out
    return None
