#!/bin/bash

# Enhanced mode changer script for voice assistant
# Changes mode with optional suspend/resume of nerd-dictation for clean transitions

MODE_FILE="/tmp/nerd-dictation.mode"
BUFFER_FILE="/tmp/nerd-dictation.buffer"

# Check if a mode was provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <mode>"
    echo "Modes: normal, command, typing"
    exit 1
fi

NEW_MODE="$1"

# Validate mode
case "$NEW_MODE" in
    "normal"|"command"|"typing")
        ;;
    *)
        echo "Error: Invalid mode '$NEW_MODE'"
        echo "Valid modes: normal, command, typing"
        exit 1
        ;;
esac

echo "Changing mode to: $NEW_MODE"

# Check if nerd-dictation is running before trying to suspend/resume
if pgrep -f "nerd-dictation" > /dev/null; then
    # Suspend nerd-dictation briefly for clean transition
    nerd-dictation suspend 2>/dev/null || true
    
    # Brief pause to ensure suspension
    sleep 0.3
    
    # Set the mode
    echo "$NEW_MODE" > "$MODE_FILE"
    
    # Clear the buffer file after mode change
    echo "" > "$BUFFER_FILE" 2>/dev/null || true
    
    # Resume nerd-dictation
    nerd-dictation resume 2>/dev/null || true
    
    echo "Mode changed to $NEW_MODE (with suspend/resume)"
else
    # nerd-dictation not running, just change the mode file
    echo "$NEW_MODE" > "$MODE_FILE"
    echo "Mode changed to $NEW_MODE (nerd-dictation not running)"
fi

# Exit successfully
exit 0
