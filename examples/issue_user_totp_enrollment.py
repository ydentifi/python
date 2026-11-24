"""Reads a user's TOTP secret, as a QR code for an authenticator app.

Usage: python issue_user_totp_enrollment.py OPAQUE_ID
"""

from __future__ import annotations

from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        enrollment = client.issue_user_totp_enrollment(opaque_id, reuse_existing=True)
        # The QR image is displayed for scanning by an authenticator app. All
        # three fields contain the secret and must be excluded from logs.
        print(f"QR code ready: {len(enrollment.qr_code_png_base64)} base64 characters")


if __name__ == "__main__":
    main()
