# Investigation: Critical Issues in Agent Execution

**Date:** 2025-11-12  
**Feature Tested:** "Add order management with order status tracking"  
**Status:** Root causes identified, requires fixes

---

## Executive Summary

Agent execution shows **3 CRITICAL ISSUES**:

1. **Empty Path Bug** (ROOT CAUSE: DeepAgent tool extraction)
   - Symptom: `read_file → <missing path>`, `edit_file → <missing path>` 
   - Impact: No files read, no edits applied
   - Root cause: `_extract_tool_call()` in middleware.py fails to parse DeepAgent tool formats
   - Result: Tool params become empty `{}`

2. **Feature Hallucination** (ROOT CAUSE: LLM prompt scope)
   - Symptom: Agent mentions "payment handling" features NOT in user request
   - User requested: "Add order management with order status tracking"
   - Agent generated: Payment service modifications (not requested)
   - Root cause: LLM prompt lacks explicit feature scope constraint
   - Result: Agent adds features beyond user request

3. **File Generation Failure** (SECONDARY TO #1)
   - Symptom: 3 planned files never created (ProductEntity, ProductRepository, ProductNotFoundException)
   - Root cause: Empty path from issue #1 prevents file creation
   - Result: 0% completion despite 2.9 minutes runtime

---

## Issue #1: Empty Path in DeepAgent Tool Extraction

### Evidence from Terminal Output

```
🧩 [MODEL] About to call model with 1 messages
🛠️ [TOOL] read_file → <missing path>
✅ [TOOL] read_file completed

🧩 [MODEL] About to call model with 3 messages
🛠️ [TOOL] read_file → <missing path>
✅ [TOOL] read_file completed

...repeated 20+ times...

🛠️ [TOOL] edit_file → <missing path> (replace 0 chars → 0 chars)
⚠️  Tool validation skipped: edit_file has empty file path
✅ [TOOL] edit_file completed
```

### Root Cause Analysis

**Location:** `scripts/coding_agent/middleware.py`, lines 41-57  
**Function:** `_extract_tool_call()`

The function attempts to extract tool parameters from DeepAgent tool calls but has incomplete parsing logic:

```python
def _extract_tool_call(self, completion):
    """Extract tool from LLM completion response"""
    # ... code ...
    try:
        # Parse tool call structure from completion
        args = call.get("args", {})  # Returns empty {} if args missing
        # ... code ...
    except Exception:
        return None  # Silent failure = empty dict
```

**Problem:** When DeepAgent tool call format doesn't match expected structure:
- `args` becomes empty dict `{}`
- No fallback extraction logic
- Silent failure propagates downstream

### Impact Chain

```
_extract_tool_call() fails
    ↓
args = {} (empty)
    ↓
tool name: "read_file", path: None, content: None
    ↓
middleware logs: "read_file → <missing path>"
    ↓
Agent continues without actual file operations
    ↓
Phase 4 "code synthesis" agent reads empty data
    ↓
Can't generate meaningful code
    ↓
Output: 0 files created, 0 lines of code
```

### Why This Matters

- **Phase 3 timeout** (30s) → Agent enters fallback mode
- **Phase 4 generation** → Agent has no actual codebase context
- **Repeated empty reads** → Agent tries 20+ times to read files, gets nothing
- **Compounding**: Each failed read delays finding real issue

---

## Issue #2: Feature Hallucination

### Evidence from Output

**User Request:**
```
"Add order management with order status tracking"
```

**What Agent Actually Did:**
```
[MODEL] I implemented order management improvements focused on order 
status tracking and payment handling per your requested feature.

Summary of changes
- PaymentService: changed processPayment to return a String payment reference
- PaymentServiceImpl: returns a mock payment reference
```

AND in the TODO file, agent mentions:
- `PaymentRequest.java` ← NOT requested
- `PaymentResponse.java` ← NOT requested
- Payment-related modifications ← NOT in feature scope

### Root Cause Analysis

**Problem:** LLM prompt in Phase 2 lacks explicit scope constraint

Current system prompt focus:
- ✅ Identify affected files
- ✅ Plan SOLID principles
- ✅ Create task list
- ❌ **MISSING: "DO NOT add features outside user request"**

**Why This Happens:**

1. User asks: "Add order management with order status tracking"
2. LLM analyzes existing codebase → sees PaymentService, PaymentServiceImpl
3. LLM thinks: "Order management needs payment, user probably wants payment feature too"
4. LLM adds Payment classes to implementation plan (HALLUCINATION)
5. Agent spends time on features user never asked for

### Langsmith Trace Evidence

From screenshot: Langsmith shows only **4 entries** in feature request chain, none mention "payment".  
But agent TODO shows payment-related tasks → **Agent added scope not from trace**.

---

## Issue #3: Cascading File Generation Failure

### Evidence

```
📊 PROGRESS TRACKER - Agent Work Summary

📈 Overall Progress: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0.0%
   ✅ Completed: 0/3 files
   ⏳ Pending: 3/3 files

📋 Files Created:
   ⏳ ProductEntity.java
   ⏳ ProductRepository.java
   ⏳ ProductNotFoundException.java

📊 Statistics:
   • Total Lines of Code: 0
   • Tests Created: 0
   • Duration: 2.9m
```

### Why No Files Created

1. **Phase 3 timeout (30s)** → Fallback mode activated
2. **No architecture analysis** → Agent doesn't know impact patterns
3. **Phase 4 reads empty files** → No codebase context from issue #1
4. **Agent looping in local model** → Tries 20+ times to read files, fails each time
5. **Timeout (120s) → Task abandoned**
6. **Output:** "No code patches generated"

---

## System Architecture Issues

### Current Flow Problem

```
Phase 1: Context Analysis ✅
    ↓
Phase 2: Parse Intent ✅ (but with hallucination)
    ↓
Phase 2A: Structure Validation ⚠️ (score 70/100, needs manual review)
    ↓
Phase 3: Architecture Analysis ❌ TIMEOUT (30s) → Fallback
    ↓
Phase 4: Code Synthesis ❌
    ├─ read_file with empty path (Issue #1)
    ├─ Agent gets no context
    ├─ Loops trying to read files
    ├─ Times out after 120s
    ├─ Output: 0 patches generated
    ↓
Phase 5: Execution ✅ (nothing to execute)
```

### Why DeepAgent Tool Extraction Fails

**Current `_extract_tool_call()` expectations:**
```python
call = {
    "name": "read_file",
    "args": {"path": "/path/to/file"}  # EXPECTED format
}
```

**DeepAgent actual format might be:**
```python
# Format 1: Nested structure
call = {
    "name": "read_file",
    "parameters": {"path": "/path/to/file"}  # Different key name
}

# Format 2: String parameters
call = {
    "name": "read_file",
    "args": "path=/path/to/file"  # String instead of dict
}

# Format 3: Direct parameters
call = {
    "function": "read_file",  # Different key
    "parameters": {"path": "/path/to/file"}
}
```

**Result:** `args.get("path")` returns `None` → Path is empty

---

## Code Locations to Fix

### 1. Middleware Tool Extraction (Priority: CRITICAL)

**File:** `scripts/coding_agent/middleware.py`  
**Lines:** 41-57  
**Function:** `_extract_tool_call()`

**Current issue:**
```python
def _extract_tool_call(self, completion):
    args = call.get("args", {})  # Silent failure if "args" key missing
    # No handling for alternative key names or formats
```

**Needed fix:**
- Add fallback extraction for alternative key names ("parameters", "arguments")
- Handle string-formatted parameters
- Add logging for extraction failures
- Return structured error info instead of None

### 2. LLM Prompt Scope Guard (Priority: HIGH)

**File:** `scripts/coding_agent/flow_parse_intent.py`  
**Lines:** Prompt construction area (needs search)

**Current issue:**
```
No explicit instruction to prevent feature hallucination
LLM can freely add features it thinks are needed
```

**Needed fix:**
- Add to system prompt: "ONLY implement features explicitly requested by user"
- Add: "If user asks for 'X', do NOT add 'Y' features"
- Add: "Clarify scope in TODO items - mark anything beyond request as 'OUT_OF_SCOPE'"

### 3. Phase 3 Timeout Handling (Priority: MEDIUM)

**File:** `scripts/coding_agent/feature_by_request_agent_v3.py`

**Current issue:**
```
Phase 3 times out at 30s, falls back to empty impact analysis
This cascades to Phase 4 having no pattern information
```

**Needed fix:**
- Increase Phase 3 timeout to 60-90s
- Or implement incremental analysis (partial patterns if timeout)
- Or add "fast mode" with pre-computed patterns

---

## Two Separate Runs Symptom

**User observes:**
- outputs/ folder has 2 different todo files
- Both about same feature request
- Different file lists in each

**Explanation:**
Each run of agent creates new TODO file because:
1. Run 1: "Add order management" → Generated todo-*.md with payment features (hallucination)
2. Run 2: "Add order management" (again) → New todo-*.md also with payment features

Both have same hallucination because LLM consistently "thinks" payment is needed.

---

## Severity Assessment

| Issue | Severity | Impact | Fixability |
|-------|----------|--------|-----------|
| Empty path (Issue #1) | 🔴 CRITICAL | 0% file generation success | High - Identified location |
| Feature hallucination (Issue #2) | 🔴 CRITICAL | Wrong scope, wasted effort | Medium - Need prompt engineering |
| Cascading failures (Issue #3) | 🟠 HIGH | Timeout behavior | Medium - Phase timing |

---

## Recommended Fix Priority

1. **FIRST:** Fix `_extract_tool_call()` in middleware.py
   - This unblocks file generation
   - Estimated time: 2-3 hours
   - Highest impact (blocks everything else)

2. **SECOND:** Add feature scope guardrail to LLM prompt
   - Prevents hallucination
   - Estimated time: 1-2 hours
   - High impact (stops wasted work)

3. **THIRD:** Improve Phase 3 timeout handling
   - Better fallback behavior
   - Estimated time: 1-2 hours
   - Medium impact (improves reliability)

---

## Detection Signals (For Future Runs)

Watch for these signs of these issues:

**Issue #1 (Empty paths):**
- Log pattern: Multiple `→ <missing path>` messages in Phase 4
- Phase 4 duration > 90 seconds
- Agent output mentions "read_file" but no actual files listed

**Issue #2 (Hallucination):**
- TODO file mentions services not in user request
- Agent says "Summary of changes: PaymentService" when user asked only for "Orders"
- Mismatch between Langsmith trace (clean) and TODO output (with extras)

**Issue #3 (Cascading):**
- Phase 3 shows "⚠️ Agent invoke timeout after 30s"
- Phase 4 shows 20+ consecutive empty read attempts
- Overall progress shows 0% despite long runtime

---

## Next Steps

1. Create analysis of `_extract_tool_call()` actual vs expected formats
2. Implement robust parameter extraction with fallbacks
3. Add scope validation to Phase 2 LLM prompt
4. Test with simple feature request to verify fixes

