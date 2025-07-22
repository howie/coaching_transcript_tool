#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="importlib._bootstrap")

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
from src.parser import VTTFormat

# Sample VTT content for testing MS Teams format
SAMPLE_MS_TEAMS_VTT = """WEBVTT

00:00:01.000 --> 00:00:05.000
<v John Doe>Hello, this is a test.</v>

00:00:06.000 --> 00:00:10.000
<v John Doe>I am continuing my speech.</v>

00:00:11.000 --> 00:00:15.000
<v Jane Smith>Nice to meet you.</v>

00:00:16.000 --> 00:00:20.000
<v John Doe>Nice to meet you too.</v>
"""

# Sample VTT content for testing MacWhisper format
SAMPLE_MAC_WHISPER_VTT = """WEBVTT

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
def ms_teams_vtt_file():
    """Create a temporary MS Teams format VTT file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.vtt') as f:
        f.write(SAMPLE_MS_TEAMS_VTT)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def mac_whisper_vtt_file():
    """Create a temporary MacWhisper format VTT file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.vtt') as f:
        f.write(SAMPLE_MAC_WHISPER_VTT)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)

@pytest.mark.parametrize('fixture_name,format_type', [
    ('ms_teams_vtt_file', VTTFormat.MS_TEAMS),
    ('mac_whisper_vtt_file', VTTFormat.MAC_WHISPER)
])
def test_parse_vtt(request, fixture_name, format_type):
    """Test parsing a VTT file."""
    vtt_file = request.getfixturevalue(fixture_name)
    parsed_data = parse_vtt(vtt_file, format_type)
    
    assert len(parsed_data) == 4
    assert parsed_data[0]['time'] == '00:00:01.000'
    assert parsed_data[0]['speaker'] == 'John Doe'
    assert parsed_data[0]['content'] == 'Hello, this is a test.'
    assert parsed_data[2]['speaker'] == 'Jane Smith'
    assert parsed_data[2]['content'] == 'Nice to meet you.'

@pytest.mark.parametrize('fixture_name,format_type', [
    ('ms_teams_vtt_file', VTTFormat.MS_TEAMS),
    ('mac_whisper_vtt_file', VTTFormat.MAC_WHISPER)
])
def test_consolidate_speakers(request, fixture_name, format_type):
    """Test consolidating consecutive speeches from the same speaker."""
    vtt_file = request.getfixturevalue(fixture_name)
    parsed_data = parse_vtt(vtt_file, format_type)
    consolidated = consolidate_speakers(parsed_data)
    
    # Should have 3 entries after consolidation (John, Jane, John)
    assert len(consolidated) == 3
    assert consolidated[0]['speaker'] == 'John Doe'
    assert 'I am continuing my speech' in consolidated[0]['content']
    assert consolidated[1]['speaker'] == 'Jane Smith'

@pytest.mark.parametrize('fixture_name,format_type', [
    ('ms_teams_vtt_file', VTTFormat.MS_TEAMS),
    ('mac_whisper_vtt_file', VTTFormat.MAC_WHISPER)
])
def test_replace_names(request, fixture_name, format_type):
    """Test replacing speaker names with roles."""
    vtt_file = request.getfixturevalue(fixture_name)
    parsed_data = parse_vtt(vtt_file, format_type)
    replaced = replace_names(parsed_data, 'John Doe', 'Jane Smith')
    
    speakers = [item['speaker'] for item in replaced]
    assert 'Coach' in speakers
    assert 'Client' in speakers

@pytest.mark.parametrize('fixture_name,format_type', [
    ('ms_teams_vtt_file', VTTFormat.MS_TEAMS),
    ('mac_whisper_vtt_file', VTTFormat.MAC_WHISPER)
])
def test_generate_markdown(request, fixture_name, format_type):
    """Test generating markdown from parsed data."""
    vtt_file = request.getfixturevalue(fixture_name)
    parsed_data = parse_vtt(vtt_file, format_type)
    markdown = generate_markdown(parsed_data)
    
    assert '| Time | Role | Content |' in markdown
    assert 'Hello, this is a test.' in markdown
    assert 'Nice to meet you.' in markdown

@pytest.mark.parametrize('fixture_name,format_type', [
    ('ms_teams_vtt_file', VTTFormat.MS_TEAMS),
    ('mac_whisper_vtt_file', VTTFormat.MAC_WHISPER)
])
def test_generate_excel(request, fixture_name, format_type, tmp_path):
    """Test generating Excel from parsed data."""
    vtt_file = request.getfixturevalue(fixture_name)
    output_file = tmp_path / 'test_output.xlsx'
    parsed_data = parse_vtt(vtt_file, format_type)
    
    generate_excel(parsed_data, str(output_file))
    
    # Check if file was created
    assert output_file.exists()
    
    # Check if the Excel file contains the expected data
    df = pd.read_excel(output_file)
    assert len(df) == 4
    # Check that both speakers are present in the Role column
    roles = df['Role'].values
    assert 'John Doe' in roles or 'Coach' in roles
    assert 'Jane Smith' in roles or 'Client' in roles
