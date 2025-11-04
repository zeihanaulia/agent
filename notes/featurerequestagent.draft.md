## Step 1 — Analisis Struktur Kode Lo Sekarang

Script lo ini udah implement:

* ✅ **Filesystem-aware agent** — via `FilesystemBackend`, bisa `ls`, `grep`, `read_file`, `write_file`
* ✅ **LLM orchestration** — pakai `DeepAgents` (yang built di atas LangGraph)
* ✅ **Context management** — via prompt `analysis_prompt`
* ✅ **Secure sandboxing** — agent cuma boleh baca/tulis di `root_dir`
* ✅ **Analysis output** — summarization + architecture extraction

Artinya:
lo udah punya *“code intelligence substrate”* yang bisa memahami dan memetakan struktur proyek (semantic + structural).

---

## Step 2 — Gap Menuju “Feature-by-Request Agent”

Yang belum ada sekarang:

1. ❌ Phase interpretasi *user intent → design spec*
2. ❌ Phase *impact analysis* (feature ini nyentuh file mana?)
3. ❌ Phase *code generation/editing berdasarkan hasil analisa struktur*

Untuk nyampe ke sana, lo perlu layer baru di atas agent ini:

> **“Contextual Intelligence Layer (CIL)”**
> yang berfungsi sebagai *bridge* antara request user dan state codebase.

---

## Step 3 — Arsitektur Multi-Phase

### Phase 1 — Context Extraction (udah ada)

> Agent lo sekarang melakukan ini.

Tujuan:

* Pahami project purpose
* Pahami dependency
* Map architecture

→ output: JSON atau Markdown summary (basis *code context memory*)

---

### Phase 2 — User Request Interpretation

Tambahkan satu **intent parser agent**:

```python
intent_prompt = """
You are a software architect agent.
User will request a new feature.
Your job is to extract:
- Feature name
- Affected modules
- Required changes (new files, edited files)
- Dependencies or services impacted
Return result as JSON:
{
  "feature_name": "...",
  "intent_summary": "...",
  "affected_files": [],
  "new_files": [],
  "modifications": [],
  "notes": "..."
}
"""
```

Agent ini:

* Baca hasil dari `analysis_agent`
* Analisa request user (`"add login endpoint"`, `"implement retry logic"`)
* Output structured spec untuk step selanjutnya

---

### Phase 3 — Impact Analysis (CIL core)

Gunakan `grep` dan `glob` tools untuk mencari lokasi relevan.
Contoh task internal:

```python
# pseudo
impact = agent.invoke({
    "input": f"Find all files related to user authentication in {codebase_path}"
})
```

Agent ini nyari pattern (e.g. `auth`, `login`, `token`) → build dependency map.

---

### Phase 4 — Code Synthesis & Diff Planning

Pakai `edit_file()` dan `write_file()` untuk membangun patch plan.

Bisa model seperti:

```python
feature_dev_prompt = """
Given the following code context and feature spec,
generate the minimal diff or new file needed to implement the feature.
Ensure consistency with existing architecture.
"""
```

Gunakan dua LLM:

* `code_planner` (LLM kecil, fast reasoning)
* `code_writer` (LLM besar, coding kuat — ex: `gpt-4o` / `deepseek-coder`)

---

### Phase 5 — Execution & Verification

Bikin *toolchain loop*:

```python
# pseudo
plan = feature_planner_agent.invoke({"input": user_request})
diffs = code_writer_agent.invoke({"plan": plan})
fs_agent.invoke({"edit": diffs})
```

Tambahkan:

* **Middleware Guardrails:** validasi syntax, enforce architecture
* **Telemetry:** LangSmith logging per file modified

---

## Step 4 — Implementasi Modular (LangGraph Style)

```
[User Request]
      ↓
[Intent Parser Agent]
      ↓
[Contextual Intelligence Layer]
   ├── Code Search (grep, glob)
   ├── Index Reader (embeddings optional)
   └── Architecture Mapper
      ↓
[Feature Planner Agent]
      ↓
[Code Writer Agent]
      ↓
[Filesystem Backend]  ← executes edits
```

LangChain v1 + DeepAgents udah support ini:

* `create_deep_agent` (execution layer)
* `BackendProtocol` (filesystem access)
* `middleware` (buat enforce rule di setiap fase)

---

## Step 5 — Contoh Integrasi Minimal

```python
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from deepagents.backends import FilesystemBackend

feature_request = "Add API endpoint /users/export that returns CSV of all users."

backend = FilesystemBackend(root_dir="/path/to/project")

intent_agent = create_deep_agent(
    model=ChatOpenAI(model="gpt-4o-mini", temperature=0.3),
    system_prompt=intent_prompt,
)

result = intent_agent.invoke({"input": feature_request})
feature_spec = result["messages"][-1].content

# Then pass feature_spec into a code writer agent
writer_prompt = f"""
Implement the following feature in the given codebase:
{feature_spec}

- Maintain existing project conventions
- Generate diff patches only
- Validate syntax before write
"""

code_writer_agent = create_deep_agent(
    model=ChatOpenAI(model="deepseek-coder"),
    backend=backend,
    system_prompt=writer_prompt
)

code_writer_agent.invoke({"input": "Implement feature now"})
```

---

## Step 6 — Dokumentasi dan Referensi

| Konsep                                | Link                                                                                                                   |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| DeepAgents Framework                  | [https://docs.langchain.com/oss/python/deepagents/overview](https://docs.langchain.com/oss/python/deepagents/overview) |
| FilesystemBackend                     | [https://docs.langchain.com/oss/python/deepagents/backends](https://docs.langchain.com/oss/python/deepagents/backends) |
| Contextual Intelligence Layer concept | [LangChain Context Engineering](https://docs.langchain.com/oss/python/langchain/context-engineering)                   |
| Middleware for guardrails             | [LangChain Middleware](https://docs.langchain.com/oss/python/langchain/middleware)                                     |
| LangGraph runtime                     | [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)                                         |
| Code agent use case                   | [LangChain DeepAgents Examples (GitHub)](https://github.com/langchain-ai/langchain/tree/master/examples/deepagents)    |
