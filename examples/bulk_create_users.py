"""Creates many anonymous users in one call, under an idempotency key.

A call again with the same key yields the users the key already created,
then creates the rest. Fewer IDs than requested means the relying party's
user cap was reached.
"""

from __future__ import annotations

import contextlib

from _common import make_client


def main() -> None:
    with make_client() as client:
        with contextlib.closing(client.bulk_create_users(1000, "migration-2026-01")) as ids:
            created = set(ids)
        print(f"received {len(created)} of 1000 opaque IDs")


if __name__ == "__main__":
    main()
