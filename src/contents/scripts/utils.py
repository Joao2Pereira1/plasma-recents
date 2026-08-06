#!/usr/bin/env python3

import os

# Base system folders and generic roots are ignored to avoid unnecessary items
HOME_DIR = os.path.expanduser("~")

BLACKLIST_PREFIXES = (
    os.path.join(HOME_DIR, "Downloads"),
    "/tmp/",
    "/run/media/",
    "/media/",
    "/mnt/",
)


def is_path_blacklisted(target_path: str) -> bool:
    """Verifies if path is identical to a system root or resides inside a blacklisted directory."""
    if target_path in {HOME_DIR, "/", "/home", "/run", "/run/media"}:
        return True

    if target_path.startswith(BLACKLIST_PREFIXES):
        return True

    return False
