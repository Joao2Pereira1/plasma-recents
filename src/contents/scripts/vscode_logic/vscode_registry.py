#!/usr/bin/env python3

"""Central registry of known VS Code variants (Code, Insiders, OSS, VSCodium).

This is the single source of other modules build on:
- database_locator.py uses product_paths to locate each variant's
  installation, since product.json marks where VS Code was installed and
  sits alongside (or gives the base to derive) the user data directory
  that holds state.vscdb — the database with the recent items history
- database_locator.py also uses legacy_dir / default_shared_dir for
  older/portable install layouts that don't resolve via product_paths

Adding a new variant only requires a new entry in VSCODE_REGISTRY —
everything else is derived from it.
"""

from typing import Any

# Centralized registry for VSCode variants and other editors/tools
VSCODE_REGISTRY: dict[str, dict[str, Any]] = {
    "code": {
        "label": "VSCode",
        "executables": ["code", "vscode"],
        "fallback_paths": [
            "/usr/bin/code",
            "/usr/share/code/bin/code",
            "/opt/visual-studio-code/bin/code",
        ],
        "default_args": ["-r"],
        "legacy_dir": "Code",
        "default_shared_dir": ".vscode-shared",
        "product_paths": [
            "/usr/lib/code/product.json",
            "/usr/share/code/resources/app/product.json",
            "/opt/visual-studio-code/resources/app/product.json",
        ],
    },
    "code-insiders": {
        "label": "VSCode Insiders",
        "executables": ["code-insiders"],
        "fallback_paths": [
            "/usr/bin/code-insiders",
            "/opt/visual-studio-code-insiders/bin/code-insiders",
        ],
        "default_args": ["-r"],
        "legacy_dir": "Code - Insiders",
        "default_shared_dir": ".vscode-insiders-shared",
        "product_paths": [
            "/usr/lib/code-insiders/product.json",
            "/usr/share/code-insiders/resources/app/product.json",
            "/opt/visual-studio-code-insiders/resources/app/product.json",
        ],
    },
    "code-oss": {
        "label": "VSCode OSS",
        "executables": ["code-oss"],
        "fallback_paths": ["/usr/bin/code-oss", "/opt/code-oss/bin/code-oss"],
        "default_args": ["-r"],
        "legacy_dir": "Code - OSS",
        "default_shared_dir": ".vscode-oss-shared",
        "product_paths": [
            "/usr/lib/code-oss/product.json",
            "/usr/share/code-oss/resources/app/product.json",
            "/opt/code-oss/resources/app/product.json",
        ],
    },
    "codium": {
        "label": "VSCodium",
        "executables": ["codium", "vscodium"],
        "fallback_paths": ["/usr/bin/codium", "/opt/vscodium/bin/codium"],
        "default_args": ["-r"],
        "legacy_dir": "VSCodium",
        "default_shared_dir": ".vscodium-shared",
        "product_paths": [
            "/usr/lib/vscodium/product.json",
            "/usr/share/vscodium/resources/app/product.json",
            "/opt/vscodium/resources/app/product.json",
        ],
    },
}


def get_vscode_variants() -> list[dict[str, Any]]:
    """Generate the legacy CODE_VARIANTS list dynamically from the registry.

    Used by database_locator to find each variant's product.json and, from
    there, its state.vscdb — the database holding the Open Recent history.
    """
    return [
        {
            "label": info["label"],
            "command": info["executables"][0],
            "legacy_dir": info["legacy_dir"],
            "default_shared_dir": info["default_shared_dir"],
            "product_paths": info["product_paths"],
        }
        for info in VSCODE_REGISTRY.values()
    ]


def get_vscode_commands() -> dict[str, list[str]]:
    """Generate maps for all VSCode variants and their executable aliases.

    Maps every known executable alias (e.g. "code", "vscode") to a launch
    command built from the variant's *first* fallback path. This is a static
    guess, not a filesystem check — open_with_app.resolve_app_command()
    validates the path actually exists before using it, falling back to
    xdg-open otherwise.
    """
    commands: dict[str, list[str]] = {}
    for info in VSCODE_REGISTRY.values():
        base_command = info["fallback_paths"][0]
        full_command = [base_command] + info.get("default_args", [])
        for exe in info["executables"]:
            commands[exe] = full_command
    return commands
