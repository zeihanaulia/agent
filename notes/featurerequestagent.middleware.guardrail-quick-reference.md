# 🛡️ Guardrail Middleware - Quick Reference

## Key Changes Summary

| Component | Before | After |
|-----------|--------|-------|
| File scope | Only files ❌ | Files + Directories ✅ |
| New file creation | BLOCKED 🛑 | ALLOWED ✅ |
| File matching | Fragile regex | Multi-level matching |
| Tool validation | Empty path crash | Graceful skip |
| enable_guardrail | False (disabled) | True (enabled) |

## How It Works Now

```
Phase 3 finds: ["HelloController.java", "Application.java"]
    ↓
_normalize_file_paths() extracts:
  - Files: ["/path/HelloController.java", "/path/Application.java"]
  - Directories: ["/path/springboot/"]
    ↓
Phase 4 creates middleware with both
    ↓
Agent calls: write_file("UserDTO.java", content="...")
    ↓
ToolCallValidationMiddleware checks:
  1. Is "UserDTO.java" in allowed_files? NO
  2. Is "UserDTO.java" within allowed_dirs? YES (/path/springboot/)
    ↓
✅ ALLOW execution
```

## Testing

### ✅ Test 1: Create file in allowed directory
```bash
python scripts/feature_by_request_agent_v2.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add new API endpoint" \
  --dry-run
```
**Expected:** ✅ Guardrails pass, code generated

### ✅ Test 2: Mention existing file in allowed scope
When agent mentions "HelloController.java", guardrail should recognize it

### ✅ Test 3: Block unauthorized files
If agent tries to modify `/etc/passwd`, should still be blocked:
```
❌ BLOCKED: File '/etc/passwd' is NOT in the allowed list
```

## Configuration

### Enable/Disable Guardrails

**In `feature_by_request_agent_v2.py`, line 435:**
```python
middleware = create_phase4_middleware(
    feature_request=spec.intent_summary,
    affected_files=files_to_modify,
    codebase_root=codebase_path,
    enable_guardrail=True   # ← Toggle here
)
```

### Adjust Sensitivity

**In `middleware.py`, line 575-577:**
```python
if enable_guardrail:
    middleware.extend([
        FileScopeGuardrail(normalized_files, soft_mode=False, verbose=True),  # ← Control here
        ToolCallValidationMiddleware(..., soft_mode=False, verbose=True),      # ← And here
    ])
```

**Options:**
- `soft_mode=False`: Block violations (hard mode)
- `soft_mode=True`: Warn but allow (soft mode)
- `verbose=False`: Quiet mode (production)
- `verbose=True`: Debug mode (development)

## Common Issues & Solutions

### Issue: File mentions not recognized
**Solution:** Improve `FileScopeGuardrail._is_allowed()` matching logic
- Already handles: full paths, relative paths, basenames, partial paths

### Issue: New files still blocked
**Solution:** Ensure directories are extracted
- Check: `"📁 Allowed directories: X dir(s)"` in output
- If missing: Phase 3 might not be finding files correctly

### Issue: Tool calls with empty file path
**Solution:** Already handled with graceful skip
- Output: `⚠️ Tool validation skipped: edit_file has empty file path`
- Agent continues without validation for that call

### Issue: Performance slow
**Solution:** Disable verbose logging
- Set `verbose=False` in `create_phase4_middleware()`
- Reduces console output overhead

## Production Checklist

- [x] `enable_guardrail=True` in feature_by_request_agent_v2.py
- [x] `soft_mode=False` for strict enforcement
- [x] `verbose=False` for production (or keep True for monitoring)
- [x] Directory extraction working
- [x] Multi-level file matching implemented
- [x] Error handling robust
- [x] Test run successful: ✅ COMPLETE with 1 code change

## Debug Commands

```bash
# Run with verbose output to see guardrail decisions
export GUARDRAIL_VERBOSE=1
python scripts/feature_by_request_agent_v2.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Your request" \
  --dry-run

# Check middleware configuration
grep -A 10 "Guardrail Scope Configuration" /tmp/output.log

# See all blocked calls
grep "🛑 HARD MODE" /tmp/output.log

# See all allowed calls
grep "✅ Guardrail check passed" /tmp/output.log
```

## Related Files

- 📄 `scripts/middleware.py` - Guardrail implementation
- 📄 `scripts/feature_by_request_agent_v2.py` - Feature agent with guardrails
- 📝 `notes/middleware.guardrail-bug-analysis.md` - Detailed bug analysis
- 📝 `notes/middleware.guardrail-fix-complete.md` - Full fix documentation

