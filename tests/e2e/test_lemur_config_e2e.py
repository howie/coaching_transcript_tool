"""
End-to-End tests for LeMUR configuration system.

Tests complete workflow of configuration loading, prompt retrieval,
and integration with actual LeMUR transcript processing services.
"""

import os
import tempfile
import pytest
from unittest.mock import patch

from coaching_assistant.config.lemur_config import (
    get_lemur_config,
    get_speaker_prompt,
    get_punctuation_prompt,
    get_combined_prompt,
    LeMURConfigLoader,
)


class TestLeMURConfigE2E:
    """End-to-End tests for complete LeMUR configuration workflow."""

    def create_production_like_config(self) -> str:
        """Create a production-like YAML configuration file."""
        yaml_content = """
# Production LeMUR Configuration
model_settings:
  default_model: "claude_sonnet_4_20250514"
  fallback_model: "claude3_5_sonnet"
  max_output_size: 4000
  enable_combined_mode: true

performance:
  batch_processing:
    max_batch_chars: 3000
    max_batch_size: 10
    min_batch_size: 1

  adaptive_sizing:
    large_transcript_threshold: 15000
    medium_transcript_threshold: 8000

  concurrent_processing:
    max_concurrent_batches: 3
    enable_parallel_processing: true

# Comprehensive prompt templates for real-world use
speaker_identification:
  chinese:
    default: |
      請分析以下教練對話轉錄，準確識別說話者的角色。

      分析重點：
      - 教練通常會問開放式問題，引導對話
      - 客戶通常會分享個人經歷和感受
      - 注意語言模式、對話節奏和角色動態

      轉錄內容：
      {transcript}

      請以 JSON 格式回覆：
      {{
        "speaker_assignments": {{
          "Speaker 1": "Coach|Client",
          "Speaker 2": "Coach|Client"
        }},
        "confidence": 0.95,
        "analysis_notes": "簡短分析說明"
      }}

    coaching_session: |
      深度分析教練會談轉錄，識別教練和客戶角色。

      教練特徵：
      - 使用強力問句技巧
      - 提供回饋和總結
      - 引導客戶自我探索

      客戶特徵：
      - 分享個人故事和挑戰
      - 表達情感和困惑
      - 設定目標和行動計畫

      會談轉錄：
      {transcript}
      會談階段：{session_phase}

      分析結果：
      {{
        "primary_coach": "Speaker X",
        "primary_client": "Speaker Y",
        "interaction_quality": "High|Medium|Low",
        "coaching_competencies": ["積極聆聽", "強力問句", "直接溝通"],
        "speaker_assignments": {{...}}
      }}

  english:
    default: |
      Analyze this coaching conversation transcript to identify speaker roles.

      Key indicators:
      - Coaches ask powerful questions and guide conversation
      - Clients share personal experiences and insights
      - Look for coaching competencies and conversation dynamics

      Transcript:
      {transcript}

      Response in JSON format:
      {{
        "speaker_assignments": {{
          "Speaker 1": "Coach|Client",
          "Speaker 2": "Coach|Client"
        }},
        "confidence": 0.95,
        "coaching_competencies_observed": ["Active Listening", "Powerful Questions"]
      }}

punctuation_optimization:
  chinese:
    default: |
      優化教練對話轉錄的標點符號，提升可讀性和專業度。

      優化原則：
      - 保持教練對話的自然流暢感
      - 正確使用中文標點符號
      - 移除多餘的口語填充詞
      - 保留重要的語氣和情感表達

      原始轉錄：
      {transcript}

      優化後的轉錄：

    professional: |
      專業級教練對話標點符號和語法優化。

      優化目標：
      1. 標準化專業教練語言表達
      2. 提升對話記錄的專業品質
      3. 保持原始對話的真實性和完整性
      4. 優化段落結構和對話流程

      原始轉錄：
      {transcript}
      對話類型：{conversation_type}
      教練風格：{coaching_style}

      專業優化結果：

combined_processing:
  chinese:
    coaching_analysis: |
      綜合分析教練會談：同步進行說話者識別和轉錄優化。

      處理步驟：
      1. 識別教練和客戶角色
      2. 評估教練能力展現
      3. 優化對話記錄品質
      4. 生成會談分析報告

      原始轉錄：
      {transcript}
      會談資訊：
      - 會談時長：{duration}
      - 會談階段：{phase}
      - 主要議題：{topics}

      綜合分析結果：
      {{
        "speaker_identification": {{
          "coach": "Speaker X",
          "client": "Speaker Y",
          "confidence": 0.95
        }},
        "optimized_transcript": "優化後的完整轉錄...",
        "coaching_analysis": {{
          "competencies_demonstrated": ["核心能力列表"],
          "conversation_quality": "評分和說明",
          "key_insights": ["主要洞察"],
          "action_items": ["行動項目"],
          "session_effectiveness": "會談效果評估"
        }},
        "recommendations": {{
          "for_coach": ["給教練的建議"],
          "for_client": ["給客戶的建議"],
          "follow_up": ["後續追蹤建議"]
        }}
      }}

# Error handling and fallback prompts
fallback_prompts:
  speaker_identification_error: |
    Unable to load specific speaker identification prompt.
    Using fallback: Identify the speakers in this transcript: {transcript}

  punctuation_error: |
    Unable to load punctuation optimization prompt.
    Using fallback: Improve the punctuation of this transcript: {transcript}

  combined_processing_error: |
    Unable to load combined processing prompt.
    Please process this transcript for both speaker identification and punctuation: {transcript}

# Configuration metadata
metadata:
  version: "1.0.0"
  created_date: "2024-01-15"
  last_updated: "2024-01-15"
  supported_languages: ["chinese", "english"]
  prompt_variants: ["default", "coaching_session", "professional", "coaching_analysis"]
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            return f.name

    @pytest.fixture
    def production_config(self):
        """Fixture providing production-like configuration."""
        config_file = self.create_production_like_config()
        yield config_file
        os.unlink(config_file)

    def test_complete_coaching_session_workflow(self, production_config):
        """Test complete E2E workflow for coaching session analysis."""
        # Initialize with production config
        loader = LeMURConfigLoader(production_config)

        # Simulate realistic coaching transcript
        sample_transcript = """
        教練: 你好，今天想聊什麼呢？
        客戶: 我最近工作壓力很大，不知道該怎麼辦。
        教練: 能跟我說說是什麼樣的壓力嗎？
        客戶: 就是工作量增加了，但是時間還是一樣，我覺得快撐不住了。
        教練: 聽起來你感到很累。那你覺得什麼樣的改變會對你有幫助？
        """

        # Test speaker identification workflow
        speaker_context = {
            "transcript": sample_transcript,
            "session_phase": "exploration"
        }

        speaker_prompt = loader.get_prompt_with_context(
            "speaker", "chinese", "coaching_session", speaker_context
        )

        # Verify prompt contains expected coaching analysis elements
        assert "教練特徵" in speaker_prompt
        assert "客戶特徵" in speaker_prompt
        assert "會談階段：exploration" in speaker_prompt
        assert sample_transcript in speaker_prompt

        # Test punctuation optimization workflow
        punctuation_context = {
            "transcript": sample_transcript,
            "conversation_type": "coaching",
            "coaching_style": "solution_focused"
        }

        punctuation_prompt = loader.get_prompt_with_context(
            "punctuation", "chinese", "professional", punctuation_context
        )

        assert "專業級教練對話標點符號" in punctuation_prompt
        assert "對話類型：coaching" in punctuation_prompt
        assert "教練風格：solution_focused" in punctuation_prompt

        # Test combined processing workflow
        combined_context = {
            "transcript": sample_transcript,
            "duration": "45 minutes",
            "phase": "goal_setting",
            "topics": "work_stress, time_management"
        }

        combined_prompt = loader.get_prompt_with_context(
            "combined", "chinese", "coaching_analysis", combined_context
        )

        assert "綜合分析教練會談" in combined_prompt
        assert "會談時長：45 minutes" in combined_prompt
        assert "會談階段：goal_setting" in combined_prompt
        assert "主要議題：work_stress, time_management" in combined_prompt

    def test_multilingual_coaching_support(self, production_config):
        """Test E2E workflow supporting multiple languages."""
        loader = LeMURConfigLoader(production_config)

        # Test Chinese coaching session
        chinese_transcript = "教練: 你今天感覺如何？ 客戶: 我感到很困惑。"

        chinese_prompt = loader.get_prompt_with_context(
            "speaker", "chinese", "default", {"transcript": chinese_transcript}
        )

        assert "請分析以下教練對話轉錄" in chinese_prompt
        assert chinese_transcript in chinese_prompt

        # Test English coaching session
        english_transcript = "Coach: How are you feeling today? Client: I feel confused."

        english_prompt = loader.get_prompt_with_context(
            "speaker", "english", "default", {"transcript": english_transcript}
        )

        assert "Analyze this coaching conversation" in english_prompt
        assert english_transcript in english_prompt

    def test_error_handling_and_fallbacks(self, production_config):
        """Test E2E error handling and fallback mechanisms."""
        loader = LeMURConfigLoader(production_config)
        config = loader.load_config()

        # Test accessing non-existent prompt type
        invalid_prompt = loader.get_prompt_with_context(
            "invalid_type", "chinese", "default", {"transcript": "test"}
        )
        assert invalid_prompt is None

        # Test accessing non-existent language
        missing_language = config.prompts.get_speaker_prompt("japanese", "default")
        assert missing_language is None

        # Test accessing non-existent variant
        missing_variant = config.prompts.get_speaker_prompt("chinese", "nonexistent")
        assert missing_variant is None

        # Test fallback prompts exist
        assert "speaker_identification_error" in config.prompts.fallback_prompts
        assert "punctuation_error" in config.prompts.fallback_prompts
        assert "combined_processing_error" in config.prompts.fallback_prompts

    def test_performance_configuration_integration(self, production_config):
        """Test E2E integration of performance settings with processing logic."""
        loader = LeMURConfigLoader(production_config)
        config = loader.load_config()

        # Verify performance settings are loaded correctly
        assert config.performance_settings.max_batch_chars == 3000
        assert config.performance_settings.max_batch_size == 10
        assert config.performance_settings.large_transcript_threshold == 15000
        assert config.performance_settings.max_concurrent_batches == 3
        assert config.performance_settings.enable_parallel_processing is True

        # Test adaptive sizing thresholds
        short_transcript = "A" * 1000  # 1K chars - below medium threshold
        medium_transcript = "B" * 10000  # 10K chars - above medium, below large
        large_transcript = "C" * 20000  # 20K chars - above large threshold

        # Verify thresholds work as expected
        assert len(short_transcript) < config.performance_settings.medium_transcript_threshold
        assert (config.performance_settings.medium_transcript_threshold <
                len(medium_transcript) < config.performance_settings.large_transcript_threshold)
        assert len(large_transcript) > config.performance_settings.large_transcript_threshold

    def test_global_configuration_e2e(self, production_config):
        """Test E2E workflow using global configuration functions."""
        # Reset global state
        import coaching_assistant.config.lemur_config
        coaching_assistant.config.lemur_config._config_loader = LeMURConfigLoader(production_config)

        # Test global configuration access
        config = get_lemur_config()
        assert config.default_model == "claude_sonnet_4_20250514"
        assert config.combined_mode_enabled is True

        # Test convenience functions with realistic coaching data
        coaching_transcript = """
        教練: 今天我們來談談你的職涯目標。你最希望在工作上達成什麼？
        客戶: 我想要升職，但是不知道該怎麼做。我覺得自己能力不夠。
        教練: 能力不夠，這個想法是什麼時候開始的？
        """

        context = {"transcript": coaching_transcript}

        # Test speaker identification
        speaker_prompt = get_speaker_prompt("chinese", "default", context)
        assert coaching_transcript in speaker_prompt
        assert "請分析以下教練對話轉錄" in speaker_prompt

        # Test punctuation optimization
        punctuation_prompt = get_punctuation_prompt("chinese", "default", context)
        assert coaching_transcript in punctuation_prompt
        assert "優化教練對話轉錄的標點符號" in punctuation_prompt

        # Test combined processing
        extended_context = {
            **context,
            "duration": "60 minutes",
            "phase": "action_planning",
            "topics": "career_development, self_confidence"
        }

        combined_prompt = get_combined_prompt("chinese", "coaching_analysis", extended_context)
        assert coaching_transcript in combined_prompt
        assert "會談時長：60 minutes" in combined_prompt

    def test_environment_override_e2e(self, production_config):
        """Test E2E workflow with environment variable overrides."""
        # Test production config with environment overrides
        with patch('coaching_assistant.config.lemur_config.settings') as mock_settings:
            mock_settings.LEMUR_MODEL = "production_claude_4"
            mock_settings.LEMUR_MAX_OUTPUT_SIZE = "6000"
            mock_settings.LEMUR_COMBINED_MODE = False

            loader = LeMURConfigLoader(production_config)
            config = loader.load_config()

            # Environment should override YAML values
            assert config.default_model == "production_claude_4"
            assert config.max_output_size == 6000
            assert config.combined_mode_enabled is False

            # Non-overridden values should come from YAML
            assert config.fallback_model == "claude3_5_sonnet"
            assert config.performance_settings.max_batch_chars == 3000

    def test_prompt_template_completeness_e2e(self, production_config):
        """Test that all required prompt templates are available for production use."""
        loader = LeMURConfigLoader(production_config)
        config = loader.load_config()

        # Required Chinese prompts
        required_chinese_prompts = [
            ("speaker", "chinese", "default"),
            ("speaker", "chinese", "coaching_session"),
            ("punctuation", "chinese", "default"),
            ("punctuation", "chinese", "professional"),
            ("combined", "chinese", "coaching_analysis"),
        ]

        for prompt_type, language, variant in required_chinese_prompts:
            if prompt_type == "speaker":
                prompt = config.prompts.get_speaker_prompt(language, variant)
            elif prompt_type == "punctuation":
                prompt = config.prompts.get_punctuation_prompt(language, variant)
            elif prompt_type == "combined":
                prompt = config.prompts.get_combined_prompt(language, variant)

            assert prompt is not None, f"Missing {prompt_type}/{language}/{variant} prompt"
            assert len(prompt.strip()) > 100, f"Prompt too short: {prompt_type}/{language}/{variant}"

        # Required English prompts
        english_speaker_prompt = config.prompts.get_speaker_prompt("english", "default")
        assert english_speaker_prompt is not None
        assert "coaching conversation" in english_speaker_prompt.lower()

        # Fallback prompts should exist
        assert len(config.prompts.fallback_prompts) >= 3
        for fallback_key in ["speaker_identification_error", "punctuation_error", "combined_processing_error"]:
            assert fallback_key in config.prompts.fallback_prompts

    def test_configuration_validation_e2e(self, production_config):
        """Test E2E validation of configuration integrity and consistency."""
        loader = LeMURConfigLoader(production_config)
        config = loader.load_config()

        # Model configuration validation
        assert config.default_model in ["claude_sonnet_4_20250514", "claude3_5_sonnet"]
        assert config.fallback_model in ["claude3_5_sonnet", "claude_sonnet_4_20250514"]
        assert 1000 <= config.max_output_size <= 10000
        assert isinstance(config.combined_mode_enabled, bool)

        # Performance settings validation
        perf = config.performance_settings
        assert 1000 <= perf.max_batch_chars <= 10000
        assert 1 <= perf.min_batch_size <= perf.max_batch_size <= 50
        assert perf.medium_transcript_threshold < perf.large_transcript_threshold
        assert 1 <= perf.max_concurrent_batches <= 10

        # Prompt structure validation
        for language in ["chinese", "english"]:
            # At least one speaker prompt per language
            speaker_prompts = config.prompts.speaker_identification.get(language, {})
            assert len(speaker_prompts) >= 1, f"No speaker prompts for {language}"

            # Check if default variants exist for main languages
            if language == "chinese":
                assert "default" in speaker_prompts

        # Fallback prompts should contain template variables
        for fallback_prompt in config.prompts.fallback_prompts.values():
            assert "{transcript}" in fallback_prompt, "Fallback prompt missing {transcript} variable"
