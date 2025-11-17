# GNOME Assistant - Voice Control for GNOME Shell

A voice-controlled assistant for GNOME Shell that uses offline speech recognition to execute commands hands-free.

> **⚠️ DISCLAIMER**: This software is provided "as is" without warranty of any kind. Use at your own risk. The authors are not responsible for any damage, data loss, or issues that may arise from using this software. This is experimental software under active development.

## What It Does

Control your GNOME desktop with voice commands:
- Say "hey" to activate, then speak a command
- Open applications, switch windows, manage workspaces
- Simulate keyboard shortcuts for any task
- Type using your voice in any application
- Works completely offline - no internet required

## How It Works

- **Say the hotword** ("hey") to activate listening
- **Speak your command** (e.g., "open terminal", "switch window")
- **Command executes automatically** if recognized with high confidence
- All processing happens locally on your machine

## Requirements

- **GNOME Shell** 45, 46, 47, 48, or 49
- **Linux distribution** with standard development tools
- **Microphone** for voice input
- **ydotool** for keyboard simulation on Wayland (most modern systems)

## Installation

### Arch Linux (AUR)

```bash
git clone https://github.com/Saim20/gnome-assistant.git
cd gnome-assistant
makepkg -si
```

**After installation, complete these steps from your GNOME desktop:**

```bash
# 1. Enable the extension
gnome-extensions enable gnome-assistant@saim

# 2. Start the service
systemctl --user start gnome-assistant.service

# 3. Enable ydotool for keyboard commands
sudo systemctl enable --now ydotool
sudo usermod -aG input $USER
# Log out and back in for group changes
```

> **⚠️ Important:** If you installed via SSH, you must run steps 1-2 from a GNOME graphical session. The service requires D-Bus which is only available in an active GNOME session.

### Other Linux Distributions

**Step 1: Install Dependencies**

```bash
# Fedora/RHEL
sudo dnf install cmake gcc-c++ sdbus-c++-devel jsoncpp-devel pulseaudio-libs-devel git ydotool

# Ubuntu/Debian
sudo apt install cmake g++ libsdbus-c++-dev libjsoncpp-dev libpulse-dev git ydotool

# Arch (manual build)
sudo pacman -S cmake gcc sdbus-cpp jsoncpp libpulse git ydotool
```

**Step 2: Build and Install**

```bash
git clone https://github.com/Saim20/gnome-assistant.git
cd gnome-assistant
./build.sh
./install.sh
```

**Step 3: Complete Setup (from GNOME desktop, not SSH)**

```bash
# Enable the extension
gnome-extensions enable gnome-assistant@saim

# Start the service
systemctl --user start gnome-assistant.service

# Enable ydotool
sudo systemctl enable --now ydotool
sudo usermod -aG input $USER
# Log out and back in

# Verify it's running
systemctl --user status gnome-assistant.service
```

> **⚠️ Important:** Steps must be run from an active GNOME session, not SSH or TTY, as the service requires D-Bus session bus.

## Getting Started

1. **Click the microphone icon** in your GNOME panel
2. **Select "Preferences"** to open settings
3. **Review the default commands** - they work out of the box
4. **Test it out**: Say "hey" then "show overview"

### Adding Custom Commands

In Preferences, you can:
- Add new voice commands
- Change the activation word (default: "hey")
- Adjust sensitivity settings
- Build keyboard shortcuts visually with the Key Command Builder

Example command:
- **Name**: "Open Firefox"
- **Command**: `firefox`
- **Phrases**: "open firefox", "launch firefox"

All changes apply immediately - no restart needed!

## Default Voice Commands

The assistant comes with useful commands pre-configured:

**Window Management:**
- "show overview" - Show all windows
- "switch window" - Alt+Tab window switcher
- "move left/right" - Switch workspace
- "maximize/minimize" - Window controls

**Applications:**
- "open terminal" - Launch terminal
- "open firefox" - Launch browser

**Text Editing:**
- "copy" - Ctrl+C
- "paste" - Ctrl+V
- "select all" - Ctrl+A

**Custom Commands:**
You can add any command or keyboard shortcut in Preferences. The extension includes a visual Key Command Builder to help you create keyboard combinations.

## Usage

**Voice Command Mode:**
1. Say "hey" (the activation word)
2. Speak your command (e.g., "open terminal")
3. Command executes automatically

**Typing Mode:**
- Switch to typing mode from the panel menu
- Everything you say will be typed as text
- Great for dictation

**Panel Icons:**
- 🎤 **Normal** - Listening for activation word
- 🔴 **Command** - Listening for command (pulsing red)
- ⌨️ **Typing** - Speech-to-text mode
- 🎤 **Gray** - Service stopped



## Troubleshooting

**Installation error: "Failed to connect to user scope bus"**

This happens when installing from SSH or a non-graphical terminal. The service requires a GNOME session to be running.

**Solution:** Log into your GNOME desktop, then:
```bash
# Start the service from your graphical session
systemctl --user start gnome-assistant.service

# Verify it's running
systemctl --user status gnome-assistant.service
```

The extension should now work. You can also start the service automatically on next login:
```bash
systemctl --user enable gnome-assistant.service
```

**Service won't start:**
```bash
# Check if service is running
systemctl --user status gnome-assistant.service

# View logs
journalctl --user -u gnome-assistant.service -f

# Check if model is downloaded
ls -lh ~/.local/share/gnome-assistant/models/
```

**Commands not working:**
```bash
# Verify ydotool is running
systemctl --user status ydotoold

# Test ydotool manually
ydotool type "test"
```

**Microphone not working:**
- Check microphone permissions in GNOME Settings
- Verify PulseAudio/PipeWire is running: `pactl info`

**Extension not showing:**
```bash
# Re-enable extension
gnome-extensions disable gnome-assistant@saim
gnome-extensions enable gnome-assistant@saim

# Restart GNOME Shell (X11 only): Alt+F2, type 'r', press Enter
# For Wayland: Log out and back in
```

## FAQ

**Is my voice data sent anywhere?**
No. All speech recognition happens locally on your computer. No internet connection required.

**How accurate is it?**
Pretty good for short commands. The tiny.en model is optimized for speed while maintaining reasonable accuracy for command phrases.

**Can I use it in other languages?**
Currently only English is supported. No other plan as of now.

**Does it work on Wayland?**
Yes! That's why ydotool is required - it's the Wayland-compatible input simulator.

**How much CPU/RAM does it use?**
Minimal - around 100-250MB RAM and low CPU usage. It's designed to be lightweight.

## Advanced Configuration

For developers and advanced users, see the configuration file at `~/.config/gnome-assistant/config.json` which includes:
- Detailed ydotool key code reference
- Custom command examples
- Threshold and timing settings

## Contributing

Contributions welcome! Please open an issue or pull request on GitHub.

## License

0BSD License - See LICENSE file

## Credits

- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Offline speech recognition
- [sdbus-c++](https://github.com/Kistler-Group/sdbus-cpp) - D-Bus communication
- [ydotool](https://github.com/ReimuNotMoe/ydotool) - Wayland input simulation

---

**Remember**: This is experimental software. Use at your own risk. Always test new commands in a safe environment before relying on them for important tasks.
