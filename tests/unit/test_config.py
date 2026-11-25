"""The configuration rules: arguments, the environment, files and channel options."""

from __future__ import annotations

import datetime as dt
import logging
import os
import threading
from pathlib import Path

import pytest

import ydentifi
from tests.unit.support import CA, write_private
from ydentifi._cert_files import CertFiles
from ydentifi._config import resolve

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
def files(tmp_path: Path) -> dict[str, str]:
    """The certificate, its key and the CA as files."""
    paths = {
        "cert_path": tmp_path / "rp.crt",
        "key_path": tmp_path / "rp.key",
        "ca_path": tmp_path / "ca.crt",
    }
    write_private(paths["cert_path"], _CERT)
    write_private(paths["key_path"], _KEY)
    write_private(paths["ca_path"], _CA.pem)
    return {k: str(v) for k, v in paths.items()}


def test_the_arguments_give_the_whole_configuration(files: dict[str, str]) -> None:
    cfg = resolve(
        server_addr="auth.example.com:443",
        cert_path=files["cert_path"],
        key_path=files["key_path"],
        ca_path=files["ca_path"],
    )
    assert cfg.target == "dns:///auth.example.com:443"
    assert (cfg.cert_pem, cfg.key_pem, cfg.ca_pem) == (_CERT, _KEY, _CA.pem)
    assert (cfg.cert_path, cfg.key_path) == (files["cert_path"], files["key_path"])


def test_a_path_may_be_a_pathlike(files: dict[str, str]) -> None:
    cfg = resolve(
        server_addr="auth.example.com:443",
        cert_path=Path(files["cert_path"]),
        key_path=Path(files["key_path"]),
        ca_path=Path(files["ca_path"]),
    )
    assert (cfg.cert_pem, cfg.key_pem, cfg.ca_pem) == (_CERT, _KEY, _CA.pem)
    assert (cfg.cert_path, cfg.key_path) == (files["cert_path"], files["key_path"])


def test_the_environment_gives_what_the_arguments_leave_out(
    files: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("YDFI_SERVER_ADDR", "10.0.0.5:443")
    monkeypatch.setenv("YDFI_SERVER_NAME", "auth.example.com")
    monkeypatch.setenv("YDFI_TLS_CERT_PATH", files["cert_path"])
    monkeypatch.setenv("YDFI_TLS_KEY_PATH", files["key_path"])
    monkeypatch.setenv("YDFI_TLS_CA_PATH", files["ca_path"])
    cfg = resolve()
    assert cfg.target == "dns:///10.0.0.5:443"
    assert ("grpc.ssl_target_name_override", "auth.example.com") in cfg.options
    assert (cfg.cert_pem, cfg.key_pem, cfg.ca_pem) == (_CERT, _KEY, _CA.pem)


def test_an_argument_wins_over_files_the_environment_names_that_cannot_be_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("YDFI_SERVER_ADDR", "127.0.0.1:1")
    monkeypatch.setenv("YDFI_TLS_CERT_PATH", str(tmp_path / "missing.crt"))
    monkeypatch.setenv("YDFI_TLS_KEY_PATH", str(tmp_path / "missing.key"))
    monkeypatch.setenv("YDFI_TLS_CA_PATH", str(tmp_path / "missing-ca.crt"))
    cfg = resolve(server_addr="auth.example.com:443", cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem)
    assert cfg.target == "dns:///auth.example.com:443"
    assert (cfg.cert_path, cfg.key_path, cfg.ca_pem) == ("", "", _CA.pem)


def test_without_a_ca_bundle_the_client_is_refused() -> None:
    with pytest.raises(ydentifi.ConfigurationError, match="CA bundle"):
        resolve(server_addr="auth.example.com", cert_pem=_CERT, key_pem=_KEY)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cert_path": "rp.crt"},
        {"key_path": "rp.key"},
        {"cert_pem": _CERT},
        {"key_pem": _KEY},
    ],
    ids=["cert_path alone", "key_path alone", "cert_pem alone", "key_pem alone"],
)
async def test_sdk_006_half_a_pair_is_refused(kwargs: dict[str, object]) -> None:
    with pytest.raises(ydentifi.ConfigurationError, match="together"):
        ydentifi.Client(server_addr="auth.example.com:443", **kwargs)  # type: ignore[arg-type]
    with pytest.raises(ydentifi.ConfigurationError, match="together"):
        ydentifi.AsyncClient(server_addr="auth.example.com:443", **kwargs)  # type: ignore[arg-type]


def test_sdk_007_the_same_material_twice(files: dict[str, str]) -> None:
    # A keyword argument given twice is refused by Python itself, so the
    # material given twice is a certificate and a CA bundle, each by file and
    # as bytes.
    with pytest.raises(ydentifi.ConfigurationError, match="both"):
        ydentifi.Client(
            server_addr="auth.example.com:443",
            cert_path=files["cert_path"],
            key_path=files["key_path"],
            cert_pem=_CERT,
            key_pem=_KEY,
        )
    with pytest.raises(ydentifi.ConfigurationError, match="both"):
        ydentifi.Client(
            server_addr="auth.example.com:443",
            cert_pem=_CERT,
            key_pem=_KEY,
            ca_path=files["ca_path"],
            ca_pem=_CA.pem,
        )


def test_sdk_008_an_unreadable_file_is_named_by_its_base_name_only(tmp_path: Path) -> None:
    missing = tmp_path / "secret-dir" / "rp.crt"
    with pytest.raises(ydentifi.ConfigurationError) as refused:
        resolve(server_addr="auth.example.com:443", cert_path=str(missing), key_path=str(missing))
    assert "rp.crt" in str(refused.value)
    assert "secret-dir" not in str(refused.value)
    # The OSError, which names the directory, is not chained.
    assert refused.value.__cause__ is None
    assert refused.value.__suppress_context__


def test_the_channel_options_start_with_the_clients_own() -> None:
    cfg = resolve(
        server_addr="Auth.Example.com:443",
        cert_pem=_CERT,
        key_pem=_KEY,
        ca_pem=_CA.pem,
        keepalive_time_seconds=20,
        keepalive_timeout_seconds=5,
        channel_options=[
            ("grpc.ssl_target_name_override", "other"),
            ("grpc.max_send_message_length", 1),
        ],
    )
    assert cfg.options == [
        ("grpc.primary_user_agent", f"ydentifi-python/{ydentifi.__version__}"),
        ("grpc.ssl_target_name_override", "auth.example.com"),
        ("grpc.keepalive_time_ms", 20_000),
        ("grpc.keepalive_timeout_ms", 5_000),
        ("grpc.ssl_target_name_override", "other"),
        ("grpc.max_send_message_length", 1),
    ]


def test_the_channel_options_may_be_any_sequence() -> None:
    cfg = resolve(
        server_addr="auth.example.com",
        cert_pem=_CERT,
        key_pem=_KEY,
        ca_pem=_CA.pem,
        channel_options=(("grpc.max_send_message_length", 1),),
    )
    assert cfg.options[-1] == ("grpc.max_send_message_length", 1)


@pytest.mark.parametrize("seconds", ["20", 0.5, 0, -1, True])
@pytest.mark.parametrize("argument", ["keepalive_time_seconds", "keepalive_timeout_seconds"])
def test_a_keepalive_is_a_whole_number_of_seconds_above_0(argument: str, seconds: object) -> None:
    with pytest.raises(ydentifi.ConfigurationError, match=argument):
        resolve(
            server_addr="auth.example.com",
            cert_pem=_CERT,
            key_pem=_KEY,
            ca_pem=_CA.pem,
            **{argument: seconds},  # type: ignore[arg-type]
        )


def test_the_user_agent_can_be_replaced() -> None:
    cfg = resolve(
        server_addr="auth.example.com",
        cert_pem=_CERT,
        key_pem=_KEY,
        ca_pem=_CA.pem,
        user_agent="rp/1",
    )
    assert cfg.options[0] == ("grpc.primary_user_agent", "rp/1")


def test_the_key_is_left_out_of_the_configurations_repr() -> None:
    cfg = resolve(server_addr="auth.example.com", cert_pem=_CERT, key_pem=_KEY, ca_pem=_CA.pem)
    assert "PRIVATE KEY" not in repr(cfg)


# --- certificate files -------------------------------------------------------


@pytest.fixture
def cert_files(tmp_path: Path) -> CertFiles:
    write_private(tmp_path / "rp.crt", _CERT)
    write_private(tmp_path / "rp.key", _KEY)
    return CertFiles(str(tmp_path / "rp.crt"), str(tmp_path / "rp.key"), _CERT)


def _replace(certs: CertFiles, cert_pem: bytes, key_pem: bytes) -> None:
    write_private(Path(certs.key_path), key_pem)
    write_private(Path(certs.cert_path), cert_pem)


def test_the_files_are_read_once_an_interval(cert_files: CertFiles) -> None:
    assert cert_files.interval == 60.0, "the README states once a minute"
    assert not cert_files.due()
    cert_files.interval = 0
    assert cert_files.due()


def test_unchanged_files_hold_no_renewal(cert_files: CertFiles) -> None:
    assert cert_files.read() is None


def test_a_new_pair_inside_its_dates_is_a_renewal(cert_files: CertFiles) -> None:
    pair = _CA.issue()
    _replace(cert_files, *pair)
    assert cert_files.read() == pair


@pytest.mark.parametrize(
    "dates",
    [
        {"not_before": dt.datetime.now(dt.UTC) + dt.timedelta(hours=1)},
        {
            "not_before": dt.datetime.now(dt.UTC) - dt.timedelta(hours=2),
            "not_after": dt.datetime.now(dt.UTC) - dt.timedelta(hours=1),
        },
    ],
    ids=["not yet valid", "expired"],
)
def test_a_pair_outside_its_dates_is_logged_and_not_used(
    cert_files: CertFiles,
    caplog: pytest.LogCaptureFixture,
    dates: dict[str, dt.datetime],
) -> None:
    if "not_after" not in dates:
        dates["not_after"] = dates["not_before"] + dt.timedelta(hours=1)
    _replace(cert_files, *_CA.issue(**dates))
    with caplog.at_level(logging.WARNING, logger="ydentifi"):
        assert cert_files.read() is None
    assert "rp.crt is valid from" in caplog.text


def test_a_pair_that_does_not_match_is_logged_and_not_used(
    cert_files: CertFiles,
    caplog: pytest.LogCaptureFixture,
) -> None:
    new_cert, _ = _CA.issue()
    _replace(cert_files, new_cert, _KEY)
    with caplog.at_level(logging.WARNING, logger="ydentifi"):
        assert cert_files.read() is None
    assert "the private key is not the certificate's" in caplog.text


def test_a_file_that_cannot_be_read_is_logged_by_its_base_name(
    cert_files: CertFiles,
    caplog: pytest.LogCaptureFixture,
) -> None:
    Path(cert_files.cert_path).unlink()
    with caplog.at_level(logging.WARNING, logger="ydentifi"):
        assert cert_files.read() is None
    assert "read rp.crt:" in caplog.text
    assert str(Path(cert_files.cert_path).parent) not in caplog.text


def test_sdk_033_the_same_certificate_in_another_encoding_is_no_new_pair(
    cert_files: CertFiles,
    caplog: pytest.LogCaptureFixture,
) -> None:
    encodings = {
        "CRLF line breaks": _CERT.replace(b"\n", b"\r\n"),
        "text before the PEM block": b"subject=CN=test-rp\n" + _CERT,
    }
    for name, cert_pem in encodings.items():
        _replace(cert_files, cert_pem, _KEY)
        with caplog.at_level(logging.WARNING, logger="ydentifi"):
            assert cert_files.read() is None, name
    assert caplog.text == ""


def _warnings(caplog: pytest.LogCaptureFixture, start: int) -> list[str]:
    return [r.getMessage() for r in caplog.records[start:] if r.levelno == logging.WARNING]


def test_sdk_032_each_problem_is_logged_once_while_it_lasts(
    cert_files: CertFiles,
    caplog: pytest.LogCaptureFixture,
) -> None:
    other, _ = _CA.issue()
    now = dt.datetime.now(dt.UTC)
    expired = _CA.issue(
        not_before=now - dt.timedelta(hours=2), not_after=now - dt.timedelta(hours=1)
    )
    steps: list[tuple[str, tuple[bytes, bytes], str]] = [
        ("a key that is not the certificate's", (other, _KEY), "is not the certificate's"),
        ("the pair in use again", (_CERT, _KEY), ""),
        ("the same problem after the pair in use", (other, _KEY), "is not the certificate's"),
        ("a certificate outside its dates", expired, "rp.crt is valid from"),
    ]
    directory = str(Path(cert_files.cert_path).parent)
    with caplog.at_level(logging.WARNING, logger="ydentifi"):
        for name, pair, reason in steps:
            start = len(caplog.records)
            _replace(cert_files, *pair)
            for _ in range(3):
                assert cert_files.read() is None, name
            lines = _warnings(caplog, start)
            if not reason:
                assert lines == [], name
                continue
            assert len(lines) == 1, (name, lines)
            assert reason in lines[0], (name, lines)
            assert directory not in lines[0], (name, lines)


def test_sdk_032_a_fifo_in_place_of_the_certificate_is_refused_at_once(
    cert_files: CertFiles,
    caplog: pytest.LogCaptureFixture,
) -> None:
    fifo = Path(cert_files.cert_path).with_name(".tmp-fifo")
    os.mkfifo(fifo)
    fifo.replace(cert_files.cert_path)
    result: list[tuple[bytes, bytes] | None] = []
    with caplog.at_level(logging.WARNING, logger="ydentifi"):
        reader = threading.Thread(target=lambda: result.append(cert_files.read()))
        reader.start()
        reader.join(2.0)
        blocked = reader.is_alive()
        while reader.is_alive():
            # A writer that opens and closes gives the blocked reader an empty file.
            try:
                os.close(os.open(cert_files.cert_path, os.O_WRONLY | os.O_NONBLOCK))
            except OSError:
                pass
            reader.join(0.05)
    assert not blocked, "the read of a FIFO waited for a writer; want it refused at once"
    assert result == [None]
    assert _warnings(caplog, 0) == ["renewed certificate not used: read rp.crt: not a regular file"]
