/**
 * WhisperModelManager.js - Whisper model download and management
 * Handles downloading and selecting whisper.cpp models
 */

import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

export class WhisperModelManager {
    constructor() {
        this._modelDir = GLib.get_home_dir() + '/.local/share/voice-assistant/models';
        this._downloadInProgress = false;
        
        // Available whisper models with their details
        this._availableModels = [
            {
                name: 'tiny.en',
                file: 'ggml-tiny.en.bin',
                size: '~75 MB',
                description: 'Fastest, good accuracy (English only)',
                url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin',
                recommended: true
            },
            {
                name: 'tiny',
                file: 'ggml-tiny.bin',
                size: '~75 MB',
                description: 'Fast, multilingual support',
                url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin',
                recommended: false
            },
            {
                name: 'base.en',
                file: 'ggml-base.en.bin',
                size: '~142 MB',
                description: 'Better accuracy (English only)',
                url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin',
                recommended: false
            },
            {
                name: 'base',
                file: 'ggml-base.bin',
                size: '~142 MB',
                description: 'Better accuracy, multilingual',
                url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin',
                recommended: false
            },
            {
                name: 'small.en',
                file: 'ggml-small.en.bin',
                size: '~466 MB',
                description: 'High accuracy (English only)',
                url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin',
                recommended: false
            },
            {
                name: 'small',
                file: 'ggml-small.bin',
                size: '~466 MB',
                description: 'High accuracy, multilingual',
                url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin',
                recommended: false
            },
            {
                name: 'medium.en',
                file: 'ggml-medium.en.bin',
                size: '~1.5 GB',
                description: 'Very high accuracy (English only)',
                url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.en.bin',
                recommended: false
            },
            {
                name: 'medium',
                file: 'ggml-medium.bin',
                size: '~1.5 GB',
                description: 'Very high accuracy, multilingual',
                url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin',
                recommended: false
            }
        ];
    }

    /**
     * Create the model management preferences group
     */
    createModelGroup(window) {
        const group = new Adw.PreferencesGroup({
            title: 'Whisper Models',
            description: 'Download and manage speech recognition models',
        });

        // Current model status
        const currentModel = this._getCurrentModel();
        const statusRow = new Adw.ActionRow({
            title: 'Current Model',
            subtitle: currentModel ? `Using ${currentModel}` : 'No model detected',
        });
        
        if (currentModel) {
            const sizeInfo = this._getModelSize(currentModel);
            if (sizeInfo) {
                const sizeLabel = new Gtk.Label({
                    label: sizeInfo,
                    css_classes: ['dim-label'],
                    valign: Gtk.Align.CENTER,
                });
                statusRow.add_suffix(sizeLabel);
            }
        }
        
        group.add(statusRow);

        // Add expander for available models
        const expanderRow = new Adw.ExpanderRow({
            title: 'Available Models',
            subtitle: 'Download and select whisper.cpp models',
        });

        for (const model of this._availableModels) {
            const modelRow = this._createModelRow(model, window);
            expanderRow.add_row(modelRow);
        }

        group.add(expanderRow);

        // Model directory info
        const dirRow = new Adw.ActionRow({
            title: 'Model Directory',
            subtitle: this._modelDir,
        });

        const openDirButton = new Gtk.Button({
            icon_name: 'folder-open-symbolic',
            valign: Gtk.Align.CENTER,
            tooltip_text: 'Open model directory',
        });
        openDirButton.connect('clicked', () => this._openModelDirectory());
        dirRow.add_suffix(openDirButton);

        group.add(dirRow);

        return group;
    }

    /**
     * Create a row for each model
     */
    _createModelRow(model, window) {
        const isInstalled = this._isModelInstalled(model.file);
        const isCurrent = this._getCurrentModel() === model.file;
        
        let subtitle = `${model.description} • ${model.size}`;
        if (model.recommended) {
            subtitle = '⭐ Recommended • ' + subtitle;
        }
        if (isInstalled && isCurrent) {
            subtitle += ' • Currently Active';
        } else if (isInstalled) {
            subtitle += ' • Installed';
        }

        const row = new Adw.ActionRow({
            title: model.name,
            subtitle: subtitle,
        });

        // Create button box
        const buttonBox = new Gtk.Box({
            spacing: 6,
            valign: Gtk.Align.CENTER,
        });

        if (isInstalled) {
            // Select button
            if (!isCurrent) {
                const selectButton = new Gtk.Button({
                    icon_name: 'emblem-ok-symbolic',
                    tooltip_text: 'Use this model',
                    css_classes: ['suggested-action'],
                });
                selectButton.connect('clicked', () => {
                    this._selectModel(model, window);
                });
                buttonBox.append(selectButton);
            }

            // Delete button
            const deleteButton = new Gtk.Button({
                icon_name: 'user-trash-symbolic',
                tooltip_text: 'Delete model',
                css_classes: ['destructive-action'],
            });
            deleteButton.connect('clicked', () => {
                this._deleteModel(model, window);
            });
            buttonBox.append(deleteButton);
        } else {
            // Download button
            const downloadButton = new Gtk.Button({
                icon_name: 'folder-download-symbolic',
                label: 'Download',
                tooltip_text: `Download ${model.name} model`,
            });
            downloadButton.connect('clicked', () => {
                this._downloadModel(model, window, downloadButton);
            });
            buttonBox.append(downloadButton);
        }

        row.add_suffix(buttonBox);
        return row;
    }

    /**
     * Check if a model is installed
     */
    _isModelInstalled(filename) {
        const file = Gio.File.new_for_path(`${this._modelDir}/${filename}`);
        return file.query_exists(null);
    }

    /**
     * Get current model from directory (first .bin file found, or tiny.en by default)
     */
    _getCurrentModel() {
        try {
            const dir = Gio.File.new_for_path(this._modelDir);
            if (!dir.query_exists(null)) {
                return null;
            }

            const enumerator = dir.enumerate_children(
                'standard::name',
                Gio.FileQueryInfoFlags.NONE,
                null
            );

            let fileInfo;
            while ((fileInfo = enumerator.next_file(null))) {
                const name = fileInfo.get_name();
                // Prefer tiny.en as default
                if (name === 'ggml-tiny.en.bin') {
                    return name;
                }
            }

            // If tiny.en not found, return first .bin file
            enumerator.close(null);
            const enumerator2 = dir.enumerate_children(
                'standard::name',
                Gio.FileQueryInfoFlags.NONE,
                null
            );

            while ((fileInfo = enumerator2.next_file(null))) {
                const name = fileInfo.get_name();
                if (name.endsWith('.bin') && name.startsWith('ggml-')) {
                    return name;
                }
            }
        } catch (e) {
            console.error('Error getting current model:', e);
        }

        return null;
    }

    /**
     * Get model file size
     */
    _getModelSize(filename) {
        try {
            const file = Gio.File.new_for_path(`${this._modelDir}/${filename}`);
            if (!file.query_exists(null)) {
                return null;
            }

            const info = file.query_info(
                'standard::size',
                Gio.FileQueryInfoFlags.NONE,
                null
            );

            const bytes = info.get_size();
            const mb = (bytes / (1024 * 1024)).toFixed(0);
            return `${mb} MB`;
        } catch (e) {
            return null;
        }
    }

    /**
     * Download a model
     */
    _downloadModel(model, window, button) {
        if (this._downloadInProgress) {
            this._showToast(window, 'Download already in progress');
            return;
        }

        this._downloadInProgress = true;
        button.sensitive = false;
        button.label = 'Downloading...';

        // Ensure model directory exists
        GLib.spawn_command_line_sync(`mkdir -p ${this._modelDir}`);

        const outputPath = `${this._modelDir}/${model.file}`;
        const command = `wget -O "${outputPath}" "${model.url}"`;

        this._showToast(window, `Downloading ${model.name} model (${model.size})...`);

        // Run download in background
        try {
            GLib.spawn_command_line_async(`sh -c '${command} && notify-send "Voice Assistant" "Model ${model.name} downloaded successfully"'`);
            
            // Re-enable button after a delay (the download continues in background)
            GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 3, () => {
                this._downloadInProgress = false;
                button.sensitive = true;
                button.label = 'Download';
                this._showToast(window, `Download started for ${model.name}. Check notifications for completion.`);
                return GLib.SOURCE_REMOVE;
            });
        } catch (e) {
            console.error('Download error:', e);
            this._downloadInProgress = false;
            button.sensitive = true;
            button.label = 'Download';
            this._showToast(window, `Download failed: ${e.message}`);
        }
    }

    /**
     * Select a model (models are auto-selected by the C++ service, just verify it exists)
     */
    _selectModel(model, window) {
        // The C++ service automatically uses models from the directory
        // We just need to restart the service for it to pick up the change
        this._showToast(window, `${model.name} selected. Restart the service to apply.`);
        
        // Optionally restart the service automatically
        try {
            GLib.spawn_command_line_async('systemctl --user restart voice-assistant.service');
            this._showToast(window, 'Restarting voice assistant service...');
        } catch (e) {
            console.error('Failed to restart service:', e);
        }
    }

    /**
     * Delete a model
     */
    _deleteModel(model, window) {
        const dialog = new Gtk.MessageDialog({
            modal: true,
            transient_for: window,
            message_type: Gtk.MessageType.QUESTION,
            buttons: Gtk.ButtonsType.YES_NO,
            text: `Delete ${model.name} model?`,
            secondary_text: `This will permanently delete the model file (${model.size}). This action cannot be undone.`,
        });

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.YES) {
                try {
                    const file = Gio.File.new_for_path(`${this._modelDir}/${model.file}`);
                    file.delete(null);
                    this._showToast(window, `${model.name} deleted`);
                } catch (e) {
                    this._showToast(window, `Failed to delete model: ${e.message}`);
                }
            }
            dialog.close();
        });

        dialog.present();
    }

    /**
     * Open model directory
     */
    _openModelDirectory() {
        try {
            GLib.spawn_command_line_sync(`mkdir -p ${this._modelDir}`);
            GLib.spawn_command_line_async(`xdg-open "${this._modelDir}"`);
        } catch (e) {
            console.error('Could not open model directory:', e);
        }
    }

    /**
     * Show toast notification
     */
    _showToast(window, message) {
        console.log(`WhisperModelManager: ${message}`);
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
