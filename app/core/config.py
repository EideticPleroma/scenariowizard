"""
Configuration management for ScenarioWizard
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings with environment variable support"""
    
    def __init__(self):
        # Database
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./scenario_wizard.db")
        
        # LLM API Keys
        self.grok_api_key = os.getenv("GROK_API_KEY") or "xai-ltDmpTr1Q5c9OIZy4Z82IlHySGodpNpVpmVKnndKWsoAN3WHUqUZy7QuieSdq4vgIg8fxZFzMJsvMBh"
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.grok_model_name = os.getenv("GROK_MODEL_NAME", "grok-4")

        # Application Settings
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # API Settings
        self.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # MCP Settings
        self.mcp_server_port = int(os.getenv("MCP_SERVER_PORT", "3000"))
        self.mcp_server_host = os.getenv("MCP_SERVER_HOST", "localhost")

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Dependency injection for settings"""
    return settings
