#!/usr/bin/env python3
"""
Configuration Manager for Voice Assistant
Handles all configuration loading, saving, and default settings
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


class ConfigManager:
    """Manages configuration for the voice assistant"""
    
    # Default settings
    DEFAULT_SETTINGS: Dict[str, Any] = {
        "hotword": "hey",
        "command_threshold": 80,
        "processing_interval": 1.0,
        "logging": {
            "level": "INFO",
            "file": "/tmp/voice_assistant.log"
        },
        "typing_mode": {
            "exit_phrases": ["stop typing", "exit typing", "normal mode", "go to normal mode"],
            "check_recent_chars": 100
        }
    }
    
    # Command to shell command mapping
    COMMAND_MAPPING: Dict[str, Optional[str]] = {
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
    
    # Default command phrases
    DEFAULT_COMMANDS = {
        "applications": {
            "terminal": ["open terminal", "start terminal", "launch terminal"],
            "firefox": ["open firefox", "launch firefox", "start web browser"],
            "files": ["open files", "launch files", "start file manager"],
            "spotify": ["open spotify", "launch spotify", "start music"],
            "code": ["open code", "launch code", "start vscode"],
            "calculator": ["open calculator", "launch calculator"]
        },
        "window_management": {
            "show_overview": ["show overview", "show windows"],
            "move_left": ["move left", "go left", "left desktop"],
            "move_right": ["move right", "go right", "right desktop"],
            "switch_window": ["switch window", "next window"],
            "new_tab": ["new tab", "next tab"],
            "close_window": ["close window", "close tab"],
            "minimize": ["minimize window", "minimize"],
            "maximize": ["maximize window", "maximize"]
        },
        "text_editing": {
            "copy": ["copy", "copy text"],
            "paste": ["paste", "paste text"],
            "cut": ["cut", "cut text"],
            "undo": ["undo", "undo last"],
            "redo": ["redo", "redo last"],
            "select_all": ["select all", "select everything"]
        },
        "system": {
            "volume_up": ["volume up", "turn up the volume", "increase volume"],
            "volume_down": ["volume down", "turn down the volume", "decrease volume"],
            "mute": ["mute", "mute audio", "silence"],
            "lock_screen": ["lock screen", "lock my screen"],
            "screenshot": ["screenshot", "take screenshot"],
            "sleep": ["sleep", "suspend"]
        },
        "modes": {
            "typing_mode": ["go to typing mode", "typing mode", "start typing"],
            "normal_mode": ["go to normal mode", "normal mode", "stop typing", "exit typing"],
            "command_mode": ["go to command mode", "command mode"],
            "cancel": ["cancel", "stop", "nevermind"]
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager"""
        if config_path is None:
            config_path = Path.home() / ".config" / "nerd-dictation" / "config.json"
        
        self.config_file = config_path
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> bool:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                    logging.info(f"Loaded config from {self.config_file}")
                    return True
            else:
                logging.info("No config file found, creating default")
                self.create_default()
                return True
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            self.create_default()
            return False
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logging.info(f"Config saved to {self.config_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            return False
    
    def create_default(self):
        """Create default configuration"""
        self.config = {
            **self.DEFAULT_SETTINGS,
            "commands": self.DEFAULT_COMMANDS
        }
        self.save()
        logging.info("Created default configuration")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value and save"""
        self.config[key] = value
        return self.save()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values"""
        self.config.update(updates)
        return self.save()
    
    def get_commands(self) -> Dict[Tuple[str, ...], Optional[str]]:
        """Get processed commands ready for use"""
        commands: Dict[Tuple[str, ...], Optional[str]] = {}
        
        try:
            config_commands = self.config.get("commands", {})
            
            for _, category_commands in config_commands.items():
                for command_key, phrases_list in category_commands.items():
                    # Get the actual shell command for this key
                    action = self.COMMAND_MAPPING.get(command_key)
                    
                    if isinstance(phrases_list, list):
                        phrases: Tuple[str, ...] = tuple(str(phrase) for phrase in phrases_list if phrase is not None)  # type: ignore
                        commands[phrases] = action
                    elif isinstance(phrases_list, str):
                        phrases = (phrases_list,)
                        commands[phrases] = action
            
            logging.info(f"Processed {len(commands)} command groups")
            return commands
            
        except Exception as e:
            logging.error(f"Error processing commands: {e}")
            return self._get_fallback_commands()
    
    def _get_fallback_commands(self) -> Dict[Tuple[str, ...], Optional[str]]:
        """Fallback commands if config processing fails"""
        return {
            ("hey",): None,
            ("open terminal",): "kgx",
            ("cancel", "stop"): None
        }
    
    def get_all_phrases(self) -> List[str]:
        """Get all command phrases for fuzzy matching"""
        commands = self.get_commands()
        return [phrase for phrases in commands.keys() for phrase in phrases]
    
    def reload(self) -> bool:
        """Reload configuration from file"""
        return self.load()
    
    @property
    def hotword(self) -> str:
        return self.get("hotword", self.DEFAULT_SETTINGS["hotword"])
    
    @property
    def command_threshold(self) -> int:
        return self.get("command_threshold", self.DEFAULT_SETTINGS["command_threshold"])
    
    @property
    def processing_interval(self) -> float:
        return self.get("processing_interval", self.DEFAULT_SETTINGS["processing_interval"])
