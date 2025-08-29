#!/bin/bash

# Enhanced stop script for nerd-dictation voice assistant
# Cleanly stops nerd-dictation and clears all temporary files

# Define the paths for the status and mode files
STATUS_FILE="/tmp/nerd-dictation.status"
MODE_FILE="/tmp/nerd-dictation.mode"
BUFFER_FILE="/tmp/nerd-dictation.buffer"

echo "Stopping Voice Assistant..."

# Check if nerd-dictation is currently running
if [ -f "$STATUS_FILE" ]; then
    echo "Nerd Dictation is running. Ending process and clearing files."
    
    # Gracefully end nerd-dictation
    nerd-dictation end 2>/dev/null || true
    
    # Kill any remaining nerd-dictation processes (use specific pattern)
    pkill -f "nerd-dictation begin" 2>/dev/null || true
    
    # Wait a moment for cleanup
    sleep 0.5
    
else
    echo "Nerd Dictation status file not found. Checking for running processes..."
    
    # Kill any running nerd-dictation processes even without status file (use specific pattern)
    if pgrep -f "nerd-dictation begin" > /dev/null; then
        echo "Found running nerd-dictation processes. Terminating..."
        pkill -f "nerd-dictation begin"
        sleep 0.5
    fi
fi

# Clean up all temporary files
echo "Cleaning up temporary files..."
rm -f "$STATUS_FILE"
rm -f "$MODE_FILE" 
rm -f "$BUFFER_FILE"

# Also clean up any other potential nerd-dictation temp files
rm -f /tmp/nerd-dictation.* 2>/dev/null || true

echo "Voice Assistant stopped and cleaned up successfully."
