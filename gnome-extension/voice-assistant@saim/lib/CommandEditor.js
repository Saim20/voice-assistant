/**
 * CommandEditor.js - Command editing widgets and utilities
 * Provides UI components for editing voice commands and categories
 */

import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import GObject from 'gi://GObject';

export const CommandCategoryRow = GObject.registerClass({
    GTypeName: 'CommandCategoryRow',
    Template: null,
}, class CommandCategoryRow extends Adw.ExpanderRow {
    _init(categoryName, commands, onUpdate) {
        super._init({
            title: this._formatCategoryName(categoryName),
            subtitle: `${Object.keys(commands).length} commands`,
        });

        this._categoryName = categoryName;
        this._commands = commands;
        this._onUpdate = onUpdate;

        this._buildCommandList();
        this._addNewCommandButton();
    }

    _formatCategoryName(name) {
        return name.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    _buildCommandList() {
        for (const [commandKey, phrases] of Object.entries(this._commands)) {
            const commandRow = new CommandRow(commandKey, phrases, (key, newPhrases) => {
                this._commands[key] = newPhrases;
                this._onUpdate(this._categoryName, this._commands);
                this._updateSubtitle();
            }, (key) => {
                delete this._commands[key];
                this._onUpdate(this._categoryName, this._commands);
                this._updateSubtitle();
            });
            this.add_row(commandRow);
        }
    }

    _addNewCommandButton() {
        const newCommandRow = new Adw.ActionRow({
            title: 'Add New Command',
            subtitle: 'Click to add a new voice command',
        });

        const addButton = new Gtk.Button({
            icon_name: 'list-add-symbolic',
            valign: Gtk.Align.CENTER,
            css_classes: ['flat'],
        });

        addButton.connect('clicked', () => {
            this._showNewCommandDialog();
        });

        newCommandRow.add_suffix(addButton);
        this.add_row(newCommandRow);
    }

    _showNewCommandDialog() {
        const dialog = new Gtk.Dialog({
            title: 'Add New Command',
            modal: true,
            transient_for: this.get_root(),
        });

        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL);
        dialog.add_button('Add', Gtk.ResponseType.OK);

        const content = dialog.get_content_area();
        content.set_spacing(12);
        content.set_margin_top(12);
        content.set_margin_bottom(12);
        content.set_margin_start(12);
        content.set_margin_end(12);

        const commandGroup = new Adw.PreferencesGroup({
            title: 'Command Details',
        });

        const nameRow = new Adw.ActionRow({
            title: 'Command Name',
            subtitle: 'Internal name for the command (e.g., "open_terminal")',
        });
        const nameEntry = new Gtk.Entry({
            placeholder_text: 'command_name',
            valign: Gtk.Align.CENTER,
        });
        nameRow.add_suffix(nameEntry);
        commandGroup.add(nameRow);

        const phrasesRow = new Adw.ActionRow({
            title: 'Voice Phrases',
            subtitle: 'Comma-separated phrases that trigger this command',
        });
        const phrasesEntry = new Gtk.Entry({
            placeholder_text: 'open terminal, start terminal, launch terminal',
            valign: Gtk.Align.CENTER,
        });
        phrasesRow.add_suffix(phrasesEntry);
        commandGroup.add(phrasesRow);

        content.append(commandGroup);

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.OK) {
                const commandName = nameEntry.get_text().trim();
                const phrasesText = phrasesEntry.get_text().trim();

                if (commandName && phrasesText) {
                    const phrases = phrasesText.split(',').map(p => p.trim()).filter(p => p);
                    this._commands[commandName] = phrases;
                    
                    // Add the new command row
                    const commandRow = new CommandRow(commandName, phrases, (key, newPhrases) => {
                        this._commands[key] = newPhrases;
                        this._onUpdate(this._categoryName, this._commands);
                        this._updateSubtitle();
                    }, (key) => {
                        delete this._commands[key];
                        this._onUpdate(this._categoryName, this._commands);
                        this._updateSubtitle();
                    });
                    
                    // Insert before the "Add New Command" button
                    const rows = [];
                    for (let i = 0; i < this.get_n_rows(); i++) {
                        rows.push(this.get_row_at_index(i));
                    }
                    const addButtonRow = rows[rows.length - 1];
                    this.insert_row_before(commandRow, addButtonRow);
                    
                    this._onUpdate(this._categoryName, this._commands);
                    this._updateSubtitle();
                }
            }
            dialog.close();
        });

        dialog.present();
    }

    _updateSubtitle() {
        this.set_subtitle(`${Object.keys(this._commands).length} commands`);
    }
});

export const CommandRow = GObject.registerClass({
    GTypeName: 'CommandRow',
}, class CommandRow extends Adw.ActionRow {
    _init(commandKey, phrases, onUpdate, onDelete) {
        super._init({
            title: commandKey.replace(/_/g, ' '),
            subtitle: Array.isArray(phrases) ? phrases.join(', ') : phrases,
        });

        this._commandKey = commandKey;
        this._phrases = phrases;
        this._onUpdate = onUpdate;
        this._onDelete = onDelete;

        this._addEditButton();
        this._addDeleteButton();
    }

    _addEditButton() {
        const editButton = new Gtk.Button({
            icon_name: 'document-edit-symbolic',
            valign: Gtk.Align.CENTER,
            css_classes: ['flat'],
            tooltip_text: 'Edit command phrases',
        });

        editButton.connect('clicked', () => {
            this._showEditDialog();
        });

        this.add_suffix(editButton);
    }

    _addDeleteButton() {
        const deleteButton = new Gtk.Button({
            icon_name: 'user-trash-symbolic',
            valign: Gtk.Align.CENTER,
            css_classes: ['flat', 'destructive-action'],
            tooltip_text: 'Delete command',
        });

        deleteButton.connect('clicked', () => {
            this._showDeleteConfirmation();
        });

        this.add_suffix(deleteButton);
    }

    _showEditDialog() {
        const dialog = new Gtk.Dialog({
            title: `Edit Command: ${this._commandKey}`,
            modal: true,
            transient_for: this.get_root(),
        });

        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL);
        dialog.add_button('Save', Gtk.ResponseType.OK);

        const content = dialog.get_content_area();
        content.set_spacing(12);
        content.set_margin_top(12);
        content.set_margin_bottom(12);
        content.set_margin_start(12);
        content.set_margin_end(12);

        const phrasesGroup = new Adw.PreferencesGroup({
            title: 'Voice Phrases',
            description: 'Enter comma-separated phrases that should trigger this command',
        });

        const phrasesEntry = new Gtk.Entry({
            text: Array.isArray(this._phrases) ? this._phrases.join(', ') : this._phrases,
            valign: Gtk.Align.CENTER,
        });

        const phrasesRow = new Adw.ActionRow({
            title: 'Phrases',
        });
        phrasesRow.add_suffix(phrasesEntry);
        phrasesGroup.add(phrasesRow);

        content.append(phrasesGroup);

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.OK) {
                const newPhrasesText = phrasesEntry.get_text().trim();
                if (newPhrasesText) {
                    const newPhrases = newPhrasesText.split(',').map(p => p.trim()).filter(p => p);
                    this._phrases = newPhrases;
                    this.set_subtitle(newPhrases.join(', '));
                    this._onUpdate(this._commandKey, newPhrases);
                }
            }
            dialog.close();
        });

        dialog.present();
    }

    _showDeleteConfirmation() {
        const dialog = new Gtk.MessageDialog({
            modal: true,
            transient_for: this.get_root(),
            message_type: Gtk.MessageType.QUESTION,
            buttons: Gtk.ButtonsType.YES_NO,
            text: 'Delete Command?',
            secondary_text: `Are you sure you want to delete the command "${this._commandKey}"? This action cannot be undone.`,
        });

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.YES) {
                this._onDelete(this._commandKey);
                this.get_parent().remove(this);
            }
            dialog.close();
        });

        dialog.present();
    }
});

export class CommandManager {
    constructor(configManager) {
        this._configManager = configManager;
    }

    /**
     * Get all command categories
     */
    getCategories() {
        const config = this._configManager.getConfig();
        return config.commands || {};
    }

    /**
     * Update a command category
     */
    updateCategory(categoryName, commands) {
        const config = this._configManager.getConfig();
        if (!config.commands) {
            config.commands = {};
        }
        config.commands[categoryName] = commands;
        return this._configManager.saveConfig(config);
    }

    /**
     * Add a new category
     */
    addCategory(categoryName) {
        const config = this._configManager.getConfig();
        if (!config.commands) {
            config.commands = {};
        }
        config.commands[categoryName] = {};
        return this._configManager.saveConfig(config);
    }

    /**
     * Delete a category
     */
    deleteCategory(categoryName) {
        const config = this._configManager.getConfig();
        if (config.commands && config.commands[categoryName]) {
            delete config.commands[categoryName];
            return this._configManager.saveConfig(config);
        }
        return false;
    }

    /**
     * Get command statistics
     */
    getStats() {
        const categories = this.getCategories();
        let totalCommands = 0;
        let totalPhrases = 0;

        for (const [categoryName, commands] of Object.entries(categories)) {
            totalCommands += Object.keys(commands).length;
            for (const phrases of Object.values(commands)) {
                if (Array.isArray(phrases)) {
                    totalPhrases += phrases.length;
                } else {
                    totalPhrases += 1;
                }
            }
        }

        return {
            categories: Object.keys(categories).length,
            commands: totalCommands,
            phrases: totalPhrases,
        };
    }
}
