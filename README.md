<div align="center">
  <h1>📁 Plasma Recents</h1>

  <a href="https://quickshell.org/">
    <img src="https://img.shields.io/badge/QuickShell-000000?style=for-the-badge&logo=linux&logoColor=white" alt="QuickShell">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://store.kde.org/p/2369537">
    <img src="https://img.shields.io/badge/KDE%20Store-1D99F3?style=for-the-badge&logo=kde&logoColor=white" alt="KDE Store">
  </a>
  <a href="https://ko-fi.com/joao_pereira">
    <img src="https://img.shields.io/badge/Ko--fi-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Ko-fi">
  </a>
  <a href="https://www.paypal.com/donate/?hosted_button_id=TD3SCYXU5BTQY">
    <img src="https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="Donate with PayPal">
  </a>
</div>

Plasma Recents is a KDE Plasma 6 widget that provides **quick access** to recently opened files, folders, workspaces, images, videos, and other items. It combines recent items from KDE and VS Code-based editors into a single, lightweight interface with quick actions for interacting with them.

<table>
  <tr>
    <td align="center">
      <img src="screenshots/vscode_tab.png" width="280" height="500">
    </td>
    <td align="center">
      <img src="screenshots/files_tab.png" width="280" height="500">
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="screenshots/horizontal_layout.png" width="500" height="300">
    </td>
    <td align="center">
      <img src="screenshots/search.png" width="500" height="300">
    </td>
  </tr>
</table>

## Demo

https://github.com/user-attachments/assets/5fa41cc4-5a32-432b-85d9-b61b0cc78817

## Why Plasma Recents?

- 🪶 **Lightweight, no indexing** — unlike **Baloo**, it doesn't index the filesystem; it reads recent-item info directly from KDE and VS Code-based editors.
- 📌 **Focused scope** — while the Plasma launcher shows recent items generically, this widget is dedicated to **files, folders, and projects**.
- ⚡ **Quick actions** — *Copy Path*, *Open With*, and double-click, directly on the items.

**Goal:** bring files, folders, and VS Code projects together in one place, with actions that are useful in everyday workflows.

## Features

📁 **Recent Files & Folders**  
Show recently opened files and directories in a simple KDE Plasma widget.

💻 **VS Code Integration**  
Track recent files, folders, and workspaces from VS Code and compatible variants such as Code - OSS and VSCodium.

🔎 **Fuzzy Search**  
Quickly find items within each recent-items tab.

📂 **Open With**  
Open an item with the default system handler or choose another application from the "Open With" menu.

📋 **Copy Path**  
Quickly copy the full path of an item.

🖱️ **Double-click**  
Double-click an item to open it with the default system handler.

## Incoming Features

The following features are planned for upcoming releases of Plasma Recents. They are focused on improving usability, customization, and interaction with recent items.

- **Open in Terminal** — quickly open the location of a recent file or directory in the user's default terminal. Files will open in their parent directory, while directories will open directly in that location.

- **Configurable Item Limit** — allow users to control how many recent items are retrieved and displayed, making it possible to reduce clutter or access a larger history of recent items.

- **Show or Hide Tabs** — allow individual sections such as VS Code, files, and directories to be enabled or disabled according to the user's preferences.

- **Favorites / Pinned Items** — allow frequently used files and directories to be pinned so they remain easily accessible independently of their recent-item history.

- **Multi-selection & Batch Actions** — support file-manager-style selection with `Ctrl + Click` and `Shift + Click`, enabling actions to be performed on multiple recent items at once, such as opening several items or copying their paths.

## Use Cases

- **Quickly** find and access files, folders, and projects you've recently used — without navigating through your filesystem again.

- **Recent files** — Find documents, images, videos, screenshots, and other files you opened recently.

- **Projects** — Quickly access VS Code and other editor workspaces.
Quick actions — Copy paths, open items with a specific application, or use them directly from a terminal.

- **Lost something?** — If you remember "I just opened that file, but where was it?", the plasmoid helps you find it again.

## Supported Sources

The plasmoid collects recently opened items from 2 sources:

### VS Code and VS Code-based editors

Reads the editor's .vscdb SQLite database to retrieve recently opened files, folders, and workspaces — without launching the editor.

### Other applications

Reads KDE's XBEL (.xbel) history to retrieve recently accessed files and locations.

Both sources are combined into a single list, giving you one place to access recent files, folders, projects, and other content.

## Target Audience

Designed for KDE Plasma users who want a faster way to access recently used content.

It is simple enough for beginners while providing useful shortcuts for experienced users, such as copying paths, opening items in a terminal, or choosing a specific application.

The goal: make recently used content faster and easier to find.

## Compatibility

Compatible with KDE Plasma 6.

The widget currently focuses on Linux and KDE Plasma environments.

## Dependencies

Plasma Recents is designed for KDE Plasma 6 and has no additional third-party dependencies.

The following components are required:

* **KDE Plasma 6** — required to run the plasmoid.
* **Python 3** — required by the helper scripts used for VS Code integration.
* **kpackagetool6** — used by the installer to install and update the plasmoid package.

## Installation

Clone the repository and run the installation script:

```bash
git clone https://github.com/joao2pereira1/plasma-recents.git
cd plasma-recents
```

Before running the installer for the first time, make sure the script has permission to execute:

```bash
chmod +x installer.sh
```

Then run the installation script:

```bash
./installer.sh
```

The installer automatically installs the plasmoid using `kpackagetool6`.

The installer automatically uses kpackagetool6 to install the plasmoid package. If kpackagetool6 is not available on your system, the installer will attempt to install it automatically.

However, it is recommended to install kpackagetool6 manually beforehand to ensure that the required KDE package management tool is available:

```bash
# Ubuntu / Debian
sudo apt install kpackagetool6

# Arch Linux
sudo pacman -S kpackagetool6

# Fedora
sudo dnf install kf6-kpackage
```

> **Note:** Package names may vary slightly depending on the distribution version and KDE Plasma packages available in your repositories. The installer will also attempt to install kpackagetool6 automatically if it is not found.

Once the installation is complete, open the KDE Plasma widget explorer and add **Plasma Recents** to your desktop or panel.

> **Note:** Plasma Recents is currently under development. An official release through the **KDE Store** is planned for the future.

## CLI

Plasma Recents includes a Python CLI to interact with the backend without opening the widget, mainly useful for development and debugging.

Commands should be run from the directory containing `main.py`:

bash

```bash
python main.py <command>
```

| Command                     | Function                                                                   |
| --------------------------- | -------------------------------------------------------------------------- |
| `-h`, `--help`              | Show CLI help                                                              |
| `--list-dbs`                | List detected SQLite databases                                             |
| `--inspect-dbs`             | Inspect database contents (useful when developing parsers)                 |
| `--list-apps`               | List configured applications                                               |
| `--apps-path`               | Show the paths used to locate configured applications                      |
| `--add-app <path>`          | Add an application by its executable path (e.g. `--add-app /usr/bin/code`) |
| `--open <path> --app <app>` | Open a file/folder with the given application                              |
| `--copy-path <path>`        | Copy an item's absolute path to the clipboard                              |
| *(no arguments)*            | Run the backend normally, producing the JSON consumed by the QML frontend  |

> You can create a shell alias (e.g. `alias recent-tracker='python /path/to/main.py'`) in `~/.bashrc` or `~/.config/fish/config.fish` to use the CLI from any directory without typing the full path.

## Development and Testing

The CLI lets you test individual backend components without launching the plasmoid — generally faster than repeatedly interacting with the QML interface.

Typical development workflow:

bash

```bash
python main.py --list-dbs
python main.py --inspect-dbs
python main.py --list-apps
python main.py --apps-path
python main.py --open /tmp/test.txt --app kate
python main.py --copy-path /tmp/test.txt
```

After verifying the backend, test the widget with:

```bash
plasmoidviewer --applet Pereira.RecentsTracker
```

If the plasmoid is already running in the Plasma panel and you need to reload changes:

```bash
plasmashell --replace & disown
```

## Configuration and Data

Plasma Recents stores its persistent configuration and runtime data in the user's XDG directories.

### Configuration

```
~/.config/recents-tracker-widget/
├── config.json    # widget configuration (max_items, page_sizes, vscode_db_path, ...)
├── apps.json      # applications available through "Open With"
└── history.json   # usage, favorites, and frecency data
```

`config.json` includes, among others: `max_items`, `page_sizes`, `missing_files`, `vscode_db_path`, `excluded_directories`, `show_vscode_tab`.

> ⚠️ The configuration format is still under development and may change or be only partially implemented.

### Logs

```
~/.local/state/recent-tracker/
```

Useful for diagnosing backend or plasmoid issues — for example, when an item isn't detected, an application fails to launch, or a database parser behaves unexpectedly. Check the logs before debugging the QML frontend.

## Quick Reference

| Location                                        | Purpose                     |
| ----------------------------------------------- | --------------------------- |
| `~/.config/recents-tracker-widget/`             | Persistent configuration    |
| `~/.config/recents-tracker-widget/config.json`  | Widget configuration        |
| `~/.config/recents-tracker-widget/apps.json`    | Configured applications     |
| `~/.config/recents-tracker-widget/history.json` | Favorites and usage history |
| `~/.local/state/recent-tracker/`                | Runtime logs                |

## Project Status

Plasma Recents is currently under active development.

Many features are planned and being implemented. The project structure, CLI, configuration format, and internal APIs may change before the first stable release.

## License

This project is licensed under the GNU General Public License v3.0.

See the [LICENSE](LICENSE) file for details.
