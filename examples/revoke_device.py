"""Revokes one device of a user.

Usage: python revoke_device.py OPAQUE_ID DEVICE_ID
"""

from __future__ import annotations

from _common import args, make_client


def main() -> None:
    opaque_id, device_id = args("opaque_id", "device_id")
    with make_client() as client:
        client.revoke_device(opaque_id, device_id)
        print("device revoked")


if __name__ == "__main__":
    main()
