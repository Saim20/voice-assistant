/**
 * CommandEditor.js - Command editing widgets and utilities
 * Provides UI components for editing voice commands with simplified structure
 */

import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import GObject from 'gi://GObject';

export const CommandListRow = GObject.registerClass({
    GTypeName: 'CommandListRow',
}, class CommandListRow extends Adw.ActionRow {
    _init(commandData, onUpdate, onDelete) {
        super._init({
            title: commandData.name || 'Unnamed Command',
            subtitle: `${commandData.command || 'No command'} • ${(commandData.phrases || []).length} phrases`,
        });

        this._commandData = commandData;
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
            tooltip_text: 'Edit command',
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
            title: 'Edit Command',
            modal: true,
            transient_for: this.get_root(),
            default_width: 500,
            default_height: 400,
        });

        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL);
        dialog.add_button('Save', Gtk.ResponseType.OK);

        const content = dialog.get_content_area();
        content.set_spacing(12);
        content.set_margin_top(12);
        content.set_margin_bottom(12);
        content.set_margin_start(12);
        content.set_margin_end(12);

        // Command details group
        const commandGroup = new Adw.PreferencesGroup({
            title: 'Command Details',
        });

        // Name entry
        const nameRow = new Adw.ActionRow({
            title: 'Display Name',
            subtitle: 'Friendly name for this command',
        });
        const nameEntry = new Gtk.Entry({
            text: this._commandData.name || '',
            placeholder_text: 'e.g., Terminal',
            valign: Gtk.Align.CENTER,
        });
        nameRow.add_suffix(nameEntry);
        commandGroup.add(nameRow);

        // Command entry
        const commandRow = new Adw.ActionRow({
            title: 'Shell Command',
            subtitle: 'The actual command to execute',
        });
        const commandEntry = new Gtk.Entry({
            text: this._commandData.command || '',
            placeholder_text: 'e.g., kgx or ydotool key 29:1 46:1 46:0 29:0',
            valign: Gtk.Align.CENTER,
        });
        commandRow.add_suffix(commandEntry);
        commandGroup.add(commandRow);

        content.append(commandGroup);

        // Phrases group
        const phrasesGroup = new Adw.PreferencesGroup({
            title: 'Voice Phrases',
            description: 'Add the phrases you want to say to trigger this command',
        });

        const phrasesScrolled = new Gtk.ScrolledWindow({
            height_request: 200,
            has_frame: true,
        });

        const phrasesListBox = new Gtk.ListBox({
            css_classes: ['boxed-list'],
        });

        phrasesScrolled.set_child(phrasesListBox);

        // Add existing phrases
        const phrases = this._commandData.phrases || [];
        const phraseEntries = [];

        phrases.forEach(phrase => {
            const entry = this._createPhraseEntry(phrase, phrasesListBox);
            phraseEntries.push(entry);
        });

        // Add new phrase button
        const addPhraseButton = new Gtk.Button({
            label: 'Add Phrase',
            icon_name: 'list-add-symbolic',
            css_classes: ['flat'],
        });

        addPhraseButton.connect('clicked', () => {
            const entry = this._createPhraseEntry('', phrasesListBox);
            phraseEntries.push(entry);
            entry.grab_focus();
        });

        phrasesGroup.add(phrasesScrolled);
        phrasesGroup.add(addPhraseButton);
        content.append(phrasesGroup);

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.OK) {
                // Collect data
                const newData = {
                    name: nameEntry.get_text().trim(),
                    command: commandEntry.get_text().trim(),
                    phrases: phraseEntries
                        .map(entry => entry.get_text().trim())
                        .filter(phrase => phrase.length > 0)
                };

                if (newData.name && newData.command && newData.phrases.length > 0) {
                    this._commandData = newData;
                    this._updateDisplay();
                    this._onUpdate(newData);
                } else {
                    // Show error - all fields required
                    const toast = new Adw.Toast({
                        title: 'Please fill in all fields and add at least one phrase',
                        timeout: 3,
                    });
                    
                    if (this.get_root().add_toast) {
                        this.get_root().add_toast(toast);
                    }
                }
            }
            dialog.destroy();
        });

        dialog.present();
    }

    _createPhraseEntry(text, listBox) {
        const row = new Adw.ActionRow();
        
        const entry = new Gtk.Entry({
            text: text,
            placeholder_text: 'e.g., open terminal',
            hexpand: true,
        });

        const deleteButton = new Gtk.Button({
            icon_name: 'user-trash-symbolic',
            valign: Gtk.Align.CENTER,
            css_classes: ['flat', 'destructive-action'],
        });

        deleteButton.connect('clicked', () => {
            listBox.remove(row);
        });

        row.add_suffix(entry);
        row.add_suffix(deleteButton);
        listBox.append(row);

        return entry;
    }

    _updateDisplay() {
        this.set_title(this._commandData.name || 'Unnamed Command');
        this.set_subtitle(`${this._commandData.command || 'No command'} • ${(this._commandData.phrases || []).length} phrases`);
    }

    _showDeleteConfirmation() {
        const dialog = new Gtk.MessageDialog({
            modal: true,
            transient_for: this.get_root(),
            text: 'Delete Command',
            secondary_text: `Are you sure you want to delete "${this._commandData.name}"?`,
        });

        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL);
        dialog.add_button('Delete', Gtk.ResponseType.OK);

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.OK) {
                this._onDelete();
            }
            dialog.destroy();
        });

        dialog.present();
    }
});

export class CommandManager {
    constructor(configManager) {
        this._configManager = configManager;
    }

    createCommandsGroup() {
        const group = new Adw.PreferencesGroup({
            title: 'Voice Commands',
            description: 'Manage voice commands and their associated actions',
        });

        const commandsListBox = new Gtk.ListBox({
            css_classes: ['boxed-list'],
        });

        const scrolled = new Gtk.ScrolledWindow({
            height_request: 300,
            has_frame: true,
        });
        scrolled.set_child(commandsListBox);

        this._loadCommands(commandsListBox);

        // Add new command button
        const addButton = new Gtk.Button({
            label: 'Add New Command',
            icon_name: 'list-add-symbolic',
            css_classes: ['suggested-action'],
        });

        addButton.connect('clicked', () => {
            this._showNewCommandDialog(commandsListBox);
        });

        group.add(scrolled);
        group.add(addButton);

        return group;
    }

    _loadCommands(listBox) {
        // Clear existing rows
        let child = listBox.get_first_child();
        while (child) {
            const next = child.get_next_sibling();
            listBox.remove(child);
            child = next;
        }

        const config = this._configManager.getConfig();
        const commands = config.commands || [];

        commands.forEach((commandData, index) => {
            const row = new CommandListRow(
                commandData,
                (updatedData) => {
                    this._updateCommand(index, updatedData);
                },
                () => {
                    this._deleteCommand(index);
                    this._loadCommands(listBox);
                }
            );
            listBox.append(row);
        });
    }

    _updateCommand(index, newData) {
        const config = this._configManager.getConfig();
        if (config.commands && config.commands[index]) {
            config.commands[index] = newData;
            this._configManager.saveConfig(config);
        }
    }

    _deleteCommand(index) {
        const config = this._configManager.getConfig();
        if (config.commands && config.commands[index]) {
            config.commands.splice(index, 1);
            this._configManager.saveConfig(config);
        }
    }

    _showNewCommandDialog(listBox) {
        const dialog = new Gtk.Dialog({
            title: 'Add New Command',
            modal: true,
            transient_for: listBox.get_root(),
            default_width: 500,
        });

        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL);
        dialog.add_button('Add', Gtk.ResponseType.OK);

        const content = dialog.get_content_area();
        content.set_spacing(12);
        content.set_margin_top(12);
        content.set_margin_bottom(12);
        content.set_margin_start(12);
        content.set_margin_end(12);

        const group = new Adw.PreferencesGroup({
            title: 'New Command',
        });

        const nameRow = new Adw.ActionRow({
            title: 'Display Name',
            subtitle: 'Friendly name for this command',
        });
        const nameEntry = new Gtk.Entry({
            placeholder_text: 'e.g., Terminal',
            valign: Gtk.Align.CENTER,
        });
        nameRow.add_suffix(nameEntry);
        group.add(nameRow);

        const commandRow = new Adw.ActionRow({
            title: 'Shell Command',
            subtitle: 'The actual command to execute',
        });
        const commandEntry = new Gtk.Entry({
            placeholder_text: 'e.g., kgx',
            valign: Gtk.Align.CENTER,
        });
        commandRow.add_suffix(commandEntry);
        group.add(commandRow);

        const phraseRow = new Adw.ActionRow({
            title: 'First Phrase',
            subtitle: 'Add at least one voice phrase',
        });
        const phraseEntry = new Gtk.Entry({
            placeholder_text: 'e.g., open terminal',
            valign: Gtk.Align.CENTER,
        });
        phraseRow.add_suffix(phraseEntry);
        group.add(phraseRow);

        content.append(group);

        dialog.connect('response', (dialog, response) => {
            if (response === Gtk.ResponseType.OK) {
                const name = nameEntry.get_text().trim();
                const command = commandEntry.get_text().trim();
                const phrase = phraseEntry.get_text().trim();

                if (name && command && phrase) {
                    const newCommand = {
                        name: name,
                        command: command,
                        phrases: [phrase]
                    };

                    const config = this._configManager.getConfig();
                    if (!config.commands) {
                        config.commands = [];
                    }
                    config.commands.push(newCommand);
                    this._configManager.saveConfig(config);
                    this._loadCommands(listBox);
                }
            }
            dialog.destroy();
        });

        dialog.present();
    }
}
