# 🤖 Code Analysis Agent - Gradio UI

Aplikasi web interaktif untuk menganalisis repository dengan AI-powered code analysis agent. Dilengkapi dengan Git integration untuk clone repository otomatis.

## 🎯 Fitur

- **Repository Cloning**: Clone dari GitHub/GitLab/Gitea langsung ke workspace
- **Codebase Selection**: Pilih dari repository yang sudah di-clone atau masukkan path custom
- **AI Analysis**: Analisis codebase menggunakan DeepAgents dengan FilesystemBackend
- **Real-time Progress**: Indikator progress untuk setiap tahap analisis
- **Comprehensive Results**: Detail architecture, tech stack, dan functionality

## 📋 Prerequisites

### System Requirements
- Python 3.10+
- Git installed dan accessible di PATH
- Virtual environment aktif

### Environment Variables (`.env`)

```bash
# Required for LLM
LITELLM_MODEL=gpt-4o-mini
LITELLM_VIRTUAL_KEY=<your-api-key>
LITELLM_API=<api-base-url>

# Optional for observability
LANGSMITH_API_KEY=<optional>
LANGSMITH_PROJECT=<optional>
```

### Dependencies

```bash
pip install gradio deepagents langchain-openai python-dotenv pydantic
```

Atau install dari `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 🚀 Usage

### Analysis Modes (NEW!)

Sekarang tersedia **2 analysis modes** untuk balance antara speed vs depth:

| Mode | Time | Best For |
|------|------|----------|
| 🚀 **Fast (Summary)** | 30-50 sec | Quick overview, large repos |
| 📊 **Detailed (Full)** | 1-3 min | Deep understanding (default) |

**Fast Mode** memberikan summary ringkas dengan:
- Project purpose (1-2 lines)
- Tech stack (1 line)
- Main components (3-5 bullets)
- ~30-50 seconds total

**Detailed Mode** memberikan analisis komprehensif dengan:
- Full architecture breakdown
- All components explained
- Dependencies listed
- Code relationships
- ~1-3 minutes total

Pilih mode sesuai kebutuhan Anda di aplikasi (radio buttons di Step 2).

📖 **Full guide**: Lihat `ANALYSIS_MODES.md` untuk detail lebih lanjut.

### 1. Aktifkan Virtual Environment

```bash
cd /Users/zeihanaulia/Programming/research/agent
source .venv/bin/activate
```

### 2. Jalankan Gradio App

```bash
python gradio/gradio_code_analysis_repo.py
```

Output:
```
✅ Environment validated
📁 Workspace: /Users/zeihanaulia/Programming/research/agent/dataset/codes
🤖 Model: gpt-4o-mini

🚀 Starting Gradio server...
📱 Open http://localhost:7860 in your browser
```

### 3. Buka di Browser

Kunjungi: `http://localhost:7860`

## 📚 Workflow

### Step 1: Clone Repository (Optional)
1. Masukkan URL repository (GitHub, GitLab, atau Gitea)
2. Klik tombol "🔄 Clone Repository"
3. Sistem akan:
   - Validasi URL format
   - Extract nama repository
   - Clone ke `/dataset/codes/<repo-name>`
   - Update daftar codebase yang tersedia

**Note**: Step ini optional - jika repo sudah ada di workspace, tidak perlu clone ulang.

### Step 2: Select Codebase
- **Pilihan 1**: Pilih dari dropdown "Available Codebases" 
  - Termasuk: git repositories yang di-clone
  - Termasuk: local codebases (e.g., springboot-demo, project folders)
- **Pilihan 2**: Masukkan path custom di field "Or enter custom path"

**Apa yang terdeteksi**:
```
/dataset/codes/
├── casdoor/           ← Git clone (punya .git/)
├── dbs/               ← Git clone (punya .git/)
├── deepagents/        ← Git clone (punya .git/)
└── springboot-demo/   ← Local codebase (tanpa .git/)
```

### Step 3: Run Analysis
1. Klik tombol "🚀 Run Analysis"
2. Sistem akan:
   - Configure AI model (ChatOpenAI)
   - Initialize FilesystemBackend dengan root_dir
   - Create analysis agent
   - Analyze codebase (eksplorasi files, read config, analyze architecture)
   - Display comprehensive results

## 🔗 Supported Repository URLs

### GitHub
```
https://github.com/user/repo.git
https://github.com/user/repo
git@github.com:user/repo.git
```

### GitLab
```
https://gitlab.com/user/repo.git
https://gitlab.com/user/repo
git@gitlab.com:user/repo.git
```

### Self-hosted Gitea
```
https://gitea.example.com/user/repo.git
git@gitea.example.com:user/repo.git
```

## 📊 Analysis Output

Hasil analisis mencakup:

```
📊 **ANALYSIS SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 **Codebase Path**: /path/to/repo
🤖 **Model**: gpt-4o-mini
🌡️ **Temperature**: 0.7
⏱️ **Analysis Time**: 45.23 seconds
🔧 **Tool Calls**: 12

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **DETAILED ANALYSIS**:

[Comprehensive analysis dengan:]
- Project purpose dan goals
- Technology stack dan dependencies
- Architecture dan main components
- Key functionalities
- Code examples
```

## 🛠️ Built-in Tools

Agent otomatis memiliki akses ke 6 filesystem tools via FilesystemBackend:

1. **ls(path)**: List files dan directories dengan metadata (size, modified_at, is_dir)
2. **read_file(path, offset, limit)**: Read file contents dengan pagination untuk large files
3. **write_file(path, content)**: Create new files dengan content validation
4. **edit_file(path, old_string, new_string)**: Perform exact string replacements
5. **glob(pattern)**: Find files matching patterns (supports `**/*.py` recursive)
6. **grep(pattern, path, glob)**: Fast text search dengan context

## 💾 Workspace Structure

```
/Users/zeihanaulia/Programming/research/agent/dataset/codes/
├── casdoor/                 # Clone 1 (punya .git/)
│   ├── .git/
│   ├── main.go
│   ├── README.md
│   └── ...
├── dbs/                     # Clone 2 (punya .git/)
│   ├── .git/
│   ├── README.md
│   └── ...
├── deepagents/              # Clone 3 (punya .git/)
│   ├── .git/
│   ├── pyproject.toml
│   └── ...
├── springboot-demo/         # Local codebase (tanpa .git/)
│   ├── pom.xml
│   ├── src/
│   └── target/
└── [other-repos]/           # Future clones
```

**Catatan**: 
- Dropdown menampilkan SEMUA direktori di workspace (git repos + local codebases)
- Git repos punya `.git/` directory
- Local codebases adalah project folders yang sudah ada
- Re-clone otomatis terdeteksi (tidak membuat duplikat)

## 🔒 Security

### Path Sandboxing
- Agent hanya bisa akses files di bawah `root_dir` (codebase path)
- FilesystemBackend validates paths dan prevents symlink traversal
- Absolute path conversion mencegah relative path attacks

### API Credentials
- API key menggunakan `SecretStr` dari Pydantic
- Environment variables di-load dari `.env` (tidak di-commit ke git)
- `.env` harus di-gitignore

## 🐛 Troubleshooting

### ❌ "Missing LITELLM_VIRTUAL_KEY"
**Solusi**: Set environment variables di `.env`:
```bash
LITELLM_VIRTUAL_KEY=your-key-here
LITELLM_API=https://api.example.com
```

### ❌ "Failed to clone repository"
**Solusi**:
- Pastikan git installed: `which git`
- Check network connectivity
- Verifikasi URL format benar
- Try manual clone: `git clone <url> /tmp/test-repo`

### ❌ "No analysis result found"
**Solusi**:
- Check LLM API credentials valid
- Verify codebase path accessible
- Check firewall/proxy tidak block API calls
- Review error message in console

### ⏱️ Analysis too slow
**Solusi**:
- Use faster model (e.g., `gpt-4o-mini` vs `gpt-4`)
- Analyze smaller repository subset
- Check network latency

## 📝 Environment Configuration

### Full `.env` Example

```bash
# LLM Configuration
LITELLM_MODEL=gpt-4o-mini
LITELLM_VIRTUAL_KEY=sk-xxx...
LITELLM_API=https://api.openai.com/v1

# LangSmith (optional)
LANGSMITH_API_KEY=ls_xxx...
LANGSMITH_PROJECT=my-project

# Codebase (optional, can be set via UI)
CODEBASE_PATH=/path/to/codebase
```

## 🔗 Architecture Components

### Gradio Interface (Frontend)
- Multi-step form untuk clone → select → analyze workflow
- Real-time status updates
- Result display dengan formatting

### Clone Engine (Backend)
- Git URL validation
- Repository name extraction
- Clone dengan timeout handling
- Duplicate detection

### Analysis Engine (DeepAgents)
- ChatOpenAI model configuration
- FilesystemBackend initialization
- Agent creation dengan system prompt
- Message processing dan result extraction

### File Structure

```
gradio/
├── gradio_code_analysis_repo.py    # Main app (ini file)
├── README_CODE_ANALYSIS.md         # Documentation (ini file)
└── requirements.txt                # Dependencies

scripts/
└── code_analysis.py                # Original non-Gradio version

dataset/codes/
└── [cloned-repositories]/          # Workspace untuk clone
```

## 🚀 Advanced Usage

### Custom Codebase Path
Jika ingin analyze codebase yang sudah ada (tidak clone):
1. Field "Or enter custom path" → `/path/to/existing/codebase`
2. Klik "Run Analysis"

### Batch Analysis (Future)
```python
# Bisa di-extend dengan loop untuk analyze multiple repos
for repo_url in repo_list:
    success, msg, path = clone_repository(repo_url)
    if success:
        run_code_analysis(path)
```

### Integration dengan CI/CD
```bash
# Script untuk non-interactive analysis
python -c "
from gradio_code_analysis_repo import run_code_analysis
success, result = run_code_analysis('/path/to/repo')
print(result)
"
```

## 📚 References

- [Gradio Documentation](https://www.gradio.app/docs)
- [DeepAgents Framework](https://docs.deepagents.ai/)
- [LangChain FilesystemBackend](https://python.langchain.com/docs/integrations/backends/filesystem/)
- [LangChain ChatOpenAI](https://python.langchain.com/docs/integrations/chat/openai/)

## 📄 License

Part of the Deep Code Analysis research project.

## 🤝 Contributing

Issues, suggestions, atau PRs welcome!

---

**Last Updated**: November 3, 2025
