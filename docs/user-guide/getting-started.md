# Getting Started with QA Scenario Writer

This guide will help you get up and running with the QA Scenario Writer MVP in just a few minutes.

## What is QA Scenario Writer?

QA Scenario Writer is a simple tool that automatically generates BDD (Behavior-Driven Development) scenarios from Markdown documents containing user stories and acceptance criteria. It uses AI to convert natural language requirements into executable Gherkin test scenarios.

## Prerequisites

Before you begin, ensure you have:
- A modern web browser (Chrome, Firefox, Safari, Edge)
- Documents in Markdown (.md) format only
- Basic understanding of BDD (Behavior-Driven Development)
- Documents should be properly formatted and complete before upload

## Quick Start (5 minutes)

### Option 1: Docker (Recommended)

The easiest way to get started:

```bash
# Clone the repository
git clone https://github.com/your-org/qa-scenario-writer.git
cd qa-scenario-writer

# Start all services
docker-compose -f docker-compose.mcp.yml up -d

# Check if services are running
docker-compose ps
```

**Access the application:**
- **Web UI**: http://localhost:8501
- **API**: http://localhost:8000
- **MCP Server**: http://localhost:8001

### Option 2: Local Development

For development or if you prefer local installation:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROK_API_KEY="your-grok-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Run the application
python main.py
```

**Access the application:**
- **Web UI**: http://localhost:8501
- **API**: http://localhost:8000

## Your First Document

### 1. Prepare Your Markdown Document

Create a Markdown file with user stories and acceptance criteria. Here's an example:

```markdown
# User Authentication Feature

## User Story
As a user, I want to log in to the application so that I can access my personal dashboard.

## Acceptance Criteria
- User can enter email and password
- System validates credentials
- User is redirected to dashboard on success
- User sees error message for invalid credentials
- User can log out securely

## Additional Requirements
- Password must be at least 8 characters
- Account locks after 3 failed attempts
- Session expires after 30 minutes of inactivity
```

**Save this as `user_auth.md`**

### 2. Upload Your Document

1. Open the web interface at http://localhost:8501
2. Click "Upload Document"
3. Select your `.md` file
4. Click "Upload Document"

### 3. Generate Scenarios

1. Go to "Generate Scenarios" page
2. Select your document
3. Choose test types (unit, integration, e2e)
4. Select LLM provider (Grok recommended)
5. Click "Generate Scenarios"

### 4. Export Results

1. Go to "Export Results" page
2. Choose export format (Gherkin, Cucumber, Playwright, pytest)
3. Click "Export Scenarios"
4. Download the generated files

## Sample Workflow

### Input: Markdown Document
```markdown
# E-commerce Checkout Feature

## User Story
As a customer, I want to complete a purchase so that I can receive my items.

## Acceptance Criteria
- Customer can add items to cart
- Customer can review order details
- Customer can enter shipping information
- Customer can select payment method
- Customer receives confirmation email
```

### Output: Generated Gherkin Scenarios
```gherkin
Feature: E-commerce Checkout
  As a customer
  I want to complete a purchase
  So that I can receive my items

  Scenario: Successful checkout with valid information
    Given I have items in my cart
    And I am on the checkout page
    When I enter valid shipping information
    And I select a payment method
    And I complete the purchase
    Then I should see a confirmation message
    And I should receive a confirmation email

  Scenario: Checkout fails with invalid payment
    Given I have items in my cart
    And I am on the checkout page
    When I enter valid shipping information
    And I enter an invalid payment method
    And I attempt to complete the purchase
    Then I should see a payment error message
    And my order should not be processed
```

## Using the API

### Upload Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@user_stories.md"
```

### Generate Scenarios
```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/generate?document_id=doc_123" \
  -H "Content-Type: application/json" \
  -d '{"test_types": ["unit", "integration"], "provider": "grok"}'
```

### Export Scenarios
```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/export?document_id=doc_123&format=gherkin"
```

## Using MCP (External Agents)

If you're building an external agent or automation:

### 1. Get Authentication Token
```bash
curl -X POST "http://localhost:8001/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "your-client", "client_secret": "your-secret"}'
```

### 2. List Available Tools
```bash
curl -X GET "http://localhost:8001/tools" \
  -H "Authorization: Bearer your-token"
```

### 3. Execute Tool
```bash
curl -X POST "http://localhost:8001/execute" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "generate_scenarios",
    "parameters": {
      "document_id": "doc_123",
      "test_types": ["unit", "integration"],
      "provider": "grok"
    }
  }'
```

## Supported Formats

### Input Formats
- **Markdown (.md)**: Only supported format
- **Structure**: User stories with acceptance criteria
- **Requirements**: Proper Markdown formatting

### Output Formats
- **Gherkin**: Standard BDD format
- **Cucumber**: Ready-to-run Cucumber tests
- **Playwright**: Browser automation tests
- **pytest**: Python unit tests

## Best Practices

### Document Structure
1. **Clear Feature Title**: Use descriptive headings
2. **User Stories**: Follow "As a X, I want Y so that Z" format
3. **Acceptance Criteria**: Use bullet points with clear conditions
4. **Additional Context**: Include any relevant requirements

### Example Good Document
```markdown
# User Registration Feature

## User Story
As a new user, I want to create an account so that I can access the application.

## Acceptance Criteria
- User can enter email address
- User can create a secure password
- User must confirm email address
- User receives welcome email
- User can log in after registration

## Business Rules
- Email must be unique
- Password must be at least 8 characters
- Email confirmation required within 24 hours
```

### Example Bad Document
```markdown
# Feature
User registration

## Story
User wants to register

## Criteria
- Email
- Password
- Login
```

## Troubleshooting

### Common Issues

1. **"Invalid file format" error**
   - **Solution**: Only .md files are supported. Convert your document to Markdown format.

2. **"Document validation failed" error**
   - **Solution**: Check that your document has proper user stories and acceptance criteria.

3. **"LLM service unavailable" error**
   - **Solution**: Check your API keys and internet connection. Try the fallback provider.

4. **"No scenarios generated" error**
   - **Solution**: Ensure your document has clear user stories with acceptance criteria.

### Getting Help

- **Check logs**: Look at the application logs for detailed error messages
- **Try different providers**: Switch between Grok and Anthropic
- **Simplify document**: Start with a simple user story
- **Check format**: Ensure proper Markdown structure

## Next Steps

1. **Try different test types**: Experiment with unit, integration, and e2e tests
2. **Export to different formats**: See how scenarios look in different frameworks
3. **Use MCP integration**: Build external agents or automation
4. **Customize prompts**: Modify the LLM prompts for your domain

## Support

- **Documentation**: Check the implementation guide for technical details
- **Issues**: Report bugs and feature requests
- **Examples**: See the phase-specific implementation docs

Happy testing! 🧪