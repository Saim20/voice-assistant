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
from fuzzyfinder import fuzzyfinder

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
        self.processing_timeout = 2.0  # seconds
        self.same_length_count = 0  # Track consecutive calls with same length
        
        # Load commands from configuration
        self.commands = self.load_commands()
        
        # Flatten command phrases for fuzzy matching
        self.all_command_phrases = [phrase for sublist in self.commands.keys() for phrase in sublist]
        
        # Initialize state
        self._initialize_state()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            # Try both config files
            if self.commands_config_file.exists():
                with open(self.commands_config_file, 'r') as f:
                    return json.load(f)
            elif self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default config if it doesn't exist
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
            self.commands_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.commands_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info("Configuration saved successfully")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def load_commands(self) -> Dict[Tuple[str, ...], Optional[str]]:
        """Load commands from configuration and convert to expected format"""
        commands = {}
        
        try:
            config_commands = self.config.get("commands", {})
            
            for category, category_commands in config_commands.items():
                for phrases_str, action in category_commands.items():
                    # Convert comma-separated phrases to tuple
                    phrases = tuple(phrase.strip() for phrase in phrases_str.split(','))
                    commands[phrases] = action
            
            logging.info(f"Loaded {len(commands)} commands from configuration")
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
            
            # Group by category (we'll determine category based on command content)
            categories = {
                "Application Launching": ["open", "launch", "start"],
                "Window and Desktop Management": ["window", "desktop", "switch", "tab", "minimize", "maximize", "overview"],
                "Text Editing Shortcuts": ["copy", "paste", "cut", "undo", "redo", "select"],
                "Volume Control": ["volume", "mute", "audio"],
                "System Actions": ["lock", "screenshot", "sleep", "suspend"],
                "Mode Switching Commands": ["mode", "typing", "normal", "command", "cancel", "stop"]
            }
            
            for phrases, action in self.commands.items():
                phrases_str = ",".join(phrases)
                
                # Determine category
                category = "Custom Commands"
                for cat, keywords in categories.items():
                    if any(keyword in phrases_str.lower() for keyword in keywords):
                        category = cat
                        break
                
                if category not in config_commands:
                    config_commands[category] = {}
                
                config_commands[category][phrases_str] = action
            
            # Update config and save
            self.config["commands"] = config_commands
            self.save_config(self.config)
            
            # Reload commands to ensure consistency
            self.commands = self.load_commands()
            self.all_command_phrases = [phrase for sublist in self.commands.keys() for phrase in sublist]
            
            logging.info("Commands saved and reloaded successfully")
            
        except Exception as e:
            logging.error(f"Error saving commands: {e}")
            raise
    
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
            for phrase in phrases:
                if phrase in self.all_command_phrases:
                    self.all_command_phrases.remove(phrase)
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
            if not self.mode_file.exists():
                with open(self.mode_file, "w") as f:
                    f.write("normal")
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
            old_mode = self.get_mode()
            with open(self.mode_file, "w") as f:
                f.write(mode)
            logging.info(f"Mode set to: {mode}")
            
            # Trigger popup notification if available
            self._notify_mode_change(old_mode, mode)
        except Exception as e:
            logging.error(f"Error setting mode: {e}")
    
    def _notify_mode_change(self, old_mode: str, new_mode: str):
        """Notify about mode changes (for GUI integration)"""
        # This can be extended for notifications
        if new_mode == "command" and old_mode != "command":
            logging.info("Entering COMMAND mode - triggering popup")
            self._trigger_popup()
        elif old_mode == "command" and new_mode != "command":
            logging.info("Exiting COMMAND mode - popup should be closed")
    
    def save_buffer_to_file(self, text: str):
        """Save current buffer text to file for GUI display"""
        try:
            with open(self.buffer_file, 'w') as f:
                f.write(text)
        except Exception as e:
            logging.error(f"Error saving buffer to file: {e}")

    def _trigger_popup(self):
        """Trigger popup display through subprocess call"""
        try:
            # Get the directory where this script is located
            script_dir = Path(__file__).parent
            popup_script = script_dir / "command_popup_kivy.py"
            
            # Save current buffer to file
            self.save_buffer_to_file(self.recognized_text_buffer)
            
            # Run command popup in background without waiting
            subprocess.Popen([
                "python3", 
                str(popup_script)
            ], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL)
            logging.info("Command popup triggered successfully in background")
        except Exception as e:
            logging.error(f"Error triggering popup: {e}")

    def get_mode(self) -> str:
        """Get the current mode"""
        try:
            with open(self.mode_file, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            # Create the file with default mode
            with open(self.mode_file, "w") as f:
                f.write("normal")
            return "normal"
        except Exception as e:
            logging.error(f"Error getting mode: {e}")
            return "normal"

    def get_cursor(self) -> int:
        """Get the main cursor position"""
        try:
            with open(self.cursor_file, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            self.update_cursor(0)
            return 0

    def get_typing_cursor(self) -> int:
        """Get the typing cursor position"""
        try:
            with open(self.typing_cursor_file, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            self.update_typing_cursor(0)
            return 0

    def update_cursor(self, length: int):
        """Update the main cursor position"""
        try:
            with open(self.cursor_file, "w") as f:
                f.write(str(length))
        except Exception as e:
            logging.error(f"Error updating cursor: {e}")

    def update_typing_cursor(self, length: int):
        """Update the typing cursor position"""
        try:
            with open(self.typing_cursor_file, "w") as f:
                f.write(str(length))
        except Exception as e:
            logging.error(f"Error updating typing cursor: {e}")

    def execute_command(self, command: str) -> bool:
        """Execute a system command"""
        try:
            subprocess.run(command, shell=True, check=True)
            logging.info(f"Successfully executed: {command}")
            return True
        except subprocess.CalledProcessError as e:
            error_message = f"Failed to execute command: '{command}'. Error: {e}"
            logging.error(error_message)
            try:
                subprocess.run(['notify-send', 'Voice Assistant Error', error_message], check=False)
            except:
                pass
            return False

    def find_best_command_match(self, text: str) -> Tuple[Optional[str], float]:
        """Find the best matching command for given text"""
        try:
            matches = fuzzyfinder(text, self.all_command_phrases)
            best_match = next(matches, None)
            
            if best_match:
                ratio = self.get_ratio(text, best_match)
                return best_match, ratio
            
            return None, 0.0
        except Exception as e:
            logging.error(f"Error finding command match: {e}")
            return None, 0.0

    def process_command_mode(self, text: str) -> str:
        """Process text in command mode"""
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
        
        if typing_mode_ratio >= self.fuzzy_match_threshold:
            self.set_mode("typing")
            # Set typing cursor to current position to avoid retyping
            current_cursor = self.get_cursor()
            self.update_typing_cursor(current_cursor)
            logging.info(f"Switching to TYPING mode. Cursor set to: {current_cursor}")
            return ""
        elif normal_mode_ratio >= self.fuzzy_match_threshold or cancel_ratio >= self.fuzzy_match_threshold:
            self.set_mode("normal")
            logging.info("Switching to NORMAL mode")
            return ""

        # Find and execute commands
        best_match, ratio = self.find_best_command_match(text)
        
        if best_match and ratio >= self.fuzzy_match_threshold:
            logging.info(f"Command match: '{best_match}' (Ratio: {ratio:.1f})")
            
            # Find the corresponding action
            for command_phrases, action in self.commands.items():
                if best_match in command_phrases:
                    if action:  # Only execute if action is not None
                        self.execute_command(action)
                    break
        else:
            logging.info(f"No suitable command found for: '{text}'")
        
        return ""

    def process_buffered_text(self, text: str) -> str:
        """Process the buffered text based on current mode"""
        current_mode = self.get_mode()
        logging.info(f"Processing buffered text in {current_mode} mode: '{text}'")
        
        if current_mode == "normal":
            if self.get_ratio(text, self.hotword) >= 90:
                self.set_mode("command")
                logging.info("Hotword recognized. Switching to COMMAND mode")
                return ""
            return ""
        
        elif current_mode == "command":
            return self.process_command_mode(text)
        
        return ""

    def process_typing_mode(self, text: str) -> str:
        """Process text in typing mode"""
        current_text_length = len(text)
        last_processed_length = self.get_typing_cursor()
        
        # Handle text length decreases (nerd-dictation reset)
        if current_text_length < last_processed_length:
            logging.info("Typing mode: Text length decreased - resetting typing cursor")
            self.update_typing_cursor(0)
            last_processed_length = 0
        
        new_text = text[last_processed_length:]
        
        # Check for exit commands in typing mode
        recent_text = text[max(0, len(text) - 100):].lower()  # Check last 100 chars
        exit_phrases = ["stop typing", "exit typing", "normal mode", "go to normal mode"]
        
        for phrase in exit_phrases:
            if phrase in recent_text:
                self.set_mode("normal")
                logging.info("Exiting TYPING mode, switching to NORMAL mode")
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
            logging.info("Text length decreased - resetting cursors")
            self.update_cursor(0)
            self.update_typing_cursor(0)
            self.recognized_text_buffer = ""
            self.same_length_count = 0
            last_processed_length = 0

        # Track consecutive calls with same length
        if current_text_length == self.last_text_length:
            self.same_length_count += 1
        else:
            self.same_length_count = 0
        self.last_text_length = current_text_length

        # Handle typing mode
        if current_mode == "typing":
            return self.process_typing_mode(text)
        
        # Handle normal and command modes
        new_text = text[last_processed_length:].lower().strip()
        
        # Add new text to buffer
        if current_text_length > last_processed_length and new_text:
            self.update_cursor(current_text_length)
            self.recognized_text_buffer += " " + new_text
            self.last_processing_time = current_time
            # Save buffer to file for GUI display
            self.save_buffer_to_file(self.recognized_text_buffer)
            logging.info(f"Added to buffer: '{new_text}', Full buffer: '{self.recognized_text_buffer}'")
        
        # Process buffer if:
        # 1. We have buffered text AND
        # 2. No new text was added (same cursor position) AND
        # 3. Either enough time passed OR we've had multiple calls with same length
        should_process_buffer = (
            self.recognized_text_buffer and 
            current_text_length == last_processed_length and 
            (self.same_length_count >= 1 or (current_time - self.last_processing_time) > 0.3)
        )
        
        if should_process_buffer:
            logging.info(f"Processing buffer (same_length_count: {self.same_length_count}, time_diff: {current_time - self.last_processing_time:.2f})")
            processed_output = self.process_buffered_text(self.recognized_text_buffer.strip())
            self.recognized_text_buffer = ""
            self.last_processing_time = current_time
            self.same_length_count = 0
            return processed_output
        
        return ""

    def get_status(self) -> Dict[str, Any]:
        """Get current assistant status - useful for GUI"""
        return {
            "mode": self.get_mode(),
            "cursor": self.get_cursor(),
            "typing_cursor": self.get_typing_cursor(),
            "buffer_length": len(self.recognized_text_buffer),
            "commands_count": len(self.commands)
        }


# Global assistant instance
assistant = VoiceAssistant()

def nerd_dictation_process(text: str) -> str:
    """Main entry point for nerd-dictation integration"""
    return assistant.process(text)


if __name__ == "__main__":
    # Test the assistant
    print("Voice Assistant Test Mode")
    print("Current status:", assistant.get_status())
    
    # Simulate some interactions
    test_inputs = [
        "hey",
        "open terminal",
        "typing mode",
        "hello world this is a test",
        "stop typing"
    ]
    
    for test_input in test_inputs:
        print(f"\nInput: '{test_input}'")
        result = assistant.process(test_input)
        print(f"Output: '{result}'")
        print(f"Status: {assistant.get_status()}")
