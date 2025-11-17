# AUR Package Submission Guide

## Pre-Submission Checklist

### 1. Test Package Build

```bash
# Test in clean environment with clean chroot
mkdir -p ~/aur-testing
cd ~/aur-testing

# Install devtools
sudo pacman -S devtools

# Create clean chroot
mkarchroot $HOME/chroot/root base-devel

# Test build
makechrootpkg -c -r $HOME/chroot

# Or test locally
makepkg -si
```

### 2. Verify Package Contents

```bash
# List package contents
tar -tzf gnome-assistant-*.pkg.tar.zst

# Should include:
# - /usr/bin/gnome-assistant-service
# - /usr/bin/gnome-assistant-download-model
# - /usr/lib/systemd/user/gnome-assistant.service
# - /usr/share/dbus-1/services/com.github.saim.GnomeAssistant.service
# - /usr/share/dbus-1/interfaces/com.github.saim.GnomeAssistant.xml
# - /usr/share/gnome-shell/extensions/gnome-assistant@saim/
# - /usr/share/gnome-assistant/config.json
# - /usr/share/doc/gnome-assistant/
# - /usr/share/licenses/gnome-assistant/LICENSE
```

### 3. Generate .SRCINFO

```bash
# Generate .SRCINFO for AUR
makepkg --printsrcinfo > .SRCINFO

# Verify it contains:
# - pkgname
# - pkgver
# - pkgrel
# - pkgdesc
# - arch
# - url
# - license
# - depends
# - makedepends
# - optdepends
```

### 4. Test Installation Flow

```bash
# Install package
sudo pacman -U gnome-assistant-*.pkg.tar.zst

# Download model
gnome-assistant-download-model

# Copy config
mkdir -p ~/.config/gnome-assistant
cp /usr/share/gnome-assistant/config.json ~/.config/gnome-assistant/

# Enable extension
gnome-extensions enable gnome-assistant@saim

# Start service
systemctl --user enable --now gnome-assistant.service

# Check status
systemctl --user status gnome-assistant.service

# Test functionality
gdbus call --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant \
  --method com.github.saim.GnomeAssistant.GetStatus
```

### 5. Test Uninstallation

```bash
# Stop service
systemctl --user stop gnome-assistant.service
systemctl --user disable gnome-assistant.service

# Disable extension
gnome-extensions disable gnome-assistant@saim

# Uninstall
sudo pacman -R gnome-assistant

# Verify removal
ls /usr/bin/gnome-assistant* 2>/dev/null
ls /usr/share/gnome-shell/extensions/gnome-assistant@saim 2>/dev/null
```

## AUR Submission

### Initial Upload

```bash
# Clone AUR repository
git clone ssh://aur@aur.archlinux.org/gnome-assistant.git aur-gnome-assistant
cd aur-gnome-assistant

# Copy files
cp ../gnome-assistant/PKGBUILD .
cp ../gnome-assistant/gnome-assistant.install .
cp ../gnome-assistant/.SRCINFO .

# Commit
git add PKGBUILD gnome-assistant.install .SRCINFO
git commit -m "Initial import of gnome-assistant"

# Push to AUR
git push
```

### Update Package

```bash
cd aur-gnome-assistant

# Update PKGBUILD (increment pkgver or pkgrel)
vim PKGBUILD

# Regenerate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Test build
makepkg -si

# Commit and push
git add PKGBUILD .SRCINFO
git commit -m "Update to version X.Y.Z"
git push
```

## Git Version (-git package)

For the development version:

```bash
# Clone git AUR repository
git clone ssh://aur@aur.archlinux.org/gnome-assistant-git.git aur-gnome-assistant-git
cd aur-gnome-assistant-git

# Copy git PKGBUILD
cp ../gnome-assistant/PKGBUILD-git PKGBUILD
cp ../gnome-assistant/gnome-assistant.install .

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Commit and push
git add PKGBUILD gnome-assistant.install .SRCINFO
git commit -m "Initial import of gnome-assistant-git"
git push
```

## Package Metadata

### PKGBUILD Header

```bash
# Maintainer: Saim <your-email@example.com>
pkgname=gnome-assistant
pkgver=2.0.0
pkgrel=1
pkgdesc="Advanced voice control for GNOME Shell with whisper.cpp offline speech recognition"
arch=('x86_64')
url="https://github.com/Saim20/gnome-assistant"
license=('MIT')
```

### Dependencies Explanation

**Runtime dependencies (depends):**
- `gnome-shell>=45` - Requires GNOME Shell 45 or newer
- `sdbus-cpp` - C++ D-Bus library for IPC
- `jsoncpp` - JSON parsing for configuration
- `libpulse` - Audio capture from microphone
- `ydotool` - Wayland input simulation for commands

**Build dependencies (makedepends):**
- `cmake` - Build system
- `git` - Clone whisper.cpp submodule
- `gcc` - C++ compiler

**Optional dependencies (optdepends):**
- `cuda` - NVIDIA GPU acceleration (if built with ENABLE_CUDA=1)
- `vulkan-icd-loader` - AMD/Intel GPU acceleration (if built with ENABLE_VULKAN=1)
- `vulkan-headers` - Vulkan build support

## Common Issues

### Build fails in clean chroot

**Problem**: Can't access $HOME to download model

**Solution**: Removed model download from build() - now done post-install

### Schema compilation fails

**Problem**: `glib-compile-schemas` returns error

**Solution**: Check if schemas directory exists before compiling

### Extension not loading

**Problem**: Extension directory permissions wrong

**Solution**: Ensure `install -dm755` for proper permissions

### Service won't start

**Problem**: Missing model file

**Solution**: User must run `gnome-assistant-download-model` post-install

## Validation Commands

```bash
# Check package for common issues
namcap gnome-assistant-*.pkg.tar.zst

# Check PKGBUILD
namcap PKGBUILD

# Check dependencies
ldd /usr/bin/gnome-assistant-service

# Verify service file
systemd-analyze verify --user gnome-assistant.service

# Check D-Bus interface
gdbus introspect --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant
```

## Package Signing

```bash
# Generate GPG key if needed
gpg --full-gen-key

# Sign package
gpg --detach-sign gnome-assistant-*.pkg.tar.zst

# Add signature to PKGBUILD (optional)
source=("gnome-assistant::git+https://github.com/Saim20/gnome-assistant.git")
sha256sums=('SKIP')
validpgpkeys=('YOUR_GPG_KEY_ID')
```

## Best Practices

1. **Version Updates**: Increment `pkgrel` for PKGBUILD changes, `pkgver` for upstream updates
2. **Testing**: Always test in clean chroot before pushing to AUR
3. **Documentation**: Keep .SRCINFO in sync with PKGBUILD
4. **Dependencies**: Only include necessary runtime dependencies
5. **Cleanup**: Remove build artifacts before packaging
6. **Post-install**: Use .install file for user instructions
7. **Licenses**: Always include LICENSE file
8. **Conflicts**: Ensure -git package conflicts with stable package

## Resources

- [AUR Submission Guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines)
- [PKGBUILD Guide](https://wiki.archlinux.org/title/PKGBUILD)
- [Creating Packages](https://wiki.archlinux.org/title/Creating_packages)
- [AUR Helper](https://wiki.archlinux.org/title/AUR_helpers)
