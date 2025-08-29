#!/bin/bash

# Start script for nerd-dictation voice assistant
# Starts nerd-dictation with proper initialization

# Define the path for the configuration file
CONFIG_FILE="$HOME/.config/nerd-dictation/voice_buffer_writer.py"

# Define the paths for the status and mode files
STATUS_FILE="/tmp/nerd-dictation.status"
MODE_FILE="/tmp/nerd-dictation.mode"
BUFFER_FILE="/tmp/nerd-dictation.buffer"

echo "Starting Voice Assistant..."

# Check if already running (using more specific process matching)
if test -f "$STATUS_FILE"; then
    echo "Voice Assistant is already running! (status file exists)"
    echo "Use stop-nerd.sh or toggle-nerd.sh to stop it first"
    exit 1
fi

# Use more specific pattern to avoid matching this script itself
if /usr/bin/pgrep -f "nerd-dictation begin" > /dev/null; then
    echo "Voice Assistant is already running! (process found)"
    echo "Use stop-nerd.sh or toggle-nerd.sh to stop it first"
    exit 1
fi

echo "Debug: Checks passed, proceeding with startup..."

# Function to check if ydotool daemon is running
ensure_ydotool_running() {
    if ! pgrep -x "ydotoold" > /dev/null; then
        echo "Starting ydotool daemon..."
        ydotoold &
        sleep 2
        if pgrep -x "ydotoold" > /dev/null; then
            echo "ydotool daemon started successfully"
        else
            echo "Warning: Failed to start ydotool daemon"
            return 1
        fi
    else
        echo "ydotool daemon already running"
    fi
    return 0
}

# Function to initialize assistant state
initialize_assistant_state() {
    echo "normal" > "$MODE_FILE"
    echo "" > "$BUFFER_FILE"
    echo "Assistant state initialized to normal mode"
}

# Check if configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found at $CONFIG_FILE"
    echo "Please ensure voice_buffer_writer.py exists in the config directory"
    exit 1
fi

# Check if nerd-dictation command exists
if ! command -v nerd-dictation &> /dev/null; then
    echo "Error: nerd-dictation command not found"
    echo "Please install nerd-dictation first"
    exit 1
fi

# Ensure ydotool is running
if ! ensure_ydotool_running; then
    echo "Warning: Continuing without ydotool daemon"
fi

# Initialize assistant state
initialize_assistant_state

# Start nerd-dictation
echo "Starting nerd-dictation with config: $CONFIG_FILE"
nerd-dictation begin --config "$CONFIG_FILE" --simulate-input-tool=YDOTOOL &

# Wait for startup and verify
sleep 2

if pgrep -f "nerd-dictation begin" > /dev/null; then
    # Create the status file to mark the process as running
    touch "$STATUS_FILE"
    echo "Voice Assistant started successfully!"
    echo "Current mode: NORMAL"
    echo "Say 'hey' to activate command mode"
else
    echo "Error: Failed to start nerd-dictation"
    echo "Check the logs for more details"
    exit 1
fi
