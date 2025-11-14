# AUR Packaging Guide for GNOME Assistant

This guide explains the AUR (Arch User Repository) packaging for GNOME Assistant.

## Files Overview

- `PKGBUILD` - Main package build script for stable releases
- `PKGBUILD-git` - Development version (tracks git master)
- `gnome-assistant.install` - Post-install, upgrade, and removal scripts
- `AUR_README.md` - User-facing installation instructions
- `build-aur.sh` - Interactive build helper script
- `SRCINFO_HOWTO.md` - Instructions for generating .SRCINFO

## Package Variants

### gnome-assistant (Stable)

The main package that tracks tagged releases.

**Source:** `PKGBUILD`

**Installation:**
```bash
git clone https://aur.archlinux.org/gnome-assistant.git
cd gnome-assistant
makepkg -si
```

### gnome-assistant-git (Development)

Tracks the latest git master branch for testing new features.

**Source:** `PKGBUILD-git`

**Installation:**
```bash
git clone https://aur.archlinux.org/gnome-assistant-git.git
cd gnome-assistant-git
makepkg -si
```

## GPU Acceleration Support

Both PKGBUILDs support optional GPU acceleration through build-time configuration.

### Method 1: Environment Variables (Recommended)

```bash
# CUDA only
ENABLE_CUDA=1 makepkg -si

# Vulkan only
ENABLE_VULKAN=1 makepkg -si

# Both
ENABLE_CUDA=1 ENABLE_VULKAN=1 makepkg -si
```

### Method 2: Interactive Helper Script

```bash
./build-aur.sh
```

The script will:
1. Detect available GPU toolkits
2. Ask user preferences
3. Build with selected options

### Method 3: Edit PKGBUILD

Edit the PKGBUILD and modify these lines:

```bash
: ${ENABLE_CUDA:=1}      # Change 0 to 1 for CUDA
: ${ENABLE_VULKAN:=1}    # Change 0 to 1 for Vulkan
```

Then build normally: `makepkg -si`

## Dependencies

### Required (Runtime)
- `gnome-shell>=45` - GNOME Shell 45 or newer
- `sdbus-cpp` - D-Bus C++ bindings
- `jsoncpp` - JSON parsing library
- `libpulse` - PulseAudio client library
- `ydotool` - Wayland input simulation

### Required (Build)
- `cmake` - Build system
- `git` - Version control (for cloning whisper.cpp)
- `gcc` - C/C++ compiler

### Optional (GPU Acceleration)
- `cuda` - NVIDIA CUDA toolkit (for CUDA support)
- `vulkan-icd-loader` - Vulkan runtime (for Vulkan support)
- `vulkan-headers` - Vulkan development headers (for building with Vulkan)

## Build Process

### 1. Prepare Phase

- Clones whisper.cpp repository
- Displays build configuration
- Checks for GPU toolkit dependencies
- Shows warnings if GPU support requested but toolkit not found

### 2. Build Phase

**Whisper.cpp:**
- Downloads tiny.en model (~75MB) to `~/.local/share/voice-assistant/models/`
- Configures with selected GPU backend(s)
- Builds whisper.cpp library

**GNOME Assistant Service:**
- Links against whisper.cpp
- Configures with matching GPU settings
- Builds the C++ D-Bus service

### 3. Package Phase

Installs:
- `/usr/bin/gnome-assistant-service` - Main service binary
- `/usr/lib/systemd/user/gnome-assistant.service` - Systemd user service
- `/usr/share/gnome-shell/extensions/gnome-assistant@saim/` - GNOME extension
- `/usr/share/dbus-1/services/` - D-Bus service file
- `/usr/share/dbus-1/interfaces/` - D-Bus interface definition
- `/usr/share/gnome-assistant/config.json` - Default configuration
- `/usr/share/doc/gnome-assistant/` - Documentation

## Post-Install Scripts

The `gnome-assistant.install` file provides:

### post_install()
- Displays setup instructions
- Guides user through:
  - Configuration file setup
  - Extension enablement
  - Service activation
  - ydotool configuration

### post_upgrade()
- Reminds user to restart service after upgrade

### pre_remove()
- Stops and disables the service
- Prevents service errors during removal

### post_remove()
- Explains how to clean up user data
- Lists configuration and model directories

## Testing the Package

### Local Testing

```bash
# Build only (don't install)
makepkg

# Build and install
makepkg -si

# Clean build
makepkg -C && makepkg -si
```

### Verify Installation

```bash
# Check service binary
ls -l /usr/bin/gnome-assistant-service

# Check extension
gnome-extensions list | grep gnome-assistant

# Check service file
systemctl --user cat gnome-assistant.service

# Check for GPU libraries (if built with GPU support)
ldd /usr/bin/gnome-assistant-service | grep -i cuda
ldd /usr/bin/gnome-assistant-service | grep -i vulkan
```

### Test Functionality

```bash
# Start service
systemctl --user start gnome-assistant.service

# Check status
systemctl --user status gnome-assistant.service

# View logs
journalctl --user -u gnome-assistant.service -f

# Enable extension
gnome-extensions enable gnome-assistant@saim
```

## Publishing to AUR

### Initial Submission

1. Create AUR account at https://aur.archlinux.org
2. Add SSH key to AUR account
3. Clone AUR repository:
   ```bash
   git clone ssh://aur@aur.archlinux.org/gnome-assistant.git
   cd gnome-assistant
   ```
4. Copy files:
   ```bash
   cp /path/to/PKGBUILD .
   cp /path/to/gnome-assistant.install .
   ```
5. Generate .SRCINFO:
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```
6. Commit and push:
   ```bash
   git add PKGBUILD gnome-assistant.install .SRCINFO
   git commit -m "Initial import: gnome-assistant 2.0.0"
   git push
   ```

### Updates

1. Update PKGBUILD (increment pkgver or pkgrel)
2. Update .SRCINFO: `makepkg --printsrcinfo > .SRCINFO`
3. Test build: `makepkg -si`
4. Commit and push:
   ```bash
   git add PKGBUILD .SRCINFO
   git commit -m "Update to version X.Y.Z"
   git push
   ```

### Both Packages

Maintain both `gnome-assistant` and `gnome-assistant-git`:

```bash
# For stable package
git clone ssh://aur@aur.archlinux.org/gnome-assistant.git

# For git package
git clone ssh://aur@aur.archlinux.org/gnome-assistant-git.git
```

Use `PKGBUILD` for stable, `PKGBUILD-git` for development.

## Troubleshooting

### Build Failures

**Issue: Whisper.cpp fails to build with CUDA**
- Ensure CUDA toolkit is installed: `pacman -S cuda`
- Check CUDA path: `ls -l /opt/cuda`

**Issue: Vulkan not found**
- Install headers: `pacman -S vulkan-headers`
- Verify: `ls /usr/include/vulkan/vulkan.h`

**Issue: Missing dependencies**
- Install build deps: `pacman -S cmake gcc git`
- Install runtime deps: `pacman -S sdbus-cpp jsoncpp libpulse ydotool`

### Installation Issues

**Issue: Extension not found after install**
- Reinstall: `pacman -R gnome-assistant && pacman -S gnome-assistant`
- Check path: `ls /usr/share/gnome-shell/extensions/gnome-assistant@saim`

**Issue: Service won't start**
- Check model: `ls ~/.local/share/voice-assistant/models/ggml-tiny.en.bin`
- View errors: `journalctl --user -u gnome-assistant.service`

## Best Practices

1. **Version Management**
   - Keep pkgver in sync with upstream releases
   - Increment pkgrel for packaging-only changes
   - Reset pkgrel to 1 when pkgver changes

2. **Dependency Management**
   - Keep depends= minimal (only runtime requirements)
   - Use optdepends= for optional features
   - Put build-only tools in makedepends=

3. **GPU Support**
   - Default to CPU-only (most users)
   - Make GPU support opt-in via environment variables
   - Document GPU options clearly

4. **Testing**
   - Always test in a clean chroot
   - Test both with and without GPU support
   - Verify post-install instructions work

5. **Documentation**
   - Keep AUR_README.md updated
   - Include GPU build instructions
   - Document troubleshooting steps

## Resources

- AUR Guidelines: https://wiki.archlinux.org/title/AUR_submission_guidelines
- PKGBUILD Reference: https://wiki.archlinux.org/title/PKGBUILD
- Arch Packaging Standards: https://wiki.archlinux.org/title/Arch_package_guidelines
- AUR Helpers: https://wiki.archlinux.org/title/AUR_helpers
