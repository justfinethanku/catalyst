"""Centralized model configuration management for Catalyst.

This module provides a single source of truth for all model configurations,
loading from the external YAML config file and providing helper functions
for model lookups throughout the codebase.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from .logging_utils import log_exceptions, log_model_selection_error, log_config_error

logger = logging.getLogger(__name__)


class ModelConfigManager:
    """Centralized manager for model configurations."""
    
    def __init__(self):
        """Initialize the model configuration manager."""
        self._config: Dict[str, Any] = {}
        self._config_path = Path(__file__).parent.parent / "config" / "models.yaml"
        self._load_config()
    
    @log_exceptions
    def _load_config(self) -> None:
        """Load model configurations from YAML file."""
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            logger.info("Successfully loaded model configurations from %s", self._config_path)
        except FileNotFoundError as e:
            log_config_error("model configuration", str(self._config_path), e, 
                           "Ensure the models.yaml file exists in src/config/")
            self._config = {}
        except yaml.YAMLError as e:
            log_config_error("model configuration", str(self._config_path), e, 
                           "Check YAML syntax - ensure proper indentation and format")
            self._config = {}
        except Exception as e:
            log_config_error("model configuration", str(self._config_path), e, 
                           "Check file permissions and encoding")
            self._config = {}
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def get_provider_models(self, provider: str) -> Dict[str, str]:
        """
        Get all models for a specific provider.
        
        Args:
            provider: Provider name (openai, gemini)
            
        Returns:
            Dictionary mapping model variants to full model names
        """
        return self._config.get(provider, {})
    
    @log_exceptions
    def get_model_name(self, provider: str, model_variant: str) -> str:
        """
        Get the full model name for a provider and variant.
        
        Args:
            provider: Provider name (openai, gemini)
            model_variant: Model variant key (e.g., 'gpt-4.1', 'gemini-2.5-flash')
            
        Returns:
            Full model name, or falls back to default for provider
        """
        provider_models = self.get_provider_models(provider)
        
        # Try to get the specific model variant
        if model_variant in provider_models:
            logger.debug("Found model variant '%s' for provider '%s': %s", 
                        model_variant, provider, provider_models[model_variant])
            return provider_models[model_variant]
        
        # Log detailed error for missing model variant
        log_model_selection_error(
            provider=provider,
            requested_model=model_variant,
            available_models=provider_models,
            caller_context="primary model selection"
        )
        
        # Fall back to provider default
        default_variant = self.get_default_model_variant(provider)
        if default_variant and default_variant in provider_models:
            logger.warning("Model variant '%s' not found for provider '%s', using default '%s'", 
                          model_variant, provider, default_variant)
            return provider_models[default_variant]
        
        # Last resort: use first available model for provider
        if provider_models:
            first_model = next(iter(provider_models.values()))
            logger.warning("No default found for provider '%s', using first available model: %s", 
                          provider, first_model)
            return first_model
        
        # Ultimate fallback: return the variant as-is
        log_model_selection_error(
            provider=provider,
            requested_model=model_variant,
            available_models={},
            caller_context="ultimate fallback - no models configured"
        )
        logger.error("No models configured for provider '%s', returning variant as-is: %s", 
                    provider, model_variant)
        return model_variant
    
    def get_default_model_variant(self, provider: str) -> Optional[str]:
        """
        Get the default model variant for a provider.
        
        Args:
            provider: Provider name (openai, gemini)
            
        Returns:
            Default model variant key for the provider, or None if not configured
        """
        defaults = self._config.get('defaults', {})
        return defaults.get(provider)
    
    def get_default_model_name(self, provider: str) -> str:
        """
        Get the default model name for a provider.
        
        Args:
            provider: Provider name (openai, gemini)
            
        Returns:
            Full default model name for the provider
        """
        default_variant = self.get_default_model_variant(provider)
        if default_variant:
            return self.get_model_name(provider, default_variant)
        
        # Fallback if no default configured
        provider_models = self.get_provider_models(provider)
        if provider_models:
            return next(iter(provider_models.values()))
        
        logger.error("No models or defaults configured for provider '%s'", provider)
        return f"unknown-{provider}-model"
    
    def is_valid_model_variant(self, provider: str, model_variant: str) -> bool:
        """
        Check if a model variant is valid for a provider.
        
        Args:
            provider: Provider name (openai, gemini)
            model_variant: Model variant key to validate
            
        Returns:
            True if the model variant exists for the provider
        """
        provider_models = self.get_provider_models(provider)
        return model_variant in provider_models
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of configured providers.
        
        Returns:
            List of provider names that have model configurations
        """
        providers = []
        for key in self._config.keys():
            if key != 'defaults' and isinstance(self._config[key], dict):
                providers.append(key)
        return providers
    
    def get_all_model_variants(self, provider: str) -> List[str]:
        """
        Get all available model variants for a provider.
        
        Args:
            provider: Provider name (openai, gemini)
            
        Returns:
            List of model variant keys for the provider
        """
        provider_models = self.get_provider_models(provider)
        return list(provider_models.keys())


# Global instance for easy access
_model_config_manager = ModelConfigManager()


# Convenience functions that use the global instance
def get_model_name(provider: str, model_variant: str) -> str:
    """Get the full model name for a provider and variant."""
    return _model_config_manager.get_model_name(provider, model_variant)


def get_default_model_name(provider: str) -> str:
    """Get the default model name for a provider."""
    return _model_config_manager.get_default_model_name(provider)


def get_default_model_variant(provider: str) -> Optional[str]:
    """Get the default model variant for a provider."""
    return _model_config_manager.get_default_model_variant(provider)


def get_provider_models(provider: str) -> Dict[str, str]:
    """Get all models for a specific provider."""
    return _model_config_manager.get_provider_models(provider)


def is_valid_model_variant(provider: str, model_variant: str) -> bool:
    """Check if a model variant is valid for a provider."""
    return _model_config_manager.is_valid_model_variant(provider, model_variant)


def get_available_providers() -> List[str]:
    """Get list of configured providers."""
    return _model_config_manager.get_available_providers()


def get_all_model_variants(provider: str) -> List[str]:
    """Get all available model variants for a provider."""
    return _model_config_manager.get_all_model_variants(provider)


def reload_model_config() -> None:
    """Reload model configuration from file."""
    _model_config_manager.reload_config()