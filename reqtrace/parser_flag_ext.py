"""Parser extension to register the flag subcommand."""
from __future__ import annotations

import argparse

from reqtrace.cmd_flag import add_flag_subcommand


def build_flag_parser() -> argparse.ArgumentParser:
    """Build a standalone argument parser for the flag command (useful for testing)."""
    parser = argparse.ArgumentParser(prog="reqtrace flag", description="Flag entries for follow-up")
    subparsers = parser.add_subparsers(dest="flag_action", required=True)

    p_add = subparsers.add_parser("add", help="Flag an entry")
    p_add.add_argument("id", help="Entry ID")
    p_add.add_argument("--reason", default="", help="Reason for flagging")

    p_rm = subparsers.add_parser("remove", help="Unflag an entry")
    p_rm.add_argument("id", help="Entry ID")

    subparsers.add_parser("list", help="List flagged entries")

    return parser


def add_flag_to_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the flag subcommand onto an existing top-level subparsers object."""
    add_flag_subcommand(subparsers)
