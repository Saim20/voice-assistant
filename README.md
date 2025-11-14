# GNOME Assistant with Whisper.cpp and GNOME Integration

A modern, D-Bus-based voice assistant for GNOME Shell that uses whisper.cpp for offline speech recognition.

## Architecture

### Components

1. **C++ D-Bus Service** (`service/`) - Core voice processing engine
   - Uses whisper.cpp for fast, offline speech recognition
   - Exposes D-Bus interface for control and status
   - Handles command matching and execution
   - Manages configuration

2. **GNOME Shell Extension** (`gnome-extension/`) - UI and user interaction
   - Panel indicator with mode/status display
   - D-Bus client for service communication
   - Configuration interface via preferences
   - Visual notifications

3. **D-Bus Interface** (`dbus/`) - Communication protocol
   - Well-defined XML interface
   - Methods for control, configuration, and status
   - Signals for events (mode changes, commands, notifications)

### Modes

- **Normal Mode**: Listens for hotword ("hey") to activate
- **Command Mode**: Processes voice commands with confidence thresholds
- **Typing Mode**: Converts speech directly to text input

## Prerequisites

### Required Dependencies

```bash
# Fedora/RHEL
sudo dnf install cmake gcc-c++ sdbus-c++-devel jsoncpp-devel pulseaudio-libs-devel git ydotool

# Ubuntu/Debian
sudo apt install cmake g++ libsdbus-c++-dev libjsoncpp-dev libpulse-dev git ydotool

# Arch
sudo pacman -S cmake gcc sdbus-cpp jsoncpp libpulse git ydotool
```

### GNOME Shell

- GNOME 45, 46, 47, 48, or **49** (fully compatible)

### Wayland Input Simulation (ydotool)

For voice commands that simulate keyboard shortcuts (window management, text editing, etc.), **ydotool is required on Wayland**. X11 users can use xdotool instead, but Wayland requires ydotool for security reasons.

**Install ydotool:**
```bash
# Fedora/RHEL
sudo dnf install ydotool

# Ubuntu/Debian
sudo apt install ydotool

# Arch
sudo pacman -S ydotool
```

**Enable ydotool service:**
```bash
# Start ydotool daemon
sudo systemctl enable --now ydotool

# OR for user service (Fedora 40+)
systemctl --user enable --now ydotoold
```

**Verify ydotool is working:**
```bash
# Test typing
ydotool type "Hello World"

# Test key press (Ctrl+C)
ydotool key 29:1 46:1 46:0 29:0
```

If you get permission errors, add your user to the `input` group:
```bash
sudo usermod -aG input $USER
# Log out and back in for changes to take effect
```

## Installation

### 1. Clone and Build

```bash
cd ~/Documents/Dev
git clone https://github.com/Saim20/gnome-assistant.git
cd gnome-assistant

# Build the service (downloads whisper.cpp and models automatically)
./build.sh
```

The build script will:
- Check for required dependencies
- Clone whisper.cpp if not present
- Download the tiny.en model (~75MB) if needed
- Build the C++ service

### 2. Install

```bash
./install.sh
```

This installs:
- Service binary to `~/.local/bin/gnome-assistant-service`
- D-Bus service file
- Systemd user service
- GNOME extension to `~/.local/share/gnome-shell/extensions/`

### 3. Enable and Start

```bash
# Enable the GNOME extension
gnome-extensions enable gnome-assistant@saim

# Start the service
systemctl --user start gnome-assistant.service

# Check status
systemctl --user status gnome-assistant.service
```

## Configuration

### Via GNOME Extension Preferences

1. Click the extension icon in the panel
2. Select "Preferences"
3. Configure:
   - **Hotword**: Activation word (default: "hey")
   - **Command Threshold**: Minimum confidence for execution (50-100%)
   - **Processing Interval**: Wait time before processing speech
   - **Commands**: Add/edit voice commands

### Via Config File

Edit `~/.config/gnome-assistant/config.json`:

The default configuration file includes comprehensive documentation with:
- Complete ydotool key code reference
- Detailed command examples and breakdowns
- All common keyboard shortcuts
- Best practices for building custom commands

Basic structure:
```json
{
  "hotword": "hey",
  "command_threshold": 80,
  "processing_interval": 1.5,
  "commands": [
    {
      "name": "Terminal",
      "command": "kgx",
      "phrases": ["open terminal", "start terminal"]
    }
  ]
}
```

Changes sync automatically between extension and service via D-Bus.

## Wayland & ydotool: Keyboard Simulation Guide

### Understanding ydotool Key Codes

Voice commands use **ydotool** to simulate keyboard input on Wayland. Each key has a numeric code, and key events use the format `keycode:state` where:
- `state = 1` means **key press**
- `state = 0` means **key release**

**Example:** `ydotool key 29:1 46:1 46:0 29:0` simulates Ctrl+C:
1. `29:1` - Press Ctrl
2. `46:1` - Press C
3. `46:0` - Release C
4. `29:0` - Release Ctrl

### Common ydotool Key Codes Reference

#### Modifier Keys
```
Ctrl (Left):   29
Alt (Left):    56
Shift (Left):  42
Super/Win:     125
Ctrl (Right):  97
Alt (Right):   100
Shift (Right): 54
```

#### Letters (A-Z)
```
A: 30    N: 49
B: 48    O: 24
C: 46    P: 25
D: 32    Q: 16
E: 18    R: 19
F: 33    S: 31
G: 34    T: 20
H: 35    U: 22
I: 23    V: 47
J: 36    W: 17
K: 37    X: 45
L: 38    Y: 21
M: 50    Z: 44
```

#### Numbers & Function Keys
```
0-9: 11-19, 10 (for 0)
F1-F12: 59-68, 87-88
Esc: 1
Tab: 15
Space: 57
Enter: 28
Backspace: 14
```

#### Navigation
```
Up Arrow:    103
Down Arrow:  108
Left Arrow:  105
Right Arrow: 106
Home:        102
End:         107
Page Up:     104
Page Down:   109
```

### Default Command Examples

Here are pre-configured voice commands using ydotool:

#### Window Management
```json
{
  "name": "Show Overview",
  "command": "ydotool key 125:1 125:0",
  "phrases": ["show overview", "show windows"]
}
```
- **Action**: Press Super key to show GNOME overview

```json
{
  "name": "Move Left",
  "command": "ydotool key 125:1 30:1 30:0 125:0",
  "phrases": ["move left", "go left", "left desktop"]
}
```
- **Action**: Super+A to move to left workspace

```json
{
  "name": "Switch Window",
  "command": "ydotool key 56:1 15:1 15:0 56:0",
  "phrases": ["switch window", "next window"]
}
```
- **Action**: Alt+Tab to switch windows

#### Text Editing
```json
{
  "name": "Copy",
  "command": "ydotool key 29:1 46:1 46:0 29:0",
  "phrases": ["copy", "copy text"]
}
```
- **Action**: Ctrl+C

```json
{
  "name": "Paste",
  "command": "ydotool key 29:1 47:1 47:0 29:0",
  "phrases": ["paste", "paste text"]
}
```
- **Action**: Ctrl+V

```json
{
  "name": "Select All",
  "command": "ydotool key 29:1 30:1 30:0 29:0",
  "phrases": ["select all"]
}
```
- **Action**: Ctrl+A

### Creating Custom Keyboard Commands

Use the GNOME Extension preferences **Key Command Builder** for a visual interface, or manually add to config.json:

1. **Find the key codes** you need from the reference above
2. **Build the command** in press/release order
3. **Test** with `ydotool key <your_command>`

**Example - Creating Ctrl+Shift+T (reopen closed tab):**
```json
{
  "name": "Reopen Tab",
  "command": "ydotool key 29:1 42:1 20:1 20:0 42:0 29:0",
  "phrases": ["reopen tab", "restore tab"]
}
```
Breakdown:
- `29:1` - Press Ctrl
- `42:1` - Press Shift
- `20:1` - Press T
- `20:0` - Release T
- `42:0` - Release Shift
- `29:0` - Release Ctrl

### Troubleshooting ydotool

**Issue: "Cannot connect to ydotool"**
```bash
# Check if ydotoold daemon is running
ps aux | grep ydotoold

# If not running, start it:
sudo systemctl start ydotool
# OR for user service:
systemctl --user start ydotoold
```

**Issue: "Permission denied"**
```bash
# Add user to input group
sudo usermod -aG input $USER
# Log out and back in
```

**Issue: "Key presses not working"**
```bash
# Test ydotool directly
ydotool type "test"

# Check ydotool socket
ls -la /run/ydotool/

# Verify permissions
sudo chmod 0666 /run/ydotool/socket
```

**Issue: "Commands work in X11 but not Wayland"**
- This is expected - xdotool doesn't work on Wayland
- Wayland requires ydotool for security
- Ensure ydotool daemon is running: `systemctl --user status ydotoold`

## Usage

### Basic Workflow

1. **Activate**: Say hotword ("hey")
2. **Command**: Speak a registered command phrase
3. **Execute**: Command runs automatically if confidence ≥ threshold
4. **Return**: Automatically returns to normal mode

### Panel Indicator

- **Microphone icon**: Normal mode
- **Red pulsing microphone**: Command mode (listening)
- **Keyboard icon**: Typing mode
- **Grayed out microphone**: Service stopped

### Menu Options

- **Mode switching**: Manually switch between Normal/Command/Typing
- **Service control**: Start/Stop/Restart the service
- **Buffer display**: View current recognized text

## D-Bus Interface

The service exposes `com.github.saim.GnomeAssistant` on the session bus.

### Example: Control via D-Bus

```bash
# Get current mode
gdbus call --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant \
  --method com.github.saim.GnomeAssistant.GetMode

# Set mode
gdbus call --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant \
  --method com.github.saim.GnomeAssistant.SetMode "command"

# Get status
gdbus call --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant \
  --method com.github.saim.GnomeAssistant.GetStatus
```

### Monitoring Signals

```bash
dbus-monitor --session \
  "interface='com.github.saim.GnomeAssistant'"
```

## Development

### Project Structure

```
gnome-assistant/
├── service/              # C++ D-Bus service
│   ├── src/
│   │   ├── main.cpp
│   │   ├── VoiceAssistantService.cpp
│   │   └── VoiceAssistantService.hpp
│   └── CMakeLists.txt
├── gnome-extension/      # GNOME Shell extension
│   └── gnome-assistant@saim/
│       ├── extension.js  # Main extension (D-Bus client)
│       ├── prefs.js      # Preferences UI
│       ├── metadata.json
│       └── lib/          # Modular components
├── dbus/                 # D-Bus interface definition
│   └── com.github.saim.GnomeAssistant.xml
├── systemd/              # Systemd service file
│   └── gnome-assistant.service
├── build.sh              # Build script
├── install.sh            # Installation script
└── config.json           # Default configuration
```

### Rebuilding

```bash
# Clean build
rm -rf service/build
./build.sh

# Reinstall
./install.sh

# Restart service
systemctl --user restart gnome-assistant.service

# Restart extension
gnome-extensions disable gnome-assistant@saim
gnome-extensions enable gnome-assistant@saim
```

### Debugging

```bash
# Service logs
journalctl --user -u gnome-assistant.service -f

# Extension logs
journalctl -f -o cat /usr/bin/gnome-shell

# D-Bus introspection
gdbus introspect --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant
```

## Troubleshooting

### Service won't start

```bash
# Check dependencies
pkg-config --exists sdbus-c++ jsoncpp && echo "OK" || echo "Missing deps"

# Check model exists
ls -lh ~/.local/share/gnome-assistant/models/ggml-tiny.en.bin

# Manual start for debugging
~/.local/bin/gnome-assistant-service
```

### Extension not connecting

```bash
# Verify service is running
systemctl --user status gnome-assistant.service

# Check D-Bus registration
gdbus call --session \
  --dest org.freedesktop.DBus \
  --object-path /org/freedesktop/DBus \
  --method org.freedesktop.DBus.ListNames | grep GnomeAssistant
```

### No audio capture

- Ensure PulseAudio/PipeWire is running
- Check microphone permissions
- Install `pulseaudio-libs-devel` and rebuild

## Performance

- **Whisper model**: tiny.en (~75MB, fastest, good accuracy for commands)
- **Memory**: ~100MB typical, ~250MB with model loaded
- **CPU**: Runs well on modern CPUs; tiny model is very efficient
- **Latency**: 0.5-1s typical recognition time

## Roadmap

- [ ] PipeWire native audio capture
- [ ] Support for larger whisper models (base, small, medium)
- [ ] GPU acceleration via CUDA/ROCm
- [ ] Continuous listening mode
- [ ] Wake word detection (separate from hotword)
- [ ] Multi-language support
- [ ] Command macro recording
- [ ] Integration with more desktop environments

## License

MIT License - See LICENSE file

## Credits

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - High-performance whisper.cpp implementation for efficient speech recognition
- [sdbus-c++](https://github.com/Kistler-Group/sdbus-cpp) - Modern C++ D-Bus library for seamless inter-process communication
- [ydotool](https://github.com/ReimuNotMoe/ydotool) - Generic command-line automation tool for Wayland
