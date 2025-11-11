import GObject from 'gi://GObject';
import St from 'gi://St';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as MessageTray from 'resource:///org/gnome/shell/ui/messageTray.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

// Import modular components
import {ConfigManager} from './lib/ConfigManager.js';

// D-Bus interface XML
const VoiceAssistantIface = `
<node>
  <interface name="com.github.saim.VoiceAssistant">
    <method name="SetMode">
      <arg direction="in" name="mode" type="s"/>
    </method>
    <method name="GetMode">
      <arg direction="out" name="mode" type="s"/>
    </method>
    <method name="GetStatus">
      <arg direction="out" name="status" type="a{sv}"/>
    </method>
    <method name="GetConfig">
      <arg direction="out" name="config" type="s"/>
    </method>
    <method name="UpdateConfig">
      <arg direction="in" name="config" type="s"/>
    </method>
    <method name="SetConfigValue">
      <arg direction="in" name="key" type="s"/>
      <arg direction="in" name="value" type="v"/>
    </method>
    <method name="Start"/>
    <method name="Stop"/>
    <method name="Restart"/>
    <method name="GetBuffer">
      <arg direction="out" name="buffer" type="s"/>
    </method>
    <signal name="ModeChanged">
      <arg name="new_mode" type="s"/>
      <arg name="old_mode" type="s"/>
    </signal>
    <signal name="BufferChanged">
      <arg name="buffer" type="s"/>
    </signal>
    <signal name="CommandExecuted">
      <arg name="command" type="s"/>
      <arg name="phrase" type="s"/>
      <arg name="confidence" type="d"/>
    </signal>
    <signal name="StatusChanged">
      <arg name="status" type="a{sv}"/>
    </signal>
    <signal name="Error">
      <arg name="message" type="s"/>
      <arg name="details" type="s"/>
    </signal>
    <signal name="Notification">
      <arg name="title" type="s"/>
      <arg name="message" type="s"/>
      <arg name="urgency" type="s"/>
    </signal>
    <property name="IsRunning" type="b" access="read"/>
    <property name="CurrentMode" type="s" access="read"/>
    <property name="CurrentBuffer" type="s" access="read"/>
    <property name="Version" type="s" access="read"/>
  </interface>
</node>`;

const VoiceAssistantProxy = Gio.DBusProxy.makeProxyWrapper(VoiceAssistantIface);

const VoiceAssistantIndicator = GObject.registerClass(
class VoiceAssistantIndicator extends PanelMenu.Button {
    _init(settings) {
        super._init(0.0, 'Voice Assistant');
        
        // Create panel UI
        this._box = new St.BoxLayout({
            style_class: 'panel-status-menu-box'
        });
        this.add_child(this._box);
        
        this._icon = new St.Icon({
            icon_name: 'microphone-sensitivity-medium-symbolic',
            style_class: 'system-status-icon'
        });
        this._box.add_child(this._icon);
        
        this._bufferLabel = new St.Label({
            text: '',
            style_class: 'voice-assistant-buffer-text',
            y_align: 2
        });
        this._box.add_child(this._bufferLabel);
        
        // State
        this._currentMode = 'normal';
        this._currentBuffer = '';
        this._isRunning = false;
        
        // Settings
        this._settings = settings;
        this._configManager = new ConfigManager(this._settings);
        
        // Notification source
        this._notificationSource = null;
        
        // Setup D-Bus connection
        this._setupDBus();
        
        // Setup menu
        this._setupMenu();
        
        // Setup settings handlers
        this._setupSettingsHandlers();
        
        console.log('Voice Assistant: Extension initialized with D-Bus');
    }
    
    _setupDBus() {
        try {
            // Create proxy to the D-Bus service
            this._proxy = new VoiceAssistantProxy(
                Gio.DBus.session,
                'com.github.saim.VoiceAssistant',
                '/com/github/saim/VoiceAssistant',
                (proxy, error) => {
                    if (error) {
                        console.error('Voice Assistant: D-Bus connection error:', error);
                        this._showNotification(
                            'Service Error',
                            'Failed to connect to Voice Assistant service',
                            MessageTray.Urgency.HIGH
                        );
                        return;
                    }
                    
                    this._onDBusConnected();
                }
            );
            
        } catch (e) {
            console.error('Voice Assistant: Failed to create D-Bus proxy:', e);
        }
    }
    
    _onDBusConnected() {
        console.log('Voice Assistant: Connected to D-Bus service');
        
        // Connect to signals
        this._proxy.connectSignal('ModeChanged', (proxy, sender, [newMode, oldMode]) => {
            this._onModeChanged(newMode, oldMode);
        });
        
        this._proxy.connectSignal('BufferChanged', (proxy, sender, [buffer]) => {
            this._onBufferChanged(buffer);
        });
        
        this._proxy.connectSignal('CommandExecuted', (proxy, sender, [command, phrase, confidence]) => {
            this._onCommandExecuted(command, phrase, confidence);
        });
        
        this._proxy.connectSignal('StatusChanged', (proxy, sender, [status]) => {
            this._onStatusChanged(status);
        });
        
        this._proxy.connectSignal('Error', (proxy, sender, [message, details]) => {
            this._onError(message, details);
        });
        
        this._proxy.connectSignal('Notification', (proxy, sender, [title, message, urgency]) => {
            this._onNotification(title, message, urgency);
        });
        
        // Get initial status
        this._updateStatus();
        
        // Poll status periodically
        this._statusTimer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 2, () => {
            this._updateStatus();
            return GLib.SOURCE_CONTINUE;
        });
    }
    
    _setupMenu() {
        // Mode display
        this._modeItem = new PopupMenu.PopupMenuItem(`Mode: NORMAL`, {
            reactive: false
        });
        this.menu.addMenuItem(this._modeItem);
        
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // Service control
        this._serviceStatusItem = new PopupMenu.PopupMenuItem('Service: Checking...', {
            reactive: false
        });
        this.menu.addMenuItem(this._serviceStatusItem);
        
        this._startItem = new PopupMenu.PopupMenuItem('Start Service');
        this._startItem.connect('activate', () => this._startService());
        this.menu.addMenuItem(this._startItem);

        this._stopItem = new PopupMenu.PopupMenuItem('Stop Service');
        this._stopItem.connect('activate', () => this._stopService());
        this.menu.addMenuItem(this._stopItem);

        this._restartItem = new PopupMenu.PopupMenuItem('Restart Service');
        this._restartItem.connect('activate', () => this._restartService());
        this.menu.addMenuItem(this._restartItem);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // Mode switching
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
        
        // Buffer display
        this._bufferItem = new PopupMenu.PopupMenuItem('Buffer: (empty)', {
            reactive: false
        });
        this.menu.addMenuItem(this._bufferItem);
        
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // Preferences
        this._prefsItem = new PopupMenu.PopupMenuItem('Preferences');
        this._prefsItem.connect('activate', () => {
            try {
                GLib.spawn_command_line_async('gnome-extensions prefs voice-assistant@saim');
            } catch (e) {
                console.error('Voice Assistant: Error opening preferences:', e);
            }
        });
        this.menu.addMenuItem(this._prefsItem);
    }
    
    _setupSettingsHandlers() {
        // When settings change, sync to D-Bus service
        const syncableKeys = ['hotword', 'command-threshold', 'processing-interval'];
        
        syncableKeys.forEach(key => {
            this._settings.connect(`changed::${key}`, () => {
                if (this._settings.get_boolean('auto-sync')) {
                    this._syncSettingsToService();
                }
            });
        });
        
        this._settings.connect('changed::auto-sync', () => {
            if (this._settings.get_boolean('auto-sync')) {
                this._syncSettingsToService();
            }
        });
    }
    
    _syncSettingsToService() {
        if (!this._proxy) return;
        
        try {
            const hotword = this._settings.get_string('hotword');
            const threshold = this._settings.get_double('command-threshold') / 100.0;
            const interval = this._settings.get_double('processing-interval');
            
            this._proxy.SetConfigValueRemote('hotword', new GLib.Variant('s', hotword));
            this._proxy.SetConfigValueRemote('command_threshold', new GLib.Variant('d', threshold));
            this._proxy.SetConfigValueRemote('processing_interval', new GLib.Variant('d', interval));
            
            console.log('Voice Assistant: Settings synced to service');
        } catch (e) {
            console.error('Voice Assistant: Error syncing settings:', e);
        }
    }
    
    // D-Bus method wrappers
    
    _setMode(mode) {
        if (!this._proxy) {
            this._showNotification('Error', 'Service not connected', MessageTray.Urgency.HIGH);
            return;
        }
        
        try {
            this._proxy.SetModeRemote(mode, (result, error) => {
                if (error) {
                    console.error('Voice Assistant: SetMode error:', error);
                    this._showNotification('Error', 'Failed to change mode', MessageTray.Urgency.HIGH);
                }
            });
        } catch (e) {
            console.error('Voice Assistant: SetMode exception:', e);
        }
    }
    
    _startService() {
        if (!this._proxy) {
            this._showNotification('Error', 'Service not connected', MessageTray.Urgency.HIGH);
            return;
        }
        
        try {
            this._proxy.StartRemote((result, error) => {
                if (error) {
                    console.error('Voice Assistant: Start error:', error);
                    this._showNotification('Error', 'Failed to start service', MessageTray.Urgency.HIGH);
                }
            });
        } catch (e) {
            console.error('Voice Assistant: Start exception:', e);
        }
    }
    
    _stopService() {
        if (!this._proxy) return;
        
        try {
            this._proxy.StopRemote((result, error) => {
                if (error) {
                    console.error('Voice Assistant: Stop error:', error);
                }
            });
        } catch (e) {
            console.error('Voice Assistant: Stop exception:', e);
        }
    }
    
    _restartService() {
        if (!this._proxy) return;
        
        try {
            this._proxy.RestartRemote((result, error) => {
                if (error) {
                    console.error('Voice Assistant: Restart error:', error);
                }
            });
        } catch (e) {
            console.error('Voice Assistant: Restart exception:', e);
        }
    }
    
    _updateStatus() {
        if (!this._proxy) return;
        
        try {
            this._proxy.GetStatusRemote((result, error) => {
                if (error) {
                    console.error('Voice Assistant: GetStatus error:', error);
                    return;
                }
                
                if (result && result[0]) {
                    const status = result[0];
                    this._onStatusChanged(status);
                }
            });
        } catch (e) {
            console.error('Voice Assistant: GetStatus exception:', e);
        }
    }
    
    // Signal handlers
    
    _onModeChanged(newMode, oldMode) {
        this._currentMode = newMode;
        this._updateDisplay();
        
        if (this._settings.get_boolean('notification-enabled')) {
            this._showNotification(
                'Mode Changed',
                `Switched from ${oldMode} to ${newMode}`,
                MessageTray.Urgency.NORMAL
            );
        }
    }
    
    _onBufferChanged(buffer) {
        this._currentBuffer = buffer;
        this._updateDisplay();
    }
    
    _onCommandExecuted(command, phrase, confidence) {
        console.log(`Voice Assistant: Command executed: ${phrase} (${(confidence * 100).toFixed(1)}%)`);
        
        if (this._settings.get_boolean('notification-enabled')) {
            this._showNotification(
                'Command Executed',
                `${phrase} (${(confidence * 100).toFixed(1)}% confidence)`,
                MessageTray.Urgency.NORMAL
            );
        }
    }
    
    _onStatusChanged(status) {
        if (status.is_running !== undefined) {
            this._isRunning = status.is_running.unpack();
        }
        if (status.current_mode !== undefined) {
            this._currentMode = status.current_mode.unpack();
        }
        if (status.current_buffer !== undefined) {
            this._currentBuffer = status.current_buffer.unpack();
        }
        
        this._updateDisplay();
    }
    
    _onError(message, details) {
        console.error('Voice Assistant:', message, details);
        this._showNotification('Error', message, MessageTray.Urgency.HIGH);
    }
    
    _onNotification(title, message, urgency) {
        if (!this._settings.get_boolean('notification-enabled')) return;
        
        const urgencyLevel = urgency === 'high' ? MessageTray.Urgency.HIGH :
                           urgency === 'low' ? MessageTray.Urgency.LOW :
                           MessageTray.Urgency.NORMAL;
        
        this._showNotification(title, message, urgencyLevel);
    }
    
    // UI updates
    
    _updateDisplay() {
        // Update icon based on mode
        let iconName = 'microphone-sensitivity-medium-symbolic';
        let iconStyle = '';
        
        if (!this._isRunning) {
            iconName = 'microphone-disabled-symbolic';
        } else if (this._currentMode === 'command') {
            iconName = 'microphone-sensitivity-high-symbolic';
            iconStyle = 'color: #ff4444;'; // Red for command mode
        } else if (this._currentMode === 'typing') {
            iconName = 'input-keyboard-symbolic';
        }
        
        this._icon.icon_name = iconName;
        if (iconStyle) {
            this._icon.style = iconStyle;
        } else {
            this._icon.style = '';
        }
        
        // Update buffer text
        const maxBufferLength = 50;
        let bufferText = this._currentBuffer;
        if (bufferText.length > maxBufferLength) {
            bufferText = '...' + bufferText.substring(bufferText.length - maxBufferLength);
        }
        this._bufferLabel.text = bufferText ? ` ${bufferText}` : '';
        
        // Update menu items
        if (this._modeItem) {
            this._modeItem.label.text = `Mode: ${this._currentMode.toUpperCase()}`;
        }
        
        if (this._bufferItem) {
            this._bufferItem.label.text = this._currentBuffer 
                ? `Buffer: ${this._currentBuffer}` 
                : 'Buffer: (empty)';
        }
        
        if (this._serviceStatusItem) {
            this._serviceStatusItem.label.text = this._isRunning 
                ? 'Service: Running' 
                : 'Service: Stopped';
        }
        
        // Update menu button sensitivity
        if (this._startItem) this._startItem.setSensitive(!this._isRunning);
        if (this._stopItem) this._stopItem.setSensitive(this._isRunning);
        if (this._restartItem) this._restartItem.setSensitive(this._isRunning);
    }
    
    _showNotification(title, message, urgency) {
        if (!this._notificationSource) {
            this._notificationSource = new MessageTray.Source({
                title: 'Voice Assistant',
                iconName: 'microphone-sensitivity-medium-symbolic'
            });
            Main.messageTray.add(this._notificationSource);
        }
        
        const notification = new MessageTray.Notification({
            source: this._notificationSource,
            title: title,
            body: message,
            urgency: urgency
        });
        
        this._notificationSource.addNotification(notification);
    }
    
    destroy() {
        // Clean up timers
        if (this._statusTimer) {
            GLib.source_remove(this._statusTimer);
            this._statusTimer = null;
        }
        
        // Clean up D-Bus proxy
        if (this._proxy) {
            this._proxy = null;
        }
        
        super.destroy();
    }
});

export default class VoiceAssistantExtension extends Extension {
    constructor(metadata) {
        super(metadata);
        this._indicator = null;
    }

    enable() {
        console.log('Voice Assistant: Enabling extension');
        const settings = this.getSettings();
        this._indicator = new VoiceAssistantIndicator(settings);
        Main.panel.addToStatusArea('voice-assistant', this._indicator);
    }

    disable() {
        console.log('Voice Assistant: Disabling extension');
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
}
