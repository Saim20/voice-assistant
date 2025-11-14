# GNOME Assistant - AUR Package

This is the Arch User Repository (AUR) package for GNOME Assistant, an advanced voice control system for GNOME Shell with whisper.cpp offline speech recognition.

## Installation

### Basic Installation (CPU-only)

```bash
# Clone from AUR (when published)
git clone https://aur.archlinux.org/gnome-assistant.git
cd gnome-assistant

# Build and install
makepkg -si
```

### Installation with GPU Acceleration

You can enable GPU acceleration during the build process using environment variables.

#### NVIDIA GPU (CUDA)

1. Install CUDA toolkit:
```bash
sudo pacman -S cuda
# Or from AUR: yay -S cuda
```

2. Build with CUDA support:
```bash
ENABLE_CUDA=1 makepkg -si
```

#### AMD/Intel GPU (Vulkan)

1. Install Vulkan development packages:
```bash
sudo pacman -S vulkan-headers vulkan-icd-loader
```

2. Build with Vulkan support:
```bash
ENABLE_VULKAN=1 makepkg -si
```

#### Both CUDA and Vulkan

You can enable both backends simultaneously:

```bash
ENABLE_CUDA=1 ENABLE_VULKAN=1 makepkg -si
```

### Alternative: Edit PKGBUILD

You can also enable GPU support by editing the `PKGBUILD` file directly before building:

```bash
# Edit PKGBUILD
nano PKGBUILD

# Find these lines and change 0 to 1:
: ${ENABLE_CUDA:=1}      # Enable CUDA
: ${ENABLE_VULKAN:=1}    # Enable Vulkan

# Then build
makepkg -si
```

## Post-Installation Setup

After installation, follow these steps:

### 1. Copy Default Configuration

```bash
mkdir -p ~/.config/gnome-assistant
cp /usr/share/gnome-assistant/config.json ~/.config/gnome-assistant/
```

### 2. Enable GNOME Extension

```bash
gnome-extensions enable gnome-assistant@saim
```

### 3. Start the Service

```bash
systemctl --user enable --now gnome-assistant.service
```

### 4. Setup ydotool (for Wayland keyboard simulation)

```bash
# Enable ydotool service
sudo systemctl enable --now ydotool

# Add your user to input group
sudo usermod -aG input $USER

# Log out and back in for changes to take effect
```

### 5. Configure

Open extension preferences:
```bash
gnome-extensions prefs gnome-assistant@saim
```

## GPU Acceleration Configuration

After installation with GPU support, you can enable/disable GPU acceleration at runtime:

1. Open extension preferences: `gnome-extensions prefs gnome-assistant@saim`
2. Go to the "General" tab
3. Toggle "GPU Acceleration"
4. Click "Sync to Service"

Changes take effect immediately without restarting the service.

## Verifying GPU Support

Check if the service was built with GPU support:

```bash
# Check for CUDA libraries
ldd /usr/bin/gnome-assistant-service | grep -i cuda

# Check for Vulkan libraries
ldd /usr/bin/gnome-assistant-service | grep -i vulkan

# View service logs
journalctl --user -u gnome-assistant.service | grep -i "gpu\|cuda\|vulkan"
```

## Dependencies

### Required
- `gnome-shell>=45` - GNOME Shell (versions 45-49 supported)
- `sdbus-cpp` - D-Bus C++ library
- `jsoncpp` - JSON library
- `libpulse` - PulseAudio library for audio capture
- `ydotool` - Wayland input simulation

### Optional (for GPU acceleration)
- `cuda` - NVIDIA CUDA toolkit (for CUDA support)
- `vulkan-icd-loader` - Vulkan runtime (for Vulkan support)
- `vulkan-headers` - Vulkan headers (for building with Vulkan)

## Troubleshooting

### Service won't start

```bash
# Check service status
systemctl --user status gnome-assistant.service

# View logs
journalctl --user -u gnome-assistant.service -f

# Ensure whisper model exists
ls -lh ~/.local/share/voice-assistant/models/ggml-tiny.en.bin
```

### GNOME Extension not working

```bash
# Verify extension is enabled
gnome-extensions list | grep gnome-assistant

# Enable if disabled
gnome-extensions enable gnome-assistant@saim

# Restart GNOME Shell (X11: Alt+F2, type 'r', Enter)
# On Wayland, log out and back in
```

### ydotool not working

```bash
# Check if ydotool daemon is running
sudo systemctl status ydotool

# Or for user service
systemctl --user status ydotoold

# Test ydotool
ydotool type "test"
```

## Documentation

Installed documentation:
- `/usr/share/doc/gnome-assistant/README.md` - Full documentation
- `/usr/share/doc/gnome-assistant/GETTING_STARTED.md` - Quick start guide
- `/usr/share/doc/gnome-assistant/GPU_ACCELERATION.md` - GPU acceleration guide

Online:
- GitHub: https://github.com/Saim20/gnome-assistant
- Issues: https://github.com/Saim20/gnome-assistant/issues

## Uninstallation

To remove the package:

```bash
sudo pacman -R gnome-assistant
```

To also remove configuration and models:

```bash
rm -rf ~/.config/gnome-assistant
rm -rf ~/.local/share/voice-assistant
```

## Building from Source

If you prefer to build from source without using AUR:

```bash
git clone https://github.com/Saim20/gnome-assistant.git
cd gnome-assistant
./build.sh
./install.sh
```

## License

MIT License - See LICENSE file in the source repository.
