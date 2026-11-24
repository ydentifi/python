"""Streams every user of the relying party.

Leaving the with block closes the stream, also on a break or an error.
"""

from __future__ import annotations

import contextlib

from _common import make_client


def main() -> None:
    with make_client() as client, contextlib.closing(client.export_users()) as users:
        for user in users:
            print(f"{user.opaque_id[:8]}... status={user.status.name}")


if __name__ == "__main__":
    main()
