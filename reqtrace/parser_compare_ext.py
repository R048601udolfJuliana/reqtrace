"""Extension that wires the 'compare' subcommand into the CLI argument parser."""

from __future__ import annotations

import argparse

from reqtrace.cmd_compare import add_compare_subcommand


def build_compare_parser(parent: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Attach the compare subcommand to *parent* and return the parser.

    This follows the same pattern used by parser_diff_ext and other extension
    modules so that reqtrace/cli.py can import and call it uniformly.
    """
    subparsers = parent._subparsers  # type: ignore[attr-defined]
    if subparsers is None:
        raise ValueError("Parent parser has no subparsers action attached.")

    # Locate the first _SubParsersAction already registered on the parser.
    for action in parent._actions:  # type: ignore[attr-defined]
        if isinstance(action, argparse._SubParsersAction):  # type: ignore[attr-defined]
            add_compare_subcommand(action)
            return parent

    raise ValueError("No _SubParsersAction found on the provided parser.")


def add_compare_to_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Convenience wrapper – call this from cli.py with the shared subparsers object."""
    add_compare_subcommand(subparsers)
