/**
 * LogViewer.js - Service log viewer
 * View voice assistant service logs in a proper window
 */

import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

export class LogViewer {
    constructor() {
        this._logFile = '/tmp/gnome_assistant.log';
    }

    /**
     * Create log viewer group for preferences
     */
    createLogViewerGroup(window) {
        const group = new Adw.PreferencesGroup({
            title: 'Service Logs',
            description: 'View and manage voice assistant service logs',
        });

        // Log file location
        const logPathRow = new Adw.ActionRow({
            title: 'Log File',
            subtitle: this._logFile,
        });

        const openLogButton = new Gtk.Button({
            icon_name: 'document-open-symbolic',
            valign: Gtk.Align.CENTER,
            tooltip_text: 'Open log file in text editor',
        });
        openLogButton.connect('clicked', () => this._openLogInEditor());
        logPathRow.add_suffix(openLogButton);

        group.add(logPathRow);

        // Systemd journal logs
        const journalRow = new Adw.ActionRow({
            title: 'Systemd Journal',
            subtitle: 'View complete service logs from systemd',
        });

        const viewJournalButton = new Gtk.Button({
            icon_name: 'utilities-terminal-symbolic',
            valign: Gtk.Align.CENTER,
            tooltip_text: 'View journal logs',
        });
        viewJournalButton.connect('clicked', () => this._viewJournalLogs(window));
        journalRow.add_suffix(viewJournalButton);

        group.add(journalRow);

        // Log info
        const logInfo = this._getLogInfo();
        if (logInfo.exists) {
            const infoRow = new Adw.ActionRow({
                title: 'Log Status',
                subtitle: `${logInfo.lines} lines • ${logInfo.size} • Last modified: ${logInfo.modified}`,
            });
            group.add(infoRow);
        } else {
            const infoRow = new Adw.ActionRow({
                title: 'Log Status',
                subtitle: 'No log file found - service may not be running',
            });
            group.add(infoRow);
        }

        // Actions
        const actionsBox = new Gtk.Box({
            orientation: Gtk.Orientation.HORIZONTAL,
            spacing: 12,
            margin_top: 12,
        });

        const viewButton = new Gtk.Button({
            label: 'View Logs',
            icon_name: 'document-open-symbolic',
            css_classes: ['suggested-action'],
        });
        viewButton.connect('clicked', () => this._showLogWindow(window));
        actionsBox.append(viewButton);

        const clearButton = new Gtk.Button({
            label: 'Clear Logs',
            icon_name: 'edit-clear-all-symbolic',
        });
        clearButton.connect('clicked', () => this._clearLogs(window));
        actionsBox.append(clearButton);

        const actionsRow = new Adw.ActionRow({
            title: 'Quick Actions',
        });
        actionsRow.add_suffix(actionsBox);
        group.add(actionsRow);

        return group;
    }

    /**
     * Get log file information
     */
    _getLogInfo() {
        try {
            const file = Gio.File.new_for_path(this._logFile);
            if (!file.query_exists(null)) {
                return { exists: false };
            }

            const info = file.query_info(
                'standard::size,time::modified',
                Gio.FileQueryInfoFlags.NONE,
                null
            );

            const size = info.get_size();
            const modified = info.get_modification_date_time();
            
            // Count lines
            const [success, contents] = file.load_contents(null);
            const lines = success ? contents.toString().split('\n').length : 0;

            return {
                exists: true,
                size: this._formatSize(size),
                lines: lines,
                modified: modified ? modified.format('%Y-%m-%d %H:%M:%S') : 'Unknown',
            };
        } catch (e) {
            console.error('Error getting log info:', e);
            return { exists: false };
        }
    }

    /**
     * Format file size
     */
    _formatSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    /**
     * Open log file in default text editor
     */
    _openLogInEditor() {
        try {
            GLib.spawn_command_line_async(`xdg-open "${this._logFile}"`);
        } catch (e) {
            console.error('Could not open log file:', e);
        }
    }

    /**
     * View journal logs (copy command to clipboard and show info)
     */
    _viewJournalLogs(window) {
        const command = 'journalctl --user -u gnome-assistant.service -f';
        
        // Copy to clipboard
        const display = window.get_display();
        const clipboard = display.get_clipboard();
        clipboard.set(command);

        const dialog = new Gtk.MessageDialog({
            modal: true,
            transient_for: window,
            message_type: Gtk.MessageType.INFO,
            buttons: Gtk.ButtonsType.CLOSE,
            text: 'View Systemd Journal Logs',
            secondary_text: `To view live service logs, run this command in a terminal:\n\n${command}\n\nThe command has been copied to your clipboard.`,
        });

        const contentArea = dialog.get_content_area();
        
        // Add button to open in terminal
        const openTerminalButton = new Gtk.Button({
            label: 'Open in Terminal',
            css_classes: ['suggested-action'],
        });
        openTerminalButton.connect('clicked', () => {
            this._openTerminalWithCommand(command);
            dialog.close();
        });
        contentArea.append(openTerminalButton);

        dialog.connect('response', () => dialog.close());
        dialog.present();
    }

    /**
     * Try to open terminal with command
     */
    _openTerminalWithCommand(command) {
        const terminals = [
            `gnome-terminal -- bash -c '${command}; exec bash'`,
            `konsole -e bash -c '${command}; exec bash'`,
            `xfce4-terminal -e "bash -c '${command}; exec bash'"`,
            `xterm -e bash -c '${command}; exec bash'`,
        ];

        for (const termCmd of terminals) {
            try {
                GLib.spawn_command_line_async(termCmd);
                return;
            } catch (e) {
                // Try next terminal
                continue;
            }
        }

        console.error('Could not find a suitable terminal emulator');
    }

    /**
     * Show log viewer window
     */
    _showLogWindow(window) {
        try {
            const file = Gio.File.new_for_path(this._logFile);
            if (!file.query_exists(null)) {
                this._showToast(window, 'Log file not found');
                return;
            }

            const [success, contents] = file.load_contents(null);
            if (!success) {
                this._showToast(window, 'Failed to read log file');
                return;
            }

            const logText = new TextDecoder().decode(contents);

            // Create dialog
            const dialog = new Adw.Window({
                modal: true,
                transient_for: window,
                default_width: 800,
                default_height: 600,
                title: 'Voice Assistant Logs',
            });

            const headerBar = new Adw.HeaderBar();
            
            const refreshButton = new Gtk.Button({
                icon_name: 'view-refresh-symbolic',
                tooltip_text: 'Refresh logs',
            });
            refreshButton.connect('clicked', () => {
                dialog.close();
                this._showLogWindow(window);
            });
            headerBar.pack_end(refreshButton);

            const box = new Gtk.Box({
                orientation: Gtk.Orientation.VERTICAL,
            });
            box.append(headerBar);

            // Text view with scrolling
            const scrolled = new Gtk.ScrolledWindow({
                vexpand: true,
                hexpand: true,
            });

            const textView = new Gtk.TextView({
                editable: false,
                monospace: true,
                wrap_mode: Gtk.WrapMode.WORD_CHAR,
                top_margin: 12,
                bottom_margin: 12,
                left_margin: 12,
                right_margin: 12,
            });

            const buffer = textView.get_buffer();
            buffer.set_text(logText, -1);

            // Scroll to bottom
            const mark = buffer.create_mark(null, buffer.get_end_iter(), false);
            textView.scroll_to_mark(mark, 0.0, true, 0.0, 1.0);

            scrolled.set_child(textView);
            box.append(scrolled);

            dialog.set_content(box);
            dialog.present();

        } catch (e) {
            console.error('Error showing log window:', e);
            this._showToast(window, `Error: ${e.message}`);
        }
    }

    /**
     * Clear log file
     */
    _clearLogs(window) {
        const dialog = new Gtk.MessageDialog({
            modal: true,
            transient_for: window,
            message_type: Gtk.MessageType.QUESTION,
            buttons: Gtk.ButtonsType.YES_NO,
            text: 'Clear Log File?',
            secondary_text: 'This will delete all log entries. This action cannot be undone.',
        });

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.YES) {
                try {
                    GLib.spawn_command_line_sync(`truncate -s 0 ${this._logFile}`);
                    this._showToast(window, 'Logs cleared');
                } catch (e) {
                    this._showToast(window, `Failed to clear logs: ${e.message}`);
                }
            }
            dialog.close();
        });

        dialog.present();
    }

    /**
     * Show toast notification
     */
    _showToast(window, message) {
        console.log(`LogViewer: ${message}`);
        try {
            const toast = new Adw.Toast({
                title: message,
                timeout: 3,
            });
            window.add_toast(toast);
        } catch (e) {
            console.log(`Toast: ${message}`);
        }
    }
}
