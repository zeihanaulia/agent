# Deep Dive: Agent Execution Flow & Empty Path Bug

**Analysis Date:** 2025-11-12  
**Root Cause:** DeepAgent return format mismatch in flow_synthesize_code.py

---

## The Real Issue: DeepAgent Response Format

### What `extract_patches_from_result()` Expects

**File:** `scripts/coding_agent/flow_synthesize_code.py`, lines 47-113

```python
def extract_patches_from_result(result: Optional[Dict[str, Any]], progress=None):
    patches = []
    
    if result and isinstance(result, dict) and "messages" in result:  # ← EXPECTS "messages" key
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls"):
                for call in getattr(msg, "tool_calls", []):
                    if call.get("name") in ["write_file", "edit_file"]:
                        tool_args = call.get("args", {})
                        file_path = tool_args.get("path") or tool_args.get("file")
```

**Expected structure:**
```python
result = {
    "messages": [
        {
            "tool_calls": [
                {
                    "name": "write_file",
                    "args": {"path": "/file.java", "content": "..."}
                },
                {
                    "name": "edit_file",
                    "args": {"path": "/file.java", "oldString": "...", "newString": "..."}
                }
            ]
        }
    ]
}
```

### What DeepAgent Actually Returns

**DeepAgent is a custom agent wrapper that:**
1. Takes system prompt and model
2. Calls LLM with tool definitions
3. Internally executes tools
4. Returns final execution result

**Actual DeepAgent return format (based on terminal logs):**
```
🛠️ [TOOL] read_file → <missing path>
✅ [TOOL] read_file completed
```

The format suggests DeepAgent returns something like:
```python
result = {
    "status": "success",
    "tool_execution_log": [
        {"tool": "read_file", "path": None, "output": "..."},
        {"tool": "write_file", "path": None, "output": "..."},
    ]
}
```

OR simply:
```python
result = "Final summary of work done..."  # Just a string, not dict with messages
```

### The Bug: Condition Fails Silently

```python
# Line 65-66 in flow_synthesize_code.py
if result and isinstance(result, dict) and "messages" in result:  # ← This is False!
    # Never executes because DeepAgent result doesn't have "messages" key
    for msg in result.get("messages", []):  # ← Never runs
        # ... extract tool calls ...
```

**When this condition fails:**
1. `patches = []` stays empty
2. No tool calls extracted
3. Code reaches line 572: `if patches:` → False
4. Output: "✅ No code patches generated"

### Why This Looks Like "Empty Path" Bug

The middleware logging happens DURING agent execution:
```
🧩 [MODEL] About to call model...
🛠️ [TOOL] read_file → <missing path>  ← Middleware logs this
✅ [TOOL] read_file completed
```

So we see the logs of attempted tool calls (with missing paths), but then NO patches are extracted because the result format doesn't match expected structure.

**It's TWO separate issues:**
1. **During execution:** Agent calls tools with empty paths (middleware issue)
2. **After execution:** Result format doesn't match expected structure (parsing issue)

---

## Why Paths Are Empty During Execution

Looking at middleware logs:
```
🛠️ [TOOL] read_file → <missing path>
🛠️ [TOOL] grep → args: {}
🛠️ [TOOL] edit_file → <missing path> (replace 0 chars → 0 chars)
```

### Middleware `_format_tool_log()` Function

**File:** `scripts/coding_agent/middleware.py`, lines 69-91

```python
def _format_tool_log(tool_name: str, args: Dict[str, Any]) -> str:
    """Create human-readable trace lines"""
    path = _extract_path(args)  # Line 72
    
    if tool_name == "write_file":
        size = len(args.get("content", ""))
        preview = (args.get("content", "")[:30] + "...") if size > 30 else ""
        return f"write_file → {path or '<missing path>'} (bytes={size})"  # ← Returns this
        
    if tool_name == "read_file":
        return f"read_file → {path or '<missing path>'}"  # ← Returns this
```

When `_extract_path(args)` returns empty string:
- `path or '<missing path>'` → outputs `<missing path>`
- This is just a LOGGING display issue

### The Actual Tool Execution

BUT: The `<missing path>` is logged, which means **args dict WAS extracted but was empty.**

```python
def _extract_path(args: Dict[str, Any]) -> str:
    """Best-effort extraction of path/directory info from tool arguments."""
    for key in ("path", "file", "filePath", "file_path", "directory"):
        value = args.get(key)  # Checking all possible key names
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""  # Returns empty string when no path found
```

**This returns `""` when:**
1. `args` dict is empty `{}`
2. `args` has keys but they're named differently
3. `path` value is None

The tool still executes (hence `✅ [TOOL] read_file completed`), but with empty/invalid parameters.

---

## Cascading Failure Chain

```
1. Phase 3 Agent Execution
   ├─ Calls tools with LLM-generated parameters
   ├─ Middleware extracts tool calls
   ├─ Some tool calls have empty/invalid args
   └─ Logs: "read_file → <missing path>"

2. Timeout/Fallback
   ├─ Phase 3 times out after 30s
   ├─ Returns incomplete analysis
   └─ Result: Empty impact analysis

3. Phase 4 Agent Execution
   ├─ Tries to read files using result from Phase 3
   ├─ Gets no real codebase context
   ├─ Agent repeatedly calls read_file with invalid paths
   ├─ Logs 20+ "read_file → <missing path>" lines
   └─ Loops endlessly trying different approaches

4. Phase 4 Timeout
   ├─ Agent times out after 120s
   ├─ Returns some result format
   └─ Result doesn't have "messages" key

5. Extract Patches Fails
   ├─ `extract_patches_from_result()` checks for "messages" key
   ├─ Key doesn't exist in DeepAgent result
   ├─ Condition `"messages" in result` → False
   ├─ No patches extracted
   ├─ patches = [] (empty)
   └─ Logs: "✅ No code patches generated"

6. No Files Created
   └─ Final progress: 0/3 files, 0 lines of code
```

---

## The Two Separate Fixes Needed

### Fix #1: DeepAgent Result Format Parsing (CRITICAL)

**Problem:** `extract_patches_from_result()` only handles one result format

**Location:** `scripts/coding_agent/flow_synthesize_code.py`, lines 47-113

**Fix:**
```python
def extract_patches_from_result(result, progress=None):
    patches = []
    
    if not result:
        return patches
    
    # Try format 1: LangChain style with "messages" key
    if isinstance(result, dict) and "messages" in result:
        for msg in result.get("messages", []):
            # ... extract from tool_calls ...
    
    # Try format 2: DeepAgent style with tool_execution_log
    elif isinstance(result, dict) and "tool_execution_log" in result:
        for log_entry in result.get("tool_execution_log", []):
            if log_entry.get("tool") in ["write_file", "edit_file"]:
                # ... extract from log_entry ...
    
    # Try format 3: Direct response string (extract mentioned files)
    elif isinstance(result, str) and ("write_file" in result or "edit_file" in result):
        # ... parse string for tool calls ...
    
    # Try format 4: Check result['output'] or result['response']
    elif isinstance(result, dict) and ("output" in result or "response" in result):
        # ... extract from output/response ...
    
    return patches
```

### Fix #2: Prevent Empty Tool Parameters (HIGH)

**Problem:** LLM generates tool calls with empty parameters

**Location:** `scripts/coding_agent/agents/agent_factory.py` (Phase 4 system prompt)

**Current prompt:**
```
6. Use edit_file and write_file tools to implement changes
```

**Enhanced prompt:**
```
6. CRITICAL: Use edit_file and write_file tools with EXPLICIT parameters:
   - write_file: MUST include both "path" AND "content" keys
   - edit_file: MUST include "path", "oldString", AND "newString" keys
   - NEVER call tools with empty or missing parameters
   - Example: write_file(path="/src/File.java", content="full java code here")
   
DO NOT generate tool calls like:
   - write_file({})           ← WRONG: empty params
   - edit_file(path, "", "")  ← WRONG: empty strings
   - write_file(content="...")← WRONG: missing path
```

### Fix #3: Feature Hallucination Prevention (HIGH)

**Problem:** LLM adds features not in user request

**Location:** `scripts/coding_agent/flow_parse_intent.py` (Phase 2 system prompt)

**Add to prompt:**
```
SCOPE CONSTRAINT:
Your analysis MUST focus EXCLUSIVELY on: {user_feature_request}

DO NOT add features like:
❌ Payment processing (unless user requested it)
❌ Authentication (unless user requested it)
❌ Caching layer (unless user requested it)

If you identify additional features that might be needed, mark them as:
[OUT_OF_SCOPE] Feature Name - Reason why it might be useful, but NOT part of current request

Keep focus narrow: Only implement what user explicitly asked for.
```

---

## Detection Checklist for Future Runs

### Sign of Issue #1 (Missing Result Format):

- [ ] Progress shows 0% completion despite long runtime
- [ ] Logs show only `✅ No code patches generated`
- [ ] No "write_file successfully..." messages
- [ ] Progress tracker shows all files as "Pending"
- [ ] Terminal output cuts off at "Step 2: Agent implementing changes..."

### Sign of Issue #2 (Empty Tool Parameters):

- [ ] 20+ lines of `read_file → <missing path>` in logs
- [ ] `edit_file → <missing path>` warnings appear
- [ ] `grep → args: {}` indicates empty argument dict
- [ ] Phase 4 duration > 60s but no actual work done
- [ ] Tool validation skipped messages: "⚠️ Tool validation skipped: edit_file has empty file path"

### Sign of Issue #3 (Hallucination):

- [ ] TODO file lists features NOT in user request
- [ ] Agent mentions services/classes user never asked for
- [ ] Langsmith trace (clean) vs TODO output (extra features) mismatch
- [ ] More files planned than logically needed for feature

---

## Test Plan After Fixes

1. **Run 1:** Simple feature - "Add entity for Product"
   - Should create 1-2 files only
   - Should complete in < 60 seconds
   - Should show progress bar reaching 100%

2. **Run 2:** Feature with scope - "Add order status tracking (no payment, no shipping)"
   - Should explicitly mark Payment/Shipping as out-of-scope
   - Should show only Order-related files created

3. **Run 3:** Verify tool params - "Add notification service"
   - Should show all write_file calls with path AND content
   - Should show no empty parameter warnings
   - Should show actual lines of code generated

---

## Priority Implementation Order

1. **FIRST (2-3 hours):** Fix DeepAgent result parsing
   - Add multiple format handlers in `extract_patches_from_result()`
   - Test with actual DeepAgent returns
   - Verify patches are extracted correctly

2. **SECOND (1-2 hours):** Fix empty tool params
   - Enhance Phase 4 system prompt
   - Add examples of correct tool usage
   - Test agent creates files with populated parameters

3. **THIRD (1-2 hours):** Prevent hallucination
   - Add scope constraint to Phase 2 prompt
   - Mark out-of-scope features in TODO
   - Test with multi-feature scenarios

