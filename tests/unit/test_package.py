"""The package: its public surface, its examples and its installation."""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
import tempfile
from importlib import resources
from pathlib import Path

import pytest

import ydentifi

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"

# One method per rpc of identity.IdentityService.
RPC_METHODS = {
    "CreateUser": "create_user",
    "BulkCreateUsers": "bulk_create_users",
    "GetUser": "get_user",
    "ExportUsers": "export_users",
    "UpdateUserStatus": "update_user_status",
    "DeleteUser": "delete_user",
    "UnlockUserRequestLimits": "unlock_user_request_limits",
    "ListDevicesForUser": "list_devices_for_user",
    "RevokeDevice": "revoke_device",
    "BanDevice": "ban_device",
    "UnbanDevice": "unban_device",
    "IssueAuthChallenge": "issue_auth_challenge",
    "AwaitChallenge": "await_challenge",
    "ListActiveChallenges": "list_active_challenges",
    "IssueUserTotpEnrollment": "issue_user_totp_enrollment",
    "VerifyUserTotp": "verify_user_totp",
    "IssueEnrollmentInvite": "issue_enrollment_invite",
    "IssueRecoveryInvite": "issue_recovery_invite",
}
STREAM_METHODS = {"bulk_create_users", "export_users", "await_challenge"}


def _public_methods(cls: type) -> set[str]:
    return {n for n in dir(cls) if not n.startswith("_") and callable(getattr(cls, n))}


def test_the_rpcs_are_the_services() -> None:
    from ydentifi._protogen.protos.identity import identity_service_pb2  # noqa: PLC0415

    service = identity_service_pb2.DESCRIPTOR.services_by_name["IdentityService"]
    assert {m.name for m in service.methods} == set(RPC_METHODS)


@pytest.mark.parametrize("cls", [ydentifi.Client, ydentifi.AsyncClient])
def test_each_client_has_one_method_per_rpc_and_close(cls: type) -> None:
    assert _public_methods(cls) == {*RPC_METHODS.values(), "close"}


def test_the_streams_are_generators_and_the_rest_coroutines_under_asyncio() -> None:
    for name in RPC_METHODS.values():
        sync, aio = getattr(ydentifi.Client, name), getattr(ydentifi.AsyncClient, name)
        if name in STREAM_METHODS:
            assert inspect.isgeneratorfunction(sync), name
            assert inspect.isasyncgenfunction(aio), name
        else:
            assert inspect.iscoroutinefunction(aio), name


@pytest.mark.parametrize("cls", [ydentifi.Client, ydentifi.AsyncClient])
def test_py_006_the_default_timeouts(cls: type) -> None:
    for name in RPC_METHODS.values():
        default = inspect.signature(getattr(cls, name)).parameters["timeout"].default
        assert default == (None if name in STREAM_METHODS else 30.0), name


def test_every_method_has_an_example() -> None:
    missing = [n for n in RPC_METHODS.values() if not (EXAMPLES_DIR / f"{n}.py").exists()]
    assert missing == []


def test_every_exported_name_resolves() -> None:
    assert [n for n in ydentifi.__all__ if not hasattr(ydentifi, n)] == []


def test_the_package_imports_with_only_itself_on_the_path() -> None:
    # The generated modules import one another through the package, never
    # through a top-level "protos" package.
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    probe = (
        "import sys, ydentifi\n"
        "import ydentifi._protogen.protos.identity.identity_service_pb2_grpc\n"
        "assert 'protos' not in sys.modules\n"
    )
    with tempfile.TemporaryDirectory() as cwd:
        done = subprocess.run(
            [sys.executable, "-c", probe],
            check=False,
            env=env,
            cwd=cwd,
            capture_output=True,
        )
    assert done.returncode == 0, done.stderr


def test_the_package_ships_its_type_marker() -> None:
    assert resources.files("ydentifi").joinpath("py.typed").is_file()
