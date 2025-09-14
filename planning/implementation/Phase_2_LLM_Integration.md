# Phase 2: LLM Integration

## Overview
**Duration**: Week 2  
**Goal**: Integrate Grok API for BDD scenario generation with fallback to Anthropic Claude

## Deliverables
- [ ] Grok API integration
- [ ] Prompt engineering for Gherkin generation
- [ ] Basic scenario generation
- [ ] Simple validation (syntax check)
- [ ] Error handling and retry logic

## Implementation Details

### 1. LLM Service Architecture

```python
# src/services/llm.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import openai
from anthropic import Anthropic
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

class LLMProvider(ABC):
    @abstractmethod
    async def generate_scenarios(self, feature: Feature, test_type: str) -> str:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass

class GrokProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"  # Grok API endpoint
        )
        self.model = "grok-beta"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_scenarios(self, feature: Feature, test_type: str) -> str:
        """Generate BDD scenarios using Grok API"""
        try:
            prompt = self._build_prompt(feature, test_type)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Grok API error", error=str(e), feature_id=feature.id)
            raise LLMProviderError(f"Grok API failed: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if Grok API is available"""
        try:
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    def _build_prompt(self, feature: Feature, test_type: str) -> str:
        """Build prompt for scenario generation"""
        return f"""
Generate BDD scenarios in Gherkin format for the following feature:

Feature: {feature.title}
Description: {feature.description}

User Stories:
{self._format_user_stories(feature.user_stories)}

Test Type: {test_type}

Please generate comprehensive BDD scenarios including:
1. Happy path scenarios
2. Edge cases
3. Error conditions
4. Background steps if applicable
5. Examples tables where appropriate

Format the output as valid Gherkin syntax with proper Given-When-Then structure.
"""

    def _format_user_stories(self, user_stories: List[UserStory]) -> str:
        """Format user stories for prompt"""
        formatted = []
        for story in user_stories:
            formatted.append(f"- As a {story.as_a}, I want {story.i_want} so that {story.so_that}")
            if story.acceptance_criteria:
                formatted.append("  Acceptance Criteria:")
                for criteria in story.acceptance_criteria:
                    formatted.append(f"    - {criteria}")
        return "\n".join(formatted)

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-sonnet-20240229"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_scenarios(self, feature: Feature, test_type: str) -> str:
        """Generate BDD scenarios using Anthropic Claude"""
        try:
            prompt = self._build_prompt(feature, test_type)
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error("Anthropic API error", error=str(e), feature_id=feature.id)
            raise LLMProviderError(f"Anthropic API failed: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if Anthropic API is available"""
        try:
            await self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
    
    def _build_prompt(self, feature: Feature, test_type: str) -> str:
        """Build prompt for scenario generation"""
        # Same prompt as Grok provider
        return f"""
Generate BDD scenarios in Gherkin format for the following feature:

Feature: {feature.title}
Description: {feature.description}

User Stories:
{self._format_user_stories(feature.user_stories)}

Test Type: {test_type}

Please generate comprehensive BDD scenarios including:
1. Happy path scenarios
2. Edge cases
3. Error conditions
4. Background steps if applicable
5. Examples tables where appropriate

Format the output as valid Gherkin syntax with proper Given-When-Then structure.
"""

    def _format_user_stories(self, user_stories: List[UserStory]) -> str:
        """Format user stories for prompt"""
        formatted = []
        for story in user_stories:
            formatted.append(f"- As a {story.as_a}, I want {story.i_want} so that {story.so_that}")
            if story.acceptance_criteria:
                formatted.append("  Acceptance Criteria:")
                for criteria in story.acceptance_criteria:
                    formatted.append(f"    - {criteria}")
        return "\n".join(formatted)

class LLMService:
    def __init__(self, providers: Dict[str, LLMProvider], fallback_order: List[str]):
        self.providers = providers
        self.fallback_order = fallback_order
    
    async def generate_scenarios(self, feature: Feature, test_type: str, preferred_provider: str = "grok") -> str:
        """Generate scenarios with fallback logic"""
        providers_to_try = [preferred_provider] + [p for p in self.fallback_order if p != preferred_provider]
        
        last_error = None
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue
            
            try:
                provider = self.providers[provider_name]
                
                # Check health before attempting
                if not await provider.health_check():
                    logger.warning("Provider health check failed", provider=provider_name)
                    continue
                
                result = await provider.generate_scenarios(feature, test_type)
                logger.info("Scenarios generated successfully", provider=provider_name, feature_id=feature.id)
                return result
                
            except Exception as e:
                last_error = e
                logger.error("Provider failed", provider=provider_name, error=str(e))
                continue
        
        # All providers failed
        raise AllProvidersFailedError(f"All LLM providers failed. Last error: {last_error}")

class LLMProviderError(Exception):
    pass

class AllProvidersFailedError(Exception):
    pass
```

### 2. Scenario Generation Service

```python
# src/services/scenario_generator.py
from typing import List, Dict, Any
import logging
from datetime import datetime

from src.models.feature import Feature
from src.models.scenario import Scenario, ScenarioCreate
from src.services.llm import LLMService
from src.services.database import DatabaseService
from src.services.validation import GherkinValidator

logger = logging.getLogger(__name__)

class ScenarioGenerator:
    def __init__(self, llm_service: LLMService, db: DatabaseService):
        self.llm_service = llm_service
        self.db = db
        self.validator = GherkinValidator()
    
    async def generate_scenarios_for_feature(self, feature: Feature, test_types: List[str] = None) -> List[Scenario]:
        """Generate scenarios for a feature"""
        if test_types is None:
            test_types = ["unit", "integration", "e2e"]
        
        scenarios = []
        
        for test_type in test_types:
            try:
                logger.info(f"Generating {test_type} scenarios for feature {feature.id}")
                
                # Generate scenarios using LLM
                gherkin_content = await self.llm_service.generate_scenarios(feature, test_type)
                
                # Validate generated Gherkin
                validation_result = self.validator.validate_gherkin(gherkin_content)
                if not validation_result["valid"]:
                    logger.warning(f"Generated Gherkin validation failed: {validation_result['errors']}")
                    # Continue with invalid content but log warning
                
                # Create scenario record
                scenario_create = ScenarioCreate(
                    feature_id=feature.id,
                    content=gherkin_content,
                    test_type=test_type
                )
                
                scenario = self.db.create_scenario(scenario_create)
                scenarios.append(scenario)
                
                logger.info(f"Generated {test_type} scenarios for feature {feature.id}")
                
            except Exception as e:
                logger.error(f"Failed to generate {test_type} scenarios for feature {feature.id}: {e}")
                continue
        
        return scenarios
    
    async def generate_scenarios_for_document(self, document_id: str, test_types: List[str] = None) -> Dict[str, Any]:
        """Generate scenarios for all features in a document"""
        try:
            # Get features for document
            features = self.db.get_features_by_document(document_id)
            
            if not features:
                raise ValueError(f"No features found for document {document_id}")
            
            all_scenarios = []
            feature_results = {}
            
            for feature in features:
                try:
                    scenarios = await self.generate_scenarios_for_feature(feature, test_types)
                    all_scenarios.extend(scenarios)
                    feature_results[feature.id] = {
                        "feature_title": feature.title,
                        "scenarios_count": len(scenarios),
                        "scenarios": [s.dict() for s in scenarios]
                    }
                except Exception as e:
                    logger.error(f"Failed to generate scenarios for feature {feature.id}: {e}")
                    feature_results[feature.id] = {
                        "feature_title": feature.title,
                        "error": str(e),
                        "scenarios_count": 0
                    }
            
            return {
                "document_id": document_id,
                "total_scenarios": len(all_scenarios),
                "features_processed": len(features),
                "feature_results": feature_results,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate scenarios for document {document_id}: {e}")
            raise
```

### 3. Gherkin Validation Service

```python
# src/services/validation.py
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class GherkinValidator:
    def __init__(self):
        self.keywords = ["Feature", "Scenario", "Given", "When", "Then", "And", "But", "Background", "Examples"]
    
    def validate_gherkin(self, content: str) -> Dict[str, Any]:
        """Validate Gherkin syntax and structure"""
        errors = []
        warnings = []
        
        lines = content.split('\n')
        
        # Check for Feature keyword
        if not any(line.strip().startswith('Feature:') for line in lines):
            errors.append("Missing 'Feature:' keyword")
        
        # Check for scenarios
        scenario_count = sum(1 for line in lines if line.strip().startswith('Scenario:'))
        if scenario_count == 0:
            errors.append("No scenarios found")
        elif scenario_count < 2:
            warnings.append("Only one scenario found - consider adding more test cases")
        
        # Check scenario structure
        self._validate_scenarios(lines, errors, warnings)
        
        # Check for proper Given-When-Then structure
        self._validate_gwt_structure(lines, errors, warnings)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "scenario_count": scenario_count
        }
    
    def _validate_scenarios(self, lines: List[str], errors: List[str], warnings: List[str]):
        """Validate individual scenarios"""
        in_scenario = False
        scenario_lines = []
        
        for i, line in enumerate(lines):
            if line.strip().startswith('Scenario:'):
                if in_scenario:
                    # Validate previous scenario
                    self._validate_single_scenario(scenario_lines, errors, warnings)
                in_scenario = True
                scenario_lines = [line]
            elif in_scenario and line.strip() and not line.startswith(' '):
                # End of scenario
                self._validate_single_scenario(scenario_lines, errors, warnings)
                in_scenario = False
                scenario_lines = []
            elif in_scenario:
                scenario_lines.append(line)
        
        # Validate last scenario
        if in_scenario:
            self._validate_single_scenario(scenario_lines, errors, warnings)
    
    def _validate_single_scenario(self, scenario_lines: List[str], errors: List[str], warnings: List[str]):
        """Validate a single scenario"""
        if not scenario_lines:
            return
        
        # Check for Given-When-Then
        has_given = any(line.strip().startswith(('Given', 'And', 'But')) for line in scenario_lines)
        has_when = any(line.strip().startswith(('When', 'And', 'But')) for line in scenario_lines)
        has_then = any(line.strip().startswith(('Then', 'And', 'But')) for line in scenario_lines)
        
        if not has_given:
            errors.append("Scenario missing 'Given' step")
        if not has_when:
            errors.append("Scenario missing 'When' step")
        if not has_then:
            errors.append("Scenario missing 'Then' step")
        
        # Check for proper indentation
        for line in scenario_lines[1:]:  # Skip scenario title
            if line.strip() and not line.startswith('  '):
                warnings.append("Scenario steps should be indented")
                break
    
    def _validate_gwt_structure(self, lines: List[str], errors: List[str], warnings: List[str]):
        """Validate Given-When-Then structure"""
        gwt_sequence = []
        
        for line in lines:
            line = line.strip()
            if line.startswith(('Given', 'When', 'Then', 'And', 'But')):
                if line.startswith('Given') or (line.startswith('And') and gwt_sequence and gwt_sequence[-1] == 'Given'):
                    gwt_sequence.append('Given')
                elif line.startswith('When') or (line.startswith('And') and gwt_sequence and gwt_sequence[-1] == 'When'):
                    gwt_sequence.append('When')
                elif line.startswith('Then') or (line.startswith('And') and gwt_sequence and gwt_sequence[-1] == 'Then'):
                    gwt_sequence.append('Then')
        
        # Check for proper sequence
        if gwt_sequence:
            if 'When' in gwt_sequence and gwt_sequence.index('When') < gwt_sequence.index('Given'):
                warnings.append("'When' step should come after 'Given' step")
            if 'Then' in gwt_sequence and gwt_sequence.index('Then') < gwt_sequence.index('When'):
                warnings.append("'Then' step should come after 'When' step")
```

### 4. API Endpoints for Scenario Generation

```python
# src/api/scenarios.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import logging

from src.models.scenario import Scenario, ScenarioCreate, ScenarioResponse
from src.services.scenario_generator import ScenarioGenerator
from src.services.llm import LLMService, GrokProvider, AnthropicProvider
from src.services.database import DatabaseService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scenarios", tags=["scenarios"])

# Initialize services
db = DatabaseService()
llm_service = LLMService(
    providers={
        "grok": GrokProvider(api_key="your-grok-api-key"),
        "anthropic": AnthropicProvider(api_key="your-anthropic-api-key")
    },
    fallback_order=["anthropic"]
)
scenario_generator = ScenarioGenerator(llm_service, db)

@router.post("/generate", response_model=dict)
async def generate_scenarios(
    document_id: str,
    test_types: Optional[List[str]] = None,
    background_tasks: BackgroundTasks = None
):
    """Generate BDD scenarios for a document"""
    try:
        if test_types is None:
            test_types = ["unit", "integration", "e2e"]
        
        # Update document status to processing
        db.update_document_status(document_id, "processing")
        
        # Generate scenarios
        result = await scenario_generator.generate_scenarios_for_document(document_id, test_types)
        
        # Update document status to completed
        db.update_document_status(document_id, "completed")
        
        logger.info(f"Generated scenarios for document {document_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate scenarios for document {document_id}: {e}")
        db.update_document_status(document_id, "failed", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str):
    """Get scenario by ID"""
    scenario = db.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return ScenarioResponse(
        id=scenario.id,
        feature_id=scenario.feature_id,
        content=scenario.content,
        test_type=scenario.test_type,
        created_at=scenario.created_at
    )

@router.get("/feature/{feature_id}", response_model=List[ScenarioResponse])
async def get_scenarios_by_feature(feature_id: str):
    """Get all scenarios for a feature"""
    scenarios = db.get_scenarios_by_feature(feature_id)
    return [
        ScenarioResponse(
            id=s.id,
            feature_id=s.feature_id,
            content=s.content,
            test_type=s.test_type,
            created_at=s.created_at
        ) for s in scenarios
    ]

@router.post("/{scenario_id}/export")
async def export_scenario(scenario_id: str, format: str = "gherkin"):
    """Export scenario in specified format"""
    scenario = db.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    if format == "gherkin":
        return {"content": scenario.content, "filename": f"scenario_{scenario_id}.feature"}
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
```

### 5. Configuration and Environment

```python
# src/config/settings.py
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./qa_scenarios.db"
    
    # LLM APIs
    grok_api_key: str
    anthropic_api_key: str
    
    # LLM Configuration
    default_llm_provider: str = "grok"
    fallback_providers: List[str] = ["anthropic"]
    
    # Generation Settings
    max_tokens: int = 2000
    temperature: float = 0.7
    max_retries: int = 3
    
    # Test Types
    default_test_types: List[str] = ["unit", "integration", "e2e"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 6. Error Handling and Logging

```python
# src/utils/exceptions.py
from fastapi import HTTPException
from typing import Optional

class QAException(Exception):
    def __init__(self, message: str, status_code: int = 500, error_type: str = "qa_error"):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(message)

class LLMProviderError(QAException):
    def __init__(self, message: str):
        super().__init__(message, 503, "llm_provider_error")

class ValidationError(QAException):
    def __init__(self, message: str):
        super().__init__(message, 422, "validation_error")

class DocumentNotFoundError(QAException):
    def __init__(self, document_id: str):
        super().__init__(f"Document {document_id} not found", 404, "document_not_found")
```

## Success Criteria
- [ ] Grok API integration works correctly
- [ ] Anthropic Claude fallback functions properly
- [ ] Scenarios are generated in valid Gherkin format
- [ ] Basic validation catches syntax errors
- [ ] Error handling provides clear feedback
- [ ] Retry logic handles transient failures
- [ ] All tests pass

## Next Phase
Phase 3 will add the Streamlit frontend and file export functionality.
