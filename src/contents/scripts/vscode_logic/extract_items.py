#!/usr/bin/env python3

"""Extracts recent files, folders, and workspaces from VS Code's state database.

Storage format
--------------
VS Code stores recent items in `state.vscdb` (SQLite) using the `ItemTable`
table purely as a key-value store: a key such as
"history.recentlyOpenedPathsList" maps to a JSON string (sometimes stored
as UTF-8/UTF-16 bytes) shaped like:

    {
      "entries": [
        {"folderUri": "file:///home/user/projects/my-app"},
        {"fileUri": "file:///home/user/docs/notes.txt"},
        {"workspace": {"configPath": "file:///home/user/my-app.code-workspace"}}
      ]
    }

Each entry is one of fileUri, folderUri, or workspace.configPath. URI
values may appear as a plain string or as a dict (scheme, fsPath/path,
external).

Extraction flow:
1. Resolve candidate database(s) via vscode_db_locator.db_candidates()
   (env override, per-variant paths, generic filesystem scan).
2. Safely read the recent-paths key from a temp copy of the database
   (the live file may be locked by VS Code).
3. Decode bytes -> str and parse the JSON.
4. Convert each entry's URI into a normalized filesystem path and classify
   it as file / folder / workspace.
5. Aggregate results across databases, dedupe by path, and optionally
   filter out paths that no longer exist (find_recent — main CLI entry
   point). A debug view of all detected databases is also available
   (inspect_databases).
"""

import json
import shutil
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from logger import log
from urllib.parse import unquote, urlparse

from utils import is_path_blacklisted
from vscode_logic.database_locator import db_candidates

# Query shared by read_state_db and inspect_databases: fetches only the
# "Open Recent" history rows, ignoring everything else in ItemTable.
RECENT_KEY_QUERY = """
    SELECT key, value
    FROM ItemTable
    WHERE key = 'history.recentlyOpenedPathsList'
       OR key LIKE 'history.recentlyOpenedPathsList.%'
"""


# Low-level value decoding (bytes/JSON -> Python values)
# ---------------------------------------------------------------------------


def decode_value(value: Any) -> str:
    """Decode SQLite values that may be stored as bytes or strings."""
    if isinstance(value, bytes):
        for enc in ("utf-8", "utf-16", "utf-16-le"):
            try:
                return value.decode(enc)
            except UnicodeDecodeError:
                continue
        log.warning(
            "Failed to decode SQLite bytes value with UTF-8/UTF-16; falling back to replacement characters."
        )
        return value.decode("utf-8", errors="replace")
    return str(value)


def uri_to_path(value: Any) -> str | None:
    """
    Convert a VS Code URI object or string into a local filesystem path.
    Example: uri_to_path("file:///home/user/app") -> /home/user/app"""

    if not value:
        return None

    if isinstance(value, dict):
        scheme = value.get("scheme")
        if scheme and scheme not in {"file", "path"}:
            return None

        for key in ("fsPath", "path"):
            raw = value.get(key)
            if isinstance(raw, str) and raw:
                return str(Path(unquote(raw)).expanduser())

        external = value.get("external")
        if isinstance(external, str):
            return uri_to_path(external)
        return None

    if not isinstance(value, str):
        return None

    raw = value.strip()
    if raw.startswith(("file:", "path:")):
        parsed = urlparse(raw)
        return str(Path(unquote(parsed.path)).expanduser()) if parsed.path else None

    if raw.startswith("/") or raw.startswith("~"):
        return str(Path(unquote(raw)).expanduser())

    return None


# Entry parsing (raw VS Code JSON -> normalized item dicts)
# ---------------------------------------------------------------------------


def item_from_entry(entry: Any, source: str) -> dict[str, str] | None:
    """Convert one VS Code recent-entry object into JSON format.

    `entry` is one element of the real "entries" array VS Code stores under
    history.recentlyOpenedPathsList — always one of fileUri / folderUri /
    workspace.configPath.
    Returns json:
        {
            "name": "app",
            "path": "/home/user/app",
            "kind": "folder",
            "source": "Code shared",
            "exists": "true",
        }
    """

    if not isinstance(entry, dict):
        return None

    kind = "unknown"
    path: str | None = None

    if "fileUri" in entry:
        kind = "file"
        path = uri_to_path(entry.get("fileUri"))
    elif "folderUri" in entry:
        kind = "folder"
        path = uri_to_path(entry.get("folderUri"))
    elif "workspace" in entry and isinstance(entry["workspace"], dict):
        kind = "workspace"
        path = uri_to_path(entry["workspace"].get("configPath"))

    if not path:
        return None

    expanded = str(Path(path).expanduser())
    if is_path_blacklisted(expanded):
        log.info(f"Skipping blacklisted path extracted from {source}: '{expanded}'")
        return None

    item_type = (
        "folder"
        if kind == "folder"
        else ("workspace" if kind == "workspace" else "file")
    )
    p = Path(expanded)
    label = entry.get("label") or p.name or expanded

    return {
        "name": str(label),
        "path": expanded,
        "kind": item_type,
        "source": source,
        "exists": "true" if p.exists() else "false",
    }


def extract_items_from_json(raw_json: str, source: str) -> list[dict[str, str]]:
    """
    Extract recent file, folder, and workspace items from VS Code JSON.
    Example:
    raw_json = '{"entries": [{"fileUri": "file:///home/user/main.py"}]}'
    extract_items_from_json(raw_json, "auto")
    # -> [{"name": "main.py", "path": "/home/user/main.py", "kind": "file", ...}]"""

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        log.warning(f"Failed to parse JSON string payload from {source}: {exc}")
        return []

    # Confirmed shape for history.recentlyOpenedPathsList's value
    entries: list[Any] = []
    if isinstance(data, dict) and isinstance(data.get("entries"), list):
        entries = data["entries"]
    elif isinstance(data, list):
        # Defensive fallback in case a very old version stored a bare array
        entries = data

    items: list[dict[str, str]] = []
    for entry in entries:
        item = item_from_entry(entry, source)
        if item:
            items.append(item)
    return items


# SQLite access (safe copy-then-read, shared by read + inspect)
# ---------------------------------------------------------------------------


@contextmanager
def _safe_connection(db_path: Path):
    """Copy the .vscdb to a temp dir and yield a connection to the copy."""
    with tempfile.TemporaryDirectory(prefix="vscode-recents-") as td:
        copied = Path(td) / "state.vscdb"
        try:
            shutil.copyfile(db_path, copied)
        except Exception as exc:
            log.error(f"Failed to create temporary copy of database '{db_path}': {exc}")
            raise

        conn = sqlite3.connect(copied)
        try:
            yield conn
        finally:
            conn.close()


def read_state_db(db_path: Path, source: str) -> list[dict[str, str]]:
    """Read only the VS Code Open Recent key from one state database safely via copy."""
    if not db_path.exists():
        return []

    try:
        with _safe_connection(db_path) as conn:
            rows = conn.execute(RECENT_KEY_QUERY).fetchall()
    except sqlite3.OperationalError as exc:
        log.error(
            f"SQLite operational failure while reading database '{db_path}': {exc}"
        )
        return []

    items: list[dict[str, str]] = []
    for _key, value in rows:
        items.extend(extract_items_from_json(decode_value(value), source))
    return items


def inspect_databases() -> dict[str, Any]:
    """Return debug information about all detected VS Code databases.

    VS Code stores settings in state.vscdb as a Key-Value store, where
    keys map to serialized JSON strings (or encoded byte streams).
    """

    databases: list[dict[str, Any]] = []

    for source, db_path in db_candidates():
        entry: dict[str, Any] = {
            "source": source,
            "path": str(db_path),
            "exists": db_path.exists(),
        }

        # checks if path to .vscdb exists
        if not db_path.exists():
            databases.append(entry)
            continue

        try:
            entry["sizeBytes"] = db_path.stat().st_size
            with _safe_connection(db_path) as conn:
                # Query all key names in ItemTable matching history/recent patterns
                # (Each key maps to a JSON payload or encoded byte stream)
                all_history_rows = conn.execute("""
                    SELECT key, length(value)
                    FROM ItemTable
                    WHERE key LIKE '%history%' OR key LIKE '%recent%'
                    ORDER BY key
                    """).fetchall()

                # Fetch specific keys whose JSON payload holds recent file/folder lists
                open_recent_rows = conn.execute(RECENT_KEY_QUERY).fetchall()

            # Store key names and the byte size of their corresponding JSON payload
            entry["historyOrRecentKeys"] = [
                {"key": key, "valueLength": length} for key, length in all_history_rows
            ]
            # Parse the JSON payload for each key and count the extracted items
            entry["openRecentItemsFound"] = sum(
                len(extract_items_from_json(decode_value(value), source))
                for _key, value in open_recent_rows
            )
        except Exception as exc:
            log.warning(f"Error inspecting database at '{db_path}': {exc}")
            entry["error"] = str(exc)

        databases.append(entry)

    return {"ok": True, "databases": databases}


# Aggregation (main entry point used by the CLI)
# ---------------------------------------------------------------------------


def dedupe(items: list[dict[str, str]]) -> list[dict[str, str]]:
    """Remove items with a duplicate path, keeping the first occurrence."""
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for item in items:
        key = item["path"]
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def find_recent(
    limit: int,
    include_missing: bool,
    db_override: str | None = None,
) -> dict[str, Any]:
    """Find recent files/folders from all detected VS Code databases.

    Main entry point used by both the CLI and Backend.

    Args:
        limit (int): Maximum number of items to return in the final list.
        include_missing (bool): If `True`, includes items even if the file/folder
            no longer exists on the filesystem.
        db_override (str | None, optional): Explicit path to a `state.vscdb` file.
            If provided, bypasses automatic detection. Defaults to None.
    Returns:
        dict[str, Any]: A dictionary containing consolidated items and search status:
            {
                "ok": True,
                "source": "Code shared",
                "items": [
                    {
                        "name": "my-project",
                        "path": "/home/user/projects/my-project",
                        "kind": "folder",
                        "source": "Code shared",
                        "exists": "true"
                    }, ...
                ],
                "errors": [],
                "checked": [...]
            }
    Examples:
        # Fetch the 15 most recent existing items:
        recents = find_recent(limit=15, include_missing=False)

        # Read from a specific DB including deleted items:
        custom_recents = find_recent(
            limit=50,
            include_missing=True,
            db_override="~/.config/Code/User/globalStorage/state.vscdb"
        )
        -> this way you can set the path to the database
    """

    errors: list[str] = []
    items: list[dict[str, str]] = []
    checked: list[dict[str, Any]] = []
    source_used = "auto"

    candidates = (
        [("override", Path(db_override).expanduser())]
        if db_override
        else db_candidates()
    )

    for source, db_path in candidates:
        checked_entry: dict[str, Any] = {
            "source": source,
            "path": str(db_path),
            "exists": db_path.exists(),
        }
        checked.append(checked_entry)

        if not db_path.exists():
            continue

        try:
            found = read_state_db(db_path, source)
            checked_entry["openRecentItemsFound"] = len(found)
        except Exception as exc:
            log.warning(f"Error reading from candidate database '{db_path}': {exc}")
            checked_entry["error"] = str(exc)
            errors.append(f"{db_path}: {exc}")
            continue

        if found:
            source_used = source
            items.extend(found)

    items = dedupe(items)

    if not include_missing:
        items = [item for item in items if item["exists"] == "true"]

    return {
        "ok": True,
        "source": source_used,
        "items": items[:limit],
        "errors": errors,
        "checked": checked,
    }
