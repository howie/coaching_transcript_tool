#!/usr/bin/env python3
"""
AssemblyAI Integration Example for Coaching Transcript Tool
Shows how to integrate AssemblyAI with your existing system
"""

import assemblyai as aai
import json
from typing import Dict, List, Optional
from datetime import datetime

# Configure API key
aai.settings.api_key = "f14cc71498f24b22a56c2be2fa4eb6b2"

class AssemblyAITranscriber:
    """
    AssemblyAI transcriber wrapper for coaching sessions
    """
    
    def __init__(self):
        self.config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best,
            speaker_labels=True,  # Enable speaker diarization
            speakers_expected=2,  # Coach and Client
            language_detection=True,  # Auto-detect language
        )
    
    def transcribe_audio(self, audio_url: str) -> Dict:
        """
        Transcribe audio and return format compatible with your system
        """
        print(f"Starting AssemblyAI transcription...")
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_url, config=self.config)
        
        if transcript.status == "error":
            raise RuntimeError(f"Transcription failed: {transcript.error}")
        
        return self._format_for_coaching_system(transcript)
    
    def _format_for_coaching_system(self, transcript) -> Dict:
        """
        Convert AssemblyAI format to your coaching system format
        """
        # Map speakers to Coach/Client (can be adjusted by user later)
        speaker_mapping = self._guess_speaker_roles(transcript)
        
        segments = []
        if transcript.utterances:
            for utterance in transcript.utterances:
                role = speaker_mapping.get(utterance.speaker, "Unknown")
                segment = {
                    "start_time": utterance.start / 1000,  # Convert to seconds
                    "end_time": utterance.end / 1000,
                    "text": utterance.text,
                    "speaker_role": role,  # Coach or Client
                    "original_speaker": f"Speaker {utterance.speaker}",
                    "confidence": utterance.confidence if hasattr(utterance, 'confidence') else 0.95
                }
                segments.append(segment)
        
        return {
            "status": "completed",
            "metadata": {
                "service": "AssemblyAI",
                "model": "best",
                "language": transcript.language_code if hasattr(transcript, 'language_code') else "en",
                "duration_seconds": transcript.audio_duration / 1000 if hasattr(transcript, 'audio_duration') else 0,
                "timestamp": datetime.now().isoformat()
            },
            "transcript": {
                "full_text": transcript.text,
                "segments": segments
            },
            "statistics": {
                "total_words": len(transcript.text.split()),
                "total_segments": len(segments),
                "speakers_detected": len(speaker_mapping)
            }
        }
    
    def _guess_speaker_roles(self, transcript) -> Dict[str, str]:
        """
        Simple heuristic to guess Coach vs Client
        Coach typically asks more questions and guides the conversation
        """
        if not transcript.utterances:
            return {}
        
        # Count questions per speaker
        speaker_stats = {}
        for utterance in transcript.utterances:
            speaker = utterance.speaker
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {"questions": 0, "statements": 0, "word_count": 0}
            
            # Count questions (simple heuristic)
            if "?" in utterance.text:
                speaker_stats[speaker]["questions"] += 1
            else:
                speaker_stats[speaker]["statements"] += 1
            
            speaker_stats[speaker]["word_count"] += len(utterance.text.split())
        
        # Simple rule: Speaker with more questions is likely the coach
        speakers = list(speaker_stats.keys())
        if len(speakers) == 2:
            if speaker_stats[speakers[0]]["questions"] > speaker_stats[speakers[1]]["questions"]:
                return {speakers[0]: "Coach", speakers[1]: "Client"}
            else:
                return {speakers[0]: "Client", speakers[1]: "Coach"}
        
        # Default mapping
        return {speaker: f"Speaker {speaker}" for speaker in speakers}

def compare_with_google_stt(audio_url: str):
    """
    Compare AssemblyAI results with your existing Google STT
    """
    print("\n" + "=" * 50)
    print("COMPARISON: AssemblyAI vs Google STT")
    print("=" * 50)
    
    # AssemblyAI transcription
    assemblyai_transcriber = AssemblyAITranscriber()
    assemblyai_result = assemblyai_transcriber.transcribe_audio(audio_url)
    
    print("\nAssemblyAI Results:")
    print(f"- Total words: {assemblyai_result['statistics']['total_words']}")
    print(f"- Total segments: {assemblyai_result['statistics']['total_segments']}")
    print(f"- Speakers detected: {assemblyai_result['statistics']['speakers_detected']}")
    
    # Export for comparison
    with open("assemblyai_coaching_format.json", "w", encoding="utf-8") as f:
        json.dump(assemblyai_result, f, indent=2, ensure_ascii=False)
    
    print("\nExported to assemblyai_coaching_format.json")
    
    # Display sample segments
    print("\nSample Segments (first 5):")
    for i, segment in enumerate(assemblyai_result['transcript']['segments'][:5]):
        print(f"{i+1}. [{segment['speaker_role']}] {segment['start_time']:.2f}s: {segment['text'][:100]}...")
    
    return assemblyai_result

def test_with_local_file():
    """
    Test with a local coaching session audio file
    """
    # Uncomment and update path to test with your local file
    # local_file = "/path/to/your/coaching_session.mp3"
    # result = compare_with_google_stt(local_file)
    
    # For demo, use AssemblyAI sample
    test_url = "https://assembly.ai/wildfires.mp3"
    result = compare_with_google_stt(test_url)
    
    return result

if __name__ == "__main__":
    print("AssemblyAI Integration POC for Coaching Transcript Tool")
    print("-" * 50)
    
    # Run the test
    result = test_with_local_file()
    
    print("\n" + "=" * 50)
    print("POC Complete!")
    print("=" * 50)
    print("\nNext Steps:")
    print("1. Test with actual coaching session audio")
    print("2. Compare accuracy with Google STT")
    print("3. Evaluate speaker diarization quality")
    print("4. Consider cost differences")
    print("5. Test with different languages (Chinese, Japanese)") 