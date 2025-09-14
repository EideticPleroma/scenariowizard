from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import structlog
from pydantic import parse_obj_as

from app.services.database import DatabaseService, get_database_session
from app.services.llm_service import LLMServiceManager, LLMServiceResponse
from app.services.prompt_service import prompt_template_service
from app.services.llm_dependencies import get_llm_manager
from app.models.schemas import (
    GenerationRequest, GenerationResponse,
    ExportRequest, ScenarioResponse, FeatureResponse
)
from app.models.database import Feature, Scenario
from sqlalchemy import select

logger = structlog.get_logger()
router = APIRouter(prefix="/scenarios", tags=["scenarios"])

@router.post("/generate", response_model=GenerationResponse)
async def generate_scenarios(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    llm_manager: LLMServiceManager = Depends(get_llm_manager)
) -> GenerationResponse:
    """Generate BDD scenarios using LLM for specified features"""
    import time
    start_time = time.time()

    db_service = DatabaseService(db)

    try:
        # LLM service manager is injected via dependency

        # Get all requested features
        features = []
        for feature_id in request.feature_ids:
            feature = await db_service.session.execute(
                select(Feature).where(Feature.id == feature_id)
            )
            feature_obj = feature.scalar_one_or_none()
            if not feature_obj:
                raise HTTPException(
                    status_code=404,
                    detail=f"Feature {feature_id} not found"
                )
            features.append(feature_obj)

        scenario_ids = []

        # Process each feature
        for feature in features:
            feature_response = FeatureResponse.from_orm(feature)

            # Generate scenarios for each requested test type
            for test_type in request.test_types:
                try:
                    # Get appropriate prompt template
                    prompt_template = prompt_template_service.get_template(test_type)

                    # Generate scenarios using LLM
                    llm_response: LLMServiceResponse = await llm_manager.generate_scenarios_with_fallback(
                        feature_response,
                        test_type,
                        prompt_template,
                        request.provider
                    )

                    # Parse the generated content (assuming it's Gherkin format)
                    # In a real implementation, you'd parse the LLM output into multiple scenarios
                    scenario_content = llm_response.content

                    # Create scenario with metadata
                    scenario_data = {
                        'feature_id': feature.id,
                        'content': scenario_content,
                        'test_type': test_type.value
                    }

                    lmm_metadata = {
                        'generated_by': llm_response.metadata.provider,
                        'llm_model': llm_response.metadata.llm_model,
                        'generation_time_ms': llm_response.metadata.generation_time_ms,
                        'token_count': {
                            'input': llm_response.metadata.input_tokens,
                            'output': llm_response.metadata.output_tokens,
                            'total': llm_response.metadata.total_tokens
                        },
                        'cost_usd': llm_response.metadata.cost_usd,
                        'prompt_template_id': f"{test_type.value}_default",
                        'generation_error': None
                    }

                    # Save scenario to database
                    scenario = await db_service.create_scenario_with_metadata(
                        scenario_data, lmm_metadata
                    )

                    scenario_ids.append(scenario.id)

                    logger.info("Scenario generated successfully",
                              scenario_id=scenario.id,
                              feature_id=feature.id,
                              test_type=test_type.value,
                              token_count=llm_response.metadata.total_tokens,
                              cost_usd=llm_response.metadata.cost_usd)

                except Exception as e:
                    logger.error("Scenario generation failed",
                               feature_id=feature.id,
                               test_type=test_type.value,
                               error=str(e))

                    # Create scenario with error metadata
                    scenario_data = {
                        'feature_id': feature.id,
                        'content': f"# Error generating {test_type.value} scenarios\n# Error: {str(e)}",
                        'test_type': test_type.value
                    }

                    lmm_metadata = {
                        'generated_by': request.provider,
                        'llm_model': None,
                        'generation_time_ms': int((time.time() - start_time) * 1000),
                        'token_count': {},
                        'cost_usd': 0.0,
                        'prompt_template_id': f"{test_type.value}_default",
                        'generation_error': str(e)
                    }

                    scenario = await db_service.create_scenario_with_metadata(
                        scenario_data, lmm_metadata
                    )
                    scenario_ids.append(scenario.id)

        # Background cleanup of old errors
        background_tasks.add_task(
            db_service.cleanup_generation_errors,
            older_than_minutes=60
        )

        processing_time = int((time.time() - start_time) * 1000)

        response = GenerationResponse(
            scenario_ids=scenario_ids,
            total_scenarios=len(scenario_ids),
            processing_time_ms=processing_time
        )

        logger.info("Batch scenario generation completed",
                  total_scenarios=len(scenario_ids),
                  processing_time_ms=processing_time)

        return response

    except Exception as e:
        logger.error("Batch scenario generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Scenario generation failed: {str(e)}")

@router.get("/feature/{feature_id}", response_model=List[ScenarioResponse])
async def get_scenarios_by_feature(
    feature_id: str,
    db: AsyncSession = Depends(get_database_session)
) -> List[ScenarioResponse]:
    """Get all scenarios for a specific feature"""
    db_service = DatabaseService(db)

    try:
        scenarios = await db_service.get_scenarios_by_feature(feature_id)
        return parse_obj_as(List[ScenarioResponse], scenarios)

    except Exception as e:
        logger.error("Failed to retrieve scenarios", feature_id=feature_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scenarios: {str(e)}")

@router.get("/{scenario_id}/metadata")
async def get_scenario_metadata(
    scenario_id: str,
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get detailed metadata for a specific scenario"""
    db_service = DatabaseService(db)

    try:
        metadata = await db_service.get_scenario_with_metadata(scenario_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Scenario not found")

        return metadata

    except Exception as e:
        logger.error("Failed to retrieve scenario metadata", scenario_id=scenario_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metadata: {str(e)}")

@router.post("/export")
async def export_scenarios(
    request: ExportRequest,
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Export scenarios in various formats"""
    db_service = DatabaseService(db)

    try:
        exported_scenarios = []

        for scenario_id in request.scenario_ids:
            metadata = await db_service.get_scenario_with_metadata(scenario_id)
            if not metadata:
                logger.warning("Scenario not found during export", scenario_id=scenario_id)
                continue

            exported_scenarios.append(metadata)

        if request.format == "feature":
            # Generate .feature file content
            feature_content = _generate_feature_file_content(exported_scenarios)
            return {
                "format": "feature",
                "content": feature_content,
                "filename": "generated_scenarios.feature",
                "total_scenarios": len(exported_scenarios)
            }

        elif request.format == "json":
            return {
                "format": "json",
                "content": exported_scenarios,
                "total_scenarios": len(exported_scenarios)
            }

        else:
            raise HTTPException(status_code=400, detail="Unsupported format")

    except Exception as e:
        logger.error("Export failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/summary")
async def get_scenarios_summary(
    feature_ids: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get summary of scenarios across features"""
    db_service = DatabaseService(db)

    try:
        if not feature_ids:
            # Get all scenarios if no feature_ids specified
            result = await db_service.session.execute(select(Scenario))
            scenarios = result.scalars().all()
        else:
            scenarios = await db_service.get_scenarios_summary(feature_ids)

        # Aggregate statistics
        total_count = len(scenarios)
        by_provider = {}
        by_test_type = {}
        total_cost = 0.0
        error_count = 0

        for scenario in scenarios:
            # Count by provider
            provider = scenario.get('generated_by', 'unknown')
            by_provider[provider] = by_provider.get(provider, 0) + 1

            # Count by test type
            test_type = scenario.get('test_type', 'unknown')
            by_test_type[test_type] = by_test_type.get(test_type, 0) + 1

            # Sum costs
            cost = scenario.get('cost_usd', 0.0)
            if isinstance(cost, str):
                try:
                    cost = float(cost)
                except:
                    cost = 0.0
            total_cost += cost

            # Count errors
            if scenario.get('generation_error'):
                error_count += 1

        return {
            "total_scenarios": total_count,
            "by_provider": by_provider,
            "by_test_type": by_test_type,
            "total_cost_usd": round(total_cost, 4),
            "error_count": error_count,
            "success_rate": round((total_count - error_count) / total_count * 100, 2) if total_count > 0 else 0
        }

    except Exception as e:
        logger.error("Summary generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@router.get("/health/llm")
async def check_llm_health(
    llm_manager: LLMServiceManager = Depends(get_llm_manager)
) -> Dict[str, bool]:
    """Check health of LLM services"""
    try:
        health_results = await llm_manager.health_check_all()

        return {
            "llm_services": health_results,
            "overall_health": any(health_results.values())
        }
    except Exception as e:
        logger.error("LLM health check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"LLM health check failed: {str(e)}")

def _generate_feature_file_content(scenarios: List[Dict[str, Any]]) -> str:
    """Generate Gherkin .feature file content from scenarios"""
    lines = ['# Generated BDD Scenarios\n', '# Auto-generated by ScenarioWizard\n\n']

    current_feature = None

    for scenario in sorted(scenarios, key=lambda s: (s.get('feature_id', ''), s.get('test_type', ''))):
        feature_id = scenario.get('feature_id', '')
        test_type = scenario.get('test_type', 'unit')
        content = scenario.get('content', '')

        # Add feature header if changed
        if current_feature != feature_id:
            lines.append(f'# Feature ID: {feature_id}\n')
            lines.append(f'Feature: Generated Scenarios ({test_type})\n\n')
            current_feature = feature_id

        # Add scenario content
        if content.strip():
            lines.append(f'# Test Type: {test_type}\n')
            lines.append(content.strip())
            lines.append('\n\n')

    return ''.join(lines)
