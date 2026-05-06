"""Parser extension: attach the 'assert' subcommand to an existing parser."""

import argparse

from reqtrace.cmd_assert import add_assert_subcommand


def build_assert_parser() -> argparse.ArgumentParser:
    """Return a standalone argument parser for the assert subcommand (useful for testing)."""
    parser = argparse.ArgumentParser(
        prog="reqtrace assert",
        description="Assert response properties for logged entries",
    )
    parser.add_argument("--id", default=None, help="Target a single entry by ID")
    parser.add_argument("--status", type=int, default=None, help="Expected HTTP status code")
    parser.add_argument(
        "--body-contains",
        default=None,
        metavar="TEXT",
        help="Expected substring in response body",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        metavar="Key:Value",
        help="Expected response header (repeatable)",
    )
    parser.add_argument(
        "--max-latency-ms",
        type=float,
        default=None,
        help="Maximum allowed response latency in milliseconds",
    )
    return parser


def add_assert_to_parser(subparsers) -> None:
    """Attach the assert subcommand to an existing subparsers group."""
    add_assert_subcommand(subparsers)
