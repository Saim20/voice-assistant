#!/bin/bash
# Execute command with automatic nerd-dictation suspend/resume
# Usage: ./command_executor.sh "command_to_run"

COMMAND="$1"

if [ -z "$COMMAND" ]; then
    echo "No command provided"
    exit 1
fi

# Execute the command
eval "$COMMAND" &

# Suspend nerd-dictation
nerd-dictation suspend 2>/dev/null

# Brief pause to ensure suspension
sleep 0.3

# Resume nerd-dictation
nerd-dictation resume 2>/dev/null

# Exit successfully
exit 0
