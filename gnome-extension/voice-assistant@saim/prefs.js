import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';

export default class VoiceAssistantExtensionPreferences {
    fillPreferencesWindow(window) {
        const page = new Adw.PreferencesPage({
            title: 'Voice Assistant',
        });

        const group = new Adw.PreferencesGroup({
            title: 'Extension Information',
            description: 'Voice Assistant extension for nerd-dictation integration',
        });

        // Add description
        const descRow = new Adw.ActionRow({
            title: 'Features',
            subtitle: 'Shows current mode in top panel - Real-time mode switching - File-based communication',
        });
        group.add(descRow);

        // Add usage instructions
        const usageRow = new Adw.ActionRow({
            title: 'Usage',
            subtitle: 'Click the microphone icon in the top panel to switch between Normal, Command, and Typing modes',
        });
        group.add(usageRow);

        // Add mode indicators
        const modeRow = new Adw.ActionRow({
            title: 'Mode Indicators',
            subtitle: 'Normal: White microphone - Command: Red microphone - Typing: Blue keyboard',
        });
        group.add(modeRow);

        page.add(group);
        window.add(page);
    }
}