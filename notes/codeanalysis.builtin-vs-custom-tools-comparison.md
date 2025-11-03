# Built-in Filesystem Tools dalam DeepAgents Framework

## Tanggal: November 3, 2025

## Overview

DeepAgents framework menyediakan **built-in filesystem tools** yang terintegrasi penuh dengan LangGraph state management. Tools ini menggunakan **BackendProtocol** sebagai interface standar untuk filesystem operations, menghindari reinventing the wheel.

## ✅ Keunggulan Built-in Filesystem Tools

### Terintegrasi dengan LangGraph State Management
- ✅ **Automatic Command objects** untuk state updates
- ✅ **State persistence** - files tersimpan dalam agent state atau external storage
- ✅ **Large content handling** - automatic eviction ke filesystem untuk prevent context overflow

### Advanced Features
- ✅ **Rich metadata**: size, modified time, line numbers
- ✅ **Pagination support**: offset/limit untuk large files
- ✅ **Advanced glob patterns**: `**/*.py`, recursive matching
- ✅ **Multiple grep modes**: raw, formatted, dengan context lines

### Built-in Safety & Security
- ✅ **Path validation** dan sandboxing
- ✅ **Symlink protection** dengan O_NOFOLLOW
- ✅ **Virtual mode** untuk sandboxed environments
- ✅ **Size limits** dan error handling yang robust

### Multiple Backend Support
- ✅ **FilesystemBackend**: Real disk operations dengan safety features
- ✅ **StateBackend**: Ephemeral storage dalam agent state
- ✅ **StoreBackend**: Persistent storage dengan LangGraph Store
- ✅ **CompositeBackend**: Routing ke multiple backends berdasarkan path prefix

## 🛠️ Tools yang Tersedia

### Core Filesystem Tools
- `ls` - List files dengan metadata lengkap (size, modified time, permissions)
- `read_file` - Read dengan line numbers, offset/limit, dan pagination
- `write_file` - Create new files dengan content validation
- `edit_file` - Exact string replacements dengan global replace mode
- `glob` - Advanced pattern matching dengan recursive support
- `grep` - Fast search dengan ripgrep integration dan multiple output modes

### Planning & Task Management
- `write_todos` - Task decomposition dan progress tracking
- `task` - Subagent spawning untuk context isolation

---

# FilesystemBackend Usage Guide & Documentation

## Official Documentation Links

### Primary Resources
- **[Backends Documentation](https://docs.langchain.com/oss/python/deepagents/backends)** - Comprehensive guide to all backend types and configuration
- **[Deep Agents Overview](https://docs.langchain.com/oss/python/deepagents/overview)** - When to use deep agents and core capabilities
- **[Quickstart Guide](https://docs.langchain.com/oss/python/deepagents/quickstart)** - Step-by-step setup and first agent creation

### Related Documentation
- **[Middleware Architecture](https://docs.langchain.com/oss/python/deepagents/middleware)** - Understanding the middleware stack
- **[Customization Options](https://docs.langchain.com/oss/python/deepagents/customization)** - Advanced configuration and customization
- **[Long-term Memory](https://docs.langchain.com/oss/python/deepagents/long-term-memory)** - Persistent storage across conversations

## FilesystemBackend Configuration & Usage

### Basic Setup

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

# Local filesystem access with absolute path
agent = create_deep_agent(
    backend=FilesystemBackend(root_dir="/Users/username/projects/myproject")
)
```

### Key Parameters

- **`root_dir`**: Absolute path to the root directory (required)
- **`virtual_mode`**: Boolean, enables sandboxed path normalization (optional, default=False)

### Virtual Mode Usage

```python
# Enable virtual mode for sandboxed environments
agent = create_deep_agent(
    backend=FilesystemBackend(
        root_dir="/sandbox/workspace",
        virtual_mode=True  # Normalizes and validates paths
    )
)
```

## Built-in Filesystem Tools Available

### Core Tools (automatically available with FilesystemBackend)

#### 1. `ls` - List Directory Contents
```python
# List files with metadata
ls("/src")  # Returns: path, size, modified_at, is_dir
```

#### 2. `read_file` - Read File Contents
```python
# Read with pagination support
read_file("/src/main.py", offset=0, limit=100)  # First 100 lines
read_file("/src/main.py", offset=100, limit=50)  # Next 50 lines
```

#### 3. `write_file` - Create New Files
```python
# Create-only operation (fails if file exists)
write_file("/notes/analysis.md", "Analysis results...")
```

#### 4. `edit_file` - Modify Existing Files
```python
# Exact string replacement
edit_file("/src/main.py", "old_code", "new_code")
edit_file("/src/main.py", "old_code", "new_code", replace_all=True)
```

#### 5. `glob` - Pattern Matching
```python
# Advanced glob patterns
glob("**/*.py")      # All Python files recursively
glob("src/**/*.js")  # JS files in src directory
glob("*.md")         # Markdown files in current directory
```

#### 6. `grep` - Search Text
```python
# Fast search with ripgrep integration
grep("function", path="/src")           # Search in directory
grep("TODO", glob="**/*.py")            # Search Python files
grep("import", path="/src", glob="*.js") # Combined filters
```

## Backend Types Comparison

### FilesystemBackend (Local Disk)
```python
from deepagents.backends import FilesystemBackend

# Best for: Local projects, CI sandboxes, mounted volumes
agent = create_deep_agent(
    backend=FilesystemBackend(root_dir="/path/to/project")
)

# Features:
# - Real file operations on disk
# - Secure path resolution
# - Symlink protection (O_NOFOLLOW)
# - Ripgrep integration for fast grep
# - Optional virtual mode for sandboxing
```

### StateBackend (Ephemeral)
```python
from deepagents.backends import StateBackend

# Best for: Scratch pad, intermediate results
agent = create_deep_agent(
    backend=lambda rt: StateBackend(rt)
)

# Features:
# - Files stored in LangGraph agent state
# - Persists across turns in same thread
# - Automatic eviction of large tool outputs
```

### StoreBackend (Persistent)
```python
from deepagents.backends import StoreBackend

# Best for: Long-term memory, cross-thread persistence
agent = create_deep_agent(
    backend=lambda rt: StoreBackend(rt)
)

# Features:
# - Persistent storage via LangGraph Store
# - Cross-thread durable storage
# - Great for memories and instructions
```

### CompositeBackend (Router)
```python
from deepagents.backends.composite import CompositeBackend

# Best for: Multiple storage sources, routing by path
composite_backend = lambda rt: CompositeBackend(
    default=StateBackend(rt),  # Default for unmatched paths
    routes={
        "/memories/": StoreBackend(rt),      # Persistent memories
        "/workspace/": FilesystemBackend(root_dir="/tmp/workspace")  # Local files
    }
)

agent = create_deep_agent(backend=composite_backend)
```

## Advanced Usage Patterns

### Custom Backend Implementation

```python
from deepagents.backends.protocol import BackendProtocol, WriteResult, EditResult
from deepagents.backends.utils import FileInfo, GrepMatch

class S3Backend(BackendProtocol):
    def __init__(self, bucket: str, prefix: str = ""):
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")

    def _key(self, path: str) -> str:
        return f"{self.prefix}{path}"

    def ls_info(self, path: str) -> list[FileInfo]:
        # List objects under path, return FileInfo entries
        # Implementation: fetch from S3, build FileInfo with path, size, modified_at
        pass

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        # Fetch object content, return numbered content
        pass

    def write(self, file_path: str, content: str) -> WriteResult:
        # Create-only semantics, return WriteResult(path=file_path, files_update=None)
        pass

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        # Read → replace → write → return occurrences
        pass

    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        # Search implementation
        pass

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        # Glob matching implementation
        pass
```

### Policy Hooks & Security

```python
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.protocol import WriteResult, EditResult

class GuardedBackend(FilesystemBackend):
    def __init__(self, *, deny_prefixes: list[str], **kwargs):
        super().__init__(**kwargs)
        self.deny_prefixes = [p if p.endswith("/") else p + "/" for p in deny_prefixes]

    def write(self, file_path: str, content: str) -> WriteResult:
        if any(file_path.startswith(p) for p in self.deny_prefixes):
            return WriteResult(error=f"Writes not allowed under {file_path}")
        return super().write(file_path, content)

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        if any(file_path.startswith(p) for p in self.deny_prefixes):
            return EditResult(error=f"Edits not allowed under {file_path}")
        return super().edit(file_path, old_string, new_string, replace_all)

# Usage
agent = create_deep_agent(
    backend=GuardedBackend(
        root_dir="/workspace",
        deny_prefixes=["/workspace/secret/", "/workspace/private/"]
    )
)
```

## Protocol Reference

### Required BackendProtocol Methods

```python
class BackendProtocol(Protocol):
    def ls_info(self, path: str) -> list[FileInfo]:
        """Return entries with at least path. Include is_dir, size, modified_at when available."""

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        """Return numbered content. On missing file: "Error: File '/x' not found"."""

    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        """Return structured matches. Invalid regex: "Invalid regex pattern: ..." """

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        """Return matched files as FileInfo entries."""

    def write(self, file_path: str, content: str) -> WriteResult:
        """Create-only. On conflict: WriteResult(error=...). Success: path and files_update."""

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        """Enforce uniqueness unless replace_all=True. Return occurrences on success."""
```

### Supporting Types

```python
@dataclass
class FileInfo:
    path: str                    # Required
    is_dir: bool | None = None   # Optional
    size: int | None = None      # Optional
    modified_at: datetime | None = None  # Optional

@dataclass
class GrepMatch:
    path: str    # File path
    line: int    # Line number
    text: str    # Matching line content

@dataclass
class WriteResult:
    error: str | None = None
    path: str | None = None
    files_update: dict | None = None

@dataclass
class EditResult:
    error: str | None = None
    path: str | None = None
    files_update: dict | None = None
    occurrences: int | None = None
```

## Troubleshooting & Common Issues

### Permission Issues
```python
# Check if directory exists and is accessible
import os
assert os.path.exists("/path/to/root")
assert os.access("/path/to/root", os.R_OK | os.W_OK)
```

### Backend Factory Pattern
```python
# For backends needing runtime access (StateBackend, StoreBackend)
backend_factory = lambda rt: StateBackend(rt)
agent = create_deep_agent(backend=backend_factory)

# For backends with static configuration (FilesystemBackend)
agent = create_deep_agent(backend=FilesystemBackend(root_dir="/path"))
```

## Performance Optimization

### Ripgrep Integration
- FilesystemBackend uses ripgrep for fast `grep` operations
- Falls back to Python implementation if ripgrep unavailable
- Supports multiple output modes: raw, formatted, with context

### Memory Management
- Automatic eviction of large tool results
- Pagination support for large files (offset/limit parameters)
- State optimization to minimize context window usage

### Security Features
- Path resolution prevents directory traversal
- Symlink protection using O_NOFOLLOW
- Size validation prevents excessive memory usage
- Virtual mode for sandboxed environments

This comprehensive guide covers all aspects of FilesystemBackend usage, from basic setup to advanced routing and custom implementations, based on the official LangChain DeepAgents documentation.