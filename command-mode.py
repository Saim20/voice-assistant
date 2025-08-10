# ~/.config/nerd-dictation/command_mode.pydef

import subprocess
import difflib
import time
import os
from fuzzyfinder import fuzzyfinder

# --- Mode and Command Definitions ---
MODE_FILE = "/tmp/nerd-dictation.mode"
CURSOR_FILE = "/tmp/nerd-dictation.cursor"
TYPING_CURSOR_FILE = "/tmp/nerd-dictation.typing-cursor"
HOTWORD = "hey"

COMMANDS = {
    # Application Launching
    ("open terminal", "start terminal", "launch terminal"): "kgx",
    ("open firefox", "launch firefox", "start web browser"): "firefox",
    ("open files", "launch files", "start file manager"): "nautilus",
    ("open spotify", "launch files", "start file manager"): "spotify",

    # Window and Desktop Management (using `ydotool`)
    ("show overview", "show windows"): "ydotool key 125:1 125:0",  # Super
    ("move left", "go left", "left desktop"): "ydotool key 125:1 30:1 30:0 125:0",  # Super+A
    ("move right", "go right", "right desktop"): "ydotool key 125:1 32:1 32:0 125:0",  # Super+D
    ("switch window", "next window"): "ydotool key 56:1 15:1 15:0 56:0",  # Alt+Tab
    ("new tab", "next tab"): "ydotool key 29:1 15:1 15:0 29:0",  # Ctrl+Tab
    ("close window"): "ydotool key 29:1 16:1 16:0 29:0",  # Ctrl+Q
    
    # Volume Control (using `pactl` for PulseAudio)
    ("volume up", "turn up the volume"): "pactl set-sink-volume @DEFAULT_SINK@ +5%",
    ("volume down", "turn down the volume"): "pactl set-sink-volume @DEFAULT_SINK@ -5%",
    ("mute", "mute audio"): "pactl set-sink-mute @DEFAULT_SINK@ toggle",

    # Other System Actions
    ("lock screen", "lock my screen"): "gnome-screensaver-command --lock",
    
    # This command is now handled internally and does not execute an external command.
    ("go to typing mode", "typing mode"): None
}

# Flatten the command phrases into a single list for fuzzyfinder.
ALL_COMMAND_PHRASES = [phrase for sublist in COMMANDS.keys() for phrase in sublist]

# --- Fuzzy Matching Settings ---
FUZZY_MATCH_THRESHOLD = 85

# Global variable for the text buffer
recognized_text_buffer = ""

def get_ratio(str1, str2):
    return difflib.SequenceMatcher(None, str1, str2).ratio() * 100

def set_mode(mode):
    with open(MODE_FILE, "w") as f:
        f.write(mode)

def get_mode():
    try:
        with open(MODE_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        set_mode("normal")
        return "normal"

def get_cursor():
    try:
        with open(CURSOR_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        with open(CURSOR_FILE, "w") as f:
            f.write("0")
        return 0

def get_typing_cursor():
    try:
        with open(TYPING_CURSOR_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        with open(TYPING_CURSOR_FILE, "w") as f:
            f.write("0")
        return 0

def update_cursor(length):
    with open(CURSOR_FILE, "w") as f:
        f.write(str(length))

def update_typing_cursor(length):
    with open(TYPING_CURSOR_FILE, "w") as f:
        f.write(str(length))

def process_buffered_text(text_to_process):
    """Handles the logic for processing the final, buffered text."""
    current_mode = get_mode()
    
    print(f"Processing buffered text in {current_mode} mode: '{text_to_process}'")
    
    if current_mode == "normal":
        if get_ratio(text_to_process, HOTWORD) >= 90:
            set_mode("command")
            print("Hotword recognized. Switching to COMMAND mode.")
            return ""
        else:
            return ""
    
    elif current_mode == "command":
        # Check for mode change command first
        typing_mode_ratio = max(get_ratio(text_to_process, "typing mode"), get_ratio(text_to_process, "go to typing mode"))
        if typing_mode_ratio >= FUZZY_MATCH_THRESHOLD:
            set_mode("typing")
            print("Switching to TYPING mode.")
            update_typing_cursor(get_cursor())
            return ""

        matches = fuzzyfinder(text_to_process, ALL_COMMAND_PHRASES)
        
        try:
            best_match = next(matches)
        except StopIteration:
            best_match = None
        
        if best_match:
            ratio = get_ratio(text_to_process, best_match)
            print(f"Closest command match: '{best_match}' (Ratio: {ratio})")

            if ratio >= FUZZY_MATCH_THRESHOLD:
                print("Threshold met. Executing command...")
                
                command_action = None
                for command_phrases, action in COMMANDS.items():
                    if best_match in command_phrases:
                        command_action = action
                        break

                if command_action:
                    print(f"Executing: '{command_action}'")
                    try:
                        subprocess.run(command_action, shell=True, check=True)
                        # No longer switching back to normal mode
                        
                    except subprocess.CalledProcessError as e:
                        error_message = f"Failed to execute command: '{command_action}'. Error: {e}"
                        print(error_message)
                        subprocess.run(['notify-send', 'Nerd Dictation Command Error', error_message], check=True)
                    
                return ""
        
        return "" # No command matched, so don't type anything

def nerd_dictation_process(text):
    global recognized_text_buffer
    
    current_mode = get_mode()

    if current_mode == "typing":
        last_processed_length = get_typing_cursor()
        new_text = text[last_processed_length:]
        update_typing_cursor(len(text))
        return new_text
    
    else:
        # We are in normal or command mode, use the main cursor
        last_processed_length = get_cursor()
        new_text = text[last_processed_length:].lower().strip()
        update_cursor(len(text))

        if new_text:
            recognized_text_buffer += " " + new_text
            return ""
        else:
            if recognized_text_buffer:
                processed_output = process_buffered_text(recognized_text_buffer.strip())
                recognized_text_buffer = ""
                return processed_output
            
            return ""
