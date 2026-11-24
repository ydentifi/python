"""Reads one user by opaque ID.

Usage: python get_user.py OPAQUE_ID
"""

from __future__ import annotations

import ydentifi
from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        try:
            user = client.get_user(opaque_id)
        except ydentifi.NotFoundError:
            print("user not found")
            return
        print(f"status={user.status.name} last_seen={user.last_activity_at}")


if __name__ == "__main__":
    main()
