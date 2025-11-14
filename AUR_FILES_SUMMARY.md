# AUR Package Files Summary

This document provides a quick reference to all AUR-related files in this repository.

## Core Package Files

| File | Size | Purpose |
|------|------|---------|
| `PKGBUILD` | 5.4K | Main AUR package for stable releases |
| `PKGBUILD-git` | 5.8K | Development version (tracks git master) |
| `gnome-assistant.install` | 1.9K | Install/upgrade/removal hooks |
| `.SRCINFO.template` | 837B | Template for .SRCINFO generation |

## User Tools

| File | Size | Purpose |
|------|------|---------|
| `build-aur.sh` | 3.2K | Interactive build helper with GPU detection |

## Documentation

| File | Size | Purpose |
|------|------|---------|
| `AUR.md` | 4.0K | Complete AUR package summary |
| `AUR_README.md` | 4.8K | User installation guide |
| `AUR_PACKAGING.md` | 7.6K | Maintainer's guide |
| `QUICKSTART_AUR.md` | 2.1K | Quick reference |
| `SRCINFO_HOWTO.md` | 1.8K | .SRCINFO generation guide |

## Quick Reference

### For Users

**Install (CPU-only):**
```bash
makepkg -si
```

**Install with NVIDIA GPU:**
```bash
ENABLE_CUDA=1 makepkg -si
```

**Install with AMD/Intel GPU:**
```bash
ENABLE_VULKAN=1 makepkg -si
```

**Interactive build:**
```bash
./build-aur.sh
```

### For Maintainers

**Generate .SRCINFO:**
```bash
makepkg --printsrcinfo > .SRCINFO
```

**Publish to AUR:**
```bash
git clone ssh://aur@aur.archlinux.org/gnome-assistant.git
cd gnome-assistant
cp /path/to/{PKGBUILD,gnome-assistant.install} .
makepkg --printsrcinfo > .SRCINFO
git add PKGBUILD gnome-assistant.install .SRCINFO
git commit -m "Initial import: gnome-assistant 2.0.0"
git push
```

## Documentation Map

- **New to AUR?** Start with `AUR_README.md`
- **Want quick install?** See `QUICKSTART_AUR.md`
- **Maintaining the package?** Read `AUR_PACKAGING.md`
- **Need .SRCINFO help?** Check `SRCINFO_HOWTO.md`
- **Overview?** See `AUR.md`

## Build Options

The PKGBUILD supports optional GPU acceleration:

### Environment Variables
- `ENABLE_CUDA=1` - Enable NVIDIA CUDA support
- `ENABLE_VULKAN=1` - Enable Vulkan support

### Examples
```bash
# CPU only (default)
makepkg -si

# CUDA only
ENABLE_CUDA=1 makepkg -si

# Vulkan only
ENABLE_VULKAN=1 makepkg -si

# Both
ENABLE_CUDA=1 ENABLE_VULKAN=1 makepkg -si
```

## File Relationships

```
PKGBUILD ──────────────┐
                       ├──> Used by makepkg
PKGBUILD-git ──────────┤
                       │
gnome-assistant.install┘

build-aur.sh ──> Interactive wrapper for makepkg

.SRCINFO.template ──> Template for AUR submission

AUR.md ────────────────┐
AUR_README.md ─────────├──> User Documentation
QUICKSTART_AUR.md ─────┘

AUR_PACKAGING.md ──────┬──> Maintainer Documentation
SRCINFO_HOWTO.md ──────┘
```

## What Each File Does

### PKGBUILD
- Defines package metadata (name, version, dependencies)
- Implements prepare(), build(), and package() functions
- Handles optional CUDA/Vulkan support
- Downloads whisper.cpp and builds service
- Installs all components to correct paths

### PKGBUILD-git
- Same as PKGBUILD but tracks git master
- Includes pkgver() function for version generation
- Used for development/testing builds

### gnome-assistant.install
- post_install(): Shows setup instructions after first install
- post_upgrade(): Reminds to restart service after upgrade
- pre_remove(): Stops service before removal
- post_remove(): Explains how to clean up user data

### build-aur.sh
- Detects CUDA/Vulkan availability
- Prompts user for GPU preferences
- Sets environment variables
- Runs makepkg with correct flags

### Documentation Files
- **AUR.md**: High-level overview and quick reference
- **AUR_README.md**: Complete installation guide for users
- **AUR_PACKAGING.md**: In-depth guide for package maintainers
- **QUICKSTART_AUR.md**: TL;DR commands for common tasks
- **SRCINFO_HOWTO.md**: How to generate and validate .SRCINFO

## Integration with Existing Files

The AUR package integrates with existing build system:
- Uses existing `service/CMakeLists.txt`
- References existing `config.json`
- Installs existing GNOME extension
- Uses existing systemd service file
- Includes existing documentation

## Dependencies

### Runtime (depends)
- gnome-shell (≥45)
- sdbus-cpp
- jsoncpp
- libpulse
- ydotool

### Build (makedepends)
- cmake
- git
- gcc

### Optional (optdepends)
- cuda (NVIDIA GPU acceleration)
- vulkan-icd-loader (Vulkan runtime)
- vulkan-headers (Vulkan build support)

## Testing

All shell scripts validated:
```bash
bash -n PKGBUILD         # ✓ OK
bash -n PKGBUILD-git     # ✓ OK
bash -n build-aur.sh     # ✓ OK
```

## Next Steps

1. **For Users**: See `QUICKSTART_AUR.md`
2. **For Testing**: Run `./build-aur.sh`
3. **For Publishing**: Follow `AUR_PACKAGING.md`
4. **For Updates**: Modify PKGBUILD, regenerate .SRCINFO

## Support

- Documentation: All `AUR_*.md` files
- Issues: https://github.com/Saim20/gnome-assistant/issues
- AUR: https://aur.archlinux.org/packages/gnome-assistant (when published)
