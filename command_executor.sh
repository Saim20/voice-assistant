#!/bin/bash
# Execute command with automatic nerd-dictation suspend/resume
# Usage: ./command_executor.sh "command_to_run"

COMMAND="$1"
BUFFER_FILE="/tmp/nerd-dictation.buffer"

if [ -z "$COMMAND" ]; then
    echo "No command provided"
    exit 1
fi

# Suspend nerd-dictation (blocking)
echo "Suspending nerd-dictation..."
nerd-dictation suspend 2>/dev/null
SUSPEND_EXIT_CODE=$?

# Execute the command (non-blocking - in background)
echo "Executing command: $COMMAND"
eval "$COMMAND" &
COMMAND_PID=$!

# Brief pause to ensure suspension is complete (blocking)
sleep 0.3


# Resume nerd-dictation (blocking)
echo "Resuming nerd-dictation..."
nerd-dictation resume 2>/dev/null
RESUME_EXIT_CODE=$?

# Wait 0.3s after resume before clearing buffer (blocking)
echo "Waiting 0.3s before clearing buffer..."
sleep 0.3

# Clear the buffer file after the delay (blocking)
echo "Clearing buffer file..."
echo "" > "$BUFFER_FILE" 2>/dev/null || true

echo "Command execution initiated with PID: $COMMAND_PID"

# Exit successfully since suspend/resume cycle completed
exit 0
