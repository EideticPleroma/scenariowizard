from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"

class DocumentBase(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class FeatureBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    user_stories: Optional[str] = None
    acceptance_criteria: Optional[str] = None

class FeatureCreate(FeatureBase):
    document_id: str

class FeatureResponse(FeatureBase):
    id: str
    document_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class ScenarioBase(BaseModel):
    content: str = Field(..., min_length=1)
    test_type: TestType = TestType.UNIT

# LLM-specific models
class LLMMetadata(BaseModel):
    generated_by: Optional[str] = None
    llm_model: Optional[str] = None
    generation_time_ms: Optional[int] = None
    token_count: Optional[dict] = None
    cost_usd: Optional[float] = None
    prompt_template_id: Optional[str] = None
    generation_error: Optional[str] = None

class ScenarioCreate(ScenarioBase):
    feature_id: str

class ScenarioResponse(ScenarioBase):
    id: str
    feature_id: str
    created_at: datetime
    generated_by: Optional[str] = None
    llm_model: Optional[str] = None
    generation_time_ms: Optional[int] = None
    token_count: Optional[dict] = None
    cost_usd: Optional[float] = None
    prompt_template_id: Optional[str] = None
    generation_error: Optional[str] = None

    class Config:
        from_attributes = True

class PromptTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    test_type: TestType
    version: str = "1.0"

class PromptTemplateCreate(PromptTemplateBase):
    pass

class PromptTemplateResponse(PromptTemplateBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Generation request/response models
class GenerationRequest(BaseModel):
    feature_ids: Optional[List[str]] = None
    document_id: Optional[str] = None  # For Phase 3 frontend compatibility
    test_types: List[TestType] = [TestType.UNIT]
    provider: Optional[str] = None  # 'grok' or 'claude', None for auto-selection
    max_scenarios: Optional[int] = 3
    include_examples: Optional[bool] = True

    @validator('feature_ids', pre=True, always=True)
    def check_ids(cls, v, values):
        if not v and not values.get('document_id'):
            raise ValueError('Either feature_ids or document_id must be provided')
        return v

class GenerationResponse(BaseModel):
    scenario_ids: List[str]
    total_scenarios: int
    processing_time_ms: int

class ExportRequest(BaseModel):
    format: str = Field(pattern="^(gherkin|cucumber|playwright|pytest)$", default="gherkin")
    scope: Optional[str] = Field(pattern="^(all|by_test_type|by_feature)$", default="all")
    test_types: Optional[List[str]] = None
    feature_ids: Optional[List[str]] = None
    scenario_ids: Optional[List[str]] = None  # For backward compatibility
