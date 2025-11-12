# Root Cause Analysis & Implementation Plan - Empty Path Issue

## 📊 Executive Summary

Test menunjukkan bahwa meskipun semua 3 fixes sudah diimplementasikan, agent masih menghasilkan **empty file_path** pada tool calls. Ini bukan masalah dengan Fix #2 prompt, tetapi ada **architectural mismatch antara LLM output dan DeepAgent tool validation**.

**Status**: ⚠️ Root cause identified, solution requires deeper integration fix

---

## 🔍 Root Cause Analysis

### **Problem Chain Identified**

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. LLM Generates Tool Call                                           │
│    read_file(path="") ← Empty path because...                        │
│    - Model uncertainty on file structure                             │
│    - Prompt not specific enough about WHICH files to read            │
│    - Model hallucinating vs. using actual file list                  │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. DeepAgent Tool Validation Layer                                   │
│    ⚠️ Tool validation SKIPPED for empty path                         │
│    "Tool validation skipped: read_file has empty file path"          │
│    → Tool executes anyway with empty path                            │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. FilesystemBackend Processes Empty Path                            │
│    ✓ Validation skipped (not enforced)                               │
│    ✓ Tool "completes" without error                                 │
│    → Returns empty result or error silently                          │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Agent Continues Loop                                              │
│    Agent: "Got empty result, trying again..."                        │
│    LLM: "Let me try read_file again with different path (still empty)"
│    → INFINITE LOOP until timeout                                    │
└─────────────────────────────────────────────────────────────────────┘
```

### **Why Fix #2 Didn't Work**

1. **Prompt added to wrong place**
   - We added prompt to `agent_factory.py` Phase 4
   - But DeepAgent uses its **own built-in system prompt**
   - Our custom prompt might be **overridden or appended too late**

2. **LLM doesn't get file list context**
   - Prompt says "use absolute paths"
   - But LLM doesn't know what files exist!
   - LLM has to hallucinate paths

3. **No hard validation at tool level**
   - DeepAgent validates but skips for empty paths
   - No enforcement mechanism

---

## 📋 LangChain Documentation Insights

### **From DeepAgent Docs:**

```python
# FilesystemMiddleware is included by default in create_deep_agent
# Custom tool descriptions can be provided
agent = create_deep_agent(
    model="claude-sonnet-4-5-20250929",
    middleware=[
        FilesystemMiddleware(
            backend=None,  # Optional: custom backend
            system_prompt="Write to the filesystem when...",  # ← THIS IS KEY!
            custom_tool_descriptions={
                "read_file": "Use the read_file tool to..."
            }
        ),
    ],
)
```

**Key Insight**: 
- FilesystemMiddleware has its OWN `system_prompt` parameter
- This overrides/adds to the agent's system prompt
- We should customize THIS instead of agent_factory.py!

### **Tool Descriptions Matter**

The documentation shows that `custom_tool_descriptions` can guide LLM behavior:
```python
"read_file": "Use the read_file tool when you need to examine an existing file..."
```

This is **more specific than generic tool schema**.

---

## 🎯 What We Need to Fix

### **The Real Problem**

Looking at test output:
```
🧩 [MODEL] About to call model with 0 messages
🛠️  [TOOL] ls → .
🛠️  [TOOL] read_file → <missing path>  ← EMPTY!
```

The agent called `ls` first (worked), but then tried `read_file` with empty path.

**Why?**
1. `ls .` returned directory listing (files exist!)
2. But LLM doesn't know how to parse the output
3. LLM tries to read files but with empty paths

### **Solution Strategy**

We need to:

1. **Fix #2.1**: Customize FilesystemMiddleware system prompt (not agent_factory)
2. **Fix #2.2**: Add hard validation at FilesystemBackend level
3. **Fix #2.3**: Provide explicit file list in context before Phase 4

---

## 🔧 Implementation Plan

### **Fix 2.1: FilesystemMiddleware Custom Prompt**

**Location**: `agents/agent_factory.py` → Update `create_code_synthesis_agent()`

Replace current implementation with:
```python
def create_code_synthesis_agent(...):
    backend = FilesystemBackend(root_dir=codebase_path)
    
    # Phase 4 system prompt (as before)
    phase4_prompt = f"""..."""
    
    # NEW: FilesystemMiddleware system prompt override
    filesystem_system_prompt = """\
FILESYSTEM TOOLS CRITICAL REQUIREMENTS:
======================================

When using filesystem tools, ALWAYS provide complete, absolute file paths:

read_file(path: str):
  - path MUST be absolute (e.g., /path/to/codebase/src/main/java/Model.java)
  - path MUST NOT be empty
  - ALWAYS use the full path from root, NOT relative paths

write_file(path: str, content: str):
  - path MUST be absolute
  - path MUST NOT be empty
  - content MUST NOT be empty

edit_file(path: str, search_string: str, replace_string: str):
  - path MUST be absolute
  - search_string and replace_string MUST NOT be empty

BEFORE calling tools:
1. First call ls . to see file structure
2. Parse the output to identify actual files
3. Build COMPLETE absolute paths using those file names
4. NEVER call tools with empty parameters

Example sequence:
  1. ls . → See "src/main/java/com/example" exists
  2. read_file("/full/path/to/src/main/java/com/example/Application.java")
  3. edit_file("/full/path/...", search_string="...", replace_string="...")
"""
    
    agent_kwargs = {
        "system_prompt": phase4_prompt,
        "model": analysis_model,
        "backend": backend,
        "middleware": [
            FilesystemMiddleware(
                backend=backend,
                system_prompt=filesystem_system_prompt,
                custom_tool_descriptions={
                    "read_file": "Read file with ABSOLUTE path (e.g., /path/to/file.java). NEVER use empty path.",
                    "write_file": "Write file with ABSOLUTE path and complete content. Path and content MUST NOT be empty.",
                    "edit_file": "Edit file with ABSOLUTE path. All parameters required: path, search_string, replace_string.",
                    "ls": "List directory contents to discover files before using their paths."
                }
            )
        ]
    }
    
    return create_deep_agent(**agent_kwargs)
```

**Benefit**: 
- Direct injection into FilesystemMiddleware
- LLM gets explicit guidance before each tool call
- Custom descriptions reinforce requirements

---

### **Fix 2.2: Validation at Backend Level**

**Location**: `agents/agent_factory.py` → Add wrapper around backend

```python
from deepagents.backends import FilesystemBackend

class ValidatingFilesystemBackend(FilesystemBackend):
    """FilesystemBackend with hard validation for required parameters"""
    
    def invoke(self, tool_input: dict, **kwargs):
        # Validate required fields based on tool name
        tool_name = tool_input.get("tool_name")
        
        if tool_name in ["read_file", "edit_file", "write_file"]:
            file_path = tool_input.get("path") or tool_input.get("file_path")
            
            if not file_path or file_path.strip() == "":
                # HARD STOP: Don't allow empty paths
                error_msg = f"{tool_name} requires non-empty path parameter. Got empty path."
                tool_input["error"] = error_msg
                return {
                    "error": error_msg,
                    "tool_name": tool_name,
                    "success": False
                }
        
        # If validation passed, proceed normally
        return super().invoke(tool_input, **kwargs)
```

Then use in agent creation:
```python
backend = ValidatingFilesystemBackend(root_dir=codebase_path)
```

**Benefit**:
- Catches empty paths before FilesystemBackend processes them
- Forces error instead of silent failure
- Agent learns not to use empty paths

---

### **Fix 2.3: Pre-load File List Context**

**Location**: `agents/agent_factory.py` → Before calling agent

```python
def create_code_synthesis_agent(...):
    # Get list of relevant files from codebase
    import os
    relevant_files = []
    for root, dirs, files in os.walk(codebase_path):
        for file in files:
            if file.endswith(('.java', '.xml', '.properties', '.sql')):
                full_path = os.path.join(root, file)
                relevant_files.append(full_path)
    
    # Add file list to prompt context
    files_list_str = "\n".join([f"  - {f}" for f in relevant_files[:50]])  # Top 50
    if len(relevant_files) > 50:
        files_list_str += f"\n  ... and {len(relevant_files) - 50} more files"
    
    phase4_prompt = f"""...
    
AVAILABLE FILES IN CODEBASE:
{files_list_str}

When using filesystem tools, select paths ONLY from this list.
Do NOT hallucinate or guess file paths.
"""
    
    return create_deep_agent(...)
```

**Benefit**:
- LLM sees actual files, not guessing
- Reduces path hallucination
- Grounds model in reality

---

## 📈 Expected Outcomes After Fixes

### **Before Fixes**
```
Phase 4: 251.75s total
  - 30s timeout (phase 1)
  - 60s timeout (phase 2)  
  - 120s timeout (phase 3)
  - 20+ empty path errors
  - 0 files created
```

### **After Fixes**
```
Phase 4: < 60s total
  - No timeouts (efficient tool use)
  - 0 empty path errors (validation catches them)
  - 3-5 files created (patches extracted)
  - Clear, actionable error messages if failures occur
```

---

## 🚀 Implementation Sequence

1. **Step 1**: Add `FilesystemMiddleware` with custom system prompt (Fix 2.1)
   - File: `agents/agent_factory.py`
   - Time: ~15 minutes
   - Risk: Low (just prompt injection)

2. **Step 2**: Create `ValidatingFilesystemBackend` wrapper (Fix 2.2)
   - File: `agents/agent_factory.py` or new file
   - Time: ~20 minutes
   - Risk: Medium (behavioral change)

3. **Step 3**: Pre-load file list into context (Fix 2.3)
   - File: `agents/agent_factory.py`
   - Time: ~10 minutes
   - Risk: Low (context enhancement only)

4. **Step 4**: Test with agent
   - Feature: "Add voucher management"
   - Expected: < 60s, files created, no empty paths

5. **Step 5**: Verify all 3 original fixes still work
   - Run verification script again
   - Confirm metrics: 3+ files, 500+ LOC, 0 errors

---

## 🎯 Key Insights

### **Why This Architecture Problem Exists**

1. **DeepAgent abstraction vs. Reality**
   - DeepAgent promises automated file handling
   - But LLM needs guidance on WHICH files to use
   - Documentation shows custom prompts are way to go

2. **Prompt Engineering ≠ System Architecture**
   - Adding prompts to agent_factory only affects general behavior
   - FilesystemMiddleware is separate layer with its own prompt
   - We need to target the RIGHT layer

3. **Validation Trap**
   - DeepAgent validates but continues on error
   - "Tool validation skipped" = silent failure
   - Need hard stop for empty paths

4. **Context Window Challenge**
   - LLM loses track of actual files
   - Needs explicit file list reminder
   - Pre-loading solves this

---

## 📚 References

**LangChain DeepAgent Docs**:
- FilesystemMiddleware system_prompt parameter
- Custom tool descriptions for guidance
- Backend abstraction for validation

**Key Finding**:
```python
FilesystemMiddleware(
    system_prompt="...",  # ← Override this, not agent prompt!
    custom_tool_descriptions={...}
)
```

This is what we missed in Fix #2!

---

## ✅ Checklist Before Implementation

- [ ] Backup current `agents/agent_factory.py`
- [ ] Review FilesystemMiddleware docs once more
- [ ] Create ValidatingFilesystemBackend class
- [ ] Add file list context to prompt
- [ ] Test with voucher management feature
- [ ] Verify no regressions in Phase 1-3
- [ ] Check Phase 4 runtime (target: <60s)
- [ ] Measure files created and LOC

