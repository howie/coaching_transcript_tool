#!/usr/bin/env python3
import os
import sys
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Define common fixtures here if needed
@pytest.fixture
def data_dir():
    """Return the path to the test data directory."""
    return os.path.join(os.path.dirname(__file__), 'data')

@pytest.fixture
def sample_vtt_path(data_dir):
    """Return the path to the sample VTT file."""
    return os.path.join(data_dir, 'sample_1.vtt', 'sample_2.vtt')
