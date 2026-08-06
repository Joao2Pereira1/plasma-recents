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

    # If arguments are sent (like --open), forward use cli made for vscode logic
    if len(sys.argv) > 1:
        sys.exit(vscode_main(sys.argv[1:]))

    # Default action: return JSON payload to populate the UI
    recent_files, recent_dirs = get_xbel_recent_items(limit=35)
    vscode_items = get_vscode_items(limit=35)

    # Master structure optimized for JSON QML parsing
    widget_payload = {
        "vscode": vscode_items,
        "recent_files": recent_files,
        "recent_dirs": recent_dirs,
    }

    # Print pure JSON output for QML standard input capture
    print(json.dumps(widget_payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
