#!/bin/bash

# Voice Assistant Setup Script
echo "Setting up Voice Assistant..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/nerd-dictation"

echo "Script directory: $SCRIPT_DIR"
echo "Config directory: $CONFIG_DIR"

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Check if nerd-dictation is installed
if ! command -v nerd-dictation &> /dev/null; then
    echo "Warning: nerd-dictation not found. Please install it first."
    echo "You can install it from: https://github.com/ideasman42/nerd-dictation"
fi

# Check if ydotool is installed
if ! command -v ydotool &> /dev/null; then
    echo "Warning: ydotool not found. Installing..."
    
    # Try to install ydotool
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y ydotool
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y ydotool
    elif command -v pacman &> /dev/null; then
        sudo pacman -S ydotool
    else
        echo "Please install ydotool manually for your distribution"
    fi
fi

# Check if fuzzyfinder is installed
if ! python3 -c "import fuzzyfinder" &> /dev/null; then
    echo "Installing fuzzyfinder..."
    pip3 install --user fuzzyfinder
fi

# Make the improved script executable
chmod +x "$SCRIPT_DIR/voice_assistant_improved.py"
chmod +x "$SCRIPT_DIR/gui.py"

# Create a backup of original if it exists
if [ -f "$CONFIG_DIR/command-mode.py" ]; then
    echo "Creating backup of original command-mode.py..."
    cp "$CONFIG_DIR/command-mode.py" "$CONFIG_DIR/command-mode.py.backup"
fi

# Copy files to config directory
echo "Copying files to config directory..."
cp "$SCRIPT_DIR/voice_assistant_improved.py" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/config.json" "$CONFIG_DIR/"
cp "$SCRIPT_DIR/gui.py" "$CONFIG_DIR/"

# Create symlink for compatibility
ln -sf "$CONFIG_DIR/voice_assistant_improved.py" "$CONFIG_DIR/command-mode.py"

# Create desktop entry for GUI
DESKTOP_FILE="$HOME/.local/share/applications/voice-assistant.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Voice Assistant
Comment=Voice Assistant Control Panel
Exec=python3 $CONFIG_DIR/gui.py
Icon=audio-input-microphone
Terminal=false
Type=Application
Categories=Utility;Audio;
EOF

echo "Creating launcher script..."
cat > "$CONFIG_DIR/launch_gui.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 gui.py
EOF
chmod +x "$CONFIG_DIR/launch_gui.sh"

# Create systemd service for ydotool (if not exists)
YDOTOOL_SERVICE="$HOME/.config/systemd/user/ydotool.service"
mkdir -p "$(dirname "$YDOTOOL_SERVICE")"

if [ ! -f "$YDOTOOL_SERVICE" ]; then
    cat > "$YDOTOOL_SERVICE" << EOF
[Unit]
Description=ydotool daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/ydotoold
Restart=always
RestartSec=1

[Install]
WantedBy=default.target
EOF

    echo "Enabling ydotool service..."
    systemctl --user daemon-reload
    systemctl --user enable ydotool.service
    systemctl --user start ydotool.service
fi

echo ""
echo "Setup complete!"
echo ""
echo "Usage:"
echo "1. Start nerd-dictation with: nerd-dictation begin --vosk-model-dir=./model"
echo "2. Open the GUI with: python3 $CONFIG_DIR/gui.py"
echo "3. Or use the desktop launcher: Voice Assistant"
echo ""
echo "Voice commands:"
echo "- Say 'hey' to activate command mode"
echo "- Say 'typing mode' to start typing"
echo "- Say 'normal mode' to return to normal"
echo ""
echo "Files created:"
echo "- $CONFIG_DIR/voice_assistant_improved.py (main script)"
echo "- $CONFIG_DIR/config.json (configuration)"
echo "- $CONFIG_DIR/gui.py (GUI interface)"
echo "- $CONFIG_DIR/command-mode.py (symlink for compatibility)"
echo "- $DESKTOP_FILE (desktop launcher)"
echo ""

# Test the setup
echo "Testing setup..."
if python3 -c "
import sys
sys.path.insert(0, '$CONFIG_DIR')
from voice_assistant_improved import VoiceAssistant
assistant = VoiceAssistant()
print('✓ Voice assistant loads successfully')
print(f'✓ Current mode: {assistant.get_mode()}')
print(f'✓ Commands available: {len(assistant.commands)}')
"; then
    echo "✓ Setup test passed!"
else
    echo "✗ Setup test failed. Please check the installation."
fi
