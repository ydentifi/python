"""Creates an anonymous user.

The opaque ID returned is stored against the relying party's own user
record; it is the only handle the server keeps for the user.
"""

from __future__ import annotations

from _common import make_client


def main() -> None:
    with make_client() as client:
        opaque_id = client.create_user()
        print("created user:", opaque_id)


if __name__ == "__main__":
    main()
