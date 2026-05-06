"""CLI subcommand: assert — validate stored responses against expectations."""

import argparse
import sys
from typing import List

from reqtrace.assert_response import assert_entry
from reqtrace.storage import LogStore


def cmd_assert(args: argparse.Namespace, store: LogStore) -> None:
    entries = []
    if args.id:
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry not found: {args.id}", file=sys.stderr)
            sys.exit(1)
        entries = [entry]
    else:
        entries = store.all()

    if not entries:
        print("No entries to assert against.")
        return

    headers_contain = {}
    if args.header:
        for h in args.header:
            if ":" not in h:
                print(f"Invalid --header format (expected Key:Value): {h}", file=sys.stderr)
                sys.exit(1)
            k, v = h.split(":", 1)
            headers_contain[k.strip()] = v.strip()

    any_failed = False
    for entry in entries:
        result = assert_entry(
            entry,
            status=args.status,
            body_contains=args.body_contains,
            headers_contain=headers_contain or None,
            max_latency_ms=args.max_latency_ms,
        )
        print(result.summary())
        if not result.passed:
            any_failed = True

    if any_failed:
        sys.exit(2)


def add_assert_subcommand(subparsers) -> None:
    p = subparsers.add_parser("assert", help="Assert response properties for logged entries")
    p.add_argument("--id", default=None, help="Assert a single entry by ID")
    p.add_argument("--status", type=int, default=None, help="Expected HTTP status code")
    p.add_argument("--body-contains", default=None, metavar="TEXT",
                   help="Expected substring in response body")
    p.add_argument("--header", action="append", default=[],
                   metavar="Key:Value", help="Expected response header (repeatable)")
    p.add_argument("--max-latency-ms", type=float, default=None,
                   help="Maximum allowed latency in milliseconds")
    p.set_defaults(func=cmd_assert)
