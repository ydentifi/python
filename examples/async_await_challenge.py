"""Issues a challenge and prints each frame of the wait, under asyncio.

asyncio.timeout bounds the wait beyond the challenge's lifetime.

Usage: python async_await_challenge.py OPAQUE_ID
"""

from __future__ import annotations

import asyncio
import contextlib

import ydentifi
from _common import args, make_async_client


async def main() -> None:
    (opaque_id,) = args("opaque_id")
    async with make_async_client() as client:
        challenge = await client.issue_auth_challenge(
            ydentifi.IssueAuthChallengeRequest(
                opaque_id=opaque_id,
                context=b"Sign in to the admin console",
                min_strength=ydentifi.AuthStrength.DEVICE_ACCESS,
                ttl_seconds=60,
            ),
        )
        async with asyncio.timeout(70):
            async with contextlib.aclosing(
                client.await_challenge(challenge.challenge_id)
            ) as frames:
                async for frame in frames:
                    print(f"status: {frame.status.name}")
                    if frame.status is ydentifi.ChallengeStatus.APPROVED:
                        print("approved: the sign-in proceeds")


if __name__ == "__main__":
    asyncio.run(main())
