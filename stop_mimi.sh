#!/usr/bin/env bash
# Stops mimi on macOS / Linux.

if pkill -f "mimi.py"; then
    echo "mimi stopped."
else
    echo "mimi was not running."
fi
