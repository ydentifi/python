"""The client's behaviour that needs no server.

Configuration, the address rule, local refusals, error kinds, enum names,
printing and the asyncio client's loop. A client in these tests names a
closed port, so a call that reached the network would raise
``UnavailableError``.
"""

from __future__ import annotations

import asyncio
import base64
import dataclasses
import datetime as dt
import logging
import os
import socket
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import grpc
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from google.protobuf import any_pb2, wrappers_pb2
from google.rpc import status_pb2
from grpc import aio

import ydentifi
from tests.unit.support import CA, key_pem, write_private
from ydentifi import _converters as convert
from ydentifi._config import resolve
from ydentifi._errors import map_rpc_error
from ydentifi._protogen.protos.identity import errors_pb2, identity_pb2
from ydentifi._protogen.protos.identity import identity_service_pb2 as pb

CLOSED_ADDR = "localhost:1"
LOCAL_SLACK = 0.1
UNKNOWN = "0" * 64
_CA = CA()
_CERT, _KEY = _CA.issue()
_ENV = (
    "YDFI_SERVER_ADDR",
    "YDFI_SERVER_NAME",
    "YDFI_TLS_CERT_PATH",
    "YDFI_TLS_KEY_PATH",
    "YDFI_TLS_CA_PATH",
)


@pytest.fixture(autouse=True)
def _no_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _ENV:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def pair_files(tmp_path: Path) -> tuple[str, str]:
    """The certificate and its key as files."""
    cert, key = tmp_path / "rp.crt", tmp_path / "rp.key"
    write_private(cert, _CERT)
    write_private(key, _KEY)
    return str(cert), str(key)


def _closed_client() -> ydentifi.Client:
    return ydentifi.Client(server_addr=CLOSED_ADDR, cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem)


# --- SDK-005 to SDK-009: configuration ---------------------------------------


@pytest.mark.parametrize(
    ("env", "kwargs"),
    [
        ({}, {"cert_pem": _CERT, "key_pem": _KEY}),
        ({"YDFI_TLS_CERT_PATH": "{cert}", "YDFI_TLS_KEY_PATH": "{key}"}, {}),
        ({}, {"server_addr": CLOSED_ADDR}),
        ({"YDFI_SERVER_ADDR": CLOSED_ADDR, "YDFI_TLS_KEY_PATH": "{key}"}, {}),
        ({"YDFI_SERVER_ADDR": CLOSED_ADDR, "YDFI_TLS_CERT_PATH": "{cert}"}, {}),
        ({}, {"server_addr": CLOSED_ADDR, "cert_pem": _CERT, "key_pem": _KEY}),
    ],
    ids=[
        "no address, the pair as arguments",
        "no address, the pair from the environment",
        "no certificate, as arguments",
        "no certificate, from the environment",
        "no key, from the environment",
        "no CA bundle",
    ],
)
async def test_sdk_005_missing_required_material(
    env: dict[str, str],
    kwargs: dict[str, Any],
    pair_files: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cert, key = pair_files
    for name, value in env.items():
        monkeypatch.setenv(name, value.format(cert=cert, key=key))
    with pytest.raises(ydentifi.ConfigurationError):
        ydentifi.Client(**kwargs)
    with pytest.raises(ydentifi.ConfigurationError):
        ydentifi.AsyncClient(**kwargs)


def _new_returns(kwargs: dict[str, Any], fifo: Path | None) -> BaseException | None:
    """Builds a client, and returns what the constructor raised.

    A constructor still reading a FIFO after 2 seconds is released by
    opening the FIFO for writing until it returns, and the test fails.
    """
    out: list[BaseException | None] = []

    def build() -> None:
        try:
            ydentifi.Client(server_addr=CLOSED_ADDR, **kwargs).close()
            out.append(None)
        except BaseException as exc:
            out.append(exc)

    worker = threading.Thread(target=build)
    start = time.monotonic()
    worker.start()
    worker.join(2.0)
    blocked = worker.is_alive()
    while worker.is_alive() and fifo is not None:
        # A writer that opens and closes gives the blocked reader an empty file.
        try:
            os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
        except OSError:
            pass
        worker.join(0.05)
    worker.join()
    if blocked:
        pytest.fail(
            f"the constructor returned after {time.monotonic() - start:.1f}s, once a FIFO it "
            "read was given a writer; want it to return at once",
        )
    return out[0]


def _unreadable(path: Path) -> None:
    path.write_bytes(_CERT)
    path.chmod(0)


_KINDS: dict[str, Callable[[Path], None]] = {
    "a path that does not exist": lambda path: None,
    "a directory": Path.mkdir,
    "a FIFO": os.mkfifo,
    "a file without read permission": _unreadable,
}


@pytest.mark.parametrize("kind", list(_KINDS))
@pytest.mark.parametrize("role", ["cert_path", "key_path", "ca_path"])
def test_sdk_008_files_that_cannot_be_used(
    kind: str,
    role: str,
    pair_files: tuple[str, str],
    tmp_path: Path,
) -> None:
    if kind == "a file without read permission" and os.geteuid() == 0:
        pytest.skip("the superuser reads a file whatever its permission bits")
    directory = tmp_path / "tenant-a"
    directory.mkdir()
    path = directory / f"{role}.pem"
    _KINDS[kind](path)
    cert, key = pair_files
    kwargs: dict[str, Any] = {"cert_path": cert, "key_path": key, role: str(path)}
    raised = _new_returns(kwargs, path if kind == "a FIFO" else None)
    assert isinstance(raised, ydentifi.ConfigurationError), raised
    assert path.name in str(raised)
    assert str(directory) not in str(raised)


async def test_sdk_009_material_that_does_not_parse() -> None:
    other_key = key_pem(ec.generate_private_key(ec.SECP256R1()))
    corrupt = b"-----BEGIN CERTIFICATE-----\nbm90IGEgY2VydGlmaWNhdGU=\n-----END CERTIFICATE-----\n"
    cases: dict[str, dict[str, bytes]] = {
        "a certificate that is not PEM": {"cert_pem": b"not a pem", "key_pem": _KEY},
        "a key that is not PEM": {"cert_pem": _CERT, "key_pem": b"not a pem"},
        "a key that is not the certificate's": {"cert_pem": _CERT, "key_pem": other_key},
        "a chain whose second certificate does not parse": {
            "cert_pem": _CERT + corrupt,
            "key_pem": _KEY,
        },
        "a CA bundle that does not parse": {
            "cert_pem": _CERT,
            "key_pem": _KEY,
            "ca_pem": corrupt + _CA.pem,
        },
        "a CA bundle that is empty": {"cert_pem": _CERT, "key_pem": _KEY, "ca_pem": b""},
    }
    for name, kwargs in cases.items():
        with pytest.raises(ydentifi.ConfigurationError):
            ydentifi.Client(server_addr=CLOSED_ADDR, **kwargs)  # type: ignore[arg-type]
        with pytest.raises(ydentifi.ConfigurationError):
            ydentifi.AsyncClient(server_addr=CLOSED_ADDR, **kwargs)  # type: ignore[arg-type]
        assert name


# --- SDK-010 to SDK-013, SDK-016, SDK-017: the address -----------------------


async def test_sdk_017_an_empty_address_argument_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty server_addr is a mistake, not a request for YDFI_SERVER_ADDR."""
    monkeypatch.setenv("YDFI_SERVER_ADDR", CLOSED_ADDR)
    kwargs: dict[str, Any] = {
        "server_addr": "",
        "cert_pem": _CERT,
        "key_pem": _KEY,
        "ca_pem": _CA.pem,
    }
    with pytest.raises(ydentifi.ConfigurationError, match="server_addr was given an empty address"):
        ydentifi.Client(**kwargs)
    with pytest.raises(ydentifi.ConfigurationError, match="server_addr was given an empty address"):
        ydentifi.AsyncClient(**kwargs)


async def test_sdk_010_a_bare_host_with_no_port() -> None:
    """The address rule admits a host with no port; the verification name is the host."""
    cfg = resolve(server_addr="localhost", cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem)
    assert cfg.target == "dns:///localhost"
    assert ("grpc.ssl_target_name_override", "localhost") in cfg.options
    ydentifi.Client(server_addr="localhost", cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem).close()
    await ydentifi.AsyncClient(
        server_addr="localhost", cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem
    ).close()


@pytest.mark.parametrize(
    "addr",
    ["dns:///localhost:443", "localhost:443/x", "::1:443", "[localhost]:443"],
)
def test_sdk_011_an_address_that_is_not_a_bare_host_and_port(addr: str) -> None:
    with pytest.raises(ydentifi.ConfigurationError):
        ydentifi.Client(server_addr=addr, cert_pem=_CERT, key_pem=_KEY).close()


@pytest.mark.parametrize("server_name", [None, "localhost"])
def test_sdk_012_no_host(server_name: str | None) -> None:
    with pytest.raises(ydentifi.ConfigurationError):
        ydentifi.Client(server_addr=":443", server_name=server_name, cert_pem=_CERT, key_pem=_KEY)


@pytest.mark.parametrize("server_name", [None, "localhost"])
def test_sdk_013_the_ports_bounds(server_name: str | None) -> None:
    for port in ("1", "65535"):
        ydentifi.Client(
            server_addr=f"localhost:{port}",
            server_name=server_name,
            cert_pem=_CERT,
            key_pem=_KEY,
            ca_pem=_CA.pem,
        ).close()
    for port in ("0", "65536", "abc"):
        with pytest.raises(ydentifi.ConfigurationError):
            ydentifi.Client(
                server_addr=f"localhost:{port}",
                server_name=server_name,
                cert_pem=_CERT,
                key_pem=_KEY,
            )


@pytest.fixture
def unix_socket_443(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """A Unix socket named 443 in the working directory, listening."""
    monkeypatch.chdir(tmp_path)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    with sock:
        sock.bind("443")
        sock.listen()
        sock.setblocking(False)
        yield sock


def _no_connection(sock: socket.socket) -> None:
    with pytest.raises(BlockingIOError):
        sock.accept()


def test_sdk_016_the_address_is_resolved_through_dns(unix_socket_443: socket.socket) -> None:
    with ydentifi.Client(
        server_addr="unix:443", cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem
    ) as client:
        with pytest.raises(ydentifi.UnavailableError):
            client.get_user(UNKNOWN, timeout=20)
    _no_connection(unix_socket_443)


async def test_async_sdk_016_the_address_is_resolved_through_dns(
    unix_socket_443: socket.socket,
) -> None:
    async with ydentifi.AsyncClient(
        server_addr="unix:443", cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem
    ) as client:
        with pytest.raises(ydentifi.UnavailableError):
            await client.get_user(UNKNOWN, timeout=20)
    _no_connection(unix_socket_443)


# --- SDK-060 and SDK-061: local refusals -------------------------------------

BAD = "\ud800"
"""A ``str`` with no UTF-8 encoding: a lone surrogate."""


def _sync_string_inputs(c: ydentifi.Client) -> dict[str, Callable[[], object]]:
    def first(it: Any) -> object:
        return next(iter(it))

    def challenge(**kw: str) -> ydentifi.IssueAuthChallengeRequest:
        return ydentifi.IssueAuthChallengeRequest(
            opaque_id=kw.get("opaque_id", UNKNOWN),
            context=b"Approve sign-in at ACME",
            min_strength=ydentifi.AuthStrength.DEVICE_ACCESS,
            challenge_id=kw.get("challenge_id", ""),
        )

    device = "00000000-0000-4000-8000-000000000000"
    return {
        "bulk_create_users key": lambda: first(c.bulk_create_users(1, BAD)),
        "get_user": lambda: c.get_user(BAD),
        "export_users": lambda: first(c.export_users(BAD)),
        "update_user_status": lambda: c.update_user_status(BAD, ydentifi.UserStatus.LOCKED),
        "delete_user": lambda: c.delete_user(BAD),
        "unlock_user_request_limits": lambda: c.unlock_user_request_limits(BAD),
        "list_devices_for_user": lambda: c.list_devices_for_user(BAD),
        "revoke_device opaque_id": lambda: c.revoke_device(BAD, device),
        "revoke_device device_id": lambda: c.revoke_device(UNKNOWN, BAD),
        "ban_device opaque_id": lambda: c.ban_device(BAD, device, "r"),
        "ban_device device_id": lambda: c.ban_device(UNKNOWN, BAD, "r"),
        "ban_device reason": lambda: c.ban_device(UNKNOWN, device, BAD),
        "unban_device opaque_id": lambda: c.unban_device(BAD, device_id=device),
        "unban_device device_id": lambda: c.unban_device(UNKNOWN, device_id=BAD),
        "unban_device permanent_id": lambda: c.unban_device(UNKNOWN, permanent_id=BAD),
        "issue_auth_challenge opaque_id": lambda: c.issue_auth_challenge(challenge(opaque_id=BAD)),
        "issue_auth_challenge challenge_id": lambda: c.issue_auth_challenge(
            challenge(challenge_id=BAD)
        ),
        "await_challenge": lambda: first(c.await_challenge(BAD)),
        "list_active_challenges": lambda: c.list_active_challenges(BAD),
        "issue_user_totp_enrollment": lambda: c.issue_user_totp_enrollment(
            BAD, reuse_existing=True
        ),
        "verify_user_totp opaque_id": lambda: c.verify_user_totp(BAD, "000000"),
        "verify_user_totp code": lambda: c.verify_user_totp(UNKNOWN, BAD),
        "issue_enrollment_invite": lambda: c.issue_enrollment_invite(
            ydentifi.IssueEnrollmentInviteRequest(opaque_id=BAD)
        ),
        "issue_recovery_invite": lambda: c.issue_recovery_invite(
            ydentifi.IssueRecoveryInviteRequest(opaque_id=BAD)
        ),
    }


def _local_unicode_error(name: str, raised: BaseException | None, took: float) -> list[str]:
    """Returns how a refusal differs from SDK-060's: the builtin UnicodeEncodeError, at once."""
    if type(raised) is not UnicodeEncodeError:
        return [f"{name}: raised {raised!r}; want the builtin UnicodeEncodeError"]
    if took > LOCAL_SLACK:
        return [f"{name}: refused after {took:.3f}s; want at once"]
    return []


def test_sdk_060_text_that_cannot_be_encoded() -> None:
    wrong: list[str] = []
    with _closed_client() as client:
        for name, call in _sync_string_inputs(client).items():
            start = time.monotonic()
            raised: BaseException | None = None
            try:
                call()
            except Exception as exc:
                raised = exc
            wrong += _local_unicode_error(name, raised, time.monotonic() - start)
    assert wrong == []


async def test_async_sdk_060_text_that_cannot_be_encoded() -> None:
    client = ydentifi.AsyncClient(
        server_addr=CLOSED_ADDR, cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem
    )
    calls: dict[str, Callable[[], Any]] = {
        "get_user": lambda: client.get_user(BAD),
        "delete_user": lambda: client.delete_user(BAD),
        "revoke_device device_id": lambda: client.revoke_device(UNKNOWN, BAD),
        "ban_device reason": lambda: client.ban_device(UNKNOWN, UNKNOWN, BAD),
        "unban_device permanent_id": lambda: client.unban_device(UNKNOWN, permanent_id=BAD),
        "verify_user_totp code": lambda: client.verify_user_totp(UNKNOWN, BAD),
        "export_users": lambda: anext(client.export_users(BAD)),
        "bulk_create_users key": lambda: anext(client.bulk_create_users(1, BAD)),
        "await_challenge": lambda: anext(client.await_challenge(BAD)),
    }
    wrong: list[str] = []
    try:
        for name, call in calls.items():
            start = time.monotonic()
            raised: BaseException | None = None
            try:
                await call()
            except Exception as exc:
                raised = exc
            wrong += _local_unicode_error(name, raised, time.monotonic() - start)
        assert client._channel.get_state() == grpc.ChannelConnectivity.IDLE
    finally:
        await client.close()
    assert wrong == []


_OUT_OF_RANGE: dict[str, tuple[str, dict[str, int]]] = {
    "count=-1": ("bulk", {"count": -1}),
    "count=2**32": ("bulk", {"count": 2**32}),
    "ttl_seconds=-1": ("challenge", {"ttl_seconds": -1}),
    "match_code=2**32": ("challenge", {"match_code": 2**32}),
}


def _challenge_request(
    ttl_seconds: int = 0, match_code: int = 0
) -> ydentifi.IssueAuthChallengeRequest:
    return ydentifi.IssueAuthChallengeRequest(
        opaque_id=UNKNOWN,
        context=b"Approve sign-in at ACME",
        min_strength=ydentifi.AuthStrength.DEVICE_ACCESS,
        ttl_seconds=ttl_seconds,
        match_code=match_code,
    )


def _send(client: ydentifi.Client, method: str, numbers: dict[str, int]) -> None:
    if method == "bulk":
        next(client.bulk_create_users(numbers["count"], "sdk-061"))
    else:
        client.issue_auth_challenge(_challenge_request(**numbers))


async def _asend(client: ydentifi.AsyncClient, method: str, numbers: dict[str, int]) -> None:
    if method == "bulk":
        await anext(client.bulk_create_users(numbers["count"], "sdk-061"))
    else:
        await client.issue_auth_challenge(_challenge_request(**numbers))


@pytest.mark.parametrize("case", list(_OUT_OF_RANGE))
def test_sdk_061_a_number_the_wire_type_cannot_hold(case: str) -> None:
    """The error protobuf raises, unchanged, before any connection."""
    method, numbers = _OUT_OF_RANGE[case]
    with _closed_client() as client, pytest.raises(ValueError, match="out of range") as refused:
        _send(client, method, numbers)
    assert refused.type is ValueError


@pytest.mark.parametrize("case", list(_OUT_OF_RANGE))
async def test_async_sdk_061_a_number_the_wire_type_cannot_hold(case: str) -> None:
    method, numbers = _OUT_OF_RANGE[case]
    async with ydentifi.AsyncClient(
        server_addr=CLOSED_ADDR, cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem
    ) as client:
        with pytest.raises(ValueError, match="out of range") as refused:
            await _asend(client, method, numbers)
        assert refused.type is ValueError
        assert client._channel.get_state() == grpc.ChannelConnectivity.IDLE


# --- SDK-046: an error leaves no call behind ----------------------------------


def _calls_held(err: BaseException) -> list[str]:
    """Returns the grpc.aio calls that the frames of an error's tracebacks hold.

    The error, its cause and its context are each followed. A call keeps its
    channel's connection open, after ``close()``, while it is referenced.
    """
    held: list[str] = []
    todo: list[BaseException] = [err]
    seen: set[int] = set()
    while todo:
        exc = todo.pop()
        if id(exc) in seen:
            continue
        seen.add(id(exc))
        tb = exc.__traceback__
        while tb is not None:
            frame = tb.tb_frame
            held += [
                f"{type(exc).__name__}: {frame.f_code.co_name}.{name}"
                for name, value in frame.f_locals.items()
                if isinstance(value, aio.Call)
            ]
            tb = tb.tb_next
        todo += [e for e in (exc.__cause__, exc.__context__) if e is not None]
    return held


async def test_async_sdk_046_an_error_holds_no_call() -> None:
    """An error the caller keeps does not keep the call it ended, unary or stream.

    The address names a closed port, so each call ends with ``UnavailableError``.
    """
    async with ydentifi.AsyncClient(
        server_addr=CLOSED_ADDR, cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem
    ) as client:
        calls: dict[str, Callable[[], Any]] = {
            "get_user": lambda: client.get_user(UNKNOWN, timeout=20),
            "export_users": lambda: anext(client.export_users(timeout=20)),
            "bulk_create_users": lambda: anext(client.bulk_create_users(1, "k", timeout=20)),
            "await_challenge": lambda: anext(client.await_challenge("0" * 26, timeout=20)),
        }
        held: list[str] = []
        for name, call in calls.items():
            with pytest.raises(ydentifi.UnavailableError) as refused:
                await call()
            held += [f"{name}: {h}" for h in _calls_held(refused.value)]
        assert held == []


# --- SDK-070: error kinds ------------------------------------------------------


class _Status(grpc.RpcError):
    """A gRPC status as a call raises it: its code, message and trailing metadata."""

    def __init__(self, code: grpc.StatusCode, reason: Any) -> None:
        self._code = code
        self._details = "refused"
        self._trailing: tuple[tuple[str, bytes], ...] = ()
        if reason is not None:
            packed = any_pb2.Any()
            packed.Pack(errors_pb2.ErrorDetail(reason=reason, trace_id="ab" * 16))
            rich = status_pb2.Status(code=code.value[0], message=self._details, details=[packed])
            self._trailing = (("grpc-status-details-bin", rich.SerializeToString()),)

    def code(self) -> grpc.StatusCode:
        return self._code

    def details(self) -> str:
        return self._details

    def trailing_metadata(self) -> Any:
        return self._trailing


_KIND_BY_CODE: dict[grpc.StatusCode, type[ydentifi.StatusError]] = {
    grpc.StatusCode.NOT_FOUND: ydentifi.NotFoundError,
    grpc.StatusCode.ALREADY_EXISTS: ydentifi.AlreadyExistsError,
    grpc.StatusCode.UNAUTHENTICATED: ydentifi.UnauthenticatedError,
    grpc.StatusCode.PERMISSION_DENIED: ydentifi.PermissionDeniedError,
    grpc.StatusCode.RESOURCE_EXHAUSTED: ydentifi.ResourceExhaustedError,
    grpc.StatusCode.FAILED_PRECONDITION: ydentifi.FailedPreconditionError,
    grpc.StatusCode.INVALID_ARGUMENT: ydentifi.InvalidArgumentError,
    grpc.StatusCode.UNAVAILABLE: ydentifi.UnavailableError,
    grpc.StatusCode.ABORTED: ydentifi.AbortedError,
    grpc.StatusCode.DEADLINE_EXCEEDED: ydentifi.DeadlineExceededError,
    grpc.StatusCode.CANCELLED: ydentifi.CancelledError,
    grpc.StatusCode.INTERNAL: ydentifi.InternalError,
}


@pytest.mark.parametrize("code", list(_KIND_BY_CODE), ids=lambda c: c.name)
def test_sdk_070_each_code_maps_to_its_class(code: grpc.StatusCode) -> None:
    bare = map_rpc_error(_Status(code, None))
    assert type(bare) is _KIND_BY_CODE[code]
    assert (bare.code, bare.reason, bare.field, bare.subject, bare.trace_id) == (
        code,
        ydentifi.ErrorReason.UNSPECIFIED,
        "",
        "",
        "",
    )
    detailed = map_rpc_error(_Status(code, errors_pb2.INVALID_ARGUMENT))
    assert type(detailed) is _KIND_BY_CODE[code]
    assert detailed.reason == ydentifi.ErrorReason.INVALID_ARGUMENT
    assert detailed.trace_id == "ab" * 16


@pytest.mark.parametrize(
    ("code", "reason", "kind", "parent"),
    [
        (
            grpc.StatusCode.RESOURCE_EXHAUSTED,
            errors_pb2.CHALLENGE_TOO_SOON,
            ydentifi.ChallengeTooSoonError,
            ydentifi.ResourceExhaustedError,
        ),
        (
            grpc.StatusCode.FAILED_PRECONDITION,
            errors_pb2.MAX_DEVICES_REACHED,
            ydentifi.DeviceLimitReachedError,
            ydentifi.FailedPreconditionError,
        ),
        (
            grpc.StatusCode.FAILED_PRECONDITION,
            errors_pb2.TOTP_LOCKED,
            ydentifi.TOTPLockedError,
            ydentifi.FailedPreconditionError,
        ),
        (
            grpc.StatusCode.INVALID_ARGUMENT,
            errors_pb2.MAX_DEVICES_REACHED,
            ydentifi.InvalidArgumentError,
            ydentifi.StatusError,
        ),
        (
            grpc.StatusCode.FAILED_PRECONDITION,
            errors_pb2.CHALLENGE_TOO_SOON,
            ydentifi.FailedPreconditionError,
            ydentifi.StatusError,
        ),
    ],
    ids=["too soon", "device limit", "totp locked", "a reason under another code", "too soon"],
)
def test_sdk_070_a_reason_narrows_the_class_under_its_code_only(
    code: grpc.StatusCode,
    reason: int,
    kind: type[ydentifi.StatusError],
    parent: type[ydentifi.StatusError],
) -> None:
    err = map_rpc_error(_Status(code, reason))
    assert type(err) is kind
    assert isinstance(err, parent)


# --- SDK-074: an answer newer than the SDK -------------------------------------


class _NewerStatus(_Status):
    """A status whose ErrorDetail has a reason the SDK does not know, alone or after another."""

    def __init__(self, code: grpc.StatusCode, other_first: bool) -> None:
        super().__init__(code, None)
        details = []
        if other_first:
            other = any_pb2.Any()
            other.Pack(wrappers_pb2.StringValue(value="newer"))
            details.append(other)
        packed = any_pb2.Any()
        reason: Any = 9999  # a number no ErrorReason value has
        packed.Pack(
            errors_pb2.ErrorDetail(
                reason=reason, trace_id="ab" * 16, field="opaque_id", subject="s"
            )
        )
        details.append(packed)
        rich = status_pb2.Status(code=code.value[0], message=self._details, details=details)
        self._trailing = (("grpc-status-details-bin", rich.SerializeToString()),)


@pytest.mark.parametrize("other_first", [False, True], ids=["alone", "after another detail"])
def test_sdk_074_an_answer_newer_than_the_sdk(other_first: bool) -> None:
    err = map_rpc_error(_NewerStatus(grpc.StatusCode.FAILED_PRECONDITION, other_first))
    assert type(err) is ydentifi.FailedPreconditionError
    assert err.reason == 9999
    assert err.reason.name == "UNKNOWN_9999"
    assert (err.trace_id, err.field, err.subject) == ("ab" * 16, "opaque_id", "s")
    unknown = map_rpc_error(_NewerStatus(grpc.StatusCode.UNKNOWN, other_first))
    assert type(unknown) is ydentifi.StatusError
    assert (unknown.code, unknown.reason, unknown.trace_id) == (
        grpc.StatusCode.UNKNOWN,
        9999,
        "ab" * 16,
    )


# --- SDK-075: an answer the SDK cannot read ----------------------------------

_GOOD = "2026-11-18T12:00:00+00:00"
# Strings that are not RFC 3339 times: a word, and the forms a lenient ISO 8601
# reader takes.
_NOT_TIMES = (
    "yesterday",
    "2026-11-18",
    "2026-11-18T12:00:00",
    "20261118T120000Z",
    "2026-11-18 12:00:00Z",
    "2026-11-18T12:00:00+0000",
)

# Each answer that carries a time: its converter, its message, its time
# fields, and those of them the server may leave empty.
_TIMED: dict[str, tuple[Callable[[Any], Any], Any, tuple[str, ...], tuple[str, ...]]] = {
    "user": (
        convert.user,
        pb.GetUserResponse,
        ("created_at", "last_authenticated_at", "last_activity_at"),
        ("last_authenticated_at", "last_activity_at"),
    ),
    "device": (
        convert.device,
        pb.DeviceSummary,
        ("created_at", "last_authenticated_at"),
        ("last_authenticated_at",),
    ),
    "challenge": (convert.challenge, pb.IssueAuthChallengeResponse, ("expires_at",), ()),
    "wait-stream frame": (
        convert.challenge_result,
        pb.AwaitChallengeFrame,
        ("emitted_at",),
        ("emitted_at",),
    ),
    "active challenge": (
        convert.active_challenge,
        pb.ActiveChallengeSummary,
        ("issued_at", "expires_at", "delivered_at"),
        ("delivered_at",),
    ),
    "enrollment invite": (
        convert.enrollment_invite,
        pb.IssueEnrollmentInviteResponse,
        ("expires_at",),
        (),
    ),
    "recovery invite": (
        convert.recovery_invite,
        pb.IssueRecoveryInviteResponse,
        ("expires_at",),
        (),
    ),
}


@pytest.mark.parametrize(
    ("answer", "field"),
    [(answer, field) for answer, (_, _, fields, _) in _TIMED.items() for field in fields],
)
def test_sdk_075_a_time_that_does_not_parse(answer: str, field: str) -> None:
    to_public, message, fields, _ = _TIMED[answer]
    times = dict.fromkeys(fields, _GOOD)
    assert to_public(message(**times)) is not None
    for not_time in _NOT_TIMES:
        with pytest.raises(ydentifi.MalformedResponseError, match=field) as raised:
            to_public(message(**{**times, field: not_time}))
        assert not isinstance(raised.value, ydentifi.StatusError)
        assert isinstance(raised.value, ydentifi.YdentifiError)


@pytest.mark.parametrize("answer", list(_TIMED))
def test_sdk_075_an_empty_time(answer: str) -> None:
    """A time the server may leave empty is None; an empty time it always sends cannot be read."""
    to_public, message, fields, optional = _TIMED[answer]
    times = {f: _GOOD for f in fields if f not in optional}
    result = to_public(message(**times))
    for f in optional:
        assert getattr(result, f) is None, f
    for f in times:
        with pytest.raises(ydentifi.MalformedResponseError, match=f):
            to_public(message(**{**times, f: ""}))


# --- SDK-071: enum names ------------------------------------------------------

_PROTO_ENUMS: dict[str, tuple[Any, str]] = {
    "UserStatus": (identity_pb2.UserStatus, "USER_STATUS_"),
    "DevicePlatform": (identity_pb2.DevicePlatform, "DEVICE_PLATFORM_"),
    "DeviceStatus": (identity_pb2.DeviceStatus, "DEVICE_STATUS_"),
    "ChallengeStatus": (identity_pb2.AuthChallengeStatus, "AUTH_CHALLENGE_STATUS_"),
    "ChallengeExpression": (identity_pb2.AuthChallengeExpression, "AUTH_CHALLENGE_EXPRESSION_"),
    "DeclineReason": (identity_pb2.DeclineReason, "DECLINE_REASON_"),
    "VerificationFailure": (identity_pb2.VerificationFailure, "VERIFICATION_FAILURE_"),
    "AuthStrength": (identity_pb2.AuthStrength, "AUTH_STRENGTH_"),
    "LocationBucket": (identity_pb2.LocationBucket, "LOCATION_BUCKET_"),
    "LocationAccuracy": (identity_pb2.LocationAccuracy, "LOCATION_ACCURACY_"),
    "LocationEnforcement": (identity_pb2.LocationEnforcement, "LOCATION_ENFORCEMENT_"),
    "ErrorReason": (errors_pb2.ErrorReason, "ERROR_REASON_"),
}


@pytest.mark.parametrize("enum", list(_PROTO_ENUMS))
def test_sdk_071_enum_names(enum: str) -> None:
    """Each value prints its protocol name; a value with none, up to one past the last, UNKNOWN_n.

    KeyAlgorithm is not part of the SDK's surface: no result carries one.
    """
    proto, prefix = _PROTO_ENUMS[enum]
    names = {v: proto.Name(v).removeprefix(prefix) for v in proto.values()}
    cls = getattr(ydentifi, enum)
    for value in range(max(names) + 2):
        assert cls(value).name == names.get(value, f"UNKNOWN_{value}"), f"{enum}({value})"


# --- SDK-072: secrets are not printed -----------------------------------------


def _secret_results() -> list[tuple[object, dict[str, Any]]]:
    """Each secret-bearing result, with its secret fields."""
    at = dt.datetime(2026, 10, 7, 12, tzinfo=dt.UTC)
    token, payload = os.urandom(32), os.urandom(96)
    secret = base64.b32encode(os.urandom(60)).decode()
    url = f"otpauth://totp/Ydentifi:u1?secret={secret}&issuer=Ydentifi"
    png = "iVBORw0KGgo" + "A" * 400
    invite: dict[str, Any] = {"invite_token": token, "qr_payload": payload}
    totp: dict[str, Any] = {"qr_code_png_base64": png, "totp_url": url, "secret_base32": secret}
    return [
        (ydentifi.EnrollmentInvite(invite_token=token, qr_payload=payload, expires_at=at), invite),
        (
            ydentifi.RecoveryInvite(
                invite_token=token, qr_payload=payload, expires_at=at, revoked_device_count=2
            ),
            invite,
        ),
        (ydentifi.TOTPEnrollment(qr_code_png_base64=png, totp_url=url, secret_base32=secret), totp),
    ]


def test_sdk_072_secrets_are_not_printed(caplog: pytest.LogCaptureFixture) -> None:
    """Each secret field is left out of the repr, by ``field(repr=False)``, name and value alike."""
    for value, secrets in _secret_results():
        hidden = {f.name for f in dataclasses.fields(value) if not f.repr}  # type: ignore[arg-type]
        assert hidden == set(secrets), f"{type(value).__name__} repr leaves out {hidden}"
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="sdk-072"):
            logging.getLogger("sdk-072").info("issued %s", value)
            logging.getLogger("sdk-072").info("issued %r", value)
        renderings = {
            "repr": repr(value),
            "str": str(value),
            "format": f"{value}",
            "%s": "%s" % (value,),  # noqa: UP031 -- the old operator is a rendering callers use
            "a list": repr([value]),
            "logging": caplog.text,
        }
        for how, out in renderings.items():
            for field, secret in secrets.items():
                text = secret if isinstance(secret, str) else secret.hex()
                assert text[:16] not in out, f"{type(value).__name__} {how} shows {field}: {out}"
                if isinstance(secret, bytes):
                    assert repr(secret)[2:18] not in out, f"{type(value).__name__} {how}: {out}"
                assert f"{field}=" not in out, f"{type(value).__name__} {how} shows {field}: {out}"


# --- Python cases -------------------------------------------------------------


def test_py_005_an_async_client_built_outside_its_event_loop() -> None:
    with pytest.raises(RuntimeError, match="no running event loop"):
        ydentifi.AsyncClient(server_addr=CLOSED_ADDR, cert_pem=_CERT, key_pem=_KEY)


class _Recorder:
    """Stands in for the gRPC stub: records the timeout each method is given, then raises."""

    class Sent(Exception):
        """Raised in place of sending."""

    def __init__(self) -> None:
        self.timeouts: list[float | None] = []

    def __getattr__(self, name: str) -> Callable[..., Any]:
        def rpc(_request: object, *, timeout: float | None) -> Any:
            self.timeouts.append(timeout)
            raise _Recorder.Sent(name)

        return rpc


_STREAMS = {"bulk_create_users", "export_users", "await_challenge"}


def _every_call(c: Any) -> dict[str, Callable[..., Any]]:
    req = _challenge_request()
    return {
        "create_user": c.create_user,
        "bulk_create_users": lambda **t: c.bulk_create_users(1, "k", **t),
        "get_user": lambda **t: c.get_user(UNKNOWN, **t),
        "export_users": c.export_users,
        "update_user_status": lambda **t: c.update_user_status(
            UNKNOWN, ydentifi.UserStatus.LOCKED, **t
        ),
        "delete_user": lambda **t: c.delete_user(UNKNOWN, **t),
        "unlock_user_request_limits": lambda **t: c.unlock_user_request_limits(UNKNOWN, **t),
        "list_devices_for_user": lambda **t: c.list_devices_for_user(UNKNOWN, **t),
        "revoke_device": lambda **t: c.revoke_device(UNKNOWN, UNKNOWN, **t),
        "ban_device": lambda **t: c.ban_device(UNKNOWN, UNKNOWN, "r", **t),
        "unban_device": lambda **t: c.unban_device(UNKNOWN, device_id=UNKNOWN, **t),
        "issue_auth_challenge": lambda **t: c.issue_auth_challenge(req, **t),
        "await_challenge": lambda **t: c.await_challenge("0" * 26, **t),
        "list_active_challenges": lambda **t: c.list_active_challenges(UNKNOWN, **t),
        "issue_user_totp_enrollment": lambda **t: c.issue_user_totp_enrollment(
            UNKNOWN, reuse_existing=True, **t
        ),
        "verify_user_totp": lambda **t: c.verify_user_totp(UNKNOWN, "000000", **t),
        "issue_enrollment_invite": lambda **t: c.issue_enrollment_invite(
            ydentifi.IssueEnrollmentInviteRequest(opaque_id=UNKNOWN), **t
        ),
        "issue_recovery_invite": lambda **t: c.issue_recovery_invite(
            ydentifi.IssueRecoveryInviteRequest(opaque_id=UNKNOWN), **t
        ),
    }


def _start(call: Callable[..., Any], kwargs: dict[str, Any], *, stream: bool) -> None:
    """Makes a call; a stream is started by reading its first item."""
    result = call(**kwargs)
    if stream:
        next(result)


async def _astart(call: Callable[..., Any], kwargs: dict[str, Any], *, stream: bool) -> None:
    result = call(**kwargs)
    await (anext(result) if stream else result)


def test_py_006_the_timeout_passed_to_grpc() -> None:
    """30 seconds for a call that is not a stream, none for a stream; None passes none."""
    with _closed_client() as client:
        recorder = _Recorder()
        client._stub = recorder  # type: ignore[assignment]
        for name, call in _every_call(client).items():
            for kwargs, want in (
                ({}, None if name in _STREAMS else 30.0),
                ({"timeout": None}, None),
            ):
                with pytest.raises(_Recorder.Sent):
                    _start(call, kwargs, stream=name in _STREAMS)
                assert recorder.timeouts.pop() == want, (name, kwargs)


async def test_async_py_006_the_timeout_passed_to_grpc() -> None:
    async with ydentifi.AsyncClient(
        server_addr=CLOSED_ADDR, cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem
    ) as client:
        recorder = _Recorder()
        client._stub = recorder  # type: ignore[assignment]
        for name, call in _every_call(client).items():
            for kwargs, want in (
                ({}, None if name in _STREAMS else 30.0),
                ({"timeout": None}, None),
            ):
                with pytest.raises(_Recorder.Sent):
                    await _astart(call, kwargs, stream=name in _STREAMS)
                assert recorder.timeouts.pop() == want, (name, kwargs)


def test_py_008_the_synchronous_cancelled_error_is_the_sdks() -> None:
    client = _closed_client()
    client.close()
    for call in (
        lambda: client.get_user(UNKNOWN),
        lambda: next(client.export_users()),
    ):
        with pytest.raises(ydentifi.CancelledError) as refused:
            call()
        assert not isinstance(refused.value, asyncio.CancelledError)
        assert refused.value.code == grpc.StatusCode.CANCELLED


class _ClosesFirst:
    """Stands in for the gRPC stub: closes the client, then starts the call on the closed one."""

    def __init__(self, client: ydentifi.Client) -> None:
        self._client = client
        self._stub = client._stub

    def __getattr__(self, name: str) -> Callable[..., Any]:
        rpc = getattr(self._stub, name)

        def start(request: object, *, timeout: float | None) -> Any:
            self._client.close()
            return rpc(request, timeout=timeout)

        return start


def test_py_008_a_call_started_as_the_client_closes() -> None:
    """A call given its stub before close() and started after it, on the closed channel."""
    for name in _every_call(_closed_client()):
        client = _closed_client()
        client._stub = _ClosesFirst(client)  # type: ignore[assignment]
        with pytest.raises(ydentifi.CancelledError) as refused:
            _start(_every_call(client)[name], {}, stream=name in _STREAMS)
        assert refused.value.code == grpc.StatusCode.CANCELLED, name


def test_py_008_a_value_error_on_an_open_client_is_not_a_close() -> None:
    """A ValueError the stub raises while the client is open reaches the caller as it is."""

    class _Refuses:
        def __getattr__(self, name: str) -> Callable[..., Any]:
            def start(_request: object, *, timeout: float | None) -> Any:
                raise ValueError(name)

            return start

    with _closed_client() as client:
        client._stub = _Refuses()  # type: ignore[assignment]
        with pytest.raises(ValueError, match="GetUser"):
            client.get_user(UNKNOWN)


class _UnreadableStatus(_Status):
    """A RESOURCE_EXHAUSTED status whose details-bin trailer holds the bytes given."""

    def __init__(self, details_bin: bytes) -> None:
        super().__init__(grpc.StatusCode.RESOURCE_EXHAUSTED, None)
        self._trailing = (("grpc-status-details-bin", details_bin),)


def _details_bin(
    detail: bytes | errors_pb2.ErrorDetail, code: int | None = None, message: str = "refused"
) -> bytes:
    """A status of RESOURCE_EXHAUSTED and its message, as details-bin, with one detail."""
    packed = any_pb2.Any()
    if isinstance(detail, bytes):
        packed.type_url = "type.googleapis.com/" + errors_pb2.ErrorDetail.DESCRIPTOR.full_name
        packed.value = detail
    else:
        packed.Pack(detail)
    if code is None:
        code = grpc.StatusCode.RESOURCE_EXHAUSTED.value[0]
    return status_pb2.Status(code=code, message=message, details=[packed]).SerializeToString()


_READABLE = errors_pb2.ErrorDetail(reason=errors_pb2.CHALLENGE_TOO_SOON, trace_id="ab" * 16)


@pytest.mark.parametrize(
    "details_bin",
    [
        _details_bin(_READABLE, code=grpc.StatusCode.NOT_FOUND.value[0]),
        _details_bin(_READABLE, message="another message"),
        b"\xff\xff\xff",
        _details_bin(b"\xff\xff\xff"),
        _details_bin(
            errors_pb2.ErrorDetail(
                reason=errors_pb2.CHALLENGE_TOO_SOON,
                trace_id="ab" * 16,
                auto_expires_at_unix_ms=2**53,
            )
        ),
    ],
    ids=[
        "another code",
        "another message",
        "not a status",
        "an ErrorDetail that does not decode",
        "a retry time past the last datetime",
    ],
)
def test_py_011_details_the_sdk_cannot_read_are_ignored(details_bin: bytes) -> None:
    err = map_rpc_error(_UnreadableStatus(details_bin))
    assert type(err) is ydentifi.ResourceExhaustedError
    assert (err.reason, err.trace_id, err.auto_expires_at) == (
        ydentifi.ErrorReason.UNSPECIFIED,
        "",
        None,
    )


def test_py_011_readable_details_are_read() -> None:
    err = map_rpc_error(_UnreadableStatus(_details_bin(_READABLE)))
    assert type(err) is ydentifi.ChallengeTooSoonError
    assert err.trace_id == "ab" * 16
