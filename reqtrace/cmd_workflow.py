"""CLI sub-command for managing entry workflows."""

from __future__ import annotations

import argparse

from reqtrace.workflow import (
    WorkflowError,
    clear_workflow,
    filter_by_stage,
    filter_by_workflow,
    get_workflow,
    set_workflow,
    update_stage,
)


def cmd_workflow(args: argparse.Namespace, store) -> None:  # noqa: C901
    action = args.workflow_action

    if action == "set":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry {args.id!r} not found.")
            return
        try:
            set_workflow(entry, args.name, args.stage)
        except WorkflowError as exc:
            print(f"Error: {exc}")
            return
        print(f"Workflow {args.name!r} (stage={args.stage}) attached to {args.id}.")

    elif action == "stage":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry {args.id!r} not found.")
            return
        try:
            update_stage(entry, args.stage)
        except WorkflowError as exc:
            print(f"Error: {exc}")
            return
        print(f"Stage updated to {args.stage!r} for entry {args.id}.")

    elif action == "clear":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry {args.id!r} not found.")
            return
        clear_workflow(entry)
        print(f"Workflow cleared from entry {args.id}.")

    elif action == "show":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry {args.id!r} not found.")
            return
        wf = get_workflow(entry)
        if wf is None:
            print("No workflow attached.")
        else:
            print(f"Workflow : {wf['name']}")
            print(f"Stage    : {wf['stage']}")

    elif action == "list":
        entries = store.all()
        if args.stage:
            entries = filter_by_stage(entries, args.stage)
        if args.name:
            entries = filter_by_workflow(entries, args.name)
        if not entries:
            print("No matching entries.")
            return
        for e in entries:
            wf = get_workflow(e)
            stage = wf["stage"] if wf else "-"
            name = wf["name"] if wf else "-"
            print(f"{e.id}  workflow={name}  stage={stage}")


def add_workflow_subcommand(subparsers) -> None:
    p = subparsers.add_parser("workflow", help="Manage entry workflows")
    sub = p.add_subparsers(dest="workflow_action", required=True)

    s = sub.add_parser("set", help="Attach a workflow to an entry")
    s.add_argument("id")
    s.add_argument("name")
    s.add_argument("--stage", default="pending")

    st = sub.add_parser("stage", help="Update the stage of an attached workflow")
    st.add_argument("id")
    st.add_argument("stage")

    cl = sub.add_parser("clear", help="Remove workflow from an entry")
    cl.add_argument("id")

    sh = sub.add_parser("show", help="Show workflow for an entry")
    sh.add_argument("id")

    ls = sub.add_parser("list", help="List entries by workflow")
    ls.add_argument("--name", default="")
    ls.add_argument("--stage", default="")
