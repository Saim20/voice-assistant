# Quick Start Guide - Smart Workflows

## Installation

After building and installing Willow, copy the context configuration:

```bash
mkdir -p ~/.config/willow
cp /path/to/willow/context.json ~/.config/willow/context.json
```

Then rebuild and install the service:

```bash
cd service/build
cmake .. && make -j$(nproc)
sudo make install
systemctl --user restart willow.service
```

## Usage Examples

### Opening Applications

Just say "**open**" or "**launch**" followed by the app name:

| Say this | What happens |
|----------|--------------|
| "open spotify" | Launches Spotify if installed |
| "launch firefox" | Opens Firefox browser |
| "start terminal" | Opens your default terminal (kgx) |
| "open files" | Opens file manager (nautilus) |
| "launch discord" | Opens Discord |
| "open vscode" | Opens VS Code (tries code, code-oss, vscodium) |

### Web Searches

Say "**search [engine] for [your query]**":

| Say this | What happens |
|----------|--------------|
| "search youtube for cooking recipes" | Opens YouTube with search results |
| "search google for weather today" | Opens Google search |
| "search github for python projects" | Opens GitHub search |
| "search reddit for gaming news" | Opens Reddit search |
| "search wikipedia for albert einstein" | Opens Wikipedia search |

### Supported Search Engines

- `youtube` - YouTube video search
- `google` - Google web search
- `facebook` - Facebook search
- `reddit` - Reddit search
- `wikipedia` - Wikipedia articles
- `github` - GitHub repository search

## Customization

Edit `~/.config/willow/context.json` to customize your setup:

### Change Default Browser

```json
{
  "default_apps": {
    "browser": "brave-browser"  // or "chromium", "google-chrome", etc.
  }
}
```

### Add Custom Search Engines

```json
{
  "search_engines": {
    "ddg": "https://duckduckgo.com/?q=",
    "amazon": "https://www.amazon.com/s?k="
  }
}
```

Then use: "search ddg for privacy tools" or "search amazon for laptop"

### Add App Aliases

If an app has multiple command names:

```json
{
  "app_aliases": {
    "music": ["rhythmbox", "spotify", "vlc"],
    "editor": ["code", "gedit", "vim"]
  }
}
```

Then: "open music" will try rhythmbox, then spotify, then vlc.

## Tips

1. **Natural Language**: Speak naturally - "open spotify" works just as well as "launch spotify"
2. **Case Insensitive**: App names are case-insensitive ("Open Spotify" = "open spotify")
3. **App Discovery**: The assistant checks if apps exist before trying to launch them
4. **No Pre-configuration**: Unlike static commands, smart workflows work dynamically

## Troubleshooting

**App doesn't open?**
- Check if it's installed: `which spotify`
- Add it to app_aliases in context.json
- Check logs: `journalctl --user -u willow.service -f`

**Search doesn't work?**
- Verify default browser is set correctly in context.json
- Check if browser is installed: `which firefox`
- Ensure ydotool service is running: `systemctl --user status ydotool`

**Context not loading?**
- Verify file exists: `cat ~/.config/willow/context.json`
- Check JSON syntax: `jq . ~/.config/willow/context.json`
- Restart service: `systemctl --user restart willow.service`

## Complete Workflow Example

```
1. Activate: "hey"
   → Assistant enters command mode (red pulsing icon)

2. Open app: "open spotify"
   → Spotify launches

3. Search: "search youtube for jazz music"
   → Firefox opens with YouTube search results

4. Return: "normal mode"
   → Assistant returns to normal mode (microphone icon)
```

## Integration with Static Commands

Smart workflows are checked FIRST, then fall back to static commands from `config.json`:

1. User speaks
2. Check for "open/launch" pattern → Execute if matched
3. Check for "search X for Y" pattern → Execute if matched  
4. Check static commands from config.json → Execute if confidence met
5. No match → Log and ignore

This means you can still use all your existing commands while benefiting from smart workflows!
