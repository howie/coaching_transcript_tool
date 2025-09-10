#!/usr/bin/env python3
"""
Utility module for Chinese text conversion between Simplified and Traditional.
"""
from typing import Dict, Any, List

try:
    import opencc

    HAS_OPENCC = True
except ImportError:
    HAS_OPENCC = False


class ChineseConverter:
    """Handle conversion between Simplified and Traditional Chinese."""

    def __init__(self):
        self.converter = None
        if HAS_OPENCC:
            try:
                # s2t: Simplified Chinese to Traditional Chinese
                # Use 's2t' instead of 's2t.json' to let opencc find the correct config file
                self.converter = opencc.OpenCC("s2t")
            except Exception as e:
                print(f"Warning: Failed to initialize Chinese converter: {e}")

    def is_available(self) -> bool:
        """Check if the converter is available."""
        return self.converter is not None

    def convert_text(self, text: str) -> str:
        """Convert Simplified Chinese text to Traditional Chinese."""
        if not text or not self.converter:
            return text
        try:
            return self.converter.convert(text)
        except Exception as e:
            print(f"Warning: Failed to convert text: {e}")
            return text

    def convert_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Simplified Chinese text in a dictionary to Traditional Chinese."""
        if not self.converter:
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.convert_text(value)
            elif isinstance(value, dict):
                result[key] = self.convert_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    (
                        self.convert_dict(item)
                        if isinstance(item, dict)
                        else (
                            self.convert_text(item)
                            if isinstance(item, str)
                            else item
                        )
                    )
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def convert_list(
        self, data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert Simplified Chinese text in a list of dictionaries to Traditional Chinese."""
        if not self.converter:
            return data_list
        return [self.convert_dict(item) for item in data_list]


# Create a singleton instance
chinese_converter = ChineseConverter()


def is_conversion_available() -> bool:
    """Check if Chinese conversion is available."""
    return chinese_converter.is_available()


def convert_to_traditional(data):
    """
    Convert Simplified Chinese text to Traditional Chinese.

    Args:
        data: Can be a string, dictionary, or list of dictionaries

    Returns:
        Converted data with Traditional Chinese text
    """
    if not chinese_converter.is_available():
        print(
            "Warning: opencc-python-reimplemented is not installed. Chinese conversion will be skipped."
        )
        print(
            "Please install it with: pip install opencc-python-reimplemented"
        )
        return data

    if isinstance(data, str):
        return chinese_converter.convert_text(data)
    elif isinstance(data, dict):
        return chinese_converter.convert_dict(data)
    elif isinstance(data, list) and all(
        isinstance(item, dict) for item in data
    ):
        return chinese_converter.convert_list(data)
    return data
