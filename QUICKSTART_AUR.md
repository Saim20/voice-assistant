# Quick Start: Building GNOME Assistant from AUR

## TL;DR - CPU Only (Default)

```bash
# Clone this repository
git clone https://github.com/Saim20/gnome-assistant.git
cd gnome-assistant

# Build and install
makepkg -si

# Download whisper model (tiny.en recommended)
gnome-assistant-download-model

# Setup
mkdir -p ~/.config/gnome-assistant
cp /usr/share/gnome-assistant/config.json ~/.config/gnome-assistant/
gnome-extensions enable gnome-assistant@saim
systemctl --user enable --now gnome-assistant.service
```

## TL;DR - With GPU Acceleration

### NVIDIA GPU (CUDA)

```bash
# Install CUDA
sudo pacman -S cuda

# Build with CUDA
ENABLE_CUDA=1 makepkg -si
```

### AMD/Intel GPU (Vulkan)

```bash
# Install Vulkan
sudo pacman -S vulkan-headers vulkan-icd-loader

# Build with Vulkan
ENABLE_VULKAN=1 makepkg -si
```

### Both CUDA and Vulkan

```bash
ENABLE_CUDA=1 ENABLE_VULKAN=1 makepkg -si
```

## Interactive Build Helper

```bash
./build-aur.sh
```

This script will:
- Detect your GPU hardware
- Ask which backends to enable
- Build with your selections

## Post-Installation

### Enable ydotool (Required for Wayland)

```bash
sudo systemctl enable --now ydotool
sudo usermod -aG input $USER
# Log out and back in
```

### Configure

```bash
# Via GUI
gnome-extensions prefs gnome-assistant@saim

# Or edit config
nano ~/.config/gnome-assistant/config.json
```

### Enable GPU at Runtime

After building with GPU support, you can toggle it:

1. Open preferences: `gnome-extensions prefs gnome-assistant@saim`
2. Go to "General" tab
3. Toggle "GPU Acceleration"
4. Click "Sync to Service"

## Documentation

- Full README: `README.md`
- Getting Started: `GETTING_STARTED.md`
- AUR Packaging: `AUR_PACKAGING.md`
- GPU Guide: `docs/GPU_ACCELERATION.md`

## Common Issues

**Service won't start:**
```bash
journalctl --user -u gnome-assistant.service -f
```

**Extension not found:**
```bash
gnome-extensions enable gnome-assistant@saim
```

**ydotool not working:**
```bash
sudo systemctl status ydotool
ydotool type "test"
```

## Support

- GitHub Issues: https://github.com/Saim20/gnome-assistant/issues
- Documentation: `/usr/share/doc/gnome-assistant/`
