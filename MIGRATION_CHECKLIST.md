# Willow Migration Checklist

Use this checklist to track your migration progress.

## Pre-Migration Review
- [ ] Read `REBRANDING_SUMMARY.md` for overview
- [ ] Read `MIGRATION.md` for detailed instructions
- [ ] Review `branding.json` - the single source of truth
- [ ] Backup current working installation (if applicable)

## Code Changes (Already Completed ✅)
- [x] Created `branding.json` with centralized configuration
- [x] Updated D-Bus interface to `com.github.saim.Willow`
- [x] Updated service code and CMake files
- [x] Updated GNOME extension code
- [x] Created new systemd service file
- [x] Updated download script
- [x] Created new install scripts
- [x] Created new PKGBUILD files
- [x] Updated documentation

## Files to Review Before Migration
- [ ] Review `service/src/main.cpp` - D-Bus service name
- [ ] Review `service/src/VoiceAssistantService.cpp` - interface name
- [ ] Review `service/CMakeLists.txt` - build configuration
- [ ] Review `gnome-extension/gnome-assistant@saim/extension.js` - D-Bus references
- [ ] Review `gnome-extension/gnome-assistant@saim/metadata.json` - extension metadata
- [ ] Review `systemd/willow.service` - service configuration
- [ ] Review `willow.install` - installation script
- [ ] Review `PKGBUILD.new` - package build script

## Manual Migration Steps

### Option A: Automated (Recommended)
- [ ] Run `./complete-migration.sh`
- [ ] Review changes with `git status` and `git diff`
- [ ] Proceed to Testing section below

### Option B: Manual Step-by-Step
- [ ] Run `./migrate-to-willow.sh` to rename directories
- [ ] Replace PKGBUILD: `mv PKGBUILD.new PKGBUILD`
- [ ] Replace PKGBUILD-git: `mv PKGBUILD-git.new PKGBUILD-git`
- [ ] Replace README: `mv README.new.md README.md`
- [ ] Replace copilot instructions: `mv .github/copilot-instructions.new.md .github/copilot-instructions.md`
- [ ] Generate .SRCINFO: `makepkg --printsrcinfo > .SRCINFO`
- [ ] Remove old backed-up files when satisfied

## Testing

### Build Test
- [ ] Clean build directory: `cd service && rm -rf build`
- [ ] Create new build: `mkdir build && cd build`
- [ ] Configure: `cmake ..`
- [ ] Build: `make`
- [ ] Verify binary exists: `ls -la willow-service`

### Service Test (if installing locally)
- [ ] Stop old service: `systemctl --user stop gnome-assistant.service`
- [ ] Disable old extension: `gnome-extensions disable gnome-assistant@saim`
- [ ] Build package: `makepkg -si`
- [ ] Enable new extension: `gnome-extensions enable willow@saim`
- [ ] Start new service: `systemctl --user start willow.service`
- [ ] Check status: `systemctl --user status willow.service`

### D-Bus Test
- [ ] Check D-Bus registration: `busctl --user list | grep Willow`
- [ ] Introspect interface: `gdbus introspect --session --dest com.github.saim.Willow --object-path /com/github/saim/VoiceAssistant`
- [ ] Test method call: `gdbus call --session --dest com.github.saim.Willow --object-path /com/github/saim/VoiceAssistant --method com.github.saim.Willow.GetStatus`

### Extension Test
- [ ] Verify extension shows in panel
- [ ] Open preferences: `gnome-extensions prefs willow@saim`
- [ ] Test mode switching via panel menu
- [ ] Verify icon changes with modes
- [ ] Check that settings save to `~/.config/willow/config.json`

### Functionality Test
- [ ] Test hotword activation ("hey")
- [ ] Test voice command execution
- [ ] Test typing mode
- [ ] Verify model loading from `~/.local/share/willow/models/`
- [ ] Test command threshold adjustments
- [ ] Test custom command creation

## Git Repository Updates
- [ ] Review all changes: `git status`
- [ ] Check diff: `git diff`
- [ ] Stage changes: `git add .`
- [ ] Commit: `git commit -m "Rebrand to Willow with centralized configuration"`
- [ ] Push changes: `git push`
- [ ] (Optional) Rename repository on GitHub to "willow"
- [ ] (Optional) Update repository description on GitHub
- [ ] (Optional) Update topics/tags on GitHub

## AUR Package Updates (if applicable)
- [ ] Verify .SRCINFO is updated
- [ ] Update AUR repository
- [ ] Test AUR package installation
- [ ] Update AUR package description
- [ ] Announce migration to AUR users

## User Communication (if applicable)
- [ ] Update project website/documentation
- [ ] Announce rebranding to users
- [ ] Provide migration instructions
- [ ] Update external links and references
- [ ] Archive old gnome-assistant package (if needed)

## Cleanup
- [ ] Remove .old backup files when satisfied
- [ ] Remove .new temporary files
- [ ] Remove migration scripts (if desired)
- [ ] Update any CI/CD configurations
- [ ] Update issue templates

## Verification

### Final Checks
- [ ] `branding.json` is the source of truth
- [ ] No references to "gnome-assistant" in active code
- [ ] All paths use `willow` naming
- [ ] D-Bus interface is `com.github.saim.Willow`
- [ ] Extension UUID is `willow@saim`
- [ ] Binary name is `willow-service`
- [ ] Systemd service is `willow.service`
- [ ] Package name is `willow`

### Documentation Verification
- [ ] README.md reflects Willow branding
- [ ] All installation instructions use new names
- [ ] All file paths are updated
- [ ] Screenshots/images updated (if any)
- [ ] Links point to correct repository

## Post-Migration
- [ ] Monitor for user reports of issues
- [ ] Update any external integrations
- [ ] Close migration-related issues
- [ ] Create release notes documenting the change
- [ ] Celebrate! 🎉

---

## Notes

Use this space for migration-specific notes, issues encountered, or decisions made:

```
Date: ___________
Notes:


```

---

## Support

If you encounter issues:
1. Check logs: `journalctl --user -u willow.service -f`
2. Review `MIGRATION.md` for troubleshooting
3. Open issue: https://github.com/Saim20/willow/issues
4. Check branding: `cat branding.json`
