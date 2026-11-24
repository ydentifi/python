"""Creates many anonymous users in one call, under asyncio.

The key names one batch: a call again with the same key resumes it, and a
new batch takes a new key. An ID may arrive in more than one call, so the IDs
are kept as a set.
"""

from __future__ import annotations

import asyncio

from _common import args, make_async_client


async def main() -> None:
    count, key = args("count", "key")
    async with make_async_client() as client:
        created = {opaque_id async for opaque_id in client.bulk_create_users(int(count), key)}
        print(f"received {len(created)} of {count} opaque IDs")


if __name__ == "__main__":
    asyncio.run(main())
