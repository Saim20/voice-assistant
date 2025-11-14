#!/bin/bash
# Helper script to build GNOME Assistant AUR package with GPU support options

set -e

echo "==================================================================="
echo "GNOME Assistant - AUR Package Build Helper"
echo "==================================================================="
echo ""
echo "This script helps you build the GNOME Assistant package with"
echo "optional GPU acceleration support."
echo ""

# Check if PKGBUILD exists
if [ ! -f "PKGBUILD" ]; then
    echo "ERROR: PKGBUILD not found in current directory"
    exit 1
fi

# Initialize build flags
ENABLE_CUDA=0
ENABLE_VULKAN=0

# Ask about CUDA
if command -v nvcc &> /dev/null || [ -d "/opt/cuda" ]; then
    echo "CUDA toolkit detected on your system."
    read -p "Build with CUDA support? [y/N]: " cuda_choice
    case "$cuda_choice" in
        [yY][eE][sS]|[yY])
            ENABLE_CUDA=1
            echo "✓ CUDA support will be enabled"
            ;;
        *)
            echo "✗ CUDA support will be disabled"
            ;;
    esac
else
    echo "CUDA toolkit not detected. Skipping CUDA support."
fi

echo ""

# Ask about Vulkan
if pacman -Qi vulkan-headers &> /dev/null 2>&1; then
    echo "Vulkan SDK detected on your system."
    read -p "Build with Vulkan support? [y/N]: " vulkan_choice
    case "$vulkan_choice" in
        [yY][eE][sS]|[yY])
            ENABLE_VULKAN=1
            echo "✓ Vulkan support will be enabled"
            ;;
        *)
            echo "✗ Vulkan support will be disabled"
            ;;
    esac
else
    echo "Vulkan SDK not detected. Skipping Vulkan support."
fi

echo ""
echo "==================================================================="
echo "Build Configuration:"
echo "  CUDA: $([ $ENABLE_CUDA -eq 1 ] && echo 'enabled' || echo 'disabled')"
echo "  Vulkan: $([ $ENABLE_VULKAN -eq 1 ] && echo 'enabled' || echo 'disabled')"
echo "==================================================================="
echo ""

# Ask for confirmation
read -p "Proceed with build? [Y/n]: " proceed
case "$proceed" in
    [nN][oO]|[nN])
        echo "Build cancelled."
        exit 0
        ;;
esac

echo ""
echo "Starting build..."
echo ""

# Export environment variables and build
export ENABLE_CUDA
export ENABLE_VULKAN

# Run makepkg with user's preferred flags
if [ -z "$MAKEPKG_FLAGS" ]; then
    MAKEPKG_FLAGS="-si"
fi

makepkg $MAKEPKG_FLAGS

echo ""
echo "==================================================================="
echo "Build complete!"
echo ""
echo "If installation succeeded, follow these steps:"
echo ""
echo "1. Copy default configuration:"
echo "   mkdir -p ~/.config/gnome-assistant"
echo "   cp /usr/share/gnome-assistant/config.json ~/.config/gnome-assistant/"
echo ""
echo "2. Enable GNOME extension:"
echo "   gnome-extensions enable gnome-assistant@saim"
echo ""
echo "3. Start the service:"
echo "   systemctl --user enable --now gnome-assistant.service"
echo ""
echo "4. Setup ydotool (for keyboard commands):"
echo "   sudo systemctl enable --now ydotool"
echo "   sudo usermod -aG input \$USER"
echo "   (then log out and back in)"
echo ""
echo "Documentation: /usr/share/doc/gnome-assistant/"
echo "==================================================================="
