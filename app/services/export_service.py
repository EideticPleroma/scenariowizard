from typing import List, Dict, Any, BinaryIO
import zipfile
import io
from datetime import datetime
import logging

from app.models.database import Scenario

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self):
        self.supported_formats = ["gherkin", "cucumber", "playwright", "pytest"]

    def export_scenarios(self, scenarios: List[Scenario], format: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Export scenarios in specified format"""
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}")

        if options is None:
            options = {}

        if format == "gherkin":
            return self._export_gherkin(scenarios, options)
        elif format == "cucumber":
            return self._export_cucumber(scenarios, options)
        elif format == "playwright":
            return self._export_playwright(scenarios, options)
        elif format == "pytest":
            return self._export_pytest(scenarios, options)

    def _export_gherkin(self, scenarios: List[Scenario], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as Gherkin .feature files"""
        files = {}

        # Group scenarios by feature
        scenarios_by_feature = {}
        for scenario in scenarios:
            feature_id = scenario.feature_id
            if feature_id not in scenarios_by_feature:
                scenarios_by_feature[feature_id] = []
            scenarios_by_feature[feature_id].append(scenario)

        for feature_id, feature_scenarios in scenarios_by_feature.items():
            filename = f"feature_{feature_id}.feature"
            content = self._generate_gherkin_content(feature_scenarios)
            files[filename] = content

        return {
            "format": "gherkin",
            "files": files,
            "total_files": len(files)
        }

    def _export_cucumber(self, scenarios: List[Scenario], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as Cucumber project"""
        files = {}

        # Generate step definitions
        files["step_definitions.py"] = self._generate_cucumber_steps(scenarios)

        # Generate feature files
        feature_files = self._generate_cucumber_features(scenarios)
        files.update(feature_files)

        # Generate configuration
        files["behave.ini"] = self._generate_behave_config()

        return {
            "format": "cucumber",
            "files": files,
            "total_files": len(files)
        }

    def _export_playwright(self, scenarios: List[Scenario], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as Playwright project"""
        files = {}

        # Generate configuration
        files["playwright.config.js"] = self._generate_playwright_config()
        files["package.json"] = self._generate_package_json()

        # Generate test files
        test_files = self._generate_playwright_tests(scenarios)
        files.update(test_files)

        return {
            "format": "playwright",
            "files": files,
            "total_files": len(files)
        }

    def _export_pytest(self, scenarios: List[Scenario], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as pytest project"""
        files = {}

        # Generate configuration
        files["conftest.py"] = self._generate_pytest_config()
        files["pytest.ini"] = self._generate_pytest_ini()

        # Generate test files
        test_files = self._generate_pytest_tests(scenarios)
        files.update(test_files)

        return {
            "format": "pytest",
            "files": files,
            "total_files": len(files)
        }

    def create_zip_archive(self, files: Dict[str, str], filename: str = None) -> BinaryIO:
        """Create a ZIP archive from files"""
        if filename is None:
            filename = f"scenarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, content in files.items():
                zip_file.writestr(file_path, content)

        zip_buffer.seek(0)
        return zip_buffer

    def _generate_gherkin_content(self, scenarios: List[Scenario]) -> str:
        """Generate Gherkin content for scenarios"""
        content = []

        # Group by test type
        scenarios_by_type = {}
        for scenario in scenarios:
            test_type = scenario.test_type
            if test_type not in scenarios_by_type:
                scenarios_by_type[test_type] = []
            scenarios_by_type[test_type].append(scenario)

        for test_type, type_scenarios in scenarios_by_type.items():
            content.append(f"# {test_type.upper()} Tests")
            content.append("")

            for scenario in type_scenarios:
                content.append(scenario.content)
                content.append("")

        return "\n".join(content)

    def _generate_cucumber_steps(self, scenarios: List[Scenario]) -> str:
        """Generate Cucumber step definitions"""
        return '''"""
Generated Cucumber step definitions
"""
from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@given('I am on the application')
def step_impl(context):
    context.driver = webdriver.Chrome()
    context.driver.get("https://example.com")

@when('I perform an action')
def step_impl(context):
    # Implementation for action
    pass

@then('I should see the expected result')
def step_impl(context):
    # Implementation for verification
    pass
'''

    def _generate_cucumber_features(self, scenarios: List[Scenario]) -> Dict[str, str]:
        """Generate Cucumber feature files"""
        files = {}

        # Group scenarios by feature
        scenarios_by_feature = {}
        for scenario in scenarios:
            feature_id = scenario.feature_id
            if feature_id not in scenarios_by_feature:
                scenarios_by_feature[feature_id] = []
            scenarios_by_feature[feature_id].append(scenario)

        for feature_id, feature_scenarios in scenarios_by_feature.items():
            filename = f"features/{feature_id}.feature"
            content = self._generate_cucumber_feature_content(feature_scenarios)
            files[filename] = content

        return files

    def _generate_cucumber_feature_content(self, scenarios: List[Scenario]) -> str:
        """Generate content for a Cucumber feature file"""
        if not scenarios:
            return ""

        # Use the first scenario to get feature info
        first_scenario = scenarios[0]
        feature_title = f"Feature: {first_scenario.feature_title}"

        content = [feature_title, ""]

        for scenario in scenarios:
            content.append(scenario.content)
            content.append("")

        return "\n".join(content)

    def _generate_behave_config(self) -> str:
        """Generate behave configuration"""
        return """[behave]
default_format = pretty
color = true
logging_level = INFO
"""

    def _generate_playwright_config(self) -> str:
        """Generate Playwright configuration"""
        return """const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 2,
  use: {
    headless: true,
    viewport: { width: 1280, height: 720 },
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
"""

    def _generate_package_json(self) -> str:
        """Generate package.json for Playwright"""
        return """{
  "name": "generated-playwright-tests",
  "version": "1.0.0",
  "description": "Generated Playwright tests",
  "scripts": {
    "test": "playwright test",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
"""

    def _generate_playwright_tests(self, scenarios: List[Scenario]) -> Dict[str, str]:
        """Generate Playwright test files"""
        files = {}

        # Group scenarios by feature and test type
        scenarios_by_feature_type = {}
        for scenario in scenarios:
            key = f"{scenario.feature_id}_{scenario.test_type}"
            if key not in scenarios_by_feature_type:
                scenarios_by_feature_type[key] = []
            scenarios_by_feature_type[key].append(scenario)

        for feature_type_key, feature_type_scenarios in scenarios_by_feature_type.items():
            filename = f"tests/{feature_type_key}.spec.js"
            content = self._generate_playwright_test_content(feature_type_scenarios)
            files[filename] = content

        return files

    def _generate_playwright_test_content(self, scenarios: List[Scenario]) -> str:
        """Generate content for a Playwright test file"""
        content = []
        content.append("const { test, expect } = require('@playwright/test');")
        content.append("")

        for i, scenario in enumerate(scenarios):
            content.append(f"test('{scenario.test_type} test {i+1}', async ({ { page } }) => {{")
            content.append("  // Test implementation will be generated here")
            content.append("  // TODO: Implement test steps based on scenario")
            content.append("});")
            content.append("")

        return "\n".join(content)

    def _generate_pytest_config(self) -> str:
        """Generate pytest configuration"""
        return """import pytest

@pytest.fixture
def setup():
    # Setup code
    pass

@pytest.fixture
def teardown():
    # Teardown code
    pass
"""

    def _generate_pytest_ini(self) -> str:
        """Generate pytest.ini configuration"""
        return """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
"""

    def _generate_pytest_tests(self, scenarios: List[Scenario]) -> Dict[str, str]:
        """Generate pytest test files"""
        files = {}

        # Group scenarios by feature and test type
        scenarios_by_feature_type = {}
        for scenario in scenarios:
            key = f"{scenario.feature_id}_{scenario.test_type}"
            if key not in scenarios_by_feature_type:
                scenarios_by_feature_type[key] = []
            scenarios_by_feature_type[key].append(scenario)

        for feature_type_key, feature_type_scenarios in scenarios_by_feature_type.items():
            filename = f"tests/test_{feature_type_key}.py"
            content = self._generate_pytest_test_content(feature_type_scenarios)
            files[filename] = content

        return files

    def _generate_pytest_test_content(self, scenarios: List[Scenario]) -> str:
        """Generate content for a pytest test file"""
        content = []
        content.append("import pytest")
        content.append("")

        for i, scenario in enumerate(scenarios):
            content.append(f"def test_{scenario.test_type}_{i+1}():")
            content.append("    # Test implementation will be generated here")
            content.append("    # TODO: Implement test steps based on scenario")
            content.append("    pass")
            content.append("")

        return "\n".join(content)
