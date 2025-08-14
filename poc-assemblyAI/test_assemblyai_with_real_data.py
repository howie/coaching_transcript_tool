#!/usr/bin/env python3
"""
Test AssemblyAI with real coaching session data
"""

import assemblyai as aai
import json
from datetime import datetime
from pathlib import Path
import time

# Configure API key
aai.settings.api_key = "f14cc71498f24b22a56c2be2fa4eb6b2"

def transcribe_coaching_session(file_path: str, output_dir: str = "./test_results"):
    """
    Transcribe a real coaching session and save results
    """
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Configure for coaching session (2 speakers expected)
    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.best,
        speaker_labels=True,  # Enable speaker diarization
        speakers_expected=2,  # Coach and Client
        language_detection=True,  # Auto-detect language
    )
    
    print(f"Starting transcription of: {file_path}")
    print("This may take a few minutes...")
    
    start_time = time.time()
    
    # Create transcriber and process file
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path, config=config)
    
    if transcript.status == "error":
        raise RuntimeError(f"Transcription failed: {transcript.error}")
    
    elapsed = time.time() - start_time
    print(f"Transcription completed in {elapsed:.2f} seconds")
    
    # Analyze speaker distribution
    speaker_analysis = analyze_speakers(transcript)
    
    # Format results
    results = {
        "file": file_path,
        "processing_time_seconds": elapsed,
        "metadata": {
            "service": "AssemblyAI",
            "model": "best",
            "language": transcript.language_code if hasattr(transcript, 'language_code') else "unknown",
            "duration_seconds": transcript.audio_duration / 1000 if hasattr(transcript, 'audio_duration') else 0,
            "timestamp": datetime.now().isoformat()
        },
        "full_transcript": transcript.text,
        "speaker_analysis": speaker_analysis,
        "segments": []
    }
    
    # Process segments with speaker labels
    if transcript.utterances:
        for utterance in transcript.utterances:
            segment = {
                "speaker": f"Speaker {utterance.speaker}",
                "start_time": utterance.start / 1000,
                "end_time": utterance.end / 1000,
                "duration": (utterance.end - utterance.start) / 1000,
                "text": utterance.text,
                "confidence": utterance.confidence if hasattr(utterance, 'confidence') else None
            }
            results["segments"].append(segment)
    
    # Save full results to JSON
    output_file = Path(output_dir) / "assemblyai_evaluation_1_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Save transcript in simple text format
    text_output = Path(output_dir) / "assemblyai_evaluation_1_transcript.txt"
    with open(text_output, 'w', encoding='utf-8') as f:
        f.write("AssemblyAI Transcription - Evaluation_1.mp4\n")
        f.write("=" * 60 + "\n\n")
        
        if transcript.utterances:
            for utterance in transcript.utterances:
                timestamp = f"[{utterance.start/1000:.2f}s - {utterance.end/1000:.2f}s]"
                speaker = f"Speaker {utterance.speaker}"
                f.write(f"{timestamp} {speaker}:\n{utterance.text}\n\n")
    
    print(f"Transcript saved to: {text_output}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("TRANSCRIPTION SUMMARY")
    print("=" * 60)
    print(f"Total duration: {results['metadata']['duration_seconds']:.2f} seconds")
    print(f"Total words: {len(transcript.text.split())}")
    print(f"Total segments: {len(results['segments'])}")
    print(f"Language detected: {results['metadata']['language']}")
    
    if speaker_analysis:
        print("\nSPEAKER ANALYSIS:")
        for speaker, stats in speaker_analysis.items():
            print(f"\n{speaker}:")
            print(f"  - Speaking time: {stats['total_time']:.2f} seconds ({stats['percentage']:.1f}%)")
            print(f"  - Word count: {stats['word_count']} words")
            print(f"  - Number of turns: {stats['turn_count']}")
            print(f"  - Questions asked: {stats['questions']}")
    
    # Show first few segments as preview
    print("\n" + "=" * 60)
    print("FIRST 5 SEGMENTS PREVIEW")
    print("=" * 60)
    for i, segment in enumerate(results['segments'][:5], 1):
        text_preview = segment['text'][:100] + "..." if len(segment['text']) > 100 else segment['text']
        print(f"{i}. [{segment['speaker']}] {segment['start_time']:.2f}s: {text_preview}")
    
    return results

def analyze_speakers(transcript):
    """
    Analyze speaker patterns to help identify Coach vs Client
    """
    if not transcript.utterances:
        return {}
    
    speaker_stats = {}
    total_duration = 0
    
    for utterance in transcript.utterances:
        speaker = f"Speaker {utterance.speaker}"
        duration = (utterance.end - utterance.start) / 1000
        total_duration += duration
        
        if speaker not in speaker_stats:
            speaker_stats[speaker] = {
                "total_time": 0,
                "word_count": 0,
                "turn_count": 0,
                "questions": 0,
                "segments": []
            }
        
        speaker_stats[speaker]["total_time"] += duration
        speaker_stats[speaker]["word_count"] += len(utterance.text.split())
        speaker_stats[speaker]["turn_count"] += 1
        
        # Count questions
        if "?" in utterance.text:
            speaker_stats[speaker]["questions"] += 1
    
    # Calculate percentages
    for speaker in speaker_stats:
        speaker_stats[speaker]["percentage"] = (speaker_stats[speaker]["total_time"] / total_duration * 100) if total_duration > 0 else 0
    
    # Guess roles based on patterns
    speakers = list(speaker_stats.keys())
    if len(speakers) == 2:
        # Heuristic: Coach typically asks more questions
        if speaker_stats[speakers[0]]["questions"] > speaker_stats[speakers[1]]["questions"]:
            speaker_stats[speakers[0]]["likely_role"] = "Coach"
            speaker_stats[speakers[1]]["likely_role"] = "Client"
        else:
            speaker_stats[speakers[0]]["likely_role"] = "Client"
            speaker_stats[speakers[1]]["likely_role"] = "Coach"
    
    return speaker_stats

def compare_with_google_stt():
    """
    Compare AssemblyAI results with Google STT results if available
    """
    # Check if Google STT results exist
    google_results_path = Path("./test-data/google_stt_results.json")
    assemblyai_results_path = Path("./test_results/assemblyai_evaluation_1_results.json")
    
    if not assemblyai_results_path.exists():
        print("AssemblyAI results not found. Run transcription first.")
        return
    
    with open(assemblyai_results_path, 'r') as f:
        assemblyai_data = json.load(f)
    
    print("\n" + "=" * 60)
    print("ASSEMBLYAI RESULTS SUMMARY")
    print("=" * 60)
    print(f"Processing time: {assemblyai_data['processing_time_seconds']:.2f} seconds")
    print(f"Total words: {len(assemblyai_data['full_transcript'].split())}")
    print(f"Total segments: {len(assemblyai_data['segments'])}")
    print(f"Language: {assemblyai_data['metadata']['language']}")
    
    if google_results_path.exists():
        with open(google_results_path, 'r') as f:
            google_data = json.load(f)
        
        print("\n" + "=" * 60)
        print("COMPARISON WITH GOOGLE STT")
        print("=" * 60)
        # Add comparison logic here
        print("Google STT results found - detailed comparison would go here")
    else:
        print("\nGoogle STT results not found for comparison")

if __name__ == "__main__":
    # Test with the actual coaching session file
    test_file = "./test-data/Evaluation_1.mp4"
    
    if not Path(test_file).exists():
        print(f"Error: Test file not found at {test_file}")
        exit(1)
    
    print("=" * 60)
    print("ASSEMBLYAI TRANSCRIPTION TEST")
    print("Real Coaching Session: Evaluation_1.mp4")
    print("=" * 60)
    
    try:
        # Run transcription
        results = transcribe_coaching_session(test_file)
        
        # Compare with Google STT if available
        compare_with_google_stt()
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE!")
        print("=" * 60)
        print("\nReview the following files for detailed results:")
        print("- test_results/assemblyai_evaluation_1_results.json (full data)")
        print("- test_results/assemblyai_evaluation_1_transcript.txt (readable format)")
        
    except Exception as e:
        print(f"\nError during transcription: {e}")
        import traceback
        traceback.print_exc()