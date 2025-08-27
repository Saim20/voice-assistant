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
        
        # Configuration file location
        config_path = Path.home() / ".config" / "nerd-dictation"
        self.config_file = config_path / "config.json"
        
        # Load configuration
        self.config = self.load_config()
        self.hotword = self.config.get("hotword", "hey")
        self.command_threshold = self.config.get("command_threshold", 80)
        self.processing_interval = self.config.get("processing_interval", 1.5)
        
        self.recognized_text_buffer = ""
        self.last_text_length = 0
        self.last_processing_time = 0
        self.buffer_cursor = 0  # Track position in buffer that has been processed
        self.last_buffer_update_time = time.time()  # Track when buffer was last updated
        self.last_process_call_time = time.time()  # Track when process() was last called
        
        # Track processed text hashes to prevent reprocessing
        self._processed_text_hashes = set()
        self._last_command_time = 0
        
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
            if self.config_file.exists():
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
            "command_threshold": 80,
            "processing_interval": 1.0,  # Reduced from 1.5 to 1.0 for better responsiveness
            "logging": {
                "level": "INFO",
                "file": "/tmp/voice_assistant.log"
            },
            "commands": {
                "applications": {
                    "terminal": [
                        "open terminal",
                        "start terminal",
                        "launch terminal"
                    ],
                    "firefox": [
                        "open firefox",
                        "launch firefox",
                        "start web browser"
                    ],
                    "files": [
                        "open files",
                        "launch files",
                        "start file manager"
                    ],
                    "spotify": [
                        "open spotify",
                        "launch spotify",
                        "start music"
                    ],
                    "code": [
                        "open code",
                        "launch code",
                        "start vscode"
                    ],
                    "calculator": [
                        "open calculator",
                        "launch calculator"
                    ]
                },
                "window_management": {
                    "show_overview": [
                        "show overview",
                        "show windows"
                    ],
                    "move_left": [
                        "move left",
                        "go left",
                        "left desktop"
                    ],
                    "move_right": [
                        "move right",
                        "go right",
                        "right desktop"
                    ],
                    "switch_window": [
                        "switch window",
                        "next window"
                    ],
                    "new_tab": [
                        "new tab",
                        "next tab"
                    ],
                    "close_window": [
                        "close window",
                        "close tab"
                    ],
                    "minimize": [
                        "minimize window",
                        "minimize"
                    ],
                    "maximize": [
                        "maximize window",
                        "maximize"
                    ]
                },
                "text_editing": {
                    "copy": [
                        "copy",
                        "copy text"
                    ],
                    "paste": [
                        "paste",
                        "paste text"
                    ],
                    "cut": [
                        "cut",
                        "cut text"
                    ],
                    "undo": [
                        "undo",
                        "undo last"
                    ],
                    "redo": [
                        "redo",
                        "redo last"
                    ],
                    "select_all": [
                        "select all",
                        "select everything"
                    ]
                },
                "system": {
                    "volume_up": [
                        "volume up",
                        "turn up the volume",
                        "increase volume"
                    ],
                    "volume_down": [
                        "volume down",
                        "turn down the volume",
                        "decrease volume"
                    ],
                    "mute": [
                        "mute",
                        "mute audio",
                        "silence"
                    ],
                    "lock_screen": [
                        "lock screen",
                        "lock my screen"
                    ],
                    "screenshot": [
                        "screenshot",
                        "take screenshot"
                    ],
                    "sleep": [
                        "sleep",
                        "suspend"
                    ]
                },
                "modes": {
                    "typing_mode": [
                        "go to typing mode",
                        "typing mode",
                        "start typing"
                    ],
                    "normal_mode": [
                        "go to normal mode",
                        "normal mode",
                        "stop typing",
                        "exit typing"
                    ],
                    "command_mode": [
                        "go to command mode",
                        "command mode"
                    ],
                    "cancel": [
                        "cancel",
                        "stop",
                        "nevermind"
                    ]
                }
            },
            "typing_mode": {
                "exit_phrases": [
                    "stop typing",
                    "exit typing",
                    "normal mode",
                    "go to normal mode"
                ],
                "check_recent_chars": 100
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
                "minimize": "ydotool key 125:1 36:1 36:0 125:0",
                "maximize": "ydotool key 125:1 17:1 17:0 125:0",
                
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
        """Set the current mode using external script with suspend/resume"""
        try:
            old_mode = self.get_mode()
            
            # Use external script for mode changes to handle suspend/resume
            script_path = Path.home() / ".config" / "nerd-dictation" / "mode_changer.sh"
            
            if script_path.exists():
                # Use the external script that handles suspend/resume
                subprocess.Popen(
                    [str(script_path), mode],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logging.info(f"Mode change requested via script: {old_mode} -> {mode}")
            else:
                # Fallback to direct mode change
                with open(self.mode_file, 'w') as f:
                    f.write(mode)
                logging.info(f"Mode set directly: {old_mode} -> {mode}")
            
            # Notify about mode changes for GUI integration
            self._last_mode = mode
            self._notify_mode_change(old_mode, mode)
            
        except Exception as e:
            logging.error(f"Error setting mode to {mode}: {e}")
            # Fallback: try direct mode change
            try:
                with open(self.mode_file, 'w') as f:
                    f.write(mode)
                logging.info(f"Mode set via fallback: {mode}")
            except:
                logging.error(f"Failed to set mode even with fallback: {mode}")
    
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
        """Execute a system command using external script that handles suspend/resume"""
        try:
            logging.info(f"Executing command with suspend/resume: {command}")
            
            # Get path to command executor script
            script_path = self.config_dir.parent / "nerd-dictation" / "command_executor.sh"
            if not script_path.exists():
                # Fallback to current directory
                script_path = Path.home() / ".config" / "nerd-dictation" / "command_executor.sh"
            
            if not script_path.exists():
                logging.error(f"Command executor script not found at {script_path}")
                # Fallback to direct execution without suspend/resume
                process = subprocess.Popen(
                    command, 
                    shell=True, 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logging.info(f"Direct command execution (no suspend/resume): {command} (PID: {process.pid})")
            else:
                # Execute command through the suspend/resume script
                process = subprocess.Popen(
                    [str(script_path), command],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logging.info(f"Command executed with suspend/resume: {command} (PID: {process.pid})")
            
            # Mark current text length as processed to prevent reprocessing
            current_text_length = getattr(self, '_current_text_length', 0)
            current_text = getattr(self, '_current_text', '')
            
            if current_text_length > 0:
                self.update_cursor(current_text_length)
                logging.info(f"Updated cursor to {current_text_length} after command execution")
                
                # Track this text as processed
                text_hash = hash(current_text.strip().lower())
                self._processed_text_hashes.add(text_hash)
                self._last_command_time = time.time()
                
                # Clean old hashes (keep last 10)
                if len(self._processed_text_hashes) > 10:
                    self._processed_text_hashes = set(list(self._processed_text_hashes)[-10:])
            
            # Clear buffer immediately after command execution
            self.clear_buffer_completely()
            # Also clear the buffer file for GUI
            self.save_buffer_to_file("")
            
            return True
            
        except Exception as e:
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
        """Process text in command mode with automatic execution"""
        # Clean up the text
        text = text.strip()
        logging.info(f"Processing command mode text: '{text}'")
        
        # Check for mode change commands first
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
        
        logging.info(f"Mode change confidences - typing: {typing_mode_ratio}%, normal: {normal_mode_ratio}%, cancel: {cancel_ratio}%")
        
        if typing_mode_ratio >= self.command_threshold:
            self.set_mode("typing")
            logging.info(f"Switched to typing mode (confidence: {typing_mode_ratio}%)")
            self.clear_buffer_completely()
            return ""
        elif normal_mode_ratio >= self.command_threshold or cancel_ratio >= self.command_threshold:
            self.set_mode("normal")
            logging.info(f"Switched to normal mode (confidence: max({normal_mode_ratio}%, {cancel_ratio}%))")
            self.clear_buffer_completely()
            return ""

        # Find commands and execute if threshold is met
        best_match, ratio = self.find_best_command_match(text)
        
        logging.info(f"Command match - '{best_match}' with {ratio}% confidence (threshold: {self.command_threshold}%)")
        
        if best_match and ratio >= self.command_threshold:
            # Find the corresponding action
            for command_phrases, action in self.commands.items():
                if best_match in command_phrases:
                    if action:
                        logging.info(f"Executing command ({ratio}%): '{best_match}' -> {action}")
                        self.execute_command(action)
                        logging.info(f"Executed command: {best_match} -> {action}")
                    else:
                        logging.info(f"Mode change command: {best_match}")
                        # Clear buffer for mode changes too
                        self.clear_buffer_completely()
                    return ""  # Return immediately after successful command
        else:
            logging.info(f"No command match for: '{text}' (best: {ratio}%, threshold: {self.command_threshold}%)")
            # Clear buffer more aggressively for failed commands
            if len(text) > 15:  # Reduced from 20 to 15 characters
                logging.info("Clearing buffer due to failed command processing")
                self.clear_buffer_completely()
            elif ratio < (self.command_threshold - 30):  # Clear if confidence is very low
                logging.info("Clearing buffer due to very low confidence")
                self.clear_buffer_completely()
        
        return ""

    def process_buffered_text(self, text: str) -> str:
        """Process the buffered text based on current mode"""
        current_mode = self.get_mode()
        logging.info(f"Processing buffered text in {current_mode} mode: '{text}'")
        
        if current_mode == "normal":
            # In normal mode, check for explicit hotword
            # Check if hotword appears in the text (word boundary aware)
            text_lower = text.strip().lower()
            hotword_lower = self.hotword.lower()
            
            # Check for exact word match or high similarity ratio
            words_in_text = text_lower.split()
            hotword_found = False
            best_hotword_ratio = 0
            
            # Check if hotword appears as a separate word
            if hotword_lower in words_in_text:
                hotword_found = True
                best_hotword_ratio = 100
                logging.info(f"Hotword '{self.hotword}' found as exact word match")
            else:
                # Check similarity with each word
                for word in words_in_text:
                    ratio = self.get_ratio(word, hotword_lower)
                    if ratio > best_hotword_ratio:
                        best_hotword_ratio = ratio
                
                # Also check similarity with the entire text for short phrases
                full_text_ratio = self.get_ratio(text_lower, hotword_lower)
                if full_text_ratio > best_hotword_ratio:
                    best_hotword_ratio = full_text_ratio
            
            logging.info(f"Hotword '{self.hotword}' confidence: {best_hotword_ratio}%")
            
            if best_hotword_ratio >= self.command_threshold:
                self.set_mode("command")
                logging.info(f"Hotword '{self.hotword}' detected ({best_hotword_ratio}%), entering command mode")
                # Don't clear buffer completely - just mark as processed to avoid losing context
                self.buffer_cursor = len(self.recognized_text_buffer)
                return ""
            else:
                logging.info(f"Text '{text}' in normal mode, hotword confidence too low ({best_hotword_ratio}%)")
        
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
        
        # Store current text for use in command execution
        self._current_text = text
        self._current_text_length = current_text_length
        
        # Create hash of current text to detect reprocessing
        text_hash = hash(text.strip().lower())
        
        logging.info(f"Processing text in {current_mode} mode. Text length: {current_text_length}, Last processed: {last_processed_length}")

        # Handle text length decreases (nerd-dictation reset or new session)
        if current_text_length < last_processed_length:
            logging.info("Text length decreased, resetting cursor and buffers")
            self.update_cursor(0)
            self.update_typing_cursor(0)
            self.recognized_text_buffer = ""
            self.buffer_cursor = 0
            self._processed_text_hashes.clear()  # Clear hash tracking
            last_processed_length = 0

        # Check if we've already processed this exact text recently (within last 5 seconds)
        if (text_hash in self._processed_text_hashes and 
            current_time - self._last_command_time < 5.0 and 
            current_mode == "command"):
            logging.info("Already processed this text recently, skipping to prevent reprocessing")
            return ""

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
        """Process text with proper buffer management and immediate processing when patterns are detected"""
        current_text_length = len(text)
        last_processed_length = self.get_cursor()
        
        # Track when this function was called
        self.last_process_call_time = current_time
        
        # Check if this looks like a completely new phrase (nerd-dictation often resets)
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
            
            # Update cursor to track what we've seen (but not necessarily processed)
            self.update_cursor(current_text_length)
            
            # Check if buffer is getting too long and clear if needed
            self.check_and_clear_long_buffer()
            
            # Process immediately if we detect word boundaries or complete phrases
            should_process_now = self._should_process_immediately(self.recognized_text_buffer, new_text)
            if should_process_now:
                logging.info(f"Immediate processing triggered by pattern detection")
                return self._process_buffer()
        
        # Fallback: Also check time-based processing for any remaining cases
        time_since_buffer_update = current_time - self.last_buffer_update_time
        has_unprocessed_text = len(self.recognized_text_buffer) > self.buffer_cursor
        
        # Use shorter timeout in command mode since user expects immediate response
        current_mode = self.get_mode()
        timeout = 0.8 if current_mode == "command" else self.processing_interval
        
        if time_since_buffer_update >= timeout and has_unprocessed_text:
            logging.info(f"Processing timeout ({timeout}s) reached, auto-processing buffer")
            return self._process_buffer()
        
        return ""
    
    def _should_process_immediately(self, full_buffer: str, new_text: str) -> bool:
        """Determine if we should process immediately based on text patterns"""
        current_mode = self.get_mode()
        buffer_lower = full_buffer.lower().strip()
        
        # In normal mode, only process if we detect the hotword
        if current_mode == "normal":
            if self.hotword.lower() in buffer_lower:
                logging.info(f"Hotword '{self.hotword}' detected in buffer, triggering immediate processing")
                return True
            return False
        
        # In command mode, be more selective about when to process
        elif current_mode == "command":
            # Only process if we see potential command endings that look complete
            command_endings = [
                'terminal', 'firefox', 'spotify', 'files', 'code', 'calculator',
                'overview', 'window', 'copy', 'paste', 'volume', 'mute', 
                'screenshot', 'mode', 'cancel', 'typing'
            ]
            
            # Check if buffer ends with a command word and looks complete
            for ending in command_endings:
                if buffer_lower.endswith(ending):
                    words = buffer_lower.split()
                    # Only process if we have enough context (2+ words)
                    if len(words) >= 2:
                        # Check if it looks like a complete command (action + target)
                        for word in words:
                            if word in ['open', 'start', 'launch', 'close', 'show', 'go', 'move', 'turn', 'take']:
                                logging.info(f"Complete command detected: '{buffer_lower}', triggering immediate processing")
                                return True
            
            # Also process mode change commands immediately
            mode_phrases = ['typing mode', 'normal mode', 'cancel', 'stop', 'nevermind']
            for phrase in mode_phrases:
                if phrase in buffer_lower:
                    logging.info(f"Mode change command detected: '{phrase}', triggering immediate processing")
                    return True
        
        return False
    
    def _extract_clean_command(self, command_text: str) -> Optional[str]:
        """Extract a clean command from potentially noisy text, prioritizing the last/most recent command"""
        words = command_text.strip().split()
        if not words:
            return None
        
        # Look for command patterns like "open terminal", "launch firefox", etc.
        action_words = ['open', 'start', 'launch', 'close', 'show', 'go', 'move', 'turn', 'take']
        target_words = ['terminal', 'firefox', 'spotify', 'files', 'code', 'calculator', 
                       'overview', 'window', 'copy', 'paste', 'volume', 'screenshot']
        
        # Find ALL action + target combinations, then take the LAST one
        found_commands = []
        
        # Try to find action + target combinations
        for i, word in enumerate(words):
            if word in action_words and i + 1 < len(words):
                next_word = words[i + 1]
                if next_word in target_words:
                    clean_command = f"{word} {next_word}"
                    found_commands.append(clean_command)
        
        # Also check for single-word commands at the end
        single_commands = ['copy', 'paste', 'cut', 'undo', 'redo', 'mute', 'cancel', 'stop']
        for word in reversed(words):  # Check from end to prioritize last commands
            if word in single_commands:
                found_commands.append(word)
                break  # Take the last single command found
        
        # Return the LAST command found (most recent)
        if found_commands:
            last_command = found_commands[-1]
            logging.info(f"Extracted clean command: '{last_command}' from '{command_text}' (found {len(found_commands)} commands)")
            return last_command
        
        # If we find a target word at the end with an action word somewhere, try that
        if words[-1] in target_words:
            for word in reversed(words[:-1]):
                if word in action_words:
                    clean_command = f"{word} {words[-1]}"
                    logging.info(f"Extracted end-pattern command: '{clean_command}' from '{command_text}'")
                    return clean_command
        
        return None

    def _process_buffer(self) -> str:
        """Process the current buffer content"""
        current_mode = self.get_mode()
        
        if current_mode == "command":
            # In command mode, extract clean commands from the buffer
            buffer_text = self.recognized_text_buffer.lower().strip()
            
            # Find the hotword and extract command after it
            hotword_pos = buffer_text.find(self.hotword.lower())
            if hotword_pos >= 0:
                # Get text after the hotword
                command_text = buffer_text[hotword_pos + len(self.hotword):].strip()
                if command_text:
                    # Try to extract a clean command by looking for common command patterns
                    clean_command = self._extract_clean_command(command_text)
                    if clean_command:
                        logging.info(f"Processing extracted clean command: '{clean_command}'")
                        result = self.process_buffered_text(clean_command)
                        # Clear buffer after successful command to prevent accumulation
                        if result == "":  # Command was processed (even if no text returned)
                            self.clear_buffer_completely()
                        return result
                    else:
                        logging.info(f"Processing full command from buffer: '{command_text}'")
                        result = self.process_buffered_text(command_text)
                        # Mark entire buffer as processed after command execution
                        self.buffer_cursor = len(self.recognized_text_buffer)
                        return result
            
            # Fallback: process unprocessed portion
            if len(self.recognized_text_buffer) > self.buffer_cursor:
                unprocessed_buffer = self.recognized_text_buffer[self.buffer_cursor:]
                logging.info(f"Processing unprocessed buffer: '{unprocessed_buffer}'")
                processed_result = self.process_buffered_text(unprocessed_buffer)
                self.buffer_cursor = len(self.recognized_text_buffer)
                return processed_result
        else:
            # For normal mode, process unprocessed buffer as before
            if len(self.recognized_text_buffer) > self.buffer_cursor:
                unprocessed_buffer = self.recognized_text_buffer[self.buffer_cursor:]
                logging.info(f"Processing buffer: '{unprocessed_buffer}'")
                processed_result = self.process_buffered_text(unprocessed_buffer)
                self.buffer_cursor = len(self.recognized_text_buffer)
                return processed_result
                
        return ""
    
    def clear_buffer_completely(self):
        """Completely clear the buffer (used after mode changes or command execution)"""
        logging.info(f"Completely clearing buffer: '{self.recognized_text_buffer}'")
        self.recognized_text_buffer = ""
        self.buffer_cursor = 0
        self.last_buffer_update_time = time.time()
        self.last_process_call_time = time.time()
        
        # DON'T reset cursor files here - let execute_command handle cursor updates
        # This prevents the cursor from being reset and causing reprocessing
        
        # Clear the buffer file for GUI immediately
        self.save_buffer_to_file("")
    
    def check_and_clear_long_buffer(self):
        """Clear buffer if it gets too long to prevent accumulation"""
        max_buffer_length = 150  # Increased from 50 to 150 characters to allow longer command sequences
        if len(self.recognized_text_buffer) > max_buffer_length:
            logging.info(f"Buffer too long ({len(self.recognized_text_buffer)} chars), clearing: '{self.recognized_text_buffer[:30]}...'")
            self.clear_buffer_completely()
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the voice assistant"""
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the voice assistant"""
        return {
            "mode": self.get_mode(),
            "cursor": self.get_cursor(),
            "typing_cursor": self.get_typing_cursor(),
            "buffer_length": len(self.recognized_text_buffer),
            "buffer_cursor": self.buffer_cursor,
            "last_buffer_update": self.last_buffer_update_time,
            "last_process_call": self.last_process_call_time,
            "commands_loaded": len(self.commands),
            "hotword": self.hotword,
            "command_threshold": self.command_threshold,
            "processing_interval": self.processing_interval,
            "buffer_content": self.recognized_text_buffer
        }

    def reload_config(self):
        """Reload configuration from file - useful for live updates"""
        try:
            old_config = self.config.copy()
            self.config = self.load_config()
            self.hotword = self.config.get("hotword", "hey")
            self.command_threshold = self.config.get("command_threshold", 80)
            self.processing_interval = self.config.get("processing_interval", 1.5)
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