import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import QtQuick.Dialogs as Dialogs
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.plasma.plasmoid
import "components" as Components

// Recents Tracker
// ----------------------------------------------------------------------------
// A KDE Plasma widget that shows recently used items grouped into three tabs:
//   1. VS Code workspaces/files
//   2. Recently opened files
//   3. Recently opened folders
//
// The Python helper is responsible for collecting the data. This file mainly
// handles the interface, user actions and filtering.
//
// Main parts of the widget:
// - VS Code / Files / Folders tabs
// - Fuzzy search
// - Open / Open with actions
// - Application management through apps.json
//
PlasmoidItem {
    id: root

    Plasmoid.icon: Qt.resolvedUrl("../icons/icon.svg")
    Plasmoid.title: "Recents Tracker"
    preferredRepresentation: compactRepresentation

    // UI state
    // ------------------------------------------------------------------

    // Message shown at the bottom of the widget.
    // Used for loading information, errors and successful actions.
    property string statusText: "Press Refresh to load recent items."

    // List of applications available in the "Open with..." menu.
    property var openWithApps: []

    // Path currently selected for the "Open with..." action.
    property string selectedOpenWithPath: ""

    // Absolute path to apps.json, used by the "Edit apps.json" menu entry.
    property string appsConfigPath: ""

    // Index of the tab currently shown (0 = VS Code, 1 = Files, 2 = Folders).
    property int currentTabIndex: 0

    // Search text.
    // Kept here so the search still works before the full widget is opened.
    property string searchQuery: ""

    // Recent items
    // ------------------------------------------------------------------
    //
    // The arrays contain the data received from Python.
    // The ListModels contain the data currently displayed by the ListView.
    //
    // Keeping these separate makes it easier to filter the original data
    // again whenever the search text or selected tab changes.
    //
    property var vscodeItems: []
    property var filesItems: []
    property var foldersItems: []

    ListModel { id: vscodeModel }
    ListModel { id: filesModel }
    ListModel { id: foldersModel }

    // Model currently bound to the ListView.
    readonly property var currentModel: currentTabIndex === 0 ? vscodeModel
                                       : currentTabIndex === 1 ? filesModel
                                       : foldersModel

    // Original data used when searching.
    readonly property var currentItems: currentTabIndex === 0 ? vscodeItems
                                       : currentTabIndex === 1 ? filesItems
                                       : foldersItems

    // Paths and small helper functions
    // ------------------------------------------------------------------

    // Absolute path to the Python helper script.
    readonly property string helperPath: decodeURIComponent(
        Qt.resolvedUrl("../scripts/main.py").toString().replace(/^file:\/\//, "")
    )

    // Quotes a value before passing it to the helper through the shell.
    // This is important for paths containing spaces or special characters.
    function shQuote(value) {
        return "'" + String(value).replace(/'/g, "'\\''") + "'"
    }

    // Converts a "file://..." URL (e.g. from a FileDialog) into a plain,
    // URL-decoded filesystem path.
    function localPathFromUrl(url) {
        var value = String(url)
        if (value.startsWith("file://")) {
            value = value.replace("file://", "")
        }
        return decodeURIComponent(value)
    }

    // Adds transparency to a theme color. Used for the
    // translucent background/border of the "kind" tag (Workspace/Folder/File).
    function transparentColor(baseColor, alpha) {
        return Qt.rgba(baseColor.r, baseColor.g, baseColor.b, alpha)
    }

    // Item type helpers
    // ------------------------------------------------------------------

    // Normalizes a "kind" string (from the helper's JSON) for comparisons:
    // lower-cased and trimmed.
    function normalizedKind(kind) {
        return String(kind || "").toLowerCase().trim()
    }

    // Text displayed in the item type badge.
    function kindLabel(kind) {
        const value = normalizedKind(kind)
        if (value === "workspace") return "Workspace"
        if (value === "folder" || value === "project" || value === "pasta" || value === "projeto") return "Folder"
        if (value === "file" || value === "ficheiro") return "File"
        return kind || "Item"
    }

    // Theme color associated with a given "kind", used for the item type badge.
    function kindColor(kind) {
        const value = normalizedKind(kind)
        if (value === "workspace") return Kirigami.Theme.negativeTextColor
        if (value === "folder" || value === "project" || value === "pasta" || value === "projeto") return Kirigami.Theme.neutralTextColor
        if (value === "file" || value === "ficheiro") return Kirigami.Theme.positiveTextColor
        return Kirigami.Theme.highlightColor
    }

    // Python helper communication
    // ------------------------------------------------------------------
    // Runs the Python helper (`main.py`) with the supplied arguments.
    //
    // `helperPath` contains the path to the Python helper.
    // `args` contains the command and any arguments passed to the helper.
    // The helper's output is passed to `callback` for further processing.
    //
    // Most operations that require filesystem or application information
    // are handled by the Python helper through this function.
    function runHelper(args, callback) {
        executable.exec("python3 " + shQuote(helperPath) + " " + args, callback)
    }

    // Core actions
    // ------------------------------------------------------------------

    // Refresh action
    // ------------------------------------------------------------------

    // Reloads all three tabs (VS Code / Files / Folders) by calling the
    // helper with no arguments and parsing its JSON response.
    function refresh() {
        statusText = "Loading recent items..."

        runHelper("", function(cmd, exitCode, exitStatus, stdout, stderr) {
            if (exitCode !== 0) {
                statusText = "Could not refresh recent items."
                console.log("refresh() failed:", exitCode, exitStatus, stderr)
                return
            }

            try {
                const payload = JSON.parse(stdout.trim())

                let newVscodeItems = []
                let newFilesItems = []
                let newFoldersItems = []

                // VS Code recents (workspaces + files opened via VS Code)
                if (payload.vscode) {
                    for (let i = 0; i < payload.vscode.length; ++i) {
                        let item = payload.vscode[i]
                        newVscodeItems.push({
                            name: String(item.name || ""),
                            path: String(item.path || ""),
                            kind: String(item.kind || "file")
                        })
                    }
                }

                // Recently opened files (system-wide, not VS Code-specific)
                if (payload.recent_files) {
                    for (let i = 0; i < payload.recent_files.length; ++i) {
                        let item = payload.recent_files[i]
                        newFilesItems.push({
                            name: String(item.name || ""),
                            path: String(item.path || ""),
                            kind: "file"
                        })
                    }
                }

                // Recently opened folders
                if (payload.recent_dirs) {
                    for (let i = 0; i < payload.recent_dirs.length; ++i) {
                        let item = payload.recent_dirs[i]
                        newFoldersItems.push({
                            name: String(item.name || ""),
                            path: String(item.path || ""),
                            kind: "folder"
                        })
                    }
                }

                root.vscodeItems = newVscodeItems
                root.filesItems = newFilesItems
                root.foldersItems = newFoldersItems

                // Update the visible list while keeping the current search.
                applyFilter()

                statusText = "Recent items updated."
            } catch (e) {
                statusText = "Could not load recent items."
                console.log("refresh() JSON parsing failed:", e.message)
                console.log("refresh() stdout:", stdout)
            }
        })
    }

    // Open with action
    // ------------------------------------------------------------------

    /// Loads the applications used by the "Open with..." menu.
    //
    // The Python helper reads apps.json and returns both the applications and
    // the location of the configuration file.
    function loadOpenWithApps() {
        runHelper("--list-apps", function(cmd, exitCode, exitStatus, stdout, stderr) {
            if (exitCode !== 0) {
                statusText = "Could not load applications."
                console.log("loadOpenWithApps() failed:", exitCode, exitStatus, stderr)
                return
            }

            try {
                const cleanStdout = stdout.trim()
                if (!cleanStdout) {
                    statusText = "No applications are configured."
                    return
                }

                const payload = JSON.parse(cleanStdout)
                if (!payload.ok) {
                    statusText = "Could not load applications. (nothing found inside apps.json)"
                    return
                }

                root.openWithApps = payload.apps || []
                root.appsConfigPath = payload.appsPath || ""
            } catch (e) {
                statusText = "Could not load application list."
                console.log("loadOpenWithApps() JSON parsing failed:", e.message)
                console.log("loadOpenWithApps() stdout:", cleanStdout)
            }
        })
    }

    // Opens a path using the selected application.
    // If no application is supplied, the system default is used.
    function openPath(targetPath, appCommand) {
        const app = appCommand && appCommand.length > 0 ? appCommand : "default"
        const args = "--open " + shQuote(targetPath) + " --app " + shQuote(app)

        runHelper(args, function(cmd, exitCode, exitStatus, stdout, stderr) {
            if (exitCode !== 0) {
                statusText = "Could not open the item."
            } else {
                statusText = app === "default"
                    ? "Opened with the default application."
                    : "Opened with " + app + "."
            }
        })
    }

    // Adds an application to apps.json.
    //
    // After adding it, the application list is refreshed and the selected
    // item is opened with the newly added application.
    function addOpenWithApp(executablePath) {
        statusText = "Adding application..."
        const args = "--add-app " + shQuote(executablePath)

        runHelper(args, function(cmd, exitCode, exitStatus, stdout, stderr) {
            if (exitCode !== 0) {
                statusText = "Could not add application."
                console.log("addOpenWithApp() failed:", exitCode, exitStatus, stderr)
                return
            }

            try {
                const payload = JSON.parse(stdout.trim())
                if (payload.ok) {
                    statusText = "Application added."

                    // Refresh the "Open with..." menu so the new app shows up.
                    root.loadOpenWithApps()

                    // Open the item that triggered "Add application..." with
                    // the app that was added.
                    if (payload.apps && payload.apps.length > 0) {
                        const lastApp = payload.apps[payload.apps.length - 1]
                        root.openPath(root.selectedOpenWithPath, lastApp.command)
                    } else {
                        root.openPath(root.selectedOpenWithPath, executablePath)
                    }
                } else {
                    statusText = "Could not add application."
                }
            } catch (e) {
                statusText = "Could not process application response."
                console.log("addOpenWithApp() JSON parsing failed:", e.message)
                console.log("addOpenWithApp() stdout:", stdout)
            }
        })
    }

    // Opens the "Open with..." menu for a specific item.
    function showOpenWithMenu(targetPath, button) {
        selectedOpenWithPath = targetPath
        // Load apps if they have not been loaded yet.
        if (!openWithApps || openWithApps.length === 0) {
            loadOpenWithApps()
        }
        openWithMenu.popup(button, 0, button.height)
    }

    // Copy path action
    // ------------------------------------------------------------------
    function copyPath(path) {
        // Send file or folder path to user clipboard
        const args = "--copy-path " + shQuote(path)

        runHelper(args, function(cmd, exitCode, exitStatus, stdout, stderr) {
            if (exitCode !== 0) {
                statusText = "Could not copy path."
                console.log("copyPath() failed:", exitCode, exitStatus, stderr)
                return
            }
        })
    }

    // Search
    // ------------------------------------------------------------------

    // Gives a score to a fuzzy match.
    function fuzzyMatch(query, target) {
        query = query.toLowerCase()
        target = target.toLowerCase()

        if (query.length === 0) return { match: true, score: 0 }

        let queryIdx = 0
        let score = 0
        let lastMatchIdx = -1
        let consecutiveBonus = 0

        for (let i = 0; i < target.length && queryIdx < query.length; i++) {
            if (target[i] === query[queryIdx]) {
                if (i === 0) score += 10

                if (lastMatchIdx === i - 1) {
                    consecutiveBonus += 5
                    score += consecutiveBonus
                } else {
                    consecutiveBonus = 0
                }

                if (i > 0 && /[\/_\-\s.]/.test(target[i - 1])) {
                    score += 8
                }

                score += 1
                lastMatchIdx = i
                queryIdx++
            }
        }

        const isMatch = queryIdx === query.length
        if (isMatch) score -= target.length * 0.1

        return { match: isMatch, score: isMatch ? score : -1 }
    }

    // Filters a list using the current search query.
    // Both the item name and its path are searched.
    function searchItems(query, items) {
        if (!query || query.length === 0) return items

        let results = []
        for (let item of items) {
            let nameMatch = fuzzyMatch(query, item.name)
            let pathMatch = fuzzyMatch(query, item.path)

            if (nameMatch.match || pathMatch.match) {
                // Prefer name matches over path-only matches.
                let finalScore = nameMatch.match ? nameMatch.score * 1.5 : pathMatch.score
                results.push({ item: item, score: finalScore })
            }
        }

        results.sort((a, b) => b.score - a.score)
        return results.map(r => r.item)
    }

    // Updates the visible list using the current tab and search query.
    function applyFilter() {
        const filtered = searchItems(root.searchQuery, currentItems)

        currentModel.clear()
        for (let item of filtered) {
            currentModel.append({
                display_name: item.name,
                display_path: item.path,
                display_kind: item.kind
            })
        }
    }

    // Backend: process execution
    // ------------------------------------------------------------------
    //
    // Plasma's executable DataSource is used to run the Python helper.
    // The callback system lets different operations wait for their own result.
    Plasma5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []

        property var callbacks: ({})

        // Runs a command and calls the callback when it finishes.
        function uniqueCommand(cmd) {
            let candidate = cmd

            while (connectedSources.indexOf(candidate) !== -1 || callbacks[candidate]) {
                candidate += " "
            }

            return candidate
        }

        // Receives the result of a command started by exec().
        function exec(cmd, callback) {
            const commandId = uniqueCommand(cmd)

            if (callback) {
                callbacks[commandId] = callback
            }

            connectSource(commandId)
        }

        onNewData: function(sourceName, data) {
            const callback = callbacks[sourceName]

            if (callback) {
                callback(
                    sourceName,
                    data["exit code"],
                    data["exit status"],
                    data["stdout"] || "",
                    data["stderr"] || ""
                )

                delete callbacks[sourceName]
            }

            // Release the source after consuming its output.
            disconnectSource(sourceName)
        }
    }

    // Dialogs & menus
    // ------------------------------------------------------------------

    // File picker used by "Add application..." to choose a .desktop entry.
    Dialogs.FileDialog {
        id: appFileDialog
        title: "Choose application"
        currentFolder: "file:///usr/share/applications"
        nameFilters: ["Applications (*.desktop)", "All files (*)"]

        onAccepted: {
            const appPath = root.localPathFromUrl(appFileDialog.selectedFile)
            addOpenWithApp(appPath)
        }
    }

    // Refresh items after plasmoid boot
    Component.onCompleted: {
        Qt.callLater(refresh)
    }

    // "Open with..." context menu: lists known apps plus management actions.
    Controls.Menu {
        id: openWithMenu

        Repeater {
            model: root.openWithApps

            delegate: Controls.MenuItem {
                text: modelData.name

                onTriggered: {
                    root.openPath(root.selectedOpenWithPath, modelData.command)
                }
            }
        }

        Controls.MenuSeparator {}

        Controls.MenuItem {
            text: "Add application..."
            onTriggered: appFileDialog.open()
        }

        Controls.MenuItem {
            text: "Reload applications"
            onTriggered: root.loadOpenWithApps()
        }

        Controls.MenuItem {
            text: "Edit apps.json"
            enabled: root.appsConfigPath.length > 0
            onTriggered: root.openPath(root.appsConfigPath, "default")
        }
    }

    // UI: compact representation (panel icon)
    // ------------------------------------------------------------------

    compactRepresentation: Item {
        id: compact

        Layout.minimumWidth: Kirigami.Units.iconSizes.medium
        Layout.minimumHeight: Kirigami.Units.iconSizes.medium
        Layout.preferredWidth: Kirigami.Units.iconSizes.medium
        Layout.preferredHeight: Kirigami.Units.iconSizes.medium

        Components.PlasmoidIcon {
            anchors.fill: parent
            customIcon: root.Plasmoid.icon
            activeIcon: compactMouse.containsMouse
        }

        MouseArea {
            id: compactMouse
            anchors.fill: parent
            hoverEnabled: true

            onClicked: root.expanded = !root.expanded
        }
    }

    // UI: full representation (expanded panel)
    // ------------------------------------------------------------------

    fullRepresentation: Item {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 22
        Layout.minimumHeight: Kirigami.Units.gridUnit * 20
        Layout.preferredWidth: Kirigami.Units.gridUnit * 30
        Layout.preferredHeight: Kirigami.Units.gridUnit * 34

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing * 2
            spacing: Kirigami.Units.smallSpacing

            // -- Header: title + manual refresh button -------------------
            RowLayout {
                Layout.fillWidth: true

                PlasmaComponents.Label {
                    text: "Recents Tracker"
                    font.bold: true
                    font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.2
                    Layout.fillWidth: true
                }

                Controls.Button {
                    text: "Refresh"
                    icon.name: "view-refresh"
                    onClicked: {
                        refresh()
                        loadOpenWithApps()
                    }
                }
            }

            // Search bar: fuzzy-filters the currently active tab
            Kirigami.SearchField {
                id: searchField
                Layout.fillWidth: true
                placeholderText: i18n("Search for items")

                // Re-filter the current tab on every keystroke.
                onTextChanged: {
                    root.searchQuery = text
                    root.applyFilter()
                }
            }

            // Tabs: switch which model is shown
            PlasmaComponents.TabBar {
                id: tabBar
                Layout.fillWidth: true
                currentIndex: 0

                // Switching tabs changes which raw array is the search
                // source, so re-run the filter against the new tab too.
                onCurrentIndexChanged: {
                    root.currentTabIndex = currentIndex
                    root.applyFilter()
                }

                PlasmaComponents.TabButton { text: "VS Code" }
                PlasmaComponents.TabButton { text: "Files" }
                PlasmaComponents.TabButton { text: "Folders" }
            }

            // Status line (loading / success / error feedback)
            PlasmaComponents.Label {
                Layout.fillWidth: true
                text: statusText
                opacity: 0.6
                font.pointSize: Kirigami.Theme.defaultFont.pointSize * 0.9
                elide: Text.ElideMiddle
                maximumLineCount: 1
            }

            // Item list, bound to the currently selected tab's (filtered) model
            Controls.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true



                ListView {
                    id: listView
                    model: root.currentModel // swapped on tab change
                    spacing: Kirigami.Units.smallSpacing
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Controls.ItemDelegate {
                        width: listView.width
                        implicitHeight: itemLayout.implicitHeight + Kirigami.Units.smallSpacing * 2

                        // Double click performs the same action as the "Open" button
                        onDoubleClicked: {
                            if (tabBar.currentIndex === 0) {
                                // VS Code tab
                            } else {
                                // Files/Folders tabs
                                let fileUrl = "file://" + model.display_path
                                console.log("Opening with default handler:", fileUrl)
                                Qt.openUrlExternally(fileUrl)
                            }
                        }

                        contentItem: ColumnLayout {
                            id: itemLayout
                            spacing: Kirigami.Units.smallSpacing

                            // Name + kind tag (Workspace/Folder/File)
                            RowLayout {
                                Layout.fillWidth: true

                                PlasmaComponents.Label {
                                    text: model.display_name
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }

                                Rectangle {
                                    Layout.alignment: Qt.AlignVCenter
                                    implicitWidth: kindText.implicitWidth + Kirigami.Units.largeSpacing
                                    implicitHeight: kindText.implicitHeight + Kirigami.Units.smallSpacing
                                    radius: Kirigami.Units.smallSpacing
                                    color: root.transparentColor(root.kindColor(model.display_kind), 0.18)
                                    border.color: root.transparentColor(root.kindColor(model.display_kind), 0.65)
                                    border.width: 1

                                    PlasmaComponents.Label {
                                        id: kindText
                                        anchors.centerIn: parent
                                        text: root.kindLabel(model.display_kind).toUpperCase()
                                        color: root.kindColor(model.display_kind)
                                        font.bold: true
                                        font.pointSize: Kirigami.Theme.defaultFont.pointSize * 0.8
                                    }
                                }
                            }

                            // Full path (elided from the left, so the file
                            // name — the most relevant part — stays visible)
                            PlasmaComponents.Label {
                                Layout.fillWidth: true
                                text: model.display_path
                                opacity: 0.5
                                font.pointSize: Kirigami.Theme.defaultFont.pointSize * 0.9
                                elide: Text.ElideLeft
                                maximumLineCount: 1
                            }

                            // Row of actions: primary "open" + "open with..."
                            RowLayout {
                                Layout.fillWidth: true

                                Controls.Button {
                                    text: tabBar.currentIndex === 0 ? "Open in Code" : "Open"
                                    icon.name: tabBar.currentIndex === 0 ? "vscode" : "document-open"

                                    onClicked: {
                                        if (tabBar.currentIndex === 0) {
                                            // VS Code tab: always open via the
                                            // helper so it's launched with `code`.
                                            root.openPath(model.display_path, "code")
                                        } else {
                                            // Files/Folders tabs: let KDE Plasma
                                            // pick the default handler natively.
                                            let fileUrl = "file://" + model.display_path
                                            console.log("Opening with default handler:", fileUrl)
                                            Qt.openUrlExternally(fileUrl)
                                        }
                                    }
                                }

                                Controls.Button {
                                    id: openWithButton
                                    text: "Open with..."
                                    icon.name: "system-run"
                                    onClicked: root.showOpenWithMenu(model.display_path, openWithButton)
                                }

                                Controls.Button {
                                    id: copyPathButton
                                    text: "Copy path"
                                    icon.name: "path"
                                    onClicked: root.copyPath(model.display_path)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
