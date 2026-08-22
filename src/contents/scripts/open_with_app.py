#!/usr/bin/env python3

"""Application registry and launcher for the "Open With" menu.

Handles everything related to opening a recent file/folder with a chosen
application:
- Known VS Code variants and generic desktop apps (name/command resolution)
- Persisted user configuration (apps.json) — read, write, ensure defaults
- Registering new apps, including parsing .desktop launcher files
- Resolving a short app id or free-form command into a safe argv list
- Spawning the detached process that actually opens the target

apps.json is a file structured like this:

{
    "apps": [
        {
            "name": "Default System Handler",
            "command": "/usr/bin/xdg-open"
        },
        {
            "name": "Kate",
            "command": "/usr/bin/kate"
        },
        ...
    ]
}
"""

import json
import os
from pathlib import Path
from typing import Any
import sys
import shlex
from logger import log
import shutil
import subprocess


from vscode_logic.vscode_registry import VSCODE_REGISTRY, get_vscode_commands

# General known applications mapping
GENERIC_KNOWN_APPS: dict[str, tuple[str, str | None]] = {
    # Text Editors
    "subl": ("Sublime Text", None),
    "zed": ("Zed", None),
    "kate": ("Kate", None),
    "kwrite": ("KWrite", None),
    "micro": ("Micro", None),
    "nano": ("Nano", None),
    "vim": ("Vim", None),
    "nvim": ("Neovim", None),
    "notepad++": ("Notepad++", None),
    "notepad": ("Notepad", None),
    "marktext": ("MarkText", None),
    # File Managers
    "dolphin": ("Dolphin", None),
    "nemo": ("Nemo", None),
    "nautilus": ("Nautilus", None),
    "thunar": ("Thunar", None),
    # Multimedia & Browsers
    "vlc": ("VLC Media Player", None),
    "gimp": ("GIMP", None),
    "brave": ("Brave Browser", None),
    "chrome": ("Google Chrome", None),
    "firefox": ("Firefox", None),
    "xdg-open": ("Default System Handler", None),
}

# Configuration storage (apps.json: read / write / ensure defaults)
# ---------------------------------------------------------------------------


def apps_config_path() -> Path:
    """Return the Path to the applications configuration file aligned with the widget."""
    config_dir = Path("~/.config/recents-tracker-widget").expanduser()  # ~ -> /home/usr
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "apps.json"


def default_open_with_apps() -> list[dict[str, str]]:
    """Default apps added when apps.json is created."""
    return [
        {"name": "Default System Handler", "command": "/usr/bin/xdg-open"},
        {"name": "Kate", "command": "/usr/bin/kate"},
        {"name": "VSCode", "command": "/usr/bin/code -r"},
    ]


def ensure_apps_config() -> Path:
    """
    Ensure apps.json exists using structural guidelines from open_with_app.
    Return: path to apps.json"""
    path = apps_config_path()

    # If apps.json is empty, it adds default apps
    if not path.exists() or path.stat().st_size == 0:
        write_open_with_apps(default_open_with_apps())
    return path


def write_open_with_apps(apps: list[dict[str, Any]]) -> None:
    """Write the updated apps list back to the configuration file inside the 'apps' key."""
    config_path = apps_config_path()
    try:
        payload = {"apps": apps}
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Failed to write configuration: {e}", file=sys.stderr)


def read_open_with_apps() -> list[dict[str, Any]]:
    """
    Read and parse the registered apps from the configuration file wrapping key.
    Return: list of dictionaries that includes app name and the respective command"""
    config_path = apps_config_path()
    if not config_path.exists():
        return []

    if config_path.stat().st_size == 0:
        try:
            config_path.unlink()
        except OSError:
            pass
        return []

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, dict) and "apps" in data:
                return data["apps"]
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError):
        try:
            config_path.unlink()
        except OSError:
            pass
        return []


# Name/command resolution for a given executable
# ---------------------------------------------------------------------------


def command_from_executable(executable_path: Path) -> str:
    """
    Return the formatted command string, prioritizing custom arguments from registries.
    Example: Path("/usr/bin/code") -> "/usr/bin/code --new-window".
    """

    executable = str(executable_path)
    exe_name = executable_path.name

    # Check if it's a known VSCode variant first
    if exe_name in get_vscode_commands():
        args = VSCODE_REGISTRY.get(exe_name, {}).get("default_args", [])
        return f"{executable} {' '.join(args)}".strip()

    # Check if it's a generic system app
    app_info = GENERIC_KNOWN_APPS.get(exe_name)
    if app_info and app_info[1]:
        return f"{executable} {app_info[1]}"

    return executable


def display_name_from_executable(executable_path: Path) -> str:
    """
    Build a readable application name checking all registered apps.
    Example: /usr/bin/code-insiders -> "Visual Studio Code Insiders"""
    exe_name = executable_path.name

    # Check VSCode registry
    if exe_name in get_vscode_commands():
        return VSCODE_REGISTRY.get(exe_name, {}).get("label", exe_name)

    # Check generic system apps registry
    app_info = GENERIC_KNOWN_APPS.get(exe_name)
    return app_info[0] if app_info else exe_name


def resolve_app_command(app: str) -> list[str]:
    """
    Resolve a short app identifier or command string into a dynamic process list.
    Examples:
        "code" -> ["/usr/bin/code"]
        "default" -> ["/usr/bin/xdg-open"]
        "gimp %f" -> ["/usr/bin/gimp"]"""

    app = app.strip()
    if not app or app.lower() in {"default", "xdg-open"}:
        return ["/usr/bin/xdg-open"]

    lower = app.lower()
    app_id_to_command = get_vscode_commands()

    if lower in app_id_to_command:
        command = app_id_to_command[lower]
        base_exe = command[0]
        if Path(base_exe).is_absolute() and Path(base_exe).exists():
            return command
        if shutil.which(base_exe):
            return command

    parts = shlex.split(app)
    if parts:
        if shutil.which(parts[0]) or (
            Path(parts[0]).is_absolute() and Path(parts[0]).exists()
        ):
            return parts

    log.warning(
        f"Could not resolve requested application '{app}'; falling back to xdg-open."
    )
    # Fallback
    return ["/usr/bin/xdg-open"]


# Execution ("open with")
# ---------------------------------------------------------------------------


def open_path(path: str, app: str) -> dict[str, Any]:
    """
    Open the given file path using the specified application.

    The application is started as a detached process so the caller
    does not have to wait for it to finish."""
    target = str(Path(path).expanduser())
    command = resolve_app_command(app) + [target]

    try:
        log.info(f"Opening '{target}' with {app}")
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"ok": True, "command": command}
    except Exception as exc:
        log.error(f"Could not open '{target}' with {app}: {exc}")
        return {"ok": False, "error": str(exc), "command": command}


# Registering new apps in the menu
# ---------------------------------------------------------------------------


def add_open_with_app(executable: str, name: str | None = None) -> dict[str, Any]:
    """
    Add a verified application or parse a .desktop file into the menu configuration.

    Workflow:
    1. Starts by launching kde default apps directory: /usr/share/applications/
    2. Then from the .desktop file it extracts the Exec= and Name=
    3. It removes custom arguments like %F %U ... and verifies if the binary exists
    4. Finally add app to apps.json and launches app immediately.

    Examples:
        add_open_with_app("/usr/share/applications/gimp.desktop")
        add_open_with_app("/usr/bin/code", name="VS Code")
    """

    executable_path = Path(executable).expanduser()

    if not executable_path.exists():
        msg = f"Executable not found: {executable_path}"
        log.warning(msg)
        return {"ok": False, "error": msg}

    if not executable_path.is_file():
        msg = f"The path is not a file: {executable_path}"
        log.warning(msg)
        return {"ok": False, "error": msg}

    app_name = name.strip() if isinstance(name, str) and name.strip() else None
    final_command_str = ""

    # Parse .desktop file
    if executable_path.suffix == ".desktop":
        try:
            exec_line = ""
            desktop_name = ""

            with open(executable_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("Exec="):
                        exec_line = line.replace("Exec=", "").strip()
                    elif line.startswith("Name=") and not desktop_name:
                        desktop_name = line.replace("Name=", "").strip()

            if not exec_line:
                msg = "Invalid .desktop file: Exec line missing."
                log.warning(f"{msg} ({executable_path})")
                return {"ok": False, "error": msg}

            clean_args = [
                part for part in shlex.split(exec_line) if not part.startswith("%")
            ]

            if not clean_args:
                msg = "Could not parse a valid command from .desktop file."
                log.warning(f"{msg} ({executable_path})")
                return {"ok": False, "error": msg}

            resolved_exe = shutil.which(clean_args[0])
            if not resolved_exe:
                msg = f"Application binary '{clean_args[0]}' not found in system PATH."
                log.warning(msg)
                return {"ok": False, "error": msg}

            final_command_str = " ".join([resolved_exe] + clean_args[1:])

            if not app_name:
                app_name = (
                    desktop_name
                    if desktop_name
                    else display_name_from_executable(Path(resolved_exe))
                )

        except Exception as e:
            msg = f"Failed to parse .desktop file: {str(e)}"
            log.error(msg)
            return {"ok": False, "error": msg}

    # Binary file path
    else:
        if not os.access(executable_path, os.X_OK):
            msg = f"The file does not have execute permission: {executable_path}"
            log.warning(msg)
            return {"ok": False, "error": msg}

        final_command_str = command_from_executable(executable_path)
        if not app_name:
            app_name = display_name_from_executable(executable_path)

    log.info(
        f"Successfully registered application '{app_name}' with command: '{final_command_str}'"
    )
    return {
        "ok": True,
        "name": app_name,
        "command": final_command_str,
    }
