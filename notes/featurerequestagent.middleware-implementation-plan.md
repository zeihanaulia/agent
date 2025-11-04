# Middleware & Guardrails Implementation Plan untuk Feature-by-Request Agent

## Executive Summary

Agent v2 saat ini mengalami dua masalah utama:
1. **Intent Loss**: Agent lupa tentang feature request user saat memanggil model di Phase 4, jadi membuat file random (GreetingService.java)
2. **No File Scope Control**: Agent bisa edit file apapun, tidak terbatas pada affected_files yang diidentifikasi

Solusi: Tambahkan **3 middleware** ke Phase 4 agent dengan LangChain's AgentMiddleware API.

---

## 📋 Component Analysis dari LangChain Middleware

### Available Hooks (dari dokumentasi)

| Hook | When | Use Case |
|------|------|----------|
| `before_agent` | Before agent starts | Load memory, validate input |
| `before_model` | Before each LLM call | **Update prompts, inject context** ✅ |
| `wrap_model_call` | Around each LLM call | Intercept requests/responses |
| `wrap_tool_call` | Around each tool call | Custom tool execution |
| `after_model` | After each LLM response | **Validate output, apply guardrails** ✅ |
| `after_agent` | After agent completes | Save results, cleanup |

### Kompatibilitas dengan DeepAgent

DeepAgent menggunakan LangChain di bawah API-nya, jadi:
- ✅ `AgentMiddleware` class bisa digunakan di `create_deep_agent()`
- ✅ `before_model` hook injection bisa modify messages sebelum model call
- ✅ `after_model` hook bisa validate tool calls

### Key Pattern dari Docs

```python
from langchain.agents.middleware import AgentMiddleware, AgentState
from langgraph.runtime import Runtime
from typing import Any

class MyMiddleware(AgentMiddleware):
    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Inspect/modify state["messages"] before model call
        # Return None if no changes, or dict with modified state
        return None
    
    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Inspect/modify state["messages"] after model response
        # Can return {"jump_to": "end"} to stop execution
        return None
```

---

## 🔧 3 Middleware Components untuk Phase 4

### 1️⃣ IntentReminderMiddleware (before_model)

**Purpose**: Inject user feature_request ke setiap model call agar agent gak lupa intent

**Implementation Pattern**:
```python
class IntentReminderMiddleware(AgentMiddleware):
    def __init__(self, feature_request: str, affected_files: List[str]):
        super().__init__()
        self.feature_request = feature_request
        self.affected_files = affected_files
    
    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Prepend system message dengan intent reminder
        reminder = {
            "role": "system",
            "content": f"""🎯 PRIMARY OBJECTIVE (Do NOT forget):
Implement this EXACT feature: "{self.feature_request}"

📁 Only modify these files:
{chr(10).join(f"  - {f}" for f in self.affected_files)}

⚠️ CONSTRAINTS:
- Do NOT create unrelated files (e.g., GreetingService.java)
- Do NOT refactor existing code outside of feature scope
- Do NOT add new dependencies
- Only touch the specified files above
"""
        }
        # Insert reminder ke messages
        messages = state.get("messages", [])
        # Cek apakah reminder sudah ada (avoid duplicates)
        has_reminder = any("PRIMARY OBJECTIVE" in str(m.get("content", "")) for m in messages)
        if not has_reminder:
            messages.insert(0, reminder)
        return {"messages": messages}
```

**Effect**: Sebelum setiap model call, agent dikasih reminder yang jelas tentang intent + file constraints.

---

### 2️⃣ FileScopeGuardrail (after_model)

**Purpose**: Validate bahwa model hanya plan edits ke allowed files

**Implementation Pattern**:
```python
class FileScopeGuardrail(AgentMiddleware):
    def __init__(self, allowed_files: List[str]):
        super().__init__()
        self.allowed_files = set(allowed_files)
    
    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Inspect last message untuk file paths
        messages = state.get("messages", [])
        if not messages:
            return None
        
        last_msg = messages[-1]
        content = str(last_msg.get("content", ""))
        
        # Extract file paths mentioned
        import re
        file_patterns = r'(?:src/|\.?/)?[\w\-./]*\.(?:java|py|ts|tsx|js|go|rb)'
        mentioned_files = set(re.findall(file_patterns, content))
        
        # Check for violations
        violations = mentioned_files - self.allowed_files
        if violations:
            # Block with intervention
            return {
                "messages": [{
                    "role": "assistant",
                    "content": f"❌ BLOCKED: You attempted to modify files outside scope: {violations}\n"
                               f"Allowed files only: {self.allowed_files}\n"
                               f"Please focus on the allowed files."
                }],
                "jump_to": "end"  # Stop execution
            }
        
        return None
```

**Effect**: Kalau agent mencoba edit file di luar allowed list, execution dihentikan dengan pesan jelas.

---

### 3️⃣ ToolCallValidationMiddleware (wrap_tool_call)

**Purpose**: Intercept tool calls (write_file, edit_file) dan validate path sebelum execution

**Implementation Pattern**:
```python
class ToolCallValidationMiddleware(AgentMiddleware):
    def __init__(self, allowed_files: List[str], codebase_root: str):
        super().__init__()
        self.allowed_files = set(allowed_files)
        self.codebase_root = codebase_root
    
    def wrap_tool_call(self, request, handler):
        tool_call = request.tool_call
        tool_name = tool_call.get("function", {}).get("name", "")
        
        # Only validate file-modifying tools
        if tool_name in ["write_file", "edit_file"]:
            args = tool_call.get("function", {}).get("arguments", {})
            file_path = args.get("path", "")
            
            # Normalize path
            import os
            abs_path = os.path.abspath(os.path.join(self.codebase_root, file_path))
            
            # Check if within allowed set
            allowed_abs = {os.path.abspath(os.path.join(self.codebase_root, f)) 
                          for f in self.allowed_files}
            
            if abs_path not in allowed_abs:
                # Return error message instead of executing
                return ToolMessage(
                    content=f"❌ File '{file_path}' is not in the allowed list. "
                           f"Allowed files: {self.allowed_files}",
                    tool_call_id=tool_call.get("id")
                )
        
        # Otherwise, execute normally
        return handler(request)
```

**Effect**: Sebelum tool call dijalankan, validate dulu bahwa path-nya allowed.

---

## 📝 Integration dengan v2 Phase 4

### Current Code (v2)
```python
def create_code_synthesis_agent(codebase_path: str):
    """Phase 4: Code Synthesis"""
    backend = FilesystemBackend(root_dir=codebase_path)
    prompt = "..."
    return create_deep_agent(system_prompt=prompt, model=analysis_model, backend=backend)
```

### Updated Code (dengan middleware)
```python
def create_code_synthesis_agent_v2(codebase_path: str, feature_request: str, affected_files: List[str]):
    """Phase 4: Code Synthesis dengan Intent Reminder + Guardrails"""
    backend = FilesystemBackend(root_dir=codebase_path)
    prompt = "..."
    
    # Create middleware instances
    middleware = [
        IntentReminderMiddleware(feature_request, affected_files),
        FileScopeGuardrail(affected_files),
        ToolCallValidationMiddleware(affected_files, codebase_path),
    ]
    
    # Pass middleware ke agent
    agent = create_deep_agent(
        system_prompt=prompt,
        model=analysis_model,
        backend=backend,
        middleware=middleware  # ← NEW
    )
    
    return agent
```

### Updated Phase 4 Invocation
```python
def run_code_synthesis_phase_v2(codebase_path: str, context: str, spec: FeatureSpec, 
                                impact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Phase 4 dengan middleware"""
    print("⚙️ Phase 4: Code Synthesis dengan Intent Reminder...")
    
    files_to_modify = impact.get("files_to_modify", spec.affected_files)
    
    # Use v2 agent dengan middleware
    agent = create_code_synthesis_agent_v2(
        codebase_path=codebase_path,
        feature_request=spec.intent_summary,  # ← Pass user intent
        affected_files=files_to_modify  # ← Pass allowed files
    )
    
    # Rest of implementation...
    result = agent.invoke({"input": analysis_prompt})
    
    return patches
```

---

## ✅ Expected Improvements

| Problem | Before | After |
|---------|--------|-------|
| Agent creates GreetingService.java | No reminder of intent | IntentReminderMiddleware setiap invoke |
| Agent modifies unrelated files | No validation | FileScopeGuardrail intercept + block |
| Hard to debug Phase 4 issues | Generic prompts | Clear intent + file constraints injected |
| Model calls too long/expensive | No optimization | (Optional: add cost limiting middleware) |

---

## 🚀 Implementation Steps

1. ✅ Create `middleware.py` dengan 3 class middleware
2. ✅ Update `feature_by_request_agent_v2.py`:
   - Import middleware classes
   - Create `create_code_synthesis_agent_v2()` dengan middleware parameter
   - Update `run_code_synthesis_phase_v2()` untuk pass feature_request + affected_files
3. ✅ Test on springboot-demo:
   - Should NOT create GreetingService.java
   - Should ONLY modify HelloController.java
4. ✅ Verify LangSmith traces menunjukkan injected prompts

---

## 📚 LangChain API References

- [Middleware Documentation](https://docs.langchain.com/oss/python/langchain/middleware)
- [Custom Middleware Pattern](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [Before/After Model Hooks](https://docs.langchain.com/oss/python/migrate/langchain-v1)
- [Guardrails Guide](https://docs.langchain.com/oss/python/langchain/guardrails)

---

## 🎯 Success Criteria

✅ Phase 4 agent menjalankan HANYA dengan files di allowed_files list
✅ Sebelum setiap model call, feature_request di-inject sebagai reminder
✅ Jika model coba edit file luar scope → execution dihentikan dengan pesan jelas
✅ Tidak ada GreetingService.java atau file random lain dibuat
✅ HelloController.java atau endpoint file yang sesuai berhasil dimodifikasi dengan code yang benar
