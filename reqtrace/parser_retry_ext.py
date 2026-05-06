"""Wires the retry sub-command into an existing ArgumentParser."""

from __future__ import annotations

import argparse

from reqtrace.cmd_retry import add_retry_subcommand


def build_retry_parser() -> argparse.ArgumentParser:
    """Return a standalone parser for the retry sub-command (useful for testing)."""
    parser = argparse.ArgumentParser(
        prog="reqtrace retry",
        description="Replay a logged request with automatic retries and back-off.",
    )
    parser.add_argument("id", help="ID of the log entry to retry")
    parser.add_argument("--max-attempts", type=int, default=3, metavar="N")
    parser.add_argument("--backoff", type=float, default=1.0, metavar="SECS")
    parser.add_argument(
        "--retry-on",
        type=int,
        nargs="+",
        default=[500, 502, 503, 504],
        metavar="STATUS",
    )
    parser.add_argument("--host", default=None, metavar="HOST")
    return parser


def add_retry_to_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the retry sub-command on an existing top-level parser."""
    add_retry_subcommand(subparsers)
