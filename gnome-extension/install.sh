#!/bin/bash

# Voice Assistant GNOME Extension Installation Script

set -e

EXTENSION_UUID="voice-assistant@saim"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"
SOURCE_DIR="$(dirname "$0")/voice-assistant@saim"

echo "Installing Voice Assistant GNOME Extension..."

# Check if GNOME Shell is running
if ! pgrep -x gnome-shell > /dev/null; then
    echo "Warning: GNOME Shell is not running. Extension will be available after login."
fi

# Create extension directory
echo "Creating extension directory..."
mkdir -p "$EXTENSION_DIR"

# Copy extension files
echo "Copying extension files..."
cp -r "$SOURCE_DIR"/* "$EXTENSION_DIR/"

# Compile schemas if glib-compile-schemas is available
if command -v glib-compile-schemas > /dev/null; then
    echo "Compiling GSettings schemas..."
    glib-compile-schemas "$EXTENSION_DIR/schemas/"
else
    echo "Warning: glib-compile-schemas not found. Some features may not work."
fi

# Set permissions
chmod +x "$EXTENSION_DIR"/*.js

echo "Extension installed successfully!"
echo ""
echo "To enable the extension:"
echo "1. Log out and log back in (or restart GNOME Shell with Alt+F2, type 'r')"
echo "2. Run: gnome-extensions enable $EXTENSION_UUID"
echo "   Or use GNOME Extensions app to enable it"
echo ""
echo "To uninstall:"
echo "   gnome-extensions disable $EXTENSION_UUID"
echo "   rm -rf '$EXTENSION_DIR'"
echo ""
echo "Extension files are located at: $EXTENSION_DIR"
