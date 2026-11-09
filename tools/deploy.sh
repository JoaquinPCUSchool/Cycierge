#!/bin/bash
set -e
REPO=~/Cycierge
WEB=/var/www/html/cycierge        # change to the folder that contains lib.php
cd "$REPO" && git pull
sudo rsync -a --no-owner --no-group "$REPO/php/cycierge/" "$WEB/"
cp "$REPO/Raspberry pi/Main.py" "$REPO/Raspberry pi/report_view.py" ~/Desktop/SourceCode/
echo "deployed - now restart Main.py"
