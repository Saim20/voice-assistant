#!/usr/bin/env python3
"""
Simple popup test to verify the popup mechanism works
"""

import tkinter as tk
import sys

def test_simple_popup():
    """Test a very simple popup"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Create simple popup
    popup = tk.Toplevel(root)
    popup.title("Test Popup")
    popup.geometry("300x200+100+100")
    popup.configure(bg='#1e293b')
    popup.attributes('-topmost', True)
    
    # Add simple content
    label = tk.Label(
        popup, 
        text="COMMAND MODE\nPopup Test", 
        bg='#1e293b', 
        fg='white',
        font=('Arial', 14, 'bold')
    )
    label.pack(expand=True)
    
    # Close button
    close_btn = tk.Button(
        popup, 
        text="Close", 
        command=popup.destroy,
        bg='#ef4444',
        fg='white'
    )
    close_btn.pack(pady=10)
    
    print("Simple popup created and should be visible")
    
    # Auto close after 5 seconds
    popup.after(5000, popup.destroy)
    popup.after(5000, root.quit)
    
    root.mainloop()

if __name__ == "__main__":
    test_simple_popup()
