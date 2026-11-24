"""Reads the reason and the trace ID of a status error.

StatusError carries the gRPC code, domain reason and optional trace ID,
field and subject. The trace ID permits correlation with server logs
by deployment operators.
"""

from __future__ import annotations

import ydentifi
from _common import make_client


def main() -> None:
    with make_client() as client:
        try:
            client.get_user("0" * 64)
        except ydentifi.StatusError as err:
            print(
                f"reason={err.reason.name} trace_id={err.trace_id} subject={err.subject}",
            )


if __name__ == "__main__":
    main()
