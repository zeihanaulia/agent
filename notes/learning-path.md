# 📚 Complete Learning Path - AI Research Agent

**Educational progression from basic ML to production AI agents**

## 🎯 Overview

This repository follows a **chronological learning path** based on actual development timeline. Each phase builds upon previous knowledge, introducing new concepts and technologies progressively.

---

## 📅 Phase-by-Phase Learning Journey

### Phase 1: ML Basics (2-3 hours)
**Timeline**: Jan-Mar 2025  
**Goal**: Master Hugging Face pipelines and Gradio interfaces

#### Learning Objectives
- Understand transformer architecture basics
- Learn Hugging Face ecosystem (models, datasets, spaces)
- Build interactive web interfaces with Gradio
- Optimize model inference for production use

#### Key Concepts
- **Pipeline API**: `pipeline("task")` for quick inference
- **Model Hub**: Finding and using pre-trained models
- **Gradio Interface**: Building web demos in minutes
- **Model Optimization**: CPU/GPU usage, batch processing

#### Hands-on Projects
1. **[Image Classification](notebooks/image_classification.ipynb)**
   - ViT (Vision Transformer) implementation
   - Custom image preprocessing
   - Performance benchmarking

2. **[Sentiment Analysis](notebooks/sentiment_analysis.ipynb)**
   - Text classification pipelines
   - Multi-language support
   - Confidence scoring

3. **[Speech Recognition](notebooks/speech_recognition.ipynb)**
   - Whisper model integration
   - Audio preprocessing
   - Real-time transcription

4. **[Text Summarization](notebooks/summarization.ipynb)**
   - BART/T5 transformer models
   - Length control and quality metrics
   - Domain-specific summarization

#### Phase 1 Deliverables
- ✅ 4 working ML demos
- ✅ Gradio web interfaces
- ✅ Performance optimization techniques
- ✅ Model deployment patterns

---

### Phase 2: Agent Fundamentals (3-4 hours)
**Timeline**: Mar-Apr 2025  
**Goal**: Build intelligent agents with DeepAgents framework

#### Learning Objectives
- Understand agent architecture patterns
- Master filesystem operations for context management
- Implement multi-step reasoning workflows
- Debug and optimize agent performance

#### Key Concepts
- **DeepAgents Framework**: Multi-step reasoning agents
- **FilesystemBackend**: Persistent context management
- **Tool Integration**: LangChain built-in vs custom tools
- **Agent Debugging**: Temperature, prompts, error handling

#### Hands-on Projects
1. **[Code Analysis Agent](notebooks/code_analysis_agent.ipynb)**
   - Repository structure analysis
   - File content understanding
   - Pattern recognition in codebases

2. **[Deep Agents Experiments](notebooks/deep_agents_experiments.ipynb)**
   - Planning tool implementation
   - Sub-agent spawning patterns
   - Context persistence strategies

3. **[Code Repair Agent](gradio/gradio_code_repair_agent.py)**
   - Error detection and fixing
   - Code quality improvements
   - Automated refactoring

#### Phase 2 Deliverables
- ✅ DeepAgents integration
- ✅ FilesystemBackend migration
- ✅ Multi-step agent workflows
- ✅ Agent debugging techniques

---

### Phase 3: Advanced Execution (4-5 hours)
**Timeline**: Apr-May 2025  
**Goal**: Secure code execution with E2B sandbox

#### Learning Objectives
- Understand sandbox isolation concepts
- Implement secure code execution
- Build template-based development environments
- Stream processing and real-time feedback

#### Key Concepts
- **E2B Sandbox**: Isolated Python execution
- **Streaming Output**: Real-time result processing
- **Template Building**: Pre-configured environments
- **Resource Management**: CPU, memory, network quotas

#### Hands-on Projects
1. **[E2B Code Runner](notebooks/e2b_sandbox_runner.ipynb)**
   - Basic sandbox operations
   - Code execution patterns
   - Error handling in sandbox

2. **[Spring Boot Template Build](notes/e2b.experiment-template-build.md)**
   - Maven project setup
   - Dependency management
   - Build process automation

3. **[Live Build Preview](gradio/gradio_e2b_code_runner.py)**
   - Streaming build logs
   - Real-time status updates
   - Interactive development

#### Phase 3 Deliverables
- ✅ E2B sandbox integration
- ✅ Template-based builds
- ✅ Streaming execution
- ✅ Secure code isolation

---

### Phase 4: Feature Request Agent (5-6 hours)
**Timeline**: May-Jun 2025  
**Goal**: Automated feature implementation with middleware

#### Learning Objectives
- Design multi-layer security architecture
- Implement intent preservation middleware
- Build file scope guardrails
- Create comprehensive testing frameworks

#### Key Concepts
- **Middleware Architecture**: IntentReminder, FileScopeGuardrail, ToolCallValidation
- **Intent Preservation**: Maintaining feature requirements across agent calls
- **Scope Enforcement**: Preventing unauthorized file operations
- **Quality Assurance**: Automated testing and validation

#### Hands-on Projects
1. **[Spring Boot Generator](notebooks/spring_boot_generator.ipynb)**
   - Live code editing interface
   - Real-time syntax validation
   - Template-based generation

2. **[Middleware Implementation](notes/featurerequestagent.middleware-guide.md)**
   - 3-layer middleware stack
   - Guardrail patterns
   - Security validation

3. **[Feature Implementation Testing](notes/featurerequestagent.complete-test-summary.md)**
   - Comprehensive test suites
   - Success rate metrics
   - Performance benchmarking

#### Phase 4 Deliverables
- ✅ Middleware architecture
- ✅ 95%+ success rate improvement
- ✅ Secure feature implementation
- ✅ Comprehensive testing

---

### Phase 5: Production Architecture (6-7 hours)
**Timeline**: Jun-Nov 2025  
**Goal**: Enterprise-grade agent orchestration

#### Learning Objectives
- Master LangGraph workflow orchestration
- Implement architectural validation
- Build layered code generation
- Create end-to-end testing pipelines

#### Key Concepts
- **LangGraph Orchestration**: Multi-phase workflow management
- **Structure Validation**: Architectural compliance checking
- **Layered Generation**: Model, DTO, Service, Controller patterns
- **End-to-End Pipeline**: Generate → Build → Test → Repair

#### Hands-on Projects
1. **[LangGraph Workflow](scripts/feature_by_request_agent_v3.py)**
   - State management
   - Conditional routing
   - Error handling

2. **[Structure Validator](notes/codeanalysis.structure-validator-complete.md)**
   - Framework detection
   - Violation assessment
   - Compliance scoring

3. **[Layered Code Generation](notes/project.completion-summary.md)**
   - Spring Boot architecture
   - SOLID principles
   - Production-quality code

#### Phase 5 Deliverables
- ✅ LangGraph orchestration
- ✅ Architectural validation
- ✅ Layered code generation
- ✅ End-to-end pipeline

---

## 🛠️ Prerequisites by Phase

### Phase 1 Prerequisites
```bash
# Core ML libraries
pip install transformers torch torchvision torchaudio
pip install gradio pillow librosa

# Optional GPU support
pip install torch --index-url https://download.pytorch.org/whl/cu118

# Environment setup
export HF_TOKEN="your_huggingface_token"  # For private models
```

### Phase 2 Prerequisites
```bash
# Agent framework
pip install deepagents langchain-openai langchain-core
pip install python-dotenv pydantic

# Environment variables
export LITELLM_MODEL="gpt-4o-mini"
export LITELLM_VIRTUAL_KEY="your_api_key"
export LITELLM_API="your_api_base_url"
```

### Phase 3 Prerequisites
```bash
# E2B sandbox
pip install e2b e2b-code-interpreter

# Environment variables
export E2B_API_KEY="your_e2b_api_key"
```

### Phase 4 Prerequisites
```bash
# Middleware and advanced agents
pip install langchain langgraph
pip install fastapi uvicorn  # For advanced integrations
```

### Phase 5 Prerequisites
```bash
# Production orchestration
pip install langgraph langchain-core
pip install pytest pytest-asyncio  # For testing
pip install docker  # For containerization
```

---

## 📊 Learning Metrics

### Phase Completion Criteria

| Phase | Duration | Projects | Concepts | Success Criteria |
|-------|----------|----------|----------|------------------|
| **1** | 2-3h | 4 | 4 | Working ML demos |
| **2** | 3-4h | 3 | 4 | Agent workflows |
| **3** | 4-5h | 3 | 4 | Sandbox execution |
| **4** | 5-6h | 3 | 4 | Middleware security |
| **5** | 6-7h | 3 | 4 | Production pipeline |

### Knowledge Progression

```
Phase 1: ML Basics
         ↓
Phase 2: Agent Architecture (+filesystem, planning)
         ↓
Phase 3: Secure Execution (+sandbox, isolation)
         ↓
Phase 4: Feature Implementation (+middleware, guardrails)
         ↓
Phase 5: Production Orchestration (+validation, layered generation)
```

---

## 🎯 Getting Started

### Quick Start Path
1. **Start with Phase 1**: Run basic ML demos
2. **Progress naturally**: Each phase builds on previous
3. **Follow chronological order**: Don't skip phases
4. **Document your learning**: Take notes on concepts

### Recommended Pace
- **1 phase per week**: Allows deep understanding
- **Hands-on practice**: Run code, experiment, break things
- **Documentation review**: Read notes/ files for each phase
- **Community engagement**: Share learnings and challenges

### Learning Resources
- **[Phase Notes](notes/)**: Detailed documentation for each phase
- **[Code Examples](scripts/)**: Working implementations
- **[Interactive Demos](gradio/)**: Live experimentation
- **[Jupyter Notebooks](notebooks/)**: Step-by-step tutorials

---

## 🚀 Next Steps

### After Completing All Phases
1. **Build your own agent**: Combine concepts from all phases
2. **Contribute back**: Add new experiments or improvements
3. **Explore advanced topics**: Database integration, authentication
4. **Join the community**: Share your AI agent projects

### Advanced Learning Paths
- **Research Track**: Academic paper implementations
- **Enterprise Track**: Production deployment patterns
- **Innovation Track**: Novel agent architectures
- **Integration Track**: Third-party service integrations

---

**Last Updated**: November 5, 2025  
**Total Learning Time**: ~25-35 hours  
**Phases**: 5 chronological phases  
**Projects**: 15+ hands-on experiments