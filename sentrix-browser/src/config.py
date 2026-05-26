"""
Sentrix Browser Configuration Module
Handles all configuration settings and environment variables
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    browser_model: str = Field(default="llama3.2", env="BROWSER_MODEL")
    code_model: str = Field(default="codellama", env="CODE_MODEL")
    navigation_model: str = Field(default="llama3.2", env="NAVIGATION_MODEL")
    
    # Gmail OAuth2 Configuration
    gmail_client_id: Optional[str] = Field(default=None, env="GMAIL_CLIENT_ID")
    gmail_client_secret: Optional[str] = Field(default=None, env="GMAIL_CLIENT_SECRET")
    gmail_redirect_uri: str = Field(default="http://localhost:8080/callback", env="GMAIL_REDIRECT_URI")
    
    # Security
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    credential_storage_path: str = Field(default="~/.sentrix/credentials", env="CREDENTIAL_STORAGE_PATH")
    
    # Browser Settings
    headless_mode: bool = Field(default=False, env="HEADLESS_MODE")
    browser_timeout: int = Field(default=30000, env="BROWSER_TIMEOUT")
    max_page_retries: int = Field(default=3, env="MAX_PAGE_RETRIES")
    
    # Scheduler
    scheduler_enabled: bool = Field(default=True, env="SCHEDULER_ENABLED")
    default_task_priority: str = Field(default="medium", env="DEFAULT_TASK_PRIORITY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="~/.sentrix/logs/sentrix.log", env="LOG_FILE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings singleton"""
    return Settings()


def setup_directories():
    """Create necessary directories for Sentrix Browser"""
    settings = get_settings()
    
    # Create credential storage directory
    cred_path = Path(settings.credential_storage_path).expanduser()
    cred_path.mkdir(parents=True, exist_ok=True)
    
    # Create log directory
    log_path = Path(settings.log_file).expanduser().parent
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create cache directory
    cache_dir = Path("~/.sentrix/cache").expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        "credentials": cred_path,
        "logs": log_path,
        "cache": cache_dir
    }
