"""
Dependency injection for LLM services
"""

from typing import Optional
from fastapi import Depends, HTTPException
from app.core.config import Settings, get_settings
from app.services.llm_service import LLMServiceManager

async def get_llm_manager(settings: Settings = Depends(get_settings)) -> LLMServiceManager:
    """Get LLM service manager with API keys from settings"""
    
    if not settings.grok_api_key and not settings.claude_api_key:
        raise HTTPException(
            status_code=500,
            detail="No LLM API keys configured. Please set GROK_API_KEY or CLAUDE_API_KEY environment variables."
        )
    
    try:
        return LLMServiceManager(
            grok_api_key=settings.grok_api_key,
            claude_api_key=settings.claude_api_key,
            grok_model_name=settings.grok_model_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize LLM services: {str(e)}"
        )

async def get_grok_api_key(settings: Settings = Depends(get_settings)) -> Optional[str]:
    """Get Grok API key from settings"""
    return settings.grok_api_key

async def get_claude_api_key(settings: Settings = Depends(get_settings)) -> Optional[str]:
    """Get Claude API key from settings"""
    return settings.claude_api_key
