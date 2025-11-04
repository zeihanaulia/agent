# 🛡️ Middleware Guardrail Fix - Complete Guide

## Problem Summary

The `FileScopeGuardrail` middleware was blocking legitimate file modifications because:

1. **Narrow Scope**: Phase 3 (impact analysis) returned only 1-2 files in `affected_files`
2. **Strict Validation**: Phase 4 agent tried to modify multiple related files (controller, service, model)
3. **False Positives**: All files outside the whitelist were treated as violations and blocked
4. **Poor Debugging**: No visibility into why guardrail was blocking execution

**Result**: ❌ `🛑 GUARDRAIL VIOLATION - EXECUTION BLOCKED`

## Solution Overview

### 1. **Automatic Scope Expansion** ✅

The middleware now intelligently expands the allowed scope to include sibling files:

```python
if expand_scope and os.path.dirname(abs_path).endswith(("controller", "service", "model", ...)):
    folder = os.path.dirname(abs_path)
    for fname in os.listdir(folder):
        if fname.endswith((".java", ".py", ".ts")):
            normalized_files.append(os.path.join(folder, fname))
```

**Effect**: If Phase 3 detects `UserController.java`, the guardrail automatically allows:
- `UserController.java`
- `UserService.java`
- `User.java` (other files in same `controller/` or `service/` folder)

### 2. **Path Normalization & Deduplication** ✅

All paths are normalized to absolute paths with intelligent matching:

```python
def _normalize_file_paths(affected_files, codebase_root, expand_scope=True):
    # Convert relative → absolute
    # Expand scope → sibling files
    # Deduplicate → single clean list
```

**Effect**: No more duplicates, consistent path handling across the system.

### 3. **Fallback for Empty Scope** ✅

If Phase 3 returns no files (parsing failure), fallback to minimal scope:

```python
if not affected_files:
    affected_files = [os.path.join(codebase_root, "src")]
```

**Effect**: Agent can still operate, not completely blocked.

### 4. **Soft Mode (Debug/Warning-Only)** ✅

New `soft_mode` parameter disables blocking but still logs violations:

```python
# Hard mode (default): Block violations
middleware = create_phase4_middleware(..., enable_guardrail=True)

# Soft mode (debug): Warn only, don't block
middleware = create_phase4_middleware(..., enable_guardrail=True, soft_mode=True)

# No guardrail (full debug): Disable guardrail entirely
middleware = create_phase4_middleware(..., enable_guardrail=False)
```

**Effect**: Easy debugging without removing safety checks entirely.

### 5. **Enhanced Logging** ✅

Detailed logging at every stage:

```python
✅ Guardrail Scope Configuration:
  • /Users/.../src/main/java/com/example/controllers/UserController.java
  • /Users/.../src/main/java/com/example/services/UserService.java
  • /Users/.../src/main/java/com/example/models/User.java
  ... and 2 more file(s)

🛡️  Guardrails: ENABLED
```

**Effect**: Clear visibility into what guardrail allows/blocks.

---

## Implementation Details

### Updated Functions

#### 1. `_normalize_file_paths()` - NEW

```python
def _normalize_file_paths(
    affected_files: List[str],
    codebase_root: str,
    expand_scope: bool = True
) -> List[str]:
    """
    Normalize and expand file paths for guardrail scope.
    
    Returns: List of normalized absolute paths (deduplicated)
    """
```

**Key Features**:
- Converts relative paths to absolute
- Optionally expands scope to sibling files
- Handles non-existent files gracefully
- Deduplicates results

---

#### 2. `create_phase4_middleware()` - UPDATED

**Before**:
```python
def create_phase4_middleware(feature_request, affected_files, codebase_root):
    return [
        TraceLoggingMiddleware(),
        IntentReminderMiddleware(feature_request, affected_files),
        FileScopeGuardrail(affected_files),
        ToolCallValidationMiddleware(affected_files, codebase_root),
    ]
```

**After**:
```python
def create_phase4_middleware(
    feature_request: str,
    affected_files: List[str],
    codebase_root: str,
    enable_guardrail: bool = True,        # 🆕 Toggle guardrail
    expand_scope: bool = True             # 🆕 Auto-expand scope
) -> List[AgentMiddleware]:
    # 1. Normalize paths automatically
    normalized_files = _normalize_file_paths(affected_files, codebase_root, expand_scope)
    
    # 2. Log scope for debugging
    print("✅ Guardrail Scope Configuration:")
    ...
    
    # 3. Compose middleware with optional guardrails
    middleware = [TraceLoggingMiddleware(), IntentReminderMiddleware(...)]
    if enable_guardrail:
        middleware.extend([FileScopeGuardrail(...), ToolCallValidationMiddleware(...)])
    return middleware
```

---

#### 3. `FileScopeGuardrail` - ENHANCED

**New Parameters**:
```python
def __init__(
    self,
    allowed_files: List[str],
    soft_mode: bool = False,              # 🆕 Warning-only mode
    verbose: bool = False                 # 🆕 Detailed logging
):
```

**New Methods**:
```python
def _normalize_path(self, path: str) -> str:
    """Normalize path for comparison (handles case, separators)"""

def _is_allowed(self, file_mention: str) -> bool:
    """Intelligent matching: exact, suffix, or sibling check"""
```

**New Logic**:
- Soft mode: ⚠️ warns instead of blocking
- Verbose mode: prints detailed logs
- Better path matching (handles relative/absolute)

---

#### 4. `ToolCallValidationMiddleware` - ENHANCED

**New Parameters**:
```python
def __init__(
    self,
    allowed_files: List[str],
    codebase_root: str,
    soft_mode: bool = False,              # 🆕 Warning-only mode
    verbose: bool = False                 # 🆕 Detailed logging
):
```

**New Method**:
```python
def _is_allowed(self, abs_path: str) -> bool:
    """
    Intelligent path validation supporting:
    - Exact matches
    - Sibling files in same directory
    - Files within allowed directories
    """
```

---

## Usage Examples

### Example 1: Standard Usage (Recommended)

```python
from scripts.middleware import create_phase4_middleware

# Phase 3 returns affected_files = ["src/UserController.java"]
middleware = create_phase4_middleware(
    feature_request="Add user API endpoint",
    affected_files=["src/UserController.java"],
    codebase_root="/path/to/project",
    # Default: enable_guardrail=True, expand_scope=True
)

# Result: Guardrail allows:
# - src/UserController.java (exact match)
# - src/UserService.java (sibling in same directory)
# - src/models/User.java (expanded scope)
```

### Example 2: Debug Mode (Soft Mode - Warnings Only)

```python
# Use during development to detect issues without blocking
middleware = create_phase4_middleware(
    feature_request="Add user API endpoint",
    affected_files=["src/UserController.java"],
    codebase_root="/path/to/project",
    enable_guardrail=True,   # Still validate
    expand_scope=True,        # Still expand scope
)

# Then manually create guardrails with soft_mode:
from scripts.middleware import FileScopeGuardrail, ToolCallValidationMiddleware

middleware = [
    ...,
    FileScopeGuardrail(normalized_files, soft_mode=True),
    ToolCallValidationMiddleware(normalized_files, codebase_root, soft_mode=True),
]

# Result: ⚠️ Violations logged but execution continues
```

### Example 3: Full Debug (No Guardrail)

```python
# Disable guardrail entirely for troubleshooting
middleware = create_phase4_middleware(
    feature_request="Add user API endpoint",
    affected_files=["src/UserController.java"],
    codebase_root="/path/to/project",
    enable_guardrail=False,  # 🔓 Disable guardrail
)

# Result: Agent has full access, no file validation
```

### Example 4: Verbose Logging

```python
# See exactly what guardrail is checking
from scripts.middleware import FileScopeGuardrail, ToolCallValidationMiddleware

guardrail = FileScopeGuardrail(allowed_files, soft_mode=False, verbose=True)
validation = ToolCallValidationMiddleware(allowed_files, codebase_root, soft_mode=False, verbose=True)

# Result: Detailed logs for every file check
# ✅ Guardrail check passed: 3 file(s) mentioned, all allowed
# ❌ BLOCKED: File 'src/new/RandomFile.java' is NOT in the allowed list
```

---

## Integration with `feature_by_request_agent_v2.py`

### In Phase 4

```python
def run_code_synthesis_phase(codebase_path, context, spec, impact):
    """Phase 4: Code synthesis with enhanced middleware"""
    
    # 1. Normalize affected files from Phase 3
    affected_files = impact.get("files_to_modify", spec.affected_files)
    
    # 2. Create middleware with automatic scope expansion
    middleware = create_phase4_middleware(
        feature_request=spec.intent_summary,
        affected_files=affected_files,
        codebase_root=codebase_path,
        enable_guardrail=True,      # Default: enabled
        expand_scope=True           # Default: expand to siblings
    )
    
    # 3. Create agent with middleware
    agent = create_code_synthesis_agent(codebase_path, middleware=middleware)
    
    # Now agent can modify:
    # - Files explicitly listed in affected_files
    # - Sibling files in same directory
    # - Files within allowed directories
```

### CLI Integration

```bash
# Standard mode (guardrail enabled, auto-expand scope)
python scripts/feature_by_request_agent_v2.py \
    --codebase-path dataset/codes/springboot-demo \
    --feature-request "Add a new API endpoint /api/users/by-role"

# Debug mode (soft mode - warn only)
python scripts/feature_by_request_agent_v2.py \
    --codebase-path dataset/codes/springboot-demo \
    --feature-request "Add a new API endpoint /api/users/by-role" \
    --debug-mode soft-guardrail

# No guardrail (full debug)
python scripts/feature_by_request_agent_v2.py \
    --codebase-path dataset/codes/springboot-demo \
    --feature-request "Add a new API endpoint /api/users/by-role" \
    --debug-mode no-guardrail
```

---

## Troubleshooting

### Issue: Still Getting "GUARDRAIL VIOLATION"

**Diagnosis**:
1. Check the output for which files are allowed
2. Verify the file the agent is trying to modify

**Solution**:
- Add `verbose=True` to see exact validation logic
- Use `soft_mode=True` to see all violations without blocking
- Check if the file is truly related to the feature

**Example**:
```python
# Add verbose logging
guardrail = FileScopeGuardrail(allowed_files, verbose=True)

# Output will show:
# ✅ Guardrail check passed: 5 file(s) mentioned, all allowed
# OR
# ❌ GUARDRAIL ALERT — 3 file(s) outside scope detected:
#   ❌ src/unrelated/RandomService.java
```

### Issue: Guardrail Too Permissive

**Diagnosis**: Agent modifying too many files

**Solution**:
- Disable scope expansion: `expand_scope=False`
- Use exact file list: Only specify files that truly need changes
- Use explicit validation: `soft_mode=False` (default)

```python
middleware = create_phase4_middleware(
    feature_request=request,
    affected_files=files,
    codebase_root=root,
    expand_scope=False,  # Don't auto-include siblings
)
```

### Issue: Phase 3 Returns Empty/Wrong Files

**Diagnosis**: `affected_files` is empty or contains "TBD - to be determined..."

**Solution**: Fallback is automatic
- Middleware will use `src/` directory as fallback
- Review Phase 3 impact analysis output
- Manually specify affected files

```python
# If Phase 3 returns empty, use this:
affected_files = [
    "src/main/java/com/example/controllers/UserController.java",
    "src/main/java/com/example/services/UserService.java",
]
```

---

## Best Practices

### ✅ DO

1. **Use scope expansion by default**: Helps with related files
2. **Enable guardrails in production**: Safety first
3. **Use verbose mode during testing**: Understand what's happening
4. **Review Phase 3 output**: Ensure accurate file analysis
5. **Log middleware configuration**: Always print allowed files

### ❌ DON'T

1. **Disable guardrails completely** (except debugging): Removes safety
2. **Use soft_mode in production**: Risk of unintended modifications
3. **Ignore guardrail violations**: They indicate scope mismatch
4. **Trust auto-expansion for unrelated files**: Manual review recommended

---

## Configuration Reference

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `enable_guardrail` | bool | `True` | Enable/disable guardrail system |
| `expand_scope` | bool | `True` | Auto-include sibling files |
| `soft_mode` | bool | `False` | Warn instead of block violations |
| `verbose` | bool | `False` | Print detailed validation logs |

### FileScopeGuardrail

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `allowed_files` | List[str] | - | Files allowed to mention in output |
| `soft_mode` | bool | `False` | Warn instead of block violations |
| `verbose` | bool | `False` | Print detailed logs |

### ToolCallValidationMiddleware

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `allowed_files` | List[str] | - | Files allowed to modify |
| `codebase_root` | str | - | Root directory of codebase |
| `soft_mode` | bool | `False` | Warn instead of block violations |
| `verbose` | bool | `False` | Print detailed logs |

---

## LangChain Best Practices Reference

Based on official LangChain documentation:

### Guardrails

- **Purpose**: Validate and filter content at key execution points
- **Patterns**: Deterministic (regex/rules) or model-based (LLM validation)
- **Hooks**: `before_agent`, `after_agent`, `before_model`, `after_model`, `wrap_tool_call`

### Middleware Lifecycle

```
before_agent
    ↓
before_model
    ↓
wrap_model_call
    ↓
after_model
    ↓
wrap_tool_call (for each tool)
    ↓
after_agent
```

### Custom Middleware Pattern

```python
from langchain.agents.middleware import AgentMiddleware

class CustomMiddleware(AgentMiddleware):
    def before_model(self, state, runtime):
        # Modify messages before LLM call
        return {"messages": modified_messages}
    
    def after_model(self, state, runtime):
        # Validate output after LLM call
        if violation:
            return {"messages": [...], "jump_to": "end"}
    
    def wrap_tool_call(self, request, handler):
        # Intercept tool execution
        return handler(request)
```

---

## Changelog

### v2.0 - Guardrail Fix

✅ **Added**:
- `_normalize_file_paths()` function for intelligent scope expansion
- `soft_mode` parameter for warning-only validation
- `verbose` parameter for detailed logging
- `expand_scope` parameter for auto-including sibling files
- Enhanced path matching with directory awareness
- Fallback scope for empty affected_files

✅ **Improved**:
- `create_phase4_middleware()` now handles scope expansion
- `FileScopeGuardrail` with soft mode and verbose logging
- `ToolCallValidationMiddleware` with better path validation
- Logging clarity with emoji indicators

✅ **Fixed**:
- False positive blocks for legitimate sibling files
- Empty affected_files causing complete block
- Poor debugging visibility

---

## Further Reading

- [LangChain Middleware Documentation](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Guardrails Guide](https://docs.langchain.com/oss/python/langchain/guardrails)
- [Custom Middleware Patterns](https://docs.langchain.com/langsmith/custom-middleware)
- [AgentMiddleware API Reference](https://reference.langchain.com/python/langchain/middleware/)
