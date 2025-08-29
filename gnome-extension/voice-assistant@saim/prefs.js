/**
 * Enhanced Voice Assistant Preferences
 * Modular, extensible preferences with command editing capabilities
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

export default class VoiceAssistantExtensionPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();
        
        // Initialize managers
        this._configManager = new ConfigManager(settings);
        this._commandManager = new CommandManager(this._configManager);
        this._prefsBuilder = new PreferencesBuilder(settings);
        this._statusManager = new StatusManager();
        
        // Set up auto-sync if enabled
        this._setupAutoSync(settings);
        
        // Create pages
        this._createGeneralPage(window, settings);
        this._createVoiceRecognitionPage(window, settings);
        this._createCommandsPage(window, settings);
        this._createAdvancedPage(window, settings);
        this._createAboutPage(window, settings);
    }

    _setupAutoSync(settings) {
        if (settings.get_boolean('auto-sync')) {
            // Sync config to settings on startup
            this._configManager.syncConfigToSettings();
            
            // Listen for settings changes and sync to config
            const syncableKeys = ['hotword', 'command-threshold', 'processing-interval'];
            syncableKeys.forEach(key => {
                settings.connect(`changed::${key}`, () => {
                    if (settings.get_boolean('auto-sync')) {
                        this._configManager.syncSettingsToConfig();
                    }
                });
            });
        }
    }

    _createGeneralPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'General',
            icon_name: 'preferences-system-symbolic',
        });

        // Interface group
        const interfaceGroup = this._prefsBuilder.createGroup(
            'Interface', 
            'Customize the extension appearance and behavior'
        );

        this._prefsBuilder.createSwitchRow(
            'Show Mode Label',
            'Display text label next to the microphone icon',
            'show-label',
            interfaceGroup
        );

        this._prefsBuilder.createSwitchRow(
            'Enable Notifications',
            'Show notifications for mode changes and command recognition',
            'notification-enabled',
            interfaceGroup
        );

        page.add(interfaceGroup);

        // Basic Settings group
        const basicGroup = this._prefsBuilder.createGroup(
            'Basic Settings',
            'Configure core voice assistant settings'
        );

        this._prefsBuilder.createEntryRow(
            'Activation Hotword',
            'Word used to activate command mode from normal mode',
            'hotword',
            'hey',
            basicGroup
        );

        this._prefsBuilder.createSpinButtonRow(
            'Update Interval',
            'How often to check for file changes (1-10 seconds)',
            'update-interval',
            1, 10, 1,
            basicGroup
        );

        page.add(basicGroup);

        // Sync group
        const syncGroup = this._prefsBuilder.createGroup(
            'Configuration Sync',
            'Manage synchronization between extension and configuration file'
        );

        this._prefsBuilder.createSwitchRow(
            'Auto-sync Configuration',
            'Automatically sync changes between extension and config file',
            'auto-sync',
            syncGroup
        );

        this._prefsBuilder.createButtonRow(
            'Sync Now',
            'Manually sync extension settings to configuration file',
            'Sync to File',
            'document-save-symbolic',
            () => {
                this._configManager.syncSettingsToConfig();
                this._showToast(window, 'Configuration synced to file');
            },
            syncGroup
        );

        this._prefsBuilder.createButtonRow(
            'Load from File',
            'Load configuration from file to extension settings',
            'Load from File',
            'document-open-symbolic',
            () => {
                this._configManager.syncConfigToSettings();
                this._showToast(window, 'Configuration loaded from file');
            },
            syncGroup
        );

        page.add(syncGroup);
        window.add(page);
    }

    _createVoiceRecognitionPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'Voice Recognition',
            icon_name: 'audio-input-microphone-symbolic',
        });

        // Recognition Settings group
        const recognitionGroup = this._prefsBuilder.createGroup(
            'Recognition Settings',
            'Configure voice command processing parameters'
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

        // Status group
        const statusGroup = this._prefsBuilder.createGroup(
            'Status',
            'Current voice recognition status and configuration'
        );

        const configStatus = this._statusManager.checkConfigStatus();
        const statusText = configStatus.exists ? 
            `Configuration file found at ${configStatus.path}` :
            'Configuration file not found - will be created automatically';

        this._prefsBuilder.createInfoRow(
            'Configuration File',
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

        // Commands management group using new simplified system
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
            'Export Commands',
            'Export your command configuration to a file',
            'Export',
            'document-save-symbolic',
            () => this._exportCommands(window),
            actionsGroup
        );

        this._prefsBuilder.createButtonRow(
            'Import Commands',
            'Import command configuration from a file',
            'Import',
            'document-open-symbolic',
            () => this._importCommands(window),
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

    _createAdvancedPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'Advanced',
            icon_name: 'applications-engineering-symbolic',
        });

        // Debug group
        const debugGroup = this._prefsBuilder.createGroup(
            'Debug & Troubleshooting',
            'Advanced options for debugging and troubleshooting'
        );

        this._prefsBuilder.createSwitchRow(
            'Debug Mode',
            'Enable verbose logging for troubleshooting issues',
            'debug-mode',
            debugGroup
        );

        this._prefsBuilder.createButtonRow(
            'View Logs',
            'Open the voice assistant log file for inspection',
            'View Logs',
            'text-x-generic-symbolic',
            () => this._openLogFile(),
            debugGroup
        );

        this._prefsBuilder.createButtonRow(
            'Clear Logs',
            'Clear the current log file contents',
            'Clear Logs',
            'edit-clear-symbolic',
            () => this._clearLogs(window),
            debugGroup
        );

        page.add(debugGroup);

        // File Management group
        const fileGroup = this._prefsBuilder.createGroup(
            'File Management',
            'Manage configuration and temporary files'
        );

        this._prefsBuilder.createButtonRow(
            'Open Config Directory',
            'Open the configuration directory in file manager',
            'Open Directory',
            'folder-open-symbolic',
            () => this._openConfigDirectory(),
            fileGroup
        );

        this._prefsBuilder.createButtonRow(
            'Reset Configuration',
            'Reset all configuration to default values',
            'Reset Config',
            'edit-undo-symbolic',
            () => this._showConfigResetConfirmation(window),
            fileGroup
        );

        page.add(fileGroup);
        window.add(page);
    }

    _createAboutPage(window, settings) {
        const page = new Adw.PreferencesPage({
            title: 'About',
            icon_name: 'help-info-symbolic',
        });

        // Info group
        const infoGroup = this._prefsBuilder.createGroup(
            'Voice Assistant Extension',
            'Advanced voice control system for GNOME'
        );

        this._prefsBuilder.createInfoRow(
            'Features',
            'Real-time mode display • Automatic command processing • Configurable thresholds • Command editing',
            infoGroup
        );

        this._prefsBuilder.createInfoRow(
            'Usage',
            'Click the microphone icon to switch modes or adjust settings here',
            infoGroup
        );

        this._prefsBuilder.createInfoRow(
            'Mode Indicators',
            'Normal: White microphone • Command: Red microphone • Typing: Blue keyboard',
            infoGroup
        );

        page.add(infoGroup);

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
    _addNewCategoryButton(group, window, statsGroup) {
        const newCategoryRow = new Adw.ActionRow({
            title: 'Add New Category',
            subtitle: 'Create a new command category',
        });

        const addButton = new Gtk.Button({
            icon_name: 'list-add-symbolic',
            valign: Gtk.Align.CENTER,
            css_classes: ['flat'],
        });

        addButton.connect('clicked', () => {
            this._showNewCategoryDialog(window, group, statsGroup);
        });

        newCategoryRow.add_suffix(addButton);
        group.add(newCategoryRow);
    }

    _showNewCategoryDialog(window, group, statsGroup) {
        const dialog = new Gtk.Dialog({
            title: 'Add New Category',
            modal: true,
            transient_for: window,
        });

        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL);
        dialog.add_button('Add', Gtk.ResponseType.OK);

        const content = dialog.get_content_area();
        content.set_spacing(12);
        content.set_margin_top(12);
        content.set_margin_bottom(12);
        content.set_margin_start(12);
        content.set_margin_end(12);

        const entry = new Gtk.Entry({
            placeholder_text: 'Category name (e.g., "my_custom_commands")',
        });

        const group_widget = new Adw.PreferencesGroup({
            title: 'Category Name',
        });
        const row = new Adw.ActionRow({
            title: 'Name',
        });
        row.add_suffix(entry);
        group_widget.add(row);

        content.append(group_widget);

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.OK) {
                const categoryName = entry.get_text().trim();
                if (categoryName) {
                    this._commandManager.addCategory(categoryName);
                    this._refreshCommandsPage(group, statsGroup, window);
                    this._showToast(window, `Category "${categoryName}" added`);
                }
            }
            dialog.close();
        });

        dialog.present();
    }

    _refreshCommandStats(statsGroup, window) {
        // Update statistics display
        const stats = this._commandManager.getStats();
        // Note: In a real implementation, we'd need to rebuild the stats group
        // For now, we'll just show a toast
        this._showToast(window, 'Commands updated');
    }

    _refreshCommandsPage(group, statsGroup, window) {
        // Rebuild the commands page
        // In a real implementation, this would refresh the entire commands section
        this._showToast(window, 'Commands page refreshed');
    }

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

    _showConfigResetConfirmation(window) {
        const dialog = new Gtk.MessageDialog({
            modal: true,
            transient_for: window,
            message_type: Gtk.MessageType.WARNING,
            buttons: Gtk.ButtonsType.YES_NO,
            text: 'Reset All Configuration?',
            secondary_text: 'This will reset ALL settings and commands to their default values. This action cannot be undone.',
        });

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.YES) {
                this._configManager.saveConfig(this._configManager._getDefaultConfig());
                this._configManager.syncConfigToSettings();
                this._showToast(window, 'Configuration reset to defaults');
            }
            dialog.close();
        });

        dialog.present();
    }

    _exportCommands(window) {
        const config = this._configManager.getConfig();
        const exportData = {
            version: "1.0",
            exported: new Date().toISOString(),
            commands: config.commands || {}
        };

        try {
            const exportPath = GLib.get_home_dir() + '/voice-assistant-commands-export.json';
            const file = Gio.File.new_for_path(exportPath);
            file.replace_contents(JSON.stringify(exportData, null, 2), null, false, Gio.FileCreateFlags.NONE, null);
            this._showToast(window, `Commands exported to ${exportPath}`);
        } catch (e) {
            this._showToast(window, `Export failed: ${e.message}`);
        }
    }

    _importCommands(window) {
        // In a real implementation, this would open a file chooser
        this._showToast(window, 'Import feature not implemented yet');
    }

    _openLogFile() {
        try {
            GLib.spawn_command_line_async('gnome-text-editor /tmp/voice_assistant.log');
        } catch (e) {
            try {
                GLib.spawn_command_line_async('gedit /tmp/voice_assistant.log');
            } catch (e2) {
                console.log('Could not open log file');
            }
        }
    }

    _clearLogs(window) {
        try {
            const logFile = Gio.File.new_for_path('/tmp/voice_assistant.log');
            if (logFile.query_exists(null)) {
                logFile.replace_contents('', null, false, Gio.FileCreateFlags.NONE, null);
                this._showToast(window, 'Logs cleared');
            }
        } catch (e) {
            this._showToast(window, 'Failed to clear logs');
        }
    }

    _openConfigDirectory() {
        try {
            const configDir = GLib.get_home_dir() + '/.config/nerd-dictation';
            GLib.spawn_command_line_async(`nautilus "${configDir}"`);
        } catch (e) {
            console.log('Could not open config directory');
        }
    }

    _openDocumentation() {
        try {
            GLib.spawn_command_line_async('xdg-open https://github.com/Saim20/voice-assistant');
        } catch (e) {
            console.log('Could not open documentation');
        }
    }

    _openIssueTracker() {
        try {
            GLib.spawn_command_line_async('xdg-open https://github.com/Saim20/voice-assistant/issues');
        } catch (e) {
            console.log('Could not open issue tracker');
        }
    }

    _showToast(window, message) {
        // In GNOME 42+, we could use Adw.Toast
        // For now, we'll use a simple console log
        console.log(`Voice Assistant: ${message}`);
        
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