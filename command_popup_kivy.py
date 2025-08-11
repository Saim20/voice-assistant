#!/usr/bin/env python3
"""
Modern Kivy Command Popup for Voice Assistant
Shows when entering command mode with real-time buffer display
"""
import os
import sys
import threading
import time
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget

class GlassmorphicWidget(Widget):
    """Custom widget with glassmorphic effect"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Glassmorphic background with blur effect - make more visible
            Color(0.1, 0.1, 0.2, 0.95)  # More opaque dark background
            RoundedRectangle(pos=self.pos, size=self.size, radius=[25])
            
            # Border effect
            Color(0.3, 0.5, 0.9, 0.6)  # More visible blue border
            RoundedRectangle(pos=(self.pos[0] + 2, self.pos[1] + 2), 
                           size=(self.size[0] - 4, self.size[1] - 4), 
                           radius=[23])

class CommandPopup(BoxLayout):
    """Modern command popup with glassmorphic design"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 15
        self.padding = [25, 25, 25, 25]
        
        # Bind to ensure background updates with window
        self.bind(pos=self.update_background, size=self.update_background)
        
        # Create content
        self.create_content()
        
        # Start monitoring
        self.buffer_file = Path("/tmp/nerd-dictation.buffer")
        self.mode_file = Path("/tmp/nerd-dictation.mode")
        self.monitoring = True
        self.startup_time = time.time()  # Track when popup started
        self.min_display_time = 3.0  # Minimum time to keep popup open (seconds)
        self.max_display_time = 30.0  # Maximum time to keep popup open (seconds)
        
        # Schedule updates
        Clock.schedule_interval(self.update_buffer, 0.2)
        Clock.schedule_interval(self.check_mode, 1.0)  # Check less frequently
        # Clock.schedule_once(self.auto_close_timeout, self.max_display_time)  # Auto-close after max time
    
    def update_background(self, *args):
        """Update glassmorphic background"""
        self.canvas.before.clear()
        with self.canvas.before:
            # Glassmorphic background with blur effect - make more visible
            Color(0.1, 0.1, 0.2, 0.95)  # More opaque dark background
            RoundedRectangle(pos=self.pos, size=self.size, radius=[25])
            
            # Border effect
            Color(0.3, 0.5, 0.9, 0.6)  # More visible blue border
            RoundedRectangle(pos=(self.pos[0] + 2, self.pos[1] + 2), 
                           size=(self.size[0] - 4, self.size[1] - 4), 
                           radius=[23])
    
    def create_content(self):
        """Create the popup content"""
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        
        # Status indicator
        self.status_indicator = Label(
            text='COMMAND MODE',
            font_size='24sp',
            color=get_color_from_hex('#00D4FF'),
            bold=True,
            size_hint_x=0.7
        )
        header.add_widget(self.status_indicator)
        
        # Close button
        close_btn = Button(
            text='X',
            size_hint=(None, None),
            size=(40, 40),
            background_color=get_color_from_hex('#FF4757'),
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True
        )
        close_btn.bind(on_press=self.close_popup)
        header.add_widget(close_btn)
        
        self.add_widget(header)
        
        # Buffer display
        buffer_header = Label(
            text='Voice Buffer:',
            font_size='16sp',
            color=get_color_from_hex('#A0A0A0'),
            size_hint_y=None,
            height=30,
            halign='left'
        )
        buffer_header.bind(size=buffer_header.setter('text_size'))
        self.add_widget(buffer_header)
        
        self.buffer_display = Label(
            text='Listening...',
            font_size='18sp',
            color=get_color_from_hex('#FFFFFF'),
            markup=True,
            halign='left',
            valign='top',
            text_size=(None, None)
        )
        self.buffer_display.bind(size=self.buffer_display.setter('text_size'))
        self.add_widget(self.buffer_display)
        
        # Available commands hint
        commands_hint = Label(
            text='Say commands like: "open terminal", "typing mode", "cancel"',
            font_size='14sp',
            color=get_color_from_hex('#70A0B0'),
            size_hint_y=None,
            height=40,
            halign='center'
        )
        commands_hint.bind(size=commands_hint.setter('text_size'))
        self.add_widget(commands_hint)
        
        # Mode buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        # Typing mode button
        typing_btn = Button(
            text='Typing Mode',
            background_color=get_color_from_hex('#2ECC71'),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        typing_btn.bind(on_press=self.switch_to_typing)
        button_layout.add_widget(typing_btn)
        
        # Normal mode button
        normal_btn = Button(
            text='Normal Mode',
            background_color=get_color_from_hex('#3498DB'),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        normal_btn.bind(on_press=self.switch_to_normal)
        button_layout.add_widget(normal_btn)
        
        self.add_widget(button_layout)
    
    def update_buffer(self, dt):
        """Update buffer display from file"""
        try:
            if self.buffer_file.exists():
                with open(self.buffer_file, 'r') as f:
                    buffer_text = f.read().strip()
                
                if buffer_text:
                    # Highlight keywords
                    highlighted_text = self.highlight_keywords(buffer_text)
                    self.buffer_display.text = highlighted_text
                else:
                    self.buffer_display.text = 'Listening...'
            else:
                self.buffer_display.text = 'Listening...'
        except Exception as e:
            print(f"Error reading buffer: {e}")
    
    def highlight_keywords(self, text):
        """Highlight important keywords in the buffer text"""
        keywords = {
            'terminal': '#00D4FF',
            'firefox': '#FF6B35',
            'typing': '#2ECC71',
            'normal': '#3498DB',
            'cancel': '#FF4757',
            'stop': '#FF4757',
            'volume': '#9B59B6',
            'window': '#F39C12'
        }
        
        highlighted = text
        for keyword, color in keywords.items():
            if keyword in text.lower():
                highlighted = highlighted.replace(
                    keyword, 
                    f'[color={color}]{keyword}[/color]'
                )
        
        return highlighted
    
    def check_mode(self, dt):
        """Check if still in command mode, but with minimum display time"""
        try:
            # Don't close too quickly - give user time to see and interact
            time_since_startup = time.time() - self.startup_time
            if time_since_startup < self.min_display_time:
                return  # Keep popup open for minimum time
            
            # After minimum time, check if we should close
            if self.mode_file.exists():
                with open(self.mode_file, 'r') as f:
                    current_mode = f.read().strip()
                
                # Only close if mode has been changed away from command for a while
                if current_mode not in ["command", "typing"]:
                    print(f"Mode is {current_mode}, closing popup after {time_since_startup:.1f}s")
                    self.close_popup()
        except Exception as e:
            print(f"Error checking mode: {e}")
    
    def auto_close_timeout(self, dt):
        """Auto-close popup after maximum display time"""
        print("Auto-closing popup after timeout")
        self.close_popup()
    
    def switch_to_typing(self, instance):
        """Switch to typing mode"""
        try:
            with open(self.mode_file, 'w') as f:
                f.write("typing")
            self.close_popup()
        except Exception as e:
            print(f"Error switching to typing mode: {e}")
    
    def switch_to_normal(self, instance):
        """Switch to normal mode"""
        try:
            with open(self.mode_file, 'w') as f:
                f.write("normal")
            self.close_popup()
        except Exception as e:
            print(f"Error switching to normal mode: {e}")
    
    def close_popup(self, instance=None):
        """Close the popup"""
        self.monitoring = False
        App.get_running_app().stop()

class CommandPopupApp(App):
    """Kivy app for command popup"""
    
    def build(self):
        # Configure window for upper right corner positioning
        Window.size = (450, 280)
        
        # Window styling - make sure window is visible and interactive
        Window.borderless = False  # Keep border for better interaction
        Window.resizable = False
        Window.clearcolor = (0.02, 0.02, 0.05, 1.0)  # Dark but not transparent background
        
        # Set window title for identification
        Window.title = "Voice Command Popup"
        
        return CommandPopup()
    
    def on_start(self):
        """Called when app starts - position window after it's created"""
        print("Command popup started")
        
        # Schedule window positioning after a short delay to ensure window is ready
        Clock.schedule_once(self.position_window, 0.1)
    
    def position_window(self, dt):
        """Position window in upper right corner"""
        try:
            # Get screen dimensions
            import subprocess
            
            # Try to get screen size using xrandr
            try:
                result = subprocess.run(['xrandr'], capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ' connected primary ' in line or ' connected ' in line:
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and '+' in part:
                                    resolution = part.split('+')[0]
                                    if 'x' in resolution:
                                        width, height = map(int, resolution.split('x'))
                                        print(f"Detected screen size: {width}x{height}")
                                        self.set_window_position(width, height)
                                        return
            except FileNotFoundError:
                pass
            
            # Fallback: Use Kivy's system size
            screen_width = Window.system_size[0] if Window.system_size[0] > 0 else 1920
            screen_height = Window.system_size[1] if Window.system_size[1] > 0 else 1080
            print(f"Using fallback screen size: {screen_width}x{screen_height}")
            self.set_window_position(screen_width, screen_height)
            
        except Exception as e:
            print(f"Error positioning window: {e}")
            # Final fallback
            self.set_window_position(1920, 1080)
    
    def set_window_position(self, screen_width, screen_height):
        """Set window position in upper right corner"""
        margin = 20
        x_pos = screen_width - Window.size[0] - margin
        y_pos = margin  # Position at top, not bottom
        
        print(f"Setting window position to: x={x_pos}, y={y_pos}")
        print(f"Window size: {Window.size}")
        print(f"Screen size: {screen_width}x{screen_height}")
        
        # Set position
        Window.left = x_pos
        Window.top = y_pos
    
    def make_window_sticky(self, dt):
        """Make window visible on all desktops - simplified version"""
        try:
            import subprocess
            
            # Simple approach - just try xprop without complex window management
            try:
                subprocess.run(['xprop', '-f', '_NET_WM_DESKTOP', '32c', '-set', 
                              '_NET_WM_DESKTOP', '0xffffffff'], 
                             capture_output=True, check=False, timeout=1)
                print("Window properties set using xprop")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                print("xprop not available or timed out")
                pass
                
        except Exception as e:
            print(f"Could not set window properties: {e}")
    
    def on_stop(self):
        """Called when app stops"""
        print("Command popup stopped")

if __name__ == '__main__':
    # Suppress Kivy debug output
    os.environ['KIVY_NO_CONSOLELOG'] = '1'
    
    try:
        CommandPopupApp().run()
    except Exception as e:
        print(f"Error running popup: {e}")
