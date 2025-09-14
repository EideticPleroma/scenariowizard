# API Endpoints Reference

This document provides documentation for all API endpoints in the QA Scenario Writer MVP system.

## Base Information

- **Base URL**: `http://localhost:8000/api/v1` (development)
- **API Version**: v1
- **Authentication**: Basic Auth (MVP) / OAuth (MCP)
- **Content Type**: `application/json`
- **Rate Limiting**: 100 requests per hour (MCP)

## Quick Start

### Development Setup
```bash
# Start the application
python main.py

# Access API documentation
http://localhost:8000/docs
```

### Docker Setup
```bash
# Start all services
docker-compose -f docker-compose.mcp.yml up -d

# Access services
# API: http://localhost:8000
# Web UI: http://localhost:8501
# MCP Server: http://localhost:8001
```

## Core Endpoints

### Health Check

#### GET /health
Check API health status.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Document Management

#### POST /documents/upload
Upload a Markdown document for processing.

**Request**:
- **Content-Type**: `multipart/form-data`
- **Body**: File upload (Markdown file only)

**Supported File Types**: Only `.md` (Markdown) files are supported.

**Response** (200 OK):
```json
{
  "id": "doc_1234567890",
  "filename": "user_stories.md",
  "status": "uploaded",
  "created_at": "2025-01-27T10:30:00Z",
  "processed_at": null,
  "error_message": null
}
```

**Error Responses**:
- `400 Bad Request`: Invalid file format (only .md files supported) or size
- `413 Payload Too Large`: File size exceeds limit
- `500 Internal Server Error`: Server error during upload

#### GET /documents/{document_id}
Get document details by ID.

**Path Parameters**:
- `document_id` (string): Unique document identifier

**Response** (200 OK):
```json
{
  "id": "doc_1234567890",
  "filename": "user_stories.md",
  "status": "completed",
  "created_at": "2025-01-27T10:30:00Z",
  "processed_at": "2025-01-27T10:31:00Z",
  "error_message": null
}
```

**Error Responses**:
- `404 Not Found`: Document not found

#### GET /documents/
List all documents.

**Query Parameters**:
- `limit` (integer, optional): Number of documents to return (default: 50)
- `offset` (integer, optional): Number of documents to skip (default: 0)
- `status` (string, optional): Filter by status (uploaded, processing, completed, failed)

**Response** (200 OK):
```json
[
  {
    "id": "doc_1234567890",
    "filename": "user_stories.md",
    "status": "completed",
    "created_at": "2025-01-27T10:30:00Z",
    "processed_at": "2025-01-27T10:31:00Z"
  }
]
```

### Scenario Generation

#### POST /scenarios/generate
Generate BDD scenarios for a document.

**Query Parameters**:
- `document_id` (string, required): Document ID to process

**Request Body**:
```json
{
  "test_types": ["unit", "integration", "e2e"],
  "provider": "grok",
  "max_scenarios": 3,
  "include_examples": true
}
```

**Response** (200 OK):
```json
{
  "document_id": "doc_1234567890",
  "total_scenarios": 9,
  "features_processed": 3,
  "feature_results": {
    "feat_1": {
      "feature_title": "User Authentication",
      "scenarios_count": 3,
      "scenarios": [
        {
          "id": "scenario_1",
          "test_type": "unit",
          "content": "Feature: User Authentication\nScenario: Valid login\n  Given I am on the login page\n  When I enter valid credentials\n  Then I should be logged in"
        }
      ]
    }
  },
  "generated_at": "2025-01-27T10:32:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Document not found
- `422 Unprocessable Entity`: Invalid request parameters
- `503 Service Unavailable`: LLM service unavailable

#### GET /scenarios/{scenario_id}
Get scenario details by ID.

**Path Parameters**:
- `scenario_id` (string): Unique scenario identifier

**Response** (200 OK):
```json
{
  "id": "scenario_123",
  "feature_id": "feat_1",
  "content": "Feature: User Authentication\nScenario: Valid login\n  Given I am on the login page\n  When I enter valid credentials\n  Then I should be logged in",
  "test_type": "unit",
  "created_at": "2025-01-27T10:32:00Z"
}
```

#### GET /scenarios/feature/{feature_id}
Get all scenarios for a feature.

**Path Parameters**:
- `feature_id` (string): Feature identifier

**Response** (200 OK):
```json
[
  {
    "id": "scenario_123",
    "feature_id": "feat_1",
    "content": "Feature: User Authentication\nScenario: Valid login\n  Given I am on the login page\n  When I enter valid credentials\n  Then I should be logged in",
    "test_type": "unit",
    "created_at": "2025-01-27T10:32:00Z"
  }
]
```

### Export

#### POST /scenarios/export
Export scenarios in specified format.

**Query Parameters**:
- `document_id` (string, required): Document ID
- `format` (string, optional): Export format (gherkin, cucumber, playwright, pytest) - default: gherkin
- `create_zip` (boolean, optional): Create ZIP archive - default: false

**Request Body**:
```json
{
  "test_types": ["unit", "integration", "e2e"],
  "include_metadata": true
}
```

**Response** (200 OK):
```json
{
  "format": "gherkin",
  "files": {
    "user_authentication.feature": "Feature: User Authentication\nScenario: Valid login\n  Given I am on the login page\n  When I enter valid credentials\n  Then I should be logged in"
  },
  "total_files": 1,
  "download_url": "http://localhost:8000/api/v1/scenarios/export/download/123"
}
```

**ZIP Response** (200 OK):
- **Content-Type**: `application/zip`
- **Content-Disposition**: `attachment; filename=scenarios_doc_123.zip`
- **Body**: ZIP file containing exported scenarios

## MCP Server Endpoints

The MCP server runs on port 8001 and provides tool-based access for external agents.

### Base Information
- **Base URL**: `http://localhost:8001`
- **Authentication**: Bearer token (JWT)
- **Rate Limiting**: 100 requests per hour per token

### MCP Tools

#### GET /tools
List available MCP tools.

**Response** (200 OK):
```json
{
  "tools": [
    {
      "name": "generate_scenarios",
      "description": "Generate BDD scenarios from a document",
      "parameters": {
        "document_id": {"type": "string", "description": "Document ID to process"},
        "test_types": {"type": "array", "description": "Test types to generate", "default": ["unit", "integration", "e2e"]},
        "provider": {"type": "string", "description": "LLM provider", "default": "grok"}
      },
      "required": ["document_id"]
    }
  ]
}
```

#### POST /execute
Execute an MCP tool.

**Request Body**:
```json
{
  "tool": "generate_scenarios",
  "parameters": {
    "document_id": "doc_1234567890",
    "test_types": ["unit", "integration"],
    "provider": "grok"
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "result": {
    "document_id": "doc_1234567890",
    "total_scenarios": 6,
    "features_processed": 2
  },
  "error": null,
  "timestamp": "2025-01-27T10:32:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "result": null,
  "error": "Tool not found",
  "timestamp": "2025-01-27T10:32:00Z"
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Types

#### 400 Bad Request
- `invalid_file_format`: Only .md files supported
- `file_too_large`: File size exceeds limit
- `invalid_parameters`: Invalid request parameters

#### 401 Unauthorized
- `invalid_token`: Invalid or expired token
- `missing_auth`: Authentication required

#### 404 Not Found
- `document_not_found`: Document ID not found
- `scenario_not_found`: Scenario ID not found

#### 422 Unprocessable Entity
- `validation_error`: Input validation failed
- `malformed_document`: Document structure invalid

#### 429 Too Many Requests
- `rate_limit_exceeded`: Too many requests

#### 503 Service Unavailable
- `llm_service_unavailable`: LLM service down
- `retry_after`: Suggested retry time in seconds

## Rate Limiting

### Web API (Port 8000)
- **Limit**: 1000 requests per hour per IP
- **Headers**: 
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

### MCP Server (Port 8001)
- **Limit**: 100 requests per hour per token
- **Headers**:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

## Examples

### Complete Workflow

1. **Upload Document**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@user_stories.md"
```

2. **Generate Scenarios**:
```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/generate?document_id=doc_123" \
  -H "Content-Type: application/json" \
  -d '{"test_types": ["unit", "integration"], "provider": "grok"}'
```

3. **Export Scenarios**:
```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/export?document_id=doc_123&format=gherkin" \
  -H "Content-Type: application/json" \
  -d '{"test_types": ["unit", "integration"]}'
```

### MCP Client Example

```python
import httpx

async def generate_scenarios(document_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/execute",
            json={
                "tool": "generate_scenarios",
                "parameters": {
                    "document_id": document_id,
                    "test_types": ["unit", "integration"],
                    "provider": "grok"
                }
            },
            headers={"Authorization": "Bearer your-token"}
        )
        return response.json()
```

## SDK Examples

### Python
```python
from qa_scenario_writer import QAScenarioClient

client = QAScenarioClient("http://localhost:8000")

# Upload document
document = client.upload_document("user_stories.md")

# Generate scenarios
scenarios = client.generate_scenarios(
    document_id=document["id"],
    test_types=["unit", "integration"],
    provider="grok"
)

# Export scenarios
export = client.export_scenarios(
    document_id=document["id"],
    format="gherkin"
)
```

### JavaScript
```javascript
const client = new QAScenarioClient("http://localhost:8000");

// Upload document
const document = await client.uploadDocument("user_stories.md");

// Generate scenarios
const scenarios = await client.generateScenarios({
  documentId: document.id,
  testTypes: ["unit", "integration"],
  provider: "grok"
});

// Export scenarios
const export = await client.exportScenarios({
  documentId: document.id,
  format: "gherkin"
});
```

## Support

For API support and questions:
- **Documentation**: Check the implementation guide
- **Issues**: Report bugs and feature requests
- **Examples**: See the phase-specific implementation docs