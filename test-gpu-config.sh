#!/bin/bash
# Test script for GPU acceleration configuration and hot-reload

echo "=== Testing GPU Acceleration Configuration ==="
echo ""

# Check if service is running
echo "1. Checking if service is running..."
if systemctl --user is-active --quiet gnome-assistant.service; then
    echo "   ✓ Service is running"
else
    echo "   ✗ Service is not running"
    echo "   Starting service..."
    systemctl --user start gnome-assistant.service
    sleep 2
fi
echo ""

# Get current configuration
echo "2. Getting current configuration..."
gdbus call --session \
    --dest com.github.saim.GnomeAssistant \
    --object-path /com/github/saim/GnomeAssistant \
    --method com.github.saim.GnomeAssistant.GetConfig | head -c 200
echo "..."
echo ""

# Read config file
echo "3. Current config.json GPU setting:"
grep -A 1 "gpu_acceleration" ~/.config/gnome-assistant/config.json || echo "   GPU setting not found in config"
echo ""

# Test: Enable GPU acceleration via D-Bus
echo "4. Testing: Enable GPU acceleration via D-Bus..."
CONFIG_JSON=$(cat ~/.config/gnome-assistant/config.json)
# Use jq to update if available, otherwise manual
if command -v jq &> /dev/null; then
    UPDATED_CONFIG=$(echo "$CONFIG_JSON" | jq '.gpu_acceleration = true')
    gdbus call --session \
        --dest com.github.saim.GnomeAssistant \
        --object-path /com/github/saim/GnomeAssistant \
        --method com.github.saim.GnomeAssistant.UpdateConfig \
        "$UPDATED_CONFIG"
    echo "   ✓ GPU acceleration enabled via D-Bus"
else
    echo "   ⚠ jq not installed, skipping automatic update"
    echo "   You can manually test by editing ~/.config/gnome-assistant/config.json"
fi
echo ""

# Check service logs for reload message
echo "5. Checking service logs for whisper reload..."
journalctl --user -u gnome-assistant.service --since "10 seconds ago" | grep -i "gpu\|reload\|whisper" | tail -5
echo ""

# Verify config was updated
echo "6. Verifying config file was updated:"
grep -A 1 "gpu_acceleration" ~/.config/gnome-assistant/config.json
echo ""

echo "=== Test Configuration Update via SetConfigValue ==="
echo "7. Testing SetConfigValue for GPU acceleration..."
gdbus call --session \
    --dest com.github.saim.GnomeAssistant \
    --object-path /com/github/saim/GnomeAssistant \
    --method com.github.saim.GnomeAssistant.SetConfigValue \
    "gpu_acceleration" "<false>"
echo "   ✓ GPU acceleration set to false via SetConfigValue"
echo ""

echo "8. Checking logs again for reload..."
journalctl --user -u gnome-assistant.service --since "5 seconds ago" | grep -i "gpu\|reload\|whisper" | tail -5
echo ""

echo "=== Test Complete ==="
echo ""
echo "To manually test the GNOME extension preferences:"
echo "  1. Run: gnome-extensions prefs gnome-assistant@saim"
echo "  2. Toggle the 'GPU Acceleration' switch"
echo "  3. Click 'Sync to Service'"
echo "  4. Check logs: journalctl --user -u gnome-assistant.service -f"
echo ""
