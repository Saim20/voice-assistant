#!/usr/bin/env python3
"""
Test script to verify popup triggering when saying "hey"
"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from voice_assistant_improved import assistant

def test_hey_popup_trigger():
    """Test the complete hey -> popup workflow"""
    print("=== Testing Hey Popup Trigger ===")
    
    # Reset to normal mode
    print(f"1. Initial mode: {assistant.get_mode()}")
    assistant.set_mode('normal')
    print(f"2. Set to normal mode: {assistant.get_mode()}")
    
    # Simulate nerd-dictation receiving "hey"
    print("3. Processing 'hey' (first call - adds to buffer)")
    result1 = assistant.process('hey')
    print(f"   Result: '{result1}'")
    
    # Simulate nerd-dictation second call (triggers processing)
    print("4. Processing 'hey' (second call - processes buffer)")
    time.sleep(0.5)  # Wait for buffer timeout
    result2 = assistant.process('hey')
    print(f"   Result: '{result2}'")
    print(f"5. Final mode: {assistant.get_mode()}")
    
    if assistant.get_mode() == "command":
        print("✅ SUCCESS: Hey hotword triggered command mode and popup!")
    else:
        print("❌ FAILED: Hey hotword did not trigger command mode")

if __name__ == "__main__":
    test_hey_popup_trigger()
