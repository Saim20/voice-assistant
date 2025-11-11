#!/bin/bash
# Clean up old files and directories from nerd-dictation version

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Cleaning up Voice Assistant project ==="
echo

# Remove old nerd-dictation scripts (already done, but just in case)
echo "Removing old nerd-dictation scripts..."
rm -f "$PROJECT_DIR/voice_buffer_writer.py"
rm -f "$PROJECT_DIR/command_executor.sh"
rm -f "$PROJECT_DIR/mode_changer.sh"
rm -f "$PROJECT_DIR/start-nerd.sh"
rm -f "$PROJECT_DIR/status-nerd.sh"
rm -f "$PROJECT_DIR/stop-nerd.sh"

# Remove old model directories (Vosk models)
echo "Removing old Vosk model directories..."
if [ -d "$PROJECT_DIR/model" ]; then
    echo "  Removing model/"
    rm -rf "$PROJECT_DIR/model"
fi

if [ -d "$PROJECT_DIR/bak" ]; then
    echo "  Removing bak/"
    rm -rf "$PROJECT_DIR/bak"
fi

# Remove build artifacts if present
if [ -d "$PROJECT_DIR/service/build" ]; then
    echo "Removing build artifacts..."
    rm -rf "$PROJECT_DIR/service/build"
fi

# Remove whisper.cpp clone (will be re-downloaded on build)
if [ -d "$PROJECT_DIR/whisper.cpp" ]; then
    echo "Removing whisper.cpp directory (will be re-downloaded)..."
    rm -rf "$PROJECT_DIR/whisper.cpp"
fi

# Remove backup files
echo "Removing backup files..."
find "$PROJECT_DIR" -name "*.old" -o -name "*.backup" -o -name "*.bak" | while read file; do
    echo "  Removing $file"
    rm -f "$file"
done

# Clean extension backup
if [ -f "$PROJECT_DIR/gnome-extension/voice-assistant@saim/extension.js.old" ]; then
    rm -f "$PROJECT_DIR/gnome-extension/voice-assistant@saim/extension.js.old"
fi

echo
echo "=== Cleanup Complete ==="
echo
echo "Project is now clean. Old files removed:"
echo "  ✓ Old nerd-dictation scripts"
echo "  ✓ Vosk model directories (model/, bak/)"
echo "  ✓ Build artifacts"
echo "  ✓ Backup files"
echo
echo "Next steps:"
echo "  1. Run ./build.sh to build with whisper.cpp tiny model"
echo "  2. Run ./install.sh to install"
echo
