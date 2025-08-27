import GObject from 'gi://GObject';
import St from 'gi://St';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

const VoiceAssistantIndicator = GObject.registerClass(
class VoiceAssistantIndicator extends PanelMenu.Button {
    _init() {
        super._init(0.0, 'Voice Assistant');
        
        // Create a horizontal box layout to hold icon and text
        this._box = new St.BoxLayout({
            style_class: 'panel-status-menu-box'
        });
        this.add_child(this._box);
        
        this._icon = new St.Icon({
            icon_name: 'audio-input-microphone-symbolic',
            style_class: 'system-status-icon'
        });
        this._box.add_child(this._icon);
        
        // Add buffer text label
        this._bufferLabel = new St.Label({
            text: '',
            style_class: 'voice-assistant-buffer-text',
            y_align: 2  // Middle alignment
        });
        this._box.add_child(this._bufferLabel);
        
        this._currentMode = 'normal';
        this._currentBuffer = '';
        this._settings = new Gio.Settings({ schema: 'org.gnome.shell.extensions.voice-assistant' });
        this._setupSettingsHandlers();
        this._setupMenu();
        this._setupFileWatchers();
        this._updateDisplay();
    }
    
    _setupSettingsHandlers() {
        // Listen for settings changes and update config file
        this._settings.connect('changed::command-threshold', () => this._updateConfigFile());
        this._settings.connect('changed::processing-interval', () => this._updateConfigFile());
        this._settings.connect('changed::hotword', () => this._updateConfigFile());
    }
    
    _updateConfigFile() {
        try {
            const configPath = GLib.get_home_dir() + '/.config/nerd-dictation/config.json';
            const configFile = Gio.File.new_for_path(configPath);
            
            if (configFile.query_exists(null)) {
                let [success, contents] = configFile.load_contents(null);
                if (success) {
                    let config = JSON.parse(new TextDecoder().decode(contents));
                    
                    // Update config with new settings
                    config.command_threshold = this._settings.get_int('command-threshold');
                    config.processing_interval = this._settings.get_double('processing-interval');
                    config.hotword = this._settings.get_string('hotword');
                    
                    // Save updated config
                    const updatedConfig = JSON.stringify(config, null, 2);
                    configFile.replace_contents(updatedConfig, null, false, 
                        Gio.FileCreateFlags.NONE, null);
                    
                    console.log('Voice Assistant: Updated config file with new settings');
                }
            }
        } catch (e) {
            console.log(`Voice Assistant: Error updating config file: ${e}`);
        }
    }
    
    _setupMenu() {
        // Current mode display
        this._modeItem = new PopupMenu.PopupMenuItem(`Mode: ${this._currentMode.toUpperCase()}`, {
            reactive: false
        });
        this.menu.addMenuItem(this._modeItem);
        
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // Mode switching buttons
        this._normalModeItem = new PopupMenu.PopupMenuItem('Switch to Normal Mode');
        this._normalModeItem.connect('activate', () => this._setMode('normal'));
        this.menu.addMenuItem(this._normalModeItem);
        
        this._commandModeItem = new PopupMenu.PopupMenuItem('Switch to Command Mode');
        this._commandModeItem.connect('activate', () => this._setMode('command'));
        this.menu.addMenuItem(this._commandModeItem);
        
        this._typingModeItem = new PopupMenu.PopupMenuItem('Switch to Typing Mode');
        this._typingModeItem.connect('activate', () => this._setMode('typing'));
        this.menu.addMenuItem(this._typingModeItem);
        
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // Status item
        this._statusItem = new PopupMenu.PopupMenuItem('Ready', {
            reactive: false
        });
        this.menu.addMenuItem(this._statusItem);
        
        // Buffer display item
        this._bufferItem = new PopupMenu.PopupMenuItem('Buffer: (empty)', {
            reactive: false
        });
        this.menu.addMenuItem(this._bufferItem);
        
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // Preferences item
        this._prefsItem = new PopupMenu.PopupMenuItem('Preferences');
        this._prefsItem.connect('activate', () => {
            try {
                GLib.spawn_command_line_async('gnome-extensions prefs voice-assistant@saim');
            } catch (e) {
                console.log(`Voice Assistant: Error opening preferences: ${e}`);
            }
        });
        this.menu.addMenuItem(this._prefsItem);
    }
    
    _setupFileWatchers() {
        try {
            // Watch mode file
            this._modeFile = Gio.File.new_for_path('/tmp/nerd-dictation.mode');
            this._modeMonitor = this._modeFile.monitor_file(Gio.FileMonitorFlags.NONE, null);
            this._modeMonitor.connect('changed', () => {
                GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
                    this._onModeChanged();
                    return GLib.SOURCE_REMOVE;
                });
            });
            
            // Watch buffer file
            this._bufferFile = Gio.File.new_for_path('/tmp/nerd-dictation.buffer');
            this._bufferMonitor = this._bufferFile.monitor_file(Gio.FileMonitorFlags.NONE, null);
            this._bufferMonitor.connect('changed', () => {
                GLib.timeout_add(GLib.PRIORITY_DEFAULT, 50, () => {
                    this._onBufferChanged();
                    return GLib.SOURCE_REMOVE;
                });
            });
            
            // Initial reads
            this._onModeChanged();
            this._onBufferChanged();
        } catch (e) {
            console.log(`Voice Assistant: Error setting up file watchers: ${e}`);
        }
    }
    
    _onModeChanged() {
        try {
            if (this._modeFile.query_exists(null)) {
                let [success, contents] = this._modeFile.load_contents(null);
                if (success) {
                    let newMode = new TextDecoder().decode(contents).trim();
                    if (newMode && newMode !== this._currentMode) {
                        this._currentMode = newMode;
                        this._updateDisplay();
                    }
                }
            }
        } catch (e) {
            console.log(`Voice Assistant: Error reading mode file: ${e}`);
        }
    }
    
    _onBufferChanged() {
        try {
            if (this._bufferFile.query_exists(null)) {
                let [success, contents] = this._bufferFile.load_contents(null);
                if (success) {
                    let newBuffer = new TextDecoder().decode(contents).trim();
                    if (newBuffer !== this._currentBuffer) {
                        this._currentBuffer = newBuffer;
                        this._updateDisplay();
                    }
                }
            } else {
                // Buffer file doesn't exist, clear buffer
                if (this._currentBuffer !== '') {
                    this._currentBuffer = '';
                    this._updateDisplay();
                }
            }
        } catch (e) {
            console.log(`Voice Assistant: Error reading buffer file: ${e}`);
        }
    }
    
    _updateDisplay() {
        // Update icon and style based on mode
        let iconName = 'audio-input-microphone-symbolic';
        let styleClass = 'system-status-icon';
        
        switch (this._currentMode) {
            case 'command':
                iconName = 'audio-input-microphone-high-symbolic';
                styleClass += ' voice-assistant-command';
                break;
            case 'typing':
                iconName = 'edit-symbolic';
                styleClass += ' voice-assistant-typing';
                break;
            default:
                iconName = 'audio-input-microphone-symbolic';
                styleClass += ' voice-assistant-normal';
                break;
        }
        
        this._icon.icon_name = iconName;
        this._icon.style_class = styleClass;
        
        // Update buffer text display
        this._updateBufferDisplay();
        
        // Update menu
        if (this._modeItem) {
            this._modeItem.label.text = `Mode: ${this._currentMode.toUpperCase()}`;
        }
        
        // Update button sensitivity
        if (this._normalModeItem) this._normalModeItem.setSensitive(this._currentMode !== 'normal');
        if (this._commandModeItem) this._commandModeItem.setSensitive(this._currentMode !== 'command');
        if (this._typingModeItem) this._typingModeItem.setSensitive(this._currentMode !== 'typing');
        
        // Update status
        if (this._statusItem) {
            let statusText = `Voice Assistant: ${this._currentMode} mode active`;
            this._statusItem.label.text = statusText;
        }
        
        // Update buffer item
        if (this._bufferItem) {
            if (this._currentBuffer && this._currentBuffer.length > 0) {
                let bufferText = this._currentBuffer;
                const maxLength = 50; // Longer limit for menu display
                if (bufferText.length > maxLength) {
                    bufferText = bufferText.substring(0, maxLength) + '...';
                }
                this._bufferItem.label.text = `Buffer: "${bufferText}"`;
            } else {
                this._bufferItem.label.text = 'Buffer: (empty)';
            }
        }
    }
    
    _updateBufferDisplay() {
        if (!this._bufferLabel) return;
        
        if (this._currentBuffer && this._currentBuffer.length > 0) {
            // Truncate buffer text if too long for display
            let displayText = this._currentBuffer;
            const maxLength = 25; // Shorter for status bar
            
            if (displayText.length > maxLength) {
                displayText = displayText.substring(0, maxLength) + '...';
            }
            
            // Show the text without quotes for cleaner look
            this._bufferLabel.text = displayText;
            this._bufferLabel.visible = true;
        } else {
            // Show placeholder text for testing - you can remove this later
            this._bufferLabel.text = '';
            this._bufferLabel.visible = false;
        }
    }
    
    _setMode(mode) {
        try {
            let file = Gio.File.new_for_path('/tmp/nerd-dictation.mode');
            file.replace_contents(mode, null, false, Gio.FileCreateFlags.NONE, null);
            console.log(`Voice Assistant: Mode set to ${mode}`);
        } catch (e) {
            console.log(`Voice Assistant: Error setting mode: ${e}`);
        }
    }
    
    destroy() {
        if (this._modeMonitor) {
            this._modeMonitor.cancel();
            this._modeMonitor = null;
        }
        if (this._bufferMonitor) {
            this._bufferMonitor.cancel();
            this._bufferMonitor = null;
        }
        super.destroy();
    }
});

export default class VoiceAssistantExtension {
    enable() {
        console.log('Voice Assistant extension enabling...');
        try {
            this._indicator = new VoiceAssistantIndicator();
            Main.panel.addToStatusArea('voice-assistant', this._indicator);
            console.log('Voice Assistant extension enabled successfully');
        } catch (e) {
            console.log(`Voice Assistant extension failed to enable: ${e}`);
        }
    }
    
    disable() {
        console.log('Voice Assistant extension disabling...');
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
        console.log('Voice Assistant extension disabled');
    }
}