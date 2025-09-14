from typing import Dict, Optional
from app.models.schemas import TestType
import structlog

logger = structlog.get_logger()

class PromptTemplateService:
    """Service for managing and formatting prompt templates for BDD scenario generation"""

    def __init__(self):
        self.templates: Dict[str, str] = {
            # Unit Test Template
            "unit_test": """
You are a BDD expert creating Gherkin scenarios from user stories and acceptance criteria.

Feature: {feature_title}

User Stories:
{user_stories}

Acceptance Criteria:
{acceptance_criteria}

Please generate comprehensive BDD test scenarios for unit testing. Focus on:
- Individual component behavior
- Happy path scenarios
- Error conditions and edge cases
- Input validation scenarios
- Expected vs actual behavior

Requirements:
- Use proper Gherkin syntax (Given, When, Then)
- Include both positive and negative test cases
- Cover all acceptance criteria
- Use descriptive, readable language
- Include scenario outlines where appropriate

Format: Return only the Gherkin Feature file content with Scenarios. Do not include explanations or comments.
""",

            # Integration Test Template
            "integration_test": """
You are a BDD expert creating Gherkin scenarios for integration testing between components.

Feature: {feature_title}

User Stories:
{user_stories}

Acceptance Criteria:
{acceptance_criteria}

Please generate comprehensive integration test scenarios that verify:
- Component interactions and data flow
- API interactions between services
- Database operations and data consistency
- End-to-end user workflows
- Third-party service integrations

Requirements:
- Use proper Gherkin syntax (Given, When, Then)
- Test complete user journeys
- Include scenarios for both success and failure states
- Cover all acceptance criteria
- Use scenario outlines for data-driven tests

Format: Return only the Gherkin Feature file content with Scenarios. Do not include explanations or comments.
""",

            # E2E Test Template
            "e2e_test": """
You are a BDD expert creating comprehensive end-to-end test scenarios.

Feature: {feature_title}

User Stories:
{user_stories}

Acceptance Criteria:
{acceptance_criteria}

Please generate complete end-to-end test scenarios that simulate real user journeys:
- Complete user workflows from start to finish
- Multi-step processes and user flows
- Performance and load test scenarios
- Security and compliance checks
- Cross-browser/device compatibility

Requirements:
- Use proper Gherkin syntax (Given, When, Then)
- Cover complete user journeys
- Include performance requirements
- Test error recovery and edge cases
- Verify data persistence and consistency

Format: Return only the Gherkin Feature file content with Scenarios. Do not include explanations or comments.
"""
        }

    def get_template(self, test_type: TestType, template_id: Optional[str] = None) -> str:
        """Get the appropriate prompt template for a test type"""
        # Default template mapping
        template_keys = {
            TestType.UNIT: "unit_test",
            TestType.INTEGRATION: "integration_test",
            TestType.E2E: "e2e_test"
        }

        template_key = template_keys.get(test_type)
        if not template_key:
            logger.warning(f"No template found for test type: {test_type}", test_type=test_type.value)
            template_key = "unit_test"  # Default fallback

        template = self.templates.get(template_key)
        if not template:
            logger.error(f"Template not found: {template_key}")
            raise ValueError(f"Template not found for test type: {test_type.value}")

        return template

    def format_prompt(
        self,
        template: str,
        feature_title: str,
        user_stories: str,
        acceptance_criteria: str,
        test_type: TestType
    ) -> str:
        """Format a prompt template with feature data"""
        try:
            return template.format(
                feature_title=feature_title,
                user_stories=user_stories,
                acceptance_criteria=acceptance_criteria,
                test_type=test_type.value
            )
        except KeyError as e:
            logger.error("Template formatting error", error=str(e), template=template[:100])
            raise ValueError(f"Template formatting error: missing key {e}")

    def add_template(self, template_id: str, template_content: str):
        """Add a custom prompt template"""
        if template_id in self.templates:
            logger.warning(f"Template {template_id} already exists, overwriting")
        self.templates[template_id] = template_content
        logger.info(f"Added custom template", template_id=template_id)

    def list_templates(self) -> Dict[str, str]:
        """List all available templates"""
        return list(self.templates.keys())

    def validate_template(self, template: str) -> bool:
        """Validate that a template has the required placeholders"""
        required_placeholders = ['feature_title', 'user_stories', 'acceptance_criteria', 'test_type']
        for placeholder in required_placeholders:
            if f"{{{placeholder}}}" not in template:
                logger.error(f"Template missing required placeholder: {placeholder}")
                return False
        return True

# Global instance for dependency injection
prompt_template_service = PromptTemplateService()
