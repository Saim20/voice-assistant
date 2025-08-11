#!/bin/bash
"""
Enhanced Voice Assistant Launcher
Launches the voice assistant with GUI and nerd-dictation integration
"""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/nerd-dictation"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🎤 Voice Assistant Enhanced Launcher${NC}"
echo "=================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a process is running
is_running() {
    pgrep -f "$1" >/dev/null
}

# Check dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

if ! command_exists "nerd-dictation"; then
    echo -e "${RED}❌ nerd-dictation not found${NC}"
    echo "Please install nerd-dictation first: https://github.com/ideasman42/nerd-dictation"
    exit 1
fi

if ! command_exists "ydotool"; then
    echo -e "${YELLOW}⚠️  ydotool not found, installing...${NC}"
    if command_exists "apt"; then
        sudo apt update && sudo apt install -y ydotool
    elif command_exists "dnf"; then
        sudo dnf install -y ydotool
    elif command_exists "pacman"; then
        sudo pacman -S ydotool
    else
        echo -e "${RED}❌ Please install ydotool manually${NC}"
        exit 1
    fi
fi

if ! python3 -c "import fuzzyfinder" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing fuzzyfinder...${NC}"
    pip3 install --user fuzzyfinder
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  tkinter not found, installing...${NC}"
    if command_exists "apt"; then
        sudo apt install -y python3-tk
    else
        echo -e "${RED}❌ Please install python3-tkinter manually${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ All dependencies satisfied${NC}"

# Ensure ydotool daemon is running
if ! is_running "ydotoold"; then
    echo -e "${BLUE}Starting ydotool daemon...${NC}"
    ydotoold &
    sleep 2
fi

# Parse command line arguments
LAUNCH_GUI=true
LAUNCH_DICTATION=true
VOSK_MODEL=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-gui)
            LAUNCH_GUI=false
            shift
            ;;
        --no-dictation)
            LAUNCH_DICTATION=false
            shift
            ;;
        --model-dir)
            VOSK_MODEL="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-gui          Don't launch the GUI"
            echo "  --no-dictation    Don't launch nerd-dictation"
            echo "  --model-dir DIR   Specify Vosk model directory"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Auto-detect Vosk model if not specified
if [[ -z "$VOSK_MODEL" ]]; then
    if [[ -d "$CONFIG_DIR/model" ]]; then
        VOSK_MODEL="$CONFIG_DIR/model"
    elif [[ -d "$CONFIG_DIR/vosk-model-small-en-us-0.15" ]]; then
        VOSK_MODEL="$CONFIG_DIR/vosk-model-small-en-us-0.15"
    elif [[ -d "$CONFIG_DIR/bak/vosk-model-small-en-us-0.15" ]]; then
        VOSK_MODEL="$CONFIG_DIR/bak/vosk-model-small-en-us-0.15"
    else
        echo -e "${RED}❌ No Vosk model found. Please download a model first.${NC}"
        echo "You can download models from: https://alphacephei.com/vosk/models"
        exit 1
    fi
fi

echo -e "${GREEN}Using Vosk model: $VOSK_MODEL${NC}"

# Kill existing processes if running
if is_running "nerd-dictation"; then
    echo -e "${YELLOW}Stopping existing nerd-dictation...${NC}"
    pkill -f "nerd-dictation"
    sleep 1
fi

# Reset assistant state
echo -e "${BLUE}Resetting assistant state...${NC}"
echo "normal" > "/tmp/nerd-dictation.mode"
echo "0" > "/tmp/nerd-dictation.cursor"
echo "0" > "/tmp/nerd-dictation.typing-cursor"

# Launch GUI if requested
if [[ "$LAUNCH_GUI" == true ]]; then
    echo -e "${BLUE}🖥️  Launching GUI...${NC}"
    cd "$CONFIG_DIR"
    python3 gui.py &
    GUI_PID=$!
    sleep 2
    echo -e "${GREEN}✅ GUI launched (PID: $GUI_PID)${NC}"
fi

# Launch nerd-dictation if requested
if [[ "$LAUNCH_DICTATION" == true ]]; then
    echo -e "${BLUE}🎤 Starting nerd-dictation...${NC}"
    cd "$CONFIG_DIR"
    
    # Use the enhanced voice assistant
    nerd-dictation begin \
        --config "$CONFIG_DIR/voice_assistant_improved.py" \
        --vosk-model-dir="$VOSK_MODEL" \
        --simulate-input-tool=YDOTOOL &
    
    DICTATION_PID=$!
    sleep 2
    
    # Create status file
    touch "/tmp/nerd-dictation.status"
    
    echo -e "${GREEN}✅ Nerd-dictation started (PID: $DICTATION_PID)${NC}"
fi

echo ""
echo -e "${PURPLE}🎉 Voice Assistant is ready!${NC}"
echo ""
echo -e "${CYAN}Usage:${NC}"
echo "  • Say '${YELLOW}hey${NC}' to activate command mode"
echo "  • Say '${YELLOW}typing mode${NC}' to start dictation"
echo "  • Say '${YELLOW}normal mode${NC}' to return to standby"
echo ""
echo -e "${CYAN}Controls:${NC}"
echo "  • Use the GUI to monitor status and test commands"
echo "  • Press Ctrl+C to stop all processes"
echo ""

# Wait for interrupt
trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; pkill -f "nerd-dictation"; pkill -f "gui.py"; rm -f "/tmp/nerd-dictation.status"; exit 0' INT

# Keep script running
if [[ "$LAUNCH_DICTATION" == true ]] || [[ "$LAUNCH_GUI" == true ]]; then
    echo -e "${BLUE}Press Ctrl+C to stop all processes${NC}"
    while true; do
        sleep 1
        
        # Check if processes are still running
        if [[ "$LAUNCH_DICTATION" == true ]] && ! is_running "nerd-dictation"; then
            echo -e "${RED}❌ nerd-dictation stopped unexpectedly${NC}"
            break
        fi
        
        if [[ "$LAUNCH_GUI" == true ]] && ! kill -0 $GUI_PID 2>/dev/null; then
            echo -e "${RED}❌ GUI stopped unexpectedly${NC}"
            break
        fi
    done
fi

echo -e "${GREEN}Voice Assistant stopped.${NC}"
