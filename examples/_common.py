"""Shared environment configuration for the examples.

Each example uses these variables:
    YDFI_SERVER_ADDR: The server host and optional port.
    YDFI_TLS_CERT_PATH: The relying-party client certificate in PEM format.
    YDFI_TLS_KEY_PATH: Its private key in PEM format.
    YDFI_TLS_CA_PATH: An optional server-verification CA bundle.
    YDFI_SERVER_NAME: The TLS verification name, required for an IP address.

Inputs such as opaque user IDs are supplied as command-line arguments.
"""

from __future__ import annotations

import sys

import ydentifi


def make_client() -> ydentifi.Client:
    """Returns a client configured from the ``YDFI_*`` environment."""
    return ydentifi.Client()


def make_async_client() -> ydentifi.AsyncClient:
    """Returns an asyncio client configured from the ``YDFI_*`` environment."""
    return ydentifi.AsyncClient()


def args(*names: str) -> list[str]:
    """Returns the command-line arguments, or exits with a usage line."""
    if len(sys.argv) != len(names) + 1:
        script = sys.argv[0].rsplit("/", 1)[-1]
        sys.exit(f"usage: python {script} {' '.join(n.upper() for n in names)}")
    return sys.argv[1:]
