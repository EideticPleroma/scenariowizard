from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete
from typing import List, Optional
import os
import json
from datetime import datetime, timedelta
from app.models.database import Base, Document, Feature, Scenario

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./scenario_wizard.db")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_database_session():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

class DatabaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(self, document_data: dict) -> Document:
        document = Document(**document_data)
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_document(self, document_id: str) -> Optional[Document]:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_documents(self) -> List[Document]:
        result = await self.session.execute(select(Document))
        return result.scalars().all()

    async def update_document_status(self, document_id: str, status: str, error_message: Optional[str] = None) -> Optional[Document]:
        # Check if document exists first
        document = await self.get_document(document_id)
        if not document:
            return None
            
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(status=status, error_message=error_message)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        # Fetch the updated document
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def create_feature(self, feature_data: dict) -> Feature:
        feature = Feature(**feature_data)
        self.session.add(feature)
        await self.session.commit()
        await self.session.refresh(feature)
        return feature

    async def create_scenario(self, scenario_data: dict) -> Scenario:
        scenario = Scenario(**scenario_data)
        self.session.add(scenario)
        await self.session.commit()
        await self.session.refresh(scenario)
        return scenario

    async def get_features_by_document(self, document_id: str) -> List[Feature]:
        result = await self.session.execute(
            select(Feature).where(Feature.document_id == document_id)
        )
        return result.scalars().all()

    async def get_scenarios_by_feature(self, feature_id: str) -> List[Scenario]:
        result = await self.session.execute(
            select(Scenario).where(Scenario.feature_id == feature_id)
        )
        return result.scalars().all()

    # LLM-related database operations

    async def create_scenario_with_metadata(
        self,
        scenario_data: dict,
        lmm_metadata: dict
    ) -> Scenario:
        """Create a scenario with LLM generation metadata"""
        # Merge scenario data with LLM metadata
        full_data = {**scenario_data}
        full_data.update({
            'generated_by': lmm_metadata.get('generated_by'),
            'llm_model': lmm_metadata.get('llm_model'),
            'generation_time_ms': lmm_metadata.get('generation_time_ms'),
            'token_count': lmm_metadata.get('token_count', {}),  # Store as JSON object
            'cost_usd': lmm_metadata.get('cost_usd', 0.0),  # Store as float
            'prompt_template_id': lmm_metadata.get('prompt_template_id'),
            'generation_error': lmm_metadata.get('generation_error')
        })

        scenario = Scenario(**full_data)
        self.session.add(scenario)
        await self.session.commit()
        await self.session.refresh(scenario)
        return scenario

    async def update_scenario_generation_error(self, scenario_id: str, error_message: str) -> Optional[Scenario]:
        """Update a scenario with generation error"""
        stmt = (
            update(Scenario)
            .where(Scenario.id == scenario_id)
            .values(generation_error=error_message)
        )
        await self.session.execute(stmt)
        await self.session.commit()

        # Fetch updated scenario
        result = await self.session.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        )
        return result.scalar_one_or_none()

    async def get_scenario_with_metadata(self, scenario_id: str) -> Optional[dict]:
        """Get a scenario with parsed metadata"""
        result = await self.session.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        )
        scenario = result.scalar_one_or_none()

        if not scenario:
            return None

        # Parse metadata fields (no JSON parsing needed for new column types)
        metadata = {
            'id': scenario.id,
            'feature_id': scenario.feature_id,
            'content': scenario.content,
            'test_type': scenario.test_type,
            'generated_by': scenario.generated_by,
            'llm_model': scenario.llm_model,
            'generation_time_ms': scenario.generation_time_ms,
            'token_count': scenario.token_count or {},
            'cost_usd': scenario.cost_usd or 0.0,
            'prompt_template_id': scenario.prompt_template_id,
            'generation_error': scenario.generation_error,
            'created_at': scenario.created_at
        }

        return metadata

    async def get_scenarios_summary(self, feature_ids: List[str]) -> List[dict]:
        """Get summary of scenarios for multiple features with metadata"""
        result = await self.session.execute(
            select(Scenario).where(Scenario.feature_id.in_(feature_ids))
        )
        scenarios = result.scalars().all()

        summary = []
        for scenario in scenarios:
            summary.append({
                'id': scenario.id,
                'feature_id': scenario.feature_id,
                'test_type': scenario.test_type,
                'generated_by': scenario.generated_by,
                'llm_model': scenario.llm_model,
                'cost_usd': scenario.cost_usd or 0.0,
                'generation_error': scenario.generation_error,
                'created_at': scenario.created_at
            })

        return summary

    async def cleanup_generation_errors(
        self,
        older_than_minutes: int = 60
    ) -> int:
        """Clean up old generation error records"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=older_than_minutes)

        result = await self.session.execute(
            update(Scenario)
            .where(
                Scenario.generation_error.isnot(None),
                Scenario.created_at < cutoff_time
            )
            .values(generation_error=None)
        )

        await self.session.commit()
        return result.rowcount
