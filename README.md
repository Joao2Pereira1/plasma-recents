# KRecentTracker

KRecentTracker is a KDE Plasma 6 widget that tracks recently opened files, folders, and workspaces from KDE and VS Code-based editors.

## Features

📁 **Recent Files & Folders**  
Show recently opened files and directories in a simple KDE Plasma widget.

💻 **VS Code Integration**  
Track recent files, folders, and workspaces from VS Code and compatible variants such as Code - OSS and VSCodium.

🔎 **Fuzzy Search**  
Quickly find items within each recent-items tab.

📂 **Open With**  
Open an item with the default system handler or choose another application from the "Open With" menu.

⭐ **Favorites**  
Pin frequently used files, folders, or workspaces so they remain easily accessible.

📋 **Copy Path**  
Quickly copy the full path of an item.

🖱️ **Double-click**  
Double-click an item to open it with the default system handler.

⚙️ **Configurable**  
Configure options such as the VS Code database path and the number of displayed items.

## Screenshots

<div align="center">
  <img src="screenshots/files_tab.png" width="600" height="400">
  <img src="screenshots/folders_tab.png" width="600" height="400">
  <img src="screenshots/horizontal_layout.png" width="600" height="400">
  <img src="screenshots/search.png" width="600" height="400">
  <img src="screenshots/vscode_tab.png" width="600" height="400">
</div>


> More screenshots incoming.

## Compatibility

Compatible with KDE Plasma 6.

The widget currently focuses on Linux and KDE Plasma environments.

## Supported Sources

Currently supported:

- KDE recent files (`recently-used.xbel`)

- Visual Studio Code

- Code - OSS

- VSCodium

- Other compatible VS Code-based installations

## Installation

KRecentTracker is currently under development and does not have an official installation method yet.

We plan to release the plasmoid through the **KDE Store**. An `installer.sh` script is also planned to make manual installation easier.

Installation instructions will be added once these methods are ready.

## Configuration

The widget uses separate JSON files for persistent data:

```text
config.json
├── max_items
├── page_size
├── show_missing_files
├── vscode_db_path
├── excluded_directories
├── show_vscode_tab
└── ...

apps.json
└── Applications available in "Open With"

history.json
├── App usage
├── Favorites
└── Frecency data
```

The configuration format is still being developed and may change before the first stable release.

## Project Status

KRecentTracker is currently under active development.

Some features are already implemented, while others are planned and tracked in `improvements.md`.

The project structure and configuration format may change before the first stable release.

## License

This project is licensed under the GNU General Public License v3.0.

See the `LICENSE` file for details.
