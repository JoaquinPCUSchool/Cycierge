#!/bin/bash
# Started by the CyCierge desktop icon: runs Main.py from this folder and keeps a log.
# Output goes to ~/cycierge-dashboard.log (run `python3 Main.py` in a terminal to see it live).
cd "$(dirname "$(readlink -f "$0")")" || exit 1
export DISPLAY="${DISPLAY:-:0}"

# one dashboard at a time: a second double-click would open a second set of camera streams/recordings
exec 9>/tmp/cycierge-dashboard.lock
flock -n 9 || exit 0

LOG="$HOME/cycierge-dashboard.log"
[ -f "$LOG" ] && [ "$(stat -c%s "$LOG")" -gt 1000000 ] && : > "$LOG"
echo "=== $(date '+%F %T') start ===" >> "$LOG"
exec python3 Main.py >> "$LOG" 2>&1
