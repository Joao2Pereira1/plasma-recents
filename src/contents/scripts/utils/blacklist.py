#!/usr/bin/env python3

import os

HOME_DIR = os.path.expanduser("~")

# Paths that should never appear as recent directories.
BLACKLIST_EXACT = {
    "/",
    "/home",
    "/run",
    "/run/media",
    "/media",
    "/mnt",
    HOME_DIR,
}

# Generic system locations that should not be shown.
BLACKLIST_PREFIXES = (
    "/tmp/",
    "/proc/",
    "/sys/",
    "/dev/",
)


def is_path_blacklisted(target_path: str) -> bool:
    """Return True if a path is an unwanted system-level location."""

    if not target_path:
        return True

    # Normalize the path before checking it.
    target_path = os.path.abspath(os.path.normpath(target_path))

    # Ignore exact system roots.
    if target_path in BLACKLIST_EXACT:
        return True

    # Ignore paths inside generic system/runtime directories.
    if target_path.startswith(BLACKLIST_PREFIXES):
        return True

    return False
