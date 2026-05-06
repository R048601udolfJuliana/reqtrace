"""CLI subcommand: ratelimit — analyse request rates per host."""

from __future__ import annotations

import argparse
from typing import Optional

from reqtrace.ratelimit import analyze_rate_limits, format_rate_report
from reqtrace.storage import LogStore


def cmd_ratelimit(args: argparse.Namespace, store: LogStore) -> None:
    entries = store.all()

    info_map = analyze_rate_limits(
        entries,
        threshold_rps=args.threshold,
        window_seconds=args.window,
    )

    if args.flagged_only:
        info_map = {h: i for h, i in info_map.items() if i.flagged}

    print(format_rate_report(info_map))

    if args.flagged_only and not info_map:
        print("No hosts exceeded the threshold.")


def add_ratelimit_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "ratelimit",
        help="Analyse request rates per host and flag potential rate-limit issues.",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        metavar="RPS",
        help="Requests-per-second above which a host is flagged (default: 10.0).",
    )
    p.add_argument(
        "--window",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Rolling window in seconds used for peak detection (default: 60).",
    )
    p.add_argument(
        "--flagged-only",
        action="store_true",
        default=False,
        help="Only show hosts that exceeded the threshold.",
    )
    p.set_defaults(func=cmd_ratelimit)
