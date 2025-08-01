#!/usr/bin/env python3
"""
Coaching Transcript CLI Tool Entry Point

This is the main entry point for the CLI application that uses the shared
core logic from packages/core-logic.
"""

import sys
import os

# Add the core-logic package to the Python path
sys.path.insert(0, '/app/packages/core-logic/src')

from coaching_assistant.cli import app

if __name__ == "__main__":
    app()
