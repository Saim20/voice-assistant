# Voice Assistant GNOME Extension

A GNOME Shell extension that provides visual feedback and control for the nerd-dictation voice assistant system.

## Features

- **Visual Mode Indicator**: Shows current voice assistant mode in the status bar
- **Real-time Feedback**: Icon changes color and style based on mode:
  - Normal: White microphone icon
  - Command: Red pulsing microphone (animated)
  - Typing: Blue keyboard icon
- **Mode Switching**: Click the icon to manually switch between modes
- **Buffer Display**: Shows current recognized text in command mode
- **Quick Controls**: Reset state, open configuration, view logs
- **Live Updates**: Monitors file changes for real-time synchronization

## Installation

1. **Install the extension:**
   ```bash
   cd /home/saim/.config/nerd-dictation/gnome-extension
   chmod +x install.sh
   ./install.sh
   ```

2. **Enable the extension:**
   ```bash
   gnome-extensions enable voice-assistant@saim
   ```
   
   Or use the GNOME Extensions app (install with `sudo apt install gnome-shell-extension-manager`)

3. **Restart GNOME Shell** (if needed):
   - Press `Alt + F2`, type `r`, press Enter
   - Or log out and log back in

## File Structure

```
voice-assistant@saim/
├── extension.js              # Main extension logic
├── prefs.js                 # Preferences dialog
├── metadata.json            # Extension metadata
├── stylesheet.css           # Visual styling
└── schemas/
    └── org.gnome.shell.extensions.voice-assistant.gschema.xml
```

## Integration with Voice Assistant

The extension monitors these files for real-time updates:

- `/tmp/nerd-dictation.mode` - Current voice assistant mode
- `/tmp/nerd-dictation.buffer` - Current recognized text buffer
- `/tmp/nerd-dictation.cursor` - Activity detection
- `/tmp/nerd-dictation.typing-cursor` - Typing mode cursor

## Usage

1. **Status Bar Icon**: The microphone icon in the top bar shows the current mode
2. **Click for Menu**: Click the icon to access:
   - Mode switching (Normal/Command/Typing)
   - Reset state
   - Open configuration files
   - View logs
3. **Visual Feedback**: 
   - Normal mode: Static white microphone
   - Command mode: Red pulsing microphone with notifications
   - Typing mode: Blue keyboard icon
4. **Notifications**: Shows mode changes and command recognition

## Configuration

Access extension preferences through:
- Right-click on the extension icon - Preferences
- GNOME Extensions app - Voice Assistant - Settings
- Or run: `gnome-extensions prefs voice-assistant@saim`

## Troubleshooting

### Extension not appearing
- Check if it's enabled: `gnome-extensions list --enabled | grep voice-assistant`
- Restart GNOME Shell: `Alt + F2`, type `r`, press Enter
- Check logs: `journalctl -f -o cat /usr/bin/gnome-shell`

### File monitoring not working
- Ensure `/tmp` directory is writable
- Check if voice assistant is creating the expected files
- View logs: `tail -f /tmp/voice_assistant.log`

### Permission issues
- Make sure extension files are executable
- Check ownership: `ls -la ~/.local/share/gnome-shell/extensions/voice-assistant@saim/`

## Uninstall

```bash
cd /home/saim/.config/nerd-dictation/gnome-extension
chmod +x uninstall.sh
./uninstall.sh
```

## Development

To modify the extension:

1. Edit files in `/home/saim/.config/nerd-dictation/gnome-extension/voice-assistant@saim/`
2. Reinstall: `./install.sh`
3. Restart GNOME Shell: `Alt + F2`, type `r`, press Enter
4. Check logs: `journalctl -f -o cat /usr/bin/gnome-shell`

## File Locations

- **Extension**: `~/.local/share/gnome-shell/extensions/voice-assistant@saim/`
- **Voice Assistant Config**: `~/.config/nerd-dictation/config.json`
- **Mode File**: `/tmp/nerd-dictation.mode`
- **Buffer File**: `/tmp/nerd-dictation.buffer`
- **Logs**: `/tmp/voice_assistant.log`

## Compatibility

- GNOME Shell 42, 43, 44, 45, 46+
- Tested on Ubuntu 22.04+ and Fedora 36+
