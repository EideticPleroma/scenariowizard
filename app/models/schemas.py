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
    user_stories: str
    acceptance_criteria: str

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
    feature_ids: List[str] = Field(..., min_items=1)
    test_types: List[TestType] = [TestType.UNIT]
    provider: Optional[str] = None  # 'grok' or 'claude', None for auto-selection

class GenerationResponse(BaseModel):
    scenario_ids: List[str]
    total_scenarios: int
    processing_time_ms: int

class ExportRequest(BaseModel):
    scenario_ids: List[str] = Field(..., min_items=1)
    format: str = Field(pattern="^(feature|json)$", default="feature")
