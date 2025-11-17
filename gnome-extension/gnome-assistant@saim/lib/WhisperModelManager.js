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
        this._modelDir = GLib.get_home_dir() + '/.local/share/gnome-assistant/models';
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

        // Store references for dynamic updates
        this._statusRow = null;
        this._expanderRow = null;
        this._modelRows = new Map(); // model.file -> row reference
        
        // Build initial content
        this._buildGroupContent(group, window);

        return group;
    }
    
    /**
     * Build or rebuild the group content
     */
    _buildGroupContent(group, window) {
        // Current model status
        const currentModel = this._getCurrentModel();
        this._statusRow = new Adw.ActionRow({
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
                this._statusRow.add_suffix(sizeLabel);
            }
        }
        
        group.add(this._statusRow);

        // Add expander for available models
        this._expanderRow = new Adw.ExpanderRow({
            title: 'Available Models',
            subtitle: 'Download and select whisper.cpp models',
        });

        this._modelRows.clear();
        for (const model of this._availableModels) {
            const modelRow = this._createModelRow(model, window, () => this._refreshUI(group, window));
            this._expanderRow.add_row(modelRow);
            this._modelRows.set(model.file, modelRow);
        }

        group.add(this._expanderRow);

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
    }
    
    /**
     * Refresh the UI after model changes
     */
    _refreshUI(group, window) {
        // Remove all children
        let child = group.get_first_child();
        while (child) {
            const next = child.get_next_sibling();
            group.remove(child);
            child = next;
        }
        
        // Rebuild content
        this._buildGroupContent(group, window);
    }

    /**
     * Create a row for each model
     */
    _createModelRow(model, window, refreshCallback) {
        const isInstalled = this._isModelInstalled(model.file);
        const currentModel = this._getCurrentModel();
        const isCurrent = currentModel === model.file;
        
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
                    this._selectModel(model, window, refreshCallback);
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
                this._deleteModel(model, window, refreshCallback);
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
                this._downloadModel(model, window, downloadButton, refreshCallback);
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
     * Get current model from config file, or fallback to checking directory
     */
    _getCurrentModel() {
        try {
            // First, try to read from config file
            const configPath = GLib.get_home_dir() + '/.config/gnome-assistant/config.json';
            const configFile = Gio.File.new_for_path(configPath);
            
            if (configFile.query_exists(null)) {
                let [success, contents] = configFile.load_contents(null);
                if (success) {
                    const config = JSON.parse(new TextDecoder().decode(contents));
                    if (config.whisper_model) {
                        // Verify the model file actually exists
                        const modelFile = Gio.File.new_for_path(`${this._modelDir}/${config.whisper_model}`);
                        if (modelFile.query_exists(null)) {
                            return config.whisper_model;
                        }
                    }
                }
            }
            
            // Fallback: check directory for installed models
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
            // Prefer tiny.en as default
            while ((fileInfo = enumerator.next_file(null))) {
                const name = fileInfo.get_name();
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
    _downloadModel(model, window, button, refreshCallback) {
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
        const tempPath = `${outputPath}.tmp`;
        const command = `wget -O "${tempPath}" "${model.url}" && mv "${tempPath}" "${outputPath}"`;

        this._showToast(window, `Downloading ${model.name} model (${model.size})...`);

        // Monitor download completion
        const checkCompletion = () => {
            const file = Gio.File.new_for_path(outputPath);
            if (file.query_exists(null)) {
                this._downloadInProgress = false;
                this._showToast(window, `${model.name} downloaded successfully`);
                if (refreshCallback) {
                    refreshCallback();
                }
                return GLib.SOURCE_REMOVE;
            }
            return GLib.SOURCE_CONTINUE;
        };

        // Run download in background
        try {
            GLib.spawn_command_line_async(`sh -c '${command} && notify-send "GNOME Assistant" "Model ${model.name} downloaded successfully"'`);
            
            // Poll for completion every 2 seconds
            GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 2, checkCompletion);
        } catch (e) {
            console.error('Download error:', e);
            this._downloadInProgress = false;
            button.sensitive = true;
            button.label = 'Download';
            this._showToast(window, `Download failed: ${e.message}`);
        }
    }

    /**
     * Select a model (save to config and restart service)
     */
    _selectModel(model, window, onComplete) {
        try {
            // Load current config
            const configPath = GLib.get_home_dir() + '/.config/gnome-assistant/config.json';
            const configFile = Gio.File.new_for_path(configPath);
            
            if (!configFile.query_exists(null)) {
                this._showToast(window, 'Configuration file not found. Please start the service first.');
                return;
            }
            
            let [success, contents] = configFile.load_contents(null);
            if (!success) {
                this._showToast(window, 'Failed to read configuration file');
                return;
            }
            
            let config = JSON.parse(new TextDecoder().decode(contents));
            
            // Update the whisper_model field
            config.whisper_model = model.file;
            
            // Save back to file
            const configJson = JSON.stringify(config, null, 2);
            configFile.replace_contents(
                configJson,
                null,
                false,
                Gio.FileCreateFlags.REPLACE_DESTINATION,
                null
            );
            
            this._showToast(window, `Selected ${model.name}. Restarting service...`);
            
            // Refresh UI immediately to show the new selection
            if (onComplete) {
                onComplete();
            }
            
            // Restart the service to apply the change
            GLib.spawn_command_line_async('systemctl --user restart gnome-assistant.service');
            
            // Show notification after a delay
            GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 2, () => {
                this._showToast(window, `Now using ${model.name} model`);
                return GLib.SOURCE_REMOVE;
            });
            
        } catch (e) {
            console.error('Failed to select model:', e);
            this._showToast(window, `Failed to select model: ${e.message}`);
        }
    }

    /**
     * Delete a model
     */
    _deleteModel(model, window, refreshCallback) {
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
                    if (refreshCallback) {
                        refreshCallback();
                    }
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
