#!/usr/bin/env python3
import os
import tempfile
import pytest
import pandas as pd
from src.vtt import (
    parse_vtt,
    consolidate_speakers,
    replace_names,
    generate_markdown,
    generate_excel
)

# Sample VTT content for testing
SAMPLE_1_VTT = """WEBVTT

00:00:01.000 --> 00:00:05.000
<v John Doe>Hello, this is a test.</v>

00:00:06.000 --> 00:00:10.000
<v John Doe>I am continuing my speech.</v>

00:00:11.000 --> 00:00:15.000
<v Jane Smith>Nice to meet you.</v>

00:00:16.000 --> 00:00:20.000
<v John Doe>Nice to meet you too.</v>
"""

@pytest.fixture
def vtt_file():
    """Create a temporary VTT file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.vtt') as f:
        f.write(SAMPLE_1_VTT)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup after test
    os.unlink(temp_path)

def test_parse_vtt(vtt_file):
    """Test parsing a VTT file."""
    parsed_data = parse_vtt(vtt_file)
    
    assert len(parsed_data) == 4
    assert parsed_data[0]['time'] == '00:00:01.000'
    assert parsed_data[0]['speaker'] == 'John Doe'
    assert parsed_data[0]['content'] == 'Hello, this is a test.'
    
    assert parsed_data[2]['time'] == '00:00:11.000'
    assert parsed_data[2]['speaker'] == 'Jane Smith'
    assert parsed_data[2]['content'] == 'Nice to meet you.'

def test_consolidate_speakers():
    """Test consolidating consecutive speeches from the same speaker."""
    data = [
        {'time': '00:00:01.000', 'speaker': 'John Doe', 'content': 'Hello, this is a test.'},
        {'time': '00:00:06.000', 'speaker': 'John Doe', 'content': 'I am continuing my speech.'},
        {'time': '00:00:11.000', 'speaker': 'Jane Smith', 'content': 'Nice to meet you.'},
        {'time': '00:00:16.000', 'speaker': 'John Doe', 'content': 'Nice to meet you too.'}
    ]
    
    consolidated = consolidate_speakers(data)
    
    assert len(consolidated) == 3
    assert consolidated[0]['speaker'] == 'John Doe'
    assert consolidated[0]['content'] == 'Hello, this is a test. I am continuing my speech.'
    assert consolidated[1]['speaker'] == 'Jane Smith'
    assert consolidated[2]['speaker'] == 'John Doe'
    assert consolidated[2]['content'] == 'Nice to meet you too.'

def test_replace_names():
    """Test replacing speaker names with roles."""
    data = [
        {'time': '00:00:01.000', 'speaker': 'John Doe', 'content': 'Hello'},
        {'time': '00:00:11.000', 'speaker': 'Jane Smith', 'content': 'Hi'}
    ]
    
    replaced = replace_names(data, 'John Doe', 'Jane Smith')
    
    assert replaced[0]['speaker'] == 'Coach'
    assert replaced[1]['speaker'] == 'Client'

def test_generate_markdown():
    """Test generating markdown from parsed data."""
    data = [
        {'time': '00:00:01.000', 'speaker': 'Coach', 'content': 'Hello'},
        {'time': '00:00:11.000', 'speaker': 'Client', 'content': 'Hi'}
    ]
    
    markdown = generate_markdown(data, content_width=80)
    
    # The actual output will have more formatting and line wrapping
    assert "| Time | Role |" in markdown
    assert "| 00:00:01.000 | **Coach** | Hello |" in markdown
    assert "| 00:00:11.000 | Client | Hi |" in markdown

def test_generate_excel():
    """Test generating Excel from parsed data."""
    data = [
        {'time': '00:00:01.000', 'speaker': 'Coach', 'content': 'Hello'},
        {'time': '00:00:11.000', 'speaker': 'Client', 'content': 'Hi'}
    ]
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        temp_path = f.name
    
    try:
        generate_excel(data, temp_path)
        
        # Verify the Excel file was created and contains the expected data
        df = pd.read_excel(temp_path)
        assert len(df) == 2
        assert df.iloc[0]['speaker'] == 'Coach'
        assert df.iloc[1]['content'] == 'Hi'
    finally:
        # Cleanup
        os.unlink(temp_path)
