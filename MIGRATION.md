# Migration Guide: From nerd-dictation to Whisper.cpp D-Bus Service

## Overview

This guide helps you migrate from the file-based nerd-dictation system to the new D-Bus architecture with whisper.cpp.

## What's Changed

### Architecture

**Old System:**
- Python script monitoring nerd-dictation files in `/tmp`
- File-based IPC between components
- External nerd-dictation process required
- Vosk speech models

**New System:**
- C++ D-Bus service with whisper.cpp integration
- D-Bus-based IPC (standard Linux communication)
- Self-contained service with built-in speech recognition
- Whisper.cpp models (more accurate, faster)

### Benefits

✅ **Stability**: D-Bus is more reliable than file monitoring  
✅ **Performance**: Whisper.cpp is faster and more accurate  
✅ **Integration**: Native Linux D-Bus communication  
✅ **Maintainability**: Cleaner architecture, easier to debug  
✅ **GNOME 49**: Fully compatible with latest GNOME

## Migration Steps

### 1. Backup Your Configuration

```bash
# Backup existing config
cp ~/.config/nerd-dictation/config.json ~/.config/nerd-dictation/config.json.backup

# Your config file will work with the new system!
```

### 2. Stop Old System (If Running)

```bash
# Stop nerd-dictation if running
pkill -f nerd-dictation
pkill -f voice_assistant

# Disable old GNOME extension (if you had one)
gnome-extensions disable voice-assistant@saim
```

### 3. Install New System

```bash
# Build and install
./build.sh
./install.sh

# Enable new extension
gnome-extensions enable voice-assistant@saim

# Start service
systemctl --user start voice-assistant.service
```

### 4. Verify Configuration

Your existing `config.json` should work as-is. The structure is the same:

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

### 5. Test the System

1. Click the panel icon - it should show "Service: Running"
2. Say "hey" - icon should turn red
3. Say a command - it should execute

## Key Differences

### Commands

**Old:** Commands were in `voice_assistant_complete.py`  
**New:** Commands are in `~/.config/nerd-dictation/config.json` and editable via extension preferences

### Logs

**Old:** `/tmp/voice_assistant.log`  
**New:** Systemd journal - view with:
```bash
journalctl --user -u voice-assistant.service -f
```

### Control

**Old:** Shell scripts (`toggle-nerd.sh`, `stop-nerd.sh`)  
**New:** Systemd and D-Bus:
```bash
# Start/stop
systemctl --user start voice-assistant.service
systemctl --user stop voice-assistant.service

# Or use the extension panel menu
```

### Mode Changes

**Old:** Files in `/tmp/nerd-dictation.mode`  
**New:** D-Bus signals and methods:
```bash
# Via D-Bus
gdbus call --session \
  --dest com.github.saim.VoiceAssistant \
  --object-path /com/github/saim/VoiceAssistant \
  --method com.github.saim.VoiceAssistant.SetMode "command"

# Or use the extension panel menu
```

## What to Keep

✅ Your `config.json` - fully compatible  
✅ Your command definitions - same format  
✅ Your hotword and threshold settings  

## What to Remove

❌ Old shell scripts (`toggle-nerd.sh`, `stop-nerd.sh`, etc.) - **ALREADY REMOVED**  
❌ `voice_assistant_complete.py` - replaced by C++ service  
❌ Old Vosk models - using whisper.cpp tiny model now (75MB vs 300MB+)  
❌ `voice_buffer_writer.py` - not needed  
❌ `command_executor.sh`, `mode_changer.sh` - replaced by D-Bus  

## Troubleshooting Migration

### "Service not connected" after migration

The old system may still be running:
```bash
# Kill old processes
pkill -f nerd-dictation
pkill -f voice_assistant

# Start new service
systemctl --user start voice-assistant.service
```

### Commands not working

Check your config file syntax:
```bash
# Validate JSON
python3 -m json.tool ~/.config/nerd-dictation/config.json
```

### Extension won't load

```bash
# Reinstall extension
./install.sh

# Check for errors
journalctl -f -o cat /usr/bin/gnome-shell
```

## Rollback (If Needed)

If you need to go back to the old system:

```bash
# Uninstall new system
./uninstall.sh

# Restore old config
cp ~/.config/nerd-dictation/config.json.backup ~/.config/nerd-dictation/config.json

# Use old scripts
./toggle-nerd.sh
```

## Getting Help

If you encounter issues during migration:

1. Check the logs:
   ```bash
   journalctl --user -u voice-assistant.service -f
   ```

2. Verify D-Bus connection:
   ```bash
   gdbus introspect --session \
     --dest com.github.saim.VoiceAssistant \
     --object-path /com/github/saim/VoiceAssistant
   ```

3. Test configuration:
   ```bash
   # Get current config from service
   gdbus call --session \
     --dest com.github.saim.VoiceAssistant \
     --object-path /com/github/saim/VoiceAssistant \
     --method com.github.saim.VoiceAssistant.GetConfig
   ```

4. Open an issue on GitHub with:
   - Your config.json
   - Service logs
   - Extension logs
   - Steps to reproduce

## Performance Notes

The new whisper.cpp service uses the **tiny.en model** (75MB) which is:

- **Faster**: ~0.5-1s recognition vs 1-2s with Vosk
- **Smaller**: 75MB vs 300MB+ for Vosk models
- **More accurate**: Especially for commands and short phrases
- **Lower memory**: ~100-250MB vs ~300MB

You can upgrade to larger models later for better accuracy if needed.

## What's Next

After migrating successfully:

- Try the new **Preferences UI** - click panel icon → Preferences
- Explore **D-Bus integration** for scripting
- Check out the **new notification system**
- Enable **auto-sync** in preferences for automatic config updates

Welcome to the new Voice Assistant! 🎉
