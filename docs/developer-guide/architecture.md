# System Architecture

This document provides an overview of the QA Scenario Writer MVP system architecture, designed for simplicity and rapid development.

## Architecture Overview

The QA Scenario Writer follows a **simplified monolithic** architecture with MCP Docker integration for external agent access. The design prioritizes simplicity and rapid development over complex enterprise features.

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Streamlit Web UI]
        CLI[Command Line Interface]
        MCP_CLIENT[MCP Client Agents]
    end
    
    subgraph "API Gateway"
        API[FastAPI Application]
        AUTH[Basic Authentication]
        VALID[Input Validation]
    end
    
    subgraph "Core Processing"
        PARSER[Markdown Parser]
        EXTRACTOR[Feature Extractor]
        LLM[LLM Service<br/>Grok API]
        VALIDATOR[Gherkin Validator]
    end
    
    subgraph "MCP Docker Container"
        MCP_SERVER[MCP Server]
        MCP_TOOLS[Exposed Tools]
        MCP_AUTH[OAuth Authentication]
    end
    
    subgraph "Data Layer"
        DB[(SQLite Database)]
        FILES[File Storage]
    end
    
    subgraph "External Services"
        GROK[Grok API]
        ANTHROPIC[Anthropic Claude<br/>Fallback]
    end
    
    %% Client connections
    UI --> API
    CLI --> API
    MCP_CLIENT --> MCP_SERVER
    
    %% API processing
    API --> PARSER
    API --> AUTH
    API --> VALID
    
    %% Core workflow
    PARSER --> EXTRACTOR
    EXTRACTOR --> LLM
    LLM --> VALIDATOR
    VALIDATOR --> API
    
    %% MCP integration
    MCP_SERVER --> API
    MCP_TOOLS --> MCP_SERVER
    MCP_AUTH --> MCP_SERVER
    
    %% Data storage
    API --> DB
    API --> FILES
    
    %% External services
    LLM --> GROK
    LLM --> ANTHROPIC
    
    %% Styling
    classDef client fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef core fill:#e8f5e8
    classDef mcp fill:#fff3e0
    classDef data fill:#fce4ec
    classDef external fill:#f1f8e9
    
    class UI,CLI,MCP_CLIENT client
    class API,AUTH,VALID api
    class PARSER,EXTRACTOR,LLM,VALIDATOR core
    class MCP_SERVER,MCP_TOOLS,MCP_AUTH mcp
    class DB,FILES data
    class GROK,ANTHROPIC external
```

## Design Principles

### 1. Simplicity First
- **Monolithic Backend**: Single FastAPI application
- **SQLite Database**: No complex database setup
- **Streamlit Frontend**: Rapid UI development
- **Docker Deployment**: Simple containerization

### 2. MCP-First Design
- **Tool Exposure**: Core functionality exposed via MCP tools
- **Agent Integration**: External agents can use tools without direct API access
- **Docker Containerization**: MCP server runs in isolated container
- **OAuth Security**: Secure authentication for external access

### 3. Modular Design
- **Clear Separation**: Parser, Extractor, LLM, Validator modules
- **Interface-Based**: Easy to swap components
- **Configuration-Driven**: Environment-based settings
- **Extensible**: Easy to add new features

## Component Details

### Client Layer

#### Streamlit Web UI
- **Purpose**: Primary user interface
- **Technology**: Streamlit 1.28+
- **Features**: File upload, scenario generation, download
- **Deployment**: Embedded in main application

#### Command Line Interface
- **Purpose**: Developer and automation access
- **Technology**: Click or Typer
- **Features**: Batch processing, script integration
- **Usage**: `qa-scenario generate input.md --output scenarios.feature`

#### MCP Client Agents
- **Purpose**: External agent integration
- **Technology**: MCP protocol
- **Features**: Tool discovery, secure authentication
- **Access**: Via Docker MCP container

### API Gateway (FastAPI)

#### Core Endpoints
```python
# Document Processing
POST /documents/upload          # Upload Markdown file
GET  /documents/{id}            # Get document details
POST /documents/{id}/process    # Process document

# Scenario Generation
POST /scenarios/generate        # Generate BDD scenarios
GET  /scenarios/{id}            # Get generated scenarios
POST /scenarios/{id}/export     # Export to .feature file

# MCP Integration
GET  /mcp/tools                 # List available MCP tools
POST /mcp/execute               # Execute MCP tool
```

#### Authentication
- **Basic Auth**: Username/password for web UI
- **API Keys**: For programmatic access
- **OAuth**: For MCP external agents

### Core Processing Modules

#### Markdown Parser
```python
class MarkdownParser:
    def parse_document(self, content: str) -> Document:
        """Parse Markdown and extract structure"""
        
    def validate_structure(self, content: str) -> ValidationResult:
        """Validate required sections and format"""
```

#### Feature Extractor
```python
class FeatureExtractor:
    def extract_features(self, document: Document) -> List[Feature]:
        """Extract user stories and acceptance criteria"""
        
    def extract_user_stories(self, content: str) -> List[UserStory]:
        """Parse user stories from content"""
```

#### LLM Service
```python
class LLMService:
    def generate_scenarios(self, feature: Feature) -> str:
        """Generate BDD scenarios using Grok API"""
        
    def health_check(self) -> bool:
        """Check LLM service availability"""
```

#### Gherkin Validator
```python
class GherkinValidator:
    def validate_syntax(self, gherkin: str) -> ValidationResult:
        """Validate Gherkin syntax"""
        
    def validate_completeness(self, gherkin: str) -> ValidationResult:
        """Check for complete scenarios"""
```

### MCP Docker Container

#### MCP Server
```python
class MCPServer:
    def __init__(self):
        self.tools = {
            "generate_scenarios": self.generate_scenarios_tool,
            "parse_document": self.parse_document_tool,
            "validate_gherkin": self.validate_gherkin_tool,
            "export_feature": self.export_feature_tool
        }
    
    async def generate_scenarios_tool(self, document_id: str) -> str:
        """MCP tool for scenario generation"""
        
    async def parse_document_tool(self, content: str) -> dict:
        """MCP tool for document parsing"""
```

#### Exposed MCP Tools
- **`generate_scenarios`**: Generate BDD scenarios from document
- **`parse_document`**: Parse and validate Markdown input
- **`validate_gherkin`**: Validate generated Gherkin syntax
- **`export_feature`**: Export scenarios to .feature files

#### Docker Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  qa-scenario-writer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./qa_scenarios.db
      - GROK_API_KEY=${GROK_API_KEY}
    volumes:
      - ./data:/app/data
      
  mcp-server:
    build: ./mcp
    ports:
      - "8001:8001"
    environment:
      - MCP_SERVER_URL=http://qa-scenario-writer:8000
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
    depends_on:
      - qa-scenario-writer
```

### Data Layer

#### SQLite Database
```sql
-- Documents table
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Features table
CREATE TABLE features (
    id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(id),
    title TEXT NOT NULL,
    user_stories TEXT,
    acceptance_criteria TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scenarios table
CREATE TABLE scenarios (
    id TEXT PRIMARY KEY,
    feature_id TEXT REFERENCES features(id),
    content TEXT NOT NULL,
    test_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### File Storage
- **Input Files**: Uploaded Markdown documents
- **Output Files**: Generated .feature files
- **Templates**: BDD scenario templates
- **Logs**: Application and error logs

## Data Flow

### 1. Web UI Workflow
```
User Upload → FastAPI → Parser → Extractor → LLM → Validator → Database → Download
```

### 2. MCP Agent Workflow
```
Agent Request → MCP Server → FastAPI → Processing → Response → Agent
```

### 3. CLI Workflow
```
CLI Command → FastAPI → Processing → File Output
```

## Technology Stack

### Backend
- **FastAPI 0.104+**: Web framework
- **SQLite**: Database
- **Pydantic**: Data validation
- **spaCy**: NLP processing

### Frontend
- **Streamlit 1.28+**: Web UI
- **HTML/CSS**: Styling
- **JavaScript**: Client-side interactions

### MCP Integration
- **MCP Protocol**: Tool communication
- **Docker**: Containerization
- **OAuth 2.0**: Authentication

### External Services
- **Grok API**: Primary LLM
- **Anthropic Claude**: Fallback LLM

## Security Model

### Web UI Security
- **Basic Authentication**: Username/password
- **Session Management**: JWT tokens
- **Input Validation**: Sanitize all inputs
- **File Upload Limits**: Size and type restrictions

### MCP Security
- **OAuth 2.0**: Secure external agent authentication
- **Token-Based**: API tokens for tool access
- **Rate Limiting**: Prevent abuse
- **CORS**: Configured for specific origins

### Data Security
- **Input Sanitization**: Clean all user inputs
- **File Validation**: Check file types and content
- **Database Security**: Parameterized queries
- **Logging**: Audit trail for all operations

## Deployment Architecture

### Development Environment
```bash
# Local development
docker-compose up -d

# Access points
Web UI: http://localhost:8000
MCP Server: http://localhost:8001
API Docs: http://localhost:8000/docs
```

### Production Environment
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With reverse proxy
nginx → FastAPI (port 8000)
nginx → MCP Server (port 8001)
```

## Scalability Considerations

### Current Design (MVP)
- **Single Instance**: One FastAPI application
- **SQLite Database**: File-based storage
- **Synchronous Processing**: Simple request/response

### Future Scaling (Post-MVP)
- **Horizontal Scaling**: Multiple FastAPI instances
- **PostgreSQL**: Relational database
- **Redis**: Caching and session storage
- **Async Processing**: Background task queues

## Monitoring and Observability

### Basic Monitoring (MVP)
- **Application Logs**: Structured logging
- **Error Tracking**: Exception handling
- **Health Checks**: Service availability
- **Basic Metrics**: Request count, response time

### Advanced Monitoring (Post-MVP)
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards
- **Jaeger**: Distributed tracing
- **ELK Stack**: Log aggregation

## Development Workflow

### Phase 1: Core Backend (Week 1)
- FastAPI setup with basic endpoints
- Markdown parsing with markdown-it-py
- SQLite database for results storage
- Basic error handling and logging

### Phase 2: LLM Integration (Week 2)
- Grok API integration
- Prompt engineering for Gherkin generation
- Basic scenario generation
- Simple validation (syntax check)

### Phase 3: Frontend & Export (Week 3)
- Streamlit web interface
- File upload/download functionality
- .feature file export
- Basic error messages and user feedback

### Phase 4: MCP Integration (Week 4)
- MCP server implementation
- Docker container for MCP
- OAuth authentication for external agents
- Tool exposure and API integration

## Best Practices

### Code Organization
- **Modular Design**: Clear separation of concerns
- **Interface-Based**: Easy to swap implementations
- **Configuration-Driven**: Environment-based settings
- **Error Handling**: Comprehensive error management

### Testing Strategy
- **Unit Tests**: Core parsing and generation logic
- **Integration Tests**: End-to-end workflow
- **User Testing**: Real user stories from different domains
- **Manual Review**: Generated scenarios reviewed by BDD experts

### Performance Considerations
- **Caching**: Simple in-memory caching for repeated requests
- **Async Processing**: Non-blocking I/O where possible
- **Resource Management**: Proper cleanup of resources
- **Monitoring**: Basic performance metrics

## Troubleshooting

### Common Issues
1. **LLM API Failures**: Check API keys and network connectivity
2. **MCP Authentication Issues**: Verify JWT secret and OAuth configuration
3. **Database Issues**: Check SQLite file permissions and disk space
4. **Docker Issues**: Check container logs and port mappings

### Debugging
- **Application Logs**: Check structured logs for errors
- **Health Checks**: Verify service availability
- **API Documentation**: Use FastAPI's built-in docs
- **MCP Tools**: Test individual tools via MCP client

This architecture provides a solid foundation for the MVP while maintaining flexibility for future enhancements. The MCP integration allows external agents to use the tools without direct API access, and the Docker containerization ensures easy deployment and scaling.