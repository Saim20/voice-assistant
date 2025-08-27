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
        
        this._icon = new St.Icon({
            icon_name: 'audio-input-microphone-symbolic',
            style_class: 'system-status-icon'
        });
        this.add_child(this._icon);
        
        this._currentMode = 'normal';
        this._setupMenu();
        this._setupFileWatchers();
        this._updateDisplay();
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
            
            // Initial mode read
            this._onModeChanged();
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
            this._statusItem.label.text = `Voice Assistant: ${this._currentMode} mode active`;
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