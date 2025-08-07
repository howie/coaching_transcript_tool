"""
Centralized version management for Coaching Assistant
"""
import json
import os
from pathlib import Path

# Try to load from the root version.json file
def get_version_info():
    """Get version information from the centralized version.json file"""
    try:
        # Look for version.json in various possible locations
        possible_paths = [
            Path(__file__).parent.parent.parent.parent.parent / "version.json",  # From core-logic
            Path("/Users/howie/Workspace/github/coaching_transcript_tool/version.json"),  # Absolute path fallback
            Path("version.json"),  # Current directory
        ]
        
        for version_path in possible_paths:
            if version_path.exists():
                with open(version_path, 'r') as f:
                    return json.load(f)
        
        # Fallback if no version.json found
        return {
            "version": "2.3.1",
            "displayVersion": "v2.3.1",
            "description": "Coaching Transcript Tool"
        }
    except Exception:
        # Fallback for any errors
        return {
            "version": "2.3.1", 
            "displayVersion": "v2.3.1",
            "description": "Coaching Transcript Tool"
        }

# Export version info
VERSION_INFO = get_version_info()
VERSION = VERSION_INFO["version"]
DISPLAY_VERSION = VERSION_INFO["displayVersion"]
DESCRIPTION = VERSION_INFO["description"]

__version__ = VERSION