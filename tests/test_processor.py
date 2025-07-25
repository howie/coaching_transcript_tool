import io
from pathlib import Path

import pytest
from coaching_assistant.core.processor import format_transcript

@pytest.fixture
def sample_vtt_content():
    """Provides the content of the sample VTT file."""
    vtt_path = Path(__file__).parent / 'data' / 'sample_1.vtt'
    with open(vtt_path, 'r', encoding='utf-8') as f:
        return f.read()

def test_format_transcript_markdown(sample_vtt_content):
    """Tests formatting the transcript to Markdown."""
    result = format_transcript(
        file_content=sample_vtt_content,
        output_format='markdown',
        coach_name='John Doe',
        client_name='Jane Smith',
    )
    assert isinstance(result, str)
    assert "**Coach**" in result
    assert "Client" in result
    assert "Hello, this is a test coaching session." in result

def test_format_transcript_excel(sample_vtt_content):
    """Tests formatting the transcript to Excel."""
    result = format_transcript(
        file_content=sample_vtt_content,
        output_format='excel',
        coach_name='Interviewer',
        client_name='Candidate',
    )
    assert isinstance(result, io.BytesIO)
    # Check if the BytesIO object is not empty and looks like an Excel file (starts with PK zip header)
    excel_content = result.getvalue()
    assert len(excel_content) > 0
    assert excel_content.startswith(b'PK\x03\x04')

def test_format_transcript_invalid_format(sample_vtt_content):
    """Tests that an invalid format raises a ValueError."""
    with pytest.raises(ValueError, match='Unsupported output format: invalid_format'):
        format_transcript(
            file_content=sample_vtt_content,
            output_format='invalid_format',
        )
