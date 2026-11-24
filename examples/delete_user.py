"""Deletes a user, with the user's devices and challenges; the user's bans stay.

Usage: python delete_user.py OPAQUE_ID
"""

from __future__ import annotations

from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        client.delete_user(opaque_id)
        print("user deleted")


if __name__ == "__main__":
    main()
