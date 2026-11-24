"""Issues a challenge and waits for its outcome.

The wait yields the challenge's frames until the first terminal one. The
server ends an unanswered wait five seconds after the challenge expires; a
timeout in seconds bounds the whole wait and raises DeadlineExceededError.

Usage: python await_challenge.py OPAQUE_ID
"""

from __future__ import annotations

import contextlib

import ydentifi
from _common import args, make_client

# The statuses that end a challenge; ChallengeStatus.is_terminal says the same.
_ENDED = {
    ydentifi.ChallengeStatus.APPROVED,
    ydentifi.ChallengeStatus.DENIED,
    ydentifi.ChallengeStatus.REJECTED,
    ydentifi.ChallengeStatus.EXPIRED,
    ydentifi.ChallengeStatus.SUPERSEDED,
    ydentifi.ChallengeStatus.DISMISSED,
}


def main() -> None:
    (opaque_id,) = args("opaque_id")
    with make_client() as client:
        challenge = client.issue_auth_challenge(
            ydentifi.IssueAuthChallengeRequest(
                opaque_id=opaque_id,
                context=b"Authorize wire transfer of EUR 1,000",
                min_strength=ydentifi.AuthStrength.BIOMETRIC,
            ),
        )
        # The timeout leaves time for the user to answer.
        with contextlib.closing(
            client.await_challenge(challenge.challenge_id, timeout=90)
        ) as frames:
            result = next(f for f in frames if f.status in _ENDED)
        if result.status == ydentifi.ChallengeStatus.APPROVED:
            print("approved - proceed with the transfer")
        elif result.status == ydentifi.ChallengeStatus.DENIED:
            # The user declined. NOT_ME reports an attempt the user did not initiate.
            print(f"the user declined - reason: {result.decline_reason.name}")
        elif result.status == ydentifi.ChallengeStatus.REJECTED:
            # User approval failed verification and must not be recorded as a decline.
            # WRONG_MATCH_CODE may indicate a request from another session.
            print(f"a check refused it: {result.verification_failure.name}")
        elif result.status == ydentifi.ChallengeStatus.EXPIRED:
            print("challenge expired - issue a new one")
        elif result.status == ydentifi.ChallengeStatus.DISMISSED:
            print("the user dismissed it without answering - ask again")
        else:
            print(f"unexpected status: {result.status.name}")


if __name__ == "__main__":
    main()
