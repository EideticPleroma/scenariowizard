# Phase 3: Frontend & Export

## Overview
**Duration**: Week 3  
**Goal**: Create Streamlit web interface and implement file export functionality

## Deliverables
- [ ] Streamlit web interface
- [ ] File upload/download functionality
- [ ] .feature file export
- [ ] Basic error messages and user feedback
- [ ] Integration with backend API

## Implementation Details

### 1. Streamlit Web Interface

#### main_streamlit.py
```python
import streamlit as st
import requests
import json
from typing import List, Dict, Any
import io
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="QA Scenario Writer",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def main():
    st.title("🧪 QA Scenario Writer")
    st.markdown("Generate BDD scenarios from Markdown documents")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page",
            ["Upload Document", "View Documents", "Generate Scenarios", "Export Results"]
        )
    
    # Main content
    if page == "Upload Document":
        upload_document_page()
    elif page == "View Documents":
        view_documents_page()
    elif page == "Generate Scenarios":
        generate_scenarios_page()
    elif page == "Export Results":
        export_results_page()

def upload_document_page():
    st.header("📄 Upload Document")
    st.markdown("Upload a Markdown document containing user stories and acceptance criteria")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a Markdown file",
        type=['md'],
        help="Only .md files are supported"
    )
    
    if uploaded_file is not None:
        # Display file content
        content = uploaded_file.read().decode('utf-8')
        st.subheader("Document Preview")
        st.text_area("Content", content, height=300)
        
        # Upload button
        if st.button("Upload Document", type="primary"):
            with st.spinner("Uploading document..."):
                try:
                    # Upload to API
                    files = {"file": (uploaded_file.name, content, "text/markdown")}
                    response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)
                    
                    if response.status_code == 200:
                        document = response.json()
                        st.success(f"Document uploaded successfully! ID: {document['id']}")
                        st.session_state['last_document_id'] = document['id']
                    else:
                        st.error(f"Upload failed: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error uploading document: {str(e)}")

def view_documents_page():
    st.header("📋 View Documents")
    
    try:
        # Get documents from API
        response = requests.get(f"{API_BASE_URL}/documents/")
        if response.status_code == 200:
            documents = response.json()
            
            if not documents:
                st.info("No documents found. Upload a document to get started.")
                return
            
            # Display documents
            for doc in documents:
                with st.expander(f"📄 {doc['filename']} - {doc['status']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**ID:** {doc['id']}")
                        st.write(f"**Status:** {doc['status']}")
                    
                    with col2:
                        st.write(f"**Created:** {doc['created_at']}")
                        if doc['processed_at']:
                            st.write(f"**Processed:** {doc['processed_at']}")
                    
                    with col3:
                        if doc['error_message']:
                            st.error(f"**Error:** {doc['error_message']}")
                        else:
                            st.success("✅ Ready")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"View Details", key=f"view_{doc['id']}"):
                            st.session_state['selected_document'] = doc['id']
                    
                    with col2:
                        if doc['status'] == 'completed':
                            if st.button(f"Generate Scenarios", key=f"gen_{doc['id']}"):
                                st.session_state['selected_document'] = doc['id']
                                st.rerun()
                    
                    with col3:
                        if doc['status'] == 'completed':
                            if st.button(f"Export", key=f"exp_{doc['id']}"):
                                st.session_state['selected_document'] = doc['id']
                                st.rerun()
        else:
            st.error(f"Failed to load documents: {response.text}")
            
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")

def generate_scenarios_page():
    st.header("🚀 Generate Scenarios")
    
    # Document selection
    if 'selected_document' in st.session_state:
        document_id = st.session_state['selected_document']
    else:
        st.info("Please select a document from the 'View Documents' page first.")
        return
    
    st.write(f"**Selected Document ID:** {document_id}")
    
    # Test type selection
    st.subheader("Test Types")
    test_types = st.multiselect(
        "Select test types to generate",
        ["unit", "integration", "e2e", "api", "ui"],
        default=["unit", "integration", "e2e"],
        help="Choose which types of tests to generate"
    )
    
    # LLM provider selection
    st.subheader("LLM Provider")
    provider = st.selectbox(
        "Select LLM provider",
        ["grok", "anthropic"],
        help="Grok is faster, Anthropic is more reliable"
    )
    
    # Generation options
    st.subheader("Generation Options")
    col1, col2 = st.columns(2)
    
    with col1:
        max_scenarios = st.number_input(
            "Max scenarios per test type",
            min_value=1,
            max_value=10,
            value=3,
            help="Maximum number of scenarios to generate per test type"
        )
    
    with col2:
        include_examples = st.checkbox(
            "Include examples tables",
            value=True,
            help="Generate examples tables for data-driven tests"
        )
    
    # Generate button
    if st.button("Generate Scenarios", type="primary"):
        if not test_types:
            st.error("Please select at least one test type.")
            return
        
        with st.spinner("Generating scenarios..."):
            try:
                # Call API to generate scenarios
                payload = {
                    "test_types": test_types,
                    "provider": provider,
                    "max_scenarios": max_scenarios,
                    "include_examples": include_examples
                }
                
                response = requests.post(
                    f"{API_BASE_URL}/scenarios/generate",
                    params={"document_id": document_id},
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("Scenarios generated successfully!")
                    
                    # Display results
                    st.subheader("Generation Results")
                    st.write(f"**Total scenarios:** {result['total_scenarios']}")
                    st.write(f"**Features processed:** {result['features_processed']}")
                    
                    # Display feature results
                    for feature_id, feature_result in result['feature_results'].items():
                        with st.expander(f"Feature: {feature_result['feature_title']}"):
                            st.write(f"**Scenarios generated:** {feature_result['scenarios_count']}")
                            
                            if 'error' in feature_result:
                                st.error(f"Error: {feature_result['error']}")
                            else:
                                for scenario in feature_result['scenarios']:
                                    st.write(f"**{scenario['test_type'].upper()} Test:**")
                                    st.code(scenario['content'], language='gherkin')
                    
                    st.session_state['last_generation_result'] = result
                    
                else:
                    st.error(f"Generation failed: {response.text}")
                    
            except Exception as e:
                st.error(f"Error generating scenarios: {str(e)}")

def export_results_page():
    st.header("📤 Export Results")
    
    if 'last_generation_result' not in st.session_state:
        st.info("No generation results to export. Generate scenarios first.")
        return
    
    result = st.session_state['last_generation_result']
    
    st.subheader("Export Options")
    
    # Export format selection
    export_format = st.selectbox(
        "Select export format",
        ["gherkin", "cucumber", "playwright", "pytest"],
        help="Choose the format for exported test files"
    )
    
    # Export scope
    export_scope = st.radio(
        "Export scope",
        ["All scenarios", "By test type", "By feature"],
        help="Choose which scenarios to export"
    )
    
    if export_scope == "By test type":
        available_types = set()
        for feature_result in result['feature_results'].values():
            if 'scenarios' in feature_result:
                for scenario in feature_result['scenarios']:
                    available_types.add(scenario['test_type'])
        
        selected_types = st.multiselect(
            "Select test types",
            list(available_types),
            default=list(available_types)
        )
    elif export_scope == "By feature":
        available_features = list(result['feature_results'].keys())
        selected_features = st.multiselect(
            "Select features",
            available_features,
            default=available_features
        )
    
    # Export button
    if st.button("Export Scenarios", type="primary"):
        with st.spinner("Preparing export..."):
            try:
                # Prepare export data
                export_data = prepare_export_data(result, export_format, export_scope)
                
                # Generate files
                files = generate_export_files(export_data, export_format)
                
                # Display download links
                st.subheader("Download Files")
                for filename, content in files.items():
                    st.download_button(
                        label=f"Download {filename}",
                        data=content,
                        file_name=filename,
                        mime="text/plain"
                    )
                
                st.success("Export completed successfully!")
                
            except Exception as e:
                st.error(f"Error exporting scenarios: {str(e)}")

def prepare_export_data(result: Dict[str, Any], format: str, scope: str) -> Dict[str, Any]:
    """Prepare data for export based on format and scope"""
    export_data = {
        "format": format,
        "scenarios": [],
        "metadata": {
            "generated_at": result.get('generated_at'),
            "total_scenarios": result['total_scenarios'],
            "features_processed": result['features_processed']
        }
    }
    
    for feature_id, feature_result in result['feature_results'].items():
        if 'scenarios' in feature_result:
            for scenario in feature_result['scenarios']:
                export_data['scenarios'].append({
                    "feature_title": feature_result['feature_title'],
                    "test_type": scenario['test_type'],
                    "content": scenario['content']
                })
    
    return export_data

def generate_export_files(export_data: Dict[str, Any], format: str) -> Dict[str, str]:
    """Generate export files based on format"""
    files = {}
    
    if format == "gherkin":
        # Generate .feature files
        scenarios_by_feature = {}
        for scenario in export_data['scenarios']:
            feature_title = scenario['feature_title']
            if feature_title not in scenarios_by_feature:
                scenarios_by_feature[feature_title] = []
            scenarios_by_feature[feature_title].append(scenario)
        
        for feature_title, scenarios in scenarios_by_feature.items():
            filename = f"{feature_title.lower().replace(' ', '_')}.feature"
            content = generate_gherkin_file(scenarios)
            files[filename] = content
    
    elif format == "cucumber":
        # Generate Cucumber step definitions
        files["step_definitions.py"] = generate_cucumber_steps(export_data['scenarios'])
        files["features/"] = generate_cucumber_features(export_data['scenarios'])
    
    elif format == "playwright":
        # Generate Playwright test files
        files["playwright.config.js"] = generate_playwright_config()
        files["tests/"] = generate_playwright_tests(export_data['scenarios'])
    
    elif format == "pytest":
        # Generate pytest test files
        files["conftest.py"] = generate_pytest_config()
        files["tests/"] = generate_pytest_tests(export_data['scenarios'])
    
    return files

def generate_gherkin_file(scenarios: List[Dict[str, Any]]) -> str:
    """Generate a Gherkin .feature file"""
    content = []
    
    # Group scenarios by test type
    scenarios_by_type = {}
    for scenario in scenarios:
        test_type = scenario['test_type']
        if test_type not in scenarios_by_type:
            scenarios_by_type[test_type] = []
        scenarios_by_type[test_type].append(scenario)
    
    for test_type, type_scenarios in scenarios_by_type.items():
        content.append(f"# {test_type.upper()} Tests")
        content.append("")
        
        for scenario in type_scenarios:
            content.append(scenario['content'])
            content.append("")
    
    return "\n".join(content)

def generate_cucumber_steps(scenarios: List[Dict[str, Any]]) -> str:
    """Generate Cucumber step definitions"""
    return """
# Generated Cucumber step definitions
from behave import given, when, then

@given('I am on the application')
def step_impl(context):
    pass

@when('I perform an action')
def step_impl(context):
    pass

@then('I should see the expected result')
def step_impl(context):
    pass
"""

def generate_playwright_config() -> str:
    """Generate Playwright configuration"""
    return """
// Generated Playwright configuration
module.exports = {
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
};
"""

def generate_playwright_tests(scenarios: List[Dict[str, Any]]) -> str:
    """Generate Playwright test files"""
    return """
// Generated Playwright tests
import { test, expect } from '@playwright/test';

test('generated test', async ({ page }) => {
  // Test implementation will be generated here
});
"""

def generate_pytest_config() -> str:
    """Generate pytest configuration"""
    return """
# Generated pytest configuration
import pytest

@pytest.fixture
def setup():
    # Setup code
    pass

@pytest.fixture
def teardown():
    # Teardown code
    pass
"""

def generate_pytest_tests(scenarios: List[Dict[str, Any]]) -> str:
    """Generate pytest test files"""
    return """
# Generated pytest tests
import pytest

def test_generated():
    # Test implementation will be generated here
    pass
"""

if __name__ == "__main__":
    main()
```

### 2. File Export Service

#### export_service.py
```python
# src/services/export_service.py
from typing import List, Dict, Any, BinaryIO
import zipfile
import io
from datetime import datetime
import logging

from src.models.scenario import Scenario

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
```

### 3. API Endpoints for Export

```python
# Add to src/api/scenarios.py
@router.post("/export")
async def export_scenarios(
    document_id: str,
    format: str = "gherkin",
    test_types: Optional[List[str]] = None,
    create_zip: bool = False
):
    """Export scenarios in specified format"""
    try:
        # Get scenarios for document
        scenarios = db.get_scenarios_by_document(document_id)
        
        if not scenarios:
            raise HTTPException(status_code=404, detail="No scenarios found for document")
        
        # Filter by test types if specified
        if test_types:
            scenarios = [s for s in scenarios if s.test_type in test_types]
        
        # Export scenarios
        export_service = ExportService()
        result = export_service.export_scenarios(scenarios, format)
        
        if create_zip:
            # Create ZIP archive
            zip_buffer = export_service.create_zip_archive(result["files"])
            return Response(
                content=zip_buffer.getvalue(),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename=scenarios_{document_id}.zip"}
            )
        else:
            return result
            
    except Exception as e:
        logger.error(f"Failed to export scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Docker Configuration for Frontend

#### docker-compose.frontend.yml
```yaml
version: '3.8'
services:
  qa-scenario-writer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/qa_scenarios.db
      - GROK_API_KEY=${GROK_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
  
  streamlit-frontend:
    build: 
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://qa-scenario-writer:8000/api/v1
    depends_on:
      - qa-scenario-writer
    restart: unless-stopped
```

#### Dockerfile.streamlit
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Streamlit app
COPY streamlit_app.py .

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Success Criteria
- [ ] Streamlit interface loads and functions correctly
- [ ] File upload works with proper validation
- [ ] Document viewing shows status and details
- [ ] Scenario generation integrates with backend
- [ ] Export functionality works for all formats
- [ ] Error messages are clear and helpful
- [ ] UI is responsive and user-friendly

## Next Phase
Phase 4 will add MCP Docker container integration for external agent access.
