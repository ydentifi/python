"""Locks a user; UserStatus.ACTIVE unlocks the user again.

Usage: python update_user_status.py OPAQUE_ID
"""

from __future__ import annotations

import ydentifi
from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        client.update_user_status(opaque_id, ydentifi.UserStatus.LOCKED)
        print("user locked")


if __name__ == "__main__":
    main()
