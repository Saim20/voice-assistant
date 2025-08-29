#!/bin/bash

# Status check script for nerd-dictation voice assistant
# Returns 0 if running, 1 if not running

# Define the paths for the status file
STATUS_FILE="/tmp/nerd-dictation.status"

# Check status file first
if [ -f "$STATUS_FILE" ]; then
    # Double-check with process list to ensure it's actually running
    if pgrep -f "nerd-dictation" > /dev/null 2>&1; then
        echo "running"
        exit 0
    else
        # Status file exists but process is not running - clean up
        rm -f "$STATUS_FILE" 2>/dev/null
        echo "stopped"
        exit 1
    fi
else
    # No status file, check if process is running anyway
    if pgrep -f "nerd-dictation" > /dev/null 2>&1; then
        # Process running but no status file - create it
        touch "$STATUS_FILE" 2>/dev/null
        echo "running"
        exit 0
    else
        echo "stopped"
        exit 1
    fi
fi
