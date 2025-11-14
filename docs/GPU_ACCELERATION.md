# GPU Acceleration and Hot-Reload Configuration

## New Features

### GPU Acceleration Control

You can now enable or disable GPU acceleration for whisper.cpp inference directly from the GNOME extension preferences. This allows you to:

- Toggle GPU acceleration on/off without editing config files
- Test performance differences between CPU and GPU inference
- Optimize for your hardware configuration

**Location**: Extension Preferences → General → GPU Acceleration

**Default**: Disabled (false)

### Configuration Hot-Reload

The service now automatically reloads configuration changes without requiring a restart. When you change settings in the GNOME extension and click "Sync to Service", the changes take effect immediately.

**Automatically reloaded settings:**
- GPU acceleration (triggers whisper model reload)
- Whisper model selection (triggers whisper model reload)
- Command threshold
- Processing interval
- Hotword
- All other configuration values

## How It Works

### Architecture

1. **Extension Preferences** → Updates GSettings and config.json
2. **ConfigManager** → Calls D-Bus `UpdateConfig()` method
3. **Voice Assistant Service** → Receives update via D-Bus
4. **Service** → Reloads whisper model if GPU/model changed
5. **Service** → Emits `ConfigChanged` signal

### GPU Acceleration

The `gpu_acceleration` setting controls the `use_gpu` parameter in whisper.cpp's context initialization:

```cpp
whisper_context_params cparams = whisper_context_default_params();
cparams.use_gpu = m_gpuAcceleration;  // From config
cparams.gpu_device = 0;  // First GPU device
```

When GPU acceleration changes:
1. Service shuts down current whisper context
2. Reinitializes whisper with new GPU setting
3. Continues processing without service restart

## Usage

### Via GNOME Extension Preferences

1. Open extension preferences:
   ```bash
   gnome-extensions prefs gnome-assistant@saim
   ```

2. Go to **General** tab

3. Toggle **GPU Acceleration** switch

4. Click **Sync to Service** to apply changes

5. Changes take effect immediately (check logs to confirm)

### Via D-Bus

Enable GPU acceleration:
```bash
gdbus call --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant \
  --method com.github.saim.GnomeAssistant.SetConfigValue \
  "gpu_acceleration" "<true>"
```

Disable GPU acceleration:
```bash
gdbus call --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant \
  --method com.github.saim.GnomeAssistant.SetConfigValue \
  "gpu_acceleration" "<false>"
```

### Via Config File

Edit `~/.config/gnome-assistant/config.json`:
```json
{
  "gpu_acceleration": true,
  ...
}
```

Then sync to service:
```bash
# Either restart service
systemctl --user restart gnome-assistant.service

# Or trigger reload via D-Bus
CONFIG=$(cat ~/.config/gnome-assistant/config.json)
gdbus call --session \
  --dest com.github.saim.GnomeAssistant \
  --object-path /com/github/saim/GnomeAssistant \
  --method com.github.saim.GnomeAssistant.UpdateConfig \
  "$CONFIG"
```

## Monitoring Changes

### Check Service Logs

Watch for reload messages:
```bash
journalctl --user -u gnome-assistant.service -f | grep -i "gpu\|reload"
```

Expected output when changing GPU setting:
```
INFO: GPU acceleration configured: enabled
INFO: GPU acceleration or model changed, reloading whisper...
INFO: Attempting to initialize Whisper with GPU acceleration: enabled
INFO: Whisper model loaded successfully (GPU acceleration: enabled)
```

### D-Bus Signal Monitoring

Listen for ConfigChanged signals:
```bash
dbus-monitor --session "interface='com.github.saim.GnomeAssistant',member='ConfigChanged'"
```

## Testing

A test script is provided: `test-gpu-config.sh`

```bash
./test-gpu-config.sh
```

This script:
1. Verifies service is running
2. Gets current configuration
3. Toggles GPU acceleration via D-Bus
4. Checks logs for reload messages
5. Verifies config file was updated

## Requirements

### GPU Acceleration

For GPU acceleration to work, whisper.cpp must be compiled with GPU support:

**CUDA (NVIDIA):**
```bash
cmake -B build -DGGML_CUDA=ON
cmake --build build
```

**Vulkan (AMD/Intel/NVIDIA):**
```bash
cmake -B build -DGGML_VULKAN=ON
cmake --build build
```

**Metal (macOS):**
```bash
cmake -B build -DGGML_METAL=ON
cmake --build build
```

If whisper.cpp was compiled without GPU support, enabling the setting will have no effect (it will fall back to CPU).

## Configuration File Format

The `config.json` includes:
```json
{
  "_comment_gpu": "Enable GPU acceleration for whisper.cpp inference (requires GPU support)",
  "gpu_acceleration": false,
  ...
}
```

Comments (fields starting with `_`) are preserved when the extension updates the config.

## Troubleshooting

### GPU acceleration not working

1. Check if whisper.cpp was compiled with GPU support:
   ```bash
   ldd ~/.local/bin/gnome-assistant-service | grep -i "cuda\|vulkan"
   ```

2. Check service logs for GPU initialization:
   ```bash
   journalctl --user -u gnome-assistant.service | grep -i gpu
   ```

3. Verify your GPU drivers are installed and working

### Config changes not taking effect

1. Ensure D-Bus service is running:
   ```bash
   systemctl --user status gnome-assistant.service
   ```

2. Check for D-Bus errors:
   ```bash
   journalctl --user -u gnome-assistant.service | grep -i error
   ```

3. Manually restart the service:
   ```bash
   systemctl --user restart gnome-assistant.service
   ```

### Extension preferences not syncing

1. Check that config file exists and is writable:
   ```bash
   ls -la ~/.config/gnome-assistant/config.json
   ```

2. Check extension logs:
   ```bash
   journalctl -f -o cat /usr/bin/gnome-shell | grep ConfigManager
   ```

3. Verify D-Bus connection in preferences:
   - The preferences should show no errors when clicking "Sync to Service"
   - If errors occur, the D-Bus service may not be reachable

## Performance Impact

**GPU Acceleration Enabled:**
- Faster inference on compatible GPUs
- Higher GPU memory usage
- Better for real-time processing

**GPU Acceleration Disabled:**
- CPU-only inference
- Lower power consumption
- Better for laptops on battery
- Still quite fast on modern CPUs with the tiny model

The tiny.en model is fast enough on modern CPUs that GPU acceleration may not be necessary unless you're using larger models (base, small, medium, large).
