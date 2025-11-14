/**
 * GNOME Assistant Preferences
 * Configuration UI for D-Bus service parameters and command management
 */

import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

// Import our modular components
import {ConfigManager} from './lib/ConfigManager.js';
import {CommandManager} from './lib/CommandEditor.js';
import {PreferencesBuilder, StatusManager} from './lib/PreferencesWidgets.js';
import {WhisperModelManager} from './lib/WhisperModelManager.js';
import {LogViewer} from './lib/LogViewer.js';

export default class VoiceAssistantExtensionPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();
        
        // Initialize managers
        this._configManager = new ConfigManager(settings);
        this._commandManager = new CommandManager(this._configManager);
        this._prefsBuilder = new PreferencesBuilder(settings);
        this._statusManager = new StatusManager();
        this._modelManager = new WhisperModelManager();
        this._logViewer = new LogViewer();
        
        // Create pages
        this._createGeneralPage(window, settings);
        this._createModelsPage(window, settings);
        this._createCommandsPage(window, settings);
        this._createLogsPage(window, settings);
        this._createAboutPage(window, settings);
    }

    _createGeneralPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'General',
            icon_name: 'preferences-system-symbolic',
        });

        // Voice Recognition Settings group
        const recognitionGroup = this._prefsBuilder.createGroup(
            'Voice Recognition',
            'Configure voice command processing parameters via D-Bus service'
        );

        this._prefsBuilder.createEntryRow(
            'Activation Hotword',
            'Word used to activate command mode from normal mode',
            'hotword',
            'hey',
            recognitionGroup
        );

        this._prefsBuilder.createSpinButtonRow(
            'Command Threshold',
            'Minimum confidence percentage to execute commands (50-100%)',
            'command-threshold',
            50, 100, 5,
            recognitionGroup
        );

        this._prefsBuilder.createDoubleSpinButtonRow(
            'Processing Interval',
            'Time to wait before processing speech (0.5-5.0 seconds)',
            'processing-interval',
            0.5, 5.0, 0.1, 1,
            recognitionGroup
        );

        page.add(recognitionGroup);

        // Interface Settings group
        const interfaceGroup = this._prefsBuilder.createGroup(
            'Interface Settings',
            'Configure extension display and refresh behavior'
        );

        this._prefsBuilder.createSpinButtonRow(
            'Status Update Interval',
            'How often to refresh D-Bus status display (1-10 seconds)',
            'update-interval',
            1, 10, 1,
            interfaceGroup
        );

        page.add(interfaceGroup);

        // D-Bus Service Control group
        const serviceGroup = this._prefsBuilder.createGroup(
            'D-Bus Service Control',
            'Manage synchronization with gnome assistant service'
        );

        this._prefsBuilder.createButtonRow(
            'Sync to Service',
            'Push current settings to the D-Bus service configuration',
            'Sync Now',
            'document-save-symbolic',
            () => {
                this._configManager.syncSettingsToConfig();
                this._showToast(window, 'Settings synced to D-Bus service');
            },
            serviceGroup
        );

        this._prefsBuilder.createButtonRow(
            'Load from Service',
            'Load configuration from D-Bus service to extension settings',
            'Load from Service',
            'document-open-symbolic',
            () => {
                this._configManager.syncConfigToSettings();
                this._showToast(window, 'Configuration loaded from service');
            },
            serviceGroup
        );

        page.add(serviceGroup);

        // Status group
        const statusGroup = this._prefsBuilder.createGroup(
            'Status',
            'Current voice recognition configuration'
        );

        const configStatus = this._statusManager.checkConfigStatus();
        const statusText = configStatus.exists ? 
            `Configuration file: ${configStatus.path}` :
            'Configuration file not found - will be created by service';

        this._prefsBuilder.createInfoRow(
            'Configuration',
            statusText,
            statusGroup
        );

        if (configStatus.exists && configStatus.lastModified) {
            this._prefsBuilder.createInfoRow(
                'Last Modified',
                this._statusManager.formatTimestamp(configStatus.lastModified),
                statusGroup
            );
        }

        page.add(statusGroup);
        window.add(page);
    }

    _createLogsPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'Logs',
            icon_name: 'text-x-generic-symbolic',
        });

        // Add log viewer group from LogViewer
        const logGroup = this._logViewer.createLogViewerGroup(window);
        page.add(logGroup);

        // Log configuration group
        const configGroup = this._prefsBuilder.createGroup(
            'Log Configuration',
            'Logging settings and information'
        );

        this._prefsBuilder.createInfoRow(
            'Log Location',
            'Service logs are written to /tmp/gnome_assistant.log',
            configGroup
        );

        this._prefsBuilder.createInfoRow(
            'Systemd Journal',
            'Complete service logs (including stdout/stderr) are available via systemd journal',
            configGroup
        );

        this._prefsBuilder.createInfoRow(
            'Log Rotation',
            'Log files in /tmp are automatically cleared on system reboot',
            configGroup
        );

        page.add(configGroup);

        window.add(page);
    }

    _createModelsPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'Models',
            icon_name: 'folder-download-symbolic',
        });

        // Add model management group from WhisperModelManager
        const modelGroup = this._modelManager.createModelGroup(window);
        page.add(modelGroup);

        // Model information group
        const infoGroup = this._prefsBuilder.createGroup(
            'Model Information',
            'Understanding whisper.cpp models for speech recognition'
        );

        this._prefsBuilder.createInfoRow(
            'Model Selection',
            'The C++ service automatically uses models from the model directory. Restart the service after downloading new models.',
            infoGroup
        );

        this._prefsBuilder.createInfoRow(
            'Recommended Models',
            'tiny.en: Best balance of speed and accuracy for English • base.en: Better accuracy, slower • small.en: High accuracy, requires more resources',
            infoGroup
        );

        this._prefsBuilder.createInfoRow(
            'Model Source',
            'Models are downloaded from Hugging Face (ggerganov/whisper.cpp repository)',
            infoGroup
        );

        page.add(infoGroup);

        // Service restart info
        const restartGroup = this._prefsBuilder.createGroup(
            'Apply Changes',
            'Service must be restarted to use a different model'
        );

        this._prefsBuilder.createButtonRow(
            'Restart Service',
            'Restart the gnome assistant service to apply model changes',
            'Restart Now',
            'view-refresh-symbolic',
            () => {
                try {
                    GLib.spawn_command_line_async('systemctl --user restart gnome-assistant.service');
                    this._showToast(window, 'Restarting gnome assistant service...');
                } catch (e) {
                    this._showToast(window, 'Failed to restart service');
                }
            },
            restartGroup
        );

        page.add(restartGroup);
        window.add(page);
    }

    
    _createCommandsPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'Commands',
            icon_name: 'utilities-terminal-symbolic',
        });

        // Statistics group
        const statsGroup = this._prefsBuilder.createGroup(
            'Command Statistics',
            'Overview of your current voice commands'
        );

        const stats = this._getCommandStats();
        this._prefsBuilder.createInfoRow(
            'Total Commands',
            `${stats.totalCommands} commands configured`,
            statsGroup
        );

        this._prefsBuilder.createInfoRow(
            'Total Phrases',
            `${stats.totalPhrases} voice phrases available`,
            statsGroup
        );

        page.add(statsGroup);

        // Commands management group
        const commandsGroup = this._commandManager.createCommandsGroup();
        page.add(commandsGroup);

        // Actions group
        const actionsGroup = this._prefsBuilder.createGroup(
            'Command Actions',
            'Manage your voice command configuration'
        );

        this._prefsBuilder.createButtonRow(
            'Reset to Defaults',
            'Restore all commands to default configuration',
            'Reset Commands',
            'edit-clear-all-symbolic',
            () => this._showResetConfirmation(window),
            actionsGroup
        );

        this._prefsBuilder.createButtonRow(
            'Open Config Directory',
            'Open configuration directory in file manager',
            'Open Directory',
            'folder-open-symbolic',
            () => this._openConfigDirectory(),
            actionsGroup
        );

        page.add(actionsGroup);
        window.add(page);
    }

    _getCommandStats() {
        const config = this._configManager.getConfig();
        const commands = config.commands || [];
        
        const totalCommands = commands.length;
        const totalPhrases = commands.reduce((sum, cmd) => {
            return sum + (cmd.phrases ? cmd.phrases.length : 0);
        }, 0);

        return {
            totalCommands,
            totalPhrases
        };
    }

    _createAboutPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'About',
            icon_name: 'help-info-symbolic',
        });

        // Info group
        const infoGroup = this._prefsBuilder.createGroup(
            'GNOME Assistant with Whisper.cpp',
            'Modern D-Bus-based voice control system for GNOME with offline speech recognition'
        );

        this._prefsBuilder.createInfoRow(
            'Features',
            'Offline whisper.cpp recognition • D-Bus integration • Real-time mode display • Wayland ydotool support',
            infoGroup
        );

        this._prefsBuilder.createInfoRow(
            'Technology',
            'C++ D-Bus service • Whisper tiny.en model • Configurable confidence thresholds • PulseAudio/PipeWire capture',
            infoGroup
        );

        this._prefsBuilder.createInfoRow(
            'Usage',
            'Say "hey" to activate • Speak commands • Extension shows live recognition buffer',
            infoGroup
        );

        this._prefsBuilder.createInfoRow(
            'Mode Indicators',
            'Normal: Microphone (listening for hotword) • Command: Red pulsing (processing commands) • Typing: Keyboard (speech-to-text)',
            infoGroup
        );

        page.add(infoGroup);

        // D-Bus Service group
        const serviceGroup = this._prefsBuilder.createGroup(
            'D-Bus Service',
            'Information about the gnome assistant D-Bus service'
        );

        this._prefsBuilder.createInfoRow(
            'Service Name',
            'com.github.saim.GnomeAssistant',
            serviceGroup
        );

        this._prefsBuilder.createInfoRow(
            'Object Path',
            '/com/github/saim/VoiceAssistant',
            serviceGroup
        );

        this._prefsBuilder.createInfoRow(
            'Service Control',
            'Use systemctl --user {start|stop|restart|status} gnome-assistant.service',
            serviceGroup
        );

        page.add(serviceGroup);

        // Support group
        const supportGroup = this._prefsBuilder.createGroup(
            'Support & Resources',
            'Get help and additional information'
        );

        this._prefsBuilder.createButtonRow(
            'Documentation',
            'View the complete documentation and setup guide',
            'View Docs',
            'text-x-readme-symbolic',
            () => this._openDocumentation(),
            supportGroup
        );

        this._prefsBuilder.createButtonRow(
            'Report Issue',
            'Report a bug or request a new feature',
            'Report Issue',
            'bug-symbolic',
            () => this._openIssueTracker(),
            supportGroup
        );

        page.add(supportGroup);
        window.add(page);
    }

    // Helper methods
    _showResetConfirmation(window) {
        const dialog = new Gtk.MessageDialog({
            modal: true,
            transient_for: window,
            message_type: Gtk.MessageType.QUESTION,
            buttons: Gtk.ButtonsType.YES_NO,
            text: 'Reset Commands to Defaults?',
            secondary_text: 'This will restore all commands to their default configuration. Custom commands will be lost. This action cannot be undone.',
        });

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.YES) {
                this._configManager.saveConfig(this._configManager._getDefaultConfig());
                this._showToast(window, 'Commands reset to defaults');
            }
            dialog.close();
        });

        dialog.present();
    }

    _openConfigDirectory() {
        try {
            const configDir = GLib.get_home_dir() + '/.config/gnome-assistant';
            GLib.spawn_command_line_async(`nautilus "${configDir}"`);
        } catch (e) {
            console.log('Could not open config directory');
        }
    }

    _openDocumentation() {
        try {
            GLib.spawn_command_line_async('xdg-open https://github.com/Saim20/gnome-assistant');
        } catch (e) {
            console.log('Could not open documentation');
        }
    }

    _openIssueTracker() {
        try {
            GLib.spawn_command_line_async('xdg-open https://github.com/Saim20/gnome-assistant/issues');
        } catch (e) {
            console.log('Could not open issue tracker');
        }
    }

    _showToast(window, message) {
        // Simple console log for compatibility
        console.log(`GNOME Assistant: ${message}`);
        
        // Try to show a toast if available
        try {
            const toast = new Adw.Toast({
                title: message,
                timeout: 3,
            });
            window.add_toast(toast);
        } catch (e) {
            // Fallback: just log
            console.log(`Toast: ${message}`);
        }
    }
}