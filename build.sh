#!/bin/bash
# Build script for Voice Assistant Service

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$PROJECT_DIR/service/build"
INSTALL_PREFIX="$HOME/.local"

echo "=== Building Voice Assistant Service ==="
echo "Project: $PROJECT_DIR"
echo "Build directory: $BUILD_DIR"
echo "Install prefix: $INSTALL_PREFIX"
echo

# Check for dependencies
echo "Checking dependencies..."
DEPS_OK=true

# Check for CMake
if ! command -v cmake &> /dev/null; then
    echo "ERROR: cmake not found. Install with: sudo dnf install cmake"
    DEPS_OK=false
fi

# Check for sdbus-c++
if ! pkg-config --exists sdbus-c++; then
    echo "ERROR: sdbus-c++ not found. Install with: sudo dnf install sdbus-c++-devel"
    DEPS_OK=false
fi

# Check for jsoncpp
if ! pkg-config --exists jsoncpp; then
    echo "ERROR: jsoncpp not found. Install with: sudo dnf install jsoncpp-devel"
    DEPS_OK=false
fi

# Check for PulseAudio
if ! pkg-config --exists libpulse-simple; then
    echo "WARNING: libpulse-simple not found. Audio capture may not work."
    echo "Install with: sudo dnf install pulseaudio-libs-devel"
fi

if [ "$DEPS_OK" = false ]; then
    echo
    echo "Missing dependencies. Please install them and try again."
    exit 1
fi

echo "All dependencies found!"
echo

# Check for whisper.cpp
if [ ! -d "$PROJECT_DIR/whisper.cpp" ]; then
    echo "Whisper.cpp not found. Cloning..."
    git clone https://github.com/ggerganov/whisper.cpp.git "$PROJECT_DIR/whisper.cpp"
    echo
fi

# Download whisper model if needed
MODEL_DIR="$HOME/.local/share/voice-assistant/models"
MODEL_FILE="$MODEL_DIR/ggml-tiny.en.bin"

if [ ! -f "$MODEL_FILE" ]; then
    echo "Whisper model not found. Downloading tiny.en model (~75MB)..."
    mkdir -p "$MODEL_DIR"
    
    cd "$PROJECT_DIR/whisper.cpp"
    bash models/download-ggml-model.sh tiny.en
    
    # Move model to proper location
    if [ -f "models/ggml-tiny.en.bin" ]; then
        mv models/ggml-tiny.en.bin "$MODEL_FILE"
        echo "Model downloaded to $MODEL_FILE"
    fi
    
    cd "$PROJECT_DIR"
    echo
fi

# Create build directory
echo "Creating build directory..."
mkdir -p "$BUILD_DIR"

# Configure
echo "Configuring..."
cd "$BUILD_DIR"
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" \
    -DWHISPER_CPP_DIR="$PROJECT_DIR/whisper.cpp"

echo

# Build
echo "Building..."
cmake --build . --parallel $(nproc)

echo
echo "=== Build Complete ==="
echo
echo "To install, run: ./install.sh"
echo "Or manually: cd service/build && cmake --install ."
