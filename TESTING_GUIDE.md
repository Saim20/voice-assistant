# Testing Guide for AUR Package

This guide helps you test the GNOME Assistant AUR package before publishing.

## Prerequisites

Ensure you have the required tools:
```bash
sudo pacman -S base-devel git
```

## Quick Test (CPU-only)

Test the basic package build:

```bash
# Navigate to repository
cd /path/to/gnome-assistant

# Test build (without installing)
makepkg -f

# Check generated package
ls -lh *.pkg.tar.zst

# Test installation
makepkg -fi
```

Expected output:
- Service installed to `/usr/bin/gnome-assistant-service`
- Extension installed to `/usr/share/gnome-shell/extensions/gnome-assistant@saim/`
- Post-install instructions displayed

## Test GPU Support

### Test CUDA Build

```bash
# Clean previous build
makepkg -C

# Build with CUDA
ENABLE_CUDA=1 makepkg -f

# Verify CUDA libraries linked
ldd /usr/bin/gnome-assistant-service | grep -i cuda
```

Expected: Should show CUDA libraries if toolkit is installed.

### Test Vulkan Build

```bash
# Clean previous build
makepkg -C

# Build with Vulkan
ENABLE_VULKAN=1 makepkg -f

# Verify Vulkan libraries linked
ldd /usr/bin/gnome-assistant-service | grep -i vulkan
```

Expected: Should show Vulkan libraries if SDK is installed.

### Test Both

```bash
# Clean previous build
makepkg -C

# Build with both
ENABLE_CUDA=1 ENABLE_VULKAN=1 makepkg -f

# Verify both libraries
ldd /usr/bin/gnome-assistant-service | grep -i "cuda\|vulkan"
```

## Test Interactive Helper

```bash
./build-aur.sh
```

Expected behavior:
1. Detects available GPU toolkits
2. Prompts for preferences
3. Shows build configuration
4. Builds package automatically
5. Asks to install

## Test Clean Chroot (Recommended)

The most reliable test - builds in isolated environment:

```bash
# Create chroot
sudo pacman -S devtools
mkdir ~/chroot

# Build in clean chroot (CPU-only)
makechrootpkg -c -r ~/chroot

# Build with CUDA
ENABLE_CUDA=1 makechrootpkg -c -r ~/chroot

# Build with Vulkan
ENABLE_VULKAN=1 makechrootpkg -c -r ~/chroot
```

This ensures:
- All dependencies are declared
- Build is reproducible
- No system-specific issues

## Test Installation

After building, test the installed package:

### 1. Verify Files

```bash
pacman -Ql gnome-assistant | head -20
```

Expected files:
- `/usr/bin/gnome-assistant-service`
- `/usr/lib/systemd/user/gnome-assistant.service`
- `/usr/share/gnome-shell/extensions/gnome-assistant@saim/`
- `/usr/share/dbus-1/services/`
- `/usr/share/gnome-assistant/config.json`

### 2. Test Service

```bash
# Copy config
mkdir -p ~/.config/gnome-assistant
cp /usr/share/gnome-assistant/config.json ~/.config/gnome-assistant/

# Start service
systemctl --user start gnome-assistant.service

# Check status
systemctl --user status gnome-assistant.service

# View logs
journalctl --user -u gnome-assistant.service -n 50
```

Expected: Service starts without errors.

### 3. Test Extension

```bash
# Enable extension
gnome-extensions enable gnome-assistant@saim

# Verify it's enabled
gnome-extensions list | grep gnome-assistant

# Check for errors
journalctl -f -o cat /usr/bin/gnome-shell | grep -i "gnome-assistant\|error"
```

Expected: Extension loads without errors, shows in panel.

### 4. Test D-Bus Interface

```bash
# Check D-Bus service
gdbus introspect --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant

# Get status
gdbus call --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant \
  --method com.github.saim.GnomeAssistant.GetStatus
```

Expected: Shows D-Bus interface, returns status.

## Test Uninstallation

```bash
# Remove package
sudo pacman -R gnome-assistant

# Verify service stopped
systemctl --user status gnome-assistant.service

# Verify extension removed
gnome-extensions list | grep gnome-assistant
```

Expected:
- Service stopped cleanly
- Extension removed
- Post-remove message shown

## Test Upgrade

```bash
# Install old version
makepkg -fi

# Make a change (bump pkgrel)
sed -i 's/pkgrel=1/pkgrel=2/' PKGBUILD

# Rebuild and upgrade
makepkg -fi

# Verify upgrade message shown
```

Expected: post_upgrade() runs, shows restart message.

## Test .SRCINFO Generation

```bash
# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Verify format
cat .SRCINFO

# Check for errors
makepkg --printsrcinfo | diff - .SRCINFO
```

Expected: No diff output (files match).

## Test Different Scenarios

### Scenario 1: Fresh Install

```bash
# Remove all related files
sudo pacman -R gnome-assistant
rm -rf ~/.config/gnome-assistant
rm -rf ~/.local/share/voice-assistant

# Fresh install
makepkg -fi

# Follow post-install instructions
```

### Scenario 2: Upgrade from Manual Install

```bash
# If previously installed via install.sh
./uninstall.sh

# Install via package
makepkg -fi
```

### Scenario 3: GPU Toggle at Runtime

```bash
# Install with GPU support
ENABLE_CUDA=1 makepkg -fi

# Start service
systemctl --user start gnome-assistant.service

# Open preferences
gnome-extensions prefs gnome-assistant@saim

# Toggle GPU acceleration
# Check logs for reload message
journalctl --user -u gnome-assistant.service -f | grep -i gpu
```

## Automated Test Script

Create a test script:

```bash
#!/bin/bash
# test-aur-package.sh

set -e

echo "=== Testing GNOME Assistant AUR Package ==="

# Test syntax
echo "1. Testing syntax..."
bash -n PKGBUILD
bash -n PKGBUILD-git
bash -n build-aur.sh
echo "   ✓ Syntax OK"

# Test build
echo "2. Testing build..."
makepkg -C -f > /dev/null 2>&1
echo "   ✓ Build OK"

# Test package
echo "3. Testing package..."
if [ -f *.pkg.tar.zst ]; then
    echo "   ✓ Package created"
else
    echo "   ✗ Package not found"
    exit 1
fi

# Test .SRCINFO generation
echo "4. Testing .SRCINFO..."
makepkg --printsrcinfo > /dev/null 2>&1
echo "   ✓ .SRCINFO OK"

echo ""
echo "All tests passed! ✓"
```

Run with: `bash test-aur-package.sh`

## Common Issues

### Issue: Build fails with missing dependencies

**Fix:** Check that all makedepends are installed:
```bash
sudo pacman -S cmake git gcc
```

### Issue: Whisper model download fails

**Fix:** Download manually:
```bash
mkdir -p ~/.local/share/voice-assistant/models
cd ~/.local/share/voice-assistant/models
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin
```

### Issue: Extension not found after install

**Fix:** Restart GNOME Shell:
- X11: Alt+F2, type 'r', Enter
- Wayland: Log out and back in

### Issue: Service won't start

**Fix:** Check logs:
```bash
journalctl --user -u gnome-assistant.service -n 100
```

Common causes:
- Missing whisper model
- Missing config file
- D-Bus service file not installed

## Checklist Before Publishing to AUR

- [ ] PKGBUILD syntax validated
- [ ] PKGBUILD-git syntax validated
- [ ] Build succeeds (CPU-only)
- [ ] Build succeeds (CUDA) if toolkit available
- [ ] Build succeeds (Vulkan) if SDK available
- [ ] Clean chroot build succeeds
- [ ] All files installed to correct paths
- [ ] Service starts successfully
- [ ] Extension loads without errors
- [ ] D-Bus interface accessible
- [ ] Post-install instructions shown
- [ ] Upgrade works correctly
- [ ] Uninstall is clean
- [ ] .SRCINFO generated correctly
- [ ] Documentation is accurate
- [ ] All dependencies declared

## Success Criteria

A successful test should demonstrate:
1. Package builds without errors
2. All dependencies are satisfied
3. Service starts and runs
4. Extension loads and functions
5. D-Bus communication works
6. GPU acceleration works (if hardware available)
7. Post-install hooks provide clear guidance
8. Uninstall is clean

## Next Steps

After successful testing:
1. Review `AUR_PACKAGING.md` for publishing instructions
2. Generate final `.SRCINFO`
3. Commit to AUR repository
4. Monitor for user feedback
5. Update as needed

## Support

If you encounter issues:
- Check existing documentation in `AUR_*.md` files
- Review logs: `journalctl --user -u gnome-assistant.service`
- File issue: https://github.com/Saim20/gnome-assistant/issues
