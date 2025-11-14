#!/bin/bash
# Install script for GNOME Assistant (Service + Extension)

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_DIR/service/build"
INSTALL_PREFIX="$HOME/.local"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/gnome-assistant@saim"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Installing GNOME Assistant ===" 
echo

# Check if built
if [ ! -f "$BUILD_DIR/gnome-assistant-service" ]; then
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
cp "$PROJECT_DIR/systemd/gnome-assistant.service" "$SYSTEMD_USER_DIR/"

# Enable systemd service
echo "Enabling systemd service..."
systemctl --user daemon-reload
systemctl --user enable gnome-assistant.service

echo

# Install GNOME extension
echo "Installing GNOME extension..."
mkdir -p "$EXTENSION_DIR"
cp -r "$PROJECT_DIR/gnome-extension/gnome-assistant@saim/"* "$EXTENSION_DIR/"

# Compile schemas
echo "Compiling extension schemas..."
glib-compile-schemas "$EXTENSION_DIR/schemas/"

echo

# Create config directory
echo "Creating config directory..."
mkdir -p "$HOME/.config/gnome-assistant"

# Copy config if it doesn't exist
if [ ! -f "$HOME/.config/gnome-assistant/config.json" ]; then
    echo "Creating default config (with comprehensive ydotool documentation)..."
    cp "$PROJECT_DIR/config.json" "$HOME/.config/gnome-assistant/config.json"
fi

echo
echo "=== Installation Complete ==="
echo
echo "Next steps:"
echo "1. Enable the GNOME extension:"
echo "   gnome-extensions enable gnome-assistant@saim"
echo
echo "2. Start the service:"
echo "   systemctl --user start gnome-assistant.service"
echo
echo "3. Check service status:"
echo "   systemctl --user status gnome-assistant.service"
echo
echo "4. View logs:"
echo "   journalctl --user -u gnome-assistant.service -f"
echo
echo "5. Configure via extension preferences or edit:"
echo "   ~/.config/gnome-assistant/config.json"
echo "   (Includes comprehensive ydotool key code reference)"
echo
