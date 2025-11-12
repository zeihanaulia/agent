# Quick Reference: Empty Path Problem & Solution

## 🔴 Problem Identified

```
SYMPTOM:
  251.75s execution time
  0 files created
  20+ "Tool validation skipped: empty file path" warnings
  3 timeouts (30s, 60s, 120s)

ROOT CAUSE:
  LLM generates: read_file(path="")
  ↓
  Backend validation skipped (not enforced)
  ↓
  Tool fails silently
  ↓
  Agent retries indefinitely
  ↓
  TIMEOUT after 120s
```

## ✅ Solution Overview

```
3 TARGETED FIXES:

1️⃣  FIX 2.1: FilesystemMiddleware System Prompt
    WHERE: agents/agent_factory.py → create_code_synthesis_agent()
    WHAT:  Add custom system_prompt to FilesystemMiddleware
    WHY:   We were prompting wrong layer before
    HOW:   Pass system_prompt parameter to FilesystemMiddleware()
    TIME:  15 min

2️⃣  FIX 2.2: Validation Wrapper Backend
    WHERE: agents/agent_factory.py → new ValidatingFilesystemBackend class
    WHAT:  Hard validation catches empty paths BEFORE backend processes
    WHY:   Silent failure causes infinite loop
    HOW:   Return error instead of continuing with empty path
    TIME:  20 min

3️⃣  FIX 2.3: Pre-load File List Context
    WHERE: agents/agent_factory.py → create_code_synthesis_agent()
    WHAT:  Scan codebase, add actual files to prompt context
    WHY:   LLM doesn't know what files exist, hallucinates paths
    HOW:   os.walk() + add to system prompt
    TIME:  10 min
```

## 📊 Expected Impact

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Phase 4 Time | 251s | <60s | <60s ✓ |
| Files Created | 0 | 3-5 | 3-5 ✓ |
| Empty Path Errors | 20+ | 0 | 0 ✓ |
| Timeouts | 3 | 0 | 0 ✓ |
| Patches Generated | 0 | 5-10 | 5+ ✓ |

## 🎯 Implementation Checklist

### Phase 1: FilesystemMiddleware Prompt (15 min)
- [ ] Open `agents/agent_factory.py`
- [ ] Locate `create_code_synthesis_agent()` function
- [ ] Find `agent_kwargs` creation
- [ ] Add `middleware=[FilesystemMiddleware(...)]` with:
  - `system_prompt="""absolute path requirements"""`
  - `custom_tool_descriptions={...}` with guidance
- [ ] Test: agent should log middleware messages

### Phase 2: Validation Wrapper (20 min)
- [ ] Create `ValidatingFilesystemBackend(FilesystemBackend)` class
- [ ] Override `invoke()` method
- [ ] Add checks for empty paths:
  - `tool_name in ["read_file", "edit_file", "write_file"]`
  - `path = tool_input.get("path")`
  - If empty: return `{"error": "Path cannot be empty"}`
- [ ] Use in: `backend = ValidatingFilesystemBackend(root_dir=...)`

### Phase 3: Pre-load File List (10 min)
- [ ] In `create_code_synthesis_agent()`, before creating prompt
- [ ] Add: `os.walk(codebase_path)` loop
- [ ] Collect `.java`, `.xml`, `.properties` files
- [ ] Add to prompt:
  ```
  AVAILABLE FILES:
  /path/to/file1.java
  /path/to/file2.java
  ...
  ```

### Phase 4: Test (30 min)
- [ ] Run: `python3 scripts/coding_agent/feature_by_request_agent_v3.py --codebase-path dataset/codes/springboot-demo --feature-request "Add voucher management feature"`
- [ ] Check: Time <60s, Files created >0, Errors =0
- [ ] Measure output

### Phase 5: Verify No Regressions (10 min)
- [ ] Run: `python verify_fixes.py`
- [ ] All 18 checks should pass
- [ ] Fix #1, #2, #3 from before still working

## 🚨 Key Points

1. **Target the RIGHT Layer**
   - Not: `agent_factory.py` generic prompt
   - YES: `FilesystemMiddleware(system_prompt=...)`

2. **Validation Matters**
   - Don't skip error cases
   - Return error instead of silent failure
   - Forces agent to course-correct

3. **Context is King**
   - LLM needs ground truth
   - File list > generic guidance
   - Reduces hallucinations

## 📝 Code Templates

### Template 1: FilesystemMiddleware
```python
from deepagents.middleware.filesystem import FilesystemMiddleware

middleware = FilesystemMiddleware(
    backend=backend,
    system_prompt="""
    CRITICAL: Use ABSOLUTE file paths only.
    Never empty paths. Always provide full path.
    """,
    custom_tool_descriptions={
        "read_file": "Read file with ABSOLUTE path (e.g., /path/to/file.java)",
        "write_file": "Write file with ABSOLUTE path and COMPLETE content"
    }
)
```

### Template 2: Validation Wrapper
```python
class ValidatingFilesystemBackend(FilesystemBackend):
    def invoke(self, tool_input: dict, **kwargs):
        if tool_input.get("tool_name") == "read_file":
            path = tool_input.get("path") or ""
            if not path.strip():
                return {"error": "read_file requires non-empty path"}
        return super().invoke(tool_input, **kwargs)
```

### Template 3: File List Context
```python
import os
files = []
for root, dirs, file_list in os.walk(codebase_path):
    for f in file_list:
        if f.endswith(('.java', '.xml')):
            files.append(os.path.join(root, f))

files_context = "AVAILABLE FILES:\n" + "\n".join(files[:30])
```

## 📞 Questions?

- **Why 3 fixes?** Each targets different part of problem
- **Which is most critical?** Fix 2.1 (FilesystemMiddleware) - the architectural fix
- **Can we do less?** Fix 2.1 alone might work, but 2.2 & 2.3 make it robust
- **Timeline?** 45 minutes total implementation

## 🎓 Learning Reference

**LangChain DeepAgent Docs**:
- https://docs.langchain.com/oss/python/deepagents/middleware
- Look for: FilesystemMiddleware system_prompt parameter
- Key: "Middleware is composable - add as many or as few as needed"

**This Problem Shows**: Architecture > Prompting for tool guidance

