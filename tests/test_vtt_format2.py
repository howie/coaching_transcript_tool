#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="importlib._bootstrap")

import os
import tempfile
import pytest
from src.vtt import parse_vtt, consolidate_speakers, replace_names

# Sample VTT content for testing format 2 (Speaker: Text)
SAMPLE_2_VTT = """WEBVTT

00:00:01.000 --> 00:00:05.000
John Doe: Hello, this is a test.

00:00:06.000 --> 00:00:10.000
John Doe: I am continuing my speech.

00:00:11.000 --> 00:00:15.000
Jane Smith: Nice to meet you.

00:00:16.000 --> 00:00:20.000
John Doe: Nice to meet you too.
"""

@pytest.fixture
def vtt_file_format2():
    """Create a temporary VTT file for testing format 2."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.vtt') as f:
        f.write(SAMPLE_2_VTT)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup after test
    os.unlink(temp_path)

def test_parse_vtt_format2(vtt_file_format2):
    """Test parsing a VTT file with format 2 (Speaker: Text)."""
    parsed_data = parse_vtt(vtt_file_format2)
    
    assert len(parsed_data) == 4
    assert parsed_data[0]['time'] == '00:00:01.000'
    assert parsed_data[0]['speaker'] == 'John Doe'
    assert parsed_data[0]['content'] == 'Hello, this is a test.'
    assert parsed_data[2]['speaker'] == 'Jane Smith'
    assert parsed_data[2]['content'] == 'Nice to meet you.'

def test_consolidate_format2(vtt_file_format2):
    """Test consolidating consecutive speeches from the same speaker in format 2."""
    parsed_data = parse_vtt(vtt_file_format2)
    consolidated = consolidate_speakers(parsed_data)
    
    # Should have 3 entries after consolidation (John, Jane, John)
    assert len(consolidated) == 3
    assert consolidated[0]['speaker'] == 'John Doe'
    assert 'I am continuing my speech' in consolidated[0]['content']
    assert consolidated[1]['speaker'] == 'Jane Smith'

def test_replace_names_format2(vtt_file_format2):
    """Test replacing speaker names with roles in format 2."""
    parsed_data = parse_vtt(vtt_file_format2)
    replaced = replace_names(parsed_data, 'John Doe', 'Jane Smith')
    
    speakers = [item['speaker'] for item in replaced]
    assert 'Coach' in speakers
    assert 'Client' in speakers
