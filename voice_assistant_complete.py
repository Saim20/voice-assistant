#!/usr/bin/env python3
"""
Improved Voice Assistant for Nerd Dictation
Enhanced with better structure, error handling, and simplified configuration
"""

import sys
import subprocess
import difflib
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Add current directory to Python path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager


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
    """Main voice assistant class with simplified structure"""
    
    def __init__(self, config_dir: str = "/tmp"):
        self.config_dir = Path(config_dir)
        self.mode_file = self.config_dir / "nerd-dictation.mode"
        self.buffer_file = Path("/tmp/nerd-dictation.buffer")
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        
        # Track processed text hashes to prevent reprocessing
        self._processed_text_hashes: set[int] = set()
        self._last_command_time = 0
        
        # Load commands from configuration
        self.commands = self.config_manager.get_commands()
        self.all_command_phrases = self.config_manager.get_all_phrases()
        
        # Debug: print loaded phrases
        logging.info(f"Loaded {len(self.all_command_phrases)} command phrases:")
        for phrase in self.all_command_phrases[:10]:  # Show first 10
            logging.info(f"  - '{phrase}'")
        if len(self.all_command_phrases) > 10:
            logging.info(f"  ... and {len(self.all_command_phrases) - 10} more")
        
        # Initialize state
        self._initialize_state()
    
    @property
    def hotword(self) -> str:
        return self.config_manager.hotword
    
    @property
    def command_threshold(self) -> int:
        return self.config_manager.command_threshold
    
    @property
    def processing_interval(self) -> float:
        return self.config_manager.processing_interval
    
    def add_command(self, phrases: Tuple[str, ...], action: str):
        """Add a new command and save to config"""
        # This is a simplified version - for full implementation, 
        # would need to properly categorize and save commands
        self.commands[phrases] = action
        self.all_command_phrases.extend(phrases)
        logging.info(f"Added new command: {phrases} -> {action}")

    def remove_command(self, phrases: Tuple[str, ...]):
        """Remove a command"""
        if phrases in self.commands:
            del self.commands[phrases]
            # Rebuild phrase list
            self.all_command_phrases = self.config_manager.get_all_phrases()
            logging.info(f"Removed command: {phrases}")
    
    def reload_commands(self):
        """Reload commands from configuration"""
        self.commands = self.config_manager.get_commands()
        self.all_command_phrases = self.config_manager.get_all_phrases()
        logging.info("Commands reloaded from configuration")
    
    def _initialize_state(self):
        """Initialize assistant state files"""
        try:
            # Ensure directories exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize mode file if it doesn't exist
            if not self.mode_file.exists():
                self.set_mode("normal")
                
            # Initialize anti-reprocessing state
            self._processed_text_hashes = set()
            self._last_command_time = 0.0
            self._current_text = ""
            self.same_length_count = 0
                
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
            
            # Track processed text to prevent reprocessing (already handled in process_command_mode)
            # Clear the buffer file for GUI
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
            return ""
        elif normal_mode_ratio >= self.command_threshold or cancel_ratio >= self.command_threshold:
            self.set_mode("normal")
            logging.info(f"Switched to normal mode (confidence: max({normal_mode_ratio}%, {cancel_ratio}%))")
            return ""

        # Find commands and execute if threshold is met
        best_match, ratio = self.find_best_command_match(text)
        
        logging.info(f"Command match - '{best_match}' with {ratio}% confidence (threshold: {self.command_threshold}%)")
        
        if best_match and ratio >= self.command_threshold:
            # Add to processed hashes immediately to prevent double execution
            text_hash = hash(text.strip().lower())
            self._processed_text_hashes.add(text_hash)
            self._last_command_time = time.time()
            
            # Clean old hashes (keep last 10)
            if len(self._processed_text_hashes) > 10:
                self._processed_text_hashes = set(list(self._processed_text_hashes)[-10:])
            
            # Find the corresponding action
            for command_phrases, action in self.commands.items():
                if best_match in command_phrases:
                    if action:
                        logging.info(f"Executing command ({ratio}%): '{best_match}' -> {action}")
                        self.execute_command(action)
                        logging.info(f"Executed command: {best_match} -> {action}")
                    else:
                        logging.info(f"Mode change command: {best_match}")
                    return ""  # Return immediately after successful command
        else:
            logging.info(f"No command match for: '{text}' (best: {ratio}%, threshold: {self.command_threshold}%)")
            # For non-matching commands in command mode, trigger suspend/resume to clear buffer
            word_count = len(text.split())
            
            if word_count >= 3:  # Only trigger for substantial text (3+ words)
                logging.info(f"Triggering suspend/resume cycle for non-matching command (words: {word_count})")
                self._trigger_suspend_resume_cycle()
            elif ratio < (self.command_threshold - 30):  # Clear if confidence is very low
                logging.info("Clearing buffer due to very low confidence")
        
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
            best_hotword_ratio = 0
            
            # Check if hotword appears as a separate word
            if hotword_lower in words_in_text:
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
                return ""
            else:
                logging.info(f"Text '{text}' in normal mode, hotword confidence too low ({best_hotword_ratio}%)")
        
        elif current_mode == "command":
            return self.process_command_mode(text)
        
        return ""

    def process_normal_mode(self, text: str) -> str:
        """Process text in normal mode - look for hotword"""
        text = text.strip()
        if not text:
            return ""
        
        # Check if hotword appears in the text (word boundary aware)
        text_lower = text.lower()
        hotword_lower = self.hotword.lower()
        
        # Check for exact word match or high similarity ratio
        words_in_text = text_lower.split()
        best_hotword_ratio = 0
        
        # Check if hotword appears as a separate word
        if hotword_lower in words_in_text:
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
            return ""
        else:
            # In normal mode, if text is getting long without hotword, trigger clear via suspend/resume
            word_count = len(words_in_text)
            if word_count > 7:  # 5 words threshold for normal mode
                logging.info(f"Buffer too long in normal mode ({word_count} words), triggering suspend/resume")
                self._trigger_suspend_resume_cycle()
            return ""

    def process_typing_mode(self, text: str) -> str:
        """Process text in typing mode - return text directly"""
        if not text:
            return ""
        
        # Check for exit commands in typing mode
        text_lower = text.lower()
        exit_phrases = ["stop typing", "exit typing", "normal mode", "go to normal mode"]
        
        for phrase in exit_phrases:
            if phrase in text_lower:
                self.set_mode("normal")
                logging.info(f"Exit phrase '{phrase}' detected, leaving typing mode")
                return ""
        
        # For typing mode, we need to track what we've already returned
        # Since we can't use cursors, we'll use a simple approach:
        # Store the last returned text and only return the new portion
        if not hasattr(self, '_last_typing_text'):
            self._last_typing_text = ""
        
        # If text is shorter than last time, it's a reset - return all text
        if len(text) < len(self._last_typing_text):
            self._last_typing_text = text
            logging.info(f"Typing mode reset detected, returning full text: '{text}'")
            return text
        
        # Extract only the new portion
        new_text = text[len(self._last_typing_text):]
        self._last_typing_text = text
        
        logging.info(f"Typing mode: returning new text: '{new_text}'")
        return new_text

    def process(self, text: str) -> str:
        """Main processing function - entry point for nerd-dictation"""
        current_mode = self.get_mode()
        current_time = time.time()
        
        # Store current text for anti-reprocessing mechanism
        self._current_text = text
        
        # Create hash of current text to detect reprocessing
        text_hash = hash(text.strip().lower())
        
        logging.info(f"Processing text in {current_mode} mode: '{text}'")

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
            return self.process_typing_mode(text)
        elif current_mode == "command":
            return self.process_command_mode(text)
        else:  # normal mode
            return self.process_normal_mode(text)
    


    def _trigger_suspend_resume_cycle(self):
        """Trigger a suspend/resume cycle using external script to clear nerd-dictation buffer"""
        try:
            script_path = Path.home() / ".config" / "nerd-dictation" / "command_executor.sh"
            
            if script_path.exists():
                # Use echo as a no-op command to trigger suspend/resume cycle
                subprocess.Popen(
                    [str(script_path), 'echo "Buffer clearing cycle"'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logging.info("Triggered suspend/resume cycle to clear nerd-dictation buffer")
            else:
                logging.warning("command_executor.sh not found")
        except Exception as e:
            logging.error(f"Error triggering suspend/resume cycle: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the voice assistant"""
        return {
            "mode": self.get_mode(),
            "commands_loaded": len(self.commands),
            "hotword": self.hotword,
            "command_threshold": self.command_threshold,
            "processing_interval": self.processing_interval
        }

    def reload_config(self):
        """Reload configuration from file - useful for live updates"""
        try:
            if self.config_manager.reload():
                self.commands = self.config_manager.get_commands()
                self.all_command_phrases = self.config_manager.get_all_phrases()
                logging.info("Configuration reloaded successfully")
                return True
            else:
                logging.error("Failed to reload configuration")
                return False
        except Exception as e:
            logging.error(f"Error reloading config: {e}")
            return False

    def get_available_commands(self) -> Dict[str, List[Any]]:
        """Get all available commands grouped by category for GUI display"""
        commands_by_category: Dict[str, List[Any]] = {}
        
        try:
            config_commands = self.config_manager.get("commands", {})
            for category, category_commands in config_commands.items():
                commands_by_category[category] = []
                for phrases_str, action in category_commands.items():
                    phrases = [phrase.strip() for phrase in str(phrases_str).split(',')]
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