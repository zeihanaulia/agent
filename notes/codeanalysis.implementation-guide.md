# Code Locations & Implementation Guide

**Status:** READY FOR IMPLEMENTATION  
**Last Updated:** 2025-11-12

---

## FIX #1: DeepAgent Result Parsing

### Location
**File:** `scripts/coding_agent/flow_synthesize_code.py`  
**Lines:** 47-113  
**Function:** `extract_patches_from_result()`

### Current Code (BROKEN)
```python
def extract_patches_from_result(result, progress=None):
    patches = []
    
    # ❌ PROBLEM: Only checks for "messages" key
    if result and isinstance(result, dict) and "messages" in result:
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls"):
                for call in getattr(msg, "tool_calls", []):
                    # extract tool calls...
    
    return patches  # Returns empty if format doesn't match!
```

### Fix Implementation

Add fallback format handlers:

```python
def extract_patches_from_result(result, progress=None):
    patches = []
    
    if not result:
        return patches
    
    # Format 1: LangChain style (current)
    if isinstance(result, dict) and "messages" in result:
        print("  ℹ️ Using format: messages-based (LangChain)")
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls"):
                for call in getattr(msg, "tool_calls", []):
                    patches.extend(_extract_patch_from_call(call, progress))
    
    # Format 2: DeepAgent style with tool execution log
    elif isinstance(result, dict) and "tool_execution_log" in result:
        print("  ℹ️ Using format: tool_execution_log (DeepAgent)")
        for log_entry in result.get("tool_execution_log", []):
            if log_entry.get("tool") in ["write_file", "edit_file"]:
                patch = _extract_patch_from_log_entry(log_entry, progress)
                if patch:
                    patches.append(patch)
    
    # Format 3: Direct response with tool calls
    elif isinstance(result, dict) and "response" in result:
        print("  ℹ️ Using format: response field")
        response_text = result.get("response", "")
        patches.extend(_extract_patches_from_text(response_text, progress))
    
    # Format 4: String response (parse for tool calls)
    elif isinstance(result, str):
        print("  ℹ️ Using format: string response")
        patches.extend(_extract_patches_from_text(result, progress))
    
    # Format 5: Check for common alternate field names
    elif isinstance(result, dict):
        print("  ℹ️ Using format: generic dict")
        for key in ["output", "result", "data", "tool_calls"]:
            if key in result:
                patches.extend(_extract_patches_from_field(key, result[key], progress))
    
    return patches


def _extract_patch_from_call(call, progress=None):
    """Extract patch from LangChain tool call"""
    patches = []
    if call.get("name") in ["write_file", "edit_file"]:
        tool_args = call.get("args", {})
        # ... rest of current extraction logic ...
    return patches


def _extract_patch_from_log_entry(log_entry, progress=None):
    """Extract patch from DeepAgent log entry"""
    tool_name = log_entry.get("tool", "")
    if tool_name == "write_file":
        file_path = log_entry.get("path") or log_entry.get("file")
        content = log_entry.get("content") or log_entry.get("output", "")
        if file_path and content:
            return {"tool": "write_file", "file": file_path, "args": {"path": file_path, "content": content}}
    
    elif tool_name == "edit_file":
        file_path = log_entry.get("path") or log_entry.get("file")
        old_string = log_entry.get("oldString") or log_entry.get("old", "")
        new_string = log_entry.get("newString") or log_entry.get("new", "")
        if file_path and old_string and new_string:
            return {"tool": "edit_file", "file": file_path, "args": {"path": file_path, "oldString": old_string, "newString": new_string}}
    
    return None


def _extract_patches_from_text(response_text, progress=None):
    """Try to extract patches from string response"""
    # Could parse for patterns like "write_file(" or JSON blocks
    # For now: return empty, can enhance later
    return []
```

### Testing This Fix

```python
# Test it works with different formats
test_results = [
    # Format 1: messages
    {"messages": [{"tool_calls": [{"name": "write_file", "args": {"path": "/file.java", "content": "code"}}]}]},
    
    # Format 2: tool_execution_log
    {"tool_execution_log": [{"tool": "write_file", "path": "/file.java", "output": "code"}]},
    
    # Format 3: response field
    {"response": "Created /file.java"},
    
    # Format 4: string
    "Successfully wrote /file.java",
]

for i, result in enumerate(test_results):
    patches = extract_patches_from_result(result)
    print(f"Format {i+1}: {len(patches)} patches extracted")
```

---

## FIX #2: Tool Parameter Validation

### Location
**File:** `scripts/coding_agent/agents/agent_factory.py`  
**Lines:** 68-105  
**Function:** `create_code_synthesis_agent()`

### Current Code (INCOMPLETE)
```python
def create_code_synthesis_agent(...):
    prompt = f"""\
You are an expert software engineer...

Your task:
1. Read existing code files...
2. Plan implementation...
...
6. Use edit_file and write_file tools to implement changes  ← ❌ VAGUE
7. Follow existing code style exactly...
8. DO NOT add new dependencies...
9. Ensure code compiles immediately...
"""
```

### Fix Implementation

Replace tool usage section:

```python
def create_code_synthesis_agent(...):
    prompt = f"""\
You are an expert software engineer implementing a feature with production-quality standards.

CODEBASE: {codebase_path}

Your task:
1. Read existing code files to understand patterns, naming conventions, imports
2. Plan implementation using write_todos with specific file changes
3. Follow SOLID principles (SRP, OCP, LSP, ISP, DIP)
4. Use appropriate design patterns (Factory, Strategy, Decorator, etc)
5. Write testable code: dependency injection, pure functions, isolated concerns

=== CRITICAL: TOOL USAGE ===

WRITE_FILE - Creating new files:
✅ CORRECT FORMAT:
   write_file(
       path="/full/path/to/FileName.java",
       content="package ...\\n\\npublic class FileName {{ ... }}"
   )

✅ REQUIREMENTS:
   - "path" key: MUST be absolute/relative path with file extension
   - "content" key: MUST contain COMPLETE valid code
   - MUST include all imports, package declarations
   - NEVER use placeholders like "//..."

❌ WRONG - NEVER DO THIS:
   write_file()                         ← Missing both parameters!
   write_file({})                       ← Empty dict!
   write_file(path="/file.java")        ← Missing content!
   write_file(content="class X")        ← Missing path!
   write_file(path=None, content="")    ← Empty values!


EDIT_FILE - Modifying existing files:
✅ CORRECT FORMAT:
   edit_file(
       path="/full/path/to/ExistingFile.java",
       oldString="    public String getOrder() {{\\n        return ...;\\n    }}",
       newString="    public String getOrderStatus() {{\\n        return status;\\n    }}"
   )

✅ REQUIREMENTS:
   - "path" key: MUST be exact file path
   - "oldString" key: MUST match EXACTLY (including whitespace, newlines)
   - "newString" key: MUST be complete replacement code
   - Use \\n for line breaks in multi-line strings

❌ WRONG - NEVER DO THIS:
   edit_file()                                  ← Missing all!
   edit_file(path="/file.java")                 ← Missing old/new!
   edit_file(path="/file.java", oldString="a") ← Missing newString!
   edit_file(path="", oldString="", newString="") ← All empty!


SEQUENCE:
1. Plan with write_todos
2. Read files with read_file (understand context)
3. Use write_file for NEW files (in planned order)
4. Use edit_file for EXISTING files
5. STOP - do not loop or re-read

6. Use edit_file and write_file tools to implement changes
7. Follow existing code style exactly (naming, formatting, structure)
8. DO NOT add new dependencies - use only what's already in pom.xml/package.json
9. Ensure code compiles/runs immediately without config changes

Generate production-grade code that fellow engineers would be proud to review.
"""
```

### Verification Checklist

After implementing, check logs for:
- ✅ No `<missing path>` in tool logs
- ✅ All `write_file` calls include both path and content
- ✅ All `edit_file` calls include path, oldString, newString
- ✅ No `args: {}` empty parameter messages
- ✅ Phase 4 completes in < 120 seconds
- ✅ Progress shows files being created

---

## FIX #3: Feature Scope Guard

### Location
**File:** `scripts/coding_agent/flow_parse_intent.py`  
**Lines:** Build analysis prompt (need to search for current location)  
**Function:** Wherever `flow_parse_intent()` builds the LLM prompt

### How to Find It

```bash
grep -n "Your task" scripts/coding_agent/flow_parse_intent.py | head -1
```

Should show something like:
```
123: Your task:
```

### Current Code

Search for section that says:
```python
prompt = f"""
You are an expert software architect...

FEATURE REQUEST: {feature_request}
...
Your task:
1. Parse feature requirements
2. Identify affected files
...
"""
```

### Fix Implementation

Add this section AFTER the feature request and BEFORE "Your task":

```python
prompt = f"""
You are an expert software architect analyzing codebase impact.

FEATURE REQUEST: {feature_request}

=== SCOPE CONSTRAINT (IMPORTANT) ===

Your analysis MUST focus EXCLUSIVELY on implementing:
"{feature_request}"

DO NOT expand scope by adding features like:
❌ Authentication/Login (unless user specifically requested)
❌ Payment/Billing (unless user specifically requested)
❌ Caching layer (unless user specifically requested)
❌ Message queues/Async (unless user specifically requested)
❌ Notification service (unless user specifically requested)

If you identify features that MIGHT be beneficial but are NOT in the user request:
1. Do NOT plan them
2. Do NOT add them to TODO
3. DO mark as [OUT_OF_SCOPE] in notes section

FOCUS: Only implement what user explicitly asked for.

=== END SCOPE CONSTRAINT ===

Your task:
1. Parse feature requirements
2. Identify affected files ONLY for requested feature
3. Plan architecture ONLY for requested scope
4. Create TODO with ONLY requested tasks
5. DO NOT add tasks for out-of-scope features
...
"""
```

### Where to Add This

In the function that builds the analysis prompt for Phase 2, after setting `FEATURE REQUEST` string.

### Verify Fix

After implementing, check output for:
- ❌ No Payment features in TODO when not requested
- ❌ No Shipping features in TODO when not requested
- ✅ Only Order-related files planned for Order feature
- ✅ TODO item count matches scope (not inflated)

---

## Implementation Checklist

```
BEFORE YOU START:
☐ Create feature branch: git checkout -b fix/agent-issues
☐ Create backup: cp flow_synthesize_code.py flow_synthesize_code.py.bak
☐ Note current line numbers for each file

FIX #1 (DeepAgent Result Parsing):
☐ Read entire extract_patches_from_result() function
☐ Add helper functions: _extract_patch_from_call, _extract_patch_from_log_entry, etc
☐ Replace main if condition with if/elif chain for 5 formats
☐ Test with sample DeepAgent results
☐ Verify no syntax errors: python -m py_compile flow_synthesize_code.py

FIX #2 (Tool Parameter Validation):
☐ Open agent_factory.py
☐ Find create_code_synthesis_agent() function
☐ Find the system prompt string
☐ Locate "6. Use edit_file and write_file tools..." line
☐ Replace entire tool usage section with enhanced prompt
☐ Add explicit examples and ❌ WRONG patterns
☐ Verify prompt is valid Python string

FIX #3 (Feature Scope Guard):
☐ Find flow_parse_intent.py
☐ Locate where feature prompt is built
☐ Find line with "FEATURE REQUEST: {feature_request}"
☐ Add SCOPE CONSTRAINT section after it
☐ Include [OUT_OF_SCOPE] marking instruction
☐ Test: Run agent and verify no extra features in TODO

TESTING EACH FIX:
☐ Run with simple feature: "Add Product entity"
  Expected: 1-2 files, 0 hallucinations
  
☐ Run with order feature: "Add order management with status tracking"
  Expected: Only Order files, NO Payment files
  
☐ Check logs for tool parameter issues:
  Expected: All write_file calls with path and content
  
☐ Verify progress tracker shows > 0%:
  Expected: Files created, lines of code > 0
```

---

## Expected Improvements After All Fixes

### Before Fixes

```
Phase 4 Execution (2.9 min):
  - 20+ read_file → <missing path>
  - 10+ edit_file → <missing path>
  - Timeout after 120s
  - Result: 0 patches extracted
  - Output: "✅ No code patches generated"

Progress:
  📈 Overall Progress: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0.0%
  ✅ Completed: 0/3 files
  ⏳ Pending: 3/3 files
  📊 Total Lines of Code: 0
```

### After Fixes

```
Phase 4 Execution (< 60 sec):
  - read_file /file.java ✅
  - write_file /Order.java (250 lines) ✅
  - write_file /OrderService.java (180 lines) ✅
  - write_file /OrderController.java (200 lines) ✅
  - Result: 3 patches extracted
  - Output: "✅ Generated 3 code change(s)"

Progress:
  📈 Overall Progress: [██████████████████████████████████████████████████░░] 90.0%
  ✅ Completed: 3/3 files
  ⏳ Pending: 0/3 files
  📊 Total Lines of Code: 630
```

---

## Success Metrics

After implementing all 3 fixes:

| Metric | Before | After |
|--------|--------|-------|
| Files created | 0 | 3 |
| Lines of code | 0 | 500+ |
| Phase 4 duration | 120s (timeout) | < 60s |
| Progress completion | 0% | 80-100% |
| Hallucinated features | 3-4 | 0 |
| Empty path warnings | 20+ | 0 |
| Patches generated | 0 | 3+ |
| Success rate | 0% | 80%+ |

---

## Rollback Plan

If something breaks:

```bash
# Restore from backup
cp flow_synthesize_code.py.bak flow_synthesize_code.py

# Revert agent factory
git checkout scripts/coding_agent/agents/agent_factory.py

# Revert parse intent
git checkout scripts/coding_agent/flow_parse_intent.py

# Test that original works
python scripts/coding_agent/feature_by_request_agent_v3.py --feature-request "test"
```

---

## Next Actions

1. ✅ Root cause analysis COMPLETE (this document)
2. ⏳ Implement Fix #1: Result parsing (start here)
3. ⏳ Implement Fix #2: Tool parameters
4. ⏳ Implement Fix #3: Scope guard
5. ⏳ Test with multiple features
6. ⏳ Create summary of improvements

