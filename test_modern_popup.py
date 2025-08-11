#!/usr/bin/env python3
"""
Test the ModernCommandPopup directly
"""

import tkinter as tk
import sys
import os
sys.path.append('/home/saim/.config/nerd-dictation')

from modern_popup import ModernCommandPopup
from voice_assistant_improved import VoiceAssistant

def test_modern_popup():
    """Test the ModernCommandPopup directly"""
    root = tk.Tk()
    root.title("Popup Test")
    root.geometry("400x300")
    
    # Create assistant instance
    assistant = VoiceAssistant(config_dir="/tmp")
    
    # Create config for popup
    config = {
        "popup_enabled": True,
        "popup_position": "top_right",
        "popup_geometry": "400x280"
    }
    
    # Create popup instance
    popup = ModernCommandPopup(root, assistant, config)
    
    # Add test button
    test_btn = tk.Button(
        root, 
        text="Show Popup", 
        command=popup.show_popup,
        font=('Arial', 14),
        bg='#3b82f6',
        fg='white',
        padx=20,
        pady=10
    )
    test_btn.pack(expand=True)
    
    print("Modern popup test ready. Click 'Show Popup' button.")
    root.mainloop()

if __name__ == "__main__":
    test_modern_popup()
