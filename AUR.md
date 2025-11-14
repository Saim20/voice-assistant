# AUR Package Summary

This repository includes complete AUR (Arch User Repository) packaging for GNOME Assistant.

## 📦 What's Included

### Package Files
- **PKGBUILD** - Stable release package
- **PKGBUILD-git** - Development version package  
- **gnome-assistant.install** - Installation hooks and user guidance

### User Tools
- **build-aur.sh** - Interactive build helper with GPU detection
- **QUICKSTART_AUR.md** - Quick reference for common scenarios

### Documentation
- **AUR_README.md** - Complete user installation guide
- **AUR_PACKAGING.md** - Maintainer's guide for publishing to AUR
- **SRCINFO_HOWTO.md** - How to generate .SRCINFO files

## 🚀 Quick Start

### Install (CPU-only)
```bash
makepkg -si
```

### Install with GPU Support
```bash
# NVIDIA (CUDA)
ENABLE_CUDA=1 makepkg -si

# AMD/Intel (Vulkan)
ENABLE_VULKAN=1 makepkg -si

# Both
ENABLE_CUDA=1 ENABLE_VULKAN=1 makepkg -si
```

### Interactive Build
```bash
./build-aur.sh
```

## 🎯 Features

### Optional GPU Acceleration
- **CUDA** for NVIDIA GPUs
- **Vulkan** for AMD/Intel/NVIDIA GPUs
- **Both backends** simultaneously
- **CPU-only** as default

### User-Friendly
- Interactive build script with GPU detection
- Clear post-install instructions
- Automatic service setup guidance
- Comprehensive troubleshooting docs

### Proper Arch Packaging
- Follows AUR submission guidelines
- Clean dependency separation
- Install/upgrade/removal hooks
- Standard installation paths

## 📚 Documentation

| File | Purpose |
|------|---------|
| [AUR_README.md](AUR_README.md) | User installation guide |
| [AUR_PACKAGING.md](AUR_PACKAGING.md) | Maintainer's guide |
| [QUICKSTART_AUR.md](QUICKSTART_AUR.md) | Quick reference |
| [SRCINFO_HOWTO.md](SRCINFO_HOWTO.md) | .SRCINFO generation |

## 🔧 For AUR Maintainers

### Initial Publication

```bash
# Clone AUR repository
git clone ssh://aur@aur.archlinux.org/gnome-assistant.git

# Copy PKGBUILD and install file
cp PKGBUILD gnome-assistant.install gnome-assistant/

# Generate .SRCINFO
cd gnome-assistant
makepkg --printsrcinfo > .SRCINFO

# Publish
git add PKGBUILD gnome-assistant.install .SRCINFO
git commit -m "Initial import: gnome-assistant 2.0.0"
git push
```

### Updates

```bash
# Edit PKGBUILD (update pkgver/pkgrel)
# Regenerate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Test
makepkg -si

# Publish
git add PKGBUILD .SRCINFO
git commit -m "Update to X.Y.Z"
git push
```

## 🛠️ Build Process

1. **prepare()** - Clones whisper.cpp, shows configuration
2. **build()** - Builds whisper.cpp and service with optional GPU support
3. **package()** - Installs service, extension, config, and docs
4. **post_install()** - Displays setup instructions

## 📋 Requirements

### Runtime Dependencies
- gnome-shell (≥45)
- sdbus-cpp
- jsoncpp
- libpulse
- ydotool

### Build Dependencies
- cmake
- git
- gcc

### Optional (GPU)
- cuda (NVIDIA)
- vulkan-headers + vulkan-icd-loader (AMD/Intel/NVIDIA)

## 💡 Usage Examples

### Standard Install
```bash
git clone https://github.com/Saim20/gnome-assistant.git
cd gnome-assistant
makepkg -si
```

### With NVIDIA GPU
```bash
sudo pacman -S cuda
ENABLE_CUDA=1 makepkg -si
```

### With AMD/Intel GPU
```bash
sudo pacman -S vulkan-headers vulkan-icd-loader
ENABLE_VULKAN=1 makepkg -si
```

### Both GPU Backends
```bash
sudo pacman -S cuda vulkan-headers vulkan-icd-loader
ENABLE_CUDA=1 ENABLE_VULKAN=1 makepkg -si
```

### Interactive (Recommended for New Users)
```bash
./build-aur.sh
```

## 🐛 Troubleshooting

See [AUR_README.md](AUR_README.md) for detailed troubleshooting.

Quick checks:
```bash
# Verify service
systemctl --user status gnome-assistant.service

# Check extension
gnome-extensions list | grep gnome-assistant

# View logs
journalctl --user -u gnome-assistant.service -f
```

## 📄 License

MIT License - See LICENSE file

## 🔗 Links

- **GitHub**: https://github.com/Saim20/gnome-assistant
- **Issues**: https://github.com/Saim20/gnome-assistant/issues
- **AUR** (when published): https://aur.archlinux.org/packages/gnome-assistant
