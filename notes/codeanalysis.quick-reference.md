# 🚀 Quick Reference - Code Analysis Gradio App

## One-Line Start
```bash
cd /Users/zeihanaulia/Programming/research/agent && ./gradio/start_app.sh
```

## Browser
```
http://localhost:7860
```

---

## 3-Step Usage

### Step 1: Clone Repository
```
Paste URL: https://github.com/user/repo.git
Click: 🔄 Clone Repository
Wait: ✅ Successfully cloned to: /dataset/codes/repo
```

### Step 2: Select Codebase + Analysis Mode
```
Choose from dropdown: /dataset/codes/repo
Select analysis mode:
  🚀 Fast (Summary) - 30-50 sec
  📊 Detailed (Full) - 1-3 min [default]
```

### Step 3: Analyze
```
Click: 🚀 Run Analysis
Wait: 30-180 seconds (depends on mode)
View: Comprehensive analysis results
```

---

## Analysis Modes

| Mode | Speed | Details | Best For |
|------|-------|---------|----------|
| 🚀 Fast | 30-50s | Summary | Quick overview |
| 📊 Detailed | 1-3m | Comprehensive | Deep analysis |

**Fast Mode**: Project name, tech stack, main components  
**Detailed Mode**: Full architecture, dependencies, all components

📖 **Full guide**: See `ANALYSIS_MODES.md`

---

## Supported URLs

✅ GitHub HTTPS
```
https://github.com/user/repo.git
https://github.com/user/repo
```

✅ GitHub SSH
```
git@github.com:user/repo.git
```

✅ GitLab
```
https://gitlab.com/user/repo.git
```

✅ Gitea
```
https://gitea.example.com/user/repo.git
```

---

## Workspace

All clones go to:
```
/Users/zeihanaulia/Programming/research/agent/dataset/codes/
```

List cloned repos:
```bash
ls /Users/zeihanaulia/Programming/research/agent/dataset/codes/
```

---

## Requirements

✅ `.env` with API keys:
```
LITELLM_VIRTUAL_KEY=<your-key>
LITELLM_API=<api-url>
```

✅ Python 3.10+  
✅ Virtual environment active  
✅ `pip install -r requirements.txt` (done)  
✅ Git installed  

---

## Files

| File | Purpose |
|------|---------|
| `gradio/gradio_code_analysis_repo.py` | Main app |
| `gradio/README_CODE_ANALYSIS.md` | Full docs |
| `gradio/start_app.sh` | Launcher |
| `INTEGRATION_GUIDE.md` | Architecture |
| `COMPLETION_SUMMARY.md` | Overview |

---

## Troubleshooting

**"Missing API key"**
→ Update `.env` with credentials

**"Clone failed"**
→ Check git: `which git`  
→ Test network: `ping github.com`

**"Analysis stuck"**
→ Use faster model in `.env`

---

## Architecture

```
Gradio UI
    ↓
Clone Engine ← Git
    ↓
Workspace Manager
    ↓
Analysis Engine → LLM API
    ↓
Results Display
```

---

## Performance

| Task | Time |
|------|------|
| Clone repo | 30s - 5min |
| Analysis | 30s - 3min |
| Total | ~1-10 min |

---

## Example Repos to Try

✅ **Local**: springboot-demo (already available)
```
Path: /Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo
Status: Ready (no clone needed)
```

✅ **FastAPI** (small, modern)
```
https://github.com/fastapi/fastapi.git
```

✅ **Django** (large, mature)
```
https://github.com/django/django.git
```

✅ **Flask** (small, educational)
```
https://github.com/pallets/flask.git
```

---

## Advanced: Batch Analysis

```python
from gradio_code_analysis_repo import run_code_analysis

for repo in ['fastapi', 'django', 'flask']:
    path = f'/dataset/codes/{repo}'
    success, result = run_code_analysis(path)
    print(f"\n{repo}:\n{result}")
```

---

## Docker (Future)

```bash
docker build -t code-analysis .
docker run -p 7860:7860 code-analysis
```

---

## API (Future)

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo.git"}'
```

---

## Debug

```bash
# Check environment
source .venv/bin/activate
python -c "from deepagents import create_deep_agent; print('✅ OK')"

# Test git
git --version

# Run with debug
PYTHONUNBUFFERED=1 python gradio/gradio_code_analysis_repo.py
```

---

## Key Commands

```bash
# Start app
./gradio/start_app.sh

# Manual start
source .venv/bin/activate
python gradio/gradio_code_analysis_repo.py

# List cloned repos
ls -la /Users/zeihanaulia/Programming/research/agent/dataset/codes/

# Remove cloned repo
rm -rf /Users/zeihanaulia/Programming/research/agent/dataset/codes/repo-name

# Test clone
git clone https://github.com/user/repo /tmp/test-clone
```

---

## URLs

| Resource | Link |
|----------|------|
| App | http://localhost:7860 |
| Gradio Docs | https://www.gradio.app/docs |
| DeepAgents | https://docs.deepagents.ai/ |
| LangChain | https://python.langchain.com/ |

---

**Status**: ✅ Ready to use  
**Version**: 1.0  
**Updated**: Nov 3, 2025  

💡 **Tip**: Start with FastAPI repo for quick test!
