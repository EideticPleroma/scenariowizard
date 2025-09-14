# BDD-Wizard

> **AI-Powered BDD Scenario Generation Tool**

Transform your business requirements, user stories, and acceptance criteria into executable BDD scenarios automatically.

## 🎯 What is BDD-Wizard?

BDD-Wizard is a practical tool that democratizes Behavior-Driven Development (BDD) by automating the creation of Gherkin scenarios from natural language inputs. Instead of spending hours manually writing Given-When-Then scenarios, BDD-Wizard generates them in minutes.

## ✨ Key Features

- **📝 Markdown Input**: Process user stories and requirements from Markdown documents
- **🤖 AI-Powered Generation**: Uses advanced LLMs to create accurate BDD scenarios
- **🎯 Gherkin Output**: Exports standard .feature files compatible with Cucumber, SpecFlow, and other BDD frameworks
- **🔧 MCP Integration**: Exposes tools via Model Context Protocol for external AI agents
- **⚡ Rapid Development**: Built with FastAPI and Streamlit for quick iteration
- **🐳 Docker Ready**: Simple deployment with Docker containers

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker (optional)
- Markdown documents with user stories and acceptance criteria

### Installation

```bash
# Clone the repository
git clone https://github.com/EideticPleroma/BDD-Wizard.git
cd BDD-Wizard

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m streamlit run app/main.py
```

### Docker Installation

```bash
# Build and run with Docker
docker-compose up --build
```

## 📖 Usage

1. **Prepare Your Documents**: Create Markdown files with user stories and acceptance criteria
2. **Upload**: Use the web interface to upload your Markdown documents
3. **Generate**: Let BDD-Wizard create BDD scenarios automatically
4. **Export**: Download .feature files ready for your BDD framework

### Example Input (Markdown)

```markdown
# User Story: User Login

## As a user
I want to log into the application
So that I can access my personal dashboard

## Acceptance Criteria
- User can enter email and password
- System validates credentials
- User is redirected to dashboard on success
- Error message shown for invalid credentials
- Password field is masked
```

### Example Output (Gherkin)

```gherkin
Feature: User Login
  As a user
  I want to log into the application
  So that I can access my personal dashboard

  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter "user@example.com" as email
    And I enter "password123" as password
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see "Welcome, user@example.com"

  Scenario: Failed login with invalid credentials
    Given I am on the login page
    When I enter "invalid@example.com" as email
    And I enter "wrongpassword" as password
    And I click the login button
    Then I should see "Invalid email or password"
    And I should remain on the login page
```

## 🏗️ Architecture

BDD-Wizard follows a modular monolith architecture with MCP integration:

- **Frontend**: Streamlit web interface
- **Backend**: FastAPI with async support
- **Database**: SQLite for simplicity
- **AI Integration**: Grok API and Anthropic Claude
- **MCP Server**: Docker container for tool exposure
- **Document Processing**: spaCy for NLP and Markdown parsing

## 🛠️ Development

### Project Structure

```
BDD-Wizard/
├── app/                    # Main application code
│   ├── api/               # FastAPI routes
│   ├── core/              # Core business logic
│   ├── models/            # Data models
│   └── services/          # Service layer
├── docs/                  # Documentation
├── tests/                 # Test suite
├── docker/                # Docker configurations
└── requirements.txt       # Python dependencies
```

### Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: Streamlit
- **Database**: SQLite
- **AI/ML**: spaCy, LangChain
- **LLM Providers**: Grok API, Anthropic Claude
- **Containerization**: Docker, Docker Compose
- **MCP**: Model Context Protocol for tool exposure

## 📚 Documentation

- [Getting Started Guide](docs/user-guide/getting-started.md)
- [API Reference](docs/api-reference/endpoints.md)
- [Architecture Overview](docs/developer-guide/architecture.md)
- [AI Agent Integration](docs/ai-agent-guide.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need to democratize BDD practices
- Built with modern AI and web technologies
- Designed for practical, real-world use

---

**Ready to transform your requirements into executable BDD scenarios?** 🚀

[Get Started](docs/user-guide/getting-started.md) | [View Documentation](docs/) | [Report Issues](https://github.com/EideticPleroma/BDD-Wizard/issues)
