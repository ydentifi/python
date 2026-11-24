"""Lists the open challenges of a user.

Usage: python list_active_challenges.py OPAQUE_ID
"""

from __future__ import annotations

from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        for challenge in client.list_active_challenges(opaque_id):
            print(
                f"challenge={challenge.challenge_id} "
                f"status={challenge.status.name} "
                f"issued={challenge.issued_at.isoformat()}",
            )


if __name__ == "__main__":
    main()
