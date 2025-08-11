#!/usr/bin/env python3
"""
Modern Command Mode Popup with glass morphism effects
"""

import tkinter as tk
import threading
import time

class ModernCommandPopup:
    """Modern borderless popup with glass morphism effects"""
    
    def __init__(self, parent, assistant, config):
        self.parent = parent
        self.assistant = assistant
        self.config = config
        self.popup = None
        self.monitoring = False
        self.drag_data = {"x": 0, "y": 0}
        
    def show_popup(self):
        """Show the modern popup with rounded corners and blur effects"""
        print("show_popup() called")
        if self.popup:
            print("Popup already exists, returning")
            return
            
        try:
            print("Creating popup window...")
            self.popup = tk.Toplevel(self.parent)
            self.popup.overrideredirect(True)
            self.popup.attributes('-topmost', True)
            
            # Set a solid background for now (no transparency)
            self.popup.configure(bg='#1e293b')
            
            print("Setting popup geometry...")
            # Geometry and positioning with margins
            width, height = 420, 300  # Slightly larger for better proportions
            self.popup.geometry(f"{width}x{height}")
            self.position_popup_with_margins(width, height)
            
            print("Creating popup content...")
            # Create modern content with rounded container
            self.create_rounded_content()
            
            print("Making popup draggable...")
            # Make draggable
            self.make_draggable()
            
            print("Starting monitoring...")
            # Start monitoring
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_mode, daemon=True)
            self.monitor_thread.start()
            
            # Make popup visible immediately for testing
            self.popup.attributes('-alpha', 1.0)
            print("Popup should now be visible!")
            
        except Exception as e:
            print(f"Error creating popup: {e}")
            import traceback
            traceback.print_exc()
    
    def position_popup_with_margins(self, width, height):
        """Position popup with margins from screen edges"""
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        
        # Margins from screen edges
        margin = 20
        
        # Position in top-right with margin
        x = screen_width - width - margin
        y = margin
        
        # Check config for position preference
        position = self.config.get("popup_position", "top_right")
        
        if position == "top_left":
            x = margin
            y = margin
        elif position == "bottom_right":
            x = screen_width - width - margin
            y = screen_height - height - margin
        elif position == "bottom_left":
            x = margin
            y = screen_height - height - margin
        elif position == "center":
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        # default is top_right
        
        self.popup.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_rounded_content(self):
        """Create rounded popup content with blur effects"""
        # Create main container with simple styling for now
        self.main_container = tk.Frame(
            self.popup,
            bg='#1e293b',
            relief='solid',
            bd=1
        )
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Header with close button - simplified
        header = tk.Frame(self.main_container, bg='#1e293b', height=50)
        header.pack(fill=tk.X, padx=15, pady=(15, 10))
        header.pack_propagate(False)
        
        # Title - using basic label
        title_label = tk.Label(
            header,
            text="⚡ COMMAND MODE",
            bg='#1e293b',
            fg='#f59e0b',
            font=('Arial', 14, 'bold')
        )
        title_label.pack(side=tk.LEFT, fill=tk.Y)
        
        # Close button - using basic button
        close_btn = tk.Button(
            header,
            text="✕",
            bg='#ef4444',
            fg='white',
            font=('Arial', 12, 'bold'),
            command=self.close_popup,
            relief='flat',
            padx=10,
            pady=5
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Content area - simplified
        content = tk.Frame(
            self.main_container,
            bg='#334155'
        )
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Quick commands section
        self.create_quick_commands(content)
        
        # Action buttons
        self.create_action_buttons(content)
    
    def create_quick_commands(self, parent):
        """Create quick command buttons - simplified"""
        # Section header
        header_label = tk.Label(
            parent,
            text="Quick Commands:",
            bg='#334155',
            fg='white',
            font=('Arial', 11, 'bold')
        )
        header_label.pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        # Commands grid
        grid_frame = tk.Frame(parent, bg='#334155')
        grid_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        quick_commands = [
            ("🖥️ Terminal", "open terminal"),
            ("🌐 Browser", "open firefox"),
            ("📁 Files", "open files"),
            ("📸 Screenshot", "screenshot"),
            ("🔊 Volume ↑", "volume up"),
            ("🔇 Mute", "mute")
        ]
        
        for i, (text, command) in enumerate(quick_commands):
            row, col = i // 2, i % 2
            
            btn = tk.Button(
                grid_frame,
                text=text,
                bg='#475569',
                fg='white',
                font=('Arial', 9),
                relief='flat',
                padx=10,
                pady=6,
                command=lambda cmd=command: self.execute_command(cmd)
            )
            btn.grid(row=row, column=col, padx=3, pady=2, sticky="ew")
        
        # Configure grid
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
    
    def create_action_buttons(self, parent):
        """Create main action buttons - simplified"""
        button_frame = tk.Frame(parent, bg='#334155')
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Typing mode button
        typing_btn = tk.Button(
            button_frame,
            text="✏️ Switch to Typing",
            bg='#3b82f6',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='flat',
            padx=10,
            pady=8,
            command=self.switch_to_typing
        )
        typing_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Normal mode button
        normal_btn = tk.Button(
            button_frame,
            text="🏠 Normal Mode",
            bg='#64748b',
            fg='white',
            font=('Arial', 10),
            relief='flat',
            padx=10,
            pady=8,
            command=self.switch_to_normal
        )
        normal_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    def make_draggable(self):
        """Make popup draggable"""
        def start_drag(event):
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
        
        def do_drag(event):
            x = self.popup.winfo_x() + (event.x - self.drag_data["x"])
            y = self.popup.winfo_y() + (event.y - self.drag_data["y"])
            self.popup.geometry(f"+{x}+{y}")
        
        self.main_container.bind("<Button-1>", start_drag)
        self.main_container.bind("<B1-Motion>", do_drag)
    
    def position_popup(self, width, height):
        """Position popup on screen"""
        position = self.config.get('popup_position', 'top_right')
        
        screen_width = self.popup.winfo_screenwidth()
        screen_height = self.popup.winfo_screenheight()
        margin = 40
        
        positions = {
            'top_right': (screen_width - width - margin, margin),
            'top_left': (margin, margin),
            'bottom_right': (screen_width - width - margin, screen_height - height - margin - 60),
            'bottom_left': (margin, screen_height - height - margin - 60),
            'center': ((screen_width - width) // 2, (screen_height - height) // 2)
        }
        
        x, y = positions.get(position, positions['top_right'])
        self.popup.geometry(f"{width}x{height}+{x}+{y}")
    
    def fade_in(self):
        """Fade in animation"""
        def animate(alpha=0.0):
            if alpha < 0.95:
                try:
                    self.popup.attributes('-alpha', alpha)
                    self.popup.after(20, lambda: animate(alpha + 0.05))
                except:
                    pass
        
        try:
            self.popup.attributes('-alpha', 0.0)
            animate()
        except:
            pass
    
    def fade_out(self, callback=None):
        """Fade out animation"""
        def animate(alpha=0.95):
            if alpha > 0.0:
                try:
                    self.popup.attributes('-alpha', alpha)
                    self.popup.after(20, lambda: animate(alpha - 0.05))
                except:
                    if callback:
                        callback()
            else:
                if callback:
                    callback()
        
        try:
            animate()
        except:
            if callback:
                callback()
    
    def execute_command(self, command):
        """Execute a quick command"""
        self.assistant.process_command_mode(command)
        self.close_popup()
    
    def switch_to_typing(self):
        """Switch to typing mode"""
        self.assistant.set_mode("typing")
        self.close_popup()
    
    def switch_to_normal(self):
        """Switch to normal mode"""
        self.assistant.set_mode("normal")
        self.close_popup()
    
    def monitor_mode(self):
        """Monitor mode changes"""
        while self.monitoring:
            try:
                current_mode = self.assistant.get_mode()
                if current_mode != "command":
                    self.popup.after(0, self.close_popup)
                    break
                time.sleep(0.5)
            except Exception as e:
                print(f"Popup monitoring error: {e}")
                break
    
    def close_popup(self):
        """Close popup with fade out"""
        self.monitoring = False
        
        def destroy_popup():
            if self.popup:
                self.popup.destroy()
                self.popup = None
        
        self.fade_out(destroy_popup)


if __name__ == "__main__":
    """Run popup standalone for voice assistant integration"""
    import sys
    import os
    from pathlib import Path
    
    # Add current directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from voice_assistant_improved import VoiceAssistant
        
        # Create root window (hidden)
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Create assistant and config
        assistant = VoiceAssistant()
        config = {
            "popup_enabled": True,
            "popup_position": "top_right",
            "popup_geometry": "420x300"
        }
        
        # Create and show popup
        popup = ModernCommandPopup(root, assistant, config)
        popup.show_popup()
        
        # Auto-close after 5 seconds if no interaction
        def auto_close():
            time.sleep(5)
            if popup.popup:
                popup.close_popup()
        
        threading.Thread(target=auto_close, daemon=True).start()
        
        # Run main loop
        root.mainloop()
        
    except Exception as e:
        print(f"Error running standalone popup: {e}")
        sys.exit(1)
