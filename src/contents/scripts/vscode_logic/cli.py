#!/usr/bin/env python3

"""CLI entry point for vscode-recent.

Orchestrates two domains:
- database_locator.py / find_recent  → list/inspect VS Code recent items
- open_with_app.py                   → manage and run the "Open With" menu

Acts as the bridge between the QML widget and the Python logic,
communicating via JSON on stdout (see emit()).
"""

from __future__ import annotations

import argparse
import json
import sys
from logger import log
from typing import Any

# Internal imports
from open_with_app import (
    add_open_with_app,
    read_open_with_apps,
    apps_config_path,
    ensure_apps_config,
    open_path,
    default_open_with_apps,
)
import vscode_logic.database_locator as db_locator


def emit(payload: dict[str, Any]) -> None:
    """Print the final JSON payload with a trailing newline safely consumed by QML."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="vscode-recent",
        description="Read and manage the equivalent of VS Code's 'File > Open Recent' list from the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--include-missing", action="store_true")
    parser.add_argument("--list-dbs", action="store_true")
    parser.add_argument("--inspect-dbs", action="store_true")
    parser.add_argument("--db", help="Use a specific state.vscdb database.")
    parser.add_argument("--list-apps", action="store_true")
    parser.add_argument("--apps-path", action="store_true")
    parser.add_argument("--add-app", help="Add an executable to the Open With menu.")
    parser.add_argument(
        "--app-name", help="Optional display name for the added application."
    )
    parser.add_argument("--open", dest="open_target")
    parser.add_argument("--app", default="code")

    args = parser.parse_args(argv)

    try:
        log.info(f"Executing CLI command with arguments: {argv}")

        if args.list_dbs:
            emit(
                {
                    "ok": True,
                    "databases": [
                        {"source": src, "path": str(p), "exists": p.exists()}
                        for src, p in db_locator.db_candidates()
                    ],
                }
            )
            return 0

        if args.inspect_dbs:
            emit(db_locator.inspect_databases())
            return 0

        if args.apps_path:
            emit({"ok": True, "appsPath": str(ensure_apps_config())})
            return 0

        if args.list_apps:
            ensure_apps_config()
            current_apps = read_open_with_apps()

            emit(
                {
                    "ok": True,
                    "appsPath": str(apps_config_path()),
                    "apps": current_apps if current_apps else default_open_with_apps(),
                }
            )
            return 0

        if args.add_app:
            result = add_open_with_app(args.add_app, args.app_name)
            if not result.get("ok"):
                log.warning(
                    f"Failed to add application '{args.add_app}': {result.get('error')}"
                )
            emit(result)
            return 0

        if args.open_target:
            log.info(f"Opening target path '{args.open_target}' using app '{args.app}'")
            emit(open_path(args.open_target, args.app))
            return 0

        # Core Default Action: fetch recent lists from decoupled parsing module
        recent_items = db_locator.find_recent(
            limit=args.limit, include_missing=args.include_missing, db_override=args.db
        )

        if recent_items.get("errors"):
            for err in recent_items["errors"]:
                log.warning(f"Warning encountered during database lookup: {err}")

        recent_items["appsPath"] = str(ensure_apps_config())
        emit(recent_items)
        return 0

    except Exception as exc:
        # Logs the full exception with Traceback cleanly to the log file
        log.error(f"Unhandled critical exception: {exc}", exc_info=True)

        emit(
            {
                "ok": False,
                "error": str(exc),
                "appsPath": "",
                "items": [],
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
