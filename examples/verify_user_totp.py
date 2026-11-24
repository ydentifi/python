"""Checks a six-digit TOTP code against a user's secret.

Usage: python verify_user_totp.py OPAQUE_ID CODE
"""

from __future__ import annotations

from _common import args, make_client


def main() -> None:
    opaque_id, code = args("opaque_id", "code")
    with make_client() as client:
        if client.verify_user_totp(opaque_id, code):
            print("accepted")
        else:
            # The code is wrong, or not later than the last code accepted.
            print("rejected")


if __name__ == "__main__":
    main()
