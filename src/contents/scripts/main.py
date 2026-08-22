#!/usr/bin/env python3

"""Entry point for the recent-items widget backend.

Aggregates recent items from two independent sources:

- VS Code recent files, folders and workspaces, via
  vscode_logic.extract_items.
- KDE/XBEL recent files and directories, via
  xbel_logic.extract_items.

The CLI also exposes operations for database inspection, application
management, opening paths and clipboard utilities.
"""

import argparse
import json
import sys
from typing import Any

from logger import log

from open_with_app import (
    add_open_with_app,
    read_open_with_apps,
    apps_config_path,
    ensure_apps_config,
    open_path,
    default_open_with_apps,
)

from utils.copy_path import copy_to_clipboard

import vscode_logic.database_locator as db_locator

from vscode_logic.extract_items import (
    get_vscode_items,
)

from xbel_logic.extract_items import get_xbel_recent_items


def emit(payload: dict[str, Any]) -> None:
    """Print a JSON payload to stdout for the QML frontend."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="recent-tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Backend for the Recents Tracker widget.\n\n"
            "Aggregates recent items from two independent sources:\n"
            "  - VS Code (recent files, folders and workspaces), read\n"
            "    directly from the 'state.vscdb' SQLite database.\n"
            "  - KDE/XBEL (recent files and directories from the system),\n"
            "    read from KDE's XBEL file.\n\n"
        ),
        epilog=(
            "examples:\n"
            "  # Run with no arguments: outputs JSON with the recent items\n"
            "  python3 main.py\n\n"
            "  # List the VS Code databases found on the system\n"
            "  python3 main.py --list-dbs\n\n"
            "  # Inspect the contents of the databases found\n"
            "  python3 main.py --inspect-dbs\n\n"
            "  # List the applications configured in the 'Open With' menu\n"
            "  python3 main.py --list-apps\n\n"
            "  # Show the path to the apps configuration file\n"
            "  python3 main.py --apps-path\n\n"
            "  # Add a new application to the 'Open With' menu\n"
            "  python3 main.py --add-app /usr/bin/kate\n\n"
            "  # Add an application with a custom display name\n"
            '  python3 main.py --add-app /usr/bin/kate --app-name "Kate"\n\n'
            "  # Open a folder with the configured 'code' application\n"
            "  python3 main.py --open /home/pereira/Pin/projeto_escadas_geradoras/repo/ --app code\n\n"
            "  # Open a file with a specific, already registered application\n"
            "  python3 main.py --open /path/to/file --app kate\n\n"
            "  # Copy a path to the clipboard\n"
            "  python3 main.py --copy-path /path/to/file\n"
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="maximum number of recent items to return (default: 40)",
    )
    parser.add_argument(
        "--include-missing",
        action="store_true",
        help="include items in the output whose path no longer exists on disk",
    )

    # VS Code
    parser.add_argument(
        "--list-dbs",
        action="store_true",
        help="list the VS Code 'state.vscdb' databases found, with their path and whether they exist",
    )
    parser.add_argument(
        "--inspect-dbs",
        action="store_true",
        help="inspect the contents (relevant tables/keys) of the VS Code databases found",
    )
    parser.add_argument(
        "--db",
        metavar="PATH",
        help="path to a specific 'state.vscdb' database to use instead of automatic detection",
    )

    # Open With
    parser.add_argument(
        "--list-apps",
        action="store_true",
        help="list the applications currently configured in the 'Open With' menu",
    )
    parser.add_argument(
        "--apps-path",
        action="store_true",
        help="show the path to the 'Open With' applications configuration file",
    )
    parser.add_argument(
        "--add-app",
        metavar="EXECUTABLE",
        help="register a new application in the 'Open With' menu (path to the executable, e.g. /usr/bin/kate)",
    )
    parser.add_argument(
        "--app-name",
        metavar="NAME",
        help="display name to use together with --add-app (optional, inferred from the executable otherwise)",
    )
    parser.add_argument(
        "--open",
        metavar="PATH",
        help="path to a file or folder to open with the application given in --app",
    )
    parser.add_argument(
        "--app",
        default="default",
        metavar="APP",
        help="name of the application to use with --open, as configured in --list-apps (default: 'default')",
    )

    # Utilities
    parser.add_argument(
        "--copy-path",
        metavar="PATH",
        help="copy the given path to the system clipboard",
    )

    args = parser.parse_args(argv)

    try:
        log.info(f"Executing CLI command with arguments: {argv}")

        # Copy path
        if args.copy_path:
            success = copy_to_clipboard(args.copy_path)
            return 0 if success else 1

        # VS Code database inspection
        if args.list_dbs:
            emit(
                {
                    "ok": True,
                    "databases": [
                        {
                            "source": src,
                            "path": str(path),
                            "exists": path.exists(),
                        }
                        for src, path in db_locator.db_candidates()
                    ],
                }
            )
            return 0

        if args.inspect_dbs:
            emit(db_locator.inspect_databases())
            return 0

        # Open With application management
        if args.apps_path:
            emit(
                {
                    "ok": True,
                    "appsPath": str(ensure_apps_config()),
                }
            )
            return 0

        if args.list_apps:
            ensure_apps_config()
            current_apps = read_open_with_apps()

            emit(
                {
                    "ok": True,
                    "appsPath": str(apps_config_path()),
                    "apps": (
                        current_apps if current_apps else default_open_with_apps()
                    ),
                }
            )
            return 0

        if args.add_app:
            result = add_open_with_app(
                args.add_app,
                args.app_name,
            )

            if not result.get("ok"):
                log.warning(
                    f"Failed to add application "
                    f"'{args.add_app}': {result.get('error')}"
                )

            emit(result)
            return 0

        # Open path
        if args.open:
            log.info(f"Opening target path '{args.open}' " f"using app '{args.app}'")

            result = open_path(args.open, args.app)
            emit(result)

            return 0 if result.get("ok") else 1

        # Default action: collect recent items
        recent_files, recent_dirs = get_xbel_recent_items(limit=40)
        vscode_items = get_vscode_items(limit=40)

        widget_payload = {
            "vscode": vscode_items,
            "recent_files": recent_files,
            "recent_dirs": recent_dirs,
        }

        emit(widget_payload)
        return 0

    except Exception as exc:
        log.error(
            f"Unhandled critical exception: {exc}",
            exc_info=True,
        )

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
    raise SystemExit(main())
