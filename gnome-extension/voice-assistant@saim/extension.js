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
        
        // Initialize state
        this._currentMode = 'normal';
        this._currentBuffer = '';
        this._lastBufferUpdate = 0;
        this._lastProcessedText = '';
        this._processedTextHashes = new Set();
        this._lastCommandTime = 0;
        this._processingTimer = null;
        this._bufferClearTimer = null;
        
        // Load configuration
        this._settings = new Gio.Settings({ schema: 'org.gnome.shell.extensions.voice-assistant' });
        this._loadConfig();
        
        this._setupSettingsHandlers();
        this._setupMenu();
        this._setupFileWatchers();
        this._updateDisplay();
        
        console.log('Voice Assistant: Initialized with persistent state management');
    }
    
    _loadConfig() {
        try {
            const configPath = GLib.get_home_dir() + '/.config/nerd-dictation/config.json';
            const configFile = Gio.File.new_for_path(configPath);
            
            if (configFile.query_exists(null)) {
                let [success, contents] = configFile.load_contents(null);
                if (success) {
                    this._config = JSON.parse(new TextDecoder().decode(contents));
                    console.log('Voice Assistant: Loaded configuration');
                } else {
                    this._config = this._getDefaultConfig();
                }
            } else {
                this._config = this._getDefaultConfig();
            }
        } catch (e) {
            console.log(`Voice Assistant: Error loading config: ${e}`);
            this._config = this._getDefaultConfig();
        }
        
        // Load commands and create phrase lookup
        this._loadCommands();
    }
    
    _getDefaultConfig() {
        return {
            hotword: "hey",
            command_threshold: 80,
            processing_interval: 1.5,
            commands: {}
        };
    }
    
    _loadCommands() {
        this._commands = {};
        this._allPhrases = [];
        
        try {
            const commands = this._config.commands || {};
            
            for (const [category, categoryCommands] of Object.entries(commands)) {
                for (const [action, phrases] of Object.entries(categoryCommands)) {
                    if (Array.isArray(phrases)) {
                        // Store command mapping
                        for (const phrase of phrases) {
                            this._commands[phrase.toLowerCase()] = action;
                            this._allPhrases.push(phrase.toLowerCase());
                        }
                    }
                }
            }
            
            console.log(`Voice Assistant: Loaded ${this._allPhrases.length} command phrases`);
        } catch (e) {
            console.log(`Voice Assistant: Error loading commands: ${e}`);
        }
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
                    
                    // Update internal config
                    this._config.command_threshold = config.command_threshold;
                    this._config.processing_interval = config.processing_interval;
                    this._config.hotword = config.hotword;
                    
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
        
        // Timing info item
        this._timingItem = new PopupMenu.PopupMenuItem('Last input: never', {
            reactive: false
        });
        this.menu.addMenuItem(this._timingItem);
        
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
            
            // Watch buffer file with immediate processing
            this._bufferFile = Gio.File.new_for_path('/tmp/nerd-dictation.buffer');
            this._bufferMonitor = this._bufferFile.monitor_file(Gio.FileMonitorFlags.NONE, null);
            this._bufferMonitor.connect('changed', () => {
                // Process buffer changes immediately with a small delay for file settling
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
                        console.log(`Voice Assistant: Mode changed from ${this._currentMode} to ${newMode}`);
                        this._currentMode = newMode;
                        
                        // Clear buffer and timers on mode change
                        this._clearProcessingTimer();
                        this._clearBufferClearTimer();
                        
                        // Reset typing mode state
                        if (newMode === 'typing') {
                            this._lastTypingText = '';
                        }
                        
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
                        const now = Date.now();
                        this._lastBufferUpdate = now;
                        this._currentBuffer = newBuffer;
                        
                        console.log(`Voice Assistant: Buffer updated (${this._currentMode} mode): "${newBuffer}"`);
                        
                        // Process the buffer based on current mode
                        this._processBuffer(newBuffer);
                        
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
    
    _processBuffer(text) {
        if (!text || text.trim() === '') {
            return;
        }
        
        // Clear any existing processing timer
        this._clearProcessingTimer();
        this._clearBufferClearTimer();
        
        const mode = this._currentMode;
        console.log(`Voice Assistant: Processing "${text}" in ${mode} mode`);
        
        if (mode === 'normal') {
            this._processNormalMode(text);
        } else if (mode === 'command') {
            this._processCommandMode(text);
        } else if (mode === 'typing') {
            this._processTypingMode(text);
        }
    }
    
    _processNormalMode(text) {
        // Look for hotword
        const hotword = this._config.hotword || 'hey';
        const words = text.toLowerCase().split(/\\s+/);
        const hotwordRatio = this._getBestWordMatch(words, hotword.toLowerCase());
        
        console.log(`Voice Assistant: Hotword "${hotword}" confidence: ${hotwordRatio}%`);
        
        if (hotwordRatio >= (this._config.command_threshold || 80)) {
            console.log(`Voice Assistant: Hotword detected, switching to command mode`);
            this._setMode('command');
            return;
        }
        
        // Clear buffer if it gets too long in normal mode
        if (words.length > 10) {
            console.log(`Voice Assistant: Buffer too long in normal mode (${words.length} words), scheduling clear`);
            this._scheduleBufferClear(2000); // Clear after 2 seconds
        }
    }
    
    _processCommandMode(text) {
        // Set up automatic processing after interval
        const interval = (this._config.processing_interval || 1.5) * 1000;
        
        this._processingTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, interval, () => {
            this._executeCommandProcessing(text);
            this._processingTimer = null;
            return GLib.SOURCE_REMOVE;
        });
        
        console.log(`Voice Assistant: Scheduled command processing in ${interval}ms`);
    }
    
    _executeCommandProcessing(text) {
        console.log(`Voice Assistant: Executing command processing for: "${text}"`);
        
        // Check for mode change commands first
        const modeSwitches = {
            'typing mode': 'typing',
            'go to typing mode': 'typing', 
            'start typing': 'typing',
            'normal mode': 'normal',
            'go to normal mode': 'normal',
            'stop typing': 'normal',
            'exit typing': 'normal',
            'cancel': 'normal',
            'stop': 'normal',
            'nevermind': 'normal'
        };
        
        for (const [phrase, targetMode] of Object.entries(modeSwitches)) {
            const ratio = this._getTextSimilarity(text.toLowerCase(), phrase);
            if (ratio >= (this._config.command_threshold || 80)) {
                console.log(`Voice Assistant: Mode switch command detected (${ratio}%): ${phrase} -> ${targetMode}`);
                this._setMode(targetMode);
                return;
            }
        }
        
        // Find best command match
        const [bestMatch, bestRatio] = this._findBestCommandMatch(text);
        
        if (bestMatch && bestRatio >= (this._config.command_threshold || 80)) {
            console.log(`Voice Assistant: Executing command (${bestRatio}%): "${bestMatch}"`);
            
            // Mark as processed
            const textHash = this._hashText(text.toLowerCase());
            this._processedTextHashes.add(textHash);
            this._lastCommandTime = Date.now();
            
            // Execute the command
            this._executeCommand(this._commands[bestMatch]);
        } else {
            console.log(`Voice Assistant: No matching command found (best: ${bestRatio}%)`);
            
            // Clear buffer if no match and substantial text
            if (text.split(/\\s+/).length >= 3) {
                this._scheduleBufferClear(1000);
            }
        }
    }
    
    _processTypingMode(text) {
        // In typing mode, check for exit commands
        const exitPhrases = ['stop typing', 'exit typing', 'normal mode', 'go to normal mode'];
        
        for (const phrase of exitPhrases) {
            if (text.toLowerCase().includes(phrase)) {
                console.log(`Voice Assistant: Exit phrase detected in typing mode: ${phrase}`);
                this._setMode('normal');
                return;
            }
        }
        
        // For typing mode, we simulate keyboard input
        this._typeText(text);
    }
    
    _findBestCommandMatch(text) {
        let bestMatch = null;
        let bestRatio = 0;
        
        const textLower = text.toLowerCase();
        
        for (const phrase of this._allPhrases) {
            const ratio = this._getTextSimilarity(textLower, phrase);
            if (ratio > bestRatio) {
                bestRatio = ratio;
                bestMatch = phrase;
            }
        }
        
        return [bestMatch, bestRatio];
    }
    
    _getBestWordMatch(words, target) {
        let bestRatio = 0;
        
        // Check for exact match
        if (words.includes(target)) {
            return 100;
        }
        
        // Check similarity with each word
        for (const word of words) {
            const ratio = this._getTextSimilarity(word, target);
            if (ratio > bestRatio) {
                bestRatio = ratio;
            }
        }
        
        return bestRatio;
    }
    
    _getTextSimilarity(str1, str2) {
        // Simple similarity calculation (Levenshtein-based)
        if (str1 === str2) return 100;
        
        const len1 = str1.length;
        const len2 = str2.length;
        
        if (len1 === 0) return len2 === 0 ? 100 : 0;
        if (len2 === 0) return 0;
        
        const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(null));
        
        for (let i = 0; i <= len1; i++) matrix[i][0] = i;
        for (let j = 0; j <= len2; j++) matrix[0][j] = j;
        
        for (let i = 1; i <= len1; i++) {
            for (let j = 1; j <= len2; j++) {
                const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
                matrix[i][j] = Math.min(
                    matrix[i - 1][j] + 1,      // deletion
                    matrix[i][j - 1] + 1,      // insertion
                    matrix[i - 1][j - 1] + cost // substitution
                );
            }
        }
        
        const maxLen = Math.max(len1, len2);
        const distance = matrix[len1][len2];
        return Math.max(0, ((maxLen - distance) / maxLen) * 100);
    }
    
    _hashText(text) {
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            const char = text.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash;
    }
    
    _executeCommand(command) {
        try {
            console.log(`Voice Assistant: Executing command: ${command}`);
            
            // Use command executor script if available
            const scriptPath = GLib.get_home_dir() + '/.config/nerd-dictation/command_executor.sh';
            const scriptFile = Gio.File.new_for_path(scriptPath);
            
            if (scriptFile.query_exists(null)) {
                GLib.spawn_command_line_async(`${scriptPath} "${command}"`);
                console.log(`Voice Assistant: Command executed via script: ${command}`);
            } else {
                // Fallback to direct execution
                GLib.spawn_command_line_async(command);
                console.log(`Voice Assistant: Command executed directly: ${command}`);
            }
            
            // Clear buffer after successful command execution
            this._clearBuffer();
            
        } catch (e) {
            console.log(`Voice Assistant: Error executing command "${command}": ${e}`);
        }
    }
    
    _typeText(text) {
        try {
            // Handle incremental typing for typing mode
            if (!this._lastTypingText) {
                this._lastTypingText = '';
            }
            
            // If text is shorter than last time, it's a reset
            if (text.length < this._lastTypingText.length) {
                this._lastTypingText = text;
                this._simulateTyping(text);
                return;
            }
            
            // Extract only the new portion
            const newText = text.substring(this._lastTypingText.length);
            if (newText) {
                this._lastTypingText = text;
                this._simulateTyping(newText);
            }
            
        } catch (e) {
            console.log(`Voice Assistant: Error typing text: ${e}`);
        }
    }
    
    _simulateTyping(text) {
        try {
            // Use ydotool to simulate typing
            const command = `ydotool type "${text.replace(/"/g, '\\\\"')}"`;
            GLib.spawn_command_line_async(command);
            console.log(`Voice Assistant: Typed: "${text}"`);
        } catch (e) {
            console.log(`Voice Assistant: Error simulating typing: ${e}`);
        }
    }
    
    _clearProcessingTimer() {
        if (this._processingTimer) {
            GLib.source_remove(this._processingTimer);
            this._processingTimer = null;
        }
    }
    
    _clearBufferClearTimer() {
        if (this._bufferClearTimer) {
            GLib.source_remove(this._bufferClearTimer);
            this._bufferClearTimer = null;
        }
    }
    
    _scheduleBufferClear(delay) {
        this._clearBufferClearTimer();
        
        this._bufferClearTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, delay, () => {
            console.log('Voice Assistant: Scheduled buffer clear triggered');
            this._suspendResumeForBufferClear();
            this._bufferClearTimer = null;
            return GLib.SOURCE_REMOVE;
        });
    }
    
    _clearBuffer() {
        try {
            const bufferFile = Gio.File.new_for_path('/tmp/nerd-dictation.buffer');
            if (bufferFile.query_exists(null)) {
                bufferFile.replace_contents('', null, false, Gio.FileCreateFlags.NONE, null);
            }
            this._currentBuffer = '';
            this._updateDisplay();
        } catch (e) {
            console.log(`Voice Assistant: Error clearing buffer: ${e}`);
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
            if (this._processingTimer) {
                statusText += ' (processing...)';
            }
            this._statusItem.label.text = statusText;
        }
        
        // Update buffer item
        if (this._bufferItem) {
            if (this._currentBuffer && this._currentBuffer.length > 0) {
                let bufferText = this._currentBuffer;
                const maxLength = 50;
                if (bufferText.length > maxLength) {
                    bufferText = bufferText.substring(0, maxLength) + '...';
                }
                this._bufferItem.label.text = `Buffer: "${bufferText}"`;
            } else {
                this._bufferItem.label.text = 'Buffer: (empty)';
            }
        }
        
        // Update timing info
        if (this._timingItem) {
            if (this._lastBufferUpdate > 0) {
                const elapsed = Math.floor((Date.now() - this._lastBufferUpdate) / 1000);
                this._timingItem.label.text = `Last input: ${elapsed}s ago`;
            } else {
                this._timingItem.label.text = 'Last input: never';
            }
        }
    }
    
    _updateBufferDisplay() {
        if (!this._bufferLabel) return;
        
        // Only show buffer text in command mode
        if (this._currentMode === 'command' && this._currentBuffer && this._currentBuffer.length > 0) {
            let displayText = this._currentBuffer;
            const maxLength = 25;
            
            if (displayText.length > maxLength) {
                displayText = displayText.substring(0, maxLength) + '...';
            }
            
            this._bufferLabel.text = displayText;
            this._bufferLabel.visible = true;
        } else {
            this._bufferLabel.text = '';
            this._bufferLabel.visible = false;
        }
    }
    
    _setMode(mode) {
        try {
            // Use the mode_changer.sh script if available for suspend/resume functionality
            const scriptPath = GLib.get_home_dir() + '/.config/nerd-dictation/mode_changer.sh';
            const scriptFile = Gio.File.new_for_path(scriptPath);
            
            if (scriptFile.query_exists(null)) {
                GLib.spawn_command_line_async(`${scriptPath} ${mode}`);
                console.log(`Voice Assistant: Mode change requested via script: ${mode}`);
            } else {
                // Fallback to direct mode change
                let file = Gio.File.new_for_path('/tmp/nerd-dictation.mode');
                file.replace_contents(mode, null, false, Gio.FileCreateFlags.NONE, null);
                console.log(`Voice Assistant: Mode set directly to ${mode}`);
            }
        } catch (e) {
            console.log(`Voice Assistant: Error setting mode: ${e}`);
        }
    }
    
    _suspendResumeForBufferClear() {
        try {
            const scriptPath = GLib.get_home_dir() + '/.config/nerd-dictation/command_executor.sh';
            const scriptFile = Gio.File.new_for_path(scriptPath);
            
            if (scriptFile.query_exists(null)) {
                GLib.spawn_command_line_async(`${scriptPath} echo "Buffer cleared"`);
                console.log('Voice Assistant: Triggered suspend/resume cycle to clear buffer');
            } else {
                console.log('Voice Assistant: command_executor.sh not found, cannot clear buffer');
            }
        } catch (e) {
            console.log(`Voice Assistant: Error triggering buffer clear: ${e}`);
        }
    }
    
    destroy() {
        // Clean up timers
        this._clearProcessingTimer();
        this._clearBufferClearTimer();
        
        // Clean up file monitors
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
