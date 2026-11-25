"""Client configuration: the keyword arguments first, then the environment."""

from __future__ import annotations

import errno
import ipaddress
import os
import stat
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization

from ydentifi._errors import ConfigurationError
from ydentifi._version import __version__

ENV_SERVER_ADDR = "YDFI_SERVER_ADDR"
ENV_SERVER_NAME = "YDFI_SERVER_NAME"
ENV_TLS_CERT_PATH = "YDFI_TLS_CERT_PATH"
ENV_TLS_KEY_PATH = "YDFI_TLS_KEY_PATH"
ENV_TLS_CA_PATH = "YDFI_TLS_CA_PATH"


@dataclass(frozen=True)
class Config:
    """A client configuration that has passed every check.

    Attributes:
        target: The gRPC target: the server address, resolved through DNS.
        options: The gRPC channel options.
        cert_pem: The client certificate chain.
        key_pem: The certificate's private key, left out of ``repr``.
        ca_pem: The deployment's CA bundle that verifies the server.
        cert_path: The certificate's file, or empty when the certificate was
            given in memory.
        key_path: The key's file, or empty.
    """

    target: str
    options: list[tuple[str, str | int]]
    cert_pem: bytes
    key_pem: bytes = field(repr=False)
    ca_pem: bytes
    cert_path: str
    key_path: str


def resolve(  # noqa: PLR0912 -- one branch per configuration rule, in order
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
    channel_options: Sequence[tuple[str, str | int]] | None = None,
) -> Config:
    """Returns the configuration the arguments give, with the environment supplying the rest.

    A file the environment names is read only when no argument gives that
    material.

    Raises:
        ConfigurationError: The configuration is missing, cannot be read, or
            cannot be used.
    """
    cert_path = None if cert_path is None else os.fspath(cert_path)
    key_path = None if key_path is None else os.fspath(key_path)
    ca_path = None if ca_path is None else os.fspath(ca_path)
    env = os.environ
    if server_addr is not None and not server_addr:
        raise ConfigurationError("server_addr was given an empty address")
    addr = server_addr or env.get(ENV_SERVER_ADDR, "")
    if not addr:
        raise ConfigurationError(f"no server address: {ENV_SERVER_ADDR} and server_addr are unset")
    name = verification_name(addr, server_name or env.get(ENV_SERVER_NAME, ""))

    files_given = cert_path is not None or key_path is not None
    if files_given and (cert_pem is not None or key_pem is not None):
        raise ConfigurationError(
            "the certificate is given both as files and as PEM; only one of the two may be given",
        )
    if ca_path is not None and ca_pem is not None:
        raise ConfigurationError(
            "the CA bundle is given both as a file and as PEM; only one of the two may be given",
        )
    if cert_pem is not None or key_pem is not None:
        if cert_pem is None or key_pem is None:
            raise ConfigurationError("cert_pem and key_pem are given together or not at all")
        cert_path = key_path = ""
    else:
        if (cert_path is None) != (key_path is None):
            raise ConfigurationError("cert_path and key_path are given together or not at all")
        if not files_given:
            cert_path = env.get(ENV_TLS_CERT_PATH, "")
            key_path = env.get(ENV_TLS_KEY_PATH, "")
        if not cert_path or not key_path:
            raise ConfigurationError(
                f"no client certificate: {ENV_TLS_CERT_PATH} and {ENV_TLS_KEY_PATH} are unset, "
                "and neither cert_path and key_path nor cert_pem and key_pem are given",
            )
        cert_pem, key_pem = _read(cert_path), _read(key_path)

    if ca_pem is None:
        ca_path = ca_path or env.get(ENV_TLS_CA_PATH, "")
        ca_pem = _read(ca_path) if ca_path else None
    if ca_pem is None:
        # The server's certificate comes from the deployment's own CA. gRPC's
        # bundled public roots would trust any server a public CA names for
        # the host, so they are never used.
        raise ConfigurationError(
            f"no CA bundle: {ENV_TLS_CA_PATH} is unset, and neither ca_path nor ca_pem is given; "
            "the deployment's CA bundle is required",
        )

    try:
        load_pair(cert_pem, key_pem)
    except ValueError as exc:
        raise ConfigurationError(f"client certificate: {exc}") from exc
    try:
        x509.load_pem_x509_certificates(ca_pem)
    except ValueError as exc:
        raise ConfigurationError(f"CA bundle: {exc}") from exc

    options: list[tuple[str, str | int]] = [
        ("grpc.primary_user_agent", user_agent or f"ydentifi-python/{__version__}"),
        ("grpc.ssl_target_name_override", name),
    ]
    for argument, seconds in (
        ("keepalive_time_seconds", keepalive_time_seconds),
        ("keepalive_timeout_seconds", keepalive_timeout_seconds),
    ):
        if seconds is not None and (type(seconds) is not int or seconds <= 0):
            raise ConfigurationError(
                f"{argument} is a whole number of seconds above 0, not {seconds!r}"
            )
    if keepalive_time_seconds is not None:
        options.append(("grpc.keepalive_time_ms", keepalive_time_seconds * 1000))
    if keepalive_timeout_seconds is not None:
        options.append(("grpc.keepalive_timeout_ms", keepalive_timeout_seconds * 1000))
    # gRPC takes the first value given for an option, so these extra options
    # cannot replace the ones above.
    options += channel_options or []
    return Config(
        target=f"dns:///{addr}",
        options=options,
        cert_pem=cert_pem,
        key_pem=key_pem,
        ca_pem=ca_pem,
        cert_path=cert_path,
        key_path=key_path,
    )


def verification_name(addr: str, server_name: str) -> str:
    """Returns the name the server's certificate is verified against.

    The name is ``server_name`` when it is given, and otherwise the address's
    host, lower-cased. An address whose host is an IP address requires a
    ``server_name``.

    Raises:
        ConfigurationError: The address is not ``host``, ``host:port`` or
            ``[IPv6]:port``, or its host is an IP address and ``server_name``
            is empty.
    """
    host = _host(addr)
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return server_name or host.lower()
    if not server_name:
        raise ConfigurationError(
            f"server address {addr!r} is an IP address, so a server_name "
            f"(or {ENV_SERVER_NAME}) is required to verify the server's certificate",
        )
    return server_name


def _host(addr: str) -> str:
    """Returns the host of a server address.

    Raises:
        ConfigurationError: The address is not ``host``, ``host:port`` or
            ``[IPv6]:port``, its host is empty, or its port is not a number
            from 1 to 65535.
    """
    if any(c in "/?#@" or c.isspace() for c in addr):
        raise _bad_address(addr)
    if addr.startswith("["):
        host, sep, port = addr[1:].partition("]:")
        if not sep or not _is_ipv6(host):
            raise _bad_address(addr)
    elif addr.count(":") > 1:
        raise _bad_address(addr)
    else:
        host, sep, port = addr.partition(":")
    if not host or "[" in host or "]" in host:
        raise _bad_address(addr)
    if sep and not (port.isascii() and port.isdigit() and 1 <= int(port) <= 65535):
        raise _bad_address(addr)
    return host


def _is_ipv6(host: str) -> bool:
    try:
        ipaddress.IPv6Address(host)
    except ValueError:
        return False
    return True


def _bad_address(addr: str) -> ConfigurationError:
    return ConfigurationError(
        f"server address {addr!r} is not host, host:port or [IPv6]:port "
        "with a port from 1 to 65535",
    )


def load_pair(cert_pem: bytes, key_pem: bytes) -> x509.Certificate:
    """Returns the leaf certificate of a PEM chain, once its private key is found to match.

    Raises:
        ValueError: The chain or the key does not parse, or the key is not
            the leaf certificate's.
    """
    try:
        leaf = x509.load_pem_x509_certificates(cert_pem)[0]
        key = serialization.load_pem_private_key(key_pem, password=None)
        same_key = leaf.public_key() == key.public_key()
    except (TypeError, UnsupportedAlgorithm) as exc:
        raise ValueError(str(exc)) from exc
    if not same_key:
        raise ValueError("the private key is not the certificate's")
    return leaf


def read_file(path: str) -> bytes:
    """Returns the bytes of a regular file.

    A path that names anything else, such as a FIFO or a directory, is
    refused before it is opened, since the read of a FIFO waits for a
    writer. A symbolic link is followed.

    Raises:
        OSError: The file cannot be read, or it is not a regular file.
    """
    if not stat.S_ISREG(os.stat(path).st_mode):
        raise OSError(errno.EINVAL, "not a regular file", path)
    return Path(path).read_bytes()


def _read(path: str) -> bytes:
    """Returns a file's bytes.

    Raises:
        ConfigurationError: The file cannot be read, or it is not a regular
            file. The message names the file by its base name only, so that
            logs do not show the directory layout.
    """
    try:
        return read_file(path)
    except OSError as exc:
        # from None: the OSError names the full path.
        raise ConfigurationError(f"read {Path(path).name}: {exc.strerror}") from None
