#!/bin/bash

# Voice Assistant GNOME Extension Uninstall Script

set -e

EXTENSION_UUID="voice-assistant@saim"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"

echo "Uninstalling Voice Assistant GNOME Extension..."

# Disable extension if it's enabled
if command -v gnome-extensions > /dev/null; then
    echo "Disabling extension..."
    gnome-extensions disable "$EXTENSION_UUID" 2>/dev/null || true
fi

# Remove extension directory
if [ -d "$EXTENSION_DIR" ]; then
    echo "Removing extension files..."
    rm -rf "$EXTENSION_DIR"
    echo "Extension uninstalled successfully!"
else
    echo "Extension not found at: $EXTENSION_DIR"
fi

echo "Done. You may need to restart GNOME Shell (Alt+F2, type 'r') to complete removal."
