# Phase 4: MCP Docker Integration

## Overview
**Duration**: Week 4  
**Goal**: Implement MCP server in Docker container for external agent access

## Deliverables
- [ ] MCP server implementation
- [ ] Docker container for MCP
- [ ] OAuth authentication for external agents
- [ ] Tool exposure and API integration
- [ ] Rate limiting and security

## Implementation Details

### 1. MCP Server Implementation

#### mcp_server.py
```python
# src/mcp/mcp_server.py
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP Server Configuration
MCP_SERVER_URL = "http://qa-scenario-writer:8000/api/v1"
MCP_AUTH_TOKEN = "your-mcp-auth-token"
JWT_SECRET = "your-jwt-secret"

# Security
security = HTTPBearer()

class MCPTool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str]

class MCPRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any]

class MCPResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str

class MCPServer:
    def __init__(self):
        self.app = FastAPI(
            title="QA Scenario Writer MCP Server",
            description="MCP server for external agent access",
            version="1.0.0"
        )
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Rate limiter
        self.rate_limiter = RateLimiter()
        
        # Available tools
        self.tools = {
            "generate_scenarios": MCPTool(
                name="generate_scenarios",
                description="Generate BDD scenarios from a document",
                parameters={
                    "document_id": {"type": "string", "description": "Document ID to process"},
                    "test_types": {"type": "array", "description": "Test types to generate", "default": ["unit", "integration", "e2e"]},
                    "provider": {"type": "string", "description": "LLM provider", "default": "grok"}
                },
                required=["document_id"]
            ),
            "parse_document": MCPTool(
                name="parse_document",
                description="Parse and validate a Markdown document",
                parameters={
                    "content": {"type": "string", "description": "Markdown content to parse"},
                    "filename": {"type": "string", "description": "Original filename"}
                },
                required=["content"]
            ),
            "validate_gherkin": MCPTool(
                name="validate_gherkin",
                description="Validate Gherkin syntax",
                parameters={
                    "content": {"type": "string", "description": "Gherkin content to validate"}
                },
                required=["content"]
            ),
            "export_scenarios": MCPTool(
                name="export_scenarios",
                description="Export scenarios in specified format",
                parameters={
                    "document_id": {"type": "string", "description": "Document ID"},
                    "format": {"type": "string", "description": "Export format", "default": "gherkin"},
                    "test_types": {"type": "array", "description": "Test types to export"}
                },
                required=["document_id"]
            ),
            "list_documents": MCPTool(
                name="list_documents",
                description="List all documents",
                parameters={},
                required=[]
            ),
            "get_document": MCPTool(
                name="get_document",
                description="Get document details",
                parameters={
                    "document_id": {"type": "string", "description": "Document ID"}
                },
                required=["document_id"]
            )
        }
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup MCP server routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
        @self.app.get("/tools")
        async def list_tools():
            """List available MCP tools"""
            return {"tools": list(self.tools.values())}
        
        @self.app.get("/tools/{tool_name}")
        async def get_tool(tool_name: str):
            """Get specific tool information"""
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail="Tool not found")
            return self.tools[tool_name]
        
        @self.app.post("/execute", response_model=MCPResponse)
        async def execute_tool(
            request: MCPRequest,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """Execute an MCP tool"""
            try:
                # Verify authentication
                if not await self._verify_auth(credentials):
                    raise HTTPException(status_code=401, detail="Invalid authentication")
                
                # Check rate limits
                if not await self.rate_limiter.check_limit(credentials.credentials):
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                
                # Validate tool exists
                if request.tool not in self.tools:
                    raise HTTPException(status_code=404, detail="Tool not found")
                
                # Execute tool
                result = await self._execute_tool(request.tool, request.parameters)
                
                return MCPResponse(
                    success=True,
                    result=result,
                    timestamp=datetime.utcnow().isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return MCPResponse(
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow().isoformat()
                )
    
    async def _verify_auth(self, credentials: HTTPAuthorizationCredentials) -> bool:
        """Verify authentication token"""
        try:
            # Decode JWT token
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
            return True
        except jwt.InvalidTokenError:
            return False
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a specific tool"""
        if tool_name == "generate_scenarios":
            return await self._generate_scenarios_tool(parameters)
        elif tool_name == "parse_document":
            return await self._parse_document_tool(parameters)
        elif tool_name == "validate_gherkin":
            return await self._validate_gherkin_tool(parameters)
        elif tool_name == "export_scenarios":
            return await self._export_scenarios_tool(parameters)
        elif tool_name == "list_documents":
            return await self._list_documents_tool(parameters)
        elif tool_name == "get_document":
            return await self._get_document_tool(parameters)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _generate_scenarios_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scenarios tool implementation"""
        document_id = parameters["document_id"]
        test_types = parameters.get("test_types", ["unit", "integration", "e2e"])
        provider = parameters.get("provider", "grok")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/scenarios/generate",
                params={"document_id": document_id},
                json={
                    "test_types": test_types,
                    "provider": provider
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API error: {response.text}")
    
    async def _parse_document_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document tool implementation"""
        content = parameters["content"]
        filename = parameters.get("filename", "document.md")
        
        async with httpx.AsyncClient() as client:
            files = {"file": (filename, content, "text/markdown")}
            response = await client.post(f"{MCP_SERVER_URL}/documents/upload", files=files)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API error: {response.text}")
    
    async def _validate_gherkin_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Gherkin tool implementation"""
        content = parameters["content"]
        
        # Basic Gherkin validation
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
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "scenario_count": scenario_count
        }
    
    async def _export_scenarios_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Export scenarios tool implementation"""
        document_id = parameters["document_id"]
        format = parameters.get("format", "gherkin")
        test_types = parameters.get("test_types")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/scenarios/export",
                params={"document_id": document_id},
                json={
                    "format": format,
                    "test_types": test_types
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API error: {response.text}")
    
    async def _list_documents_tool(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List documents tool implementation"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MCP_SERVER_URL}/documents/")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API error: {response.text}")
    
    async def _get_document_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get document tool implementation"""
        document_id = parameters["document_id"]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MCP_SERVER_URL}/documents/{document_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise Exception("Document not found")
            else:
                raise Exception(f"API error: {response.text}")

class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def check_limit(self, token: str) -> bool:
        """Check if request is within rate limit"""
        now = datetime.utcnow()
        window_start = now.timestamp() - self.window_seconds
        
        # Clean old requests
        if token in self.requests:
            self.requests[token] = [
                req_time for req_time in self.requests[token]
                if req_time > window_start
            ]
        else:
            self.requests[token] = []
        
        # Check limit
        if len(self.requests[token]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[token].append(now.timestamp())
        return True

# Create MCP server instance
mcp_server = MCPServer()
app = mcp_server.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 2. Docker Configuration for MCP

#### Dockerfile.mcp
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

# Copy MCP server code
COPY src/mcp/ ./src/mcp/
COPY mcp_server.py .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8001

# Run MCP server
CMD ["python", "mcp_server.py"]
```

#### docker-compose.mcp.yml
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
  
  mcp-server:
    build: 
      context: .
      dockerfile: Dockerfile.mcp
    ports:
      - "8001:8001"
    environment:
      - MCP_SERVER_URL=http://qa-scenario-writer:8000/api/v1
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - qa-scenario-writer
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

### 3. MCP Client Example

#### mcp_client_example.py
```python
# Example MCP client for testing
import asyncio
import httpx
import json

class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8001", auth_token: str = "your-auth-token"):
        self.base_url = base_url
        self.auth_token = auth_token
        self.headers = {"Authorization": f"Bearer {auth_token}"}
    
    async def list_tools(self):
        """List available MCP tools"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/tools", headers=self.headers)
            return response.json()
    
    async def execute_tool(self, tool_name: str, parameters: dict):
        """Execute an MCP tool"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/execute",
                json={"tool": tool_name, "parameters": parameters},
                headers=self.headers
            )
            return response.json()
    
    async def generate_scenarios(self, document_id: str, test_types: list = None):
        """Generate scenarios using MCP"""
        if test_types is None:
            test_types = ["unit", "integration", "e2e"]
        
        return await self.execute_tool("generate_scenarios", {
            "document_id": document_id,
            "test_types": test_types,
            "provider": "grok"
        })
    
    async def parse_document(self, content: str, filename: str = "document.md"):
        """Parse document using MCP"""
        return await self.execute_tool("parse_document", {
            "content": content,
            "filename": filename
        })
    
    async def validate_gherkin(self, content: str):
        """Validate Gherkin using MCP"""
        return await self.execute_tool("validate_gherkin", {
            "content": content
        })

async def main():
    client = MCPClient()
    
    # List available tools
    print("Available tools:")
    tools = await client.list_tools()
    for tool in tools["tools"]:
        print(f"- {tool['name']}: {tool['description']}")
    
    # Example: Parse a document
    sample_content = """
# User Authentication Feature

## User Story
As a user, I want to log in to the application so that I can access my personal dashboard.

## Acceptance Criteria
- User can enter email and password
- System validates credentials
- User is redirected to dashboard on success
"""
    
    print("\nParsing document...")
    result = await client.parse_document(sample_content, "auth_feature.md")
    print(f"Document parsed: {result}")
    
    if result["success"]:
        document_id = result["result"]["id"]
        
        # Generate scenarios
        print("\nGenerating scenarios...")
        scenarios = await client.generate_scenarios(document_id)
        print(f"Scenarios generated: {scenarios}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. OAuth Configuration

#### oauth_config.py
```python
# src/mcp/oauth_config.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Optional

# OAuth configuration
JWT_SECRET = "your-jwt-secret"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

class OAuthManager:
    def __init__(self):
        self.clients = {
            "agent-1": {
                "client_id": "agent-1",
                "client_secret": "secret-1",
                "scopes": ["read", "write", "execute"],
                "rate_limit": 1000
            },
            "agent-2": {
                "client_id": "agent-2", 
                "client_secret": "secret-2",
                "scopes": ["read", "execute"],
                "rate_limit": 500
            }
        }
    
    def generate_token(self, client_id: str, client_secret: str) -> str:
        """Generate JWT token for client"""
        if client_id not in self.clients:
            raise HTTPException(status_code=401, detail="Invalid client")
        
        client = self.clients[client_id]
        if client["client_secret"] != client_secret:
            raise HTTPException(status_code=401, detail="Invalid secret")
        
        payload = {
            "client_id": client_id,
            "scopes": client["scopes"],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def check_scope(self, token: str, required_scope: str) -> bool:
        """Check if token has required scope"""
        payload = self.verify_token(token)
        return required_scope in payload.get("scopes", [])

oauth_manager = OAuthManager()

async def verify_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication and return client info"""
    token = credentials.credentials
    payload = oauth_manager.verify_token(token)
    return payload
```

### 5. Environment Configuration

#### .env.mcp
```bash
# MCP Server Configuration
MCP_SERVER_URL=http://qa-scenario-writer:8000/api/v1
MCP_AUTH_TOKEN=your-mcp-auth-token
JWT_SECRET=your-jwt-secret

# OAuth Configuration
OAUTH_CLIENTS=agent-1:secret-1,agent-2:secret-2

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8501
```

## Success Criteria
- [ ] MCP server starts and responds to health checks
- [ ] OAuth authentication works correctly
- [ ] All tools are exposed and functional
- [ ] Rate limiting prevents abuse
- [ ] Docker container runs without issues
- [ ] External agents can access tools
- [ ] Error handling provides clear feedback

## Next Phase
Phase 5 will add testing, documentation, and deployment preparation.
