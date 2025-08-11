#!/usr/bin/env python3
"""
Modern UI Components for Voice Assistant
Provides reusable, styled components with modern effects
"""

import tkinter as tk
from tkinter import ttk
import math

class ModernStyles:
    """Modern styling configuration and utilities"""
    
    COLORS = {
        'bg_primary': '#0f172a',
        'bg_secondary': '#1e293b', 
        'bg_card': '#334155',
        'bg_surface': '#475569',
        'text_primary': '#f8fafc',
        'text_secondary': '#cbd5e1',
        'text_muted': '#94a3b8',
        'accent': '#3b82f6',
        'accent_hover': '#2563eb',
        'success': '#10b981',
        'warning': '#f59e0b',
        'error': '#ef4444',
        'border': '#475569',
        'shadow': '#000000'
    }
    
    FONTS = {
        'heading': ('Inter', 18, 'bold'),
        'subheading': ('Inter', 14, 'bold'),
        'body': ('Inter', 11),
        'caption': ('Inter', 9),
        'mono': ('JetBrains Mono', 10)
    }
    
    @staticmethod
    def apply_modern_theme(root):
        """Apply modern theme to the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure modern styles
        style.configure('Modern.TNotebook', 
                       background=ModernStyles.COLORS['bg_primary'],
                       borderwidth=0,
                       tabmargins=[0, 0, 0, 0])
        
        style.configure('Modern.TNotebook.Tab',
                       background=ModernStyles.COLORS['bg_secondary'],
                       foreground=ModernStyles.COLORS['text_primary'],
                       padding=[20, 12],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', ModernStyles.COLORS['bg_card']),
                           ('active', ModernStyles.COLORS['bg_surface'])])
        
        style.configure('Modern.Treeview',
                       background=ModernStyles.COLORS['bg_secondary'],
                       foreground=ModernStyles.COLORS['text_primary'],
                       fieldbackground=ModernStyles.COLORS['bg_secondary'],
                       borderwidth=0,
                       rowheight=32)
        
        style.configure('Modern.Treeview.Heading',
                       background=ModernStyles.COLORS['bg_card'],
                       foreground=ModernStyles.COLORS['text_primary'],
                       borderwidth=0,
                       font=ModernStyles.FONTS['body'])
        
        style.map('Modern.Treeview',
                 background=[('selected', ModernStyles.COLORS['accent'])])

class ModernFrame(tk.Frame):
    """Modern frame with rounded corners and shadow effect"""
    
    def __init__(self, parent, **kwargs):
        # Extract custom properties
        self.corner_radius = kwargs.pop('corner_radius', 8)
        self.shadow_color = kwargs.pop('shadow_color', ModernStyles.COLORS['shadow'])
        self.shadow_offset = kwargs.pop('shadow_offset', 2)
        
        # Set default styling
        kwargs.setdefault('bg', ModernStyles.COLORS['bg_card'])
        kwargs.setdefault('relief', tk.FLAT)
        kwargs.setdefault('bd', 0)
        
        super().__init__(parent, **kwargs)

class ModernButton(tk.Button):
    """Modern button with hover effects and styling"""
    
    def __init__(self, parent, style='primary', **kwargs):
        # Define button styles
        styles = {
            'primary': {
                'bg': ModernStyles.COLORS['accent'],
                'fg': ModernStyles.COLORS['text_primary'],
                'activebackground': ModernStyles.COLORS['accent_hover']
            },
            'secondary': {
                'bg': ModernStyles.COLORS['bg_card'],
                'fg': ModernStyles.COLORS['text_primary'],
                'activebackground': ModernStyles.COLORS['bg_surface']
            },
            'success': {
                'bg': ModernStyles.COLORS['success'],
                'fg': ModernStyles.COLORS['text_primary'],
                'activebackground': '#059669'
            },
            'warning': {
                'bg': ModernStyles.COLORS['warning'],
                'fg': ModernStyles.COLORS['text_primary'],
                'activebackground': '#d97706'
            },
            'error': {
                'bg': ModernStyles.COLORS['error'],
                'fg': ModernStyles.COLORS['text_primary'],
                'activebackground': '#dc2626'
            }
        }
        
        # Apply style
        button_style = styles.get(style, styles['primary'])
        kwargs.update(button_style)
        
        # Default properties
        kwargs.setdefault('font', ModernStyles.FONTS['body'])
        kwargs.setdefault('relief', tk.FLAT)
        kwargs.setdefault('bd', 0)
        kwargs.setdefault('padx', 20)
        kwargs.setdefault('pady', 10)
        kwargs.setdefault('cursor', 'hand2')
        
        super().__init__(parent, **kwargs)

class ModernEntry(tk.Entry):
    """Modern entry with better styling"""
    
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('font', ModernStyles.FONTS['body'])
        kwargs.setdefault('bg', ModernStyles.COLORS['bg_secondary'])
        kwargs.setdefault('fg', ModernStyles.COLORS['text_primary'])
        kwargs.setdefault('relief', tk.FLAT)
        kwargs.setdefault('bd', 1)
        kwargs.setdefault('insertbackground', ModernStyles.COLORS['accent'])
        kwargs.setdefault('selectbackground', ModernStyles.COLORS['accent'])
        
        super().__init__(parent, **kwargs)

class ModernLabel(tk.Label):
    """Modern label with typography"""
    
    def __init__(self, parent, style='body', **kwargs):
        # Typography styles
        typography = {
            'heading': {
                'font': ModernStyles.FONTS['heading'],
                'fg': ModernStyles.COLORS['text_primary']
            },
            'subheading': {
                'font': ModernStyles.FONTS['subheading'],
                'fg': ModernStyles.COLORS['text_primary']
            },
            'body': {
                'font': ModernStyles.FONTS['body'],
                'fg': ModernStyles.COLORS['text_primary']
            },
            'caption': {
                'font': ModernStyles.FONTS['caption'],
                'fg': ModernStyles.COLORS['text_secondary']
            },
            'muted': {
                'font': ModernStyles.FONTS['body'],
                'fg': ModernStyles.COLORS['text_muted']
            }
        }
        
        # Apply typography
        text_style = typography.get(style, typography['body'])
        kwargs.update(text_style)
        
        kwargs.setdefault('bg', ModernStyles.COLORS['bg_primary'])
        
        super().__init__(parent, **kwargs)

class GlassFrame(tk.Frame):
    """Glass morphism frame with blur effect simulation"""
    
    def __init__(self, parent, **kwargs):
        # Glass effect properties
        self.opacity = kwargs.pop('opacity', 0.9)
        self.blur_radius = kwargs.pop('blur_radius', 10)
        
        # Base styling for glass effect
        kwargs.setdefault('bg', '#1e293b')  # Semi-transparent base
        kwargs.setdefault('relief', tk.FLAT)
        kwargs.setdefault('bd', 1)
        
        super().__init__(parent, **kwargs)
        
        # Add subtle border for glass effect
        self.configure(highlightbackground=ModernStyles.COLORS['border'],
                      highlightthickness=1)

class ModernCard(ModernFrame):
    """Card component with modern styling"""
    
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('corner_radius', 12)
        kwargs.setdefault('padx', 20)
        kwargs.setdefault('pady', 15)
        
        super().__init__(parent, **kwargs)

class StatusDot(tk.Label):
    """Animated status dot indicator"""
    
    def __init__(self, parent, color=None, **kwargs):
        self.color = color or ModernStyles.COLORS['success']
        self.animation_state = 0
        
        kwargs.setdefault('text', '●')
        kwargs.setdefault('font', ('Inter', 16))
        kwargs.setdefault('fg', self.color)
        kwargs.setdefault('bg', ModernStyles.COLORS['bg_primary'])
        
        super().__init__(parent, **kwargs)
        
        # Start pulsing animation
        self.start_pulse()
    
    def start_pulse(self):
        """Start pulsing animation"""
        def pulse():
            # Create pulsing effect by varying opacity
            colors = [self.color, '#' + ''.join([
                format(max(0, min(255, int(self.color[i:i+2], 16) + 20)), '02x')
                for i in [1, 3, 5]
            ])]
            
            self.config(fg=colors[self.animation_state])
            self.animation_state = 1 - self.animation_state
            
            self.after(1000, pulse)  # Pulse every second
        
        pulse()

class ModernProgressBar(tk.Frame):
    """Modern progress bar with smooth animations"""
    
    def __init__(self, parent, **kwargs):
        self.progress_value = kwargs.pop('value', 0)
        self.max_value = kwargs.pop('maximum', 100)
        
        kwargs.setdefault('bg', ModernStyles.COLORS['bg_secondary'])
        kwargs.setdefault('height', 8)
        kwargs.setdefault('relief', tk.FLAT)
        
        super().__init__(parent, **kwargs)
        
        # Progress fill
        self.fill = tk.Frame(
            self,
            bg=ModernStyles.COLORS['accent'],
            height=8
        )
        
        self.update_progress()
    
    def set_value(self, value):
        """Update progress value"""
        self.progress_value = max(0, min(self.max_value, value))
        self.update_progress()
    
    def update_progress(self):
        """Update visual progress"""
        width = self.winfo_width()
        if width > 1:
            fill_width = int((self.progress_value / self.max_value) * width)
            self.fill.place(x=0, y=0, width=fill_width, height=8)

class TooltipManager:
    """Tooltip manager for modern UI components"""
    
    @staticmethod
    def add_tooltip(widget, text):
        """Add tooltip to widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.configure(bg=ModernStyles.COLORS['bg_card'])
            
            label = ModernLabel(
                tooltip,
                text=text,
                style='caption',
                bg=ModernStyles.COLORS['bg_card'],
                padx=8,
                pady=4
            )
            label.pack()
            
            # Position tooltip
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() - 30
            tooltip.geometry(f"+{x}+{y}")
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)


class RoundedBlurFrame(tk.Frame):
    """Advanced frame with rounded corners and blur effect simulation"""
    
    def __init__(self, parent, corner_radius=12, bg_color='#1e293b', opacity=0.9, blur_radius=8, **kwargs):
        self.corner_radius = corner_radius
        self.bg_color = bg_color
        self.opacity = opacity
        self.blur_radius = blur_radius
        
        # Create frame with transparent background
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bd', 0)
        kwargs.setdefault('relief', 'flat')
        
        super().__init__(parent, **kwargs)
        
        # Bind to configure events to redraw when resized
        self.bind('<Configure>', self._on_configure)
        self.after(1, self._create_rounded_background)
    
    def _on_configure(self, event=None):
        """Handle resize events"""
        if event and event.widget == self:
            self.after_idle(self._create_rounded_background)
    
    def _create_rounded_background(self):
        """Create rounded corner background with blur simulation"""
        try:
            import tkinter as tk
            from tkinter import Canvas
            
            # Get current dimensions
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            
            if width <= 1 or height <= 1:
                self.after(10, self._create_rounded_background)
                return
            
            # Remove existing canvas if any
            for child in self.winfo_children():
                if isinstance(child, Canvas) and hasattr(child, '_is_background'):
                    child.destroy()
            
            # Create background canvas
            canvas = Canvas(
                self,
                width=width,
                height=height,
                highlightthickness=0,
                bd=0
            )
            canvas._is_background = True
            canvas.place(x=0, y=0)
            
            # Create rounded rectangle with gradient effect for blur simulation
            self._draw_rounded_rectangle(canvas, width, height)
            
            # Lower canvas so content appears on top
            canvas.lower()
            
        except Exception as e:
            # Fallback to simple colored background
            self.configure(bg=self.bg_color)
    
    def _draw_rounded_rectangle(self, canvas, width, height):
        """Draw rounded rectangle with blur simulation"""
        r = self.corner_radius
        
        # Create gradient colors for blur effect
        base_color = self.bg_color
        if base_color.startswith('#'):
            # Convert hex to RGB
            rgb = tuple(int(base_color[i:i+2], 16) for i in (1, 3, 5))
        else:
            rgb = (30, 41, 59)  # Default dark blue
        
        # Create multiple layers for blur effect
        for i in range(self.blur_radius):
            alpha = 0.1 + (i / self.blur_radius) * (self.opacity - 0.1)
            offset = self.blur_radius - i
            
            # Create color with varying darkness for layered effect
            factor = 1.0 + (i * 0.05)
            layer_rgb = tuple(min(255, int(c * factor)) for c in rgb)
            layer_color = f"#{layer_rgb[0]:02x}{layer_rgb[1]:02x}{layer_rgb[2]:02x}"
            
            # Draw rounded rectangle layer
            self._draw_rounded_rect_layer(
                canvas, 
                offset, 
                offset, 
                width - offset, 
                height - offset, 
                r - offset//2, 
                layer_color
            )
        
        # Draw main rounded rectangle
        self._draw_rounded_rect_layer(canvas, 0, 0, width, height, r, base_color)
    
    def _draw_rounded_rect_layer(self, canvas, x1, y1, x2, y2, radius, color):
        """Draw a single rounded rectangle layer"""
        if radius > (x2 - x1) // 2:
            radius = (x2 - x1) // 2
        if radius > (y2 - y1) // 2:
            radius = (y2 - y1) // 2
        
        if radius <= 0:
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
            return
        
        # Draw rounded rectangle using multiple shapes
        # Main rectangle (middle)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=color, outline=color)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=color, outline=color)
        
        # Corner circles
        canvas.create_oval(x1, y1, x1 + 2*radius, y1 + 2*radius, fill=color, outline=color)
        canvas.create_oval(x2 - 2*radius, y1, x2, y1 + 2*radius, fill=color, outline=color)
        canvas.create_oval(x1, y2 - 2*radius, x1 + 2*radius, y2, fill=color, outline=color)
        canvas.create_oval(x2 - 2*radius, y2 - 2*radius, x2, y2, fill=color, outline=color)


class BlurredFrame(tk.Frame):
    """Simplified blurred frame for better compatibility"""
    
    def __init__(self, parent, bg_color='#1e293b', corner_radius=12, **kwargs):
        # Set default styling
        kwargs.setdefault('bg', bg_color)
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('bd', 0)
        kwargs.setdefault('relief', 'flat')
        
        super().__init__(parent, **kwargs)
        
        # Add subtle border effect
        self.configure(highlightbackground='#374151', highlightcolor='#374151', highlightthickness=1)
