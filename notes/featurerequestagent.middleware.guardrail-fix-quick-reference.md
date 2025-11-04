# 🚀 Guardrail Fix - Quick Start

## Problem Fixed ✅

Previously: `🛑 GUARDRAIL VIOLATION - EXECUTION BLOCKED`

**Root Cause**: Middleware's allowed files list was too narrow (1-2 files), but agent needed to modify related files (service, model, etc)

## What Changed

1. **Automatic scope expansion** - Sibling files in same directory auto-included
2. **Path normalization** - Consistent absolute path handling
3. **Soft mode** - Can warn instead of block (for debugging)
4. **Better logging** - Clear visibility into what's allowed
5. **Fallback scope** - Never completely blocked if Phase 3 fails

## How to Use

### Default (Recommended)

```python
from scripts.middleware import create_phase4_middleware

middleware = create_phase4_middleware(
    feature_request="Add user endpoint",
    affected_files=["src/UserController.java"],  # Phase 3 output
    codebase_root="/path/to/project"
    # enable_guardrail=True (default)
    # expand_scope=True (default)
)
```

**Result**: ✅ Agent can modify:
- `src/UserController.java` (exact)
- `src/UserService.java` (sibling)
- `src/models/User.java` (expanded)

### Debug Mode (Warnings Only)

```python
from scripts.middleware import FileScopeGuardrail, ToolCallValidationMiddleware

# Use with soft_mode=True
guardrail = FileScopeGuardrail(allowed_files, soft_mode=True)
validation = ToolCallValidationMiddleware(allowed_files, root, soft_mode=True)

# Result: ⚠️ Violations logged but execution continues
```

### No Guardrail (Full Debug)

```python
middleware = create_phase4_middleware(
    feature_request="...",
    affected_files=[...],
    codebase_root="...",
    enable_guardrail=False  # 🔓 Disable completely
)
```

## Testing

```bash
# Run with default settings
python scripts/feature_by_request_agent_v2.py \
    --codebase-path dataset/codes/springboot-demo \
    --feature-request "Add a new API endpoint /api/users/by-role"

# Should see:
# ✅ Guardrail Scope Configuration:
#   • /path/to/UserController.java
#   • /path/to/UserService.java
#   ... and 2 more file(s)
```

## Configuration

| Setting | What It Does |
|---------|------------|
| `enable_guardrail=True` | ✅ Default - Block violations |
| `enable_guardrail=False` | 🔓 Debug - No guardrail |
| `expand_scope=True` | ✅ Default - Include siblings |
| `expand_scope=False` | 🔒 Strict - Only specified files |
| `soft_mode=True` | ⚠️ Warn only, don't block |
| `verbose=True` | 📋 Detailed logs |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Still getting guardrail block | Use `soft_mode=True` to see what's happening |
| Need to modify more files | Increase Phase 3 `affected_files` list |
| Too permissive | Use `expand_scope=False` |
| Not seeing logs | Use `verbose=True` |

## Files Changed

- `scripts/middleware.py` - Enhanced with scope expansion and soft mode
- `notes/middleware.guardrail-fix.md` - Complete documentation
- `notes/middleware.guardrail-fix-quick-reference.md` - This file

## Key Functions

### `_normalize_file_paths()` - NEW

Normalizes paths and auto-expands scope:
- Converts relative → absolute paths
- Includes sibling files in same directory
- Deduplicates results

### `create_phase4_middleware()` - UPDATED

Now handles:
- Path normalization
- Scope expansion
- Conditional guardrail enabling
- Enhanced logging

### `FileScopeGuardrail` - ENHANCED

New features:
- `soft_mode` - Warn instead of block
- `verbose` - Detailed logs
- Better path matching

### `ToolCallValidationMiddleware` - ENHANCED

New features:
- `soft_mode` - Warn instead of block
- `verbose` - Detailed logs
- Directory-aware validation

## Next Steps

1. ✅ Review `scripts/middleware.py` - Changes applied
2. ✅ Test with default settings - Should work now
3. 📋 If issues, enable `verbose=True`
4. 📖 See `notes/middleware.guardrail-fix.md` for full details
