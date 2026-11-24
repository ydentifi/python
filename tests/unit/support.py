"""Certificates made in memory for the unit tests."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


def key_pem(key: ec.EllipticCurvePrivateKey) -> bytes:
    """Returns a private key as unencrypted PKCS #8 PEM."""
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


class CA:
    """A certificate authority that issues client certificates."""

    def __init__(self) -> None:
        now = dt.datetime.now(dt.UTC)
        self._key = ec.generate_private_key(ec.SECP256R1())
        self._name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-ca")])
        self.cert = (
            x509.CertificateBuilder()
            .subject_name(self._name)
            .issuer_name(self._name)
            .public_key(self._key.public_key())
            .serial_number(1)
            .not_valid_before(now - dt.timedelta(minutes=1))
            .not_valid_after(now + dt.timedelta(hours=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(self._key, hashes.SHA256())
        )
        self.pem = self.cert.public_bytes(serialization.Encoding.PEM)

    def issue(
        self,
        *,
        not_before: dt.datetime | None = None,
        not_after: dt.datetime | None = None,
    ) -> tuple[bytes, bytes]:
        """Returns a client certificate and its key, valid for an hour by default."""
        now = dt.datetime.now(dt.UTC)
        key = ec.generate_private_key(ec.SECP256R1())
        cert = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-rp")]))
            .issuer_name(self._name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_before or now - dt.timedelta(minutes=1))
            .not_valid_after(not_after or now + dt.timedelta(hours=1))
            .sign(self._key, hashes.SHA256())
        )
        return cert.public_bytes(serialization.Encoding.PEM), key_pem(key)


def write_private(path: Path, data: bytes) -> None:
    """Writes a file only its owner can read, in a directory only its owner can enter."""
    path.parent.chmod(0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)


def unknown_key_type(cert_pem: bytes) -> bytes:
    """Returns the certificate with a key algorithm no library can load.

    The EC public-key OID becomes 1.2.840.10045.2.9: the certificate still
    parses, but its public key does not.
    """
    der = x509.load_pem_x509_certificate(cert_pem).public_bytes(serialization.Encoding.DER)
    ec_oid = bytes.fromhex("06072a8648ce3d0201")
    assert der.count(ec_oid) == 1
    odd = der.replace(ec_oid, bytes.fromhex("06072a8648ce3d0209"))
    return x509.load_der_x509_certificate(odd).public_bytes(serialization.Encoding.PEM)
