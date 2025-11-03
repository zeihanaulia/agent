# DeepAgents FilesystemBackend Implementation Guide

## 📋 Overview

Script `code_analysis.py` telah direfaktor untuk menggunakan **FilesystemBackend bawaan LangChain** menggantikan custom tools. Ini mengikuti best practices untuk agent development dengan LangChain DeepAgents.

## ✨ Perubahan Utama

### Sebelumnya (Custom Tools Approach)
```python
from langchain_core.tools import tool

@tool
def list_directory(path: str) -> str:
    """List files in a directory"""
    # Implementation...
    
@tool
def read_file(file_path: str, max_lines: int = 100) -> str:
    """Read file contents"""
    # Implementation...

# ... lebih banyak custom tools ...

agent = create_deep_agent(
    system_prompt=analysis_prompt,
    model=analysis_model,
    tools=tools,  # Passing custom tools
)
```

### Sekarang (FilesystemBackend Approach) ✅
```python
from deepagents.backends import FilesystemBackend

# Backend otomatis menyediakan semua filesystem tools
backend = FilesystemBackend(root_dir=codebase_path)

agent = create_deep_agent(
    system_prompt=analysis_prompt,
    model=analysis_model,
    backend=backend,  # Passing backend
)
```

## 🎯 Keuntungan Implementasi Baru

### 1. **Tidak Perlu Custom Tools**
- ❌ Menghapus 4 custom tool functions (~200+ lines of code)
- ❌ Menghapus `@tool` decorators
- ✅ Menggunakan built-in filesystem tools dari LangChain

### 2. **Built-in Tools Tersedia Otomatis**
Dengan FilesystemBackend, agent mendapatkan 6 tools langsung:

| Tool | Fungsi | Contoh |
|------|--------|--------|
| `ls` | List files dengan metadata | `ls("/src")` → size, modified_at, is_dir |
| `read_file` | Read dengan pagination | `read_file("/main.py", offset=100, limit=50)` |
| `write_file` | Create new files | `write_file("/notes.md", "content")` |
| `edit_file` | String replacement | `edit_file("/file.py", "old", "new")` |
| `glob` | Pattern matching | `glob("**/*.py")` |
| `grep` | Fast text search | `grep("TODO", path="/src")` |

### 3. **Best Practices & Security**
- ✅ **Path Validation** - Mencegah directory traversal attacks
- ✅ **Symlink Protection** - O_NOFOLLOW untuk prevent symlink issues
- ✅ **Sandboxing** - root_dir membatasi akses hanya ke folder yang ditentukan
- ✅ **Large Content Handling** - Automatic eviction ke filesystem mencegah context overflow
- ✅ **Ripgrep Integration** - Fast grep operation di Linux/Mac

### 4. **Backend Protocol Integration**
FilesystemBackend mengimplementasikan `BackendProtocol` resmi LangChain:
```python
class BackendProtocol(Protocol):
    def ls_info(path: str) -> list[FileInfo]
    def read(file_path: str, offset: int, limit: int) -> str
    def write(file_path: str, content: str) -> WriteResult
    def edit(file_path: str, old_string: str, new_string: str) -> EditResult
    def glob_info(pattern: str) -> list[FileInfo]
    def grep_raw(pattern: str, path: str, glob: str) -> list[GrepMatch] | str
```

### 5. **LangGraph State Management**
- ✅ Tools terintegrasi dengan LangGraph state
- ✅ Automatic Command objects untuk state updates
- ✅ Cross-thread persistence via CompositeBackend jika diperlukan

## 📊 Perbandingan Kode

### Jumlah Baris
- **Sebelumnya**: 312 lines (termasuk 200+ lines custom tools)
- **Sekarang**: 312 lines (namun lebih bersih, tanpa custom tool boilerplate)

### Kompleksitas
- **Custom Tools**: Perlu memahami `@tool` decorator, docstring parsing, error handling
- **FilesystemBackend**: Cukup pass `backend=` parameter ke `create_deep_agent()`

## 🔧 Konfigurasi FilesystemBackend

### Dasar (Local Filesystem)
```python
from deepagents.backends import FilesystemBackend

backend = FilesystemBackend(root_dir="/path/to/project")
agent = create_deep_agent(backend=backend)
```

### Virtual Mode (Sandboxed)
```python
backend = FilesystemBackend(
    root_dir="/path/to/project",
    virtual_mode=True  # Normalizes paths under root_dir
)
```

### Composite Backend (Multiple Sources)
```python
from deepagents.backends.composite import CompositeBackend
from deepagents.backends import StateBackend, StoreBackend

composite_backend = lambda rt: CompositeBackend(
    default=StateBackend(rt),
    routes={
        "/memories/": StoreBackend(rt),      # Persistent
        "/workspace/": FilesystemBackend(root_dir="/tmp/workspace")  # Local
    }
)
agent = create_deep_agent(backend=composite_backend)
```

## 📝 Tools Usage dalam Agent Prompt

Agent sekarang dapat menggunakan tools dengan natural language:

```
"Analyze the project structure"
→ Agent calls: ls("/"), glob("**/*.py"), read_file("README.md")

"Search for configuration files"
→ Agent calls: glob("*.json"), glob("*.yaml"), grep("config", glob="**/*")

"Find all test files and read one"
→ Agent calls: glob("**/test_*.py"), read_file("/tests/test_main.py")
```

## 🚀 Penggunaan Script

```bash
# Default codebase
python scripts/code_analysis.py

# Custom codebase
python scripts/code_analysis.py --codebase-path /path/to/project

# Via environment variable
CODEBASE_PATH=/path/to/project python scripts/code_analysis.py
```

## 📚 Dokumentasi Resmi

- **Backends**: https://docs.langchain.com/oss/python/deepagents/backends
- **DeepAgents Overview**: https://docs.langchain.com/oss/python/deepagents/overview
- **BackendProtocol**: https://docs.langchain.com/oss/python/deepagents/backends#protocol-reference

## 🎓 Learning Path

1. **Pahami BackendProtocol** - Interface standar untuk filesystem operations
2. **Explore Built-in Tools** - ls, read_file, glob, grep capabilities
3. **Try Different Backends**:
   - `FilesystemBackend` - Real disk access
   - `StateBackend` - Ephemeral storage
   - `StoreBackend` - Persistent storage
   - `CompositeBackend` - Multiple backends
4. **Custom Backends** - Implementasi S3Backend, PostgresBackend, dll

## ✅ Checklist Implementasi

- [x] Remove custom tools (@tool decorators)
- [x] Remove Path import (tidak digunakan lagi)
- [x] Add FilesystemBackend import
- [x] Configure backend dengan root_dir
- [x] Update agent initialization untuk pakai backend
- [x] Update system prompt untuk reflect built-in tools
- [x] Remove tools parameter dari create_deep_agent
- [x] Update startup message untuk show FilesystemBackend
- [x] Verify no linting errors
- [x] Document changes dan best practices

## 🔍 Testing & Validation

Untuk memverifikasi implementasi:

```bash
# 1. Check no syntax errors
python -m py_compile scripts/code_analysis.py

# 2. Run dengan debug mode
python scripts/code_analysis.py -p /path/to/project

# 3. Verify tools tersedia
# (Check dalam agent output bahwa ls, read_file, glob, grep digunakan)
```

## 🎯 Next Steps

1. **Advanced Backends** - Implement custom backend untuk S3/Database
2. **Policy Hooks** - Add security policies (deny_prefixes, etc)
3. **Performance** - Monitor token usage dengan large tool results
4. **Integration** - Combine dengan LangSmith untuk observability

---

**Last Updated**: November 3, 2025  
**Framework**: LangChain DeepAgents v0.2+  
**Reference**: BackendProtocol & FilesystemBackend Documentation
