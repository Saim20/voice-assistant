#!/bin/bash

# Enhanced toggle script for nerd-dictation voice assistant
# Starts or stops nerd-dictation with proper state management

# Define the path for the configuration file
CONFIG_FILE="$HOME/.config/nerd-dictation/voice_buffer_writer.py"

# Define the paths for the status and mode files
STATUS_FILE="/tmp/nerd-dictation.status"
MODE_FILE="/tmp/nerd-dictation.mode"
BUFFER_FILE="/tmp/nerd-dictation.buffer"

# Function to initialize assistant state
initialize_assistant_state() {
    echo "normal" > "$MODE_FILE"
    echo "" > "$BUFFER_FILE"
    echo "Assistant state initialized to normal mode"
}

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

# Function to check if voice_buffer_writer.py exists
check_config_file() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Configuration file not found at $CONFIG_FILE"
        echo "Please ensure voice_buffer_writer.py exists in the config directory"
        return 1
    fi
    return 0
}

# Check if nerd-dictation is currently running
if [ -f "$STATUS_FILE" ] || pgrep -f "nerd-dictation" > /dev/null; then
    echo "Voice Assistant is running. Stopping..."
    
    # Use the stop script for clean shutdown
    SCRIPT_DIR="$(dirname "$0")"
    if [ -f "$SCRIPT_DIR/stop-nerd.sh" ]; then
        "$SCRIPT_DIR/stop-nerd.sh"
    else
        # Fallback stop logic
        nerd-dictation end 2>/dev/null || true
        pkill -f "nerd-dictation" 2>/dev/null || true
        rm -f "$STATUS_FILE" "$MODE_FILE" "$BUFFER_FILE"
        echo "Voice Assistant stopped"
    fi
    
else
    echo "Voice Assistant not running. Starting..."
    
    # Check prerequisites
    if ! check_config_file; then
        exit 1
    fi
    
    if ! ensure_ydotool_running; then
        echo "Warning: Continuing without ydotool daemon"
    fi
    
    # Initialize assistant state
    initialize_assistant_state
    
    # Start nerd-dictation
    echo "Starting nerd-dictation with config: $CONFIG_FILE"
    
    # Check if nerd-dictation command exists
    if ! command -v nerd-dictation &> /dev/null; then
        echo "Error: nerd-dictation command not found"
        echo "Please install nerd-dictation first"
        exit 1
    fi
    
    # Start the process
    nerd-dictation begin --config "$CONFIG_FILE" --simulate-input-tool=YDOTOOL &
    
    # Wait for startup and check if it started successfully
    sleep 2
    
    if pgrep -f "nerd-dictation" > /dev/null; then
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
fi
