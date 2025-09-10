from pathlib import Path

import pytest
from coaching_assistant.core.processor import format_transcript


@pytest.fixture
def sample_vtt_content():
    """Provides the content of the sample VTT file."""
    vtt_path = Path(__file__).parent / "data" / "sample_1.vtt"
    with open(vtt_path, "r", encoding="utf-8") as f:
        return f.read()


def test_format_transcript_markdown(sample_vtt_content):
    """Tests formatting the transcript to Markdown."""
    result = format_transcript(
        file_content=sample_vtt_content.encode("utf-8"),
        original_filename="sample.vtt",
        output_format="markdown",
        coach_name="John Doe",
        client_name="Jane Smith",
    )
    assert isinstance(result, str)
    assert "**Coach**" in result
    assert "Client" in result
    assert "Hello, this is a test coaching session." in result


def test_format_transcript_excel(sample_vtt_content):
    """Tests formatting the transcript to Excel."""
    result = format_transcript(
        file_content=sample_vtt_content.encode("utf-8"),
        original_filename="sample.vtt",
        output_format="excel",
        coach_name="Interviewer",
        client_name="Candidate",
    )
    assert isinstance(result, bytes)
    # Check if the bytes object is not empty and looks like an Excel file (starts with PK zip header)
    assert len(result) > 0
    assert result.startswith(b"PK\x03\x04")


def test_format_transcript_invalid_format(sample_vtt_content):
    """Tests that an invalid format raises a ValueError."""
    with pytest.raises(
        ValueError, match="Unsupported output format: invalid_format"
    ):
        format_transcript(
            file_content=sample_vtt_content.encode("utf-8"),
            original_filename="sample.vtt",
            output_format="invalid_format",
        )


@pytest.fixture
def simplified_chinese_vtt_content():
    """Provides VTT content with simplified Chinese in MAC_WHISPER format."""
    return (
        "WEBVTT\n\n"
        "00:00:00.500 --> 00:00:03.000\n"
        "教练: 你好，这是一段测试录音。\n\n"
        "00:00:03.500 --> 00:00:06.000\n"
        "客户: 你好教练，我们来谈谈项目进展。\n"
    )


def test_format_transcript_simplified_to_traditional(
    simplified_chinese_vtt_content,
):
    """Tests converting simplified Chinese to traditional Chinese."""
    result = format_transcript(
        file_content=simplified_chinese_vtt_content.encode("utf-8"),
        original_filename="simplified.vtt",
        output_format="markdown",
        convert_to_traditional_chinese=True,
        coach_name="教练",
        client_name="客户",
    )
    assert isinstance(result, str)
    # Check for traditional characters in the output
    assert "**Coach**" in result
    assert "**Client**" in result
    assert "你好，這是一段測試錄音。" in result
    assert "你好教練，我們來談談項目進展。" in result

    # Verify that simplified characters are no longer present
    assert "这是一段测试录音。" not in result
    assert "你好教练，我们来谈谈项目进展。" not in result
