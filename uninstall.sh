#!/bin/bash
# Uninstall script for Voice Assistant

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PREFIX="$HOME/.local"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/voice-assistant@saim"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "=== Uninstalling Voice Assistant ==="
echo

# Stop and disable service
echo "Stopping service..."
systemctl --user stop voice-assistant.service 2>/dev/null || true
systemctl --user disable voice-assistant.service 2>/dev/null || true

# Remove systemd service
echo "Removing systemd service..."
rm -f "$SYSTEMD_USER_DIR/voice-assistant.service"
systemctl --user daemon-reload

# Disable GNOME extension
echo "Disabling GNOME extension..."
gnome-extensions disable voice-assistant@saim 2>/dev/null || true

# Remove extension
echo "Removing GNOME extension..."
rm -rf "$EXTENSION_DIR"

# Remove service binary
echo "Removing service binary..."
rm -f "$INSTALL_PREFIX/bin/voice-assistant-service"

# Remove D-Bus files
echo "Removing D-Bus files..."
rm -f "$HOME/.local/share/dbus-1/services/com.github.saim.VoiceAssistant.service"
rm -f "$HOME/.local/share/dbus-1/interfaces/com.github.saim.VoiceAssistant.xml"

echo
echo "=== Uninstallation Complete ==="
echo
echo "Configuration files preserved in:"
echo "  ~/.config/nerd-dictation/config.json"
echo
echo "To remove configuration:"
echo "  rm -rf ~/.config/nerd-dictation"
echo
echo "To remove build artifacts:"
echo "  rm -rf $PROJECT_DIR/service/build"
echo "  rm -rf $PROJECT_DIR/whisper.cpp"
echo
