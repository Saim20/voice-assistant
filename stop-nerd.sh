#!/bin/bash

# Define the paths for the status, mode, and cursor files.
STATUS_FILE="/tmp/nerd-dictation.status"
MODE_FILE="/tmp/nerd-dictation.mode"
CURSOR_FILE="/tmp/nerd-dictation.cursor"
TYPING_CURSOR_FILE="/tmp/nerd-dictation.typing-cursor"

# Check if nerd-dictation is currently running.
if [ -f "$STATUS_FILE" ]; then
    echo "Nerd Dictation is running. Ending process and clearing files."
    
    nerd-dictation end
    
    # Remove all temporary files.
    rm "$STATUS_FILE"
    rm "$MODE_FILE"
    rm "$CURSOR_FILE"
    rm "$TYPING_CURSOR_FILE"
else
    echo "Nerd Dictation is not running. Clearing files just in case."
    
    if [ -f "$STATUS_FILE" ]; then rm "$STATUS_FILE"; fi
    if [ -f "$MODE_FILE" ]; then rm "$MODE_FILE"; fi
    if [ -f "$CURSOR_FILE" ]; then rm "$CURSOR_FILE"; fi
    if [ -f "$TYPING_CURSOR_FILE" ]; then rm "$TYPING_CURSOR_FILE"; fi
fi
