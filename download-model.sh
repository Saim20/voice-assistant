#!/bin/bash
# Helper script to download whisper models for GNOME Assistant

set -e

MODEL_DIR="$HOME/.local/share/gnome-assistant/models"
WHISPER_REPO="https://huggingface.co/ggerganov/whisper.cpp/resolve/main"

echo "==================================================================="
echo "GNOME Assistant - Whisper Model Downloader"
echo "==================================================================="
echo ""
echo "Available models:"
echo "  1) tiny.en    (~75MB)  - Fastest, good for commands (recommended)"
echo "  2) base.en    (~142MB) - Better accuracy, still fast"
echo "  3) small.en   (~466MB) - High accuracy, moderate speed"
echo "  4) medium.en  (~1.5GB) - Best accuracy, slower"
echo ""

# Check if model already exists
if [ -f "$MODEL_DIR/ggml-tiny.en.bin" ]; then
    echo "Note: tiny.en model already exists at:"
    echo "  $MODEL_DIR/ggml-tiny.en.bin"
    echo ""
fi

read -p "Select model to download [1-4, default: 1]: " choice
choice=${choice:-1}

case $choice in
    1)
        MODEL="tiny.en"
        SIZE="75MB"
        ;;
    2)
        MODEL="base.en"
        SIZE="142MB"
        ;;
    3)
        MODEL="small.en"
        SIZE="466MB"
        ;;
    4)
        MODEL="medium.en"
        SIZE="1.5GB"
        ;;
    *)
        echo "Invalid choice. Defaulting to tiny.en"
        MODEL="tiny.en"
        SIZE="75MB"
        ;;
esac

MODEL_FILE="ggml-$MODEL.bin"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"

echo ""
echo "Downloading: $MODEL ($SIZE)"
echo "Destination: $MODEL_PATH"
echo ""

# Create directory
mkdir -p "$MODEL_DIR"

# Download with progress
if command -v curl &> /dev/null; then
    curl -L --progress-bar "$WHISPER_REPO/$MODEL_FILE" -o "$MODEL_PATH"
elif command -v wget &> /dev/null; then
    wget --show-progress "$WHISPER_REPO/$MODEL_FILE" -O "$MODEL_PATH"
else
    echo "ERROR: Neither curl nor wget found. Please install one of them."
    exit 1
fi

echo ""
echo "==================================================================="
echo "Download complete!"
echo ""
echo "Model saved to: $MODEL_PATH"
echo ""

# If not tiny.en, update config
if [ "$MODEL" != "tiny.en" ]; then
    CONFIG_FILE="$HOME/.config/gnome-assistant/config.json"
    if [ -f "$CONFIG_FILE" ]; then
        echo "To use this model, update your config:"
        echo "  1. Open: gnome-extensions prefs gnome-assistant@saim"
        echo "  2. Go to 'General' tab"
        echo "  3. Change 'Whisper Model' to: $MODEL_FILE"
        echo ""
        echo "Or manually edit: $CONFIG_FILE"
        echo "  Change 'model_path' to: $MODEL_PATH"
    fi
fi

echo "Restart the service to use the new model:"
echo "  systemctl --user restart gnome-assistant.service"
echo "==================================================================="
