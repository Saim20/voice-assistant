import GObject from 'gi://GObject';
import St from 'gi://St';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

// Import modular components
import {ConfigManager} from './lib/ConfigManager.js';

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
            icon_name: 'applications-system-symbolic',
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
        this._lastExecutedText = '';
        this._processingTimer = null;
        this._bufferClearTimer = null;
        this._bufferTimeoutTimer = null;
        this._debounceTimer = null;
        
        // Load configuration using ConfigManager
        this._settings = new Gio.Settings({ schema: 'org.gnome.shell.extensions.voice-assistant' });
        this._configManager = new ConfigManager(this._settings);
        this._config = this._configManager.getConfig();
        
        this._setupSettingsHandlers();
        this._setupMenu();
        this._setupFileWatchers();
        this._updateDisplay();
        
        // Load commands using the config manager
        this._loadCommands();
        
        console.log('Voice Assistant: Initialized with persistent state management');
    }
    
    _loadCommands() {
        this._commands = {};
        this._allPhrases = [];
        
        try {
            const commands = this._config.commands || [];
            
            // New simplified structure: each command has name, command, and phrases
            for (const commandDef of commands) {
                if (commandDef.phrases && Array.isArray(commandDef.phrases) && commandDef.command) {
                    for (const phrase of commandDef.phrases) {
                        this._commands[phrase.toLowerCase()] = commandDef.command;
                        this._allPhrases.push(phrase.toLowerCase());
                    }
                }
            }
            
            console.log(`Voice Assistant: Loaded ${this._allPhrases.length} command phrases`);
        } catch (e) {
            console.log(`Voice Assistant: Error loading commands: ${e}`);
        }
    }
    
    _setupSettingsHandlers() {
        // Listen for settings changes and update config file if auto-sync is enabled
        const syncableKeys = ['command-threshold', 'processing-interval', 'hotword'];
        
        syncableKeys.forEach(key => {
            this._settings.connect(`changed::${key}`, () => {
                if (this._settings.get_boolean('auto-sync')) {
                    this._configManager.syncSettingsToConfig();
                    // Reload config to get the updated values
                    this._config = this._configManager.getConfig();
                }
            });
        });
        
        // Also watch for auto-sync setting changes
        this._settings.connect('changed::auto-sync', () => {
            if (this._settings.get_boolean('auto-sync')) {
                this._configManager.syncSettingsToConfig();
            }
        });
    }
    
    _setupMenu() {
        // Current mode display
        this._modeItem = new PopupMenu.PopupMenuItem(`Mode: ${this._currentMode.toUpperCase()}`, {
            reactive: false
        });
        this.menu.addMenuItem(this._modeItem);
        
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        
        // Nerd-dictation control section
        this._controlItem = new PopupMenu.PopupMenuItem('Voice Assistant: Checking...', {
            reactive: false
        });
        this.menu.addMenuItem(this._controlItem);
        
        this._startItem = new PopupMenu.PopupMenuItem('Start Voice Assistant');
        this._startItem.connect('activate', () => this._startNerdDictation());
        this.menu.addMenuItem(this._startItem);

        this._stopItem = new PopupMenu.PopupMenuItem('Stop Voice Assistant');
        this._stopItem.connect('activate', () => this._stopNerdDictation());
        this.menu.addMenuItem(this._stopItem);

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
        
        // Update control status
        this._updateControlStatus();
        
        // Set up periodic status checking
        this._statusTimer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 5, () => {
            this._updateControlStatus();
            return GLib.SOURCE_CONTINUE;
        });
    }
    
    _setupFileWatchers() {
        try {
            // Watch mode file
            this._modeFile = Gio.File.new_for_path('/tmp/nerd-dictation.mode');
            this._modeMonitor = this._modeFile.monitor_file(Gio.FileMonitorFlags.NONE, null);
            this._modeMonitor.connect('changed', () => {
                GLib.timeout_add(GLib.PRIORITY_DEFAULT, 50, () => {
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
                        const oldMode = this._currentMode;
                        console.log(`Voice Assistant: Mode changed from ${oldMode} to ${newMode}`);
                        this._currentMode = newMode;
                        
                        // Show notification for mode change
                        this._showNotification('Voice Assistant', `Switched to ${newMode.toUpperCase()} mode`);
                        
                        // Clear buffer and timers on mode change
                        this._clearProcessingTimer();
                        this._clearBufferClearTimer();
                        this._clearBufferTimeoutTimer();
                        
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
                        console.log(`Voice Assistant: Raw buffer change detected: "${newBuffer}"`);
                        
                        // Additional check: if buffer was recently cleared and this is the same text,
                        // it might be from a suspend/resume cycle - ignore it
                        if (this._lastCommandTime && 
                            (Date.now() - this._lastCommandTime) < 2000 && 
                            this._lastExecutedText === newBuffer.toLowerCase()) {
                            console.log(`Voice Assistant: Ignoring duplicate text from suspend/resume cycle: "${newBuffer}"`);
                            return;
                        }
                        
                        // Clear existing debounce timer
                        if (this._debounceTimer) {
                            GLib.source_remove(this._debounceTimer);
                            this._debounceTimer = null;
                        }
                        
                        // Update buffer immediately
                        this._currentBuffer = newBuffer;
                        
                        // Set up debounced processing (process the current buffer, not the captured value)
                        this._debounceTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
                            this._processBufferChange();
                            this._debounceTimer = null;
                            return GLib.SOURCE_REMOVE;
                        });
                    }
                }
            } else {
                // Buffer file doesn't exist, clear buffer
                if (this._currentBuffer !== '') {
                    this._currentBuffer = '';
                    this._clearBufferTimeoutTimer();
                    this._updateDisplay();
                }
            }
        } catch (e) {
            console.log(`Voice Assistant: Error reading buffer file: ${e}`);
        }
    }
    
    _processBufferChange() {
        const now = Date.now();
        this._lastBufferUpdate = now;
        
        console.log(`Voice Assistant: Buffer updated (${this._currentMode} mode): "${this._currentBuffer}"`);
        
        // Clear all existing timers when new text arrives
        this._clearBufferTimeoutTimer();
        this._clearProcessingTimer();
        this._clearBufferClearTimer();
        
        // Process the buffer based on current mode
        this._processBuffer(this._currentBuffer);
        
        this._updateDisplay();
    }
    
    _processBuffer(text) {
        if (!text || text.trim() === '') {
            return;
        }
        
        // Clear any existing processing timer before setting a new one
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
        const words = text.toLowerCase().split(/\s+/);
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
        // Wait for the processing interval before checking commands
        const interval = (this._config.processing_interval || 1.5) * 1000;
        
        // Only set timer if one isn't already running for this text
        if (!this._processingTimer) {
            this._processingTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, interval, () => {
                this._executeCommandProcessing(text);
                this._processingTimer = null;
                return GLib.SOURCE_REMOVE;
            });
            
            console.log(`Voice Assistant: Scheduled command processing in ${interval}ms`);
        } else {
            console.log(`Voice Assistant: Processing timer already running, skipping`);
        }
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
            
            // Track the executed text and timestamp to prevent duplicate execution
            this._lastExecutedText = text.toLowerCase();
            this._lastCommandTime = Date.now();
            
            // Execute the command
            this._executeCommand(this._commands[bestMatch]);
        } else {
            console.log(`Voice Assistant: No matching command found (best: ${bestRatio}%)`);
            
            // Schedule buffer clear after another interval if no commands match
            const clearInterval = (this._config.processing_interval || 1.5) * 1000;
            this._scheduleBufferClear(clearInterval);
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
            
            // Show notification for command execution
            this._showNotification('Command Executed', `Running: ${command}`);
            
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
            this._showNotification('Command Error', `Failed to execute: ${command}`);
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
    
    _clearBufferTimeoutTimer() {
        if (this._bufferTimeoutTimer) {
            GLib.source_remove(this._bufferTimeoutTimer);
            this._bufferTimeoutTimer = null;
        }
    }
    
    _clearDebounceTimer() {
        if (this._debounceTimer) {
            GLib.source_remove(this._debounceTimer);
            this._debounceTimer = null;
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
            // Clear any pending processing timers when buffer is cleared
            this._clearProcessingTimer();
            this._clearBufferClearTimer();
            this._clearDebounceTimer();
            
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
        let iconName = 'radio-symbolic';
        let styleClass = 'system-status-icon';
        
        switch (this._currentMode) {
            case 'command':
                iconName = 'applications-system-symbolic';
                styleClass += ' voice-assistant-command';
                break;
            case 'typing':
                iconName = 'edit-symbolic';
                styleClass += ' voice-assistant-typing';
                break;
            default:
                iconName = 'radio-symbolic';
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

    _updateControlStatus() {
        try {
            // Check if nerd-dictation is running
            this._isNerdDictationRunning((isRunning) => {
                if (this._controlItem) {
                    this._controlItem.label.text = isRunning ? 
                        'Voice Assistant: Running' : 
                        'Voice Assistant: Stopped';
                }
                
                // Show/hide appropriate control items based on running status
                if (this._startItem) {
                    this._startItem.visible = !isRunning;
                }
                
                if (this._stopItem) {
                    this._stopItem.visible = isRunning;
                }
                
                // Update mode controls sensitivity based on running status
                const modeControlsEnabled = isRunning;
                if (this._normalModeItem) this._normalModeItem.setSensitive(modeControlsEnabled && this._currentMode !== 'normal');
                if (this._commandModeItem) this._commandModeItem.setSensitive(modeControlsEnabled && this._currentMode !== 'command');
                if (this._typingModeItem) this._typingModeItem.setSensitive(modeControlsEnabled && this._currentMode !== 'typing');
            });
        } catch (e) {
            console.log(`Voice Assistant: Error updating control status: ${e}`);
        }
    }

    _isNerdDictationRunning(callback) {
        try {
            // Check status file first
            const statusFile = Gio.File.new_for_path('/tmp/nerd-dictation.status');
            if (statusFile.query_exists(null)) {
                callback(true);
                return;
            }
            
            // Fallback: check for running process synchronously (use specific pattern)
            try {
                const [success, stdout] = GLib.spawn_command_line_sync('pgrep -f "nerd-dictation begin"');
                const isRunning = success && stdout.length > 0;
                callback(isRunning);
            } catch (e) {
                callback(false);
            }
        } catch (e) {
            callback(false);
        }
    }

    _startNerdDictation() {
        try {
            const scriptPath = GLib.get_home_dir() + '/.config/nerd-dictation/start-nerd.sh';
            const scriptFile = Gio.File.new_for_path(scriptPath);
            
            if (scriptFile.query_exists(null)) {
                console.log('Voice Assistant: Starting nerd-dictation via script');
                GLib.spawn_command_line_async(`${scriptPath}`);
                
                // Update status after a delay
                GLib.timeout_add(GLib.PRIORITY_DEFAULT, 2000, () => {
                    this._updateControlStatus();
                    return GLib.SOURCE_REMOVE;
                });
            } else {
                console.log('Voice Assistant: start-nerd.sh script not found');
                this._showNotification('Error', 'Start script not found at ' + scriptPath);
            }
        } catch (e) {
            console.log(`Voice Assistant: Error starting nerd-dictation: ${e}`);
            this._showNotification('Error', 'Failed to start voice assistant');
        }
    }

    _stopNerdDictation() {
        try {
            const scriptPath = GLib.get_home_dir() + '/.config/nerd-dictation/stop-nerd.sh';
            const scriptFile = Gio.File.new_for_path(scriptPath);
            
            if (scriptFile.query_exists(null)) {
                console.log('Voice Assistant: Stopping nerd-dictation via script');
                GLib.spawn_command_line_async(`${scriptPath}`);
                
                // Update status after a delay
                GLib.timeout_add(GLib.PRIORITY_DEFAULT, 2000, () => {
                    this._updateControlStatus();
                    return GLib.SOURCE_REMOVE;
                });
            } else {
                console.log('Voice Assistant: stop-nerd.sh script not found');
                this._showNotification('Error', 'Stop script not found at ' + scriptPath);
            }
        } catch (e) {
            console.log(`Voice Assistant: Error stopping nerd-dictation: ${e}`);
            this._showNotification('Error', 'Failed to stop voice assistant');
        }
    }

    _showNotification(title, message) {
        try {
            // Check if notifications are enabled in settings
            if (!this._settings.get_boolean('notification-enabled')) {
                return;
            }
            
            // Use notify-send for system notifications
            const command = ['notify-send', '--app-name=Voice Assistant', `--icon=audio-input-microphone-symbolic`, title, message];
            GLib.spawn_async(null, command, null, GLib.SpawnFlags.SEARCH_PATH, null);
            console.log(`Voice Assistant: Notification sent - ${title}: ${message}`);
        } catch (e) {
            console.log(`Voice Assistant: Notification error: ${e}`);
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
        this._clearBufferTimeoutTimer();
        this._clearDebounceTimer();
        
        if (this._statusTimer) {
            GLib.source_remove(this._statusTimer);
            this._statusTimer = null;
        }
        
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
