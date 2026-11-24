"""Streams every user of the relying party, under asyncio.

Leaving the async with block closes the stream, also on a break or an error.
"""

from __future__ import annotations

import asyncio
import contextlib

from _common import make_async_client


async def main() -> None:
    async with make_async_client() as client, contextlib.aclosing(client.export_users()) as users:
        async for user in users:
            print(f"{user.opaque_id[:8]}... status={user.status.name}")


if __name__ == "__main__":
    asyncio.run(main())
