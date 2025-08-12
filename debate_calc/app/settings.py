"""
Configuration settings for the Debate Calculator system.
Handles environment variables, pacing parameters, and model configurations.
"""

import os
from typing import Dict, Literal
from pydantic import Field, validator

# Handle BaseSettings import for different Pydantic versions
try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        raise ImportError(
            "BaseSettings not found. Please install pydantic-settings: "
            "pip install pydantic-settings"
        )
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PaceMode = Literal["slow", "medium", "fast"]


class PacingProfile(BaseSettings):
    """Configuration for debate pacing and timing."""
    
    min_turn_seconds: float = Field(description="Minimum wall-clock duration per speaker turn")
    inter_turn_gap_seconds: float = Field(description="Pause between speaker transitions")
    typeout_rate_chars_per_sec: float = Field(description="Character typing rate for UI effects")
    max_tokens_per_turn: int = Field(description="Maximum tokens per model response")
    
    class Config:
        env_prefix = ""


class ModelConfig(BaseSettings):
    """Configuration for individual AI models."""
    
    api_key: str = Field(description="API key for the model")
    model: str = Field(description="Model identifier")
    max_tokens: int = Field(default=350, description="Maximum tokens per response")
    temperature: float = Field(description="Model temperature setting")
    
    class Config:
        env_prefix = ""


class Settings(BaseSettings):
    """Main configuration class for the Debate Calculator."""
    
    # OpenAI Configuration (Terrence)
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=350, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.2, env="OPENAI_TEMPERATURE")
    
    # Anthropic Configuration (Neil)
    anthropic_api_key: str = Field(env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL")
    anthropic_max_tokens: int = Field(default=350, env="ANTHROPIC_MAX_TOKENS")
    anthropic_temperature: float = Field(default=0.3, env="ANTHROPIC_TEMPERATURE")
    
    # Pacing Configuration
    default_pace_mode: PaceMode = Field(default="slow", env="DEFAULT_PACE_MODE")
    
    # Slow pace settings
    slow_min_turn_seconds: float = Field(default=2.0, env="SLOW_MIN_TURN_SECONDS")
    slow_inter_turn_gap_seconds: float = Field(default=1.0, env="SLOW_INTER_TURN_GAP_SECONDS")
    slow_typeout_rate_chars_per_sec: float = Field(default=45, env="SLOW_TYPEOUT_RATE_CHARS_PER_SEC")
    slow_max_tokens_per_turn: int = Field(default=350, env="SLOW_MAX_TOKENS_PER_TURN")
    
    # Medium pace settings
    medium_min_turn_seconds: float = Field(default=1.2, env="MEDIUM_MIN_TURN_SECONDS")
    medium_inter_turn_gap_seconds: float = Field(default=0.6, env="MEDIUM_INTER_TURN_GAP_SECONDS")
    medium_typeout_rate_chars_per_sec: float = Field(default=70, env="MEDIUM_TYPEOUT_RATE_CHARS_PER_SEC")
    medium_max_tokens_per_turn: int = Field(default=300, env="MEDIUM_MAX_TOKENS_PER_TURN")
    
    # Fast pace settings
    fast_min_turn_seconds: float = Field(default=0.6, env="FAST_MIN_TURN_SECONDS")
    fast_inter_turn_gap_seconds: float = Field(default=0.3, env="FAST_INTER_TURN_GAP_SECONDS")
    fast_typeout_rate_chars_per_sec: float = Field(default=110, env="FAST_TYPEOUT_RATE_CHARS_PER_SEC")
    fast_max_tokens_per_turn: int = Field(default=250, env="FAST_MAX_TOKENS_PER_TURN")
    
    # Debate Configuration
    max_rounds: int = Field(default=12, env="MAX_ROUNDS")
    jitter_percentage: float = Field(default=0.15, env="JITTER_PERCENTAGE")
    retry_max_attempts: int = Field(default=3, env="RETRY_MAX_ATTEMPTS")
    retry_backoff_factor: float = Field(default=2.0, env="RETRY_BACKOFF_FACTOR")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    telemetry_enabled: bool = Field(default=True, env="TELEMETRY_ENABLED")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @validator("jitter_percentage")
    def validate_jitter(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Jitter percentage must be between 0 and 1")
        return v
    
    def get_pacing_profile(self, pace: PaceMode) -> PacingProfile:
        """Get pacing configuration for the specified pace mode."""
        if pace == "slow":
            return PacingProfile(
                min_turn_seconds=self.slow_min_turn_seconds,
                inter_turn_gap_seconds=self.slow_inter_turn_gap_seconds,
                typeout_rate_chars_per_sec=self.slow_typeout_rate_chars_per_sec,
                max_tokens_per_turn=self.slow_max_tokens_per_turn
            )
        elif pace == "medium":
            return PacingProfile(
                min_turn_seconds=self.medium_min_turn_seconds,
                inter_turn_gap_seconds=self.medium_inter_turn_gap_seconds,
                typeout_rate_chars_per_sec=self.medium_typeout_rate_chars_per_sec,
                max_tokens_per_turn=self.medium_max_tokens_per_turn
            )
        elif pace == "fast":
            return PacingProfile(
                min_turn_seconds=self.fast_min_turn_seconds,
                inter_turn_gap_seconds=self.fast_inter_turn_gap_seconds,
                typeout_rate_chars_per_sec=self.fast_typeout_rate_chars_per_sec,
                max_tokens_per_turn=self.fast_max_tokens_per_turn
            )
        else:
            raise ValueError(f"Unknown pace mode: {pace}")
    
    def get_terrence_config(self) -> ModelConfig:
        """Get configuration for Terrence (OpenAI GPT-5)."""
        return ModelConfig(
            api_key=self.openai_api_key,
            model=self.openai_model,
            max_tokens=self.openai_max_tokens,
            temperature=self.openai_temperature
        )
    
    def get_neil_config(self) -> ModelConfig:
        """Get configuration for Neil (Anthropic Claude 3.7 Sonnet)."""
        return ModelConfig(
            api_key=self.anthropic_api_key,
            model=self.anthropic_model,
            max_tokens=self.anthropic_max_tokens,
            temperature=self.anthropic_temperature
        )


# Global settings instance
settings = Settings()
