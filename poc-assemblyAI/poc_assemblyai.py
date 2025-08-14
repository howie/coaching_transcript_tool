#!/usr/bin/env python3
"""
AssemblyAI Transcription POC for Coaching Sessions
"""

import assemblyai as aai
import json
from datetime import datetime

# Configure API key
aai.settings.api_key = "f14cc71498f24b22a56c2be2fa4eb6b2"

def transcribe_with_speakers(audio_file):
    """
    Transcribe audio with speaker diarization
    """
    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.best,
        speaker_labels=True,  # Enable speaker diarization
    )
    
    print(f"Starting transcription of: {audio_file}")
    transcript = aai.Transcriber(config=config).transcribe(audio_file)
    
    if transcript.status == "error":
        raise RuntimeError(f"Transcription failed: {transcript.error}")
    
    return transcript

def format_transcript_output(transcript):
    """
    Format transcript with speaker labels and timestamps
    """
    output = []
    output.append("=" * 50)
    output.append("FULL TRANSCRIPT")
    output.append("=" * 50)
    output.append(transcript.text)
    output.append("")
    
    if transcript.utterances:
        output.append("=" * 50)
        output.append("SPEAKER DIARIZATION")
        output.append("=" * 50)
        
        for utterance in transcript.utterances:
            speaker = f"Speaker {utterance.speaker}"
            timestamp = f"[{utterance.start/1000:.2f}s - {utterance.end/1000:.2f}s]"
            output.append(f"{timestamp} {speaker}: {utterance.text}")
            output.append("")
    
    return "\n".join(output)

def export_to_json(transcript, filename="assemblyai_transcript.json"):
    """
    Export transcript to JSON format compatible with your system
    """
    segments = []
    
    if transcript.utterances:
        for utterance in transcript.utterances:
            segment = {
                "start_time": utterance.start / 1000,  # Convert to seconds
                "end_time": utterance.end / 1000,
                "text": utterance.text,
                "speaker": f"Speaker {utterance.speaker}",
                "confidence": utterance.confidence if hasattr(utterance, 'confidence') else None
            }
            segments.append(segment)
    
    export_data = {
        "metadata": {
            "transcription_service": "AssemblyAI",
            "model": "best",
            "timestamp": datetime.now().isoformat(),
            "duration": transcript.audio_duration if hasattr(transcript, 'audio_duration') else None
        },
        "full_text": transcript.text,
        "segments": segments
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported to {filename}")
    return filename

def main():
    # Test with sample audio or local file
    # audio_file = "./local_file.mp3"  # Uncomment to use local file
    audio_file = "https://assembly.ai/wildfires.mp3"  # Sample file
    
    try:
        # Transcribe with speaker diarization
        transcript = transcribe_with_speakers(audio_file)
        
        # Display formatted output
        formatted_output = format_transcript_output(transcript)
        print(formatted_output)
        
        # Export to JSON
        json_file = export_to_json(transcript)
        
        # Print statistics
        print("\n" + "=" * 50)
        print("STATISTICS")
        print("=" * 50)
        print(f"Total duration: {transcript.audio_duration/1000:.2f}s" if hasattr(transcript, 'audio_duration') else "Duration not available")
        print(f"Total words: {len(transcript.text.split())}")
        if transcript.utterances:
            speakers = set(u.speaker for u in transcript.utterances)
            print(f"Number of speakers: {len(speakers)}")
            print(f"Total utterances: {len(transcript.utterances)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()