"""
LeMUR Configuration Management

Centralizes configuration for AssemblyAI LeMUR processing including:
- Model selection (Claude 4 Sonnet, Claude 3.5 Sonnet fallback)
- Prompt templates for speaker identification and punctuation optimization
- Performance settings and batch processing parameters
- Dynamic configuration loading from YAML files
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ModelSettings:
    """LeMUR model configuration settings."""

    default_model: str = "claude_sonnet_4_20250514"
    fallback_model: str = "claude3_5_sonnet"
    max_output_size: int = 4000
    enable_combined_mode: bool = True


@dataclass
class PerformanceSettings:
    """Performance and batch processing settings."""

    max_batch_chars: int = 3000
    max_batch_size: int = 10
    min_batch_size: int = 1
    large_transcript_threshold: int = 15000
    medium_transcript_threshold: int = 8000
    max_concurrent_batches: int = 3
    enable_parallel_processing: bool = True


@dataclass
class LeMURPrompts:
    """Container for LeMUR prompt templates."""

    speaker_identification: Dict[str, Dict[str, str]] = field(default_factory=dict)
    punctuation_optimization: Dict[str, Dict[str, str]] = field(default_factory=dict)
    combined_processing: Dict[str, Dict[str, str]] = field(default_factory=dict)
    fallback_prompts: Dict[str, str] = field(default_factory=dict)
    templates: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def get_speaker_prompt(
        self, language: str = "chinese", variant: str = "default"
    ) -> Optional[str]:
        """Get speaker identification prompt for language and variant."""
        return self.speaker_identification.get(language, {}).get(variant)

    def get_punctuation_prompt(
        self, language: str = "chinese", variant: str = "default"
    ) -> Optional[str]:
        """Get punctuation optimization prompt for language and variant."""
        return self.punctuation_optimization.get(language, {}).get(variant)

    def get_combined_prompt(
        self, language: str = "chinese", variant: str = "default"
    ) -> Optional[str]:
        """Get combined processing prompt for language and variant."""
        return self.combined_processing.get(language, {}).get(variant)


@dataclass
class LeMURConfig:
    """Complete LeMUR configuration with all settings and prompts."""

    model_settings: ModelSettings = field(default_factory=ModelSettings)
    performance_settings: PerformanceSettings = field(
        default_factory=PerformanceSettings
    )
    prompts: LeMURPrompts = field(default_factory=LeMURPrompts)

    @property
    def default_model(self) -> str:
        """Get the default LeMUR model identifier."""
        return self.model_settings.default_model

    @property
    def fallback_model(self) -> str:
        """Get the fallback LeMUR model identifier."""
        return self.model_settings.fallback_model

    @property
    def max_output_size(self) -> int:
        """Get the maximum output size for LeMUR responses."""
        return self.model_settings.max_output_size

    @property
    def combined_mode_enabled(self) -> bool:
        """Check if combined processing mode is enabled."""
        return self.model_settings.enable_combined_mode


class LeMURConfigLoader:
    """Loads and manages LeMUR configuration from YAML files and environment variables."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to YAML configuration file. If None, uses default location.
        """
        if config_path is None:
            # Default to prompts file in same directory
            config_path = Path(__file__).parent / "lemur_prompts.yaml"

        self.config_path = Path(config_path)
        self._config: Optional[LeMURConfig] = None

    def load_config(self, force_reload: bool = False) -> LeMURConfig:
        """
        Load LeMUR configuration from YAML file with environment variable overrides.

        Args:
            force_reload: Force reloading even if config is already cached

        Returns:
            Complete LeMUR configuration object

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if self._config is not None and not force_reload:
            return self._config

        logger.info(f"Loading LeMUR configuration from {self.config_path}")

        if not self.config_path.exists():
            logger.error(f"LeMUR configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f)

            # Parse configuration sections
            model_config = yaml_config.get("model_settings", {})
            perf_config = yaml_config.get("performance", {})

            # Create configuration objects
            model_settings = ModelSettings(
                default_model=model_config.get(
                    "default_model", "claude_sonnet_4_20250514"
                ),
                fallback_model=model_config.get("fallback_model", "claude3_5_sonnet"),
                max_output_size=model_config.get("max_output_size", 4000),
                enable_combined_mode=model_config.get("enable_combined_mode", True),
            )

            batch_config = perf_config.get("batch_processing", {})
            adaptive_config = perf_config.get("adaptive_sizing", {})
            concurrent_config = perf_config.get("concurrent_processing", {})

            performance_settings = PerformanceSettings(
                max_batch_chars=batch_config.get("max_batch_chars", 3000),
                max_batch_size=batch_config.get("max_batch_size", 10),
                min_batch_size=batch_config.get("min_batch_size", 1),
                large_transcript_threshold=adaptive_config.get(
                    "large_transcript_threshold", 15000
                ),
                medium_transcript_threshold=adaptive_config.get(
                    "medium_transcript_threshold", 8000
                ),
                max_concurrent_batches=concurrent_config.get(
                    "max_concurrent_batches", 3
                ),
                enable_parallel_processing=concurrent_config.get(
                    "enable_parallel_processing", True
                ),
            )

            # Load prompts
            prompts = LeMURPrompts(
                speaker_identification=yaml_config.get("speaker_identification", {}),
                punctuation_optimization=yaml_config.get(
                    "punctuation_optimization", {}
                ),
                combined_processing=yaml_config.get("combined_processing", {}),
                fallback_prompts=yaml_config.get("fallback_prompts", {}),
                templates=yaml_config.get("templates", {}),
            )

            # Apply environment variable overrides
            model_settings = self._apply_env_overrides(model_settings)

            self._config = LeMURConfig(
                model_settings=model_settings,
                performance_settings=performance_settings,
                prompts=prompts,
            )

            logger.info("✅ LeMUR configuration loaded successfully")
            logger.info(f"   Default model: {self._config.default_model}")
            logger.info(f"   Combined mode: {self._config.combined_mode_enabled}")
            logger.info(
                f"   Prompt languages: {list(self._config.prompts.speaker_identification.keys())}"
            )

            return self._config

        except yaml.YAMLError as e:
            logger.error(f"❌ Failed to parse YAML configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading LeMUR configuration: {e}")
            raise

    def _apply_env_overrides(self, model_settings: ModelSettings) -> ModelSettings:
        """Apply environment variable overrides to model settings."""
        # Check for environment variable overrides
        if hasattr(settings, "LEMUR_MODEL") and settings.LEMUR_MODEL:
            model_settings.default_model = settings.LEMUR_MODEL
            logger.info(f"🔧 Model override from environment: {settings.LEMUR_MODEL}")

        if (
            hasattr(settings, "LEMUR_MAX_OUTPUT_SIZE")
            and settings.LEMUR_MAX_OUTPUT_SIZE
        ):
            model_settings.max_output_size = int(settings.LEMUR_MAX_OUTPUT_SIZE)
            logger.info(
                f"🔧 Max output size override: {settings.LEMUR_MAX_OUTPUT_SIZE}"
            )

        if (
            hasattr(settings, "LEMUR_COMBINED_MODE")
            and settings.LEMUR_COMBINED_MODE is not None
        ):
            model_settings.enable_combined_mode = bool(settings.LEMUR_COMBINED_MODE)
            logger.info(f"🔧 Combined mode override: {settings.LEMUR_COMBINED_MODE}")

        return model_settings

    def get_prompt_with_context(
        self,
        prompt_type: str,
        language: str = "chinese",
        variant: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Get a prompt template with context variables filled in.

        Args:
            prompt_type: Type of prompt ('speaker', 'punctuation', 'combined')
            language: Language variant ('chinese', 'english')
            variant: Prompt variant ('default', 'enhanced', 'optimized')
            context: Dictionary of context variables for template substitution

        Returns:
            Formatted prompt string or None if not found
        """
        config = self.load_config()

        if prompt_type == "speaker":
            prompt = config.prompts.get_speaker_prompt(language, variant)
        elif prompt_type == "punctuation":
            prompt = config.prompts.get_punctuation_prompt(language, variant)
        elif prompt_type == "combined":
            prompt = config.prompts.get_combined_prompt(language, variant)
        else:
            logger.warning(f"Unknown prompt type: {prompt_type}")
            return None

        if prompt is None:
            logger.warning(f"Prompt not found: {prompt_type}/{language}/{variant}")
            return None

        # Apply context substitution if provided
        if context:
            try:
                return prompt.format(**context)
            except KeyError as e:
                logger.error(f"Missing context variable for prompt template: {e}")
                return prompt

        return prompt


# Global configuration loader instance
_config_loader: Optional[LeMURConfigLoader] = None


def get_lemur_config() -> LeMURConfig:
    """
    Get the global LeMUR configuration instance.

    Returns:
        Global LeMUR configuration object
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = LeMURConfigLoader()

    return _config_loader.load_config()


def reload_lemur_config() -> LeMURConfig:
    """
    Force reload the LeMUR configuration from files.

    Returns:
        Reloaded LeMUR configuration object
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = LeMURConfigLoader()

    return _config_loader.load_config(force_reload=True)


def get_prompt_template(
    prompt_type: str,
    language: str = "chinese",
    variant: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Convenience function to get a formatted prompt template.

    Args:
        prompt_type: Type of prompt ('speaker', 'punctuation', 'combined')
        language: Language variant ('chinese', 'english')
        variant: Prompt variant ('default', 'enhanced', 'optimized')
        context: Dictionary of context variables for template substitution

    Returns:
        Formatted prompt string or None if not found
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = LeMURConfigLoader()

    return _config_loader.get_prompt_with_context(
        prompt_type=prompt_type,
        language=language,
        variant=variant,
        context=context,
    )


# Convenience functions for common use cases
def get_speaker_prompt(
    language: str = "chinese",
    variant: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Get speaker identification prompt."""
    return get_prompt_template("speaker", language, variant, context)


def get_punctuation_prompt(
    language: str = "chinese",
    variant: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Get punctuation optimization prompt."""
    return get_prompt_template("punctuation", language, variant, context)


def get_combined_prompt(
    language: str = "chinese",
    variant: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Get combined processing prompt."""
    return get_prompt_template("combined", language, variant, context)
