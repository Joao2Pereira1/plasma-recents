#!/usr/bin/env python3

"""Copy file or folder path to user clipboard."""

import os
import subprocess


def get_session_type():
    """Return the current graphical session type."""
    return os.environ.get("XDG_SESSION_TYPE", "").lower()


def copy_to_clipboard(path):
    """Copy path to user clipboard."""
    session_type = get_session_type()

    if session_type == "wayland":
        command = ["wl-copy"]
    elif session_type == "x11":
        command = ["xclip", "-selection", "clipboard"]
    else:
        return False

    try:
        subprocess.run(command, input=path, text=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
