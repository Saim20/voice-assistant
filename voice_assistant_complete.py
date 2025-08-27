#!/usr/bin/env python3
"""
Improved Voice Assistant for Nerd Dictation
Enhanced with better structure, error handling, and GUI preparation
"""

import subprocess
import difflib
import time
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
try:
    from fuzzyfinder import fuzzyfinder
except ImportError:
    fuzzyfinder = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/voice_assistant.log'),
        logging.StreamHandler()
    ]
)

class VoiceAssistant:
    """Main voice assistant class with improved structure"""
    
    def __init__(self, config_dir: str = "/tmp"):
        self.config_dir = Path(config_dir)
        self.mode_file = self.config_dir / "nerd-dictation.mode"
        self.cursor_file = self.config_dir / "nerd-dictation.cursor"
        self.typing_cursor_file = self.config_dir / "nerd-dictation.typing-cursor"
        self.buffer_file = Path("/tmp/nerd-dictation.buffer")
        self.state_file = self.config_dir / "voice_assistant_state.json"
        
        # Try both config locations
        config_path = Path.home() / ".config" / "nerd-dictation"
        self.commands_config_file = config_path / "commands_config.json"
        self.config_file = config_path / "config.json"
        
        # Load configuration
        self.config = self.load_config()
        self.hotword = self.config.get("hotword", "hey")
        self.fuzzy_match_threshold = self.config.get("fuzzy_match_threshold", 85)
        
        self.recognized_text_buffer = ""
        self.last_text_length = 0
        self.last_processing_time = 0
        self.processing_timeout = 1.5  # seconds - moderate timeout for hotword detection
        self.same_length_count = 0  # Track consecutive calls with same length
        self.buffer_cursor = 0  # Track position in buffer that has been processed
        self.last_buffer_update_time = time.time()  # Track when buffer was last updated
        self.auto_process_enabled = True  # Enable automatic processing for hotwords
        self.auto_execute_commands = False  # But disable automatic command execution
        
        # Load commands from configuration
        self.commands = self.load_commands()
        
        # Flatten command phrases for fuzzy matching
        self.all_command_phrases = [phrase for sublist in self.commands.keys() for phrase in sublist]
        
        # Debug: print loaded phrases
        logging.info(f"Loaded {len(self.all_command_phrases)} command phrases:")
        for phrase in self.all_command_phrases[:10]:  # Show first 10
            logging.info(f"  - '{phrase}'")
        if len(self.all_command_phrases) > 10:
            logging.info(f"  ... and {len(self.all_command_phrases) - 10} more")
        
        # Initialize state
        self._initialize_state()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            # Try commands_config.json first (has complete command mappings)
            if self.commands_config_file.exists():
                with open(self.commands_config_file, 'r') as f:
                    config = json.load(f)
                    logging.info(f"Loaded config from {self.commands_config_file}")
                    return config
            elif self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    logging.info(f"Loaded config from {self.config_file}")
                    return config
            else:
                logging.info("No config file found, creating default")
                return self.create_default_config()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return self.create_default_config()
    
    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        default_config = {
            "hotword": "hey",
            "fuzzy_match_threshold": 85,
            "commands": {
                "Application Launching": {
                    "open terminal,start terminal,launch terminal": "kgx",
                    "open firefox,launch firefox,start web browser": "firefox",
                    "open files,launch files,start file manager": "nautilus",
                    "open spotify,launch spotify,start music": "spotify",
                    "open code,launch code,start vscode": "code",
                    "open calculator,launch calculator": "gnome-calculator"
                },
                "Window and Desktop Management": {
                    "show overview,show windows": "ydotool key 125:1 125:0",
                    "left,move left,go left,left desktop": "ydotool key 125:1 30:1 30:0 125:0",
                    "right,move right,go right,right desktop": "ydotool key 125:1 32:1 32:0 125:0",
                    "switch window,next window": "ydotool key 56:1 15:1 15:0 56:0",
                    "new tab,next tab": "ydotool key 29:1 15:1 15:0 29:0",
                    "close window,close tab": "ydotool key 29:1 16:1 16:0 29:0",
                    "minimize window,minimize": "ydotool key 125:1 36:1 36:0 125:0",
                    "maximize window,maximize": "ydotool key 125:1 17:1 17:0 125:0"
                },
                "Text Editing Shortcuts": {
                    "copy,copy text": "ydotool key 29:1 46:1 46:0 29:0",
                    "paste,paste text": "ydotool key 29:1 47:1 47:0 29:0",
                    "cut,cut text": "ydotool key 29:1 45:1 45:0 29:0",
                    "undo,undo last": "ydotool key 29:1 44:1 44:0 29:0",
                    "redo,redo last": "ydotool key 29:1 42:1 21:1 21:0 42:0 29:0",
                    "select all,select everything": "ydotool key 29:1 30:1 30:0 29:0"
                },
                "Volume Control": {
                    "volume up,turn up the volume,increase volume": "pactl set-sink-volume @DEFAULT_SINK@ +5%",
                    "volume down,turn down the volume,decrease volume": "pactl set-sink-volume @DEFAULT_SINK@ -5%",
                    "mute,mute audio,silence": "pactl set-sink-mute @DEFAULT_SINK@ toggle"
                },
                "System Actions": {
                    "lock screen,lock my screen": "gnome-screensaver-command --lock",
                    "screenshot,take screenshot": "gnome-screenshot",
                    "sleep,suspend": "systemctl suspend"
                },
                "Mode Switching Commands": {
                    "go to typing mode,typing mode,start typing": None,
                    "go to normal mode,normal mode,stop typing,exit typing": None,
                    "go to command mode,command mode": None,
                    "cancel,stop,nevermind": None
                }
            }
        }
        
        # Save default config
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def load_commands(self) -> Dict[Tuple[str, ...], Optional[str]]:
        """Load commands from configuration and convert to expected format"""
        commands = {}
        
        try:
            config_commands = self.config.get("commands", {})
            
            # Check if config is in the old format (category -> phrases_str -> action)
            if any(isinstance(v, dict) and any(isinstance(vv, str) for vv in v.values()) for v in config_commands.values()):
                # Old format: "Application Launching": {"open terminal,start terminal": "kgx"}
                for category, category_commands in config_commands.items():
                    for phrases_str, action in category_commands.items():
                        # Split phrases by comma and create tuple
                        phrases = tuple(phrase.strip() for phrase in phrases_str.split(','))
                        commands[phrases] = action
            else:
                # New format: "applications": {"terminal": ["open terminal", "start terminal"]}
                # Create a mapping from command keys to actual commands
                command_mapping = {
                    # Applications
                    "terminal": "kgx",
                    "firefox": "firefox", 
                    "files": "nautilus",
                    "spotify": "spotify",
                    "code": "code",
                    "calculator": "gnome-calculator",
                    
                    # Window management
                    "show_overview": "ydotool key 125:1 125:0",
                    "move_left": "ydotool key 125:1 30:1 30:0 125:0",
                    "move_right": "ydotool key 125:1 32:1 32:0 125:0",
                    "switch_window": "ydotool key 56:1 15:1 15:0 56:0",
                    "new_tab": "ydotool key 29:1 15:1 15:0 29:0",
                    "close_window": "ydotool key 29:1 16:1 16:0 29:0",
                    "minimize_window": "ydotool key 125:1 36:1 36:0 125:0",
                    "maximize_window": "ydotool key 125:1 17:1 17:0 125:0",
                    
                    # Text editing
                    "copy": "ydotool key 29:1 46:1 46:0 29:0",
                    "paste": "ydotool key 29:1 47:1 47:0 29:0",
                    "cut": "ydotool key 29:1 45:1 45:0 29:0",
                    "undo": "ydotool key 29:1 44:1 44:0 29:0",
                    "redo": "ydotool key 29:1 42:1 21:1 21:0 42:0 29:0",
                    "select_all": "ydotool key 29:1 30:1 30:0 29:0",
                    
                    # Volume
                    "volume_up": "pactl set-sink-volume @DEFAULT_SINK@ +5%",
                    "volume_down": "pactl set-sink-volume @DEFAULT_SINK@ -5%",
                    "mute": "pactl set-sink-mute @DEFAULT_SINK@ toggle",
                    
                    # System
                    "lock_screen": "gnome-screensaver-command --lock",
                    "screenshot": "gnome-screenshot",
                    "sleep": "systemctl suspend",
                    
                    # Mode commands (no action)
                    "typing_mode": None,
                    "normal_mode": None,
                    "command_mode": None,
                    "cancel": None
                }
                
                for category, category_commands in config_commands.items():
                    for command_key, phrases_list in category_commands.items():
                        if isinstance(phrases_list, list):
                            # Convert list to tuple for consistency
                            phrases = tuple(phrases_list)
                            # Map command_key to actual command
                            action = command_mapping.get(command_key)
                            commands[phrases] = action
                        elif isinstance(phrases_list, str):
                            # Single phrase
                            phrases = (phrases_list,)
                            action = command_mapping.get(command_key)
                            commands[phrases] = action
            
            logging.info(f"Loaded {len(commands)} command groups from config")
            return commands
            
        except Exception as e:
            logging.error(f"Error loading commands: {e}")
            return self._get_fallback_commands()
    
    def _get_fallback_commands(self) -> Dict[Tuple[str, ...], Optional[str]]:
        """Fallback commands if config loading fails"""
        return {
            ("hey",): None,
            ("open terminal",): "kgx",
            ("cancel", "stop"): None
        }
    
    def save_commands(self):
        """Save current commands back to configuration file"""
        try:
            # Convert commands back to config format
            config_commands = {}
            for phrases, action in self.commands.items():
                # Find which category this belongs to (or create new one)
                phrases_str = ",".join(phrases)
                
                # Try to find existing category or use "Custom Commands"
                category = "Custom Commands"
                config_commands.setdefault(category, {})[phrases_str] = action
            
            self.config["commands"] = config_commands
            self.save_config(self.config)
            
        except Exception as e:
            logging.error(f"Error saving commands: {e}")
    
    def add_command(self, phrases: Tuple[str, ...], action: str):
        """Add a new command and save to config"""
        self.commands[phrases] = action
        self.all_command_phrases.extend(phrases)
        self.save_commands()
        logging.info(f"Added new command: {phrases} -> {action}")

    def remove_command(self, phrases: Tuple[str, ...]):
        """Remove a command and save to config"""
        if phrases in self.commands:
            del self.commands[phrases]
            # Rebuild phrase list
            self.all_command_phrases = [phrase for sublist in self.commands.keys() for phrase in sublist]
            self.save_commands()
            logging.info(f"Removed command: {phrases}")
    
    def update_command(self, old_phrases: Tuple[str, ...], new_phrases: Tuple[str, ...], action: str):
        """Update an existing command and save to config"""
        # Remove old command
        if old_phrases in self.commands:
            self.remove_command(old_phrases)
        
        # Add new command
        self.add_command(new_phrases, action)
    
    def _initialize_state(self):
        """Initialize assistant state files"""
        try:
            # Ensure directories exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize mode file if it doesn't exist
            if not self.mode_file.exists():
                self.set_mode("normal")
            
            # Initialize cursor files
            if not self.cursor_file.exists():
                self.update_cursor(0)
            
            if not self.typing_cursor_file.exists():
                self.update_typing_cursor(0)
                
        except Exception as e:
            logging.error(f"Error initializing state: {e}")
    
    def get_ratio(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings"""
        return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio() * 100

    def set_mode(self, mode: str):
        """Set the current mode"""
        try:
            with open(self.mode_file, 'w') as f:
                f.write(mode)
            logging.info(f"Mode set to: {mode}")
            
            # Notify about mode changes for GUI integration
            old_mode = getattr(self, '_last_mode', 'normal')
            self._last_mode = mode
            self._notify_mode_change(old_mode, mode)
            
        except Exception as e:
            logging.error(f"Error setting mode: {e}")
    
    def _notify_mode_change(self, old_mode: str, new_mode: str):
        """Notify about mode changes (for GUI integration)"""
        # This can be extended for notifications
        if new_mode == "command" and old_mode != "command":
            logging.info("Entered command mode - listening for voice commands")
            self._trigger_popup()
        elif old_mode == "command" and new_mode != "command":
            logging.info("Exited command mode")
    
    def save_buffer_to_file(self, text: str):
        """Save current buffer text to file for GUI display"""
        try:
            with open(self.buffer_file, 'w') as f:
                f.write(text)
        except Exception as e:
            logging.error(f"Error saving buffer: {e}")

    def _trigger_popup(self):
        """Trigger popup display through subprocess call"""
        try:
            # This could trigger a popup window or notification
            # For now, just log the event
            logging.info("Command mode popup triggered")
        except Exception as e:
            logging.error(f"Error triggering popup: {e}")

    def get_mode(self) -> str:
        """Get the current mode"""
        try:
            with open(self.mode_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return "normal"
        except Exception as e:
            logging.error(f"Error reading mode: {e}")
            return "normal"

    def get_cursor(self) -> int:
        """Get the main cursor position"""
        try:
            with open(self.cursor_file, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def get_typing_cursor(self) -> int:
        """Get the typing cursor position"""
        try:
            with open(self.typing_cursor_file, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def update_cursor(self, length: int):
        """Update the main cursor position"""
        try:
            with open(self.cursor_file, 'w') as f:
                f.write(str(length))
        except Exception as e:
            logging.error(f"Error updating cursor: {e}")

    def update_typing_cursor(self, length: int):
        """Update the typing cursor position"""
        try:
            with open(self.typing_cursor_file, 'w') as f:
                f.write(str(length))
        except Exception as e:
            logging.error(f"Error updating typing cursor: {e}")

    def execute_command(self, command: str) -> bool:
        """Execute a system command"""
        try:
            logging.info(f"Executing command: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"Command executed successfully: {command}")
                return True
            else:
                logging.error(f"Command failed: {command}, error: {result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            logging.error(f"Error executing command '{command}': {e}")
            return False

    def find_best_command_match(self, text: str) -> Tuple[Optional[str], float]:
        """Find the best matching command for given text"""
        try:
            best_match = None
            best_ratio = 0.0
            
            # Check all command phrases
            logging.debug(f"Checking {len(self.all_command_phrases)} phrases for text: '{text}'")
            for phrase in self.all_command_phrases:
                ratio = self.get_ratio(text, phrase)
                logging.debug(f"  '{text}' vs '{phrase}' = {ratio}%")
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = phrase
            
            logging.info(f"Best match for '{text}': '{best_match}' ({best_ratio}%)")
            return best_match, best_ratio
            
        except Exception as e:
            logging.error(f"Error finding command match: {e}")
            return None, 0.0

    def process_command_mode(self, text: str) -> str:
        """Process text in command mode - MANUAL PROCESSING ONLY"""
        # Clean up the text
        text = text.strip()
        logging.info(f"MANUAL: Processing command mode text: '{text}'")
        
        # Check for mode change commands first with very high confidence
        typing_mode_ratio = max(
            self.get_ratio(text, "typing mode"), 
            self.get_ratio(text, "go to typing mode"),
            self.get_ratio(text, "start typing")
        )
        normal_mode_ratio = max(
            self.get_ratio(text, "normal mode"), 
            self.get_ratio(text, "go to normal mode"),
            self.get_ratio(text, "stop typing"),
            self.get_ratio(text, "exit typing")
        )
        cancel_ratio = max(
            self.get_ratio(text, "cancel"),
            self.get_ratio(text, "stop"),
            self.get_ratio(text, "nevermind")
        )
        
        # Require extremely high confidence for mode changes
        mode_change_threshold = 98
        
        logging.info(f"MANUAL: Mode change confidences - typing: {typing_mode_ratio}%, normal: {normal_mode_ratio}%, cancel: {cancel_ratio}%")
        
        if typing_mode_ratio >= mode_change_threshold:
            self.set_mode("typing")
            logging.info(f"MANUAL: Switched to typing mode (confidence: {typing_mode_ratio}%)")
            self.clear_buffer_completely()
            return ""
        elif normal_mode_ratio >= mode_change_threshold or cancel_ratio >= mode_change_threshold:
            self.set_mode("normal")
            logging.info(f"MANUAL: Switched to normal mode (confidence: max({normal_mode_ratio}%, {cancel_ratio}%))")
            self.clear_buffer_completely()
            return ""

        # Find commands but require extremely high confidence for execution
        best_match, ratio = self.find_best_command_match(text)
        
        # Require extremely high confidence for command execution
        execution_threshold = 98
        
        logging.info(f"MANUAL: Command match - '{best_match}' with {ratio}% confidence (threshold: {execution_threshold}%)")
        
        if best_match and ratio >= execution_threshold:
            # Find the corresponding action
            for command_phrases, action in self.commands.items():
                if best_match in command_phrases:
                    if action:
                        logging.info(f"MANUAL: Executing high confidence command ({ratio}%): '{best_match}' -> {action}")
                        self.execute_command(action)
                        logging.info(f"MANUAL: Executed command: {best_match} -> {action}")
                    else:
                        logging.info(f"MANUAL: Mode change command: {best_match}")
                    # Clear buffer after processing command
                    self.clear_buffer_completely()
                    break
        else:
            logging.info(f"MANUAL: No high-confidence command match for: '{text}' (best: {ratio}%, threshold: {execution_threshold}%) - NO ACTION TAKEN")
            # Don't clear buffer, keep it for potential retry
        
        return ""

    def process_buffered_text(self, text: str) -> str:
        """Process the buffered text based on current mode - MANUAL ONLY"""
        current_mode = self.get_mode()
        logging.info(f"MANUAL processing buffered text in {current_mode} mode: '{text}'")
        
        if current_mode == "normal":
            # In normal mode, check for explicit hotword with very high confidence
            hotword_ratio = self.get_ratio(text.strip(), self.hotword)
            logging.info(f"Hotword '{self.hotword}' confidence: {hotword_ratio}%")
            if hotword_ratio >= 98:  # Require extremely high confidence for hotword
                self.set_mode("command")
                logging.info(f"MANUAL: Hotword '{self.hotword}' detected with very high confidence ({hotword_ratio}%), entering command mode")
                self.clear_buffer_completely()
                return ""
            else:
                logging.info(f"MANUAL: Text '{text}' in normal mode, hotword confidence too low ({hotword_ratio}%), no action taken")
        
        elif current_mode == "command":
            return self.process_command_mode(text)
        
        return ""

    def process_typing_mode(self, text: str) -> str:
        """Process text in typing mode"""
        current_text_length = len(text)
        last_processed_length = self.get_typing_cursor()
        
        # Handle text length decreases (nerd-dictation reset)
        if current_text_length < last_processed_length:
            logging.info("Text length decreased, resetting typing cursor")
            self.update_typing_cursor(0)
            last_processed_length = 0
        
        new_text = text[last_processed_length:]
        
        # Check for exit commands in typing mode
        recent_text = text[max(0, len(text) - 100):].lower()  # Check last 100 chars
        exit_phrases = ["stop typing", "exit typing", "normal mode", "go to normal mode"]
        
        for phrase in exit_phrases:
            if phrase in recent_text:
                self.set_mode("normal")
                logging.info(f"Exit phrase '{phrase}' detected, leaving typing mode")
                # Don't return the exit phrase text
                return ""
        
        self.update_typing_cursor(current_text_length)
        logging.info(f"Typing mode: returning text from {last_processed_length} to {current_text_length}: '{new_text}'")
        return new_text

    def process(self, text: str) -> str:
        """Main processing function - entry point for nerd-dictation"""
        current_mode = self.get_mode()
        current_text_length = len(text)
        last_processed_length = self.get_cursor()
        current_time = time.time()
        
        logging.info(f"Processing text in {current_mode} mode. Text length: {current_text_length}, Last processed: {last_processed_length}")

        # Handle text length decreases (nerd-dictation reset or new session)
        if current_text_length < last_processed_length:
            logging.info("Text length decreased, resetting cursor and buffers")
            self.update_cursor(0)
            self.update_typing_cursor(0)
            self.recognized_text_buffer = ""
            self.buffer_cursor = 0
            last_processed_length = 0

        # Update buffer for GUI display
        self.save_buffer_to_file(text)

        # Handle different modes
        if current_mode == "typing":
            result = self.process_typing_mode(text)
            return result
        else:
            # For normal and command modes, manage buffer with timeout
            return self._process_with_buffer_management(text, current_time)
    
    def _process_with_buffer_management(self, text: str, current_time: float) -> str:
        """Process text with proper buffer management and timeout"""
        current_text_length = len(text)
        last_processed_length = self.get_cursor()
        
        # Check if this looks like a completely new phrase (nerd-dictation often resets)
        # This happens when the new text is much shorter than what we've processed
        if current_text_length < last_processed_length:
            logging.info(f"Detected text reset, clearing state. New text: '{text}'")
            self.update_cursor(0)
            self.clear_buffer_completely()
            last_processed_length = 0
        
        # Check if we have new text
        has_new_text = current_text_length > last_processed_length
        
        if has_new_text:
            # Extract new text and add to buffer
            new_text = text[last_processed_length:]
            self.recognized_text_buffer += new_text
            self.last_buffer_update_time = current_time
            logging.info(f"Added new text to buffer: '{new_text}'. Full buffer: '{self.recognized_text_buffer}'")
            
            # Update cursor to track processed input
            self.update_cursor(current_text_length)
            
            # Check if buffer is getting too long and clear if needed
            self.check_and_clear_long_buffer()
        
        # NEVER auto-process - only manual processing allowed
        logging.debug(f"Buffer updated. Auto-processing disabled. Use force_process_buffer() to process manually.")
        return ""
    
    def force_process_buffer(self) -> str:
        """Manually force processing of the current buffer content"""
        if len(self.recognized_text_buffer) > self.buffer_cursor:
            unprocessed_buffer = self.recognized_text_buffer[self.buffer_cursor:]
            logging.info(f"Force processing buffer: '{unprocessed_buffer}'")
            
            # Process the unprocessed buffer
            processed_result = self.process_buffered_text(unprocessed_buffer)
            
            # Mark buffer content as processed
            self.buffer_cursor = len(self.recognized_text_buffer)
            
            return processed_result
        return ""
    
    def enable_auto_processing(self, enabled: bool = True):
        """Enable or disable automatic buffer processing"""
        self.auto_process_enabled = enabled
        logging.info(f"Auto-processing {'enabled' if enabled else 'disabled'}")
    
    def _clear_processed_buffer_content(self):
        """Clear processed content from buffer, keeping only unprocessed part"""
        if self.buffer_cursor > 0:
            unprocessed_part = self.recognized_text_buffer[self.buffer_cursor:]
            logging.info(f"Clearing processed buffer content. Keeping: '{unprocessed_part}'")
            self.recognized_text_buffer = unprocessed_part
            self.buffer_cursor = 0
    
    def clear_buffer_completely(self):
        """Completely clear the buffer (used after mode changes or command execution)"""
        logging.info(f"Completely clearing buffer: '{self.recognized_text_buffer}'")
        self.recognized_text_buffer = ""
        self.buffer_cursor = 0
        self.last_buffer_update_time = time.time()
    
    def check_and_clear_long_buffer(self):
        """Clear buffer if it gets too long to prevent accumulation"""
        max_buffer_length = 100  # Maximum characters in buffer
        if len(self.recognized_text_buffer) > max_buffer_length:
            logging.info(f"Buffer too long ({len(self.recognized_text_buffer)} chars), clearing: '{self.recognized_text_buffer[:50]}...'")
            self.clear_buffer_completely()
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the voice assistant"""
        return {
            "mode": self.get_mode(),
            "cursor": self.get_cursor(),
            "typing_cursor": self.get_typing_cursor(),
            "buffer_length": len(self.recognized_text_buffer),
            "buffer_cursor": self.buffer_cursor,
            "last_buffer_update": self.last_buffer_update_time,
            "commands_loaded": len(self.commands),
            "hotword": self.hotword,
            "fuzzy_threshold": self.fuzzy_match_threshold,
            "processing_timeout": self.processing_timeout,
            "auto_process_enabled": self.auto_process_enabled,
            "buffer_content": self.recognized_text_buffer
        }

    def reload_config(self):
        """Reload configuration from file - useful for live updates"""
        try:
            old_config = self.config.copy()
            self.config = self.load_config()
            self.hotword = self.config.get("hotword", "hey")
            self.fuzzy_match_threshold = self.config.get("fuzzy_match_threshold", 85)
            self.commands = self.load_commands()
            self.all_command_phrases = [phrase for sublist in self.commands.keys() for phrase in sublist]
            
            logging.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logging.error(f"Error reloading config: {e}")
            # Restore old config on error
            self.config = old_config
            return False

    def get_available_commands(self) -> Dict[str, List[str]]:
        """Get all available commands grouped by category for GUI display"""
        commands_by_category = {}
        
        try:
            config_commands = self.config.get("commands", {})
            for category, category_commands in config_commands.items():
                commands_by_category[category] = []
                for phrases_str, action in category_commands.items():
                    phrases = [phrase.strip() for phrase in phrases_str.split(',')]
                    commands_by_category[category].append({
                        'phrases': phrases,
                        'action': action,
                        'phrases_str': phrases_str
                    })
        except Exception as e:
            logging.error(f"Error getting commands: {e}")
        
        return commands_by_category

    def reset_state(self):
        """Reset assistant to clean state"""
        try:
            self.set_mode('normal')
            self.update_cursor(0)
            self.update_typing_cursor(0)
            self.clear_buffer_completely()
            self.same_length_count = 0
            
            # Clear buffer file
            if self.buffer_file.exists():
                self.buffer_file.unlink()
            
            logging.info("Assistant state reset")
            return True
        except Exception as e:
            logging.error(f"Error resetting state: {e}")
            return False


# Global assistant instance
assistant = VoiceAssistant()

def nerd_dictation_process(text: str) -> str:
    """Main entry point for nerd-dictation integration"""
    return assistant.process(text)


# if __name__ == "__main__":
#     # Test the assistant
#     print("Voice Assistant Test Mode")
    
#     # Reset assistant to clean state
#     assistant.reset_state()
#     print("Current status:", assistant.get_status())
    
#     print("\n=== Test 1: Conservative hotword detection ===")
    
#     # Test with exact hotword
#     print("User says: 'hey'")
#     result = assistant.process("hey")
#     print(f"Immediate result: '{result}', Mode: {assistant.get_mode()}")
    
#     # Enable auto-processing temporarily for testing
#     assistant.enable_auto_processing(True)
#     time.sleep(2.1)  # Wait longer than timeout
#     result = assistant.process("hey")  # Same text, should trigger processing with high confidence
#     print(f"After timeout: '{result}', Mode: {assistant.get_mode()}")
    
#     # Disable auto-processing for safety
#     assistant.enable_auto_processing(False)
    
#     print("\n=== Test 2: Manual command processing ===")
    
#     if assistant.get_mode() == "command":
#         print("In command mode, manually testing command")
#         assistant.clear_buffer_completely()
#         assistant.update_cursor(0)
        
#         print("User says: 'open terminal'")
#         result = assistant.process("open terminal")
#         print(f"Immediate result: '{result}', Buffer: '{assistant.recognized_text_buffer}'")
        
#         # Manually force processing
#         print("Manually forcing buffer processing...")
#         result = assistant.force_process_buffer()
#         print(f"Manual processing result: '{result}', Mode: {assistant.get_mode()}")
    
#     print("\n=== Test 3: Low confidence commands (should not execute) ===")
    
#     # Reset to command mode for testing
#     assistant.set_mode("command")
#     assistant.clear_buffer_completely()
#     assistant.update_cursor(0)
    
#     print("User says something unclear: 'open term'")
#     result = assistant.process("open term")
#     print(f"Immediate result: '{result}', Buffer: '{assistant.recognized_text_buffer}'")
    
#     # Try to force process (should not execute due to low confidence)
#     result = assistant.force_process_buffer()
#     print(f"Force processing result: '{result}', Mode: {assistant.get_mode()}")
    
#     print("\n=== Test 4: High confidence cancel ===")
    
#     print("User says: 'cancel'")
#     assistant.clear_buffer_completely()
#     assistant.update_cursor(0)
#     result = assistant.process("cancel")
#     result = assistant.force_process_buffer()
#     print(f"Cancel result: '{result}', Mode: {assistant.get_mode()}")
    
#     print("\n=== Final Status ===")
#     print("Final status:", assistant.get_status())
