"""Lifts the ban on a phone, named by one of its device IDs or by its permanent ID.

After delete_user the user's devices are gone and the ban stays, so the
permanent ID is the only way to name the phone.

Usage: python unban_device.py OPAQUE_ID (--device DEVICE_ID | --permanent PERMANENT_ID)
"""

from __future__ import annotations

import argparse

from _common import make_client


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("opaque_id")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--device", default="")
    which.add_argument("--permanent", default="")
    a = parser.parse_args()
    with make_client() as client:
        client.unban_device(a.opaque_id, device_id=a.device, permanent_id=a.permanent)
        print("phone unbanned")


if __name__ == "__main__":
    main()
