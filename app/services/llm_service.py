from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import time
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog
import asyncio
from pydantic import BaseModel

from app.models.schemas import TestType, FeatureResponse

logger = structlog.get_logger()

class LLMUsageMetrics(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    generation_time_ms: int
    llm_model: str
    provider: str

class LLMServiceResponse(BaseModel):
    content: str
    metadata: LLMUsageMetrics

class LLMService(ABC):
    """Abstract base class for LLM services (Grok, Claude)"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def generate_scenarios(
        self,
        feature: FeatureResponse,
        test_type: TestType,
        prompt_template: str
    ) -> LLMServiceResponse:
        """Generate Gherkin scenarios for a feature"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM service is available"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name for tracking purposes"""
        pass

class GrokService(LLMService):
    """Grok API implementation for LLM service"""

    def __init__(self, api_key: str, model_name: str = "grok-4"):
        from app.services.grok_sdk import Grok  # Import here to avoid circular imports
        super().__init__(api_key)
        self.client = Grok(api_key=api_key)
        self.model = model_name

    def get_model_name(self) -> str:
        return self.model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def generate_scenarios(
        self,
        feature: FeatureResponse,
        test_type: TestType,
        prompt_template: str
    ) -> LLMServiceResponse:
        """Generate Gherkin scenarios using Grok API"""
        start_time = time.time()

        try:
            # Format the prompt with feature data
            formatted_prompt = prompt_template.format(
                feature_title=feature.title,
                user_stories=feature.user_stories,
                acceptance_criteria=feature.acceptance_criteria,
                test_type=test_type.value
            )

            # Make API call
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": formatted_prompt}],
                temperature=0.7,
                max_tokens=1000
            )

            generation_time = int((time.time() - start_time) * 1000)

            # Extract usage metrics (Grok SDK specific)
            usage = response.get('usage', {})
            input_tokens = usage.get('prompt_tokens', 0)
            output_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', input_tokens + output_tokens)

            # Calculate cost (approximate pricing)
            cost_usd = (input_tokens * 0.00001) + (output_tokens * 0.00003)

            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')

            return LLMServiceResponse(
                content=content,
                metadata=LLMUsageMetrics(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost_usd=round(cost_usd, 6),
                    generation_time_ms=generation_time,
                    llm_model=self.model,
                    provider="grok"
                )
            )

        except Exception as e:
            logger.error("Grok API error", error=str(e), feature_id=feature.id)
            generation_time = int((time.time() - start_time) * 1000)
            raise Exception(f"Grok generation failed: {str(e)}")

    async def health_check(self) -> bool:
        """Health check for Grok API"""
        try:
            # Simple health check with a minimal prompt
            response = await self.client.chat_completion(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.get('choices'))
        except Exception as e:
            logger.error("Grok health check failed", error=str(e))
            return False

class ClaudeService(LLMService):
    """Anthropic Claude API implementation for LLM service"""

    def __init__(self, api_key: str):
        import anthropic
        super().__init__(api_key)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"

    def get_model_name(self) -> str:
        return self.model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    async def generate_scenarios(
        self,
        feature: FeatureResponse,
        test_type: TestType,
        prompt_template: str
    ) -> LLMServiceResponse:
        """Generate Gherkin scenarios using Claude API"""
        start_time = time.time()

        try:
            # Format the prompt with feature data
            formatted_prompt = prompt_template.format(
                feature_title=feature.title,
                user_stories=feature.user_stories,
                acceptance_criteria=feature.acceptance_criteria,
                test_type=test_type.value
            )

            # Make API call
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": formatted_prompt}],
                max_tokens=1000,
                temperature=0.7
            )

            generation_time = int((time.time() - start_time) * 1000)

            # Extract usage metrics from Claude response
            usage = response.usage
            input_tokens = usage.input_tokens if hasattr(usage, 'input_tokens') else 0
            output_tokens = usage.output_tokens if hasattr(usage, 'output_tokens') else 0
            total_tokens = input_tokens + output_tokens

            # Calculate cost (approximate pricing)
            cost_usd = (input_tokens * 0.000015) + (output_tokens * 0.000075)

            content = response.content[0].text if response.content else ""

            return LLMServiceResponse(
                content=content,
                metadata=LLMUsageMetrics(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost_usd=round(cost_usd, 6),
                    generation_time_ms=generation_time,
                    llm_model=self.model,
                    provider="claude"
                )
            )

        except Exception as e:
            logger.error("Claude API error", error=str(e), feature_id=feature.id)
            generation_time = int((time.time() - start_time) * 1000)
            raise Exception(f"Claude generation failed: {str(e)}")

    async def health_check(self) -> bool:
        """Health check for Claude API"""
        try:
            # Simple health check with a minimal prompt
            response = await self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.content and len(response.content) > 0)
        except Exception as e:
            logger.error("Claude health check failed", error=str(e))
            return False

class LLMServiceManager:
    """Manager class for LLM services with fallback logic"""

    def __init__(self, grok_api_key: Optional[str] = None, claude_api_key: Optional[str] = None, grok_model_name: str = "grok-4"):
        self.services: Dict[str, LLMService] = {}
        self.primary_provider = "grok"

        if grok_api_key:
            self.services["grok"] = GrokService(grok_api_key, model_name=grok_model_name)

        if claude_api_key:
            self.services["claude"] = ClaudeService(claude_api_key)

        if not self.services:
            raise ValueError("At least one LLM API key must be provided")

        # Set primary to available service
        if "grok" in self.services:
            self.primary_provider = "grok"
        elif "claude" in self.services:
            self.primary_provider = "claude"

    async def generate_scenarios_with_fallback(
        self,
        feature: FeatureResponse,
        test_type: TestType,
        prompt_template: str,
        preferred_provider: Optional[str] = None
    ) -> LLMServiceResponse:
        """Generate scenarios with automatic fallback between providers"""

        providers_to_try = []
        if preferred_provider and preferred_provider in self.services:
            providers_to_try = [preferred_provider]
        else:
            providers_to_try = [self.primary_provider]

        # Add fallback providers
        fallback_providers = [p for p in self.services.keys() if p not in providers_to_try]
        providers_to_try.extend(fallback_providers)

        last_error = None

        for provider in providers_to_try:
            try:
                logger.info(f"Attempting scenario generation with {provider}",
                          feature_id=feature.id, test_type=test_type.value)

                response = await self.services[provider].generate_scenarios(
                    feature, test_type, prompt_template
                )

                logger.info(f"Successfully generated scenarios with {provider}",
                          feature_id=feature.id,
                          input_tokens=response.metadata.input_tokens,
                          output_tokens=response.metadata.output_tokens,
                          cost_usd=response.metadata.cost_usd)

                return response

            except Exception as e:
                error_msg = f"{provider} generation failed: {str(e)}"
                logger.warning(error_msg, feature_id=feature.id, test_type=test_type.value)
                last_error = e
                continue

        # If all providers failed
        logger.error("All LLM providers failed", feature_id=feature.id, last_error=str(last_error))
        raise Exception(f"All LLM providers failed. Last error: {str(last_error)}")

    async def health_check_all(self) -> Dict[str, bool]:
        """Health check all configured LLM services"""
        results = {}
        for provider, service in self.services.items():
            results[provider] = await service.health_check()
        return results
