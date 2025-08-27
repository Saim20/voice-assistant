import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';
import Gio from 'gi://Gio';

export default class VoiceAssistantExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = new Gio.Settings({
            schema: 'org.gnome.shell.extensions.voice-assistant'
        });

        const page = new Adw.PreferencesPage({
            title: 'Voice Assistant',
        });

        // General group
        const generalGroup = new Adw.PreferencesGroup({
            title: 'General Settings',
            description: 'Basic extension configuration',
        });

        // Show label toggle
        const labelRow = new Adw.ActionRow({
            title: 'Show Mode Label',
            subtitle: 'Display text label next to the microphone icon',
        });
        const labelSwitch = new Gtk.Switch({
            active: settings.get_boolean('show-label'),
            valign: Gtk.Align.CENTER,
        });
        settings.bind('show-label', labelSwitch, 'active', Gio.SettingsBindFlags.DEFAULT);
        labelRow.add_suffix(labelSwitch);
        generalGroup.add(labelRow);

        // Notifications toggle
        const notificationRow = new Adw.ActionRow({
            title: 'Enable Notifications',
            subtitle: 'Show notifications for mode changes and command recognition',
        });
        const notificationSwitch = new Gtk.Switch({
            active: settings.get_boolean('notification-enabled'),
            valign: Gtk.Align.CENTER,
        });
        settings.bind('notification-enabled', notificationSwitch, 'active', Gio.SettingsBindFlags.DEFAULT);
        notificationRow.add_suffix(notificationSwitch);
        generalGroup.add(notificationRow);

        // Hotword setting
        const hotwordRow = new Adw.ActionRow({
            title: 'Activation Hotword',
            subtitle: 'Word used to activate command mode from normal mode',
        });
        const hotwordEntry = new Gtk.Entry({
            text: settings.get_string('hotword'),
            valign: Gtk.Align.CENTER,
        });
        settings.bind('hotword', hotwordEntry, 'text', Gio.SettingsBindFlags.DEFAULT);
        hotwordRow.add_suffix(hotwordEntry);
        generalGroup.add(hotwordRow);

        page.add(generalGroup);

        // Voice Recognition group
        const voiceGroup = new Adw.PreferencesGroup({
            title: 'Voice Recognition',
            description: 'Configure voice command processing settings',
        });

        // Command threshold
        const thresholdRow = new Adw.ActionRow({
            title: 'Command Threshold',
            subtitle: 'Minimum confidence percentage to execute commands (50-100%)',
        });
        const thresholdSpinButton = new Gtk.SpinButton({
            adjustment: new Gtk.Adjustment({
                lower: 50,
                upper: 100,
                step_increment: 5,
                page_increment: 10,
                value: settings.get_int('command-threshold'),
            }),
            valign: Gtk.Align.CENTER,
        });
        settings.bind('command-threshold', thresholdSpinButton, 'value', Gio.SettingsBindFlags.DEFAULT);
        thresholdRow.add_suffix(thresholdSpinButton);
        voiceGroup.add(thresholdRow);

        // Processing interval
        const intervalRow = new Adw.ActionRow({
            title: 'Processing Interval',
            subtitle: 'Time to wait before processing speech (0.5-5.0 seconds)',
        });
        const intervalSpinButton = new Gtk.SpinButton({
            adjustment: new Gtk.Adjustment({
                lower: 0.5,
                upper: 5.0,
                step_increment: 0.1,
                page_increment: 0.5,
                value: settings.get_double('processing-interval'),
            }),
            digits: 1,
            valign: Gtk.Align.CENTER,
        });
        settings.bind('processing-interval', intervalSpinButton, 'value', Gio.SettingsBindFlags.DEFAULT);
        intervalRow.add_suffix(intervalSpinButton);
        voiceGroup.add(intervalRow);

        // Update interval
        const updateRow = new Adw.ActionRow({
            title: 'Update Interval',
            subtitle: 'How often to check for file changes (1-10 seconds)',
        });
        const updateSpinButton = new Gtk.SpinButton({
            adjustment: new Gtk.Adjustment({
                lower: 1,
                upper: 10,
                step_increment: 1,
                page_increment: 1,
                value: settings.get_int('update-interval'),
            }),
            valign: Gtk.Align.CENTER,
        });
        settings.bind('update-interval', updateSpinButton, 'value', Gio.SettingsBindFlags.DEFAULT);
        updateRow.add_suffix(updateSpinButton);
        voiceGroup.add(updateRow);

        page.add(voiceGroup);

        // Information group
        const infoGroup = new Adw.PreferencesGroup({
            title: 'Information',
            description: 'About the Voice Assistant extension',
        });

        // Features
        const featuresRow = new Adw.ActionRow({
            title: 'Features',
            subtitle: 'Real-time mode display • Automatic command processing • Configurable thresholds',
        });
        infoGroup.add(featuresRow);

        // Usage
        const usageRow = new Adw.ActionRow({
            title: 'Usage',
            subtitle: 'Click the microphone icon to switch modes or adjust settings here',
        });
        infoGroup.add(usageRow);

        // Mode indicators
        const modeRow = new Adw.ActionRow({
            title: 'Mode Indicators',
            subtitle: 'Normal: White microphone • Command: Red microphone • Typing: Blue keyboard',
        });
        infoGroup.add(modeRow);

        page.add(infoGroup);
        window.add(page);
    }
}