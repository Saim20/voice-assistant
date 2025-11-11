#!/bin/bash
# Install script for Voice Assistant (Service + Extension)

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_DIR/service/build"
INSTALL_PREFIX="$HOME/.local"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/voice-assistant@saim"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Installing Voice Assistant ===" 
echo

# Check if built
if [ ! -f "$BUILD_DIR/voice-assistant-service" ]; then
    echo "Service not built yet. Building first..."
    "$PROJECT_DIR/build.sh"
    echo
fi

# Install the service binary
echo "Installing service..."
cd "$BUILD_DIR"
cmake --install .

echo

# Install systemd service
echo "Installing systemd service..."
mkdir -p "$SYSTEMD_USER_DIR"
cp "$PROJECT_DIR/systemd/voice-assistant.service" "$SYSTEMD_USER_DIR/"

# Enable systemd service
echo "Enabling systemd service..."
systemctl --user daemon-reload
systemctl --user enable voice-assistant.service

echo

# Install GNOME extension
echo "Installing GNOME extension..."
mkdir -p "$EXTENSION_DIR"
cp -r "$PROJECT_DIR/gnome-extension/voice-assistant@saim/"* "$EXTENSION_DIR/"

# Compile schemas
echo "Compiling extension schemas..."
glib-compile-schemas "$EXTENSION_DIR/schemas/"

echo

# Create config directory
echo "Creating config directory..."
mkdir -p "$HOME/.config/nerd-dictation"

# Copy config if it doesn't exist
if [ ! -f "$HOME/.config/nerd-dictation/config.json" ]; then
    echo "Creating default config..."
    cp "$PROJECT_DIR/config.json" "$HOME/.config/nerd-dictation/config.json"
fi

echo
echo "=== Installation Complete ===" 
echo
echo "Next steps:"
echo "1. Enable the GNOME extension:"
echo "   gnome-extensions enable voice-assistant@saim"
echo
echo "2. Start the service:"
echo "   systemctl --user start voice-assistant.service"
echo
echo "3. Check service status:"
echo "   systemctl --user status voice-assistant.service"
echo
echo "4. View logs:"
echo "   journalctl --user -u voice-assistant.service -f"
echo
echo "5. Configure via extension preferences or edit:"
echo "   ~/.config/nerd-dictation/config.json"
echo
