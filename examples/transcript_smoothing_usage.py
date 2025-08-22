"""
Usage examples for the transcript smoothing service.

This file demonstrates how to use the transcript smoothing functionality
both as a Python library and via the REST API.
"""

import asyncio
import json
from coaching_assistant.services.transcript_smoother import smooth_and_punctuate


def example_chinese_transcript():
    """Example Chinese coaching session transcript."""
    return {
        "utterances": [
            {
                "speaker": "A",
                "start": 1000,
                "end": 4500,
                "confidence": 0.92,
                "words": [
                    {"text": "好", "start": 1000, "end": 1200, "confidence": 0.95},
                    {"text": "那", "start": 1200, "end": 1400, "confidence": 0.89},
                    {"text": "我們", "start": 1400, "end": 1750, "confidence": 0.94},
                    {"text": "今天", "start": 1750, "end": 2100, "confidence": 0.97},
                    {"text": "來", "start": 2100, "end": 2250, "confidence": 0.93},
                    {"text": "聊聊", "start": 2250, "end": 2600, "confidence": 0.96},
                    {"text": "你", "start": 2600, "end": 2750, "confidence": 0.91},
                    {"text": "最近", "start": 2750, "end": 3100, "confidence": 0.88},
                    {"text": "的", "start": 3100, "end": 3200, "confidence": 0.92},
                    {"text": "想法", "start": 3200, "end": 3600, "confidence": 0.95}
                ]
            },
            {
                "speaker": "B",
                "start": 3700,
                "end": 3950,
                "confidence": 0.78,
                "words": [
                    {"text": "嗯", "start": 3700, "end": 3950, "confidence": 0.82}
                ]
            },
            {
                "speaker": "A", 
                "start": 4000,
                "end": 6500,
                "confidence": 0.88,
                "words": [
                    {"text": "你", "start": 4000, "end": 4150, "confidence": 0.95},
                    {"text": "覺得", "start": 4150, "end": 4500, "confidence": 0.89},
                    {"text": "工作", "start": 4500, "end": 4850, "confidence": 0.97},
                    {"text": "上", "start": 4850, "end": 5000, "confidence": 0.92},
                    {"text": "有", "start": 5000, "end": 5150, "confidence": 0.88},
                    {"text": "什麼", "start": 5150, "end": 5500, "confidence": 0.94},
                    {"text": "挑戰", "start": 5500, "end": 5900, "confidence": 0.91},
                    {"text": "嗎", "start": 5900, "end": 6100, "confidence": 0.96}
                ]
            }
        ]
    }


def example_english_transcript():
    """Example English coaching session transcript."""
    return {
        "utterances": [
            {
                "speaker": "A",
                "start": 1000,
                "end": 3500,
                "confidence": 0.94,
                "words": [
                    {"text": "So", "start": 1000, "end": 1150, "confidence": 0.96},
                    {"text": "let's", "start": 1150, "end": 1350, "confidence": 0.92},
                    {"text": "talk", "start": 1350, "end": 1650, "confidence": 0.98},
                    {"text": "about", "start": 1650, "end": 1900, "confidence": 0.94},
                    {"text": "your", "start": 1900, "end": 2100, "confidence": 0.97},
                    {"text": "recent", "start": 2100, "end": 2450, "confidence": 0.95},
                    {"text": "challenges", "start": 2450, "end": 2950, "confidence": 0.99}
                ]
            },
            {
                "speaker": "B",
                "start": 3100,
                "end": 3350,
                "confidence": 0.81,
                "words": [
                    {"text": "Yeah", "start": 3100, "end": 3350, "confidence": 0.85}
                ]
            },
            {
                "speaker": "A",
                "start": 3400,
                "end": 5200,
                "confidence": 0.89,
                "words": [
                    {"text": "What", "start": 3400, "end": 3600, "confidence": 0.94},
                    {"text": "do", "start": 3600, "end": 3700, "confidence": 0.91},
                    {"text": "you", "start": 3700, "end": 3850, "confidence": 0.97},
                    {"text": "think", "start": 3850, "end": 4100, "confidence": 0.93},
                    {"text": "is", "start": 4100, "end": 4200, "confidence": 0.98},
                    {"text": "your", "start": 4200, "end": 4350, "confidence": 0.89},
                    {"text": "biggest", "start": 4350, "end": 4700, "confidence": 0.95},
                    {"text": "obstacle", "start": 4700, "end": 5200, "confidence": 0.92}
                ]
            }
        ]
    }


def demo_library_usage():
    """Demonstrate library usage with examples."""
    print("=" * 60)
    print("TRANSCRIPT SMOOTHING LIBRARY USAGE DEMO")
    print("=" * 60)
    
    # Chinese example
    print("\n🇨🇳 CHINESE TRANSCRIPT PROCESSING")
    print("-" * 40)
    
    chinese_transcript = example_chinese_transcript()
    
    print("Original utterances:")
    for i, utt in enumerate(chinese_transcript["utterances"]):
        words_text = "".join([w["text"] for w in utt["words"]])
        print(f"  {i+1}. Speaker {utt['speaker']}: {words_text}")
    
    # Process with explicit language
    result = smooth_and_punctuate(chinese_transcript, language="chinese")
    
    print(f"\nProcessed segments ({len(result['segments'])} total):")
    for i, seg in enumerate(result["segments"]):
        print(f"  {i+1}. Speaker {seg['speaker']}: {seg['text']}")
    
    print(f"\nProcessing statistics:")
    stats = result["stats"]
    print(f"  - Language detected: {stats['language_detected']}")
    print(f"  - Processor used: {stats['processor_used']}")
    print(f"  - Words moved: {stats['moved_word_count']}")
    print(f"  - Segments merged: {stats['merged_segments']}")
    print(f"  - Filler words backfilled: {stats['heuristic_hits']['filler_words']}")
    print(f"  - Short head backfills: {stats['heuristic_hits']['short_first_segment']}")
    
    # English example
    print("\n🇺🇸 ENGLISH TRANSCRIPT PROCESSING")
    print("-" * 40)
    
    english_transcript = example_english_transcript()
    
    print("Original utterances:")
    for i, utt in enumerate(english_transcript["utterances"]):
        words_text = " ".join([w["text"] for w in utt["words"]])
        print(f"  {i+1}. Speaker {utt['speaker']}: {words_text}")
    
    # Process with auto-detection
    result = smooth_and_punctuate(english_transcript, language="auto")
    
    print(f"\nProcessed segments ({len(result['segments'])} total):")
    for i, seg in enumerate(result["segments"]):
        print(f"  {i+1}. Speaker {seg['speaker']}: {seg['text']}")
    
    print(f"\nProcessing statistics:")
    stats = result["stats"]
    print(f"  - Language detected: {stats['language_detected']}")
    print(f"  - Processor used: {stats['processor_used']}")
    print(f"  - Words moved: {stats['moved_word_count']}")
    print(f"  - Segments merged: {stats['merged_segments']}")


def demo_custom_configuration():
    """Demonstrate custom configuration options."""
    print("\n⚙️ CUSTOM CONFIGURATION DEMO")
    print("-" * 40)
    
    transcript = example_chinese_transcript()
    
    # Default configuration
    print("Processing with default configuration:")
    result_default = smooth_and_punctuate(transcript, language="chinese")
    print(f"  - Segments: {len(result_default['segments'])}")
    print(f"  - Words moved: {result_default['stats']['moved_word_count']}")
    
    # Strict configuration (less aggressive smoothing)
    print("\nProcessing with strict configuration:")
    result_strict = smooth_and_punctuate(
        transcript,
        language="chinese",
        th_short_head_sec=0.3,  # Very short threshold
        th_filler_max_sec=0.2,  # Very short filler threshold
        th_sent_gap_sec=1.0     # Longer pause for sentence splits
    )
    print(f"  - Segments: {len(result_strict['segments'])}")
    print(f"  - Words moved: {result_strict['stats']['moved_word_count']}")
    
    # Permissive configuration (more aggressive smoothing)
    print("\nProcessing with permissive configuration:")
    result_permissive = smooth_and_punctuate(
        transcript,
        language="chinese",
        th_short_head_sec=2.0,   # Longer threshold
        th_filler_max_sec=1.0,   # Longer filler threshold
        th_sent_gap_sec=0.3,     # Shorter pause for sentence splits
        n_pass=3                 # More smoothing passes
    )
    print(f"  - Segments: {len(result_permissive['segments'])}")
    print(f"  - Words moved: {result_permissive['stats']['moved_word_count']}")


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n❌ ERROR HANDLING DEMO")
    print("-" * 40)
    
    # Missing words error
    try:
        invalid_transcript = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 2000,
                    "confidence": 0.9,
                    "words": []  # Empty words list
                }
            ]
        }
        smooth_and_punctuate(invalid_transcript)
    except Exception as e:
        print(f"✅ Caught expected error: {type(e).__name__}: {e}")
    
    # Missing utterances error
    try:
        empty_transcript = {"utterances": []}
        smooth_and_punctuate(empty_transcript)
    except Exception as e:
        print(f"✅ Caught expected error: {type(e).__name__}: {e}")


def demo_api_usage():
    """Show example API usage with curl commands."""
    print("\n🌐 API USAGE EXAMPLES")
    print("-" * 40)
    
    # Example request body
    api_request = {
        "transcript": example_chinese_transcript(),
        "language": "chinese",
        "config": {
            "th_short_head_sec": 0.9,
            "th_filler_max_sec": 0.6,
            "th_sent_gap_sec": 0.6
        }
    }
    
    print("Example API request (POST /api/v1/transcript/smooth-and-punctuate):")
    print(json.dumps(api_request, indent=2, ensure_ascii=False))
    
    print("\nCurl command example:")
    print("""
curl -X POST "http://localhost:8000/api/v1/transcript/smooth-and-punctuate" \\
     -H "Content-Type: application/json" \\
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
     -d @transcript_request.json
    """)
    
    print("\nOther available endpoints:")
    print("  GET /api/v1/transcript/smooth/config/defaults?language=chinese")
    print("  GET /api/v1/transcript/smooth/languages")


if __name__ == "__main__":
    """Run all demos."""
    demo_library_usage()
    demo_custom_configuration()
    demo_error_handling()
    demo_api_usage()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Try the library functions with your own transcripts")
    print("2. Test the API endpoints with real authentication")
    print("3. Experiment with different configuration parameters")
    print("4. Check the comprehensive test suite for more examples")
    print("\nFor more information, see:")
    print("- docs/features/improve-assembly-with-lemur/")
    print("- tests/unit/services/test_transcript_smoother.py")
    print("- tests/integration/test_transcript_smoother_integration.py")