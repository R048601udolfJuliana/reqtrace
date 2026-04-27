"""Extends the reqtrace CLI parser with the 'diff' subcommand."""

import argparse
from typing import Optional


def add_diff_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'diff' subcommand onto an existing subparsers action."""
    diff_parser: argparse.ArgumentParser = subparsers.add_parser(
        "diff",
        help="Compare two logged requests by their IDs",
    )
    diff_parser.add_argument(
        "id_a",
        metavar="ID_A",
        help="ID of the first log entry",
    )
    diff_parser.add_argument(
        "id_b",
        metavar="ID_B",
        help="ID of the second log entry",
    )


def build_diff_parser() -> argparse.ArgumentParser:
    """Build a standalone argument parser that includes the diff subcommand.

    Useful for testing the subcommand in isolation.
    """
    parser = argparse.ArgumentParser(
        prog="reqtrace",
        description="Lightweight HTTP request logger and replay tool",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_diff_subcommand(subparsers)
    return parser
