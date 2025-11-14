/**
 * KeyCommandBuilder.js - Visual key combination builder for ydotool commands
 * Provides an intuitive interface for building keyboard shortcuts
 */

import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import GObject from 'gi://GObject';

// Key code mappings for ydotool
export const KEY_CODES = {
    // Modifier keys
    'Ctrl': 29,
    'Alt': 56,
    'Shift': 42,
    'Super': 125,
    'AltGr': 100,
    
    // Function keys
    'F1': 59, 'F2': 60, 'F3': 61, 'F4': 62,
    'F5': 63, 'F6': 64, 'F7': 65, 'F8': 66,
    'F9': 67, 'F10': 68, 'F11': 87, 'F12': 88,
    
    // Number row
    '1': 2, '2': 3, '3': 4, '4': 5, '5': 6,
    '6': 7, '7': 8, '8': 9, '9': 10, '0': 11,
    
    // Letters (QWERTY layout)
    'Q': 16, 'W': 17, 'E': 18, 'R': 19, 'T': 20,
    'Y': 21, 'U': 22, 'I': 23, 'O': 24, 'P': 25,
    'A': 30, 'S': 31, 'D': 32, 'F': 33, 'G': 34,
    'H': 35, 'J': 36, 'K': 37, 'L': 38,
    'Z': 44, 'X': 45, 'C': 46, 'V': 47, 'B': 48,
    'N': 49, 'M': 50,
    
    // Special keys
    'Escape': 1,
    'Backspace': 14,
    'Tab': 15,
    'Enter': 28,
    'Space': 57,
    'CapsLock': 58,
    
    // Arrow keys
    'Up': 103,
    'Down': 108,
    'Left': 105,
    'Right': 106,
    
    // Symbols and punctuation
    'Minus': 12,        // -
    'Equal': 13,        // =
    'LeftBracket': 26,  // [
    'RightBracket': 27, // ]
    'Semicolon': 39,    // ;
    'Quote': 40,        // '
    'Grave': 41,        // `
    'Backslash': 43,    // \
    'Comma': 51,        // ,
    'Period': 52,       // .
    'Slash': 53,        // /
    
    // Navigation keys
    'Insert': 110,
    'Delete': 111,
    'Home': 102,
    'End': 107,
    'PageUp': 104,
    'PageDown': 109,
    
    // Media keys
    'VolumeUp': 115,
    'VolumeDown': 114,
    'Mute': 113,
    'PlayPause': 164,
    'Stop': 166,
    'PreviousTrack': 165,
    'NextTrack': 163,
    
    // Numpad
    'Numpad0': 82, 'Numpad1': 79, 'Numpad2': 80, 'Numpad3': 81,
    'Numpad4': 75, 'Numpad5': 76, 'Numpad6': 77, 'Numpad7': 71,
    'Numpad8': 72, 'Numpad9': 73,
    'NumpadEnter': 96,
    'NumpadPlus': 78,
    'NumpadMinus': 74,
    'NumpadMultiply': 55,
    'NumpadDivide': 98,
    'NumpadPeriod': 83,
    
    // System keys
    'PrintScreen': 99,
    'ScrollLock': 70,
    'Pause': 119,
    'Menu': 127,
};

// Key categories for organized display
export const KEY_CATEGORIES = {
    'Modifiers': ['Ctrl', 'Alt', 'Shift', 'Super', 'AltGr'],
    'Letters': ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
                'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
                'Z', 'X', 'C', 'V', 'B', 'N', 'M'],
    'Numbers': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
    'Function Keys': ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'],
    'Navigation': ['Up', 'Down', 'Left', 'Right', 'Home', 'End', 'PageUp', 'PageDown'],
    'Editing': ['Insert', 'Delete', 'Backspace', 'Tab', 'Enter', 'Space'],
    'Symbols': ['Minus', 'Equal', 'LeftBracket', 'RightBracket', 'Semicolon', 'Quote', 
                'Grave', 'Backslash', 'Comma', 'Period', 'Slash'],
    'Media': ['VolumeUp', 'VolumeDown', 'Mute', 'PlayPause', 'Stop', 'PreviousTrack', 'NextTrack'],
    'System': ['Escape', 'CapsLock', 'PrintScreen', 'ScrollLock', 'Pause', 'Menu']
};

// Common shortcuts for quick selection
export const COMMON_SHORTCUTS = {
    'Copy': ['Ctrl', 'C'],
    'Paste': ['Ctrl', 'V'],
    'Cut': ['Ctrl', 'X'],
    'Undo': ['Ctrl', 'Z'],
    'Redo': ['Ctrl', 'Y'],
    'Select All': ['Ctrl', 'A'],
    'Save': ['Ctrl', 'S'],
    'Open': ['Ctrl', 'O'],
    'New': ['Ctrl', 'N'],
    'Find': ['Ctrl', 'F'],
    'Close Tab': ['Ctrl', 'W'],
    'New Tab': ['Ctrl', 'T'],
    'Switch Window': ['Alt', 'Tab'],
    'Show Desktop': ['Super', 'D'],
    'Lock Screen': ['Super', 'L'],
    'Screenshot': ['PrintScreen'],
    'Minimize': ['Super', 'H'],
    'Maximize': ['Super', 'Up'],
    'Move Left Workspace': ['Super', 'Left'],
    'Move Right Workspace': ['Super', 'Right']
};

export const KeyCommandBuilder = GObject.registerClass({
    GTypeName: 'KeyCommandBuilder',
    Signals: {
        'command-changed': {
            param_types: [GObject.TYPE_STRING]
        }
    }
}, class KeyCommandBuilder extends Gtk.Box {
    _init() {
        super._init({
            orientation: Gtk.Orientation.VERTICAL,
            spacing: 12,
        });

        this._selectedKeys = [];
        this._currentCommand = '';
        this._keyButtons = new Map();

        this._buildInterface();
        this._updateCommandDisplay();
    }

    _buildInterface() {
        // Title and preview in compact format
        const headerBox = new Gtk.Box({
            orientation: Gtk.Orientation.VERTICAL,
            spacing: 8,
        });

        const titleLabel = new Gtk.Label({
            label: '<b>Key Builder</b>',
            use_markup: true,
            halign: Gtk.Align.START,
        });

        // Compact key preview
        this._keyPreviewBox = new Gtk.Box({
            orientation: Gtk.Orientation.HORIZONTAL,
            spacing: 6,
            halign: Gtk.Align.CENTER,
        });

        const previewFrame = new Gtk.Frame({
            child: this._keyPreviewBox,
            css_classes: ['view'],
            height_request: 40,
        });

        // Command display - more compact
        this._commandDisplay = new Gtk.Entry({
            placeholder_text: 'Command will appear here',
            editable: false,
            css_classes: ['monospace'],
        });

        // Compact action buttons
        const actionBox = new Gtk.Box({
            orientation: Gtk.Orientation.HORIZONTAL,
            spacing: 4,
            halign: Gtk.Align.END,
        });

        const clearButton = new Gtk.Button({
            icon_name: 'edit-clear-symbolic',
            css_classes: ['flat'],
            tooltip_text: 'Clear selection',
        });
        clearButton.connect('clicked', () => this._clearSelection());

        actionBox.append(clearButton);

        headerBox.append(titleLabel);
        headerBox.append(previewFrame);
        headerBox.append(this._commandDisplay);
        headerBox.append(actionBox);
        this.append(headerBox);

        // Main content in scrolled window
        const mainScrolled = new Gtk.ScrolledWindow({
            height_request: 300,
            vexpand: true,
            propagate_natural_height: false,
        });

        const mainBox = new Gtk.Box({
            orientation: Gtk.Orientation.VERTICAL,
            spacing: 8,
        });

        // Compact common shortcuts
        this._createCompactShortcuts(mainBox);

        // Compact key categories
        this._createCompactKeyCategories(mainBox);

        mainScrolled.set_child(mainBox);
        this.append(mainScrolled);
    }

    _createCompactShortcuts(container) {
        const shortcutsExpander = new Adw.ExpanderRow({
            title: 'Common Shortcuts',
            subtitle: 'Quick access to popular combinations',
        });

        const shortcutsBox = new Gtk.FlowBox({
            max_children_per_line: 3,
            column_spacing: 4,
            row_spacing: 4,
            selection_mode: Gtk.SelectionMode.NONE,
            margin_top: 8,
            margin_bottom: 8,
            margin_start: 8,
            margin_end: 8,
        });

        // Show only most common shortcuts
        const popularShortcuts = {
            'Copy': ['Ctrl', 'C'],
            'Paste': ['Ctrl', 'V'],
            'Cut': ['Ctrl', 'X'],
            'Undo': ['Ctrl', 'Z'],
            'Save': ['Ctrl', 'S'],
            'Find': ['Ctrl', 'F'],
            'New Tab': ['Ctrl', 'T'],
            'Close': ['Ctrl', 'W'],
            'Switch App': ['Alt', 'Tab'],
        };

        Object.entries(popularShortcuts).forEach(([name, keys]) => {
            const button = new Gtk.Button({
                label: name,
                tooltip_text: keys.join(' + '),
                css_classes: ['flat', 'pill'],
            });

            button.connect('clicked', () => {
                this._selectedKeys = [...keys];
                this._updateCommandDisplay();
                this._refreshAllButtons();
            });

            shortcutsBox.append(button);
        });

        shortcutsExpander.add_row(new Adw.ActionRow({
            child: shortcutsBox,
        }));

        container.append(shortcutsExpander);
    }

    _createCompactKeyCategories(container) {
        // Most used categories as expandable rows
        const importantCategories = {
            'Modifiers': KEY_CATEGORIES['Modifiers'],
            'Letters': KEY_CATEGORIES['Letters'],
            'Numbers': KEY_CATEGORIES['Numbers'],
            'Function Keys': KEY_CATEGORIES['Function Keys'].slice(0, 8), // Only F1-F8
            'Navigation': KEY_CATEGORIES['Navigation'],
            'Common Keys': ['Enter', 'Space', 'Backspace', 'Tab', 'Escape']
        };

        Object.entries(importantCategories).forEach(([category, keys]) => {
            const expander = new Adw.ExpanderRow({
                title: category,
                subtitle: `${keys.length} keys`,
            });

            const flowBox = new Gtk.FlowBox({
                max_children_per_line: category === 'Letters' ? 8 : 6,
                column_spacing: 3,
                row_spacing: 3,
                selection_mode: Gtk.SelectionMode.NONE,
                margin_top: 6,
                margin_bottom: 6,
                margin_start: 6,
                margin_end: 6,
            });

            keys.forEach(key => {
                const button = this._createCompactKeyButton(key, category);
                flowBox.append(button);
            });

            expander.add_row(new Adw.ActionRow({
                child: flowBox,
            }));

            container.append(expander);
        });
    }

    _createCompactKeyButton(key, category) {
        const isModifier = KEY_CATEGORIES['Modifiers'].includes(key);
        const isSelected = this._selectedKeys.includes(key);

        const button = new Gtk.ToggleButton({
            label: key,
            active: isSelected,
            tooltip_text: `${key} (${KEY_CODES[key]})`,
            width_request: 32,
            height_request: 28,
        });

        // Compact styling
        button.add_css_class('flat');
        
        if (isModifier) {
            button.add_css_class('suggested-action');
        }

        if (category === 'Function Keys') {
            button.add_css_class('pill');
        }

        button.connect('toggled', () => {
            if (button.get_active()) {
                if (!this._selectedKeys.includes(key)) {
                    // Add modifiers first, then other keys
                    if (isModifier) {
                        const modifierIndex = this._selectedKeys.findIndex(k => !KEY_CATEGORIES['Modifiers'].includes(k));
                        if (modifierIndex === -1) {
                            this._selectedKeys.push(key);
                        } else {
                            this._selectedKeys.splice(modifierIndex, 0, key);
                        }
                    } else {
                        this._selectedKeys.push(key);
                    }
                }
            } else {
                this._selectedKeys = this._selectedKeys.filter(k => k !== key);
            }
            this._updateCommandDisplay();
            this._refreshAllButtons();
        });

        // Store reference for later updates
        if (!this._keyButtons) {
            this._keyButtons = new Map();
        }
        this._keyButtons.set(key, button);

        return button;
    }

    _refreshAllButtons() {
        if (this._keyButtons) {
            this._keyButtons.forEach((button, key) => {
                const shouldBeActive = this._selectedKeys.includes(key);
                if (button.get_active() !== shouldBeActive) {
                    button.set_active(shouldBeActive);
                }
            });
        }
    }

    _updateCommandDisplay() {
        if (this._selectedKeys.length === 0) {
            this._currentCommand = '';
            this._commandDisplay.set_text('');
            this._commandDisplay.set_placeholder_text('Select keys below to build a command');
            this._updateKeyPreview([]);
        } else {
            this._currentCommand = this._buildYdotoolCommand(this._selectedKeys);
            this._commandDisplay.set_text(this._currentCommand);
            this._updateKeyPreview(this._selectedKeys);
        }

        this.emit('command-changed', this._currentCommand);
    }

    _updateKeyPreview(keys) {
        if (!this._keyPreviewBox) return;

        // Clear existing preview
        let child = this._keyPreviewBox.get_first_child();
        while (child) {
            const next = child.get_next_sibling();
            this._keyPreviewBox.remove(child);
            child = next;
        }

        if (keys.length === 0) {
            const emptyLabel = new Gtk.Label({
                label: 'No keys selected',
                css_classes: ['dim-label'],
            });
            this._keyPreviewBox.append(emptyLabel);
            return;
        }

        // Add key preview buttons
        keys.forEach((key, index) => {
            if (index > 0) {
                const plusLabel = new Gtk.Label({
                    label: '+',
                    css_classes: ['dim-label'],
                });
                this._keyPreviewBox.append(plusLabel);
            }

            const keyLabel = new Gtk.Label({
                label: key,
                css_classes: ['keyboard-key'],
            });
            this._keyPreviewBox.append(keyLabel);
        });
    }

    _buildYdotoolCommand(keys) {
        if (keys.length === 0) return '';

        const keyPresses = [];
        const keyReleases = [];

        // Press all keys in order
        keys.forEach(key => {
            const code = KEY_CODES[key];
            if (code !== undefined) {
                keyPresses.push(`${code}:1`);
            }
        });

        // Release all keys in reverse order
        keys.slice().reverse().forEach(key => {
            const code = KEY_CODES[key];
            if (code !== undefined) {
                keyReleases.push(`${code}:0`);
            }
        });

        const allPresses = [...keyPresses, ...keyReleases];
        return `ydotool key ${allPresses.join(' ')}`;
    }

    _clearSelection() {
        this._selectedKeys = [];
        this._updateCommandDisplay();
        this._refreshAllButtons();
    }

    _copyToClipboard() {
        if (this._currentCommand) {
            const display = this.get_display();
            const clipboard = display.get_clipboard();
            clipboard.set_text(this._currentCommand);
            
            // Show feedback
            const toast = new Adw.Toast({
                title: 'Command copied to clipboard',
                timeout: 2,
            });
            
            const root = this.get_root();
            if (root && root.add_toast) {
                root.add_toast(toast);
            }
        }
    }

    // Public methods
    setCommand(command) {
        // Parse existing ydotool command to set selected keys
        this._parseYdotoolCommand(command);
        this._updateCommandDisplay();
    }

    getCommand() {
        return this._currentCommand;
    }

    getSelectedKeys() {
        return [...this._selectedKeys];
    }

    _parseYdotoolCommand(command) {
        // Simple parser for ydotool commands
        // Format: "ydotool key 29:1 46:1 46:0 29:0"
        this._selectedKeys = [];
        
        if (!command || !command.startsWith('ydotool key ')) {
            return;
        }

        const keyPart = command.replace('ydotool key ', '');
        const parts = keyPart.split(' ');
        
        // Extract press events (ending with :1)
        const pressEvents = parts.filter(part => part.endsWith(':1'));
        
        pressEvents.forEach(event => {
            const code = parseInt(event.split(':')[0]);
            const key = Object.keys(KEY_CODES).find(k => KEY_CODES[k] === code);
            if (key && !this._selectedKeys.includes(key)) {
                this._selectedKeys.push(key);
            }
        });
    }
});
