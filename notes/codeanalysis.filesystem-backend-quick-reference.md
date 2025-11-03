# Quick Reference: FilesystemBackend Integration

## 🎯 One-Minute Overview

**What Changed:**
- ❌ Removed 4 custom tools (~200 lines)
- ✅ Added FilesystemBackend (3 lines config)
- ✅ Agent now has 6 built-in tools automatically

**Before:**
```python
from langchain_core.tools import tool

@tool
def list_directory(path: str) -> str:
    # 20 lines of code...

# ... 3 more custom tools ...
agent = create_deep_agent(..., tools=[list_directory, ...])
```

**After:**
```python
from deepagents.backends import FilesystemBackend

backend = FilesystemBackend(root_dir=codebase_path)
agent = create_deep_agent(..., backend=backend)
```

---

## 📚 Built-in Tools Reference

### Tool: `ls` (List Files)
```python
# List files with metadata
ls("/path/to/dir")

# Returns: path, is_dir, size, modified_at
# Example output:
# /path/to/dir/file.py (size: 2048, modified: 2025-11-03)
# /path/to/dir/subdir/ (dir)
```

### Tool: `read_file` (Read with Pagination)
```python
# Read entire file
read_file("/path/to/file.py")

# Read with pagination
read_file("/path/to/file.py", offset=100, limit=50)
# offset: starting line (0-based)
# limit: number of lines to read

# Returns: numbered content with line numbers
# 100: def my_function():
# 101:     return True
```

### Tool: `glob` (Pattern Matching)
```python
# Find Python files
glob("**/*.py")

# Find in specific directory
glob("src/**/*.js")

# Simple patterns
glob("*.md")
glob("test_*.py")

# Returns: list of matching paths
```

### Tool: `grep` (Text Search)
```python
# Search in directory
grep("TODO", path="/src")

# Search with glob pattern
grep("function", glob="**/*.py")

# Combined search
grep("import", path="/src", glob="*.js")

# Returns: matching lines with context
# path/to/file.py:42: import numpy as np
```

### Tool: `write_file` (Create Files)
```python
# Create new file
write_file("/path/to/new_file.md", "File content here")

# Returns: success/error with path

# Note: Fails if file already exists (create-only semantics)
```

### Tool: `edit_file` (String Replacement)
```python
# Replace first occurrence
edit_file("/path/to/file.py", "old_code", "new_code")

# Replace all occurrences
edit_file("/path/to/file.py", "old_code", "new_code", replace_all=True)

# Returns: error if not found or success with occurrences count
```

---

## 🔧 Configuration Options

### Basic Setup
```python
from deepagents.backends import FilesystemBackend

backend = FilesystemBackend(root_dir="/path/to/project")
agent = create_deep_agent(backend=backend)
```

### With Virtual Mode (Sandboxed)
```python
backend = FilesystemBackend(
    root_dir="/path/to/project",
    virtual_mode=True  # Normalizes paths, prevents escaping
)
```

### Multiple Backends (Composite)
```python
from deepagents.backends.composite import CompositeBackend
from deepagents.backends import FilesystemBackend, StoreBackend, StateBackend

composite_backend = lambda rt: CompositeBackend(
    default=StateBackend(rt),  # Ephemeral by default
    routes={
        "/memories/": StoreBackend(rt),  # Persistent
        "/workspace/": FilesystemBackend(root_dir="/tmp/work")  # Real filesystem
    }
)
agent = create_deep_agent(backend=composite_backend)
```

---

## 🔒 Security Features (Built-in)

| Feature | Description |
|---------|-------------|
| **Path Validation** | Prevents directory traversal attacks |
| **Sandboxing** | root_dir limits agent to specific folder |
| **Symlink Protection** | O_NOFOLLOW prevents symlink loop attacks |
| **Size Limits** | Configurable limits for large files |
| **Error Handling** | Consistent, safe error messages |
| **Permissions** | Respects OS file permissions |

---

## 📝 Example: Using in Agent Prompt

Your system prompt can reference tools naturally:

```python
analysis_prompt = """
You have access to these filesystem tools:
- ls(path): List directory contents
- read_file(path, offset, limit): Read file with pagination
- glob(pattern): Find files matching pattern
- grep(pattern, path): Search for text
- write_file(path, content): Create new file
- edit_file(path, old, new): Replace text in file

Tasks:
1. Use glob("**/*.py") to find all Python files
2. Use read_file() with offset/limit for large files
3. Use grep() to search for specific patterns
4. Use edit_file() to make code changes
"""
```

---

## 🚀 Common Patterns

### Pattern 1: Explore Directory Structure
```
Agent strategy:
1. ls("/") - see root contents
2. glob("**/*.md") - find documentation
3. glob("**/*.json") - find config files
4. read_file("README.md") - understand project
```

### Pattern 2: Search for Specific Code
```
Agent strategy:
1. glob("**/*.py") - find Python files
2. grep("def main", path="/src") - find main functions
3. read_file("/src/main.py", offset=0, limit=50) - read first 50 lines
```

### Pattern 3: Analyze Large Project
```
Agent strategy:
1. ls("/") - overview
2. glob("**/*.json") - configuration files
3. read_file() with pagination for large files
4. grep() for cross-file patterns
```

### Pattern 4: Make Code Changes
```
Agent strategy:
1. read_file("/path/to/file.py") - view content
2. Analyze what needs changing
3. edit_file("/path/to/file.py", "old", "new") - make change
4. read_file() - verify change
```

---

## 🎓 Best Practices

### ✅ DO:
- Use `glob()` for finding files by pattern
- Use `read_file()` with offset/limit for large files
- Use `grep()` to search across multiple files
- Combine multiple tools in single response
- Use `root_dir` to sandbox agent access

### ❌ DON'T:
- Try to read entire huge files at once (use offset/limit)
- Assume file exists without checking first
- Use hardcoded paths (use glob for discovery)
- Ignore error messages from tools
- Write files outside root_dir

---

## 📊 Performance Tips

| Scenario | Recommendation |
|----------|-----------------|
| Large file (>10K lines) | Use read_file with offset/limit |
| Find specific files | Use glob with pattern |
| Search across files | Use grep instead of reading all |
| Multiple reads | Consider combining in one tool call |
| Batch operations | Combine tools in agent response |

---

## 🔗 Reference Links

- **Official Docs**: https://docs.langchain.com/oss/python/deepagents/backends
- **BackendProtocol**: https://docs.langchain.com/oss/python/deepagents/backends#protocol-reference
- **DeepAgents Overview**: https://docs.langchain.com/oss/python/deepagents/overview

---

## ❓ FAQ

**Q: Do I need to define custom tools anymore?**  
A: No! FilesystemBackend provides 6 built-in tools automatically.

**Q: Can I still use custom tools if I want?**  
A: Yes, but it's not recommended. Use backend for filesystem, custom tools for domain-specific logic.

**Q: What if I need more than 6 tools?**  
A: Create custom tools and pass them alongside backend.

**Q: Can I switch backends?**  
A: Yes! All tools work with any backend implementing BackendProtocol.

**Q: Is this production-ready?**  
A: Yes! FilesystemBackend has built-in security and error handling.

**Q: How do I handle permissions?**  
A: Use OS permissions on root_dir. Backend respects system permissions automatically.

---

## 🎯 Next Steps

1. **Try It Out**: Run the script with `python scripts/code_analysis.py`
2. **Experiment**: Try different backends (StateBackend, StoreBackend)
3. **Extend**: Create custom backend for S3, Database, etc.
4. **Monitor**: Use LangSmith for observability
5. **Scale**: Deploy with CompositeBackend for production

---

**Last Updated**: November 3, 2025  
**Status**: ✅ Production Ready  
**Framework**: LangChain DeepAgents v0.2+
