#!/usr/bin/env python3
"""
Chinese Text Post-Processor for AssemblyAI Output
Handles the three main issues identified:
1. Removes spaces between Chinese characters
2. Converts Simplified to Traditional Chinese
3. Fixes language code identification
"""

import re
from typing import Dict, List, Optional

def remove_chinese_spaces(text: str) -> str:
    """
    Remove spaces between Chinese characters while preserving spaces
    between Chinese and English text
    
    Example:
        Input:  "我 想要 聊 一个 关于 work life balance 的 议题"
        Output: "我想要聊一个关于 work life balance 的议题"
    """
    # Pattern: Space between two Chinese characters
    chinese_pattern = r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])'
    text = re.sub(chinese_pattern, '', text)
    
    # Also handle CJK punctuation
    cjk_punct_pattern = r'(?<=[\u4e00-\u9fff])\s+(?=[，。！？；：、])'
    text = re.sub(cjk_punct_pattern, '', text)
    
    punct_cjk_pattern = r'(?<=[，。！？；：、])\s+(?=[\u4e00-\u9fff])'
    text = re.sub(punct_cjk_pattern, '', text)
    
    return text

def convert_to_traditional(text: str) -> str:
    """
    Convert Simplified Chinese to Traditional Chinese
    Requires: pip install opencc-python-reimplemented
    """
    try:
        from opencc import OpenCC
        cc = OpenCC('s2twp')  # Simplified to Traditional (Taiwan) with phrase conversion
        return cc.convert(text)
    except ImportError:
        print("Warning: OpenCC not installed. Install with: pip install opencc-python-reimplemented")
        return text
    except Exception as e:
        print(f"Error converting to Traditional Chinese: {e}")
        return text

def fix_mixed_chinese(text: str) -> str:
    """
    Fix mixed Simplified and Traditional Chinese in the same text
    by converting everything to Traditional
    """
    # Common character mappings that might be missed
    replacements = {
        '这': '這', '说': '說', '觉': '覺', '会': '會',
        '给': '給', '对': '對', '让': '讓', '过': '過',
        '时': '時', '应': '應', '开': '開', '关': '關',
        '还': '還', '为': '為', '来': '來', '与': '與',
        '个': '個', '们': '們', '么': '麼', '得': '得',
    }
    
    for simp, trad in replacements.items():
        text = text.replace(simp, trad)
    
    return text

def detect_chinese_language(text: str) -> str:
    """
    Detect whether text is Traditional or Simplified Chinese
    Returns language code suitable for our system
    """
    # Count Traditional vs Simplified characters
    traditional_chars = set('這說覺會給對讓過時應開關還為來與個們麼')
    simplified_chars = set('这说觉会给对让过时应开关还为来与个们么')
    
    trad_count = sum(1 for char in text if char in traditional_chars)
    simp_count = sum(1 for char in text if char in simplified_chars)
    
    if trad_count > simp_count:
        return "zh-TW"  # Traditional Chinese (Taiwan)
    elif simp_count > 0:
        return "zh-CN"  # Simplified Chinese (China)
    else:
        # Check for any Chinese characters
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "zh"  # Generic Chinese
        return "unknown"

def process_assemblyai_chinese(transcript_data: Dict) -> Dict:
    """
    Process AssemblyAI transcript data to fix Chinese formatting issues
    
    Args:
        transcript_data: Dictionary containing AssemblyAI transcript data
        
    Returns:
        Processed transcript data with fixed Chinese text
    """
    # Process full text
    if 'full_text' in transcript_data:
        original_text = transcript_data['full_text']
        processed_text = remove_chinese_spaces(original_text)
        processed_text = convert_to_traditional(processed_text)
        processed_text = fix_mixed_chinese(processed_text)
        transcript_data['full_text'] = processed_text
        
        # Detect language if not properly set
        if transcript_data.get('language') in ['unknown', None]:
            transcript_data['language'] = detect_chinese_language(processed_text)
    
    # Process segments
    if 'segments' in transcript_data:
        for segment in transcript_data['segments']:
            if 'text' in segment:
                original = segment['text']
                processed = remove_chinese_spaces(original)
                processed = convert_to_traditional(processed)
                processed = fix_mixed_chinese(processed)
                segment['text'] = processed
    
    # Process utterances (if using raw AssemblyAI format)
    if 'utterances' in transcript_data:
        for utterance in transcript_data['utterances']:
            if 'text' in utterance:
                original = utterance['text']
                processed = remove_chinese_spaces(original)
                processed = convert_to_traditional(processed)
                processed = fix_mixed_chinese(processed)
                utterance['text'] = processed
    
    return transcript_data

def format_for_display(text: str) -> str:
    """
    Format Chinese text for display with proper punctuation
    """
    # Ensure Chinese punctuation is used consistently
    replacements = {
        '.': '。',
        ',': '，',
        '?': '？',
        '!': '！',
        ':': '：',
        ';': '；',
        '(': '（',
        ')': '）',
    }
    
    # Only replace if surrounded by Chinese characters
    for eng, chi in replacements.items():
        pattern = f'(?<=[\u4e00-\u9fff]){re.escape(eng)}(?=[\u4e00-\u9fff])'
        text = re.sub(pattern, chi, text)
    
    return text

def process_segment_for_export(segment: Dict) -> Dict:
    """
    Process a single segment for export formats (VTT, SRT, etc.)
    """
    if 'text' in segment:
        segment['text'] = remove_chinese_spaces(segment['text'])
        segment['text'] = convert_to_traditional(segment['text'])
        segment['text'] = fix_mixed_chinese(segment['text'])
        segment['text'] = format_for_display(segment['text'])
    
    return segment

# Example usage and testing
if __name__ == "__main__":
    # Test samples from actual AssemblyAI output
    test_samples = [
        "我 想要 聊 一个 关于 生活 工作",
        "平衡 的 议题 嗯 生活 工作 平",
        "那 你 想 覺得 這個 平衡 對 你來 說 是 什麼 呢",
        "对 我们 当天 甚至还针对 这 一件 事情 还特别 的 聊 了 一下",
    ]
    
    print("Chinese Text Processing Tests")
    print("=" * 60)
    
    for sample in test_samples:
        print(f"\nOriginal: {sample}")
        processed = remove_chinese_spaces(sample)
        processed = convert_to_traditional(processed)
        processed = fix_mixed_chinese(processed)
        print(f"Processed: {processed}")
        print(f"Language: {detect_chinese_language(processed)}")
    
    # Test with actual transcript data structure
    test_transcript = {
        "full_text": "我 想要 聊 一个 关于 生活 工作 平衡 的 议题",
        "language": "unknown",
        "segments": [
            {"text": "我 想要 聊 一个 关于 生活 工作", "start_time": 2.89},
            {"text": "平衡 的 议题 嗯 生活 工作 平", "start_time": 6.21},
        ]
    }
    
    print("\n" + "=" * 60)
    print("Full Transcript Processing Test")
    print("=" * 60)
    processed_transcript = process_assemblyai_chinese(test_transcript.copy())
    print(f"Original language: {test_transcript['language']}")
    print(f"Detected language: {processed_transcript['language']}")
    print(f"Original text: {test_transcript['full_text']}")
    print(f"Processed text: {processed_transcript['full_text']}")
    
    print("\nProcessed segments:")
    for i, segment in enumerate(processed_transcript['segments'], 1):
        print(f"{i}. {segment['text']}")