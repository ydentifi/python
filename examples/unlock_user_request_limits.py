"""Gives a user back every try of the per-user limits, after a completed recovery.

The limits are reset only after the recovery, because the limit on
unanswered challenges is what stops a flood of approval requests.

Usage: python unlock_user_request_limits.py OPAQUE_ID
"""

from __future__ import annotations

from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        client.unlock_user_request_limits(opaque_id)
        print("the user's tries are back")


if __name__ == "__main__":
    main()
