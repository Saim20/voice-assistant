#!/usr/bin/env python3
"""
Voice Assistant Debug and Monitoring Tool
"""

import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from voice_assistant_improved import VoiceAssistant

def monitor_assistant():
    """Monitor assistant status in real-time"""
    assistant = VoiceAssistant()
    
    print("Voice Assistant Monitor - Press Ctrl+C to exit")
    print("-" * 50)
    
    last_status = None
    
    try:
        while True:
            status = assistant.get_status()
            
            # Only print if status changed
            if status != last_status:
                print(f"Mode: {status['mode']:<8} | "
                      f"Cursor: {status['cursor']:<3} | "
                      f"T-Cursor: {status['typing_cursor']:<3} | "
                      f"Buffer: {status['buffer_length']:<3} | "
                      f"Time: {time.strftime('%H:%M:%S')}")
                last_status = status.copy()
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

def test_commands():
    """Test command recognition"""
    assistant = VoiceAssistant()
    
    test_scenarios = [
        # (input_sequence, expected_behavior)
        (["hey"], "Should switch to command mode"),
        (["hey", "hey"], "Should switch to command mode"),
        (["hey", "hey", "open terminal"], "Should execute open terminal"),
        (["hey", "hey", "typing mode"], "Should switch to typing mode"),
        (["hello world typing"], "Should type in typing mode"),
        (["hello world typing stop typing"], "Should exit typing mode"),
    ]
    
    print("Testing command scenarios...")
    print("-" * 50)
    
    for i, (inputs, expected) in enumerate(test_scenarios):
        print(f"\nScenario {i+1}: {expected}")
        print(f"Inputs: {inputs}")
        
        # Reset for each scenario
        assistant.set_mode("normal")
        assistant.update_cursor(0)
        assistant.update_typing_cursor(0)
        assistant.recognized_text_buffer = ""
        assistant.last_processing_time = 0
        
        results = []
        for j, text_input in enumerate(inputs):
            print(f"  Step {j+1}: '{text_input}'")
            
            # Simulate the way nerd-dictation sends text (accumulative)
            accumulated_text = " ".join(inputs[:j+1])
            
            # First call with new text
            result1 = assistant.process(accumulated_text)
            
            # Second call with same text (simulating no new input)
            time.sleep(0.1)  # Small delay
            result2 = assistant.process(accumulated_text)
            
            status = assistant.get_status()
            results.append({
                'input': text_input,
                'result1': result1,
                'result2': result2,
                'status': status
            })
            
            print(f"    Result1: '{result1}', Result2: '{result2}'")
            print(f"    Status: {status}")
        
        print(f"  Final mode: {assistant.get_mode()}")
        print("-" * 30)

def reset_assistant():
    """Reset assistant to clean state"""
    assistant = VoiceAssistant()
    assistant.set_mode("normal")
    assistant.update_cursor(0)
    assistant.update_typing_cursor(0)
    assistant.recognized_text_buffer = ""
    print("Assistant reset to normal mode with clean state.")

def interactive_test():
    """Interactive testing mode"""
    assistant = VoiceAssistant()
    
    print("Interactive Voice Assistant Test")
    print("Commands:")
    print("  Type text to simulate speech input")
    print("  'reset' - Reset assistant state")
    print("  'status' - Show current status")
    print("  'quit' - Exit")
    print("-" * 40)
    
    accumulated_text = ""
    
    while True:
        try:
            user_input = input("\nSimulate speech: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'reset':
                assistant.set_mode("normal")
                assistant.update_cursor(0)
                assistant.update_typing_cursor(0)
                assistant.recognized_text_buffer = ""
                accumulated_text = ""
                print("Assistant reset.")
                continue
            elif user_input.lower() == 'status':
                status = assistant.get_status()
                print(f"Status: {status}")
                continue
            
            if user_input:
                # Add to accumulated text (simulating nerd-dictation behavior)
                if accumulated_text:
                    accumulated_text += " " + user_input
                else:
                    accumulated_text = user_input
                
                print(f"Processing: '{accumulated_text}'")
                
                # Process twice to simulate nerd-dictation behavior
                result1 = assistant.process(accumulated_text)
                time.sleep(0.1)
                result2 = assistant.process(accumulated_text)
                
                status = assistant.get_status()
                
                print(f"Result1: '{result1}', Result2: '{result2}'")
                print(f"Mode: {status['mode']}, Cursor: {status['cursor']}, Buffer: {status['buffer_length']}")
                
                # If we got output, it might be typing
                if result2:
                    print(f"TYPED: '{result2}'")
        
        except KeyboardInterrupt:
            break
    
    print("\nInteractive test ended.")

def show_status():
    """Show current assistant status"""
    assistant = VoiceAssistant()
    status = assistant.get_status()
    
    print("Current Assistant Status:")
    print("-" * 25)
    for key, value in status.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 debug_tool.py [monitor|test|reset|status|interactive]")
        print("\nCommands:")
        print("  monitor     - Real-time status monitoring")
        print("  test        - Test command scenarios")
        print("  interactive - Interactive testing mode")
        print("  reset       - Reset assistant to clean state")
        print("  status      - Show current status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "monitor":
        monitor_assistant()
    elif command == "test":
        test_commands()
    elif command == "interactive":
        interactive_test()
    elif command == "reset":
        reset_assistant()
    elif command == "status":
        show_status()
    else:
        print(f"Unknown command: {command}")
