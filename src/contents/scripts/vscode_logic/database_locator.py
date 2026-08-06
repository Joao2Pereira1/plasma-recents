#!/usr/bin/env python3

"""Locates VS Code state.vscdb database candidates on disk.

vscode_db_locator.db_candidates() resolves the actual state.vscdb path(s) to
read, combining three discovery routes (in order):
- explicit override: the VSCODE_RECENTS_DB env var, if set
- per-variant paths: for each variant in VSCODE_REGISTRY, product.json
  (when found) gives the exact shared-storage folder name, plus fixed
  fallback paths for legacy/portable/flatpak layouts
- generic scan: a filesystem sweep for any other state.vscdb
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any
from logger import log

# Internal imports
from vscode_logic.vscode_registry import get_vscode_variants

# Dependencies loaded from vscode_registry
CODE_VARIANTS: list[dict[str, Any]] = get_vscode_variants()


# XDG base directories
# ---------------------------------------------------------------------------


def xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or "~/.config").expanduser()


def xdg_data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or "~/.local/share").expanduser()


# Shared helper: dedupe by expanded path, keeping first occurrence
# ---------------------------------------------------------------------------


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    """Expand and dedupe a list of paths, preserving order."""
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        expanded = path.expanduser()
        if expanded in seen:
            continue
        seen.add(expanded)
        out.append(expanded)
    return out


def _dedupe_candidates(candidates: list[tuple[str, Path]]) -> list[tuple[str, Path]]:
    """Expand and dedupe (label, path) candidates by path, keeping first label."""
    seen: set[Path] = set()
    out: list[tuple[str, Path]] = []
    for label, path in candidates:
        expanded = path.expanduser()
        if expanded in seen:
            continue
        seen.add(expanded)
        out.append((label, expanded))
    return out


# Route 2: per-variant discovery via product.json
# ---------------------------------------------------------------------------


def candidate_product_json_paths(command: str, extra_paths: list[str]) -> list[Path]:
    """Find product.json candidates for a VS Code-like installation.

    Resolves `command` on PATH and probes a few directories relative to the
    executable (its own dir and up to two parents), on top of the registry's
    known product_paths. Only paths that actually exist are returned.
    """
    candidates: list[Path] = []
    executable = shutil.which(command)

    if executable:
        exe = Path(executable).resolve()
        for base in (exe.parent, exe.parent.parent, exe.parent.parent.parent):
            candidates.extend(
                [
                    base / "product.json",
                    base / "resources" / "app" / "product.json",
                    base / "lib" / command / "product.json",
                    base / "share" / command / "resources" / "app" / "product.json",
                ]
            )

    candidates.extend(Path(path) for path in extra_paths)
    return [p for p in _dedupe_paths(candidates) if p.is_file()]


def read_product_json(path: Path) -> dict[str, Any]:
    """Read and parse a product.json file, returning {} on any failure."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning(f"Failed to read or parse product.json at '{path}': {exc}")
        return {}


def shared_db_from_product_json(
    product_path: Path, fallback_label: str
) -> tuple[str, Path] | None:
    """Given a product.json, resolve the exact state.vscdb path for this
    install using its sharedDataFolderName — or None if that key is missing.

    product.json itself is metadata, not a database: sharedDataFolderName is
    the name of a folder under the home dir where this install's actual
    state.vscdb (SQLite) lives.
    """
    product = read_product_json(product_path)
    product_label = (
        product.get("nameLong") or product.get("nameShort") or fallback_label
    )
    shared_dir = product.get("sharedDataFolderName")

    if not isinstance(shared_dir, str) or not shared_dir:
        return None

    return (
        f"{product_label} shared",
        Path.home() / shared_dir / "sharedStorage" / "state.vscdb",
    )


# Route 3: generic filesystem scan (fallback for unmodeled installs)
# ---------------------------------------------------------------------------


def discovered_state_dbs() -> list[tuple[str, Path]]:
    """Search common locations for VS Code state.vscdb databases.

    Generic fallback scan: walks XDG config/data dirs (and a few known
    shared/Flatpak roots) for any state.vscdb whose path suggests it
    belongs to a VS Code-family editor. Catches variants or non-standard
    install layouts not explicitly covered by VSCODE_REGISTRY.
    """
    roots = [
        xdg_config_home(),
        xdg_data_home(),
        Path.home() / ".var" / "app",
        Path.home() / ".vscode-shared",
        Path.home() / ".vscode-insiders-shared",
        Path.home() / ".vscode-oss-shared",
        Path.home() / ".vscodium-shared",
    ]

    found: list[tuple[str, Path]] = []
    for root in roots:
        if not root.exists():
            continue
        try:
            for db in root.rglob("state.vscdb"):
                db_str = str(db)
                if (
                    "Code" in db_str
                    or "vscode" in db_str.lower()
                    or "codium" in db_str.lower()
                ):
                    found.append(("discovered", db))
        except (PermissionError, OSError) as exc:
            log.warning(
                f"Permission denied or I/O error scanning root directory '{root}': {exc}"
            )
            continue

    return found


# Main entry point: builds and orders the full candidate list
# ---------------------------------------------------------------------------


def db_candidates() -> list[tuple[str, Path]]:
    """Build the ordered list of databases that may contain recent items.

    Order:
    - explicit env override
    - per-variant candidates (product.json)
    - generic filesystem scan
    Duplicate paths are dropped, keeping the first (highest-priority) occurrence.
    """
    candidates: list[tuple[str, Path]] = []
    explicit_db = os.environ.get("VSCODE_RECENTS_DB")

    if explicit_db:
        log.info(
            f"Using explicit database override from environment variable: {explicit_db}"
        )
        candidates.append(("explicit env", Path(explicit_db).expanduser()))

    for variant in CODE_VARIANTS:
        label = str(variant["label"])
        command = str(variant["command"])
        legacy_dir = str(variant["legacy_dir"])
        default_shared_dir = str(variant["default_shared_dir"])
        product_paths = candidate_product_json_paths(
            command, list(variant["product_paths"])
        )

        # 2a: exact shared-storage path, resolved from product.json's
        # sharedDataFolderName when a readable product.json is found
        # (product.json is metadata, not the DB itself)
        for product_path in product_paths:
            resolved = shared_db_from_product_json(product_path, label)
            if resolved:
                candidates.append(resolved)

        # 2b: fixed fallback guesses, added unconditionally as a safety
        # net regardless of whether product.json resolved above
        candidates.extend(
            [
                (
                    f"{label} shared",
                    Path.home() / default_shared_dir / "sharedStorage" / "state.vscdb",
                ),
                (
                    f"{label} legacy config",
                    xdg_config_home()
                    / legacy_dir
                    / "User"
                    / "globalStorage"
                    / "state.vscdb",
                ),
                (
                    f"{label} legacy data",
                    xdg_data_home()
                    / legacy_dir
                    / "User"
                    / "globalStorage"
                    / "state.vscdb",
                ),
                (
                    f"{label} portable",
                    xdg_data_home()
                    / legacy_dir
                    / "user-data"
                    / "User"
                    / "globalStorage"
                    / "state.vscdb",
                ),
                (
                    f"{label} flatpak config",
                    Path.home()
                    / ".var"
                    / "app"
                    / "com.visualstudio.code"
                    / "config"
                    / legacy_dir
                    / "User"
                    / "globalStorage"
                    / "state.vscdb",
                ),
            ]
        )

    # Route 3: generic scan, lowest priority
    candidates.extend(discovered_state_dbs())

    return _dedupe_candidates(candidates)
