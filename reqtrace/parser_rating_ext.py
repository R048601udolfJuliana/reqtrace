"""Helpers to attach the rating sub-command to an existing argument parser."""

from __future__ import annotations

import argparse

from reqtrace.cmd_rating import add_rating_subcommand, cmd_rating


def build_rating_parser() -> argparse.ArgumentParser:
    """Return a stand-alone parser useful for isolated testing."""
    parser = argparse.ArgumentParser(prog="reqtrace rating")
    subparsers = parser.add_subparsers(dest="rating_action", required=True)
    add_rating_subcommand(subparsers)
    return parser


def add_rating_to_parser(subparsers) -> None:  # noqa: ANN001
    """Register the *rating* command onto an existing subparsers group."""
    add_rating_subcommand(subparsers)


__all__ = ["build_rating_parser", "add_rating_to_parser", "cmd_rating"]
