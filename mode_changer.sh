#!/bin/bash
# Change mode with automatic nerd-dictation suspend/resume
# Usage: ./mode_changer.sh <mode>

MODE="$1"
MODE_FILE="/tmp/nerd-dictation.mode"
BUFFER_FILE="/tmp/nerd-dictation.buffer"

if [ -z "$MODE" ]; then
    echo "No mode provided"
    exit 1
fi

# Suspend nerd-dictation
nerd-dictation suspend 2>/dev/null

# Brief pause to ensure suspension
sleep 0.3

# Resume nerd-dictation
nerd-dictation resume 2>/dev/null

# Set the mode
echo "$MODE" > "$MODE_FILE"

# Clear the buffer file after mode change
echo "Clearing buffer file..."
echo "" > "$BUFFER_FILE" 2>/dev/null || true


# Exit successfully
exit 0
