#!/usr/bin/env bash
# Starts mimi in the background on macOS / Linux (keeps running after you close the terminal).
# mimi.py restarts itself on crashes, so this just launches it once.

cd "$(dirname "$0")" || exit 1

if pgrep -f "mimi.py" >/dev/null 2>&1; then
    echo "mimi is already running."
    exit 0
fi

nohup python3 mimi.py >/dev/null 2>&1 &
echo "mimi started (PID $!)."
