#!/usr/bin/env python3

"""Entry point for the recent-items widget backend.

Aggregates "recent items" from two independent sources (vscode and xbel)
and prints a single JSON payload to stdout for the QML frontend to consume:

- VS Code (and variants) recent files/folders/workspaces, via
  vscode_logic.extract_items.find_recent (reads state.vscdb).
- KDE/XBEL recent files and directories, via
  xbel_logic.extract_items.get_xbel_recent_items (reads
  ~/.local/share/recently-used.xbel).

If called with CLI arguments (e.g. --open), execution is forwarded
directly to vscode_logic.cli.main instead of producing the default JSON
payload.
"""

import os
import json
import sys

# Import VS Code script functions directly
try:
    from xbel_logic.extract_items import get_xbel_recent_items
    from vscode_logic.extract_items import find_recent
    from vscode_logic.cli import main as vscode_main
    from utils.copy_path import copy_to_clipboard
except ImportError:
    # Just in case the file is in the same directory but not in path
    import sys

    # Dynamically inject this script's directory into sys.path to resolve the import
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from xbel_logic.extract_items import get_xbel_recent_items
    from vscode_logic.extract_items import find_recent
    from vscode_logic.cli import main as vscode_main


def get_vscode_items(limit) -> list[dict[str, str]]:
    """Uses vscode_recent.py to fetch VS Code recent items."""
    try:
        # vscode_parser.find_recent handles the logic via imported context
        result = find_recent(limit=limit, include_missing=False, db_override=None)

        # dynamic dict response validation matching new structure
        if isinstance(result, dict) and "items" in result:
            return [
                {
                    "name": item["name"],
                    "path": item["path"],
                    "kind": item["kind"],
                }
                for item in result["items"]
            ]
    except Exception as e:
        print(f"Internal debug error: {e}", file=sys.stderr)
        return [
            {
                "name": f"Error loading VSCode items: {str(e)}",
                "path": "",
                "kind": "file",
            }
        ]
    return []


def main():

    # If arguments are provided, use the VS Code CLI logic or other utils.
    # This allows the QML frontend to request specific operations,
    # such as listing available applications or opening an item.
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "--copy-path":
            success = copy_to_clipboard(sys.argv[2])
            sys.exit(0 if success else 1)  # exitCode
        else:
            sys.exit(vscode_main(sys.argv[2:]))

    # Default action: collect recent items and return them as JSON
    # to populate the QML interface.
    recent_files, recent_dirs = get_xbel_recent_items(limit=40)
    vscode_items = get_vscode_items(limit=40)

    # Build a single payload containing all recent item sources.
    # The structure is optimized for parsing in QML.
    widget_payload = {
        "vscode": vscode_items,
        "recent_files": recent_files,
        "recent_dirs": recent_dirs,
    }

    # Print pure JSON output for QML standard input capture
    print(json.dumps(widget_payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
