# Willow Migration Guide

## Overview

This guide explains the complete migration from "gnome-assistant" to "Willow" branding. The project has been systematically rebranded with a centralized configuration system.

## Centralized Branding System

All project branding is now centralized in **`branding.json`** at the project root. This file contains:

- Project name and description
- Technical identifiers (D-Bus interface, extension UUID, etc.)
- File and directory paths
- URLs and metadata

**This is the single source of truth for all naming throughout the project.**

## Key Changes Summary

### Names and Identifiers

| Component | Old | New |
|-----------|-----|-----|
| **Project Name** | GNOME Assistant | Willow |
| **Description** | Advanced voice control... | Simple offline configurable voice assistant for gnome |
| **D-Bus Interface** | `com.github.saim.GnomeAssistant` | `com.github.saim.Willow` |
| **Extension UUID** | `gnome-assistant@saim` | `willow@saim` |
| **Service Binary** | `gnome-assistant-service` | `willow-service` |
| **Download Script** | `gnome-assistant-download-model` | `willow-download-model` |
| **Systemd Service** | `gnome-assistant.service` | `willow.service` |
| **Package Name** | `gnome-assistant` | `willow` |
| **GSchema ID** | `org.gnome.shell.extensions.gnome-assistant` | `org.gnome.shell.extensions.willow` |

### File Paths

| Type | Old | New |
|------|-----|-----|
| **Config Directory** | `~/.config/gnome-assistant` | `~/.config/willow` |
| **Data Directory** | `~/.local/share/gnome-assistant` | `~/.local/share/willow` |
| **Models** | `~/.local/share/gnome-assistant/models` | `~/.local/share/willow/models` |

### Files Created/Updated

#### New Files Created:
- ✅ `branding.json` - Centralized branding configuration
- ✅ `dbus/com.github.saim.Willow.xml` - D-Bus interface definition
- ✅ `dbus/com.github.saim.Willow.service.in` - D-Bus service configuration
- ✅ `systemd/willow.service` - systemd user service
- ✅ `willow.install` - Arch Linux install script
- ✅ `PKGBUILD.new` - Updated Arch package build script
- ✅ `PKGBUILD-git.new` - Updated git version package script
- ✅ `README.new.md` - Updated README with Willow branding
- ✅ `.github/copilot-instructions.new.md` - Updated AI instructions
- ✅ `gnome-extension/willow@saim/schemas/org.gnome.shell.extensions.willow.gschema.xml` - GSettings schema
- ✅ `migrate-to-willow.sh` - Migration script

#### Files Updated:
- ✅ `service/src/main.cpp` - D-Bus service name
- ✅ `service/src/VoiceAssistantService.cpp` - D-Bus interface name
- ✅ `service/CMakeLists.txt` - Build configuration
- ✅ `download-model.sh` - Model download paths and branding
- ✅ `gnome-extension/gnome-assistant@saim/extension.js` - D-Bus interface and paths
- ✅ `gnome-extension/gnome-assistant@saim/metadata.json` - Extension metadata

#### Files to be Removed (after migration):
- ❌ `dbus/com.github.saim.GnomeAssistant.xml`
- ❌ `dbus/com.github.saim.GnomeAssistant.service.in`
- ❌ `systemd/gnome-assistant.service`
- ❌ `gnome-assistant.install`
- ❌ `gnome-extension/gnome-assistant@saim/schemas/org.gnome.shell.extensions.gnome-assistant.gschema.xml`

#### Directory to be Renamed:
- 📁 `gnome-extension/gnome-assistant@saim/` → `gnome-extension/willow@saim/`

## Migration Steps

### For Users (Migrating Existing Installation)

1. **Stop the old service**:
   ```bash
   systemctl --user stop gnome-assistant.service
   systemctl --user disable gnome-assistant.service
   ```

2. **Disable the old extension**:
   ```bash
   gnome-extensions disable gnome-assistant@saim
   ```

3. **Migrate configuration** (optional - preserves your settings):
   ```bash
   mv ~/.config/gnome-assistant ~/.config/willow
   mv ~/.local/share/gnome-assistant ~/.local/share/willow
   ```

4. **Remove old package** (if installed via AUR):
   ```bash
   yay -R gnome-assistant
   ```

5. **Install Willow**:
   ```bash
   # Build and install new package
   cd willow
   makepkg -si
   ```

6. **Enable and start**:
   ```bash
   gnome-extensions enable willow@saim
   systemctl --user start willow.service
   ```

### For Developers (Repository Migration)

1. **Run the migration script**:
   ```bash
   chmod +x migrate-to-willow.sh
   ./migrate-to-willow.sh
   ```

2. **Replace PKGBUILD files**:
   ```bash
   mv PKGBUILD.new PKGBUILD
   mv PKGBUILD-git.new PKGBUILD-git
   ```

3. **Replace documentation**:
   ```bash
   mv README.new.md README.md
   mv .github/copilot-instructions.new.md .github/copilot-instructions.md
   ```

4. **Update .SRCINFO** (for AUR):
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

5. **Test the build**:
   ```bash
   cd service
   rm -rf build
   mkdir build && cd build
   cmake ..
   make
   ```

6. **Verify D-Bus interface**:
   ```bash
   # Start the service
   ./willow-service &
   
   # Test D-Bus connection
   gdbus introspect --session --dest com.github.saim.Willow \
     --object-path /com/github/saim/VoiceAssistant
   ```

## Verification Checklist

After migration, verify:

- [ ] Service starts: `systemctl --user status willow.service`
- [ ] D-Bus interface available: `gdbus call --session --dest com.github.saim.Willow --object-path /com/github/saim/VoiceAssistant --method com.github.saim.Willow.GetStatus`
- [ ] Extension shows in panel
- [ ] Preferences open: `gnome-extensions prefs willow@saim`
- [ ] Voice recognition works
- [ ] Configuration saved to `~/.config/willow/config.json`
- [ ] Models in `~/.local/share/willow/models/`

## Troubleshooting

### Service won't start
```bash
# Check for old service conflicts
systemctl --user list-units | grep -i assistant

# View logs
journalctl --user -u willow.service -n 50
```

### Extension not found
```bash
# Verify installation
ls -la ~/.local/share/gnome-shell/extensions/willow@saim/

# Restart GNOME Shell
# X11: Alt+F2, type 'r', press Enter
# Wayland: Log out and back in
```

### D-Bus connection errors
```bash
# Check if service is registered
busctl --user list | grep Willow

# Verify D-Bus files
ls -la /usr/share/dbus-1/services/com.github.saim.Willow.service
ls -la /usr/share/dbus-1/interfaces/com.github.saim.Willow.xml
```

### Configuration not migrated
```bash
# Manually copy if needed
cp -r ~/.config/gnome-assistant ~/.config/willow
cp -r ~/.local/share/gnome-assistant ~/.local/share/willow
```

## Rollback (if needed)

If you need to rollback to gnome-assistant:

1. Stop Willow:
   ```bash
   systemctl --user stop willow.service
   gnome-extensions disable willow@saim
   ```

2. Restore old configuration:
   ```bash
   mv ~/.config/willow ~/.config/gnome-assistant
   mv ~/.local/share/willow ~/.local/share/gnome-assistant
   ```

3. Reinstall gnome-assistant from previous commit

## Next Steps

After successful migration:

1. Update GitHub repository name (if applicable)
2. Update AUR package
3. Announce migration to users
4. Update any external documentation/links
5. Archive old gnome-assistant package

## Support

For issues during migration:
- Open an issue: https://github.com/Saim20/willow/issues
- Check logs: `journalctl --user -u willow.service -f`
- Verify branding: `cat branding.json`
