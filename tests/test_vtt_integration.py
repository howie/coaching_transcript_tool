#!/usr/bin/env python3
import os
import tempfile
import subprocess
import pytest
import pandas as pd

# Sample VTT content for integration testing
SAMPLE_VTT = """WEBVTT

00:00:01.000 --> 00:00:05.000
<v Coach Name>How are you feeling today?</v>

00:00:06.000 --> 00:00:10.000
<v Client Name>I'm feeling pretty good, thanks for asking.</v>

00:00:11.000 --> 00:00:15.000
<v Coach Name>That's great to hear. What would you like to focus on today?</v>

00:00:16.000 --> 00:00:20.000
<v Client Name>I'd like to discuss my career goals.</v>
"""

@pytest.fixture
def sample_vtt_file():
    """Create a temporary VTT file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.vtt') as f:
        f.write(SAMPLE_VTT)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup after test
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_markdown_output_cli(sample_vtt_file):
    """Test the CLI with markdown output."""
    with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
        output_path = f.name
    
    try:
        # Run the command with subprocess
        cmd = [
            "python", 
            "-m", "src.vtt", 
            sample_vtt_file, 
            output_path,
            "-Coach", "Coach Name",
            "-Client", "Client Name"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True
        )
        
        # Check command executed successfully
        assert result.returncode == 0, f"Command failed with error: {result.stderr}"
        
        # Check output file exists
        assert os.path.exists(output_path)
        
        # Read and verify content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        assert "| Time | Role | Content |" in content
        assert "| 00:00:01.000 | Coach | How are you feeling today? |" in content
        assert "| 00:00:06.000 | Client | I'm feeling pretty good, thanks for asking. |" in content
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_excel_output_cli(sample_vtt_file):
    """Test the CLI with Excel output."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        output_path = f.name
    
    try:
        # Run the command with subprocess
        cmd = [
            "python", 
            "-m", "src.vtt", 
            sample_vtt_file, 
            output_path,
            "-Coach", "Coach Name",
            "-Client", "Client Name"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True
        )
        
        # Check command executed successfully
        assert result.returncode == 0, f"Command failed with error: {result.stderr}"
        
        # Check output file exists
        assert os.path.exists(output_path)
        
        # Read and verify content
        df = pd.read_excel(output_path)
        
        assert len(df) == 4
        assert df.iloc[0]['speaker'] == 'Coach'
        assert 'feeling today' in df.iloc[0]['content']
        assert df.iloc[1]['speaker'] == 'Client'
        assert 'career goals' in df.iloc[3]['content']
    finally:
        # Cleanup
        if os.path.exists(output_path):
            os.unlink(output_path)
