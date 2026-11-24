"""The asyncio client.

A grpc.aio call holds its channel's connection open, after ``close()``,
for as long as the call itself is referenced. The client therefore leaves
no reference to a call behind it:

- Streams are read with ``call.read()`` until ``aio.EOF``. Iterating a
  grpc.aio call with ``async for`` creates a reference cycle through the
  call, which lasts until the garbage collector runs.
- A stream's generator drops its call when the stream ends. The frame of
  the generator outlives it whenever an error raised from the stream is
  kept, since the error's traceback holds the frame.
- An error is raised from the gRPC error without that error's traceback,
  whose frames hold the call. The gRPC error stays the cause.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Callable
from typing import Any

import grpc
from grpc import aio

from ydentifi import _converters as convert
from ydentifi._cert_files import CertFiles
from ydentifi._client import DEFAULT_TIMEOUT
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

# grpc's type information omits aio.EOF, the documented end-of-stream marker.
_EOF = aio.EOF  # type: ignore[attr-defined]


async def _ainvoke(rpc: Callable[..., Any], request: object, timeout: float | None) -> Any:
    """Makes one unary call and returns its response.

    Raises:
        StatusError: The call ended with a gRPC error.
    """
    try:
        return await rpc(request, timeout=timeout)
    except grpc.RpcError as exc:
        raise map_rpc_error(exc) from exc.with_traceback(None)


class AsyncClient:
    """The asyncio client: the methods of :class:`Client`, as coroutines and async generators.

    It is built inside a coroutine of the event loop that uses it, and is
    shared by the tasks of that loop. Built where no event loop runs, it
    raises :class:`RuntimeError`.
    The streaming methods are async generators, closed when exhausted or by
    :func:`contextlib.aclosing`. A task cancelled during a call raises
    :class:`asyncio.CancelledError`, and so does a call in flight when the
    client is closed.

    Certificate files are read again as for :class:`Client`; the read runs
    in a worker thread (:func:`asyncio.to_thread`), one at a time.
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
        asyncio.get_running_loop()
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
        self._old_channels: list[aio.Channel] = []
        self._closed = False
        # Held by the one task that reads the certificate files.
        self._renewing = asyncio.Lock()

    async def close(self) -> None:
        """Closes the client's channels; calls in flight raise :class:`asyncio.CancelledError`."""
        if self._closed:
            return
        self._closed = True
        for channel in [self._channel, *self._old_channels]:
            await channel.close()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def create_user(self, *, timeout: float | None = DEFAULT_TIMEOUT) -> str:
        """Creates an anonymous user and returns its opaque ID."""
        stub = await self._service()
        resp = await _ainvoke(stub.CreateUser, pb.CreateUserRequest(), timeout)
        return resp.opaque_id

    async def bulk_create_users(
        self,
        count: int,
        idempotency_key: str,
        *,
        timeout: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """Creates up to ``count`` users under an idempotency key and yields their opaque IDs.

        A call again with the same key first yields the users the key already
        created, then creates the rest. When the relying party's user cap is
        reached, the iteration ends with fewer than ``count`` IDs.
        """
        request = pb.BulkCreateUsersRequest(count=count, idempotency_key=idempotency_key)
        call = (await self._service()).BulkCreateUsers(request, timeout=timeout)
        try:
            # The summary frame that ends the stream carries no chunk.
            while (frame := await call.read()) is not _EOF:
                for opaque_id in frame.chunk.opaque_ids:
                    yield opaque_id
        except grpc.RpcError as exc:
            raise map_rpc_error(exc) from exc.with_traceback(None)
        finally:
            call.cancel()
            del call

    async def get_user(self, opaque_id: str, *, timeout: float | None = DEFAULT_TIMEOUT) -> User:
        """Returns one user."""
        stub = await self._service()
        resp = await _ainvoke(stub.GetUser, pb.GetUserRequest(opaque_id=opaque_id), timeout)
        return convert.user(resp)

    async def export_users(
        self,
        start_after_id: str = "",
        *,
        timeout: float | None = None,
    ) -> AsyncGenerator[User, None]:
        """Yields every user of the relying party, after ``start_after_id`` when it is given."""
        request = pb.ExportUsersRequest(start_after_user_id=start_after_id)
        call = (await self._service()).ExportUsers(request, timeout=timeout)
        try:
            while (page := await call.read()) is not _EOF:
                for u in page.users:
                    yield convert.user(u)
        except grpc.RpcError as exc:
            raise map_rpc_error(exc) from exc.with_traceback(None)
        finally:
            call.cancel()
            del call

    async def update_user_status(
        self,
        opaque_id: str,
        status: UserStatus,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> None:
        """Locks a user (``UserStatus.LOCKED``) or unlocks one (``UserStatus.ACTIVE``)."""
        stub = await self._service()
        request = convert.update_user_status_request(opaque_id, status)
        await _ainvoke(stub.UpdateUserStatus, request, timeout)

    async def delete_user(self, opaque_id: str, *, timeout: float | None = DEFAULT_TIMEOUT) -> None:
        """Deletes a user with the user's devices and challenges; the user's bans stay."""
        stub = await self._service()
        await _ainvoke(stub.DeleteUser, pb.DeleteUserRequest(opaque_id=opaque_id), timeout)

    async def unlock_user_request_limits(
        self,
        opaque_id: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> None:
        """Gives a user back every try of every per-user limit."""
        stub = await self._service()
        request = pb.UnlockUserRequestLimitsRequest(opaque_id=opaque_id)
        await _ainvoke(stub.UnlockUserRequestLimits, request, timeout)

    async def list_devices_for_user(
        self,
        opaque_id: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> list[Device]:
        """Returns the user's devices in every status: active, inactive and banned."""
        stub = await self._service()
        request = pb.ListDevicesForUserRequest(opaque_id=opaque_id)
        resp = await _ainvoke(stub.ListDevicesForUser, request, timeout)
        return [convert.device(d) for d in resp.devices]

    async def revoke_device(
        self,
        opaque_id: str,
        device_id: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> None:
        """Revokes one device; the user's TOTP secret is not replaced."""
        stub = await self._service()
        request = pb.RevokeDeviceRequest(opaque_id=opaque_id, device_id=device_id)
        await _ainvoke(stub.RevokeDevice, request, timeout)

    async def ban_device(
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
        stub = await self._service()
        request = pb.BanDeviceRequest(opaque_id=opaque_id, device_id=device_id, reason=reason)
        return (await _ainvoke(stub.BanDevice, request, timeout)).cascaded_device_count

    async def unban_device(
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
        stub = await self._service()
        request = pb.UnbanDeviceRequest(
            opaque_id=opaque_id,
            device_id=device_id,
            permanent_id=permanent_id,
        )
        await _ainvoke(stub.UnbanDevice, request, timeout)

    async def issue_auth_challenge(
        self,
        req: IssueAuthChallengeRequest,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> Challenge:
        """Issues a challenge to the user's phones."""
        stub = await self._service()
        request = convert.auth_challenge_request(req)
        return convert.challenge(await _ainvoke(stub.IssueAuthChallenge, request, timeout))

    async def await_challenge(
        self,
        challenge_id: str,
        *,
        timeout: float | None = None,
    ) -> AsyncGenerator[ChallengeResult, None]:
        """Yields the frames of a challenge until the server ends the stream.

        The first frame is the challenge's state when the stream opens. The
        last frame is the first terminal one (``ChallengeStatus.is_terminal``),
        after which the server ends the stream.
        """
        request = pb.AwaitChallengeRequest(challenge_id=challenge_id)
        call = (await self._service()).AwaitChallenge(request, timeout=timeout)
        try:
            while (frame := await call.read()) is not _EOF:
                yield convert.challenge_result(frame)
        except grpc.RpcError as exc:
            raise map_rpc_error(exc) from exc.with_traceback(None)
        finally:
            call.cancel()
            del call

    async def list_active_challenges(
        self,
        opaque_id: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> list[ActiveChallenge]:
        """Returns the user's open challenges: those pending or delivered, not yet ended."""
        stub = await self._service()
        request = pb.ListActiveChallengesRequest(opaque_id=opaque_id)
        resp = await _ainvoke(stub.ListActiveChallenges, request, timeout)
        return [convert.active_challenge(s) for s in resp.challenges]

    async def issue_user_totp_enrollment(
        self,
        opaque_id: str,
        *,
        reuse_existing: bool,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> TOTPEnrollment:
        """Returns the user's TOTP secret, or replaces it when ``reuse_existing`` is false."""
        stub = await self._service()
        request = pb.IssueUserTotpEnrollmentRequest(
            opaque_id=opaque_id,
            reuse_existing=reuse_existing,
        )
        resp = await _ainvoke(stub.IssueUserTotpEnrollment, request, timeout)
        return convert.totp_enrollment(resp)

    async def verify_user_totp(
        self,
        opaque_id: str,
        code: str,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> bool:
        """Returns whether a TOTP code is right; a code already accepted is not."""
        stub = await self._service()
        request = pb.VerifyUserTotpRequest(opaque_id=opaque_id, totp_code=code)
        return (await _ainvoke(stub.VerifyUserTotp, request, timeout)).valid

    async def issue_enrollment_invite(
        self,
        req: IssueEnrollmentInviteRequest,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> EnrollmentInvite:
        """Issues an invite to enroll a phone, revoking the user's previous invite."""
        stub = await self._service()
        request = convert.enrollment_invite_request(req)
        resp = await _ainvoke(stub.IssueEnrollmentInvite, request, timeout)
        return convert.enrollment_invite(resp)

    async def issue_recovery_invite(
        self,
        req: IssueRecoveryInviteRequest,
        *,
        timeout: float | None = DEFAULT_TIMEOUT,
    ) -> RecoveryInvite:
        """Revokes every active device of the user and issues an invite to enroll a new phone."""
        stub = await self._service()
        request = convert.recovery_invite_request(req)
        resp = await _ainvoke(stub.IssueRecoveryInvite, request, timeout)
        return convert.recovery_invite(resp)

    async def _service(self) -> pb_grpc.IdentityServiceStub:
        """Returns the stub for a call, first moving to a renewed certificate when one is due.

        Raises:
            CancelledError: The client is closed.
        """
        certs = self._certs
        if certs is not None and certs.due():
            async with self._renewing:
                if certs.due():
                    pair = await asyncio.to_thread(certs.read)
                    if pair is not None and not self._closed:
                        self._old_channels.append(self._channel)
                        self._channel = self._open(*pair)
                        self._stub = pb_grpc.IdentityServiceStub(self._channel)
                        certs.cert_pem = pair[0]
        if self._closed:
            raise CancelledError(
                grpc.StatusCode.CANCELLED,
                ErrorReason.UNSPECIFIED,
                "the client is closed",
            )
        return self._stub

    def _open(self, cert_pem: bytes, key_pem: bytes) -> aio.Channel:
        """Returns a new channel that presents the certificate."""
        creds = grpc.ssl_channel_credentials(self._ca_pem, key_pem, cert_pem)
        return aio.secure_channel(self._target, creds, options=self._options)
