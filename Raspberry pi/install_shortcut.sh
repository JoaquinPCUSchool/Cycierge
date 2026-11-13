#!/bin/bash
# Puts a "CyCierge Dashboard" icon on the desktop and in the app menu. Run once (re-run after moving the folder):
#     bash install_shortcut.sh
set -e
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
chmod +x "$DIR/run_dashboard.sh"
DESK="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
MENU="$HOME/.local/share/applications"
mkdir -p "$DESK" "$MENU"

make_entry() {
cat > "$1" <<DESKTOP
[Desktop Entry]
Type=Application
Name=CyCierge Dashboard
Comment=Door access and visitor monitoring
Exec="$DIR/run_dashboard.sh"
Path=$DIR
Icon=$DIR/cycierge.png
Terminal=false
Categories=Utility;
DESKTOP
chmod +x "$1"
gio set "$1" metadata::trusted true 2>/dev/null || true     # lets the desktop launch it without asking
}

make_entry "$DESK/CyCierge Dashboard.desktop"
make_entry "$MENU/cycierge-dashboard.desktop"
echo "Done. Double-click 'CyCierge Dashboard' on the desktop (or find it in the menu)."
echo "If the icon shows a question mark or asks what to do: right-click it > Allow Launching / Execute."
