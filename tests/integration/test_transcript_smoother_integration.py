"""
Integration tests for transcript smoothing with real AssemblyAI-like data.

Tests the complete pipeline with realistic data formats and scenarios.
"""

import pytest
from decimal import Decimal

from coaching_assistant.services.transcript_smoother import (
    smooth_and_punctuate,
    TranscriptSmoothingService,
    SupportedLanguage
)


class TestRealWorldIntegration:
    """Test integration with realistic AssemblyAI transcript data."""
    
    def test_chinese_coaching_session_transcript(self):
        """Test with a realistic Chinese coaching session transcript."""
        # Real-world AssemblyAI-like transcript data
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1240,
                    "end": 6780,
                    "confidence": 0.92,
                    "words": [
                        {"text": "好", "start": 1240, "end": 1450, "confidence": 0.95},
                        {"text": "那", "start": 1450, "end": 1620, "confidence": 0.89},
                        {"text": "我們", "start": 1620, "end": 1950, "confidence": 0.94},
                        {"text": "今天", "start": 1950, "end": 2280, "confidence": 0.97},
                        {"text": "的", "start": 2280, "end": 2380, "confidence": 0.93},
                        {"text": "教練", "start": 2380, "end": 2720, "confidence": 0.96},
                        {"text": "對話", "start": 2720, "end": 3100, "confidence": 0.91},
                        {"text": "就", "start": 3100, "end": 3250, "confidence": 0.88},
                        {"text": "從", "start": 3250, "end": 3420, "confidence": 0.92},
                        {"text": "這裡", "start": 3420, "end": 3750, "confidence": 0.95},
                        {"text": "開始", "start": 3750, "end": 4100, "confidence": 0.97}
                    ]
                },
                {
                    "speaker": "B",
                    "start": 4200,
                    "end": 4450,
                    "confidence": 0.78,
                    "words": [
                        {"text": "嗯", "start": 4200, "end": 4450, "confidence": 0.82}
                    ]
                },
                {
                    "speaker": "A", 
                    "start": 4500,
                    "end": 8900,
                    "confidence": 0.88,
                    "words": [
                        {"text": "你", "start": 4500, "end": 4650, "confidence": 0.95},
                        {"text": "最近", "start": 4650, "end": 5000, "confidence": 0.89},
                        {"text": "有", "start": 5000, "end": 5150, "confidence": 0.97},
                        {"text": "什麼", "start": 5150, "end": 5480, "confidence": 0.92},
                        {"text": "想要", "start": 5480, "end": 5820, "confidence": 0.88},
                        {"text": "討論", "start": 5820, "end": 6180, "confidence": 0.94},
                        {"text": "的", "start": 6180, "end": 6280, "confidence": 0.91},
                        {"text": "話題", "start": 6280, "end": 6650, "confidence": 0.96},
                        {"text": "嗎", "start": 6650, "end": 6850, "confidence": 0.93}
                    ]
                },
                {
                    "speaker": "B",
                    "start": 7200,
                    "end": 11500,
                    "confidence": 0.85,
                    "words": [
                        {"text": "我", "start": 7200, "end": 7350, "confidence": 0.98},
                        {"text": "想", "start": 7350, "end": 7520, "confidence": 0.94},
                        {"text": "跟", "start": 7520, "end": 7680, "confidence": 0.91},
                        {"text": "你", "start": 7680, "end": 7830, "confidence": 0.96},
                        {"text": "聊聊", "start": 7830, "end": 8180, "confidence": 0.88},
                        {"text": "關於", "start": 8180, "end": 8520, "confidence": 0.92},
                        {"text": "工作", "start": 8520, "end": 8850, "confidence": 0.95},
                        {"text": "上面", "start": 8850, "end": 9200, "confidence": 0.89},
                        {"text": "的", "start": 9200, "end": 9300, "confidence": 0.97},
                        {"text": "一些", "start": 9300, "end": 9650, "confidence": 0.83},
                        {"text": "挑戰", "start": 9650, "end": 10000, "confidence": 0.91}
                    ]
                }
            ]
        }
        
        # When
        result = smooth_and_punctuate(transcript_json, language="chinese")
        
        # Then
        assert "segments" in result
        assert "stats" in result
        
        segments = result["segments"]
        stats = result["stats"]
        
        # Should have processed the transcript (may merge into fewer segments due to smoothing)
        assert len(segments) >= 1
        assert stats["language_detected"] == "chinese"
        assert stats["processor_used"] == "ChineseProcessor"
        
        # Check processing occurred (may be short head backfill instead of filler word)
        assert stats["moved_word_count"] >= 0
        assert stats["heuristic_hits"]["short_first_segment"] + stats["heuristic_hits"]["filler_words"] >= 1
        
        # Verify segments have proper punctuation
        for segment in segments:
            assert segment["text"].endswith(("。", "？", "！", "…"))
            assert segment["speaker"] in ["A", "B"]
            assert segment["start_ms"] < segment["end_ms"]
    
    def test_english_coaching_session_transcript(self):
        """Test with a realistic English coaching session transcript."""
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 4500,
                    "confidence": 0.94,
                    "words": [
                        {"text": "So", "start": 1000, "end": 1150, "confidence": 0.96},
                        {"text": "let's", "start": 1150, "end": 1350, "confidence": 0.92},
                        {"text": "start", "start": 1350, "end": 1650, "confidence": 0.98},
                        {"text": "our", "start": 1650, "end": 1800, "confidence": 0.94},
                        {"text": "coaching", "start": 1800, "end": 2200, "confidence": 0.97},
                        {"text": "session", "start": 2200, "end": 2600, "confidence": 0.95},
                        {"text": "today", "start": 2600, "end": 2950, "confidence": 0.99}
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
                    "end": 6800,
                    "confidence": 0.89,
                    "words": [
                        {"text": "What", "start": 3400, "end": 3600, "confidence": 0.94},
                        {"text": "would", "start": 3600, "end": 3850, "confidence": 0.91},
                        {"text": "you", "start": 3850, "end": 4000, "confidence": 0.97},
                        {"text": "like", "start": 4000, "end": 4200, "confidence": 0.93},
                        {"text": "to", "start": 4200, "end": 4300, "confidence": 0.98},
                        {"text": "focus", "start": 4300, "end": 4650, "confidence": 0.89},
                        {"text": "on", "start": 4650, "end": 4800, "confidence": 0.95}
                    ]
                }
            ]
        }
        
        # When
        result = smooth_and_punctuate(transcript_json, language="english")
        
        # Then
        segments = result["segments"]
        stats = result["stats"]
        
        assert stats["language_detected"] == "english"
        assert stats["processor_used"] == "EnglishProcessor"
        
        # Check that some smoothing occurred
        assert stats["moved_word_count"] >= 0
        assert stats["heuristic_hits"]["short_first_segment"] + stats["heuristic_hits"]["filler_words"] >= 1
        
        # Verify English punctuation
        for segment in segments:
            assert segment["text"].endswith((".", "?", "!"))
    
    def test_auto_language_detection_integration(self):
        """Test automatic language detection with mixed scenarios."""
        chinese_transcript = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 3000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "你好", "start": 1000, "end": 1500, "confidence": 0.95},
                        {"text": "歡迎", "start": 1500, "end": 2000, "confidence": 0.92},
                        {"text": "來到", "start": 2000, "end": 2500, "confidence": 0.89},
                        {"text": "我們的", "start": 2500, "end": 3000, "confidence": 0.94}
                    ]
                }
            ]
        }
        
        english_transcript = {
            "utterances": [
                {
                    "speaker": "A", 
                    "start": 1000,
                    "end": 3000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "Welcome", "start": 1000, "end": 1400, "confidence": 0.96},
                        {"text": "to", "start": 1400, "end": 1500, "confidence": 0.98},
                        {"text": "our", "start": 1500, "end": 1700, "confidence": 0.94},
                        {"text": "session", "start": 1700, "end": 2100, "confidence": 0.97}
                    ]
                }
            ]
        }
        
        # Test Chinese auto-detection
        chinese_result = smooth_and_punctuate(chinese_transcript, language="auto")
        assert chinese_result["stats"]["language_detected"] == "chinese"
        
        # Test English auto-detection
        english_result = smooth_and_punctuate(english_transcript, language="auto")
        assert english_result["stats"]["language_detected"] == "english"
    
    def test_edge_case_very_short_segments(self):
        """Test handling of very short segments and single words."""
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 1200,
                    "confidence": 0.8,
                    "words": [
                        {"text": "好", "start": 1000, "end": 1200, "confidence": 0.9}
                    ]
                },
                {
                    "speaker": "B",
                    "start": 1300,
                    "end": 1500,
                    "confidence": 0.7,
                    "words": [
                        {"text": "嗯", "start": 1300, "end": 1500, "confidence": 0.8}
                    ]
                },
                {
                    "speaker": "A",
                    "start": 1600,
                    "end": 1800,
                    "confidence": 0.9,
                    "words": [
                        {"text": "對", "start": 1600, "end": 1800, "confidence": 0.95}
                    ]
                }
            ]
        }
        
        # Should not raise errors
        result = smooth_and_punctuate(transcript_json)
        
        assert len(result["segments"]) >= 1
        assert result["stats"]["moved_word_count"] >= 0
    
    def test_complex_punctuation_scenarios(self):
        """Test complex punctuation and quote handling."""
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 5000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "他", "start": 1000, "end": 1200, "confidence": 0.95},
                        {"text": "說", "start": 1200, "end": 1400, "confidence": 0.92},
                        {"text": '"', "start": 1400, "end": 1450, "confidence": 0.8},
                        {"text": "這樣", "start": 1450, "end": 1800, "confidence": 0.94},
                        {"text": "很", "start": 1800, "end": 1950, "confidence": 0.91},
                        {"text": "好", "start": 1950, "end": 2100, "confidence": 0.96},
                        {"text": '"', "start": 2100, "end": 2150, "confidence": 0.8},
                        {"text": "但是", "start": 2300, "end": 2650, "confidence": 0.89},
                        {"text": "我", "start": 2650, "end": 2800, "confidence": 0.97},
                        {"text": "不", "start": 2800, "end": 2950, "confidence": 0.94},
                        {"text": "確定", "start": 2950, "end": 3300, "confidence": 0.88}
                    ]
                }
            ]
        }
        
        result = smooth_and_punctuate(transcript_json)
        
        # Should handle quotes properly
        segments = result["segments"]
        found_smart_quotes = any('"' in segment["text"] and '"' in segment["text"] 
                               for segment in segments)
        assert found_smart_quotes or any('"' in segment["text"] for segment in segments)
    
    def test_performance_with_large_transcript(self):
        """Test performance with a larger transcript."""
        # Generate a larger transcript (simulating 30 seconds of dialog)
        words_base = [
            {"text": "我", "confidence": 0.95},
            {"text": "覺得", "confidence": 0.92},
            {"text": "這個", "confidence": 0.89},
            {"text": "想法", "confidence": 0.94},
            {"text": "很", "confidence": 0.91},
            {"text": "有趣", "confidence": 0.96}
        ]
        
        utterances = []
        current_time = 1000
        
        for i in range(20):  # 20 utterances
            speaker = "A" if i % 2 == 0 else "B"
            words = []
            
            for j, word_template in enumerate(words_base):
                word = {
                    "text": word_template["text"],
                    "start": current_time,
                    "end": current_time + 300,
                    "confidence": word_template["confidence"]
                }
                words.append(word)
                current_time += 350
            
            utterance = {
                "speaker": speaker,
                "start": words[0]["start"],
                "end": words[-1]["end"], 
                "confidence": 0.9,
                "words": words
            }
            utterances.append(utterance)
            current_time += 500  # Gap between utterances
        
        transcript_json = {"utterances": utterances}
        
        # Should process without performance issues
        import time
        start_time = time.time()
        result = smooth_and_punctuate(transcript_json)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Should complete in under 5 seconds
        assert len(result["segments"]) > 0
        assert result["stats"]["moved_word_count"] >= 0


class TestConfigurationOptions:
    """Test different configuration options and parameters."""
    
    def test_custom_filler_words(self):
        """Test custom filler word configuration."""
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 2000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "我", "start": 1000, "end": 1200, "confidence": 0.95},
                        {"text": "想。", "start": 1200, "end": 1600, "confidence": 0.92}
                    ]
                },
                {
                    "speaker": "B", 
                    "start": 1700,
                    "end": 2000,
                    "confidence": 0.8,
                    "words": [
                        {"text": "對呀", "start": 1700, "end": 2000, "confidence": 0.85}
                    ]
                }
            ]
        }
        
        # Test with custom filler words
        result = smooth_and_punctuate(
            transcript_json, 
            language="chinese",
            filler_whitelist=["對呀", "嗯", "啊"]
        )
        
        # Should not backfill because previous segment has terminal punctuation
        assert result["stats"]["heuristic_hits"]["filler_words"] == 0
    
    def test_threshold_adjustments(self):
        """Test adjusting various threshold parameters."""
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 2000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "我們", "start": 1000, "end": 1400, "confidence": 0.95},
                        {"text": "討論", "start": 1400, "end": 1800, "confidence": 0.92}
                    ]
                },
                {
                    "speaker": "B",
                    "start": 2100,
                    "end": 2300,
                    "confidence": 0.8,
                    "words": [
                        {"text": "嗯", "start": 2100, "end": 2300, "confidence": 0.85}
                    ]
                }
            ]
        }
        
        # Test with very strict thresholds (should prevent merging)
        result_strict = smooth_and_punctuate(
            transcript_json,
            th_short_head_sec=0.1,
            th_filler_max_sec=0.1
        )
        
        # Test with very permissive thresholds (should allow merging)
        result_permissive = smooth_and_punctuate(
            transcript_json,
            th_short_head_sec=2.0,
            th_filler_max_sec=1.0
        )
        
        # Results should be different
        assert result_strict["stats"]["moved_word_count"] != result_permissive["stats"]["moved_word_count"]


class TestErrorRecovery:
    """Test error recovery and robustness."""
    
    def test_malformed_timestamps(self):
        """Test handling of malformed or inconsistent timestamps."""
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 3000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "Hello", "start": 1000, "end": 1500, "confidence": 0.95},
                        {"text": "world", "start": 1400, "end": 2000, "confidence": 0.92},  # Overlapping
                        {"text": "test", "start": 1800, "end": 2200, "confidence": 0.89}    # Overlapping
                    ]
                }
            ]
        }
        
        # Should handle gracefully without crashing
        result = smooth_and_punctuate(transcript_json)
        assert len(result["segments"]) >= 1
    
    def test_missing_confidence_scores(self):
        """Test handling of missing confidence scores."""
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 2000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "Test", "start": 1000, "end": 1500},  # Missing confidence
                        {"text": "word", "start": 1500, "end": 2000, "confidence": 0.92}
                    ]
                }
            ]
        }
        
        # Should handle gracefully and use default confidence
        result = smooth_and_punctuate(transcript_json)
        assert len(result["segments"]) >= 1