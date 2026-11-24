"""Issues an invite to enroll a phone, shown as a QR code.

Usage: python issue_enrollment_invite.py OPAQUE_ID
"""

from __future__ import annotations

import ydentifi
from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        invite = client.issue_enrollment_invite(
            ydentifi.IssueEnrollmentInviteRequest(
                opaque_id=opaque_id,
                ttl_seconds=300,
                context=b"Acme Corp: enrollment of a second phone",
            ),
        )
        # The invite payload is rendered unchanged as a QR code.
        print(f"invite expires at: {invite.expires_at.isoformat()}")


if __name__ == "__main__":
    main()
