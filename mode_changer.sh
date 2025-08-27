#!/bin/bash
# Set mode with automatic nerd-dictation suspend/resume
# Usage: ./mode_changer.sh "mode_name"

MODE="$1"
MODE_FILE="/tmp/nerd-dictation.mode"

if [ -z "$MODE" ]; then
    echo "No mode provided"
    exit 1
fi

# Suspend nerd-dictation
nerd-dictation suspend 2>/dev/null

# Brief pause to ensure suspension
sleep 0.4

# Resume nerd-dictation
nerd-dictation resume 2>/dev/null

# Set the mode
echo "$MODE" > "$MODE_FILE"

# Exit successfully
exit 0
