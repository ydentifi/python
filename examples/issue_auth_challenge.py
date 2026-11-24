"""Issues a challenge to a user's phones.

Usage: python issue_auth_challenge.py OPAQUE_ID
"""

from __future__ import annotations

import ydentifi
from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        challenge = client.issue_auth_challenge(
            ydentifi.IssueAuthChallengeRequest(
                opaque_id=opaque_id,
                ttl_seconds=60,
                context=b"Login to Acme Corp dashboard",
                # min_strength is required: the server refuses a challenge
                # issued with AuthStrength.UNSPECIFIED.
                min_strength=ydentifi.AuthStrength.DEVICE_ACCESS,
            ),
        )
        # challenge.qr_encoded is rendered unchanged as a QR code, for a phone to scan.
        print("challenge issued:", challenge.challenge_id)


if __name__ == "__main__":
    main()
