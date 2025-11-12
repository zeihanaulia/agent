# Quick Reference: Functions to Remove/Refactor

## Status Summary

**Current File**: `flow_parse_intent.py` (2,475 lines)  
**Post-Cleanup Target**: ~2,200 lines (save ~275 lines)  

---

## 3 Functions Analysis

### 1️⃣ `create_intent_parser_agent()` - LINE 2189
```
❌ UNUSED - DELETE IMMEDIATELY
   └─ Never called in main flow
   └─ Dead code from previous refactoring
   └─ ~50 lines
```

**Before**:
```python
def create_intent_parser_agent(analysis_model: Any):
    """Alternative to direct LLM..."""
    # 50 lines of code
    return create_deep_agent(system_prompt=prompt, model=analysis_model)
```

**After**: DELETE ✂️

---

### 2️⃣ `extract_tasks_from_response()` - LINE 463
```
⚠️ REDUNDANT - REMOVE
   └─ Unreliable regex extraction from unstructured LLM output
   └─ generate_structured_todos() overwrites it anyway (Line 1894)
   └─ ~30 lines
   └─ Called at Line 1859 (can be simplified)
```

**Before**:
```python
# Line 1859
todos_found = extract_tasks_from_response(response_text)  # Often empty!

# Line 1894
todo_list = generate_structured_todos(...)  # Overwrites todos_found
```

**After**: DELETE, replace with `todos_found = []`

---

### 3️⃣ `build_intent_prompt()` - LINE 775
```
⚠️ PARTIALLY REDUNDANT - REMOVE
   └─ DeepAgent's build_comprehensive_spec_analysis_prompt() does everything better
   └─ Result not effectively used (tasks extracted unreliably)
   └─ ~115 lines
   └─ Also: Remove entire STEP 2 (Lines 1836-1850)
```

**Current Problem**:
```python
# STEP 1: Deep analysis via DeepAgent (structured, comprehensive)
deep_analysis_result = spec_analyzer.invoke(...)  # ✓ Excellent

# STEP 2: Standard analysis via LLM (unstructured, redundant)
prompt = build_intent_prompt(...)  # ← REDUNDANT
response = analysis_model.invoke([...])  # ← Unnecessary LLM call
todos_found = extract_tasks_from_response(response_text)  # ← Unreliable

# STEP 3: Generate todos anyway
todo_list = generate_structured_todos(...)  # ← OVERWRITES everything
```

**After**: DELETE both function and its call site

---

## Removal Impact

### Lines Saved
| Item | Lines | Type |
|------|-------|------|
| `create_intent_parser_agent()` | ~50 | Function def |
| `build_intent_prompt()` | ~115 | Function def |
| `extract_tasks_from_response()` | ~30 | Function def |
| Call to `extract_tasks_from_response()` | ~5 | Code logic |
| STEP 2 (build_intent_prompt call + LLM) | ~20 | Code logic |
| **TOTAL** | **~220 lines** | **Code saved** |

### Performance Gains
- **LLM calls**: 2 → 1 (50% reduction)
- **Extraction attempts**: 2 regex patterns → 0
- **Failure modes**: Multiple → Single (JSON parsing)

### Code Quality
- **Cyclomatic complexity**: Reduced (fewer branches)
- **Function count**: 20 → 17
- **Maintainability**: Improved (clearer flow)

---

## Implementation Order

### Phase 1: Delete (5 min)
```python
# DELETE Line 2189-2237
def create_intent_parser_agent(analysis_model: Any):
    ...
```

### Phase 2: Remove & Simplify (10 min)
```python
# DELETE Line 463-491
def extract_tasks_from_response(response_text: str) -> List[Dict[str, str]]:
    ...

# CHANGE Line 1859
- todos_found = extract_tasks_from_response(response_text)
+ todos_found = []  # Extracted from deep analysis if needed
```

### Phase 3: Remove Redundant Analysis (10 min)
```python
# DELETE Line 775-887
def build_intent_prompt(...):
    ...

# DELETE Lines 1836-1850 (entire STEP 2 section)
# prompt = build_intent_prompt(...)
# response = analysis_model.invoke([...])
# response_text = ...
# todos_found = ...  (already handled above)
# affected_files = ...  (use filesystem scan instead)
```

### Phase 4: Validate (10 min)
```bash
# Run test
python3 scripts/coding_agent/flow_parse_intent.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request-spec scripts/coding_agent/studio.md

# Expected: Same output, 50% faster
```

---

## ✅ Validation Checklist

After cleanup:
- [ ] File compiles without errors
- [ ] `flow_parse_intent()` runs successfully
- [ ] Deep analysis identifies 9 feature areas
- [ ] Entities: [InventoryTransaction, Product, Category]
- [ ] Todo list: 65 tasks, 7 phases
- [ ] Files planning: 21 new files
- [ ] No imports of deleted functions elsewhere
- [ ] Performance: Faster (fewer LLM calls)

---

## 🔗 See Also
- `codeanalysis.flow-parse-intent-cleanup-analysis.md` - Detailed analysis
- `codeanalysis.deepagent-spec-analyzer-enhancement.md` - DeepAgent integration
- `session-summary-deepagent-enhancement.md` - Session summary
