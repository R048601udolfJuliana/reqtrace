"""Helpers to attach the 'label' sub-command to an existing ArgumentParser."""

from __future__ import annotations

import argparse

from reqtrace.cmd_label import add_label_subcommand


def build_label_parser() -> argparse.ArgumentParser:
    """Return a standalone parser for the label sub-command (useful for tests)."""
    parser = argparse.ArgumentParser(prog="reqtrace label")
    subparsers = parser.add_subparsers(dest="label_action", required=True)

    add_p = subparsers.add_parser("add")
    add_p.add_argument("id")
    add_p.add_argument("label")

    rm_p = subparsers.add_parser("remove")
    rm_p.add_argument("id")
    rm_p.add_argument("label")

    ls_p = subparsers.add_parser("list")
    ls_p.add_argument("id", nargs="?", default=None)

    fi_p = subparsers.add_parser("filter")
    fi_p.add_argument("label")

    return parser


def add_label_to_parser(subparsers) -> None:
    """Register the label sub-command on an existing subparsers action."""
    add_label_subcommand(subparsers)
