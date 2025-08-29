/**
 * ConfigManager.js - Configuration management utilities
 * Handles loading, saving, and synchronizing configuration between extension and files
 */

import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

export class ConfigManager {
    constructor(settings) {
        this._settings = settings;
        this._configPath = GLib.get_home_dir() + '/.config/nerd-dictation/config.json';
        this._configFile = Gio.File.new_for_path(this._configPath);
        this._config = null;
    }

    /**
     * Load configuration from file
     */
    loadConfig() {
        try {
            if (this._configFile.query_exists(null)) {
                let [success, contents] = this._configFile.load_contents(null);
                if (success) {
                    this._config = JSON.parse(new TextDecoder().decode(contents));
                    return this._config;
                }
            }
            return this._getDefaultConfig();
        } catch (e) {
            console.log(`ConfigManager: Error loading config: ${e}`);
            return this._getDefaultConfig();
        }
    }

    /**
     * Save configuration to file
     */
    saveConfig(config) {
        try {
            // Ensure parent directory exists
            const parentDir = this._configFile.get_parent();
            if (!parentDir.query_exists(null)) {
                parentDir.make_directory_with_parents(null);
            }

            const configJson = JSON.stringify(config, null, 2);
            this._configFile.replace_contents(configJson, null, false, Gio.FileCreateFlags.NONE, null);
            this._config = config;
            return true;
        } catch (e) {
            console.log(`ConfigManager: Error saving config: ${e}`);
            return false;
        }
    }

    /**
     * Get current config (load if needed)
     */
    getConfig() {
        if (!this._config) {
            this._config = this.loadConfig();
        }
        return this._config;
    }

    /**
     * Update specific config section
     */
    updateConfigSection(section, data) {
        const config = this.getConfig();
        config[section] = data;
        return this.saveConfig(config);
    }

    /**
     * Sync extension settings to config file
     */
    syncSettingsToConfig() {
        const config = this.getConfig();
        
        // Update basic settings
        config.hotword = this._settings.get_string('hotword');
        config.command_threshold = this._settings.get_int('command-threshold');
        config.processing_interval = this._settings.get_double('processing-interval');

        return this.saveConfig(config);
    }

    /**
     * Sync config file to extension settings
     */
    syncConfigToSettings() {
        const config = this.getConfig();
        
        this._settings.set_string('hotword', config.hotword || 'hey');
        this._settings.set_int('command-threshold', config.command_threshold || 80);
        this._settings.set_double('processing-interval', config.processing_interval || 1.5);
    }

    /**
     * Get default configuration structure
     */
    _getDefaultConfig() {
        return {
            "hotword": "hey",
            "command_threshold": 80,
            "processing_interval": 1.5,
            "logging": {
                "level": "INFO",
                "file": "/tmp/voice_assistant.log"
            },
            "commands": {
                "applications": {
                    "terminal": ["open terminal", "start terminal", "launch terminal"],
                    "firefox": ["open firefox", "launch firefox", "start web browser"],
                    "files": ["open files", "launch files", "start file manager"],
                    "spotify": ["open spotify", "launch spotify", "start music"],
                    "code": ["open code", "launch code", "start vscode"],
                    "calculator": ["open calculator", "launch calculator"]
                },
                "window_management": {
                    "show_overview": ["show overview", "show windows"],
                    "move_left": ["move left", "go left", "left desktop"],
                    "move_right": ["move right", "go right", "right desktop"],
                    "switch_window": ["switch window", "next window"],
                    "new_tab": ["new tab", "next tab"],
                    "close_window": ["close window", "close tab"],
                    "minimize": ["minimize window", "minimize"],
                    "maximize": ["maximize window", "maximize"]
                },
                "text_editing": {
                    "copy": ["copy", "copy text"],
                    "paste": ["paste", "paste text"],
                    "cut": ["cut", "cut text"],
                    "undo": ["undo", "undo last"],
                    "redo": ["redo", "redo last"],
                    "select_all": ["select all", "select everything"]
                },
                "system": {
                    "volume_up": ["volume up", "turn up the volume", "increase volume"],
                    "volume_down": ["volume down", "turn down the volume", "decrease volume"],
                    "mute": ["mute", "mute audio", "silence"],
                    "lock_screen": ["lock screen", "lock my screen"],
                    "screenshot": ["screenshot", "take screenshot"],
                    "sleep": ["sleep", "suspend"]
                },
                "modes": {
                    "typing_mode": ["go to typing mode", "typing mode", "start typing"],
                    "normal_mode": ["go to normal mode", "normal mode", "stop typing", "exit typing"],
                    "command_mode": ["go to command mode", "command mode"],
                    "cancel": ["cancel", "stop", "nevermind"]
                }
            }
        };
    }
}
