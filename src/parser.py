#!/usr/bin/env python3
"""
Module for parsing VTT files into a structured format.
"""
import re
from typing import List, Dict, Any

def parse_vtt(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse a VTT file and return a list of dictionaries with time, speaker, and content.
    
    Args:
        file_path: Path to the VTT file
        
    Returns:
        List of dictionaries containing 'time', 'speaker', and 'content' keys
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\n<v ([^>]+)>(.+?)</v>'
    matches = re.findall(pattern, content, re.DOTALL)

    parsed_data = []
    for start_time, _, speaker, text in matches:
        parsed_data.append({
            'time': start_time,
            'speaker': speaker.strip(),
            'content': text.strip().replace('\n', ' ')
        })

    return parsed_data

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
