#!/usr/bin/env python3
"""
Module for parsing VTT files into a structured format.
Supports multiple formats:
1. MS Teams VTT format: <v Speaker Name>Text</v>
2. MacWhisper VTT format: Speaker Name: Text
"""
import re
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Type, Pattern, Match, Tuple

class VTTFormat(Enum):
    """Supported VTT format types."""
    MS_TEAMS = auto()    # <v Speaker>Text</v>
    MAC_WHISPER = auto() # Speaker: Text
    # Add more formats here like ZOOM, SRT, etc.

class BaseVTTParser(ABC):
    """Base class for VTT parsers."""
    
    @classmethod
    @abstractmethod
    def get_pattern(cls) -> str:
        """Return the regex pattern for this format."""
        pass
    
    @classmethod
    @abstractmethod
    def extract_data(cls, match: Match) -> Dict[str, Any]:
        """Extract data from regex match groups."""
        pass
    
    @classmethod
    def parse(cls, content: str) -> List[Dict[str, Any]]:
        """Parse VTT content using this parser's format."""
        matches = re.finditer(cls.get_pattern(), content, re.DOTALL)
        return [cls.extract_data(match) for match in matches]

class MSTeamsParser(BaseVTTParser):
    """Parser for MS Teams VTT format: <v Speaker>Text</v>"""
    
    @classmethod
    def get_pattern(cls) -> str:
        return r'(?m)^(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}\s*\n<v\s*([^>]+)>([^<]+)</v>'
    
    @classmethod
    def extract_data(cls, match: Match) -> Dict[str, Any]:
        return {
            'time': match.group(1).strip(),
            'speaker': match.group(2).strip(),
            'content': match.group(3).strip().replace('\n', ' ')
        }

class MacWhisperParser(BaseVTTParser):
    """Parser for MacWhisper VTT format: Speaker: Text"""
    
    @classmethod
    def get_pattern(cls) -> str:
        return r'(?m)^(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}\s*\n([^\n:]+):\s*([^\n]+)'
    
    @classmethod
    def extract_data(cls, match: Match) -> Dict[str, Any]:
        return {
            'time': match.group(1).strip(),
            'speaker': match.group(2).strip(),
            'content': match.group(3).strip()
        }

# Map of format names to their respective parsers
PARSERS = {
    'MS_TEAMS': MSTeamsParser,
    'MAC_WHISPER': MacWhisperParser,
}

def detect_format(content: str) -> Optional[VTTFormat]:
    """Detect the VTT format from the content."""
    # Check for MS Teams format
    if re.search(r'<v\s*[^>]+>.*</v>', content, re.DOTALL):
        return VTTFormat.MS_TEAMS
    # Check for MacWhisper format (Speaker: Text pattern)
    if re.search(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}\s*\n[^\n:]+:', content, re.MULTILINE):
        return VTTFormat.MAC_WHISPER
    
    return None

def parse_vtt(content: str, format_type: Optional[VTTFormat] = None) -> List[Dict[str, Any]]:
    """
    Parse VTT content and return a list of dictionaries with time, speaker, and content.

    Args:
        content: The string content of the VTT file.
        format_type: Optional format type to force. If None, will auto-detect.

    Returns:
        List of dictionaries containing 'time', 'speaker', and 'content' keys.

    Raises:
        ValueError: If the format cannot be detected or is not supported.
    """
    
    # If format not specified, try to detect it
    if format_type is None:
        format_type = detect_format(content)
        if format_type is None:
            raise ValueError("Could not detect VTT format. Please specify the format type.")
        format_name = format_type.name if hasattr(format_type, 'name') else str(format_type)
        print(f"Detected VTT format: {format_name}")
    else:
        format_name = format_type.name if hasattr(format_type, 'name') else str(format_type)
        print(f"Using specified VTT format: {format_name}")
    
    # Get the appropriate parser
    parser = PARSERS.get(format_name)
    if parser is None:
        raise ValueError(f"No parser available for format: {format_name}")
    
    # Parse the content
    try:
        return parser.parse(content)
    except Exception as e:
        raise ValueError(f"Error parsing VTT file with format {format_name}: {str(e)}")

def consolidate_speakers(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Consolidate consecutive speeches from the same speaker.
    
    Args:
        data: List of parsed VTT entries
        
    Returns:
        Consolidated list of entries
    """
    consolidated = []
    current_speaker = None
    current_content = []
    current_time = None

    for item in data:
        if item['speaker'] != current_speaker:
            if current_speaker:
                consolidated.append({
                    'time': current_time,
                    'speaker': current_speaker,
                    'content': ' '.join(current_content)
                })
            current_speaker = item['speaker']
            current_content = [item['content']]
            current_time = item['time']
        else:
            current_content.append(item['content'])

    if current_speaker:
        consolidated.append({
            'time': current_time,
            'speaker': current_speaker,
            'content': ' '.join(current_content)
        })

    return consolidated

def replace_names(data: List[Dict[str, Any]], coach: str, client: str) -> List[Dict[str, Any]]:
    """
    Replace speaker names with 'Coach' or 'Client' based on provided names.
    
    Args:
        data: List of VTT entries
        coach: Name of the coach to be replaced with 'Coach'
        client: Name of the client to be replaced with 'Client'
        
    Returns:
        List of entries with replaced names
    """
    for item in data:
        if item['speaker'] == coach:
            item['speaker'] = 'Coach'
        elif item['speaker'] == client:
            item['speaker'] = 'Client'
    return data
