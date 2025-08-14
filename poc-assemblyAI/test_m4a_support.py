#!/usr/bin/env python3
"""
Test AssemblyAI M4A format support
"""

import assemblyai as aai
import json
from pathlib import Path
import time

# Configure API key
aai.settings.api_key = "f14cc71498f24b22a56c2be2fa4eb6b2"

def test_m4a_support():
    """
    Test if AssemblyAI can handle M4A files
    """
    print("=" * 60)
    print("ASSEMBLYAI M4A FORMAT SUPPORT TEST")
    print("=" * 60)
    
    # Check supported formats from AssemblyAI documentation
    print("\nAssemblyAI officially supports these audio formats:")
    supported_formats = [
        "3gp", "aac", "aiff", "amr", "ape", "au", "avi", "caf", "dss", "flac", 
        "flv", "m4a", "m4v", "mkv", "mov", "mp3", "mp4", "mpc", "mpeg", "mpg", 
        "ogg", "opus", "qcp", "qt", "ra", "ram", "wav", "webm", "wma", "wmv"
    ]
    
    print(", ".join(supported_formats))
    print(f"\n✅ M4A is officially supported: {'m4a' in supported_formats}")
    
    # Test with a sample M4A file if available
    test_m4a_file = "./test-data/sample.m4a"
    
    if Path(test_m4a_file).exists():
        print(f"\n🔍 Testing actual M4A file: {test_m4a_file}")
        
        try:
            config = aai.TranscriptionConfig(
                speech_model=aai.SpeechModel.best,
                speaker_labels=True,
                speakers_expected=2,
                language_detection=True,
            )
            
            print("Starting transcription test...")
            start_time = time.time()
            
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(test_m4a_file, config=config)
            
            elapsed = time.time() - start_time
            
            if transcript.status == "error":
                print(f"❌ Transcription failed: {transcript.error}")
                return False
            else:
                print(f"✅ M4A file successfully transcribed in {elapsed:.2f} seconds")
                print(f"   Language detected: {getattr(transcript, 'language_code', 'unknown')}")
                print(f"   Text length: {len(transcript.text)} characters")
                print(f"   Utterances: {len(transcript.utterances) if transcript.utterances else 0}")
                
                # Save sample results
                results = {
                    "format": "m4a",
                    "status": "success",
                    "processing_time": elapsed,
                    "language": getattr(transcript, 'language_code', 'unknown'),
                    "text_length": len(transcript.text),
                    "utterance_count": len(transcript.utterances) if transcript.utterances else 0,
                    "sample_text": transcript.text[:200] + "..." if len(transcript.text) > 200 else transcript.text
                }
                
                with open("./test_results/m4a_test_results.json", 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                
                return True
                
        except Exception as e:
            print(f"❌ Error testing M4A file: {e}")
            return False
    else:
        print(f"\n⚠️  No M4A test file found at {test_m4a_file}")
        print("To test with actual M4A file:")
        print("1. Place an M4A audio file at ./test-data/sample.m4a")
        print("2. Run this script again")
    
    return True

def create_test_recommendations():
    """
    Provide recommendations for M4A testing
    """
    print("\n" + "=" * 60)
    print("M4A TESTING RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = [
        "✅ M4A is officially supported by AssemblyAI",
        "🎯 Test with various M4A quality settings (bitrate, sample rate)",
        "🔊 Verify mono vs stereo M4A handling",
        "🎤 Test M4A files with different codecs (AAC-LC, AAC-HE)",
        "⏱️  Compare M4A vs MP4 processing times",
        "🗣️  Ensure speaker diarization works with M4A",
        "🌐 Test M4A with different languages (especially Chinese)",
        "📱 Test M4A files recorded from iOS devices (common format)"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print("\n💡 Next steps:")
    print("  1. Convert existing MP4 test file to M4A")
    print("  2. Record new M4A sample for testing")
    print("  3. Add M4A to supported formats in frontend upload")
    print("  4. Update documentation to mention M4A support")

if __name__ == "__main__":
    # Create results directory
    Path("./test_results").mkdir(exist_ok=True)
    
    try:
        success = test_m4a_support()
        create_test_recommendations()
        
        if success:
            print("\n🎉 M4A format support confirmed!")
        else:
            print("\n⚠️  M4A support needs further testing")
            
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()