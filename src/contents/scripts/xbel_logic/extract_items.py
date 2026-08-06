import os
import xml.etree.ElementTree as ET
from urllib.parse import unquote
from utils import is_path_blacklisted


def get_xbel_recent_items(limit=15):
    """Extract recently opened files and directories by applications in KDE (e.g., Kate, Dolphin).

    Extraction logic:
    - Files: Identified via valid 'file://' URIs existing on the filesystem.
    - Directories: Extracted by trimming the filename (os.path.dirname)
      or detected directly when the URI points to a folder.
    Args:
        limit (int): Maximum number of items to return for each category.
    Returns:
        tuple[list[dict], list[dict]]: Two lists of dictionaries formatted as
        {'name': str, 'path': str}, one for files and another for directories.
    """

    xbel_path = os.path.expanduser("~/.local/share/recently-used.xbel")
    recent_files = []
    recent_dirs = []

    # Fallback guard in case the XBEL file does not exist yet on the system
    if not os.path.exists(xbel_path):
        return recent_files, recent_dirs

    try:
        tree = ET.parse(xbel_path)
        root = tree.getroot()

        bookmarks = root.findall("bookmark")

        # XBEL stores oldest first, reverse it to process the most recent items first
        bookmarks.reverse()

        seen_files = set()
        seen_dirs = set()

        for bookmark in bookmarks:
            href = bookmark.get("href")
            # Ignore invalid entries or schemes that are not local files
            if not href or not href.startswith("file://"):
                continue

            # Convert URI (e.g., file:///path/with%20space) to a clean absolute local path
            absolute_path = unquote(href.replace("file://", ""))

            if os.path.isfile(absolute_path):
                # CATEGORY 1: Recent Files Category
                if absolute_path not in seen_files and len(recent_files) < limit:
                    seen_files.add(absolute_path)
                    recent_files.append(
                        {"name": os.path.basename(absolute_path), "path": absolute_path}
                    )

                # CATEGORY 2: Recent Folders Category (Extracted from file paths)
                parent_dir = os.path.dirname(absolute_path)
                if (
                    os.path.isdir(parent_dir)
                    and parent_dir not in seen_dirs
                    and not is_path_blacklisted(parent_dir)
                ):
                    if len(recent_dirs) < limit:
                        seen_dirs.add(parent_dir)
                        recent_dirs.append(
                            {
                                "name": os.path.basename(parent_dir) or parent_dir,
                                "path": parent_dir,
                            }
                        )

                # CATEGORY 3: Direct directories (e.g., opened in file manager)
                if absolute_path not in seen_dirs and not is_path_blacklisted(
                    absolute_path
                ):
                    if len(recent_dirs) < limit:
                        seen_dirs.add(absolute_path)
                        recent_dirs.append(
                            {
                                "name": os.path.basename(absolute_path)
                                or absolute_path,
                                "path": absolute_path,
                            }
                        )

    except ET.ParseError:
        pass
    except Exception:
        pass

    return recent_files, recent_dirs
