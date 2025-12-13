#!/bin/bash
# Composure Quick Open Script
# Opens the most recent screenshot from ~/Pictures in Composure
# 
# Usage:
#   1. Take a screenshot with Print Screen (GNOME's built-in)
#   2. Press Alt+Shift+W to open it in Composure

COMPOSURE_DIR="/home/nick/.gemini/antigravity/Composure"
PICTURES_DIR="$HOME/Pictures"

# Find the most recent screenshot
LATEST=$(ls -t "$PICTURES_DIR"/Screenshot*.png 2>/dev/null | head -1)

if [ -z "$LATEST" ] || [ ! -f "$LATEST" ]; then
    notify-send "Composure" "No screenshots found in ~/Pictures" 2>/dev/null
    exit 1
fi

# Check how old the file is (warn if older than 5 minutes)
NOW=$(date +%s)
FILE_TIME=$(stat -c %Y "$LATEST" 2>/dev/null || echo "0")
AGE=$((NOW - FILE_TIME))

if [ $AGE -gt 300 ]; then
    # Older than 5 minutes, still open but notify
    notify-send "Composure" "Opening screenshot ($(($AGE / 60)) min old)..." 2>/dev/null
else
    notify-send -i "$LATEST" "Composure" "Opening latest screenshot..." 2>/dev/null
fi

# Kill existing Composure and launch with the screenshot
pkill -f "python3 -m src.main" 2>/dev/null
sleep 0.2

cd "$COMPOSURE_DIR"
python3 -m src.main "$LATEST" &

exit 0
