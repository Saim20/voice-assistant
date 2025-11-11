# Voice Assistant with Whisper.cpp and GNOME Integration

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
sudo dnf install cmake gcc-c++ sdbus-c++-devel jsoncpp-devel pulseaudio-libs-devel git

# Ubuntu/Debian
sudo apt install cmake g++ libsdbus-c++-dev libjsoncpp-dev libpulse-dev git

# Arch
sudo pacman -S cmake gcc sdbus-cpp jsoncpp libpulse git
```

### GNOME Shell

- GNOME 45, 46, 47, 48, or **49** (fully compatible)

## Installation

### 1. Clone and Build

```bash
cd ~/Documents/Dev
git clone https://github.com/your-repo/voice-assistant.git
cd voice-assistant

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
- Service binary to `~/.local/bin/voice-assistant-service`
- D-Bus service file
- Systemd user service
- GNOME extension to `~/.local/share/gnome-shell/extensions/`

### 3. Enable and Start

```bash
# Enable the GNOME extension
gnome-extensions enable voice-assistant@saim

# Start the service
systemctl --user start voice-assistant.service

# Check status
systemctl --user status voice-assistant.service
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

Edit `~/.config/nerd-dictation/config.json`:

```json
{
  "hotword": "hey",
  "command_threshold": 80,
  "processing_interval": 1.5,
  "commands": [
    {
      "name": "Terminal",
      "command": "kgx",
      "phrases": [
        "open terminal",
        "start terminal"
      ]
    }
  ]
}
```

Changes sync automatically between extension and service via D-Bus.

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

The service exposes `com.github.saim.VoiceAssistant` on the session bus.

### Example: Control via D-Bus

```bash
# Get current mode
gdbus call --session \
  --dest com.github.saim.VoiceAssistant \
  --object-path /com/github/saim/VoiceAssistant \
  --method com.github.saim.VoiceAssistant.GetMode

# Set mode
gdbus call --session \
  --dest com.github.saim.VoiceAssistant \
  --object-path /com/github/saim/VoiceAssistant \
  --method com.github.saim.VoiceAssistant.SetMode "command"

# Get status
gdbus call --session \
  --dest com.github.saim.VoiceAssistant \
  --object-path /com/github/saim/VoiceAssistant \
  --method com.github.saim.VoiceAssistant.GetStatus
```

### Monitoring Signals

```bash
dbus-monitor --session \
  "interface='com.github.saim.VoiceAssistant'"
```

## Development

### Project Structure

```
voice-assistant/
├── service/              # C++ D-Bus service
│   ├── src/
│   │   ├── main.cpp
│   │   ├── VoiceAssistantService.cpp
│   │   └── VoiceAssistantService.hpp
│   └── CMakeLists.txt
├── gnome-extension/      # GNOME Shell extension
│   └── voice-assistant@saim/
│       ├── extension.js  # Main extension (D-Bus client)
│       ├── prefs.js      # Preferences UI
│       ├── metadata.json
│       └── lib/          # Modular components
├── dbus/                 # D-Bus interface definition
│   └── com.github.saim.VoiceAssistant.xml
├── systemd/              # Systemd service file
│   └── voice-assistant.service
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
systemctl --user restart voice-assistant.service

# Restart extension
gnome-extensions disable voice-assistant@saim
gnome-extensions enable voice-assistant@saim
```

### Debugging

```bash
# Service logs
journalctl --user -u voice-assistant.service -f

# Extension logs
journalctl -f -o cat /usr/bin/gnome-shell

# D-Bus introspection
gdbus introspect --session \
  --dest com.github.saim.VoiceAssistant \
  --object-path /com/github/saim/VoiceAssistant
```

## Troubleshooting

### Service won't start

```bash
# Check dependencies
pkg-config --exists sdbus-c++ jsoncpp && echo "OK" || echo "Missing deps"

# Check model exists
ls -lh ~/.local/share/voice-assistant/models/ggml-tiny.en.bin

# Manual start for debugging
~/.local/bin/voice-assistant-service
```

### Extension not connecting

```bash
# Verify service is running
systemctl --user status voice-assistant.service

# Check D-Bus registration
gdbus call --session \
  --dest org.freedesktop.DBus \
  --object-path /org/freedesktop/DBus \
  --method org.freedesktop.DBus.ListNames | grep VoiceAssistant
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

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Efficient whisper inference
- [sdbus-c++](https://github.com/Kistler-Group/sdbus-cpp) - Modern C++ D-Bus library
- Original nerd-dictation integration concept
