# Getting Started Guide

## Prerequisites

### System Requirements
- **Operating System**: macOS, Linux, or Windows with WSL
- **Python**: 3.9 or higher
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 2GB free space for dependencies and models

### Required API Keys
- **OpenAI API Key**: For LLM operations (GPT-4 recommended)
- **Anthropic API Key** (Optional): For Claude models  
- **Tavily API Key**: For research integration

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/agnostic-coding-agent.git
cd agnostic-coding-agent
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install additional tree-sitter parsers
python scripts/setup/install_parsers.py
```

### 4. Configure Environment

Create `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# Required: OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Optional: Anthropic Configuration  
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-opus-20240229

# Required: Research Integration
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: LangGraph Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_PROJECT=agnostic-agent

# System Configuration
LOG_LEVEL=INFO
MAX_CONTEXT_SIZE=8192
ENABLE_RESEARCH=true
ENABLE_MULTI_AGENT=true
```

### 5. Verify Installation

```bash
# Test basic functionality
python scripts/test/verify_installation.py

# Expected output:
# ✅ Virtual environment: Active
# ✅ Dependencies: Installed
# ✅ Tree-sitter parsers: Available
# ✅ API keys: Configured
# ✅ System: Ready
```

## Quick Start

### Example 1: Java Spring Boot Feature

Let's add a new REST endpoint to an existing Spring Boot project:

```bash
# 1. Navigate to your project
cd /path/to/your/springboot/project

# 2. Create feature specification
cat > new-endpoint-spec.md << 'EOF'
# User Profile Management API

## Feature Request
Add a REST API endpoint for user profile management with the following capabilities:

1. **Get User Profile** - GET /api/users/{id}/profile
2. **Update User Profile** - PUT /api/users/{id}/profile  
3. **Upload Profile Picture** - POST /api/users/{id}/profile/avatar

## Requirements
- Follow Spring Boot REST conventions
- Include proper validation and error handling
- Add comprehensive unit tests
- Use JPA entities for data persistence
- Include Swagger documentation

## Data Model
```json
{
  "id": "string",
  "firstName": "string", 
  "lastName": "string",
  "email": "string",
  "bio": "string",
  "avatarUrl": "string",
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```
EOF

# 3. Run the agnostic agent
source .venv/bin/activate
python scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path . \
  --feature-request-spec new-endpoint-spec.md
```

**Expected Output**:
```
🔍 Analyzing project structure...
   ✅ Detected: Java Spring Boot with Maven
   ✅ Architecture: Layered (Controller-Service-Repository)
   ✅ Dependencies: Spring Web, JPA, Validation

🧠 Parsing feature specification...
   ✅ Requirements extracted: 3 endpoints, validation, testing
   ✅ Research completed: Spring Boot REST best practices
   ✅ Templates selected: Spring Controller, JPA Entity, Test Suite

🛠️  Synthesizing code...
   ✅ Generated: UserProfileController.java
   ✅ Generated: UserProfile.java (Entity)
   ✅ Generated: UserProfileService.java  
   ✅ Generated: UserProfileRepository.java
   ✅ Generated: UserProfileControllerTest.java
   ✅ Updated: application.yml (database configuration)

📁 Files placed according to Maven conventions:
   src/main/java/com/example/controller/UserProfileController.java
   src/main/java/com/example/entity/UserProfile.java
   src/main/java/com/example/service/UserProfileService.java
   src/main/java/com/example/repository/UserProfileRepository.java
   src/test/java/com/example/controller/UserProfileControllerTest.java

🎉 Feature implementation complete!
```

### Example 2: Python FastAPI Feature

Adding a similar feature to a FastAPI project:

```bash
# 1. Create FastAPI feature spec
cat > fastapi-user-spec.md << 'EOF'  
# User Management FastAPI Service

## Feature Request
Create a user management service with FastAPI including:

1. User CRUD operations
2. Pydantic models for validation  
3. SQLAlchemy integration
4. Automatic API documentation
5. Authentication middleware

## Technical Requirements
- Use async/await patterns
- Include proper type hints
- Add comprehensive error handling
- Include pytest test suite
- Follow FastAPI best practices
EOF

# 2. Run on FastAPI project
python scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path ./my-fastapi-project \
  --feature-request-spec fastapi-user-spec.md
```

**Expected Output**:
```
🔍 Analyzing project structure...
   ✅ Detected: Python FastAPI with Poetry
   ✅ Architecture: Clean Architecture (Domain-Service-Repository)
   ✅ Dependencies: FastAPI, SQLAlchemy, Pydantic

🧠 Parsing feature specification...
   ✅ Requirements extracted: CRUD operations, async patterns
   ✅ Research completed: FastAPI async best practices
   ✅ Templates selected: FastAPI Router, Pydantic Models, SQLAlchemy

🛠️  Synthesizing code...
   ✅ Generated: user_router.py
   ✅ Generated: user_models.py (Pydantic)
   ✅ Generated: user_schema.py (SQLAlchemy)
   ✅ Generated: user_service.py
   ✅ Generated: test_user_router.py

📁 Files placed according to FastAPI conventions:
   app/routers/user_router.py
   app/models/user_models.py
   app/schemas/user_schema.py
   app/services/user_service.py
   tests/test_user_router.py

🎉 Feature implementation complete!
```

## Understanding the Output

### Project Analysis
The agent automatically detects:
- **Framework**: Spring Boot, FastAPI, Express.js, etc.
- **Build System**: Maven, Gradle, Poetry, npm, etc.  
- **Architecture Pattern**: Layered, Clean, Hexagonal, etc.
- **Dependencies**: Available libraries and versions

### Code Generation
For each feature request, the agent generates:
- **Main Implementation**: Controllers, routers, handlers
- **Data Models**: Entities, schemas, DTOs
- **Business Logic**: Services, use cases, domain logic
- **Data Access**: Repositories, DAOs, database integration
- **Tests**: Unit tests, integration tests, mocks
- **Configuration**: Application settings, database config

### File Organization
Files are automatically placed following framework conventions:
- **Java/Maven**: `src/main/java/package/structure/`
- **Python**: `app/`, `src/`, or project-specific structure
- **Node.js**: `src/`, `lib/`, or package-specific structure

## Common Use Cases

### 1. Adding New Features
```bash
# Any framework - same command structure
python scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path /path/to/project \
  --feature-request-spec /path/to/feature-spec.md
```

### 2. Cross-Framework Migration
```bash
# Generate equivalent feature for different framework
python scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path /path/to/new/framework/project \
  --feature-request-spec same-feature-spec.md
```

### 3. Learning New Frameworks
```bash
# Study generated code to understand framework patterns
python scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path /path/to/sample/project \
  --feature-request-spec learning-spec.md \
  --explain-patterns
```

## Tips for Success

### Writing Effective Specifications
1. **Be Specific**: Include exact requirements, data models, and constraints
2. **Provide Context**: Mention existing patterns and conventions to follow
3. **Include Examples**: Show expected inputs/outputs and API contracts
4. **Specify Testing**: Mention required test coverage and scenarios

### Working with Generated Code
1. **Review First**: Always review generated code before integration
2. **Test Thoroughly**: Run all generated tests and add additional ones
3. **Customize**: Adapt generated code to specific project needs
4. **Learn**: Study patterns to improve your own coding practices

### Troubleshooting
- **Check Logs**: Review `logs/agent-execution.log` for detailed information
- **Verify Setup**: Ensure all API keys and dependencies are correctly configured
- **Update Dependencies**: Keep tree-sitter parsers and models up to date
- **Report Issues**: Use GitHub issues for bugs and feature requests

## Next Steps

Now that you've completed the basic setup:

1. **Explore Examples**: Review [framework-specific examples](java-springboot-examples.md)
2. **Learn Specification Writing**: Read [Specification Writing Guide](specification-writing-guide.md)
3. **Understand Architecture**: Study [Architecture Guide](architecture-guide.md)
4. **Customize Configuration**: See [Configuration Options](configuration-options.md)
5. **Integrate with Workflow**: Check [Framework Integration Guide](framework-integration-guide.md)

## Support and Community

- **Documentation**: Complete guides available in `notes/` directory
- **Examples**: Sample projects and specifications in `dataset/` directory
- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions for tips and best practices

---

*You're now ready to use the Framework-Agnostic Coding Agent with any supported technology stack!*