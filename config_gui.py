#!/usr/bin/env python3
"""
Modern Kivy Configuration GUI for Voice Assistant
Allows editing of config.json and commands_config.json
"""
import os
import json
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.widget import Widget
from kivy.uix.spinner import Spinner

class ModernCard(BoxLayout):
    """Modern card widget with rounded corners and shadow effect"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [20, 20, 20, 20]
        self.spacing = 10
        
        with self.canvas.before:
            # Main card background
            Color(0.12, 0.12, 0.18, 0.95)  # Dark card background
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
            
            # Subtle border effect
            Color(0.2, 0.4, 0.8, 0.2)  # Blue accent border
            self.border_rect = RoundedRectangle(
                pos=(self.pos[0] + 1, self.pos[1] + 1), 
                size=(self.size[0] - 2, self.size[1] - 2), 
                radius=[14]
            )
        
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border_rect.pos = (self.pos[0] + 1, self.pos[1] + 1)
        self.border_rect.size = (self.size[0] - 2, self.size[1] - 2)

class ConfigEditor(BoxLayout):
    """Main configuration editor"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 20
        self.padding = [30, 30, 30, 30]
        
        # Configuration file paths
        self.config_dir = Path.home() / ".config" / "nerd-dictation"
        self.config_file = self.config_dir / "config.json"
        self.commands_config_file = self.config_dir / "commands_config.json"
        
        # Load configurations
        self.config_data = self.load_config(self.config_file)
        self.commands_data = self.load_config(self.commands_config_file)
        
        self.create_ui()
    
    def load_config(self, file_path):
        """Load configuration from JSON file"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}
    
    def save_config(self, file_path, data):
        """Save configuration to JSON file"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {file_path}: {e}")
            return False
    
    def create_ui(self):
        """Create the user interface"""
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)
        
        title = Label(
            text='Voice Assistant Configuration',
            font_size='28sp',
            color=get_color_from_hex('#00D4FF'),
            bold=True,
            size_hint_x=0.8
        )
        header.add_widget(title)
        
        # Save all button
        save_all_btn = Button(
            text='Save All',
            size_hint=(None, None),
            size=(120, 50),
            background_color=get_color_from_hex('#2ECC71'),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        save_all_btn.bind(on_press=self.save_all_configs)
        header.add_widget(save_all_btn)
        
        self.add_widget(header)
        
        # Tabbed interface
        self.tab_panel = TabbedPanel(do_default_tab=False)
        
        # Basic Settings Tab
        self.create_basic_settings_tab()
        
        # Commands Tab
        self.create_commands_tab()
        
        # Advanced Settings Tab
        self.create_advanced_settings_tab()
        
        self.add_widget(self.tab_panel)
    
    def create_basic_settings_tab(self):
        """Create basic settings tab"""
        tab = TabbedPanelItem(text='Basic Settings')
        
        content = ScrollView()
        layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=None, padding=[20, 20])
        layout.bind(minimum_height=layout.setter('height'))
        
        # Hotword setting
        hotword_card = ModernCard(size_hint_y=None, height=150)
        hotword_card.add_widget(Label(
            text='Activation Hotword',
            font_size='20sp',
            color=get_color_from_hex('#FFFFFF'),
            size_hint_y=None,
            height=40,
            bold=True
        ))
        
        hotword_desc = Label(
            text='The word that triggers command mode',
            font_size='14sp',
            color=get_color_from_hex('#A0A0A0'),
            size_hint_y=None,
            height=30
        )
        hotword_card.add_widget(hotword_desc)
        
        self.hotword_input = TextInput(
            text=self.config_data.get('hotword', 'hey'),
            multiline=False,
            size_hint_y=None,
            height=40,
            background_color=get_color_from_hex('#2A2A30'),
            foreground_color=get_color_from_hex('#FFFFFF'),
            font_size='16sp'
        )
        hotword_card.add_widget(self.hotword_input)
        layout.add_widget(hotword_card)
        
        # Fuzzy match threshold
        threshold_card = ModernCard(size_hint_y=None, height=180)
        threshold_card.add_widget(Label(
            text='Match Threshold',
            font_size='20sp',
            color=get_color_from_hex('#FFFFFF'),
            size_hint_y=None,
            height=40,
            bold=True
        ))
        
        threshold_desc = Label(
            text='How closely voice commands must match (50-100)',
            font_size='14sp',
            color=get_color_from_hex('#A0A0A0'),
            size_hint_y=None,
            height=30
        )
        threshold_card.add_widget(threshold_desc)
        
        self.threshold_input = TextInput(
            text=str(self.config_data.get('fuzzy_match_threshold', 85)),
            multiline=False,
            size_hint_y=None,
            height=40,
            input_filter='int',
            background_color=get_color_from_hex('#2A2A30'),
            foreground_color=get_color_from_hex('#FFFFFF'),
            font_size='16sp'
        )
        threshold_card.add_widget(self.threshold_input)
        
        # Test button
        test_btn = Button(
            text='Test Settings',
            size_hint_y=None,
            height=40,
            background_color=get_color_from_hex('#3498DB'),
            color=(1, 1, 1, 1)
        )
        test_btn.bind(on_press=self.test_settings)
        threshold_card.add_widget(test_btn)
        layout.add_widget(threshold_card)
        
        content.add_widget(layout)
        tab.content = content
        self.tab_panel.add_widget(tab)
    
    def create_commands_tab(self):
        """Create commands management tab"""
        tab = TabbedPanelItem(text='Commands')
        
        main_layout = BoxLayout(orientation='vertical', spacing=15, padding=[20, 20])
        
        # Header with add button
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        header.add_widget(Label(
            text='Voice Commands',
            font_size='24sp',
            color=get_color_from_hex('#00D4FF'),
            bold=True,
            size_hint_x=0.7
        ))
        
        add_btn = Button(
            text='Add Command',
            size_hint=(None, None),
            size=(150, 50),
            background_color=get_color_from_hex('#2ECC71'),
            color=(1, 1, 1, 1)
        )
        add_btn.bind(on_press=self.show_add_command_dialog)
        header.add_widget(add_btn)
        main_layout.add_widget(header)
        
        # Commands list
        self.commands_scroll = ScrollView()
        self.commands_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.commands_layout.bind(minimum_height=self.commands_layout.setter('height'))
        
        self.refresh_commands_list()
        
        self.commands_scroll.add_widget(self.commands_layout)
        main_layout.add_widget(self.commands_scroll)
        
        tab.content = main_layout
        self.tab_panel.add_widget(tab)
    
    def create_advanced_settings_tab(self):
        """Create advanced settings tab"""
        tab = TabbedPanelItem(text='Advanced')
        
        content = ScrollView()
        layout = BoxLayout(orientation='vertical', spacing=20, size_hint_y=None, padding=[20, 20])
        layout.bind(minimum_height=layout.setter('height'))
        
        # JSON Editor Card
        json_card = ModernCard(size_hint_y=None, height=400)
        json_card.add_widget(Label(
            text='Raw JSON Editor',
            font_size='20sp',
            color=get_color_from_hex('#FFFFFF'),
            size_hint_y=None,
            height=40,
            bold=True
        ))
        
        # Config selector
        config_selector = Spinner(
            text='Select Configuration',
            values=['config.json', 'commands_config.json'],
            size_hint_y=None,
            height=40,
            background_color=get_color_from_hex('#3498DB'),
            color=(1, 1, 1, 1)
        )
        config_selector.bind(text=self.on_config_select)
        json_card.add_widget(config_selector)
        
        # JSON text area
        self.json_editor = TextInput(
            text=json.dumps(self.config_data, indent=2),
            multiline=True,
            background_color=get_color_from_hex('#1A1A1A'),
            foreground_color=get_color_from_hex('#FFFFFF'),
            font_name='RobotoMono-Regular',
            font_size='12sp'
        )
        json_card.add_widget(self.json_editor)
        
        # JSON buttons
        json_buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        validate_btn = Button(
            text='Validate JSON',
            background_color=get_color_from_hex('#F39C12'),
            color=(1, 1, 1, 1)
        )
        validate_btn.bind(on_press=self.validate_json)
        json_buttons.add_widget(validate_btn)
        
        format_btn = Button(
            text='Format JSON',
            background_color=get_color_from_hex('#9B59B6'),
            color=(1, 1, 1, 1)
        )
        format_btn.bind(on_press=self.format_json)
        json_buttons.add_widget(format_btn)
        
        json_card.add_widget(json_buttons)
        layout.add_widget(json_card)
        
        content.add_widget(layout)
        tab.content = content
        self.tab_panel.add_widget(tab)
    
    def refresh_commands_list(self):
        """Refresh the commands list display"""
        self.commands_layout.clear_widgets()
        
        commands = self.commands_data.get('commands', {})
        
        for category, category_commands in commands.items():
            # Category header
            category_card = ModernCard(size_hint_y=None, height=80)
            category_header = BoxLayout(orientation='horizontal')
            
            category_header.add_widget(Label(
                text=f'{category}',
                font_size='18sp',
                color=get_color_from_hex('#00D4FF'),
                bold=True,
                size_hint_x=0.8
            ))
            
            # Expand/collapse button (placeholder for now)
            expand_btn = Button(
                text='[...]',
                size_hint=(None, None),
                size=(50, 50),
                background_color=get_color_from_hex('#3498DB')
            )
            category_header.add_widget(expand_btn)
            
            category_card.add_widget(category_header)
            self.commands_layout.add_widget(category_card)
            
            # Commands in category
            for phrases, action in category_commands.items():
                command_card = self.create_command_card(category, phrases, action)
                self.commands_layout.add_widget(command_card)
    
    def create_command_card(self, category, phrases, action):
        """Create a card for a single command"""
        card = ModernCard(size_hint_y=None, height=120)
        
        # Command info
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.8)
        
        phrases_label = Label(
            text=f'{phrases}',
            font_size='16sp',
            color=get_color_from_hex('#FFFFFF'),
            halign='left',
            size_hint_y=None,
            height=30
        )
        phrases_label.bind(size=phrases_label.setter('text_size'))
        info_layout.add_widget(phrases_label)
        
        action_text = action if action else "Mode switch"
        action_label = Label(
            text=f'{action_text}',
            font_size='14sp',
            color=get_color_from_hex('#A0A0A0'),
            halign='left',
            size_hint_y=None,
            height=25
        )
        action_label.bind(size=action_label.setter('text_size'))
        info_layout.add_widget(action_label)
        
        card.add_widget(info_layout)
        
        # Action buttons
        buttons_layout = BoxLayout(orientation='horizontal', size_hint_x=0.2, spacing=5)
        
        edit_btn = Button(
            text='Edit',
            size_hint=(None, None),
            size=(40, 40),
            background_color=get_color_from_hex('#F39C12')
        )
        edit_btn.bind(on_press=lambda x: self.edit_command(category, phrases, action))
        buttons_layout.add_widget(edit_btn)
        
        delete_btn = Button(
            text='Del',
            size_hint=(None, None),
            size=(40, 40),
            background_color=get_color_from_hex('#FF4757')
        )
        delete_btn.bind(on_press=lambda x: self.delete_command(category, phrases))
        buttons_layout.add_widget(delete_btn)
        
        card.add_widget(buttons_layout)
        
        return card
    
    def show_add_command_dialog(self, instance):
        """Show dialog to add new command"""
        self.show_command_dialog("Add Command")
    
    def edit_command(self, category, phrases, action):
        """Edit existing command"""
        self.show_command_dialog("Edit Command", category, phrases, action)
    
    def show_command_dialog(self, title, category="", phrases="", action=""):
        """Show command editing dialog"""
        content = BoxLayout(orientation='vertical', spacing=15, padding=[20, 20])
        
        # Category
        content.add_widget(Label(text='Category:', size_hint_y=None, height=30, color=(1,1,1,1)))
        category_input = TextInput(
            text=category,
            size_hint_y=None,
            height=40,
            multiline=False,
            background_color=get_color_from_hex('#2A2A30'),
            foreground_color=(1, 1, 1, 1)
        )
        content.add_widget(category_input)
        
        # Phrases
        content.add_widget(Label(text='Voice Phrases (comma-separated):', size_hint_y=None, height=30, color=(1,1,1,1)))
        phrases_input = TextInput(
            text=phrases,
            size_hint_y=None,
            height=80,
            multiline=True,
            background_color=get_color_from_hex('#2A2A30'),
            foreground_color=(1, 1, 1, 1)
        )
        content.add_widget(phrases_input)
        
        # Action
        content.add_widget(Label(text='Action Command:', size_hint_y=None, height=30, color=(1,1,1,1)))
        action_input = TextInput(
            text=action if action else "",
            size_hint_y=None,
            height=40,
            multiline=False,
            background_color=get_color_from_hex('#2A2A30'),
            foreground_color=(1, 1, 1, 1)
        )
        content.add_widget(action_input)
        
        # Buttons
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        save_btn = Button(text='Save', background_color=get_color_from_hex('#2ECC71'))
        cancel_btn = Button(text='Cancel', background_color=get_color_from_hex('#FF4757'))
        
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.8),
            background_color=get_color_from_hex('#1A1A1A')
        )
        
        def save_command(instance):
            cat = category_input.text.strip()
            phr = phrases_input.text.strip()
            act = action_input.text.strip() or None
            
            if cat and phr:
                if cat not in self.commands_data.setdefault('commands', {}):
                    self.commands_data['commands'][cat] = {}
                
                # Remove old command if editing
                if category and phrases and category in self.commands_data['commands']:
                    if phrases in self.commands_data['commands'][category]:
                        del self.commands_data['commands'][category][phrases]
                
                self.commands_data['commands'][cat][phr] = act
                self.refresh_commands_list()
                popup.dismiss()
        
        save_btn.bind(on_press=save_command)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def delete_command(self, category, phrases):
        """Delete a command"""
        if category in self.commands_data.get('commands', {}):
            if phrases in self.commands_data['commands'][category]:
                del self.commands_data['commands'][category][phrases]
                self.refresh_commands_list()
    
    def on_config_select(self, spinner, text):
        """Handle config file selection"""
        if text == 'config.json':
            self.json_editor.text = json.dumps(self.config_data, indent=2)
        elif text == 'commands_config.json':
            self.json_editor.text = json.dumps(self.commands_data, indent=2)
    
    def validate_json(self, instance):
        """Validate JSON syntax"""
        try:
            json.loads(self.json_editor.text)
            self.show_popup("Valid JSON", "JSON syntax is valid!")
        except json.JSONDecodeError as e:
            self.show_popup("Invalid JSON", f"JSON syntax error:\n{str(e)}")
    
    def format_json(self, instance):
        """Format JSON text"""
        try:
            data = json.loads(self.json_editor.text)
            self.json_editor.text = json.dumps(data, indent=2)
        except json.JSONDecodeError as e:
            self.show_popup("Cannot Format", f"Invalid JSON:\n{str(e)}")
    
    def test_settings(self, instance):
        """Test current settings"""
        hotword = self.hotword_input.text.strip()
        threshold = self.threshold_input.text.strip()
        
        if hotword and threshold.isdigit():
            self.show_popup("Test Results", f"Hotword: '{hotword}'\nThreshold: {threshold}%\n\nSettings look good!")
        else:
            self.show_popup("Invalid Settings", "Please check your hotword and threshold values.")
    
    def save_all_configs(self, instance):
        """Save all configuration changes"""
        try:
            # Update config data from inputs
            self.config_data['hotword'] = self.hotword_input.text.strip()
            try:
                self.config_data['fuzzy_match_threshold'] = int(self.threshold_input.text.strip())
            except ValueError:
                self.config_data['fuzzy_match_threshold'] = 85
            
            # Save both files
            config_saved = self.save_config(self.config_file, self.config_data)
            commands_saved = self.save_config(self.commands_config_file, self.commands_data)
            
            if config_saved and commands_saved:
                self.show_popup("Success", "All configurations saved successfully!")
            else:
                self.show_popup("Error", "Failed to save some configurations.")
                
        except Exception as e:
            self.show_popup("Error", f"Error saving configurations:\n{str(e)}")
    
    def show_popup(self, title, message):
        """Show informational popup"""
        content = Label(text=message, color=(1, 1, 1, 1))
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.6, 0.4),
            background_color=get_color_from_hex('#1A1A1A')
        )
        popup.open()

class ConfigApp(App):
    """Main configuration app"""
    
    def build(self):
        # Configure window
        Window.size = (1200, 800)
        Window.clearcolor = get_color_from_hex('#0A0A0F')  # Very dark background
        
        # Center the window
        Window.left = (Window.system_size[0] - Window.size[0]) // 2
        Window.top = (Window.system_size[1] - Window.size[1]) // 2
        
        return ConfigEditor()

if __name__ == '__main__':
    # Suppress Kivy debug output
    os.environ['KIVY_NO_CONSOLELOG'] = '1'
    
    ConfigApp().run()
