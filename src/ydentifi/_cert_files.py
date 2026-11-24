"""Certificate renewal from files.

A client whose certificate came from files reads them again, at most once
per :data:`CHECK_INTERVAL`, and moves to a new pair it finds there.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization

from ydentifi._config import load_pair, read_file

CHECK_INTERVAL = 60.0
"""The least time, in seconds, between two reads of the certificate files."""

_logger = logging.getLogger(__name__)


class CertFiles:
    """The client certificate's files and the certificate in use.

    The clients call :meth:`CertFiles.read` one at a time, and record the
    pair they move to in :attr:`CertFiles.cert_pem`.
    """

    def __init__(self, cert_path: str, key_path: str, cert_pem: bytes) -> None:
        # Absolute paths name the same files after a change of working directory.
        self.cert_path = os.path.abspath(cert_path)
        self.key_path = os.path.abspath(key_path)
        self.cert_pem = cert_pem
        self.interval = CHECK_INTERVAL
        self.checked = time.monotonic()
        # The reason the files were last refused for, or empty. A refusal is
        # logged only when its reason differs, so that each problem is
        # logged once while it lasts.
        self.refused = ""

    def due(self) -> bool:
        """Returns whether the interval since the last read has passed."""
        return time.monotonic() - self.checked >= self.interval

    def read(self) -> tuple[bytes, bytes] | None:
        """Returns the certificate and key the files hold, when they are a new pair to use.

        Returns ``None`` when the files hold the certificates in use, in
        this encoding or another. A pair that cannot be read, does not
        parse, does not match, or is outside its validity dates is not used,
        and ``None`` is returned; the refusal is logged at ``WARNING`` once
        while the same problem lasts. Files are named by their base names
        only.
        """
        self.checked = time.monotonic()
        cert_name, key_name = Path(self.cert_path).name, Path(self.key_path).name
        try:
            cert_pem = read_file(self.cert_path)
            if _same_certificates(cert_pem, self.cert_pem):
                self.refused = ""
                return None
            key_pem = read_file(self.key_path)
            leaf = load_pair(cert_pem, key_pem)
        except OSError as exc:
            self._refuse(f"read {Path(exc.filename or '').name}: {exc.strerror}")
            return None
        except ValueError as exc:
            self._refuse(f"{cert_name} and {key_name}: {exc}")
            return None
        now = datetime.now(UTC)
        if not leaf.not_valid_before_utc <= now <= leaf.not_valid_after_utc:
            self._refuse(
                f"{cert_name} is valid from {leaf.not_valid_before_utc} "
                f"to {leaf.not_valid_after_utc}",
            )
            return None
        self.refused = ""
        return cert_pem, key_pem

    def _refuse(self, reason: str) -> None:
        """Logs a refused pair at ``WARNING``, unless its reason is the one logged last."""
        if reason != self.refused:
            _logger.warning("renewed certificate not used: %s", reason)
            self.refused = reason


def _same_certificates(pem: bytes, other: bytes) -> bool:
    """Returns whether two PEM texts hold the same certificates, compared by their DER encoding.

    Line breaks and other differences of encoding are not differences of
    certificate. A text that does not parse holds no certificate in use.
    """
    try:
        return _der(pem) == _der(other)
    except ValueError:
        return False


def _der(pem: bytes) -> list[bytes]:
    """Returns the DER encoding of each certificate of a PEM chain.

    Raises:
        ValueError: The text holds no certificate, or one that does not parse.
    """
    return [
        cert.public_bytes(serialization.Encoding.DER)
        for cert in x509.load_pem_x509_certificates(pem)
    ]
