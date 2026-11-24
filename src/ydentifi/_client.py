"""The synchronous client."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable, Generator
from typing import Any

import grpc

from ydentifi import _converters as convert
from ydentifi._cert_files import CertFiles
from ydentifi._config import resolve
from ydentifi._enums import ErrorReason, UserStatus
from ydentifi._errors import CancelledError, map_rpc_error
from ydentifi._protogen.protos.identity import identity_service_pb2 as pb
from ydentifi._protogen.protos.identity import identity_service_pb2_grpc as pb_grpc
from ydentifi._types import (
    ActiveChallenge,
    Challenge,
    ChallengeResult,
    Device,
    EnrollmentInvite,
    IssueAuthChallengeRequest,
    IssueEnrollmentInviteRequest,
    IssueRecoveryInviteRequest,
    RecoveryInvite,
    TOTPEnrollment,
    User,
)

DEFAULT_TIMEOUT = 30.0
"""The seconds a call that is not a stream waits by default: the server's own limit."""


def _closed_error() -> CancelledError:
    """The error a call on a closed client ends with."""
    return CancelledError(
        grpc.StatusCode.CANCELLED, ErrorReason.UNSPECIFIED, "the client is closed"
    )


class Client:
    """The synchronous client.

    One instance is shared by any number of threads; one gRPC channel
    carries every call. Every method takes a keyword-only ``timeout`` in
    seconds: 30 by default for a call that is not a stream, none for a
    stream, and ``None`` for no limit.

    The streaming methods are generators. Each one starts its call at its
    first iteration and ends it when the generator is exhausted or closed,
    as by :func:`contextlib.closing`.

    A certificate given as files is read again at most once a minute, by the
    next call. A new pair inside its validity dates is presented on a new
    channel from that call on; the channel it replaces stays open, for the
    calls in flight on it, until :meth:`Client.close`.
    """

    def __init__(
        self,
        *,
        server_addr: str | None = None,
        server_name: str | None = None,
        cert_path: str | os.PathLike[str] | None = None,
        key_path: str | os.PathLike[str] | None = None,
        cert_pem: bytes | None = None,
        key_pem: bytes | None = None,
        ca_path: str | os.PathLike[str] | None = None,
        ca_pem: bytes | None = None,
        user_agent: str | None = None,
        keepalive_time_seconds: int | None = None,
        keepalive_timeout_seconds: int | None = None,
        channel_options: list[tuple[str, str | int]] | None = None,
    ) -> None:
        cfg = resolve(
            server_addr=server_addr,
            server_name=server_name,
            cert_path=cert_path,
            key_path=key_path,
            cert_pem=cert_pem,
            key_pem=key_pem,
            ca_path=ca_path,
            ca_pem=ca_pem,
            user_agent=user_agent,
            keepalive_time_seconds=keepalive_time_seconds,
            keepalive_timeout_seconds=keepalive_timeout_seconds,
            channel_options=channel_options,
        )
        self._target, self._options, self._ca_pem = cfg.target, cfg.options, cfg.ca_pem
        self._certs = None
        if cfg.cert_path:
            self._certs = CertFiles(cfg.cert_path, cfg.key_path, cfg.cert_pem)
        self._channel = self._open(cfg.cert_pem, cfg.key_pem)
        self._stub = pb_grpc.IdentityServiceStub(self._channel)
        self._old_channels: list[grpc.Channel] = []
        self._closed = False
        # Guards the channels, the stub, the closed flag and the certificate check.
        self._lock = threading.Lock()

    def close(self) -> None:
        """Closes the client's channels; calls still in flight end with :class:`CancelledError`."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            channels = [self._channel, *self._old_channels]
        for channel in channels:
            channel.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def create_user(self, *, timeout: float | None = DEFAULT_TIMEOUT) -> str:
        """Creates an anonymous user and returns its opaque ID."""
        resp = self._invoke(self._service().CreateUser, pb.CreateUserRequest(), timeout)
        return resp.opaque_id

    def bulk_create_users(
        self,
        count: int,
        idempotency_key: str,
        *,
        timeout: float | None = None,
    ) -> Generator[str, None, None]:
        """Creates up to ``count`` users under an idempotency key and yields their opaque IDs.

        A call again with the same key first yields the users the key already
        created, then creates the rest. When the relying party's user cap is
        reached, the iteration ends with fewer than ``count`` IDs.
        """
        request = pb.BulkCreateUsersRequest(count=count, idempotency_key=idempotency_key)
        call = self._invoke(self._service().BulkCreateUsers, request, timeout)
        try:
            # The summary frame that ends the stream carries no chunk.
            for frame in call:
                yield from frame.chunk.opaque_ids
        except grpc.RpcError as exc:
            raise map_rpc_error(exc) from exc
        finally:
            call.cancel()

    def get_user(self, opaque_id: str, *, timeout: float | None = DEFAULT_TIMEOUT) -> User:
        """Returns one user."""
        request = pb.GetUserRequest(opaque_id=opaque_id)
        resp = self._invoke(self._service().GetUser, request, timeout)
        return convert.user(resp)

    def export_users(
        self,
        start_after_id: str = "",
        *,
        timeout: float | None = None,
    ) -> Generator[User, None, None]:
        """Yields every user of the relying party, after ``start_after_id`` when it is given."""
        request = pb.ExportUsersRequest(start_after_user_id=start_after_id)
        call = self._invoke(self._service().ExportUsers, request, timeout)
        try:
            for page in call:
                for u in page.users:
                    yield convert.user(u)
        except grpc.RpcError as exc:
            raise map_rpc_error(exc) from exc
        finally:
            call.cancel()

    def update_user_status(
        self,
        opaque_id: str,
        status: UserStatus,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> None:
        """Locks a user (``UserStatus.LOCKED``) or unlocks one (``UserStatus.ACTIVE``)."""
        request = convert.update_user_status_request(opaque_id, status)
        self._invoke(self._service().UpdateUserStatus, request, timeout)

    def delete_user(self, opaque_id: str, *, timeout: float | None = DEFAULT_TIMEOUT) -> None:
        """Deletes a user with the user's devices and challenges; the user's bans stay."""
        self._invoke(self._service().DeleteUser, pb.DeleteUserRequest(opaque_id=opaque_id), timeout)

    def unlock_user_request_limits(
        self,
        opaque_id: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> None:
        """Gives a user back every try of every per-user limit."""
        request = pb.UnlockUserRequestLimitsRequest(opaque_id=opaque_id)
        self._invoke(self._service().UnlockUserRequestLimits, request, timeout)

    def list_devices_for_user(
        self,
        opaque_id: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> list[Device]:
        """Returns the user's devices in every status: active, inactive and banned."""
        request = pb.ListDevicesForUserRequest(opaque_id=opaque_id)
        resp = self._invoke(self._service().ListDevicesForUser, request, timeout)
        return [convert.device(d) for d in resp.devices]

    def revoke_device(
        self,
        opaque_id: str,
        device_id: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> None:
        """Revokes one device; the user's TOTP secret is not replaced."""
        request = pb.RevokeDeviceRequest(opaque_id=opaque_id, device_id=device_id)
        self._invoke(self._service().RevokeDevice, request, timeout)

    def ban_device(
        self,
        opaque_id: str,
        device_id: str,
        reason: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> int:
        """Bans the phone behind a device from the relying party.

        Returns how many active devices on that phone the ban moved to
        ``BANNED``: 0 or 1.
        """
        request = pb.BanDeviceRequest(opaque_id=opaque_id, device_id=device_id, reason=reason)
        return self._invoke(self._service().BanDevice, request, timeout).cascaded_device_count

    def unban_device(
        self,
        opaque_id: str,
        *,
        device_id: str = "",
        permanent_id: str = "",
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> None:
        """Lifts the ban on a phone, named by one of its device IDs or by its permanent ID.

        Exactly one of ``device_id`` and ``permanent_id`` is to be given; the
        server refuses both and neither.
        """
        request = pb.UnbanDeviceRequest(
            opaque_id=opaque_id,
            device_id=device_id,
            permanent_id=permanent_id,
        )
        self._invoke(self._service().UnbanDevice, request, timeout)

    def issue_auth_challenge(
        self,
        req: IssueAuthChallengeRequest,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> Challenge:
        """Issues a challenge to the user's phones."""
        request = convert.auth_challenge_request(req)
        return convert.challenge(self._invoke(self._service().IssueAuthChallenge, request, timeout))

    def await_challenge(
        self,
        challenge_id: str,
        *,
        timeout: float | None = None,
    ) -> Generator[ChallengeResult, None, None]:
        """Yields the frames of a challenge until the server ends the stream.

        The first frame is the challenge's state when the stream opens. The
        last frame is the first terminal one (``ChallengeStatus.is_terminal``),
        after which the server ends the stream.
        """
        request = pb.AwaitChallengeRequest(challenge_id=challenge_id)
        call = self._invoke(self._service().AwaitChallenge, request, timeout)
        try:
            for frame in call:
                yield convert.challenge_result(frame)
        except grpc.RpcError as exc:
            raise map_rpc_error(exc) from exc
        finally:
            call.cancel()

    def list_active_challenges(
        self,
        opaque_id: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> list[ActiveChallenge]:
        """Returns the user's open challenges: those pending or delivered, not yet ended."""
        request = pb.ListActiveChallengesRequest(opaque_id=opaque_id)
        resp = self._invoke(self._service().ListActiveChallenges, request, timeout)
        return [convert.active_challenge(s) for s in resp.challenges]

    def issue_user_totp_enrollment(
        self,
        opaque_id: str,
        *,
        reuse_existing: bool,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> TOTPEnrollment:
        """Returns the user's TOTP secret, or replaces it when ``reuse_existing`` is false."""
        request = pb.IssueUserTotpEnrollmentRequest(
            opaque_id=opaque_id,
            reuse_existing=reuse_existing,
        )
        resp = self._invoke(self._service().IssueUserTotpEnrollment, request, timeout)
        return convert.totp_enrollment(resp)

    def verify_user_totp(
        self,
        opaque_id: str,
        code: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> bool:
        """Returns whether a TOTP code is right; a code already accepted is not."""
        request = pb.VerifyUserTotpRequest(opaque_id=opaque_id, totp_code=code)
        return self._invoke(self._service().VerifyUserTotp, request, timeout).valid

    def issue_enrollment_invite(
        self,
        req: IssueEnrollmentInviteRequest,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> EnrollmentInvite:
        """Issues an invite to enroll a phone, revoking the user's previous invite."""
        request = convert.enrollment_invite_request(req)
        resp = self._invoke(self._service().IssueEnrollmentInvite, request, timeout)
        return convert.enrollment_invite(resp)

    def issue_recovery_invite(
        self,
        req: IssueRecoveryInviteRequest,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> RecoveryInvite:
        """Revokes every active device of the user and issues an invite to enroll a new phone."""
        request = convert.recovery_invite_request(req)
        resp = self._invoke(self._service().IssueRecoveryInvite, request, timeout)
        return convert.recovery_invite(resp)

    def _service(self) -> pb_grpc.IdentityServiceStub:
        """Returns the stub for a call, first moving to a renewed certificate when one is due.

        Raises:
            CancelledError: The client is closed.
        """
        with self._lock:
            if self._closed:
                raise _closed_error()
            if self._certs is not None and self._certs.due():
                pair = self._certs.read()
                if pair is not None:
                    self._old_channels.append(self._channel)
                    self._channel = self._open(*pair)
                    self._stub = pb_grpc.IdentityServiceStub(self._channel)
                    self._certs.cert_pem = pair[0]
            return self._stub

    def _invoke(self, rpc: Callable[..., Any], request: object, timeout: float | None) -> Any:
        """Starts one call and returns a unary call's response or a stream's call.

        A call may be given its stub before :meth:`Client.close` and start
        after it, on a closed channel, which gRPC refuses with ``ValueError``.

        Raises:
            StatusError: The call ended with a gRPC error.
            CancelledError: The client was closed before the call started.
        """
        try:
            return rpc(request, timeout=timeout)
        except grpc.RpcError as exc:
            raise map_rpc_error(exc) from exc
        except ValueError:
            with self._lock:
                closed = self._closed
            if closed:
                raise _closed_error() from None
            raise

    def _open(self, cert_pem: bytes, key_pem: bytes) -> grpc.Channel:
        """Returns a new channel that presents the certificate."""
        creds = grpc.ssl_channel_credentials(self._ca_pem, key_pem, cert_pem)
        return grpc.secure_channel(self._target, creds, options=self._options)
