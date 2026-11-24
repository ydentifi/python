"""Creates many anonymous users in one call, under an idempotency key.

The key names one batch: a call again with the same key yields the users
the key already created, then creates the rest, and a new batch takes a new
key. Fewer IDs than requested means the relying party's user cap was reached.
"""

from __future__ import annotations

import contextlib

from _common import args, make_client


def main() -> None:
    count, key = args("count", "key")
    with make_client() as client:
        with contextlib.closing(client.bulk_create_users(int(count), key)) as ids:
            created = set(ids)
        print(f"received {len(created)} of {count} opaque IDs")


if __name__ == "__main__":
    main()
