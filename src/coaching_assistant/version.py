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
            Path(__file__).parent.parent.parent.parent.parent.parent
            / "version.json",  # From src/coaching_assistant
            Path(__file__).parent.parent.parent.parent
            / "version.json",  # From packages/core-logic
            Path.cwd().parent.parent / "version.json",  # Relative from core-logic
            Path("/app/version.json"),  # Docker container path
            Path("version.json"),  # Current directory
        ]

        # Debug logging
        debug = os.environ.get("DEBUG_VERSION") == "true"
        if debug:
            print(f"[VERSION] Looking for version.json from {__file__}")

        for version_path in possible_paths:
            try:
                if version_path.exists():
                    if debug:
                        print(f"[VERSION] Found at: {version_path}")
                    with open(version_path, "r") as f:
                        data = json.load(f)
                        if debug:
                            print(f"[VERSION] Loaded: {data}")
                        return data
            except Exception as e:
                if debug:
                    print(f"[VERSION] Error checking {version_path}: {e}")
                continue

        # Fallback if no version.json found
        return {
            "version": "2.20.0",
            "displayVersion": "v2.20.0",
            "description": "Coaching Transcript Tool",
        }
    except Exception:
        # Fallback for any errors
        return {
            "version": "2.20.0",
            "displayVersion": "v2.20.0",
            "description": "Coaching Transcript Tool",
        }


# Export version info
VERSION_INFO = get_version_info()
VERSION = VERSION_INFO["version"]
DISPLAY_VERSION = VERSION_INFO["displayVersion"]
DESCRIPTION = VERSION_INFO["description"]

__version__ = VERSION
