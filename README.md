
# AI Research Agent

Proyek ini berisi notebook, script, dan eksperimen untuk eksplorasi model dan agen (Hugging Face, Gradio, E2B, Deep Agents).

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
python -m venv .venv && source .venv/bin/activate
```

### Available Experiments

| Category | Notebook | Gradio App | Description |
|----------|----------|------------|-------------|
| **ML Basics** | [Image Classification](notebooks/image_classification.ipynb) | [gradio_image_classification.py](gradio/gradio_image_classification.py) | ViT image classification |
| | [Sentiment Analysis](notebooks/sentiment_analysis.ipynb) | [gradio_sentiment_analysis.py](gradio/gradio_sentiment_analysis.py) | Text sentiment analysis |
| | [Speech Recognition](notebooks/speech_recognition.ipynb) | [gradio_speech_recognition.py](gradio/gradio_speech_recognition.py) | Whisper speech-to-text |
| | [Summarization](notebooks/summarization.ipynb) | [gradio_summarization.py](gradio/gradio_summarization.py) | Text summarization |
| **AI Agents** | [Code Analysis](notebooks/code_analysis_agent.ipynb) | [gradio_code_analysis_repo.py](gradio/gradio_code_analysis_repo.py) | DeepAgents + FilesystemBackend |
| | [Deep Agents](notebooks/deep_agents_experiments.ipynb) | [gradio_deepagent_experiments.py](gradio/gradio_deepagent_experiments.py) | Agent architecture experiments |
| | [Code Repair Agent](-) | [gradio_code_repair_agent.py](gradio/gradio_code_repair_agent.py) | AI-powered code repair |
| | [E2B Code Runner](notebooks/e2b_sandbox_runner.ipynb) | [gradio_e2b_code_runner.py](gradio/gradio_e2b_code_runner.py) | Sandbox code execution |
| **Advanced** | [GPU Device](notebooks/gpu_device_notebook.ipynb) | [gradio_device_sentiment.py](gradio/gradio_device_sentiment.py) | Device detection |
| | [Spring Boot Generator](notebooks/spring_boot_generator.ipynb) | [gradio_springboot_generator.py](gradio/gradio_springboot_generator.py) | Live Spring Boot editor |
| | [Spring Boot Generator Fixed](notebooks/spring_boot_generator_fixed.ipynb) | - | Improved Spring Boot generator |

### Running Examples
```bash
# Basic ML demos
python gradio/gradio_image_classification.py
python gradio/gradio_sentiment_analysis.py

# AI Agents
python scripts/code_analysis.py --codebase-path /your/project
python gradio/gradio_code_analysis_repo.py
python gradio/gradio_deepagent_experiments.py
python gradio/gradio_code_repair_agent.py
python gradio/gradio_e2b_code_runner.py

# Advanced experiments
python gradio/gradio_device_sentiment.py
```

## 📚 Learning Path

Repositori ini dirancang sebagai **educational resource**. Ikuti progression dari basic ML sampai advanced AI agents:

**Level 1: ML Basics (2-3 jam)**
→ Hugging Face pipelines → Basic notebooks → Gradio interfaces

**Level 2: Agent Fundamentals (3-4 jam)**  
→ Deep Agents intro → Code analysis agent → FilesystemBackend

**Level 3: Advanced Execution (4-5 jam)**
→ E2B sandbox → Code execution → Template building

**Level 4: Agent Architecture (5-6 jam)**
→ Middleware → Multi-phase agents → Production patterns

**📖 Full Documentation**: [Learning Path Guide](notes/README.md) | [Category Indexes](notes/)

## 🛠️ Advanced Setup

### E2B Integration
```bash
pip install e2b e2b-code-interpreter
export E2B_API_KEY="your_key"
```

### Code Analysis Agent
```bash
pip install deepagents langchain-openai python-dotenv pydantic
export LITELLM_MODEL="gpt-4o-mini"
export LITELLM_VIRTUAL_KEY="your_key"
```

### Development
```bash
# GPU support (optional)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Model cache
export HF_TOKEN="your_huggingface_token"  # For private models
```

## Key Features

- **Educational Structure**: 5-level learning progression dari beginner sampai advanced
- **Production Ready**: LangChain DeepAgents, E2B sandbox, Hugging Face integration
- **Interactive Demos**: 10+ Gradio web interfaces untuk experimentation
- **Comprehensive Docs**: 25+ documentation files dengan cross-references
- **Modular Architecture**: Independent experiments yang bisa dijalankan separately

## Project Structure

```
├── notebooks/          # Jupyter notebooks (educational)
├── gradio/            # Interactive web demos
├── scripts/           # CLI tools & agents
├── dataset/           # Sample data & codebases
├── notes/             # Documentation (indexed by category)
└── requirements.txt   # Python dependencies
```

## Troubleshooting

- **Model Download Issues**: Check internet connection, use `HF_TOKEN` for private models
- **CUDA/GPU Problems**: Install CPU-only torch if GPU unavailable: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- **E2B Errors**: Verify `E2B_API_KEY` is set correctly
- **Memory Issues**: Use smaller models or reduce batch sizes in notebooks

## Roadmap

### Current Focus: Coding Agent Baseline
"Generate → Build → Test → Repair" automated pipeline:

- ✅ **Generate**: Feature request → code implementation (Phase 4 agent)
- 🚧 **Build**: Persistent sandbox dengan Maven cache (`~/.m2`)
- 🚧 **Test**: Automated testing dalam sandbox environment  
- 🚧 **Repair**: Error parsing → agent-driven fixes

### Target Components
- `build_and_test_once(sandbox, project_dir)` → structured results
- Maven error parser untuk compilation failures
- Repair loop: build → parse errors → agent fix → retry

## Contributing

Repository ini educational - contributions untuk:
- New experiment notebooks
- Documentation improvements  
- Bug fixes dan enhancements
- Additional model integrations

## License

Consider adding LICENSE and CONTRIBUTING.md for public sharing.
