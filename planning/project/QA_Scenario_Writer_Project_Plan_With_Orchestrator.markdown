# QA Scenario Writer Project Plan with Orchestrator

## Project Overview
Create a QA scenario generator hosted locally behind an MCP, running in Docker for simplified networking. The agent ingests collated documentation (feature descriptions, user stories, acceptance criteria) and generates BDD-style scenarios with maximum coverage. It supports different test types (unit, system, integration, end-to-end) based on user input. An orchestrator coordinates tasks between components and external LLMs (e.g., Grok API), with flexibility for future custom models. The MCP exposes an API for other web agents to interact securely.

## Objectives
- Parse documentation to extract features, stories, and acceptance criteria.
- Generate comprehensive BDD scenarios for each user story using an LLM.
- Support distinct test types via modular scripts.
- Host in Docker, using its gateway for MCP integration.
- Expose functionality via secure API for external agents.
- Use an orchestrator to manage task flows and enable scaling to specialized models/agents.
- Ensure scalability for future enhancements (e.g., custom trained models, new test frameworks).

## Architecture
- **Language**: Python 3.12 for NLP, scripting, and orchestration.
- **Framework**: FastAPI for async API, Celery for task queuing.
- **Containerization**: Docker for dependency isolation and networking.
- **Components**:
  - **Orchestrator**: Central hub using Celery to dispatch tasks (parsing, scenario generation, test scripting) to appropriate modules or LLMs. Configurable to route to Grok API now, custom models later.
  - **Input Handler**: Parses documents (PDFs, Markdown) using PyPDF2 or LangChain.
  - **Scenario Generator**: Uses LLM (Grok API initially) for BDD scenario creation, called via orchestrator.
  - **Test Script Router**: Selects scripts for unit, system, integration, or E2E tests based on user input.
  - **API Layer**: Exposes endpoints via MCP with JWT/API key auth.
  - **Storage**: SQLite for lightweight session data, Redis for Celery task queues, stateless design for scale.

## Project Phases
### Phase 1: Setup and Prototyping (4-6 days)
- Install Docker on host machine.
- Create Dockerfile for agent and orchestrator: Python 3.12, FastAPI, Uvicorn, LangChain, Pydantic, Celery, Redis.
- Build prototype: Orchestrator dispatches doc parsing and sample BDD scenario generation using placeholder LLM call.
- Test locally with `docker-compose up` (includes Redis for Celery).

### Phase 2: Core Functionality (5-7 days)
- Implement document parser for PDFs/Markdown, extracting features, stories, acceptance criteria.
- Develop scenario generator: Orchestrator sends stories to LLM (Grok API via https://x.ai/api) for comprehensive scenarios (happy paths, edge cases).
- Output Gherkin-compatible BDD files.

### Phase 3: Test-Type Scripts (4-6 days)
- Create modular scripts:
  - `unit.py`: Isolated function tests with mocks.
  - `system.py`: Full application flow tests.
  - `integration.py`: API/service interaction tests.
  - `e2e.py`: UI/process simulation tests.
- Orchestrator routes user input (e.g., `--type=unit`) to correct script via Celery tasks.
- Ensure coverage by generating multiple scenarios per acceptance criterion.

### Phase 4: Orchestrator Integration (4-6 days)
- Implement Celery-based orchestrator:
  - Task queue for parsing, scenario generation, and test scripting.
  - Configurable routing table to map tasks to LLMs or future models.
  - Async task handling for scalability.
- Test orchestrator with sample workflows: Doc upload → parsing → LLM call → scenario output.

### Phase 5: Docker and Networking (3-5 days)
- Set up Docker Compose for multi-container setup (agent, orchestrator, Redis).
- Configure Docker gateway for MCP reverse proxy.
- Use environment variables for API keys, ports, LLM endpoints.

### Phase 6: API Exposure and Security (4-6 days)
- Implement FastAPI routes (e.g., `POST /qa-generate`) for document upload and test type selection.
- Orchestrator handles API requests, dispatching tasks to Celery workers.
- Add JWT or API key authentication.
- Test external access via MCP endpoint.

### Phase 7: Testing and Iteration (3-5 days)
- Write unit tests with Pytest for all modules, including orchestrator.
- Run end-to-end tests with sample documentation.
- Add logging (file-based or Prometheus for metrics).
- Plan for extensibility: Swappable LLMs, plugin support for new test frameworks, custom model integration.

## Timeline
- **Total Duration**: 3-5 weeks (part-time development, ~15-20 hours/week).
- **Milestones**:
  - Week 1: Setup, prototype, orchestrator scaffold.
  - Week 2: Core scenario generation, test-type scripts.
  - Week 3: Orchestrator integration, Docker networking.
  - Week 4: API exposure, security, initial testing.
  - Week 5: Full testing, iteration, documentation.

## Scalability Considerations
- **Orchestrator**: Celery enables dynamic task routing to multiple models/agents.
- **Modular Design**: Separate parsing, generation, scripting, and orchestration for easy feature additions.
- **Stateless Core**: Minimize DB reliance, use Redis for task queues.
- **Extensibility**: Configurable routing for future custom models, plugin system for new test types.

## Next Steps
- Share this plan with project planning AI for detailed task breakdown.
- Prioritize Phase 1 for quick prototype with orchestrator.
- Confirm LLM choice (Grok API recommended: https://x.ai/api).
- Plan for custom model integration post-training.