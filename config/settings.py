"""Application settings using Pydantic."""
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration."""
    
    # API Keys
    openai_api_key: str
    google_api_key: Optional[str] = None
    
    # LLM Configuration
    default_llm_provider: str = "openai"
    llm_models: Dict[str, str] = {
        "openai": "gpt-4.1-2025-04-14",
        "gemini": "gemini-1.5-pro"
    }
    enable_web_search: bool = True
    enable_vision: bool = True
    
    # Vector Database
    vector_db_path: str = "./catalyst_vector_db"
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    similarity_threshold: float = 0.7
    max_search_results: int = 20
    
    # Storage
    client_data_path: str = "./clients"
    enable_json_backup: bool = True
    enable_vector_storage: bool = True
    
    # Intelligence Settings
    min_pattern_occurrences: int = 3
    contradiction_threshold: float = 0.8
    insight_confidence_threshold: float = 0.6
    enable_auto_insights: bool = True
    
    # Processing
    batch_size: int = 10
    max_concurrent_requests: int = 5
    request_timeout: int = 60
    
    # UI Settings
    streamlit_theme: str = "dark"
    show_debug_info: bool = False
    enable_analytics: bool = True
    
    # Paths
    templates_path: str = "./config/prompts"
    housekeeping_path: str = "./housekeeping"
    docs_path: str = "./docs"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_llm_model(self, provider: str) -> str:
        """Get model name for a provider."""
        return self.llm_models.get(provider, self.llm_models["openai"])
    
    def get_template_path(self, phase: str, step: str) -> Path:
        """Get path to a specific template."""
        return Path(self.templates_path) / phase / step
    
    def get_client_path(self, client_name: str) -> Path:
        """Get path for client data."""
        clean_name = client_name.lower().replace(" ", "_")
        return Path(self.client_data_path) / clean_name


# Create global settings instance
settings = Settings()