# Smart Workflows Implementation Summary

## Overview

I've successfully implemented smart workflows for the Willow voice assistant that make it more intelligent and context-aware. The assistant can now dynamically handle voice commands without requiring pre-configured entries.

## What Was Implemented

### 1. Context Configuration System (`context.json`)

Created `/home/saim/.config/willow/context.json` with:

- **Default Apps**: Browser, terminal, file manager, text editor, etc.
- **Search Engines**: YouTube, Google, Facebook, Reddit, Wikipedia, GitHub
- **App Aliases**: Map common app names to their system commands (e.g., "vscode" → ["code", "code-oss", "vscodium"])

This allows the assistant to understand user preferences and find apps intelligently.

### 2. Smart "Open/Launch" Workflow

**How it works:**
- User says: "**open spotify**" or "**launch firefox**" or "**start discord**"
- The assistant:
  1. Detects the "open/launch/start" trigger
  2. Extracts the app name from the command
  3. Checks if the app exists on the system using `which` command
  4. Looks up app aliases if the exact name isn't found
  5. Executes the app if available

**Example commands:**
- "open spotify" → Launches Spotify if installed
- "launch vscode" → Finds and launches VS Code (code/code-oss/vscodium)
- "start browser" → Opens default browser (firefox)

### 3. Smart "Search X for Y" Workflow

**How it works:**
- User says: "**search youtube for tutorials**" or "**search google for recipes**"
- The assistant:
  1. Detects the "search [engine] for [query]" pattern
  2. Extracts the search engine and query
  3. URL-encodes the query properly
  4. Opens the search in the default browser

**Example commands:**
- "search youtube for cooking videos" → Opens YouTube search
- "search google for weather forecast" → Opens Google search
- "search github for python projects" → Opens GitHub search

## Technical Implementation

### Files Modified

1. **`service/src/CommandExecutor.hpp`**
   - Added `ContextConfig` structure
   - Added smart workflow methods: `executeSmartOpen()`, `executeSmartSearch()`
   - Added helper methods: `loadContextConfig()`, `findApp()`, `urlEncode()`, `isCommandAvailable()`

2. **`service/src/CommandExecutor.cpp`**
   - Implemented context loading from JSON
   - Implemented smart open logic with app discovery
   - Implemented smart search with URL encoding
   - Auto-loads context config on initialization

3. **`service/src/ModeWorkers.hpp`**
   - Added smart workflow processing methods to `CommandModeWorker`
   - Added helper methods: `processSmartOpen()`, `processSmartSearch()`, `extractAppName()`, `extractSearchQuery()`

4. **`service/src/ModeWorkers.cpp`**
   - Integrated smart workflows into command processing pipeline
   - Smart workflows are checked BEFORE static command matching
   - Includes duplicate detection for smart commands

### Files Created

1. **`context.json`** (project root)
   - Template context configuration
   - Copied to `~/.config/willow/context.json`

2. **Updated `README.md`**
   - Added Smart Workflows section
   - Added Context Configuration documentation
   - Added usage examples

## How It Works

### Processing Flow

```
User speaks → Whisper transcribes → CommandModeWorker processes:
    ↓
    1. Check for smart "open/launch" commands
       - Extract app name
       - Find app on system
       - Execute if found
    ↓
    2. Check for smart "search X for Y" commands
       - Extract engine and query
       - Build search URL
       - Open in browser
    ↓
    3. Fall back to static command matching
       - Match against config.json commands
       - Execute if confidence threshold met
```

### Key Features

- **Automatic App Discovery**: Uses `which` command to verify apps exist
- **Alias Resolution**: Checks multiple command variants (e.g., code, code-oss, vscodium for VS Code)
- **URL Encoding**: Properly encodes search queries for web URLs
- **Duplicate Prevention**: Prevents repeated execution of the same command
- **Fallback Handling**: If smart workflows don't match, falls back to configured commands

## Usage Examples

### Opening Applications

```
User: "hey"
Assistant: [Switches to command mode]
User: "open spotify"
Assistant: [Finds and launches Spotify]

User: "launch file manager"
Assistant: [Launches nautilus]
```

### Web Searches

```
User: "hey"
Assistant: [Switches to command mode]
User: "search youtube for python tutorials"
Assistant: [Opens Firefox with YouTube search results]

User: "search github for rust projects"
Assistant: [Opens Firefox with GitHub search results]
```

## Configuration

Users can customize their experience by editing `~/.config/willow/context.json`:

```json
{
  "default_apps": {
    "browser": "brave-browser",  // Change default browser
    "terminal": "alacritty"       // Change default terminal
  },
  "search_engines": {
    "ddg": "https://duckduckgo.com/?q="  // Add DuckDuckGo
  },
  "app_aliases": {
    "editor": ["nvim", "vim", "nano"]  // Add text editor aliases
  }
}
```

## Benefits

1. **More Natural**: Users can speak naturally without memorizing exact phrases
2. **Dynamic**: Works with any installed app, not just pre-configured ones
3. **Extensible**: Easy to add new search engines or app aliases
4. **Intelligent**: Checks if apps exist before attempting to launch
5. **Privacy-Preserving**: All processing happens locally

## Build Status

✅ Successfully compiled with CUDA support
✅ All smart workflow features integrated
✅ No breaking changes to existing functionality
✅ Backward compatible with existing config.json commands

## Next Steps (Optional Enhancements)

1. Add fuzzy matching for app names (e.g., "spotfy" → "spotify")
2. Support "open X in Y" commands (e.g., "open reddit in private window")
3. Add more search engines by default
4. Create a GUI preference panel for context.json editing
5. Add voice feedback for when apps aren't found
