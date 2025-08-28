# Voice Assistant for Nerd Dictation - AI Agent Instructions

## Project Overview

This is a sophisticated voice-controlled system built on top of `nerd-dictation` with three core components:
1. **Python Voice Assistant** (`voice_assistant_complete.py`) - Main speech processing engine
2. **GNOME Shell Extension** (`gnome-extension/`) - Visual feedback and control integration  
3. **Vosk Speech Models** (`model/`, `bak/`) - Local offline speech recognition

## Architecture & Data Flow

### Mode-Based State Machine
The system operates in three distinct modes managed through `/tmp` files:
- **Normal Mode**: Listens for hotword "hey" to activate
- **Command Mode**: Processes voice commands with automatic execution after interval
- **Typing Mode**: Converts speech directly to text input

Critical state files (all in `/tmp/`):
- `nerd-dictation.mode` - Current mode (normal/command/typing)
- `nerd-dictation.cursor` - Main processing cursor position  
- `nerd-dictation.typing-cursor` - Typing mode cursor position
- `nerd-dictation.buffer` - Current recognized text buffer

### Configuration System
Uses single modern JSON format (`config.json`):
- Nested categories with phrase arrays
- Configurable thresholds and intervals
- GNOME extension preferences sync to config file

Commands map voice phrases to shell commands via `ydotool` for system control.

## Development Workflows

### Starting/Stopping the System
```bash
# Toggle nerd-dictation service
./toggle-nerd.sh  # Starts/stops with proper state management
./stop-nerd.sh    # Clean shutdown with file cleanup

# GNOME extension management
cd gnome-extension && ./install.sh && gnome-extensions enable voice-assistant@saim

# Command execution wrapper (automatic suspend/resume)
./command_executor.sh "your_command"  # Handles nerd-dictation lifecycle
```

### Command Processing & Execution
Automatic processing is enabled with configurable intervals and automatic nerd-dictation suspension:
```python
# Commands are processed automatically after processing_interval (default 1.5s)
# Threshold: 80% confidence required for execution (configurable via extension)
assistant.process("open terminal")  # Automatically executes after interval

# Commands now execute through command_executor.sh for better control:
# - Automatic nerd-dictation suspend/resume during command execution
# - Buffer clearing after execution to prevent interference
```

### Configuration via GNOME Extension
- Access via panel icon → Preferences
- Real-time updates to `~/.config/nerd-dictation/config.json`
- Settings: command threshold, processing interval, hotword, notifications

### Debugging Tools
- Primary log: `/tmp/voice_assistant.log`
- Real-time status: `assistant.get_status()` method
- Mode file monitoring: GNOME extension provides visual feedback

## Key Patterns & Conventions

### Automatic Command Execution
Commands execute automatically after configurable interval:
```python
if best_match and ratio >= self.command_threshold:  # Default 80%
    self.execute_command(action)
```

### File-Based IPC
All components communicate via monitored files in `/tmp/` rather than sockets/pipes:
- Enables easy integration with shell scripts and GNOME extension
- Files are created/monitored atomically for race condition safety

### Cursor Management
Essential for nerd-dictation integration since it returns full text:
- `cursor` tracks processed position in main buffer
- `typing-cursor` tracks typing mode position  
- Handles text length decreases (resets) properly

### Buffer Management  
Text accumulates in `recognized_text_buffer` with cursor tracking to handle:
- nerd-dictation resets (text length decreases)
- Mode transitions (preserve/clear appropriately)
- Typing mode word boundaries

## Integration Points

### GNOME Shell Extension
- Monitors mode files with `Gio.File.monitor_file()`
- Updates panel icon: microphone (normal), red pulsing (command), keyboard (typing)  
- Provides manual mode switching via panel menu
- Settings UI syncs to voice assistant config file
- Preferences: command threshold, processing interval, hotword

### ydotool Integration
Essential for Linux input simulation:
- Daemon must be running: `ydotoold &`
- Key codes for shortcuts: `29:1` = Ctrl press, `46:1` = C press, etc.
- Commands like `ydotool key 29:1 46:1 46:0 29:0` = Ctrl+C

### Vosk Models
Local speech recognition models in `model/` directory:
- `am/final.mdl` - Acoustic model
- `graph/` - Language model graphs  
- `ivector/` - Speaker adaptation
- Models are language-specific (en-us, en-gb, etc.)

## Common Gotchas

1. **Automatic processing enabled** - commands execute after configurable interval
2. **Case-sensitive mode files** - write exactly "normal", "command", or "typing"
3. **ydotool daemon dependency** - system commands fail if daemon not running
4. **Configurable thresholds** - 80% default for execution, adjustable via extension
5. **Buffer cursor tracking** - handle text length decreases (resets) properly
6. **Single config format** - only uses new JSON format with arrays

## File Locations

**Core:** `voice_assistant_complete.py`, `config.json`  
**Scripts:** `toggle-nerd.sh`, `stop-nerd.sh`, `command_executor.sh`  
**Extension:** `gnome-extension/voice-assistant@saim/`  
**Models:** `model/` (active), `bak/` (backups)  
**State:** `/tmp/nerd-dictation.*` files  
**Logs:** `/tmp/voice_assistant.log`

## Configuration

All settings configurable via GNOME extension preferences:
- **Command Threshold**: Minimum confidence % for execution (50-100%, default 80%)
- **Processing Interval**: Time to wait before processing speech (0.5-5.0s, default 1.5s)  
- **Hotword**: Activation word (default "hey")
- **Notifications**: Enable/disable mode change notifications

Changes in extension preferences automatically update the voice assistant config file.

When adding commands, use the new array format and ensure proper cursor/buffer state management for mode transitions.
