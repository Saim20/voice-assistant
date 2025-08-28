#!/usr/bin/env python3
"""
Simplified Voice Buffer Writer for Nerd Dictation
Only writes text to buffer file - all processing handled by GNOME extension
"""

from pathlib import Path

def write_to_buffer(text: str) -> str:
    """Write text to buffer file for GNOME extension processing"""
    try:
        buffer_file = Path("/tmp/nerd-dictation.buffer")
        with open(buffer_file, 'w') as f:
            f.write(text)
    except Exception:
        # Silent fail to avoid nerd-dictation issues
        pass
    
    # Return empty string so nerd-dictation doesn't type anything
    return ""

def nerd_dictation_process(text: str) -> str:
    """Main entry point for nerd-dictation integration"""
    return write_to_buffer(text)
