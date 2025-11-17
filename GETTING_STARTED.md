# Getting Started with GNOME Assistant

## Quick Start

### 1. Install Dependencies

**Fedora/RHEL:**
```bash
sudo dnf install cmake gcc-c++ sdbus-c++-devel jsoncpp-devel pulseaudio-libs-devel git
```

**Ubuntu/Debian:**
```bash
sudo apt install cmake g++ libsdbus-c++-dev libjsoncpp-dev libpulse-dev git
```

**Arch Linux:**
```bash
sudo pacman -S cmake gcc sdbus-cpp jsoncpp libpulse git
```

### 2. Build and Install

```bash
# Build the service (downloads tiny.en model ~75MB)
./build.sh

# Install everything (service + extension)
./install.sh
```

### 3. Enable and Start

```bash
# Enable GNOME extension
gnome-extensions enable gnome-assistant@saim

# Start the service
systemctl --user start gnome-assistant.service

# Verify it's running
systemctl --user status gnome-assistant.service
```

### 4. First Use

1. Click the microphone icon in your GNOME panel
2. Select "Start Service" if not already started
3. Say "hey" (the default hotword)
4. When the icon turns red, say a command like "open terminal"
5. The command will execute automatically

## Configuration

### Adding Custom Commands

1. Click the microphone icon → **Preferences**
2. Go to the **Commands** tab
3. Click **+ Add Command**
4. Fill in:
   - **Name**: Display name (e.g., "Firefox")
   - **Command**: Shell command to run (e.g., `firefox`)
   - **Phrases**: Voice triggers (e.g., "open firefox", "launch browser")
5. Click **Save**

### Adjusting Recognition

If commands aren't executing reliably:

1. Open **Preferences** → **Voice Recognition**
2. Lower **Command Threshold** (try 70% instead of 80%)
3. Increase **Processing Interval** (try 2.0s instead of 1.5s)

**Note**: The tiny.en model is optimized for speed. If you need better accuracy for complex phrases, you can manually upgrade to a larger model (base, small, medium) by replacing the model file in `~/.local/share/gnome-assistant/models/`.

### Changing the Hotword

1. Open **Preferences** → **General**
2. Change **Activation Hotword** from "hey" to your preferred word
3. Changes apply immediately

## Troubleshooting

### "Service not connected" error

The D-Bus service isn't running. Start it:
```bash
systemctl --user start gnome-assistant.service
```

### Commands not executing

1. Check the threshold in Preferences
2. Speak clearly and wait for the processing interval
3. Check logs: `journalctl --user -u gnome-assistant.service -f`

### Microphone not working

```bash
# Test microphone
parecord --channels=1 --rate=16000 test.wav
# Speak for a few seconds, then Ctrl+C
# Play back:
paplay test.wav
```

If that doesn't work, check your PulseAudio/PipeWire settings.

### Extension won't load

```bash
# Check for errors
journalctl -f -o cat /usr/bin/gnome-shell

# Reinstall
./install.sh
gnome-extensions enable gnome-assistant@saim
```

## Next Steps

- Explore the **Commands** preferences to add your own commands
- Try typing mode for dictation: click icon → "Switch to Typing Mode"
- Monitor the service: `journalctl --user -u gnome-assistant.service -f`
- Read the full README.md for advanced usage and D-Bus interface details

## Need Help?

- Check the logs: `/tmp/gnome_assistant.log` and `journalctl --user -u gnome-assistant.service`
- Verify D-Bus connection: `gdbus introspect --session --dest com.github.saim.GnomeAssistant --object-path /com/github/saim/GnomeAssistant`
- Open an issue on GitHub with log output
