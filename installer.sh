#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PLASMOID_ID="Pereira.RecentsTracker"
PLASMOID_DIR="$SCRIPT_DIR/src"

log() {
    echo "[install] $*"
}

error() {
    echo "[error] $*" >&2
    exit 1
}

check_dependencies() {
    command -v python3 >/dev/null 2>&1 ||
        error "python3 not found."

    command -v kpackagetool6 >/dev/null 2>&1 ||
        error "kpackagetool6 not found. KDE Plasma 6 is required."
}

install_plasmoid() {
    log "Installing KRecentTracker..."

    [[ -d "$PLASMOID_DIR" ]] ||
        error "Package not found: $PLASMOID_DIR"

    [[ -f "$PLASMOID_DIR/metadata.json" ]] ||
        error "metadata.json not found in $PLASMOID_DIR"

    if kpackagetool6 \
        --type Plasma/Applet \
        --show "$PLASMOID_ID" >/dev/null 2>&1; then

        log "Existing installation found. Updating..."
        kpackagetool6 \
            --type Plasma/Applet \
            --upgrade "$PLASMOID_DIR"
    else

        log "Installing for the first time..."
        kpackagetool6 \
            --type Plasma/Applet \
            --install "$PLASMOID_DIR"
    fi
}

main() {
    check_dependencies
    install_plasmoid

    echo
    log "KRecentTracker installed successfully."
    log "You can add it through the KDE Plasma widget explorer."
}

main "$@"
