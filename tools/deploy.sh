#!/bin/bash
set -e
REPO=~/Cycierge
WEB=/var/www/html/cycierge        # change to the folder that contains lib.php
APP=~/Desktop/SourceCode          # where the dashboard runs from (VideoCapture/ lives here too)
cd "$REPO" && git pull
sudo rsync -a --no-owner --no-group "$REPO/php/cycierge/" "$WEB/"
mkdir -p "$APP"
cd "$REPO/Raspberry pi"
cp Main.py report_view.py cy_theme.py cycierge.png run_dashboard.sh install_shortcut.sh "$APP/"
bash "$APP/install_shortcut.sh"
echo "deployed - close the old dashboard window, then double-click the CyCierge Dashboard icon"
