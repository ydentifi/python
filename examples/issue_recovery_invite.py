"""Revokes every active device of a user and issues a recovery invite.

The relying party must authenticate the user out of band before the call.

Usage: python issue_recovery_invite.py OPAQUE_ID
"""

from __future__ import annotations

import ydentifi
from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        invite = client.issue_recovery_invite(
            ydentifi.IssueRecoveryInviteRequest(
                opaque_id=opaque_id,
                ttl_seconds=300,
                context=b"Acme Corp: recovery after a lost phone",
            ),
        )
        print(
            f"revoked {invite.revoked_device_count} device(s); "
            f"invite expires at {invite.expires_at.isoformat()}",
        )


if __name__ == "__main__":
    main()
