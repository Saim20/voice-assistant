# Willow - AI Agent Instructions

## Project Overview

This is a sophisticated voice-controlled system with a modern D-Bus architecture and three core components:
1. **C++ D-Bus Service** (`service/`) - Core voice processing engine using whisper.cpp for offline speech recognition
2. **GNOME Shell Extension** (`gnome-extension/`) - Visual feedback and D-Bus client integration  
3. **Whisper.cpp Models** (`~/.local/share/willow/models/`) - Fast, accurate offline speech recognition (tiny.en model)

## Architecture & Data Flow

### Mode-Based State Machine
The system operates in three distinct modes managed via D-Bus:
- **Normal Mode**: Listens for hotword "hey" to activate command mode
- **Command Mode**: Processes voice commands with automatic execution based on confidence threshold
- **Typing Mode**: Converts speech directly to text input (via ydotool key simulation)

### D-Bus Communication
All components communicate via D-Bus interface `com.github.saim.Willow`:
- Methods: SetMode, GetMode, GetStatus, Start, Stop, UpdateConfig, etc.
- Signals: ModeChanged, CommandExecuted, BufferChanged, StatusChanged
- Properties: IsRunning, CurrentMode, CurrentBuffer, Version

### Configuration System
Uses modern JSON format (`~/.config/willow/config.json`):
- Simple array-based command structure
- Configurable thresholds, intervals, and hotword
- GNOME extension preferences sync to config file via D-Bus

Commands map voice phrases to shell commands, with ydotool for keyboard/window control.

## Centralized Branding

**IMPORTANT**: All branding is centralized in `branding.json` at the project root. This file is the single source of truth for:
- Project name: "Willow"
- Description: "Simple offline configurable voice assistant for gnome"
- D-Bus interface: `com.github.saim.Willow`
- Extension UUID: `willow@saim`
- Service binary: `willow-service`
- Config paths: `~/.config/willow`, `~/.local/share/willow`
- Package name: `willow`
- All other project identifiers

**When making changes that involve naming/branding, always reference `branding.json` first.**

## Development Workflows

### Starting/Stopping the System
```bash
# Service control via systemd
systemctl --user start willow.service
systemctl --user stop willow.service
systemctl --user restart willow.service
systemctl --user status willow.service

# View logs
journalctl --user -u willow.service -f

# GNOME extension management
gnome-extensions enable willow@saim
gnome-extensions disable willow@saim
gnome-extensions prefs willow@saim
```

### D-Bus Control
```bash
# Set mode
gdbus call --session --dest com.github.saim.Willow \
  --object-path /com/github/saim/VoiceAssistant \
  --method com.github.saim.Willow.SetMode "command"

# Get status
gdbus call --session --dest com.github.saim.Willow \
  --object-path /com/github/saim/VoiceAssistant \
  --method com.github.saim.Willow.GetStatus

# Monitor signals
dbus-monitor --session "interface='com.github.saim.Willow'"
```

### Configuration via GNOME Extension
- Access via panel icon → Preferences
- Real-time updates to `~/.config/willow/config.json`
- Settings: command threshold, processing interval, hotword, notifications
- Visual key command builder for ydotool commands

### Debugging Tools
- Service logs: `journalctl --user -u willow.service -f`
- D-Bus introspection: `gdbus introspect --session --dest com.github.saim.Willow --object-path /com/github/saim/VoiceAssistant`
- Extension logs: `journalctl -f -o cat /usr/bin/gnome-shell`
- Status via panel menu or D-Bus GetStatus method

## Key Patterns & Conventions

### Command Execution
Commands execute when confidence threshold is met (default 80%):
```cpp
if (bestMatch && confidence >= m_commandThreshold) {
    executeCommand(command);
}
```

### D-Bus Signal Pattern
Service emits signals for state changes:
```cpp
void emitModeChanged(const std::string& newMode, const std::string& oldMode);
void emitCommandExecuted(const std::string& command, const std::string& phrase, double confidence);
void emitNotification(const std::string& title, const std::string& message, const std::string& urgency);
```

### Buffer Management  
Text buffer tracks recognized speech and is accessible via:
- D-Bus method: `GetBuffer()`
- D-Bus signal: `BufferChanged`
- Panel menu display in GNOME extension

## Integration Points

### GNOME Shell Extension
- D-Bus client connecting to `com.github.saim.Willow`
- Updates panel icon: microphone (normal), red pulsing (command), keyboard (typing)  
- Provides manual mode switching via panel menu
- Settings UI syncs to voice assistant config file via D-Bus
- Preferences: command threshold, processing interval, hotword

### ydotool Integration
Essential for Wayland input simulation:
- Daemon must be running: `systemctl --user start ydotool`
- Key codes for shortcuts: `29:1` = Ctrl press, `46:1` = C press, etc.
- Commands like `ydotool key 29:1 46:1 46:0 29:0` = Ctrl+C
- Format: `keycode:state` where state is 1 (press) or 0 (release)

### Whisper.cpp Models
Local speech recognition models in `~/.local/share/willow/models/`:
- `ggml-tiny.en.bin` - Default fast model (~75MB)
- Supports base, small, medium models for better accuracy
- CPU-based inference, efficient on modern processors

## Common Gotchas

1. **ydotool daemon required** - Commands with key simulation fail if daemon not running
2. **systemd-run for GUI apps** - Uses `systemd-run --user --scope` for proper app launching
3. **Configurable thresholds** - 80% default confidence for execution, adjustable via extension
4. **Wayland specific** - ydotool is required for Wayland; xdotool won't work
5. **D-Bus session bus** - Service must be on session bus, not system bus

## File Locations

**Service:** `~/.local/bin/willow-service` or `/usr/bin/willow-service`
**Config:** `~/.config/willow/config.json`  
**Extension:** `~/.local/share/gnome-shell/extensions/willow@saim/`  
**Models:** `~/.local/share/willow/models/`  
**D-Bus Interface:** `~/.local/share/dbus-1/interfaces/com.github.saim.Willow.xml`  
**Systemd Service:** `~/.config/systemd/user/willow.service` or `/usr/lib/systemd/user/willow.service`
**Branding Config:** `branding.json` (project root - single source of truth)

## Configuration

All settings configurable via GNOME extension preferences:
- **Command Threshold**: Minimum confidence % for execution (50-100%, default 80%)
- **Processing Interval**: Time to wait before processing speech (0.5-5.0s, default 1.5s)  
- **Hotword**: Activation word (default "hey")
- **Notifications**: Enable/disable mode change notifications

Changes in extension preferences automatically update the voice assistant config file via D-Bus.

When adding commands, ensure proper ydotool format for keyboard shortcuts (e.g., `ydotool key 29:1 46:1 46:0 29:0` for Ctrl+C).
