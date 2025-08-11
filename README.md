# Voice Assistant for Nerd Dictation

An improved voice assistant built on top of nerd-dictation with better structure, error handling, and a GUI interface.

## Features

- **Three Operating Modes:**
  - **Normal Mode**: Listens for activation keyword ("hey" by default)
  - **Command Mode**: Processes voice commands with optional popup notification
  - **Typing Mode**: Converts speech to text

- **Enhanced GUI Control Panel:**
  - Real-time status monitoring with modern dark/light themes
  - Command mode popup notifications (configurable)
  - Interactive command testing and debugging
  - Comprehensive settings and appearance customization
  - Advanced command search and filtering
  - Live system logs monitoring
  - Color customization for all UI elements

- **Command Mode Popup:**
  - Automatic popup when entering command mode
  - Configurable position (top-right, top-left, center, etc.)
  - Shows available commands and current status
  - Auto-closes when exiting command mode
  - Customizable appearance and colors

- **Extensive Command Library:**
  - Application launching (terminal, firefox, spotify, etc.)
  - Window management (switch windows, new tabs, close windows)
  - Text editing shortcuts (copy, paste, undo, select all)
  - Volume control
  - System actions (screenshot, lock screen, suspend)

- **Improved Architecture:**
  - Object-oriented design with enhanced error handling
  - Comprehensive logging and debugging tools
  - JSON configuration system
  - Extensible command system with categories
  - Real-time status monitoring

## Installation

1. **Prerequisites:**
   ```bash
   # Install nerd-dictation (follow their installation guide)
   # https://github.com/ideasman42/nerd-dictation
   
   # Install ydotool
   sudo apt install ydotool  # Ubuntu/Debian
   # or
   sudo dnf install ydotool  # Fedora
   # or
   sudo pacman -S ydotool    # Arch
   
   # Install Python dependencies
   pip3 install --user fuzzyfinder
   
   # Install tkinter for GUI (if not already installed)
   sudo apt install python3-tk  # Ubuntu/Debian
   ```

2. **Quick Setup:**
   ```bash
   cd ~/.config/nerd-dictation
   ./setup.sh
   ```

3. **Enhanced Launcher:**
   ```bash
   # Launch everything with enhanced GUI
   ./launch.sh
   
   # Launch without GUI
   ./launch.sh --no-gui
   
   # Launch only GUI (for testing)
   ./launch.sh --no-dictation
   
   # Specify custom model directory
   ./launch.sh --model-dir /path/to/vosk/model
   ```

## Usage

### Quick Start with Enhanced Launcher

The easiest way to start the voice assistant:

```bash
cd ~/.config/nerd-dictation
./launch.sh
```

This will:
- Check and install dependencies
- Start the ydotool daemon
- Launch the enhanced GUI
- Start nerd-dictation with the voice assistant
- Show a command mode popup when activated

### Manual Starting

1. **Start nerd-dictation:**
   ```bash
   nerd-dictation begin --config voice_assistant_improved.py --vosk-model-dir=./model --simulate-input-tool=YDOTOOL
   ```

2. **Start the enhanced GUI:**
   ```bash
   python3 gui.py
   ```

### GUI Features

#### Main Interface
- **Status Tab**: Real-time monitoring with mode indicators and statistics
- **Commands Tab**: Searchable command library with categories
- **Settings Tab**: Voice recognition and threshold configuration
- **Appearance Tab**: Theme and color customization
- **Logs Tab**: Live system logs with filtering

#### Command Mode Popup
- Automatically appears when entering command mode
- Shows available commands and current status
- Configurable position and appearance
- Manual controls for mode switching
- Auto-closes when exiting command mode

#### Customization Options
- **Themes**: Dark and light themes
- **Colors**: Fully customizable color scheme
- **Popup Settings**: Position, size, and behavior
- **Advanced**: Borderless mode, transparency options

### Voice Commands

#### Mode Switching
- Say **"hey"** to activate command mode from normal mode
- Say **"typing mode"** or **"start typing"** to enter typing mode
- Say **"normal mode"** or **"stop typing"** to return to normal mode

#### Application Launching
- "open terminal" / "start terminal" / "launch terminal"
- "open firefox" / "launch firefox" / "start web browser"
- "open files" / "launch files" / "start file manager"
- "open spotify" / "launch spotify" / "start music"
- "open code" / "launch code" / "start vscode"
- "open calculator" / "launch calculator"

#### Window Management
- "show overview" / "show windows"
- "move left" / "go left" / "left desktop"
- "move right" / "go right" / "right desktop"
- "switch window" / "next window"
- "new tab" / "next tab"
- "close window" / "close tab"
- "minimize window" / "minimize"
- "maximize window" / "maximize"

#### Text Editing
- "copy" / "copy text"
- "paste" / "paste text"
- "cut" / "cut text"
- "undo" / "undo last"
- "redo" / "redo last"
- "select all" / "select everything"

#### Volume Control
- "volume up" / "turn up the volume" / "increase volume"
- "volume down" / "turn down the volume" / "decrease volume"
- "mute" / "mute audio" / "silence"

#### System Actions
- "lock screen" / "lock my screen"
- "screenshot" / "take screenshot"
- "sleep" / "suspend"

## Configuration

Edit `~/.config/nerd-dictation/config.json` to customize:

- **hotword**: Activation word (default: "hey")
- **fuzzy_match_threshold**: Similarity threshold for command matching (default: 85)
- **commands**: Add or modify voice commands
- **logging**: Configure logging behavior

## Architecture

### Main Components

1. **VoiceAssistant Class** (`voice_assistant_improved.py`):
   - Core logic and command processing
   - Mode management
   - Fuzzy command matching
   - Cursor tracking for typing mode

2. **GUI Interface** (`gui.py`):
   - Real-time status monitoring
   - Manual controls
   - Settings configuration
   - Log viewing

3. **Configuration** (`config.json`):
   - Centralized settings
   - Command definitions
   - Customizable parameters

### Key Improvements Over Original

1. **Fixed Typing Mode Issues:**
   - Proper cursor management when switching modes
   - Prevents retyping of previous text
   - Better exit command detection

2. **Better Error Handling:**
   - Comprehensive logging
   - Graceful command failure handling
   - User notifications for errors

3. **Extensible Design:**
   - Easy to add new commands
   - Configurable through JSON
   - Plugin-ready architecture

4. **GUI Management:**
   - Real-time monitoring
   - Easy mode switching
   - Command testing interface

## Troubleshooting

### Common Issues

1. **Typing Mode Not Working:**
   - Check that cursor files are writable in `/tmp`
   - Verify that mode switching commands are recognized
   - Check logs for cursor position tracking

2. **Commands Not Executing:**
   - Verify ydotool is running: `systemctl --user status ydotool`
   - Check fuzzy match threshold in settings
   - Review command logs for matching issues

3. **GUI Not Starting:**
   - Ensure tkinter is installed: `sudo apt install python3-tk`
   - Check Python path and dependencies
   - Run from terminal to see error messages

4. **Popup Not Appearing:**
   - Check if popup is enabled in Appearance settings
   - Verify assistant is entering command mode
   - Check for window manager conflicts

### Debugging Tools

1. **Enhanced Debug Tool:**
   ```bash
   # Real-time status monitoring
   python3 debug_tool.py monitor
   
   # Interactive testing mode
   python3 debug_tool.py interactive
   
   # Test command scenarios
   python3 debug_tool.py test
   
   # Show current status
   python3 debug_tool.py status
   
   # Reset to clean state
   python3 debug_tool.py reset
   ```

2. **Test Popup Functionality:**
   ```bash
   python3 test_popup.py
   ```

3. **Check Logs:**
   ```bash
   tail -f /tmp/voice_assistant.log
   ```

4. **Test Commands in GUI:**
   - Use the test input field in the Status tab
   - Monitor real-time feedback and results
   - Check mode transitions and cursor positions

### Performance Optimization

1. **Reduce Processing Delays:**
   - Adjust fuzzy match threshold (lower = faster, less accurate)
   - Use specific command phrases
   - Optimize system resources

2. **GUI Performance:**
   - Disable popup if not needed
   - Use light theme for lower resource usage
   - Close unnecessary tabs in GUI

### Advanced Configuration

1. **Custom Commands:**
   ```python
   # Add via GUI or directly in code
   assistant.add_command(
       ("my command", "custom action"), 
       "echo 'Hello World'"
   )
   ```

2. **Configuration Files:**
   - `gui_config.json`: GUI appearance and behavior
   - `config.json`: Voice assistant settings
   - Log files in `/tmp/voice_assistant.log`

3. **Integration with Other Tools:**
   - System integration via ydotool
   - Custom notification systems
   - Home automation integration

## Development

### Adding New Commands

1. **Via Configuration:**
   Edit `config.json` and add to the appropriate category.

2. **Via Code:**
   ```python
   assistant.add_command(
       ("new phrase", "another phrase"), 
       "command to execute"
   )
   ```

### Extending the GUI

The GUI is built with tkinter and designed to be easily extensible. Key areas for enhancement:

- Add new tabs for specific functionality
- Implement command management interface
- Add voice training/calibration tools
- Integrate with speech recognition settings

## Future Enhancements

- [ ] Plugin system for custom commands
- [ ] Voice training interface
- [ ] Multiple language support
- [ ] Cloud synchronization of settings
- [ ] Advanced command scripting
- [ ] Integration with home automation
- [ ] Voice feedback system
- [ ] Command history and analytics

## Contributing

Feel free to submit issues and enhancement requests. Key areas for contribution:

1. Additional command sets
2. GUI improvements
3. Performance optimizations
4. Documentation improvements
5. Testing and bug fixes

## License

This project builds upon nerd-dictation and follows similar licensing principles. Please respect the licenses of all dependencies.
