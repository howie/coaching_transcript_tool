"""
Unit tests for LeMUR configuration management.

Tests all classes and methods in coaching_assistant.config.lemur_config module.
Following TDD methodology: Red → Green → Refactor
"""

import os
import tempfile
import pytest
from unittest.mock import patch
import yaml

from coaching_assistant.config.lemur_config import (
    ModelSettings,
    PerformanceSettings,
    LeMURPrompts,
    LeMURConfig,
    LeMURConfigLoader,
    get_lemur_config,
    reload_lemur_config,
    get_prompt_template,
    get_speaker_prompt,
    get_punctuation_prompt,
    get_combined_prompt,
)


class TestModelSettings:
    """Test ModelSettings dataclass."""

    def test_default_values(self):
        """Should create ModelSettings with correct default values."""
        settings = ModelSettings()

        assert settings.default_model == "claude_sonnet_4_20250514"
        assert settings.fallback_model == "claude3_5_sonnet"
        assert settings.max_output_size == 4000
        assert settings.enable_combined_mode is True

    def test_custom_values(self):
        """Should create ModelSettings with custom values."""
        settings = ModelSettings(
            default_model="custom_model",
            fallback_model="custom_fallback",
            max_output_size=8000,
            enable_combined_mode=False,
        )

        assert settings.default_model == "custom_model"
        assert settings.fallback_model == "custom_fallback"
        assert settings.max_output_size == 8000
        assert settings.enable_combined_mode is False


class TestPerformanceSettings:
    """Test PerformanceSettings dataclass."""

    def test_default_values(self):
        """Should create PerformanceSettings with correct default values."""
        settings = PerformanceSettings()

        assert settings.max_batch_chars == 3000
        assert settings.max_batch_size == 10
        assert settings.min_batch_size == 1
        assert settings.large_transcript_threshold == 15000
        assert settings.medium_transcript_threshold == 8000
        assert settings.max_concurrent_batches == 3
        assert settings.enable_parallel_processing is True

    def test_custom_values(self):
        """Should create PerformanceSettings with custom values."""
        settings = PerformanceSettings(
            max_batch_chars=5000,
            max_batch_size=20,
            min_batch_size=2,
            large_transcript_threshold=20000,
            medium_transcript_threshold=10000,
            max_concurrent_batches=5,
            enable_parallel_processing=False,
        )

        assert settings.max_batch_chars == 5000
        assert settings.max_batch_size == 20
        assert settings.min_batch_size == 2
        assert settings.large_transcript_threshold == 20000
        assert settings.medium_transcript_threshold == 10000
        assert settings.max_concurrent_batches == 5
        assert settings.enable_parallel_processing is False


class TestLeMURPrompts:
    """Test LeMURPrompts dataclass."""

    def test_default_initialization(self):
        """Should create LeMURPrompts with empty dictionaries."""
        prompts = LeMURPrompts()

        assert prompts.speaker_identification == {}
        assert prompts.punctuation_optimization == {}
        assert prompts.combined_processing == {}
        assert prompts.fallback_prompts == {}
        assert prompts.templates == {}

    def test_get_speaker_prompt_existing(self):
        """Should return speaker prompt when it exists."""
        prompts = LeMURPrompts(
            speaker_identification={"chinese": {"default": "Speaker prompt"}}
        )

        result = prompts.get_speaker_prompt("chinese", "default")
        assert result == "Speaker prompt"

    def test_get_speaker_prompt_missing_language(self):
        """Should return None when language doesn't exist."""
        prompts = LeMURPrompts()

        result = prompts.get_speaker_prompt("chinese", "default")
        assert result is None

    def test_get_speaker_prompt_missing_variant(self):
        """Should return None when variant doesn't exist."""
        prompts = LeMURPrompts(
            speaker_identification={"chinese": {"other": "Other prompt"}}
        )

        result = prompts.get_speaker_prompt("chinese", "default")
        assert result is None

    def test_get_punctuation_prompt_existing(self):
        """Should return punctuation prompt when it exists."""
        prompts = LeMURPrompts(
            punctuation_optimization={
                "english": {"enhanced": "Punctuation prompt"}
            }
        )

        result = prompts.get_punctuation_prompt("english", "enhanced")
        assert result == "Punctuation prompt"

    def test_get_combined_prompt_existing(self):
        """Should return combined prompt when it exists."""
        prompts = LeMURPrompts(
            combined_processing={"chinese": {"optimized": "Combined prompt"}}
        )

        result = prompts.get_combined_prompt("chinese", "optimized")
        assert result == "Combined prompt"


class TestLeMURConfig:
    """Test LeMURConfig dataclass and properties."""

    def test_default_initialization(self):
        """Should create LeMURConfig with default components."""
        config = LeMURConfig()

        assert isinstance(config.model_settings, ModelSettings)
        assert isinstance(config.performance_settings, PerformanceSettings)
        assert isinstance(config.prompts, LeMURPrompts)

    def test_default_model_property(self):
        """Should return default model from model_settings."""
        config = LeMURConfig()
        config.model_settings.default_model = "test_model"

        assert config.default_model == "test_model"

    def test_fallback_model_property(self):
        """Should return fallback model from model_settings."""
        config = LeMURConfig()
        config.model_settings.fallback_model = "test_fallback"

        assert config.fallback_model == "test_fallback"

    def test_max_output_size_property(self):
        """Should return max output size from model_settings."""
        config = LeMURConfig()
        config.model_settings.max_output_size = 5000

        assert config.max_output_size == 5000

    def test_combined_mode_enabled_property(self):
        """Should return combined mode status from model_settings."""
        config = LeMURConfig()
        config.model_settings.enable_combined_mode = False

        assert config.combined_mode_enabled is False


class TestLeMURConfigLoader:
    """Test LeMURConfigLoader class."""

    def test_initialization_default_path(self):
        """Should initialize with default config path."""
        loader = LeMURConfigLoader()

        # Just check the filename since absolute paths may vary
        assert loader.config_path.name == "lemur_prompts.yaml"

    def test_initialization_custom_path(self):
        """Should initialize with custom config path."""
        custom_path = "/custom/path/config.yaml"
        loader = LeMURConfigLoader(custom_path)

        assert str(loader.config_path) == custom_path

    def test_load_config_file_not_found(self):
        """Should raise FileNotFoundError when config file doesn't exist."""
        loader = LeMURConfigLoader("/nonexistent/path.yaml")

        with pytest.raises(
            FileNotFoundError, match="Configuration file not found"
        ):
            loader.load_config()

    def test_load_config_invalid_yaml(self):
        """Should raise yaml.YAMLError when YAML is invalid."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            loader = LeMURConfigLoader(temp_path)
            with pytest.raises(yaml.YAMLError):
                loader.load_config()
        finally:
            os.unlink(temp_path)

    @patch("coaching_assistant.config.lemur_config.settings")
    def test_load_config_minimal_yaml(self, mock_settings):
        """Should load minimal YAML configuration successfully."""
        # Mock settings to not override YAML values
        mock_settings.LEMUR_MODEL = None
        mock_settings.LEMUR_MAX_OUTPUT_SIZE = None
        mock_settings.LEMUR_COMBINED_MODE = None

        yaml_content = """
model_settings:
  default_model: "test_model"

performance:
  batch_processing:
    max_batch_chars: 2000

speaker_identification:
  chinese:
    default: "Test speaker prompt"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = LeMURConfigLoader(temp_path)
            config = loader.load_config()

            assert config.default_model == "test_model"
            assert config.performance_settings.max_batch_chars == 2000
            assert (
                config.prompts.get_speaker_prompt("chinese", "default")
                == "Test speaker prompt"
            )
        finally:
            os.unlink(temp_path)

    @patch("coaching_assistant.config.lemur_config.settings")
    def test_load_config_caching(self, mock_settings):
        """Should cache loaded configuration and not reload unless forced."""
        # Mock settings to not override YAML values
        mock_settings.LEMUR_MODEL = None
        mock_settings.LEMUR_MAX_OUTPUT_SIZE = None
        mock_settings.LEMUR_COMBINED_MODE = None

        yaml_content = """
model_settings:
  default_model: "cached_model"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = LeMURConfigLoader(temp_path)

            # First load
            config1 = loader.load_config()
            assert config1.default_model == "cached_model"

            # Modify the file
            with open(temp_path, "w") as f:
                f.write(
                    """
model_settings:
  default_model: "modified_model"
"""
                )

            # Second load without force_reload should return cached version
            config2 = loader.load_config()
            assert config2.default_model == "cached_model"

            # Force reload should load new version
            config3 = loader.load_config(force_reload=True)
            assert config3.default_model == "modified_model"

        finally:
            os.unlink(temp_path)

    @patch("coaching_assistant.config.lemur_config.settings")
    def test_apply_env_overrides(self, mock_settings):
        """Should apply environment variable overrides to model settings."""
        mock_settings.LEMUR_MODEL = "env_model"
        mock_settings.LEMUR_MAX_OUTPUT_SIZE = "6000"
        mock_settings.LEMUR_COMBINED_MODE = True

        loader = LeMURConfigLoader()
        original_settings = ModelSettings(
            default_model="original_model",
            max_output_size=4000,
            enable_combined_mode=False,
        )

        result = loader._apply_env_overrides(original_settings)

        assert result.default_model == "env_model"
        assert result.max_output_size == 6000
        assert result.enable_combined_mode is True

    def test_get_prompt_with_context_speaker_type(self):
        """Should return formatted speaker prompt with context."""
        yaml_content = """
speaker_identification:
  chinese:
    default: "Hello {name}, analyze {role}"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = LeMURConfigLoader(temp_path)
            context = {"name": "Coach", "role": "speaker"}

            result = loader.get_prompt_with_context(
                "speaker", "chinese", "default", context
            )
            assert result == "Hello Coach, analyze speaker"
        finally:
            os.unlink(temp_path)

    def test_get_prompt_with_context_missing_context_var(self):
        """Should return original prompt when context variable is missing."""
        yaml_content = """
speaker_identification:
  chinese:
    default: "Hello {name}, analyze {role}"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = LeMURConfigLoader(temp_path)
            context = {"name": "Coach"}  # Missing 'role' variable

            result = loader.get_prompt_with_context(
                "speaker", "chinese", "default", context
            )
            assert (
                result == "Hello {name}, analyze {role}"
            )  # Original template returned
        finally:
            os.unlink(temp_path)

    def test_get_prompt_with_context_invalid_type(self):
        """Should return None for invalid prompt type."""
        yaml_content = """
speaker_identification:
  chinese:
    default: "Test prompt"
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            loader = LeMURConfigLoader(temp_path)

            result = loader.get_prompt_with_context(
                "invalid_type", "chinese", "default"
            )
            assert result is None
        finally:
            os.unlink(temp_path)


class TestGlobalFunctions:
    """Test global convenience functions."""

    @patch("coaching_assistant.config.lemur_config._config_loader", None)
    def test_get_lemur_config_creates_loader(self):
        """Should create global loader instance on first call."""
        # Reset global state
        import coaching_assistant.config.lemur_config

        coaching_assistant.config.lemur_config._config_loader = None

        with patch.object(
            coaching_assistant.config.lemur_config.LeMURConfigLoader,
            "load_config",
        ) as mock_load:
            mock_config = LeMURConfig()
            mock_load.return_value = mock_config

            result = get_lemur_config()

            assert result is mock_config
            mock_load.assert_called_once()

    @patch("coaching_assistant.config.lemur_config._config_loader", None)
    def test_reload_lemur_config_forces_reload(self):
        """Should force reload configuration."""
        # Reset global state
        import coaching_assistant.config.lemur_config

        coaching_assistant.config.lemur_config._config_loader = None

        with patch.object(
            coaching_assistant.config.lemur_config.LeMURConfigLoader,
            "load_config",
        ) as mock_load:
            mock_config = LeMURConfig()
            mock_load.return_value = mock_config

            result = reload_lemur_config()

            assert result is mock_config
            mock_load.assert_called_once_with(force_reload=True)

    @patch("coaching_assistant.config.lemur_config._config_loader", None)
    def test_get_prompt_template_calls_loader(self):
        """Should call loader's get_prompt_with_context method."""
        # Reset global state
        import coaching_assistant.config.lemur_config

        coaching_assistant.config.lemur_config._config_loader = None

        mock_loader = (
            coaching_assistant.config.lemur_config.LeMURConfigLoader()
        )
        with patch(
            "coaching_assistant.config.lemur_config.LeMURConfigLoader"
        ) as MockLoader:
            MockLoader.return_value = mock_loader
            with patch.object(
                mock_loader, "get_prompt_with_context"
            ) as mock_get_prompt:
                mock_get_prompt.return_value = "Test prompt"

                result = get_prompt_template(
                    "speaker", "chinese", "default", {"key": "value"}
                )

                assert result == "Test prompt"
                mock_get_prompt.assert_called_once_with(
                    prompt_type="speaker",
                    language="chinese",
                    variant="default",
                    context={"key": "value"},
                )

    def test_convenience_functions(self):
        """Should call get_prompt_template with correct parameters."""
        with patch(
            "coaching_assistant.config.lemur_config.get_prompt_template"
        ) as mock_get:
            mock_get.return_value = "Test prompt"

            # Test get_speaker_promp
            result = get_speaker_prompt(
                "english", "enhanced", {"context": "value"}
            )
            assert result == "Test prompt"
            mock_get.assert_called_with(
                "speaker", "english", "enhanced", {"context": "value"}
            )

            # Test get_punctuation_promp
            result = get_punctuation_prompt(
                "chinese", "optimized", {"key": "val"}
            )
            assert result == "Test prompt"
            mock_get.assert_called_with(
                "punctuation", "chinese", "optimized", {"key": "val"}
            )

            # Test get_combined_promp
            result = get_combined_prompt("japanese", "default", None)
            assert result == "Test prompt"
            mock_get.assert_called_with(
                "combined", "japanese", "default", None
            )
