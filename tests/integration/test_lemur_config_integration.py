"""
Integration tests for LeMUR configuration management.

Tests real YAML file loading, environment variable integration,
and configuration system integration with the application.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from coaching_assistant.config.lemur_config import (
    LeMURConfigLoader,
    get_lemur_config,
    reload_lemur_config,
    get_speaker_prompt,
    get_punctuation_prompt,
    get_combined_prompt,
)


class TestLeMURConfigIntegration:
    """Integration tests for complete LeMUR configuration system."""

    def create_test_yaml_config(self) -> str:
        """Create a comprehensive test YAML configuration file."""
        yaml_content = """
# Model Configuration
model_settings:
  default_model: "claude_sonnet_4_20250514"
  fallback_model: "claude3_5_sonnet"
  max_output_size: 4000
  enable_combined_mode: true

# Performance Settings
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

# Speaker Identification Prompts
speaker_identification:
  chinese:
    default: |
      請分析以下對話轉錄，識別說話者的角色。
      根據內容和語調判斷誰是教練(Coach)、誰是客戶(Client)。

      轉錄內容：{transcript}

      請回覆 JSON 格式：
      {
        "speaker_assignments": {
          "Speaker 1": "Coach|Client",
          "Speaker 2": "Coach|Client"
        }
      }

    enhanced: |
      深度分析對話轉錄中的說話者角色識別。

      分析要點：
      1. 語言模式：教練通常使用開放式問題
      2. 對話主導：教練引導對話方向
      3. 語調特徵：客戶分享個人經歷

      轉錄內容：{transcript}
      說話者數量：{speaker_count}

      回覆格式：
      {
        "analysis": "分析說明",
        "confidence": 0.95,
        "speaker_assignments": {...}
      }

  english:
    default: |
      Analyze the following transcript to identify speaker roles.
      Determine who is the Coach and who is the Client based on conversation patterns.

      Transcript: {transcript}

      Response format:
      {
        "speaker_assignments": {
          "Speaker 1": "Coach|Client",
          "Speaker 2": "Coach|Client"
        }
      }

# Punctuation Optimization Prompts
punctuation_optimization:
  chinese:
    default: |
      優化以下中文轉錄的標點符號，使其更易閱讀。

      規則：
      - 使用適當的句號、逗號、問號
      - 保持原文意思不變
      - 移除不必要的填充詞

      原始轉錄：{transcript}

      請直接回覆優化後的文字，不需要額外說明。

    enhanced: |
      深度優化中文轉錄的標點符號和語法結構。

      優化目標：
      1. 標準化標點符號使用
      2. 改善句子流暢度
      3. 保持原意和語調
      4. 移除口語填充詞（嗯、那個、就是）

      原始轉錄：{transcript}
      語境：{context}

      優化後文字：

  english:
    default: |
      Improve punctuation and readability of the following transcript.

      Guidelines:
      - Add appropriate periods, commas, question marks
      - Maintain original meaning
      - Remove unnecessary filler words

      Original transcript: {transcript}

      Please provide only the improved text without additional explanation.

# Combined Processing Prompts
combined_processing:
  chinese:
    default: |
      同時進行說話者識別和標點符號優化。

      步驟：
      1. 識別說話者角色（教練/客戶）
      2. 優化標點符號和語法
      3. 格式化最終轉錄

      原始轉錄：{transcript}

      回覆格式：
      {
        "speaker_assignments": {...},
        "optimized_transcript": "優化後的完整轉錄",
        "processing_notes": "處理說明"
      }

# Fallback Prompts
fallback_prompts:
  generic_speaker: "Identify speakers in this transcript: {transcript}"
  generic_punctuation: "Improve punctuation: {transcript}"

# Template Variables
templates:
  common_context:
    coach_indicators: ["問問題", "引導", "總結", "建議"]
    client_indicators: ["分享", "回答", "困惑", "目標"]
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            return f.name

    def test_full_yaml_loading(self):
        """Should load complete YAML configuration with all sections."""
        config_file = self.create_test_yaml_config()

        try:
            loader = LeMURConfigLoader(config_file)
            config = loader.load_config()

            # Test model settings
            assert config.default_model == "claude_sonnet_4_20250514"
            assert config.fallback_model == "claude3_5_sonnet"
            assert config.max_output_size == 4000
            assert config.combined_mode_enabled is True

            # Test performance settings
            assert config.performance_settings.max_batch_chars == 3000
            assert config.performance_settings.large_transcript_threshold == 15000
            assert config.performance_settings.max_concurrent_batches == 3

            # Test prompts
            speaker_prompt = config.prompts.get_speaker_prompt("chinese", "default")
            assert "請分析以下對話轉錄" in speaker_prompt

            punctuation_prompt = config.prompts.get_punctuation_prompt("chinese", "enhanced")
            assert "深度優化中文轉錄" in punctuation_prompt

            combined_prompt = config.prompts.get_combined_prompt("chinese", "default")
            assert "同時進行說話者識別和標點符號優化" in combined_prompt

        finally:
            os.unlink(config_file)

    def test_environment_variable_overrides(self):
        """Should apply environment variable overrides to loaded configuration."""
        config_file = self.create_test_yaml_config()

        try:
            # Mock environment settings
            with patch('coaching_assistant.config.lemur_config.settings') as mock_settings:
                mock_settings.LEMUR_MODEL = "env_override_model"
                mock_settings.LEMUR_MAX_OUTPUT_SIZE = "8000"
                mock_settings.LEMUR_COMBINED_MODE = False

                loader = LeMURConfigLoader(config_file)
                config = loader.load_config()

                # Should use environment overrides
                assert config.default_model == "env_override_model"
                assert config.max_output_size == 8000
                assert config.combined_mode_enabled is False

                # Other settings should remain from YAML
                assert config.fallback_model == "claude3_5_sonnet"
                assert config.performance_settings.max_batch_chars == 3000

        finally:
            os.unlink(config_file)

    def test_template_context_substitution(self):
        """Should properly substitute context variables in prompt templates."""
        config_file = self.create_test_yaml_config()

        try:
            loader = LeMURConfigLoader(config_file)
            context = {
                "transcript": "測試轉錄內容",
                "speaker_count": 2
            }

            prompt = loader.get_prompt_with_context(
                "speaker", "chinese", "enhanced", context
            )

            assert "測試轉錄內容" in prompt
            assert "說話者數量：2" in prompt
            assert "{transcript}" not in prompt  # Should be substituted
            assert "{speaker_count}" not in prompt  # Should be substituted

        finally:
            os.unlink(config_file)

    def test_multilingual_prompt_support(self):
        """Should support prompts in multiple languages."""
        config_file = self.create_test_yaml_config()

        try:
            loader = LeMURConfigLoader(config_file)
            config = loader.load_config()

            # Test Chinese prompts
            chinese_speaker = config.prompts.get_speaker_prompt("chinese", "default")
            assert "請分析以下對話轉錄" in chinese_speaker

            chinese_punctuation = config.prompts.get_punctuation_prompt("chinese", "default")
            assert "優化以下中文轉錄的標點符號" in chinese_punctuation

            # Test English prompts
            english_speaker = config.prompts.get_speaker_prompt("english", "default")
            assert "Analyze the following transcript" in english_speaker

            english_punctuation = config.prompts.get_punctuation_prompt("english", "default")
            assert "Improve punctuation and readability" in english_punctuation

        finally:
            os.unlink(config_file)

    def test_prompt_variant_selection(self):
        """Should correctly select different prompt variants."""
        config_file = self.create_test_yaml_config()

        try:
            loader = LeMURConfigLoader(config_file)
            config = loader.load_config()

            # Test default variant
            default_prompt = config.prompts.get_speaker_prompt("chinese", "default")
            assert "請分析以下對話轉錄，識別說話者的角色" in default_prompt

            # Test enhanced variant
            enhanced_prompt = config.prompts.get_speaker_prompt("chinese", "enhanced")
            assert "深度分析對話轉錄中的說話者角色識別" in enhanced_prompt

            # Variants should be different
            assert default_prompt != enhanced_prompt

        finally:
            os.unlink(config_file)

    def test_global_config_persistence(self):
        """Should maintain global configuration state across calls."""
        config_file = self.create_test_yaml_config()

        try:
            # Reset global state
            import coaching_assistant.config.lemur_config
            coaching_assistant.config.lemur_config._config_loader = None

            # Patch the default config path to use our test file
            with patch.object(LeMURConfigLoader, '__init__') as mock_init:
                def init_with_test_path(self, config_path=None):
                    if config_path is None:
                        config_path = config_file
                    self.config_path = Path(config_path)
                    self._config = None

                mock_init.side_effect = init_with_test_path

                # First call should load config
                config1 = get_lemur_config()
                assert config1.default_model == "claude_sonnet_4_20250514"

                # Second call should return cached config
                config2 = get_lemur_config()
                assert config1 is config2  # Same object reference

                # Force reload should create new config
                config3 = reload_lemur_config()
                assert config3.default_model == "claude_sonnet_4_20250514"

        finally:
            os.unlink(config_file)

    def test_convenience_functions_integration(self):
        """Should test convenience functions with real configuration."""
        config_file = self.create_test_yaml_config()

        try:
            # Reset global state and use test config
            import coaching_assistant.config.lemur_config
            coaching_assistant.config.lemur_config._config_loader = LeMURConfigLoader(config_file)

            # Test speaker prompt function
            speaker_prompt = get_speaker_prompt("chinese", "default")
            assert "請分析以下對話轉錄" in speaker_prompt

            # Test punctuation prompt function
            punctuation_prompt = get_punctuation_prompt("chinese", "enhanced")
            assert "深度優化中文轉錄" in punctuation_prompt

            # Test combined prompt function
            combined_prompt = get_combined_prompt("chinese", "default")
            assert "同時進行說話者識別和標點符號優化" in combined_prompt

            # Test with context
            context = {"transcript": "測試內容"}
            prompt_with_context = get_speaker_prompt("chinese", "default", context)
            assert "測試內容" in prompt_with_context

        finally:
            os.unlink(config_file)

    def test_missing_config_file_handling(self):
        """Should handle missing configuration file gracefully."""
        # Reset global state
        import coaching_assistant.config.lemur_config
        coaching_assistant.config.lemur_config._config_loader = None

        nonexistent_path = "/nonexistent/config.yaml"

        with patch.object(LeMURConfigLoader, '__init__') as mock_init:
            def init_with_missing_path(self, config_path=None):
                if config_path is None:
                    config_path = nonexistent_path
                self.config_path = Path(config_path)
                self._config = None

            mock_init.side_effect = init_with_missing_path

            # Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                get_lemur_config()

    def test_partial_yaml_configuration(self):
        """Should handle partial YAML configuration with defaults."""
        # Create minimal YAML with only some sections
        minimal_yaml = """
model_settings:
  default_model: "custom_model"

speaker_identification:
  chinese:
    default: "Minimal speaker prompt"
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(minimal_yaml)
            config_file = f.name

        try:
            loader = LeMURConfigLoader(config_file)
            config = loader.load_config()

            # Should use custom value from YAML
            assert config.default_model == "custom_model"

            # Should use defaults for missing values
            assert config.fallback_model == "claude3_5_sonnet"  # Default
            assert config.max_output_size == 4000  # Default
            assert config.performance_settings.max_batch_chars == 3000  # Default

            # Should load specified prompts
            speaker_prompt = config.prompts.get_speaker_prompt("chinese", "default")
            assert speaker_prompt == "Minimal speaker prompt"

            # Missing prompts should return None
            punctuation_prompt = config.prompts.get_punctuation_prompt("chinese", "default")
            assert punctuation_prompt is None

        finally:
            os.unlink(config_file)
