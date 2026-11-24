"""Bans the phone behind a device from the relying party.

Usage: python ban_device.py OPAQUE_ID DEVICE_ID
"""

from __future__ import annotations

from _common import args, make_client


def main() -> None:
    opaque_id, device_id = args("opaque_id", "device_id")
    with make_client() as client:
        moved = client.ban_device(opaque_id, device_id, "reported stolen")
        print(f"phone banned; {moved} active device(s) moved to banned")


if __name__ == "__main__":
    main()
