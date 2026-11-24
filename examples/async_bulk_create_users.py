"""Creates many anonymous users in one call, under asyncio.

A call again with the same idempotency key resumes the operation. An ID may
arrive in more than one call, so the IDs are kept as a set.
"""

from __future__ import annotations

import asyncio

from _common import make_async_client


async def main() -> None:
    async with make_async_client() as client:
        created = {
            opaque_id async for opaque_id in client.bulk_create_users(1000, "migration-2026-01")
        }
        print(f"received {len(created)} of 1000 opaque IDs")


if __name__ == "__main__":
    asyncio.run(main())
