import pytest

from coaching_assistant.core.config import Settings


@pytest.mark.parametrize(
    "value,expected",
    [
        (
            "http://localhost:3000, https://example.com",
            ["http://localhost:3000", "https://example.com"],
        ),
        (
            '["http://localhost:3000", "https://example.com"]',
            ["http://localhost:3000", "https://example.com"],
        ),
        (
            '"http://localhost:3000"',
            ["http://localhost:3000"],
        ),
        ("", []),
    ],
)
def test_allowed_origins_parsing(value, expected):
    settings = Settings(ALLOWED_ORIGINS=value)
    assert settings.ALLOWED_ORIGINS == expected


def test_allowed_origins_default_list_remains_unchanged():
    settings = Settings()
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert settings.ALLOWED_ORIGINS  # default list is not empty
