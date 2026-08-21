#!/usr/bin/env python3

import os
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse
from logger import log
from utils.blacklist import is_path_blacklisted


def get_xbel_recent_items(limit):
    """Extract recently opened files and directories from KDE's XBEL history.

    Files:
        Added when the XBEL entry points to an existing file.

    Directories:
        Added when the XBEL entry points directly to an existing directory.
        The parent directory of a recent file is also added.

    Args:
        limit (int): Maximum number of items to return for each category.

    Returns:
        tuple[list[dict], list[dict]]:
            Two lists containing dictionaries formatted as:
            {'name': str, 'path': str}
    """

    xbel_path = os.path.expanduser("~/.local/share/recently-used.xbel")

    recent_files = []
    recent_dirs = []

    # Fallback guard in case the XBEL file does not exist yet
    if not os.path.exists(xbel_path):
        return recent_files, recent_dirs

    try:
        tree = ET.parse(xbel_path)
        root = tree.getroot()

        bookmarks = root.findall("bookmark")

        # XBEL stores oldest entries first.
        # Reverse to process the most recent entries first.
        bookmarks.reverse()

        # Remove duplicates while preserving insertion order.
        seen_files = set()
        seen_dirs = set()

        for bookmark in bookmarks:
            href = bookmark.get("href")

            # Ignore invalid entries or non-local resources.
            if not href or not href.startswith("file://"):
                continue

            # Convert file:// URI to a local filesystem path.
            parsed_uri = urlparse(href)
            absolute_path = unquote(parsed_uri.path)

            if not absolute_path:
                continue

            # CATEGORY 1: Recent Files
            # ---------------------------------------------------------
            if os.path.isfile(absolute_path):
                if (
                    absolute_path not in seen_files
                    and len(recent_files) < limit
                    and not is_path_blacklisted(absolute_path)
                ):
                    seen_files.add(absolute_path)

                    recent_files.append(
                        {
                            "name": os.path.basename(absolute_path),
                            "path": absolute_path,
                        }
                    )

                # CATEGORY 2: Parent directory of a recent file
                # -----------------------------------------------------
                parent_dir = os.path.dirname(absolute_path)

                if (
                    os.path.isdir(parent_dir)
                    and parent_dir not in seen_dirs
                    and len(recent_dirs) < limit
                    and not is_path_blacklisted(parent_dir)
                ):
                    seen_dirs.add(parent_dir)

                    recent_dirs.append(
                        {
                            "name": os.path.basename(parent_dir) or parent_dir,
                            "path": parent_dir,
                        }
                    )

            # CATEGORY 3: Recent Directories
            # ---------------------------------------------------------
            elif os.path.isdir(absolute_path):
                if (
                    absolute_path not in seen_dirs
                    and len(recent_dirs) < limit
                    and not is_path_blacklisted(absolute_path)
                ):
                    seen_dirs.add(absolute_path)

                    recent_dirs.append(
                        {
                            "name": os.path.basename(absolute_path) or absolute_path,
                            "path": absolute_path,
                        }
                    )

            # CATEGORY 4: Missing / invalid paths
            # ---------------------------------------------------------
            else:
                log.warning(f"Skipping unavailable path: {absolute_path}")

    except ET.ParseError as e:
        log.warning(f"Failed to parse XBEL file: {e}")

    return recent_files, recent_dirs
