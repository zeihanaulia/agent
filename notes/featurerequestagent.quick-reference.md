# Quick Reference: Middleware Components & Integration

## 📋 Files Created

```
scripts/
├── middleware.py                           ← NEW: 3 middleware classes
├── EXECUTIVE_SUMMARY.md                    ← NEW: Quick overview
├── SOLUTION_ARCHITECTURE.md                ← NEW: Deep dive explanation  
├── MIDDLEWARE_IMPLEMENTATION_PLAN.md       ← NEW: Technical spec
├── INTEGRATION_GUIDE.md                    ← NEW: Step-by-step integration
└── feature_by_request_agent_v2.py         ← TO MODIFY: Add middleware
```

---

## 🔧 3 Middleware Components

### Component 1: IntentReminderMiddleware

```python
from middleware import IntentReminderMiddleware

mw = IntentReminderMiddleware(
    feature_request="Add endpoint /api/users/by-role",
    affected_files=["HelloController.java", "UserService.java"]
)

# Hook: before_model
# Effect: Injects reminder at every LLM call
```

**What it does:**
```
Before Model Call:
  state["messages"] ← Prepend system message:
    "🎯 PRIMARY OBJECTIVE: Add endpoint /api/users/by-role"
    "📁 ALLOWED FILES: HelloController.java, UserService.java"
    "⚠️ DO NOT create GreetingService.java"
```

---

### Component 2: FileScopeGuardrail

```python
from middleware import FileScopeGuardrail

mw = FileScopeGuardrail(
    allowed_files=["HelloController.java", "UserService.java"]
)

# Hook: after_model
# Effect: Validates output doesn't mention unauthorized files
```

**What it does:**
```
After Model Response:
  if model_output mentions unauthorized files:
    return {"jump_to": "end"}  # BLOCK execution
  else:
    return None  # Continue
```

---

### Component 3: ToolCallValidationMiddleware

```python
from middleware import ToolCallValidationMiddleware

mw = ToolCallValidationMiddleware(
    allowed_files=["HelloController.java", "UserService.java"],
    codebase_root="/path/to/codebase"
)

# Hook: wrap_tool_call
# Effect: Validates tool paths before execution
```

**What it does:**
```
Before Tool Execution:
  if tool is write_file or edit_file:
    if file_path NOT in allowed_files:
      return ToolMessage("❌ BLOCKED")  # Stop tool
    else:
      return handler(request)  # Execute tool
```

---

## 🧩 Integration Template

### Step 1: Import

```python
from middleware import create_phase4_middleware
```

### Step 2: Create Agent with Middleware

```python
def create_code_synthesis_agent_v2(codebase_path, feature_request, affected_files):
    middleware = create_phase4_middleware(
        feature_request=feature_request,
        affected_files=affected_files,
        codebase_root=codebase_path
    )
    
    agent = create_deep_agent(
        system_prompt=PROMPT,
        model=model,
        backend=FilesystemBackend(root_dir=codebase_path),
        middleware=middleware  # ← KEY
    )
    return agent
```

### Step 3: Use in Phase 4

```python
def run_code_synthesis_phase_v2(codebase_path, context, spec, impact):
    files = impact.get("files_to_modify", [])
    
    agent = create_code_synthesis_agent_v2(
        codebase_path=codebase_path,
        feature_request=spec.intent_summary,
        affected_files=files
    )
    
    result = agent.invoke({"input": prompt})
    return patches
```

---

## ✅ Validation Checklist

Before running tests:

- [ ] `middleware.py` created with 3 classes
- [ ] No lint errors: `pylint scripts/middleware.py`
- [ ] Imports added to v2 script
- [ ] `create_code_synthesis_agent_v2()` created
- [ ] `run_code_synthesis_phase_v2()` created
- [ ] `main()` updated to call v2 functions
- [ ] Old functions removed
- [ ] All documentation files reviewed

---

## 🧪 Quick Test

```bash
# Run test
python scripts/feature_by_request_agent_v2.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add endpoint /api/users/by-role"

# Verify
ls dataset/codes/springboot-demo/src/main/java/com/example/GreetingService.java
# Expected: NOT FOUND ✓

grep "by-role" dataset/codes/springboot-demo/src/main/java/com/example/HelloController.java
# Expected: FOUND ✓
```

---

## 🔍 Debug Commands

```bash
# Check middleware is loaded
grep -n "middleware=" scripts/feature_by_request_agent_v2.py
# Should show: middleware=[...] in create_deep_agent call

# Check middleware module
python -c "from scripts.middleware import IntentReminderMiddleware; print('✓ Middleware imports OK')"

# Run with verbose logging
LANGCHAIN_DEBUG=1 python scripts/feature_by_request_agent_v2.py --codebase-path ...
```

---

## 📊 Success Indicators

### Phase 4 Output

✅ Should see:
```
🔧 Middleware Configuration:
  Feature: Add endpoint /api/users/by-role
  Allowed files: 2 file(s)
    • HelloController.java
    • UserService.java
```

✅ Should modify:
```
✓ Generated 2 code change(s)
  - edit_file: HelloController.java
  - edit_file: UserService.java
```

❌ Should NOT see:
```
- write_file: GreetingService.java
- create new file
- BLOCKED (unless test is intentional)
```

---

## 🎯 Expected Flow

```
User Request
↓
Phase 1-3: Analysis (unchanged)
↓
Phase 4: Code Synthesis
├─ [before_model] Inject intent reminder ✓
├─ Model Call 1: Read files (with reminder)
├─ [wrap_tool_call] Validate read_file path ✓
├─ Tool: read_file("HelloController.java") ✓
├─ [before_model] Inject intent reminder again ✓
├─ Model Call 2: Generate code (with reminder)
├─ [after_model] Validate output for scope ✓
├─ [wrap_tool_call] Validate edit_file path ✓
├─ Tool: edit_file("HelloController.java", code) ✓
└─ Result: Code implemented in correct file ✓
↓
Phase 5: Execution (unchanged)
```

---

## 🚀 One-Command Integration

After understanding the architecture, copy this to integrate:

```bash
# Add imports
sed -i '1i from middleware import create_phase4_middleware' scripts/feature_by_request_agent_v2.py

# Update main() call in Phase 4 (manual step - see INTEGRATION_GUIDE.md)
# Update function definitions (manual step - see INTEGRATION_GUIDE.md)
```

---

## 📚 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| `EXECUTIVE_SUMMARY.md` | Quick overview + problem/solution | 5 min |
| `SOLUTION_ARCHITECTURE.md` | Deep dive into root causes + design | 10 min |
| `MIDDLEWARE_IMPLEMENTATION_PLAN.md` | Technical component details | 8 min |
| `INTEGRATION_GUIDE.md` | Step-by-step integration + testing | 15 min |
| `QUICK_REFERENCE.md` | This file - quick lookup | 5 min |

**Total Learning Time**: ~40 minutes  
**Integration Time**: ~10 minutes  
**Testing Time**: ~5 minutes

---

## 🎓 Key Concepts

### Hook System

| Hook | When | Example |
|------|------|---------|
| `before_agent` | Before agent starts | Setup memory |
| **`before_model`** | BEFORE each LLM call | **Inject reminder** ← We use |
| `wrap_model_call` | AROUND LLM call | Modify request/response |
| `wrap_tool_call` | AROUND tool call | Validate paths ← We use |
| **`after_model`** | AFTER LLM response | **Validate output** ← We use |
| `after_agent` | After agent done | Cleanup |

### Our 3 Layers

```
Layer 1 (before_model): Intention Enforcement
  └─ "Don't forget: add /api/users/by-role"

Layer 2 (after_model): Output Validation  
  └─ "You mentioned unauthorized files - BLOCKED"

Layer 3 (wrap_tool_call): Execution Guard
  └─ "File not in allowed list - BLOCKED"
```

---

## 💾 State Flow

```python
# Before Phase 4
state = {
    "messages": [...],
    "codebase_path": "...",
    "feature_request": "Add endpoint /api/users/by-role",
    "affected_files": ["HelloController.java", "UserService.java"]
}

# During Phase 4 - middleware modifies state
state["messages"] = [
    SystemMessage("🎯 PRIMARY OBJECTIVE: Add endpoint /api/users/by-role\n🎯 ALLOWED FILES: ..."),
    *original_messages
]

# Tool calls validated
# wrap_tool_call checks: "HelloController.java in allowed_files?" → YES ✓

# Output validated
# after_model checks: "mentions only allowed files?" → YES ✓
```

---

**Ready to integrate? Start with INTEGRATION_GUIDE.md**
