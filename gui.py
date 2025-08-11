#!/usr/bin/env python3
"""
Modern Voice Assistant GUI - Clean, Modular Design
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, colorchooser, filedialog
import threading
import time
import json
import logging
from pathlib import Path
from voice_assistant_improved import VoiceAssistant
from modern_popup import ModernCommandPopup
from ui_components import ModernStyles, ModernFrame, ModernButton, ModernLabel, ModernEntry

class VoiceAssistantGUI:
    """Modern Voice Assistant GUI with clean, modular design"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant - Modern Edition")
        self.root.geometry("1200x800")
        self.root.configure(bg=ModernStyles.COLORS['bg_primary'])
        
        # Load configuration
        self.config = self.load_config()
        
        # Apply modern theme
        ModernStyles.apply_modern_theme(self.root)
        
        # Initialize assistant
        config_dir = "/tmp"  # Use same directory as nerd-dictation
        self.assistant = VoiceAssistant(config_dir=config_dir)
        
        # Create modern popup
        self.command_popup = ModernCommandPopup(self.root, self.assistant, self.config)
        
        # Create GUI
        self.create_modern_gui()
        
        # Start monitoring
        self.monitoring = True
        self.last_mode = "normal"
        self.monitor_thread = threading.Thread(target=self.monitor_assistant, daemon=True)
        self.monitor_thread.start()
    
    def load_config(self):
        """Load GUI configuration"""
        config_file = Path.home() / ".config" / "nerd-dictation" / "gui_config.json"
        default_config = {
            "popup_enabled": True,
            "popup_position": "top_right",
            "popup_geometry": "400x280"
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            print(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save GUI configuration"""
        config_file = Path.home() / ".config" / "nerd-dictation" / "gui_config.json"
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def create_modern_gui(self):
        """Create the modern GUI layout"""
        # Main notebook with modern styling
        self.notebook = ttk.Notebook(self.root, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create tabs
        self.create_status_tab()
        self.create_commands_tab()
        self.create_settings_tab()
    
    def create_status_tab(self):
        """Create modern status tab"""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="📊 Status")
        
        # Header
        header = ModernFrame(status_frame, corner_radius=12)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ModernLabel(
            header,
            text="🎤 Voice Assistant Status",
            style='heading'
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        # Quick actions
        actions = tk.Frame(header, bg=ModernStyles.COLORS['bg_card'])
        actions.pack(side=tk.RIGHT, padx=20, pady=15)
        
        ModernButton(
            actions,
            text="🔄 Reset",
            style='warning',
            command=self.reset_assistant
        ).pack(side=tk.RIGHT, padx=5)
        
        ModernButton(
            actions,
            text="🔔 Test Popup",
            style='primary',
            command=self.test_popup
        ).pack(side=tk.RIGHT, padx=5)
        
        # Current mode display
        mode_card = ModernFrame(status_frame, corner_radius=12)
        mode_card.pack(fill=tk.X, padx=20, pady=10)
        
        mode_header = tk.Frame(mode_card, bg=ModernStyles.COLORS['bg_card'])
        mode_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        ModernLabel(
            mode_header,
            text="Current Mode",
            style='subheading'
        ).pack(side=tk.LEFT)
        
        self.mode_label = ModernLabel(
            mode_header,
            text="NORMAL",
            style='subheading'
        )
        self.mode_label.pack(side=tk.RIGHT)
        
        # Mode buttons
        button_frame = tk.Frame(mode_card, bg=ModernStyles.COLORS['bg_card'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        modes = [
            ("Normal", "normal", "success"),
            ("Command", "command", "warning"),
            ("Typing", "typing", "primary")
        ]
        
        for mode_name, mode_value, style in modes:
            ModernButton(
                button_frame,
                text=mode_name,
                style=style,
                command=lambda m=mode_value: self.set_mode(m)
            ).pack(side=tk.LEFT, padx=5)
        
        # Statistics
        stats_frame = ModernFrame(status_frame, corner_radius=12)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ModernLabel(
            stats_frame,
            text="📈 Statistics",
            style='subheading'
        ).pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        stats_grid = tk.Frame(stats_frame, bg=ModernStyles.COLORS['bg_card'])
        stats_grid.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # Create stat displays
        self.create_stat_display(stats_grid, "Commands", "commands_stat", 0)
        self.create_stat_display(stats_grid, "Cursor", "cursor_stat", 1)
        self.create_stat_display(stats_grid, "Typing Cursor", "typing_cursor_stat", 2)
        
        # Test input
        test_card = ModernFrame(status_frame, corner_radius=12)
        test_card.pack(fill=tk.X, padx=20, pady=10)
        
        ModernLabel(
            test_card,
            text="🧪 Test Input",
            style='subheading'
        ).pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        test_input_frame = tk.Frame(test_card, bg=ModernStyles.COLORS['bg_card'])
        test_input_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.test_entry = ModernEntry(test_input_frame)
        self.test_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.test_entry.bind('<Return>', lambda e: self.process_test_input())
        
        ModernButton(
            test_input_frame,
            text="Process",
            command=self.process_test_input
        ).pack(side=tk.RIGHT)
        
        # Result display
        self.test_result = ModernLabel(
            test_card,
            text="Result will appear here...",
            style='muted'
        )
        self.test_result.pack(anchor=tk.W, padx=20, pady=(0, 15))
    
    def create_stat_display(self, parent, title, attr_name, column):
        """Create a statistic display"""
        stat_frame = tk.Frame(parent, bg=ModernStyles.COLORS['bg_secondary'])
        stat_frame.grid(row=0, column=column, padx=5, pady=5, sticky="ew")
        parent.grid_columnconfigure(column, weight=1)
        
        ModernLabel(
            stat_frame,
            text=title,
            style='caption',
            bg=ModernStyles.COLORS['bg_secondary']
        ).pack(pady=(10, 5))
        
        value_label = ModernLabel(
            stat_frame,
            text="0",
            style='subheading',
            bg=ModernStyles.COLORS['bg_secondary']
        )
        value_label.pack(pady=(0, 10))
        
        setattr(self, attr_name, value_label)
    
    def create_commands_tab(self):
        """Create modern commands management tab"""
        commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(commands_frame, text="🎯 Commands")
        
        # Header with actions
        header = ModernFrame(commands_frame, corner_radius=12)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        title_frame = tk.Frame(header, bg=ModernStyles.COLORS['bg_card'])
        title_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=15)
        
        ModernLabel(
            title_frame,
            text="🎯 Command Management",
            style='heading'
        ).pack(anchor=tk.W)
        
        ModernLabel(
            title_frame,
            text="Configure voice commands and actions",
            style='muted'
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Action buttons
        actions = tk.Frame(header, bg=ModernStyles.COLORS['bg_card'])
        actions.pack(side=tk.RIGHT, padx=20, pady=15)
        
        ModernButton(
            actions,
            text="➕ Add",
            style='primary',
            command=self.show_add_command_dialog
        ).pack(side=tk.RIGHT, padx=2)
        
        ModernButton(
            actions,
            text="✏️ Edit",
            style='warning',
            command=self.show_edit_command_dialog
        ).pack(side=tk.RIGHT, padx=2)
        
        ModernButton(
            actions,
            text="🗑️ Delete",
            style='error',
            command=self.delete_selected_command
        ).pack(side=tk.RIGHT, padx=2)
        
        # Search and filter
        filter_card = ModernFrame(commands_frame, corner_radius=12)
        filter_card.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        filter_frame = tk.Frame(filter_card, bg=ModernStyles.COLORS['bg_card'])
        filter_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ModernLabel(
            filter_frame,
            text="🔍",
            style='body'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_commands)
        
        search_entry = ModernEntry(filter_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        
        ModernLabel(
            filter_frame,
            text="Category:",
            style='body'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.category_filter = tk.StringVar(value="All")
        category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_filter,
            values=["All", "Application", "Window", "Text", "Volume", "System", "Mode", "Other"],
            state="readonly",
            width=12
        )
        category_combo.pack(side=tk.LEFT)
        category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_commands())
        
        # Commands table
        table_card = ModernFrame(commands_frame, corner_radius=12)
        table_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Treeview
        columns = ("Category", "Phrases", "Action", "Status")
        self.commands_tree = ttk.Treeview(
            table_card, 
            columns=columns, 
            show="headings",
            style="Modern.Treeview"
        )
        
        # Configure columns
        for col, text in zip(columns, ["📁 Category", "🗣️ Commands", "⚡ Action", "📊 Status"]):
            self.commands_tree.heading(col, text=text)
        
        self.commands_tree.column("Category", width=120)
        self.commands_tree.column("Phrases", width=350)
        self.commands_tree.column("Action", width=300)
        self.commands_tree.column("Status", width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.commands_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_card, orient=tk.HORIZONTAL, command=self.commands_tree.xview)
        self.commands_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack
        self.commands_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15)
        
        # Bind events
        self.commands_tree.bind("<Double-1>", lambda e: self.show_edit_command_dialog())
        
        # Populate
        self.populate_commands_tree()
    
    def create_settings_tab(self):
        """Create modern settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Create scrollable content
        canvas = tk.Canvas(settings_frame, bg=ModernStyles.COLORS['bg_primary'])
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=ModernStyles.COLORS['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Voice settings
        voice_card = ModernFrame(scrollable_frame, corner_radius=12)
        voice_card.pack(fill=tk.X, padx=20, pady=20)
        
        ModernLabel(
            voice_card,
            text="🎤 Voice Settings",
            style='subheading'
        ).pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        # Hotword setting
        hotword_frame = tk.Frame(voice_card, bg=ModernStyles.COLORS['bg_card'])
        hotword_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ModernLabel(
            hotword_frame,
            text="Activation Word:",
            style='body'
        ).pack(side=tk.LEFT, anchor='w', padx=(0, 10))
        
        self.hotword_var = tk.StringVar(value=self.assistant.hotword)
        hotword_entry = ModernEntry(hotword_frame, textvariable=self.hotword_var, width=15)
        hotword_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ModernButton(
            hotword_frame,
            text="Update",
            command=self.update_hotword
        ).pack(side=tk.LEFT)
        
        # Threshold setting
        threshold_frame = tk.Frame(voice_card, bg=ModernStyles.COLORS['bg_card'])
        threshold_frame.pack(fill=tk.X, padx=20, pady=(5, 15))
        
        ModernLabel(
            threshold_frame,
            text="Match Threshold:",
            style='body'
        ).pack(side=tk.LEFT, anchor='w', padx=(0, 10))
        
        self.threshold_var = tk.IntVar(value=self.assistant.fuzzy_match_threshold)
        threshold_scale = tk.Scale(
            threshold_frame,
            from_=50, to=100,
            variable=self.threshold_var,
            orient=tk.HORIZONTAL,
            bg=ModernStyles.COLORS['bg_card'],
            fg=ModernStyles.COLORS['text_primary'],
            length=200
        )
        threshold_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        ModernButton(
            threshold_frame,
            text="Update",
            command=self.update_threshold
        ).pack(side=tk.LEFT)
        
        # Popup settings
        popup_card = ModernFrame(scrollable_frame, corner_radius=12)
        popup_card.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        ModernLabel(
            popup_card,
            text="🔔 Popup Settings",
            style='subheading'
        ).pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        # Popup enabled
        popup_enabled_frame = tk.Frame(popup_card, bg=ModernStyles.COLORS['bg_card'])
        popup_enabled_frame.pack(fill=tk.X, padx=20, pady=(5, 15))
        
        self.popup_enabled_var = tk.BooleanVar(value=self.config.get("popup_enabled", True))
        
        tk.Checkbutton(
            popup_enabled_frame,
            text="Show popup when entering command mode",
            variable=self.popup_enabled_var,
            command=self.update_popup_settings,
            bg=ModernStyles.COLORS['bg_card'],
            fg=ModernStyles.COLORS['text_primary'],
            selectcolor=ModernStyles.COLORS['accent'],
            activebackground=ModernStyles.COLORS['bg_card'],
            activeforeground=ModernStyles.COLORS['text_primary']
        ).pack(side=tk.LEFT)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    # Command management methods
    def filter_commands(self, *args):
        """Filter commands based on search and category"""
        search_term = self.search_var.get().lower()
        category_filter = self.category_filter.get()
        
        # Clear current items
        for item in self.commands_tree.get_children():
            self.commands_tree.delete(item)
        
        # Categories for classification
        categories = {
            "Application": ["open", "launch", "start"],
            "Window": ["window", "desktop", "switch", "tab", "minimize", "maximize"],
            "Text": ["copy", "paste", "cut", "undo", "redo", "select"],
            "Volume": ["volume", "mute", "audio"],
            "System": ["lock", "screenshot", "sleep", "suspend"],
            "Mode": ["mode", "typing", "normal", "command"]
        }
        
        for phrases, action in self.assistant.commands.items():
            phrases_str = ", ".join(phrases)
            action_str = action if action else "Mode switch"
            status = "Active" if action else "System"
            
            # Determine category
            category = "Other"
            for cat, keywords in categories.items():
                if any(keyword in phrases_str.lower() for keyword in keywords):
                    category = cat
                    break
            
            # Apply filters
            search_match = (not search_term or 
                          search_term in phrases_str.lower() or 
                          search_term in action_str.lower() or
                          search_term in category.lower())
            
            category_match = (category_filter == "All" or category_filter == category)
            
            if search_match and category_match:
                self.commands_tree.insert("", tk.END, values=(category, phrases_str, action_str, status))
    
    def populate_commands_tree(self):
        """Populate the commands tree"""
        self.filter_commands()
    
    def show_add_command_dialog(self):
        """Show add command dialog"""
        self.show_command_dialog("Add Command", edit_mode=False)
    
    def show_edit_command_dialog(self):
        """Show edit command dialog"""
        selection = self.commands_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a command to edit.")
            return
        
        item = self.commands_tree.item(selection[0])
        values = item['values']
        
        if len(values) >= 3:
            phrases_str = values[1]
            action = values[2]
            self.show_command_dialog("Edit Command", edit_mode=True, 
                                   current_phrases=phrases_str, current_action=action)
    
    def show_command_dialog(self, title, edit_mode=False, current_phrases="", current_action=""):
        """Show command editing dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x400")
        dialog.configure(bg=ModernStyles.COLORS['bg_primary'])
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = ModernFrame(dialog, corner_radius=12)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ModernLabel(
            header,
            text=f"{'✏️' if edit_mode else '➕'} {title}",
            style='heading'
        ).pack(pady=15)
        
        # Form
        form = ModernFrame(dialog, corner_radius=12)
        form.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        # Phrases
        ModernLabel(
            form,
            text="🗣️ Voice Command Phrases",
            style='subheading'
        ).pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        phrases_text = scrolledtext.ScrolledText(
            form,
            height=6,
            font=ModernStyles.FONTS['body'],
            bg=ModernStyles.COLORS['bg_secondary'],
            fg=ModernStyles.COLORS['text_primary'],
            insertbackground=ModernStyles.COLORS['accent']
        )
        phrases_text.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        if edit_mode and current_phrases:
            phrases = current_phrases.split(", ")
            phrases_text.insert(tk.END, "\n".join(phrases))
        
        # Action
        ModernLabel(
            form,
            text="⚡ Command Action",
            style='subheading'
        ).pack(anchor=tk.W, padx=20, pady=(0, 5))
        
        action_entry = ModernEntry(form)
        action_entry.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        if edit_mode and current_action:
            action_entry.insert(0, current_action)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=ModernStyles.COLORS['bg_primary'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        def save_command():
            phrases_input = phrases_text.get("1.0", tk.END).strip()
            action_input = action_entry.get().strip()
            
            if not phrases_input:
                messagebox.showerror("Error", "Please enter at least one voice command phrase.")
                return
            
            try:
                phrases_list = [phrase.strip() for phrase in phrases_input.split('\n') if phrase.strip()]
                phrases_tuple = tuple(phrases_list)
                
                if edit_mode:
                    # Update existing command
                    old_phrases = tuple(current_phrases.split(", "))
                    self.assistant.update_command(old_phrases, phrases_tuple, action_input or None)
                else:
                    # Add new command
                    self.assistant.add_command(phrases_tuple, action_input or None)
                
                self.populate_commands_tree()
                dialog.destroy()
                messagebox.showinfo("Success", f"Command {'updated' if edit_mode else 'added'} successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save command: {e}")
                logging.error(f"Error saving command: {e}")
        
        ModernButton(
            button_frame,
            text=f"💾 {'Update' if edit_mode else 'Save'}",
            command=save_command
        ).pack(side=tk.RIGHT)
        
        ModernButton(
            button_frame,
            text="❌ Cancel",
            style='secondary',
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=(0, 10))
    
    def delete_selected_command(self):
        """Delete selected command"""
        selection = self.commands_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a command to delete.")
            return
        
        item = self.commands_tree.item(selection[0])
        phrases_str = item['values'][1]
        
        if messagebox.askyesno("Confirm Delete", f"Delete command:\n\n{phrases_str}"):
            try:
                phrases_tuple = tuple(phrases_str.split(", "))
                self.assistant.remove_command(phrases_tuple)
                self.populate_commands_tree()
                messagebox.showinfo("Success", "Command deleted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete command: {e}")
                logging.error(f"Error deleting command: {e}")
    
    # Event handlers
    def monitor_assistant(self):
        """Monitor assistant status"""
        while self.monitoring:
            try:
                status = self.assistant.get_status()
                current_mode = status["mode"]
                
                # Debug print
                print(f"Monitor: mode={current_mode}, last_mode={self.last_mode}, popup_enabled={self.config.get('popup_enabled', True)}, popup_exists={self.command_popup.popup is not None}")
                
                # Check for mode changes
                if current_mode != self.last_mode:
                    print(f"Mode changed from {self.last_mode} to {current_mode}")
                    self.last_mode = current_mode
                    
                    # Show popup when entering command mode
                    if (current_mode == "command" and 
                        self.config.get("popup_enabled", True)):
                        print("Triggering popup display...")
                        try:
                            self.root.after(0, self.command_popup.show_popup)
                        except Exception as e:
                            print(f"Error showing popup: {e}")
                
                # Update GUI
                self.root.after(0, self.update_status_display, status)
                time.sleep(0.5)
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
    
    def update_status_display(self, status):
        """Update status display elements"""
        mode = status["mode"].upper()
        colors = {
            "NORMAL": ModernStyles.COLORS['success'],
            "COMMAND": ModernStyles.COLORS['warning'],
            "TYPING": ModernStyles.COLORS['accent']
        }
        
        self.mode_label.config(text=mode, fg=colors.get(mode, ModernStyles.COLORS['text_primary']))
        self.cursor_stat.config(text=str(status['cursor']))
        self.typing_cursor_stat.config(text=str(status['typing_cursor']))
        self.commands_stat.config(text=str(status['commands_count']))
    
    def set_mode(self, mode):
        """Set assistant mode"""
        self.assistant.set_mode(mode)
    
    def test_popup(self):
        """Test popup display"""
        print("Test popup button clicked")
        try:
            self.command_popup.show_popup()
            print("Popup show_popup() called successfully")
        except Exception as e:
            print(f"Error showing popup: {e}")
            messagebox.showerror("Popup Error", f"Error showing popup: {e}")
    
    def reset_assistant(self):
        """Reset assistant"""
        self.assistant.set_mode("normal")
        self.assistant.update_cursor(0)
        self.assistant.update_typing_cursor(0)
        self.assistant.recognized_text_buffer = ""
        messagebox.showinfo("Reset", "Assistant reset to normal mode.")
    
    def process_test_input(self):
        """Process test input"""
        text = self.test_entry.get()
        if text:
            result = self.assistant.process(text)
            status = self.assistant.get_status()
            result_text = f"Input: '{text}' → Output: '{result}' → Mode: {status['mode']}"
            self.test_result.config(text=result_text)
            self.test_entry.delete(0, tk.END)
    
    def update_hotword(self):
        """Update hotword"""
        try:
            new_hotword = self.hotword_var.get()
            self.assistant.hotword = new_hotword
            self.assistant.config["hotword"] = new_hotword
            self.assistant.save_config(self.assistant.config)
            messagebox.showinfo("Updated", f"Hotword updated to: {new_hotword}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update hotword: {e}")
    
    def update_threshold(self):
        """Update threshold"""
        try:
            new_threshold = self.threshold_var.get()
            self.assistant.fuzzy_match_threshold = new_threshold
            self.assistant.config["fuzzy_match_threshold"] = new_threshold
            self.assistant.save_config(self.assistant.config)
            messagebox.showinfo("Updated", f"Threshold updated to: {new_threshold}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update threshold: {e}")
    
    def update_popup_settings(self):
        """Update popup settings"""
        self.config["popup_enabled"] = self.popup_enabled_var.get()
        self.save_config()
        messagebox.showinfo("Updated", "Popup settings updated.")
    
    def on_closing(self):
        """Handle window closing"""
        self.monitoring = False
        if self.command_popup.popup:
            self.command_popup.close_popup()
        self.root.destroy()

def main():
    """Run the modern GUI"""
    root = tk.Tk()
    app = VoiceAssistantGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
