# 🤖 Code Analysis Agent - Integration Guide

## 📝 Overview

Transformation dari `scripts/code_analysis.py` (CLI script) menjadi `gradio/gradio_code_analysis_repo.py` (Web UI dengan Git integration).

## 🔄 Transformation Summary

### Apa yang berubah?

| Aspek | Original (`code_analysis.py`) | New (`gradio_code_analysis_repo.py`) |
|-------|------|------|
| **Interface** | Command-line (argparse) | Web UI (Gradio) |
| **Repository Input** | Manual path via `--codebase-path` | URL input + auto-clone |
| **Git Integration** | None | Full git clone support |
| **Workspace** | Any directory | Centralized `/dataset/codes/` |
| **Result Display** | STDOUT + formatted text | Gradio UI with status updates |
| **Error Handling** | Try-catch + sys.exit | Gradio error display + continue |
| **Progress Tracking** | Timestamps + prints | Real-time progress bar |

### Apa yang sama?

- ✅ Sama AI model configuration (ChatOpenAI)
- ✅ Sama FilesystemBackend usage
- ✅ Sama analysis prompt dan workflow
- ✅ Sama built-in tools (ls, read_file, glob, grep, etc.)
- ✅ Sama result extraction logic
- ✅ Sama environment variable handling (.env)

## 🎯 Key New Features

### 1. Repository URL Input
```
https://github.com/user/repo.git
https://gitlab.com/user/repo
git@github.com:user/repo.git
```
✅ Automatic validation dan clone

### 2. Workspace Management
```
/dataset/codes/
├── repo1-name/
├── repo2-name/
└── repo3-name/
```
✅ Centralized, shareable workspace

### 3. Smart Codebase Selection
- **Dropdown**: Pilih dari cloned repos
- **Custom Path**: Input path manual jika perlu

### 4. Multi-Step Workflow
```
Step 1: Clone Repository
  ↓
Step 2: Select Codebase  
  ↓
Step 3: Run Analysis
  ↓
View Results
```

## 🚀 Quick Start

### 1. Setup (first time only)

```bash
cd /Users/zeihanaulia/Programming/research/agent

# Optional: create .env if not exists
cp .env.example .env
# Edit .env dengan credentials Anda
```

### 2. Run App

```bash
# Option A: Using bash script (recommended)
./gradio/start_app.sh

# Option B: Manual
source .venv/bin/activate
python gradio/gradio_code_analysis_repo.py
```

### 3. Open Browser
```
http://localhost:7860
```

### 4. Use the App
1. **Clone Tab**: Paste repository URL → Click "🔄 Clone"
2. **Select Tab**: Choose from dropdown or enter custom path
3. **Analyze Tab**: Click "🚀 Run Analysis"
4. **View Results**: See comprehensive analysis

## 📂 File Structure

```
agent/
├── .env                                   # Credentials (gitignored)
├── .env.example                           # Template
├── requirements.txt                       # All dependencies
│
├── scripts/
│   └── code_analysis.py                  # Original CLI version
│
├── gradio/
│   ├── gradio_code_analysis_repo.py      # NEW: Main Gradio app
│   ├── README_CODE_ANALYSIS.md           # NEW: Full documentation
│   ├── start_app.sh                      # NEW: Bash launcher
│   ├── [other-gradio-apps]/              # Existing apps
│   └── __pycache__/
│
├── dataset/
│   └── codes/
│       ├── casdoor/                      # Cloned repo 1
│       ├── deepagents/                   # Cloned repo 2
│       ├── springboot-demo/              # Cloned repo 3
│       └── [new-clones]/                 # Future clones
│
└── notebooks/
    └── code_analysis_agent.ipynb         # Related notebook
```

## 🔗 Component Architecture

### Gradio App Flow

```
┌─────────────────────────────────────────────────────────┐
│                   GRADIO UI FRONTEND                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Clone      │  │   Select     │  │   Analyze    │   │
│  │ Repository   │→ │  Codebase    │→ │  & Display   │   │
│  │   Form       │  │   Dropdown   │  │   Results    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────────┐
│                   BACKEND SERVICES                        │
│  ┌────────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Clone Engine   │  │ Workspace  │  │   Analysis   │  │
│  │                │  │  Manager   │  │   Engine     │  │
│  │ - Git URL      │  │            │  │              │  │
│  │ - Clone        │  │ - List     │  │ - AI Model   │  │
│  │ - Validate     │  │ - Select   │  │ - FilesysBE  │  │
│  │ - Error handle │  │ - Track    │  │ - Agent Inv. │  │
│  └────────────────┘  └────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────────┐
│              EXTERNAL RESOURCES                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐    │
│  │  Git Repos  │  │   Local     │  │   LLM API    │    │
│  │             │  │ Filesystem  │  │              │    │
│  │ github.com  │  │  /dataset   │  │ openai/groq  │    │
│  │ gitlab.com  │  │  /codes     │  │ /v1/chat     │    │
│  └─────────────┘  └─────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input (URL)
    ↓
clone_repository()
    ├─ validate_git_url()
    ├─ extract_repo_name()
    ├─ subprocess.run(git clone)
    └─ Return local_path
    ↓
list_available_codebases()
    ├─ Scan /dataset/codes/
    ├─ Find .git directories
    └─ Return sorted list
    ↓
run_code_analysis(codebase_path)
    ├─ validate_environment() [API keys]
    ├─ ChatOpenAI(api_key, model, base_url, temperature)
    ├─ FilesystemBackend(root_dir=codebase_path)
    ├─ create_deep_agent(prompt, model, backend)
    ├─ agent.invoke() [AI analysis]
    └─ Extract & format results
    ↓
Gradio UI Display
```

## 🛠️ Key Functions Breakdown

### Clone Engine (`clone_repository`)
```python
Input:  repo_url = "https://github.com/user/repo.git"
        ↓
1. validate_git_url()        # Check URL format
2. extract_repo_name()       # Get "repo" from URL
3. Check if already cloned   # Avoid duplicates
4. subprocess.run("git clone")
        ↓
Output: (success, message, local_path)
```

### Analysis Engine (`run_code_analysis`)
```python
Input:  codebase_path = "/dataset/codes/repo"
        ↓
1. validate_environment()           # Check API keys
2. Configure AI Model (ChatOpenAI)  # Model setup
3. FilesystemBackend(root_dir)      # Sandbox access
4. create_deep_agent()              # Create agent
5. agent.invoke()                   # Run analysis
6. Extract final message            # Get results
        ↓
Output: (success, formatted_result)
```

### Gradio Interface (`create_gradio_interface`)
```python
Creates 3 event handlers:
1. clone_btn.click()          → clone_repo_handler()
2. refresh_btn.click()        → refresh_list_handler()
3. analyze_btn.click()        → analyze_handler()

Plus on_load() to initialize dropdown
```

## 🔐 Security Considerations

### Path Sandboxing
- FilesystemBackend validates `root_dir`
- Agent only accesses files under codebase_path
- Symlink traversal prevented

### API Credentials
```python
# Secure handling
api_key = os.getenv("LITELLM_VIRTUAL_KEY")  # From .env
SecretStr(api_key)  # Pydantic secure wrapper
```

### URL Validation
```python
# Validates Git URL patterns
github.com, gitlab.com, gitea, git@, .git
```

### Error Isolation
- Clone failures don't crash app
- Analysis errors return error message + continue
- Gradio displays errors gracefully

## 📊 Usage Examples

### Example 1: Clone & Analyze Public Repo

```
1. Paste: https://github.com/fastapi/fastapi.git
2. Click: 🔄 Clone Repository
3. Wait for: ✅ Successfully cloned to: /dataset/codes/fastapi
4. Dropdown auto-updates, select: /dataset/codes/fastapi
5. Click: 🚀 Run Analysis
6. View comprehensive analysis (architecture, tech stack, etc.)
```

### Example 2: Analyze Existing Local Repo

```
1. Skip clone step
2. Manual path: /Users/user/my-project
3. Click: 🚀 Run Analysis
4. Get analysis without cloning
```

### Example 3: Batch Analyze Multiple Repos

```python
# Use Python script to extend functionality
from gradio_code_analysis_repo import run_code_analysis

repos = [
    "/dataset/codes/fastapi",
    "/dataset/codes/django",
    "/dataset/codes/flask"
]

for repo_path in repos:
    success, result = run_code_analysis(repo_path)
    if success:
        print(f"\n{repo_path}:\n{result}")
```

## 🐛 Troubleshooting

### Issue: "Missing LITELLM_VIRTUAL_KEY"
**Solution**: 
```bash
# Create .env
LITELLM_VIRTUAL_KEY=sk-xxx...
LITELLM_API=https://api.openai.com/v1
```

### Issue: "Failed to clone repository"
**Solution**:
```bash
# Test manual clone
git clone https://github.com/user/repo.git /tmp/test-repo

# Check network
ping github.com
```

### Issue: Analysis hangs
**Solution**:
- Use faster model (gpt-4o-mini vs gpt-4)
- Analyze smaller repo
- Check LLM API status

## 🔄 Migration Checklist

- [x] Create Gradio app wrapper
- [x] Add git clone functionality
- [x] Implement workspace management
- [x] Add URL validation
- [x] Handle errors gracefully
- [x] Create documentation
- [x] Test imports
- [x] Create launcher script
- [x] Add progress tracking
- [x] Verify security

## 📚 Next Steps / Future Enhancements

### Phase 2 Features
- [ ] **Batch Analysis**: Analyze multiple repos in parallel
- [ ] **Result Export**: Save analysis to markdown/PDF
- [ ] **Comparison**: Side-by-side repo analysis
- [ ] **Scheduling**: Scheduled analysis jobs
- [ ] **Webhooks**: GitHub/GitLab integration

### Phase 3 Integration
- [ ] **Docker**: Containerize app
- [ ] **CI/CD**: GitHub Actions workflow
- [ ] **Database**: Store analysis history
- [ ] **API**: REST API for programmatic access
- [ ] **Auth**: Multi-user support

## 📖 Related Resources

### Original Script
- File: `scripts/code_analysis.py`
- Documentation: Inline docstrings
- CLI: `python scripts/code_analysis.py --codebase-path /path`

### Jupyter Notebook
- File: `notebooks/code_analysis_agent.ipynb`
- Type: Educational walkthrough
- Use: Learn step-by-step how it works

### Gradio App (NEW)
- File: `gradio/gradio_code_analysis_repo.py`
- Type: Web UI with git integration
- Use: User-friendly repository analysis

### Documentation
- `gradio/README_CODE_ANALYSIS.md` - Full user guide
- `gradio/start_app.sh` - Quick launcher
- This file - Architecture & integration

## ✅ Verification Checklist

Before using in production:

- [ ] `.env` configured with valid API keys
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Git installed and accessible (`which git`)
- [ ] Network connectivity to GitHub/GitLab/API
- [ ] `/dataset/codes/` directory writable
- [ ] Test clone small repo successfully
- [ ] Test analysis on small repo completes
- [ ] Results display correctly in UI

## 🎓 Learning Path

1. **Start with CLI**: Run `scripts/code_analysis.py` to understand flow
2. **Study Notebook**: Walk through `notebooks/code_analysis_agent.ipynb`
3. **Explore Gradio App**: Use `gradio/gradio_code_analysis_repo.py`
4. **Customize**: Extend with your own features

## 📞 Support

For issues or questions:
1. Check Troubleshooting section
2. Review error messages in console
3. Check `.env` configuration
4. Verify network connectivity
5. Test individual components

---

**Version**: 1.0
**Last Updated**: November 3, 2025
**Status**: Production Ready ✅
