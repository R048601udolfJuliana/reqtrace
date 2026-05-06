"""CLI sub-command: retry — replay a logged request with automatic retries."""

from __future__ import annotations

import argparse
from typing import Optional

from reqtrace.retry import RetryPolicy, retry_entry
from reqtrace.storage import LogStore


def cmd_retry(args: argparse.Namespace, store: LogStore) -> None:
    entry = store.get_by_id(args.id)
    if entry is None:
        print(f"Entry '{args.id}' not found.")
        return

    policy = RetryPolicy(
        max_attempts=args.max_attempts,
        backoff_base=args.backoff,
        retry_on_status=list(args.retry_on),
        override_host=args.host,
    )

    print(
        f"Retrying entry {args.id} — up to {policy.max_attempts} attempt(s), "
        f"back-off base {policy.backoff_base}s …"
    )

    result = retry_entry(entry, policy)

    status_label = str(result.final_status) if result.final_status else "N/A"
    outcome = "SUCCESS" if result.success else "FAILED"
    print(
        f"[{outcome}] attempts={result.attempts}  final_status={status_label}"
        + (f"  error={result.error}" if result.error else "")
    )


def add_retry_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("retry", help="Replay a request with automatic retries")
    p.add_argument("id", help="ID of the log entry to retry")
    p.add_argument("--max-attempts", type=int, default=3, metavar="N",
                   help="Maximum number of attempts (default: 3)")
    p.add_argument("--backoff", type=float, default=1.0, metavar="SECS",
                   help="Base back-off in seconds between retries (default: 1.0)")
    p.add_argument("--retry-on", type=int, nargs="+", default=[500, 502, 503, 504],
                   metavar="STATUS",
                   help="HTTP status codes that trigger a retry (default: 500 502 503 504)")
    p.add_argument("--host", default=None, metavar="HOST",
                   help="Override the target host for the replay")
    p.set_defaults(func=cmd_retry)
