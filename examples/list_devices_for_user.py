"""Lists the devices of a user, in every status.

Usage: python list_devices_for_user.py OPAQUE_ID
"""

from __future__ import annotations

from _common import args, make_client


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        for device in client.list_devices_for_user(opaque_id):
            print(
                f"device={device.device_id} "
                f"platform={device.platform.name} "
                f"status={device.status.name}",
            )


if __name__ == "__main__":
    main()
