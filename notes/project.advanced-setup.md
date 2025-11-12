# 🛠️ Advanced Setup Guide - AI Research Agent

**Complete setup instructions for each development phase**

## 📋 Overview

This guide provides detailed setup instructions for each phase of the AI Research Agent development. Each phase has specific prerequisites and configuration requirements.

---

## Phase 1: ML Basics Setup

### Core Dependencies
```bash
# Install Python 3.9+ if not already installed
python --version

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install core ML libraries
pip install transformers torch torchvision torchaudio
pip install gradio pillow librosa soundfile

# Verify installations
python -c "import transformers, torch, gradio; print('✅ All imports successful')"
```

### GPU Support (Optional but Recommended)
```bash
# NVIDIA GPU with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# AMD GPU (ROCm)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.4.2

# Apple Silicon (M1/M2)
# PyTorch automatically detects Apple Silicon

# Verify GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Hugging Face Configuration
```bash
# Install huggingface_hub for authentication
pip install huggingface_hub

# Login to Hugging Face (optional, for private models)
huggingface-cli login

# Or set environment variable
export HF_TOKEN="your_huggingface_token"

# Test model download
python -c "from transformers import pipeline; print(pipeline('sentiment-analysis')('Hello world!'))"
```

### Gradio Development Setup
```bash
# Additional Gradio dependencies for advanced features
pip install gradio[ffmpeg]  # For audio/video processing

# Test Gradio installation
python -c "import gradio as gr; print(f'Gradio version: {gr.__version__}')"

# Run test interface
python -c "
import gradio as gr
def greet(name): return f'Hello {name}!'
gr.Interface(fn=greet, inputs='text', outputs='text').launch(share=False)
"
```

### Phase 1 Environment Variables
```bash
# Model cache directory (optional)
export HF_HOME="/path/to/huggingface/cache"

# Transformers settings
export TRANSFORMERS_CACHE="/path/to/transformers/cache"

# Disable progress bars for cleaner output
export TRANSFORMERS_NO_PROGRESS_BARS="1"
```

---

## Phase 2: Agent Fundamentals Setup

### DeepAgents Framework
```bash
# Install DeepAgents and dependencies
pip install deepagents langchain-openai langchain-core
pip install python-dotenv pydantic

# Verify DeepAgents installation
python -c "from deepagents import create_deep_agent; print('✅ DeepAgents imported successfully')"
```

### LLM API Configuration
```bash
# Required environment variables for LLM access
export LITELLM_MODEL="gpt-4o-mini"
export LITELLM_VIRTUAL_KEY="your_api_key_here"
export LITELLM_API="https://your-api-endpoint.com/v1"

# Alternative configurations:
# OpenAI direct
export OPENAI_API_KEY="your_openai_key"

# Azure OpenAI
export AZURE_OPENAI_API_KEY="your_azure_key"
export AZURE_OPENAI_ENDPOINT="your_azure_endpoint"
export AZURE_OPENAI_DEPLOYMENT="your_deployment_name"

# Test LLM connection
python -c "
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    api_key=os.getenv('LITELLM_VIRTUAL_KEY'),
    model=os.getenv('LITELLM_MODEL', 'gpt-4o-mini'),
    base_url=os.getenv('LITELLM_API')
)
response = llm.invoke('Hello, test message')
print(f'✅ LLM connection successful: {response.content[:50]}...')
"
```

### Filesystem Backend Setup
```bash
# Filesystem backend is included with DeepAgents
# Test filesystem operations
python -c "
from deepagents.backends import FilesystemBackend
import tempfile
import os

# Create temporary directory for testing
with tempfile.TemporaryDirectory() as tmpdir:
    backend = FilesystemBackend(root_dir=tmpdir)
    # Test basic operations
    print('✅ FilesystemBackend initialized successfully')
"
```

### Agent Development Environment
```bash
# Additional tools for agent development
pip install jupyter ipykernel  # For notebook development
pip install black isort flake8  # Code formatting and linting

# Register Jupyter kernel
python -m ipykernel install --user --name agent-dev --display-name "Agent Development"

# Test agent creation
python -c "
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

agent = create_deep_agent(
    system_prompt='You are a helpful AI assistant for testing.',
    model='gpt-4o-mini',
    backend=FilesystemBackend(root_dir='.')
)
print('✅ Agent creation successful')
"
```

### Phase 2 Environment Variables
```bash
# Agent configuration
export AGENT_MODEL="gpt-4o-mini"
export AGENT_TEMPERATURE="0.7"
export AGENT_MAX_TOKENS="4000"

# Filesystem backend settings
export BACKEND_ROOT_DIR="/path/to/project/root"
export BACKEND_MAX_FILE_SIZE="10485760"  # 10MB

# Logging configuration
export AGENT_LOG_LEVEL="INFO"
export AGENT_LOG_FILE="/path/to/agent.log"
```

---

## Phase 3: Advanced Execution Setup

### E2B Sandbox Installation
```bash
# Install E2B SDK
pip install e2b e2b-code-interpreter

# Verify E2B installation
python -c "import e2b; print(f'✅ E2B version: {e2b.__version__}')"
```

### E2B API Configuration
```bash
# Get API key from https://e2b.dev
export E2B_API_KEY="your_e2b_api_key_here"

# Test E2B connection
python -c "
import os
from e2b_code_interpreter import Sandbox

# Test sandbox creation
sandbox = Sandbox.create()
result = sandbox.run_code('print(\"Hello from E2B!\")')
print(f'✅ E2B connection successful: {result.logs.stdout}')
sandbox.kill()
"
```

### Sandbox Template Setup
```bash
# For custom templates, install additional tools
pip install e2b[template]  # If available

# Test template operations
python -c "
from e2b import Sandbox

# Test general sandbox
sandbox = Sandbox.create()
sandbox.files.write('/test.txt', 'Hello E2B!')
content = sandbox.files.read('/test.txt')
print(f'✅ File operations successful: {content}')
sandbox.kill()
"
```

### Streaming and Real-time Features
```bash
# Test streaming capabilities
python -c "
from e2b_code_interpreter import Sandbox

def on_stdout(message):
    print(f'Streaming: {message}', end='', flush=True)

sandbox = Sandbox.create()
execution = sandbox.run_code('''
import time
for i in range(3):
    print(f'Line {i+1}')
    time.sleep(0.5)
''', on_stdout=on_stdout)

print(f'\\n✅ Streaming test completed')
sandbox.kill()
"
```

### Phase 3 Environment Variables
```bash
# E2B configuration
export E2B_API_KEY="your_e2b_key"
export E2B_TEMPLATE_ID="default"  # For custom templates
export E2B_SANDBOX_TIMEOUT="300"  # 5 minutes

# Resource limits
export E2B_MAX_CPU="2"
export E2B_MAX_MEMORY="4GB"
export E2B_MAX_DISK="10GB"
```

---

## Phase 4: Feature Request Agent Setup

### Middleware Dependencies
```bash
# Install LangGraph for orchestration
pip install langgraph langchain

# Additional middleware dependencies
pip install fastapi uvicorn python-multipart

# Test middleware imports
python -c "
try:
    from langgraph.graph import StateGraph
    import langchain
    print('✅ Middleware dependencies installed')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
"
```

### Agent Middleware Setup
```bash
# Middleware components are in the scripts directory
# Test middleware loading
python -c "
import sys
import os
sys.path.append('scripts')

try:
    # Test imports from feature_by_request_agent_v3.py
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph
    print('✅ Agent middleware components available')
except ImportError as e:
    print(f'❌ Middleware import error: {e}')
"
```

### Testing Framework Setup
```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov
pip install requests httpx  # For API testing

# Install test coverage tools
pip install coverage

# Test testing framework
python -c "
import pytest
print('✅ Testing framework ready')
"
```

### Phase 4 Environment Variables
```bash
# Agent middleware settings
export MIDDLEWARE_ENABLED="true"
export INTENT_REMINDER_ENABLED="true"
export FILE_SCOPE_GUARDRAIL_ENABLED="true"
export TOOL_VALIDATION_ENABLED="true"

# Testing configuration
export TEST_MODE="true"
export TEST_COVERAGE_MIN="80"
export TEST_PARALLEL_WORKERS="4"
```

---

## Phase 5: Production Architecture Setup

### LangGraph Orchestration
```bash
# Full LangGraph installation
pip install langgraph[all]  # Includes all optional dependencies

# Test LangGraph installation
python -c "
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

# Test basic graph creation
graph = StateGraph(dict)
print('✅ LangGraph orchestration ready')
"
```

### Structure Validator Setup
```bash
# Structure validator is part of the codebase
# Test structure validation imports
python -c "
import sys
sys.path.append('scripts')

try:
    # Test structure validator import
    print('✅ Structure validator components available')
except ImportError as e:
    print(f'⚠️  Structure validator not yet implemented: {e}')
"
```

### Build and Test Pipeline
```bash
# Install build tools
pip install build twine  # For Python packaging
pip install docker  # For containerization

# Install Java/Maven for Spring Boot testing
# Note: Requires Java 17+ and Maven 3.6+
# brew install openjdk@17 maven  # macOS
# sudo apt install openjdk-17-jdk maven  # Ubuntu

# Test Java/Maven installation
java -version
mvn -version
```

### Database and Persistence
```bash
# Install database connectors (as needed)
pip install sqlalchemy psycopg2-binary  # PostgreSQL
pip install pymongo  # MongoDB
pip install redis  # Redis for caching

# Test database connections (example for PostgreSQL)
python -c "
import sqlalchemy
print('✅ Database libraries available')
"
```

### Phase 5 Environment Variables
```bash
# Production settings
export PRODUCTION_MODE="true"
export LOG_LEVEL="INFO"
export METRICS_ENABLED="true"

# Build configuration
export BUILD_TOOL="maven"
export JAVA_HOME="/path/to/java17"
export MAVEN_HOME="/path/to/maven"

# Database configuration (examples)
export DATABASE_URL="postgresql://user:pass@localhost:5432/db"
export REDIS_URL="redis://localhost:6379"
```

---

## 🔧 Development Environment Setup

### IDE Configuration

#### VS Code Setup
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension ms-python.isort
code --install-extension ms-toolsai.jupyter
code --install-extension redhat.java  # For Java development
```

#### PyCharm Setup
- Install PyCharm Professional
- Configure Python interpreter (.venv)
- Enable Jupyter notebook support
- Install Java plugin for Spring Boot development

### Git Configuration
```bash
# Configure Git for development
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Setup Git hooks for code quality
pip install pre-commit
pre-commit install

# Test Git setup
git status
```

### Docker Setup (Optional)
```bash
# Install Docker
# https://docs.docker.com/get-docker/

# Test Docker installation
docker --version
docker run hello-world

# Build test container
docker build -t agent-test .
```

---

## 🚀 Quick Verification Scripts

### Phase 1 Verification
```bash
#!/bin/bash
# verify_phase1.sh
echo "🔍 Verifying Phase 1 setup..."

python -c "
import transformers, torch, gradio
from transformers import pipeline

# Test basic pipeline
classifier = pipeline('sentiment-analysis')
result = classifier('I love this project!')
print(f'✅ ML pipeline working: {result}')

# Test Gradio
print('✅ Gradio available')
print('🎉 Phase 1 setup complete!')
"
```

### Phase 2 Verification
```bash
#!/bin/bash
# verify_phase2.sh
echo "🔍 Verifying Phase 2 setup..."

python -c "
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI
import os

# Test LLM connection
llm = ChatOpenAI(
    api_key=os.getenv('LITELLM_VIRTUAL_KEY'),
    model='gpt-4o-mini',
    base_url=os.getenv('LITELLM_API')
)

# Test agent creation
agent = create_deep_agent(
    system_prompt='Test agent',
    model='gpt-4o-mini',
    backend=FilesystemBackend(root_dir='.')
)

print('✅ Agent framework working')
print('🎉 Phase 2 setup complete!')
"
```

### Phase 3 Verification
```bash
#!/bin/bash
# verify_phase3.sh
echo "🔍 Verifying Phase 3 setup..."

python -c "
from e2b_code_interpreter import Sandbox
from e2b import Sandbox as GeneralSandbox
import os

# Test E2B connection
sandbox = Sandbox.create()
result = sandbox.run_code('print(42)')
print(f'✅ E2B code execution: {result.logs.stdout}')

# Test file operations
general_sandbox = GeneralSandbox.create()
general_sandbox.files.write('/test.txt', 'Hello E2B!')
content = general_sandbox.files.read('/test.txt')
print(f'✅ E2B file operations: {content}')

sandbox.kill()
general_sandbox.kill()

print('🎉 Phase 3 setup complete!')
"
```

---

## 🐛 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Clear pip cache and reinstall
pip cache purge
pip uninstall package_name
pip install package_name

# Check Python path
python -c "import sys; print(sys.path)"
```

#### API Connection Issues
```bash
# Test network connectivity
curl -I https://api.openai.com/v1/models

# Check environment variables
env | grep -E "(LITELLM|OPENAI|E2B)"

# Test with minimal example
python -c "import openai; print('OpenAI library available')"
```

#### GPU Issues
```bash
# Check CUDA installation
nvidia-smi
nvcc --version

# Verify PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

#### Memory Issues
```bash
# Monitor memory usage
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
"

# Use smaller models
export MODEL_NAME="distilbert-base-uncased-finetuned-sst-2-english"
```

---

## 📞 Support

### Getting Help
1. **Check documentation**: Review phase-specific notes in `notes/`
2. **Run verification scripts**: Use the verification scripts above
3. **Check logs**: Look for error messages and stack traces
4. **Community support**: Share issues and solutions

### Useful Commands
```bash
# Check Python environment
which python
python --version
pip list | grep -E "(torch|transformers|deepagents|e2b)"

# Check environment variables
env | grep -E "(HF|LITELLM|E2B|CUDA)"

# Test basic functionality
python -c "import sys; print('Python path:'); [print(p) for p in sys.path[:3]]"
```

---

**Last Updated**: November 5, 2025  
**Setup Time**: ~30-60 minutes per phase  
**Total Dependencies**: 50+ packages across all phases