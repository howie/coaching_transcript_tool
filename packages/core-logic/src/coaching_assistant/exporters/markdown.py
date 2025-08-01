#!/usr/bin/env python3
"""
Module for exporting transcript data to Markdown format.
"""
from typing import List, Dict, Any

def _wrap_content(content: str, max_width: int) -> str:
    """Wrap content to the specified width."""
    if max_width <= 0 or len(content) <= max_width:
        return content
        
    words = content.split()
    wrapped_lines = []
    current_line = ""
    
    for word in words:
        if not current_line:
            current_line = word
        elif len(current_line) + len(word) + 1 <= max_width:
            current_line += f" {word}"
        else:
            wrapped_lines.append(current_line)
            current_line = word
    
    if current_line:
        wrapped_lines.append(current_line)
    
    return "<br>".join(wrapped_lines)

def _format_table_row(time: str, speaker: str, content: str) -> str:
    """Format a single row of the markdown table."""
    speaker_formatted = f"**{speaker}**" if speaker in ['Coach', 'Client'] else speaker
    return f"| {time} | {speaker_formatted} | {content} |\n"

def generate_markdown(data: List[Dict[str, Any]], content_width: int = 80) -> str:
    """
    Generate a Markdown table from the parsed data.
    
    Args:
        data: List of dictionaries with time, speaker, and content
        content_width: Maximum width for content column before wrapping (default: 80)
        
    Returns:
        Markdown table as a string
    """
    markdown = "| Time | Role | Content |\n| ---- | ---- | ------- |\n"
    
    for item in data:
        content = _wrap_content(item['content'], content_width)
        markdown += _format_table_row(item['time'], item['speaker'], content)
    
    return markdown
