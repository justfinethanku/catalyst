"""Multi-provider LLM support for Catalyst with comprehensive logging."""
import os
import json
import logging
from typing import Dict, Any, List
from abc import ABC, abstractmethod
import asyncio

# Provider imports
import openai
import google.generativeai as genai

# Model configuration import
from .model_config import get_model_name, get_default_model_name, get_provider_models

# Import logging utilities
from .logging_utils import log_exceptions, log_api_error, get_logger, log_config_error

logger = get_logger(__name__)


# Legacy function kept for backward compatibility - now uses centralized config
def load_model_config() -> Dict[str, Dict[str, str]]:
    """
    Load model configurations from centralized config manager.
    
    Returns:
        Dict containing model configurations for each provider
    """
    from .model_config import _model_config_manager
    return {
        provider: _model_config_manager.get_provider_models(provider) 
        for provider in _model_config_manager.get_available_providers()
    }


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    @abstractmethod
    async def execute_research(self, prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research with the LLM."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> Dict[str, str]:
        """Get available models for this provider."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: str, models: Dict[str, str]):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            models: Dictionary of model configurations loaded from config file
        """
        # Clean the API key of any whitespace or quotes
        clean_api_key = api_key.strip().strip('"').strip("'") if api_key else None
        self.client = openai.OpenAI(api_key=clean_api_key)
        
        logger.info("OpenAI client initialized with key: %s...%s", 
                   clean_api_key[:10] if clean_api_key else 'None',
                   clean_api_key[-4:] if clean_api_key else 'None')
        
        # CHANGED: Model configurations now loaded from external YAML config
        # instead of being hardcoded in Python
        self.models = models or {}
        logger.debug("OpenAI provider initialized with %d models: %s", 
                    len(self.models), list(self.models.keys()))
    
    @log_exceptions
    async def execute_research(self, prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute research using OpenAI Chat Completions API.
        
        Follows OpenAI's official Chat Completions API documentation:
        https://platform.openai.com/docs/api-reference/chat
        
        Model names are loaded from src/config/models.yaml via centralized config.
        """
        # Get model name from centralized config - no hardcoded model names
        # Model names sourced from models.yaml via get_provider_models helper
        model_key = config.get("model", "gpt-4.1")  # Changed from model_variant to model
        
        # Validate model exists in config before proceeding
        available_models = get_provider_models("openai")
        if model_key not in available_models:
            available_keys = list(available_models.keys())
            logger.error("Model '%s' not found in models.yaml config. Available: %s", model_key, available_keys)
            raise ValueError(f"Model '{model_key}' not available. Available models: {available_keys}")
        
        # Get official OpenAI model name from config (not hardcoded)
        model_name = available_models[model_key]
        
        context = {
            "model_key": model_key,
            "model_name": model_name,
            "max_tokens": config.get("max_tokens", 4000),
            "temperature": config.get("temperature", 0.3)
        }
        
        logger.info("Executing OpenAI research with model: %s (from models.yaml)", model_name)
        
        try:
            # Build structured prompt with system/user messages
            # Following OpenAI Chat Completions API message format
            messages = [
                {
                    "role": "system", 
                    "content": """You are an expert business analyst conducting deep strategic research.

Provide comprehensive, insightful analysis with specific examples and evidence. Focus on actionable insights and strategic implications. Use structured formatting with clear sections. Support findings with data and market context."""
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # Use only official OpenAI Chat Completions API
            # No legacy endpoints or custom APIs - strictly following OpenAI documentation
            logger.debug("Calling OpenAI Chat Completions API with model: %s", model_name)
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model_name,  # Official model name from models.yaml
                messages=messages,
                max_tokens=config.get("max_tokens", 4000),
                temperature=config.get("temperature", 0.3),
                # Additional parameters following OpenAI API spec
                top_p=config.get("top_p", 1.0),
                frequency_penalty=config.get("frequency_penalty", 0.0),
                presence_penalty=config.get("presence_penalty", 0.0)
            )
            
            # Extract content from Chat Completions response format
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
            else:
                content = "No content received from API"
                logger.warning("Empty response from OpenAI Chat Completions API")
            
            if not content:
                content = "Empty response received from OpenAI API"
                logger.warning("Empty response received from OpenAI API")
            
            logger.info("OpenAI Chat Completions API call successful")
            return {
                "status": "success",
                "content": content,  # Fixed: content should be the string, not wrapped in dict
                "raw_response": content,
                "tool_calls": [],
                "model": model_name,  # Return actual model name used
                "provider": "openai",
                "usage": {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0)
                } if hasattr(response, 'usage') else {}
            }
            
        except Exception as e:
            log_api_error("openai", "chat completions", e, context)
            return {
                "status": "error",
                "error": f"OpenAI Chat Completions API Error: {str(e)}",
                "content": "",  # Fixed: content should be string even in error case
                "provider": "openai"
            }
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available OpenAI models."""
        return self.models


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""
    
    def __init__(self, api_key: str, models: Dict[str, str]):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google API key
            models: Dictionary of model configurations loaded from config file
        """
        genai.configure(api_key=api_key)
        logger.info("Gemini client initialized")
        
        # CHANGED: Model configurations now loaded from external YAML config
        # instead of being hardcoded in Python
        self.models = models or {}
        logger.debug("Gemini provider initialized with %d models: %s", 
                    len(self.models), list(self.models.keys()))
    
    @log_exceptions
    async def execute_research(self, prompt: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research using Gemini."""
        # Get model using centralized config
        model_key = config.get("model", "gemini-2.5-flash")  # Changed from model_variant to model
        model_name = get_model_name("gemini", model_key)
        
        context = {
            "model_key": model_key,
            "model": model_name,
            "max_tokens": config.get("max_tokens", 4000),
            "temperature": config.get("temperature", 0.3)
        }
        
        logger.info("Executing Gemini research with model: %s", model_name)
        
        try:
            # Initialize model
            model = genai.GenerativeModel(model_name)
            logger.debug("Gemini model initialized: %s", model_name)
            
            # Generate
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=config.get("temperature", 0.3),
                    max_output_tokens=config.get("max_tokens", 4000),
                )
            )
            
            # Extract content
            content = response.text
            
            if not content:
                logger.warning("Empty response received from Gemini API")
                content = "Empty response received from Gemini API"
            
            logger.info("Gemini research execution completed successfully")
            return {
                "status": "success",
                "content": content,  # Fixed: content should be the string, not wrapped in dict
                "raw_response": content,
                "tool_calls": [],
                "model": model_name,
                "provider": "gemini"
            }
            
        except Exception as e:
            log_api_error("gemini", "research execution", e, context)
            return {
                "status": "error",
                "error": f"Gemini API Error: {str(e)}",
                "content": "",  # Fixed: content should be string even in error case
                "provider": "gemini"
            }
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available Gemini models."""
        return self.models


class MultiProviderLLM:
    """Multi-provider LLM interface."""
    
    def __init__(self):
        """Initialize multi-provider system."""
        self.providers = {}
        self.model_configs = {}
        self._load_model_configs()
        self._initialize_providers()
    
    @log_exceptions
    def _load_model_configs(self):
        """Load model configurations from centralized config."""
        try:
            # Import here to access the global config manager
            from .model_config import _model_config_manager
            self.model_configs = {
                provider: _model_config_manager.get_provider_models(provider) 
                for provider in _model_config_manager.get_available_providers()
            }
            if not self.model_configs:
                logger.warning("No model configurations loaded. Providers may not function correctly.")
            else:
                logger.info("Loaded model configurations for %d providers: %s", 
                           len(self.model_configs), list(self.model_configs.keys()))
        except Exception as e:
            logger.error("Failed to load model configurations: %s", str(e))
            self.model_configs = {}
    
    @log_exceptions
    def _initialize_providers(self):
        """Initialize available providers."""
        # Dynamic import path adjustment needed because this module is in src/core/
        # but api_secrets/ is at project root. This allows importing api_keys module
        # TODO: Consider refactoring to use proper package structure or environment variables
        # for API key management to eliminate the need for sys.path manipulation
        import sys
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            from api_secrets.api_keys import OPENAI_API_KEY, GOOGLE_API_KEY
            logger.info("Successfully imported API keys from api_secrets")
        except ImportError as e:
            log_config_error("API keys", "api_secrets/api_keys.py", e, 
                           "Ensure api_secrets/api_keys.py exists with proper API key definitions")
            return
        
        # Initialize providers with available API keys and model configs
        provider_count = 0
        
        # OpenAI Provider
        if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                openai_models = self.model_configs.get("openai", {})
                self.providers["openai"] = OpenAIProvider(OPENAI_API_KEY, openai_models)
                provider_count += 1
                logger.info("✅ OpenAI provider initialized successfully with %d models", len(openai_models))
            except Exception as e:
                log_api_error("openai", "provider initialization", e, 
                             {"models_count": len(self.model_configs.get("openai", {}))})
        else:
            logger.warning("⚠️ OpenAI provider not initialized: API key missing or placeholder")
        
        # Gemini Provider
        if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
            try:
                gemini_models = self.model_configs.get("gemini", {})
                self.providers["gemini"] = GeminiProvider(GOOGLE_API_KEY, gemini_models)
                provider_count += 1
                logger.info("✅ Gemini provider initialized successfully with %d models", len(gemini_models))
            except Exception as e:
                log_api_error("gemini", "provider initialization", e, 
                             {"models_count": len(self.model_configs.get("gemini", {}))})
        else:
            logger.warning("⚠️ Gemini provider not initialized: API key missing or placeholder")
        
        if provider_count == 0:
            logger.error("❌ No LLM providers initialized! Check API key configuration.")
        else:
            logger.info("🚀 MultiProviderLLM initialized with %d providers: %s", 
                       provider_count, list(self.providers.keys()))
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())
    
    def get_provider_models(self, provider: str) -> Dict[str, str]:
        """Get available models for a provider."""
        if provider in self.providers:
            return self.providers[provider].get_available_models()
        logger.warning("Requested models for unavailable provider: %s", provider)
        return {}
    
    async def execute_research(self, 
                              prompt: str, 
                              provider: str,
                              config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research with specified provider."""
        if provider not in self.providers:
            error_msg = f"Provider {provider} not available. Available: {self.get_available_providers()}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "content": ""  # Fixed: content should be string even in error case
            }
        
        logger.info("Executing research with provider: %s", provider)
        result = await self.providers[provider].execute_research(prompt, config)
        
        if result.get("status") == "error":
            logger.error("Research execution failed for provider %s: %s", 
                        provider, result.get("error"))
        
        return result