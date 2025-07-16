"""
Configuration management for the World Model backend.
Centralized settings, constants, and configuration validation.
"""

import os
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class AnthropicModel(str, Enum):
    """Available Anthropic models"""
    CLAUDE_3_5_SONNET_LATEST = "claude-3-5-sonnet-latest"
    CLAUDE_3_5_SONNET_20241022 = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_HAIKU_20241022 = "claude-3-5-haiku-20241022"
    CLAUDE_3_SONNET_20240229 = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU_20240307 = "claude-3-haiku-20240307"
    CLAUDE_3_OPUS_20240229 = "claude-3-opus-20240229"


class OpenAIModel(str, Enum):
    """Available OpenAI models"""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


class GenerationLimits(BaseModel):
    """Limits for generation parameters"""
    min_actors: int = Field(1, description="Minimum number of actors")
    max_actors: int = Field(200, description="Maximum number of actors")
    min_subactors: int = Field(1, description="Minimum number of sub-actors")
    max_subactors: int = Field(20, description="Maximum number of sub-actors")
    min_depth: int = Field(0, description="Minimum depth level")
    max_depth: int = Field(10, description="Maximum depth level")
    min_params: int = Field(1, description="Minimum parameters per actor")
    max_params: int = Field(100, description="Maximum parameters per actor")


class LLMSettings(BaseModel):
    """LLM API settings"""
    max_tokens: int = Field(4096, description="Maximum tokens per request")
    temperature: float = Field(0.2, description="Temperature for generation")
    max_concurrent_requests: int = Field(5, description="Maximum concurrent requests")
    request_timeout: int = Field(60, description="Request timeout in seconds")


class AppConfig(BaseModel):
    """Main application configuration"""
    # Generation limits
    limits: GenerationLimits = Field(default_factory=GenerationLimits)
    
    # LLM settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    
    # File paths
    base_logs_dir: str = Field("init_logs", description="Base directory for logs")
    script_version: str = Field("3.0.0", description="Current script version")
    
    # API settings
    api_host: str = Field("localhost", description="API host")
    api_port: int = Field(8000, description="API port")
    cors_origins: List[str] = Field(["http://localhost:3000"], description="CORS origins")
    
    # Default values
    default_provider: ModelProvider = Field(ModelProvider.ANTHROPIC, description="Default LLM provider")
    default_anthropic_model: AnthropicModel = Field(AnthropicModel.CLAUDE_3_5_SONNET_LATEST)
    default_openai_model: OpenAIModel = Field(OpenAIModel.GPT_4O)
    default_num_actors: int = Field(10, description="Default number of actors")
    default_num_subactors: int = Field(8, description="Default number of sub-actors")
    default_target_depth: int = Field(2, description="Default target depth")
    default_num_params: int = Field(20, description="Default parameters per actor")

    @property
    def model_options(self) -> Dict[str, List[Dict[str, str]]]:
        """Get model options for frontend"""
        return {
            "anthropic": [
                {"value": model.value, "label": self._format_model_name(model.value)}
                for model in AnthropicModel
            ],
            "openai": [
                {"value": model.value, "label": self._format_model_name(model.value)}
                for model in OpenAIModel
            ]
        }

    def _format_model_name(self, model_name: str) -> str:
        """Format model name for display"""
        # Convert model names to human-readable format
        name_map = {
            "claude-3-5-sonnet-latest": "Claude 3.5 Sonnet (Latest)",
            "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (Oct 2024)",
            "claude-3-5-haiku-20241022": "Claude 3.5 Haiku (Oct 2024)",
            "claude-3-sonnet-20240229": "Claude 3 Sonnet",
            "claude-3-haiku-20240307": "Claude 3 Haiku",
            "claude-3-opus-20240229": "Claude 3 Opus",
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o Mini",
            "gpt-4": "GPT-4",
            "gpt-4-turbo": "GPT-4 Turbo",
            "gpt-3.5-turbo": "GPT-3.5 Turbo"
        }
        return name_map.get(model_name, model_name.replace("-", " ").title())

    def get_default_model(self, provider: ModelProvider) -> str:
        """Get default model for provider"""
        if provider == ModelProvider.ANTHROPIC:
            return self.default_anthropic_model.value
        elif provider == ModelProvider.OPENAI:
            return self.default_openai_model.value
        else:
            return self.default_anthropic_model.value

    def validate_generation_params(self, **kwargs) -> Dict[str, any]:
        """Validate and clamp generation parameters"""
        validated = {}
        
        # Validate actors
        num_actors = kwargs.get('num_actors', self.default_num_actors)
        validated['num_actors'] = max(self.limits.min_actors, 
                                    min(self.limits.max_actors, num_actors))
        
        # Validate sub-actors
        num_subactors = kwargs.get('num_subactors', self.default_num_subactors)
        validated['num_subactors'] = max(self.limits.min_subactors, 
                                       min(self.limits.max_subactors, num_subactors))
        
        # Validate depth
        target_depth = kwargs.get('target_depth', self.default_target_depth)
        validated['target_depth'] = max(self.limits.min_depth, 
                                      min(self.limits.max_depth, target_depth))
        
        # Validate parameters
        num_params = kwargs.get('num_params', self.default_num_params)
        validated['num_params'] = max(self.limits.min_params, 
                                    min(self.limits.max_params, num_params))
        
        # Other params
        validated['provider'] = kwargs.get('provider', self.default_provider.value)
        validated['model'] = kwargs.get('model', self.get_default_model(ModelProvider(validated['provider'])))
        validated['skip_on_error'] = kwargs.get('skip_on_error', True)
        
        return validated


# Global configuration instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance"""
    return config


def validate_environment() -> List[str]:
    """Validate required environment variables"""
    missing = []
    
    # Check for required API keys based on usage
    if not os.getenv('ANTHROPIC_API_KEY'):
        missing.append('ANTHROPIC_API_KEY')
    
    if not os.getenv('OPENAI_API_KEY'):
        missing.append('OPENAI_API_KEY')
    
    return missing


# Export commonly used items
__all__ = [
    'config',
    'get_config',
    'validate_environment',
    'ModelProvider',
    'AnthropicModel',
    'OpenAIModel',
    'GenerationLimits',
    'LLMSettings',
    'AppConfig'
] 