"""
Grok API client implementation using direct HTTP requests to xAI API
"""

import aiohttp
import json
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()

class Grok:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-4"

    async def chat_completion(
        self, 
        model: str, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """Make actual API call to Grok API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("Grok API call successful", 
                                  model=model, 
                                  tokens=result.get('usage', {}).get('total_tokens', 0))
                        return result
                    else:
                        error_text = await response.text()
                        logger.error("Grok API error", 
                                   status=response.status, 
                                   error=error_text)
                        raise Exception(f"Grok API error {response.status}: {error_text}")
                        
        except aiohttp.ClientError as e:
            logger.error("Grok API connection error", error=str(e))
            raise Exception(f"Grok API connection failed: {str(e)}")
        except Exception as e:
            logger.error("Grok API unexpected error", error=str(e))
            raise Exception(f"Grok API error: {str(e)}")

