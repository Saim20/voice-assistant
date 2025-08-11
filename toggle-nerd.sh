#!/bin/bash

# Define the path for your single configuration file.
CONFIG_FILE="$HOME/.config/nerd-dictation/voice_assistant_improved.py"

# Define the paths for the status, mode, and cursor files.
STATUS_FILE="/tmp/nerd-dictation.status"
MODE_FILE="/tmp/nerd-dictation.mode"
CURSOR_FILE="/tmp/nerd-dictation.cursor"
TYPING_CURSOR_FILE="/tmp/nerd-dictation.typing-cursor"

# Function to reset assistant state
reset_assistant_state() {
    echo "normal" > "$MODE_FILE"
    echo "0" > "$CURSOR_FILE"
    echo "0" > "$TYPING_CURSOR_FILE"
    echo "Assistant state reset to normal mode"
}

# Check if nerd-dictation is currently running.
if [ -f "$STATUS_FILE" ]; then
    echo "Nerd Dictation is running. Stopping and resetting to NORMAL mode."
    
    # Kill nerd-dictation process
    pkill -f "nerd-dictation"
    
    # Remove status file
    rm -f "$STATUS_FILE"
    
    # Reset assistant state
    reset_assistant_state
    
    echo "Nerd Dictation stopped."
else
    echo "Nerd Dictation not running. Starting in NORMAL MODE."
    
    # Ensure ydotool is running
    if ! pgrep -x "ydotoold" > /dev/null; then
        echo "Starting ydotool daemon..."
        ydotoold &
        sleep 1
    fi
    
    # Reset assistant state before starting
    reset_assistant_state
    
    # Start the process with the single config file.
    echo "Starting nerd-dictation with config: $CONFIG_FILE"
    nerd-dictation begin --config "$CONFIG_FILE" --simulate-input-tool=YDOTOOL &
    
    # Wait a moment for startup
    sleep 1
    
    # Create the status file to mark the process as running.
    touch "$STATUS_FILE"
    
    echo "Nerd Dictation started successfully."
    echo "Say 'hey' to activate command mode."
fi
