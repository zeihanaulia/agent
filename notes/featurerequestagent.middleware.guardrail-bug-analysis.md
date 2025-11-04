# Analisis Bug Guardrail Middleware - "Blocking Tool Call" Error

## 🎯 Ringkasan Masalah
Ketika `enable_guardrail=True`, feature implementation selalu gagal dengan error:
```
🛑 HARD MODE: Blocking tool call
```

Namun ketika `enable_guardrail=False`, semuanya bekerja normal dan code updates berhasil.

---

## 🔍 Root Cause Analysis

### 1. **Masalah Utama: `wrap_tool_call` tidak menjalankan `handler(request)` dengan benar**

Di `ToolCallValidationMiddleware.wrap_tool_call()` (line 290-375):

```python
def wrap_tool_call(self, request: Any, handler: Callable) -> ToolMessage:
    """Intercept and validate tool calls."""
    try:
        # ... validation logic ...
        
        if not self._is_allowed(abs_path):
            # Hard mode: block execution
            print("🛑 HARD MODE: Blocking tool call")
            return ToolMessage(
                content=error_msg,
                tool_call_id=tool_call.get("id", "unknown")
            )
        
        # Path is allowed, execute normally
        return handler(request)  # ✅ FLOW OK
```

**MASALAHNYA:** Meskipun path seharusnya "allowed", logic `_is_allowed()` masih return `False` karena:

### 2. **Bug di Logic Perbandingan Path (Line 314-335)**

```python
def _is_allowed(self, abs_path: str) -> bool:
    abs_path = os.path.abspath(abs_path)
    
    # Direct match
    if abs_path in self.allowed_abs_paths:
        return True
    
    # Check if path is within an allowed directory
    for allowed in self.allowed_abs_paths:
        if os.path.isdir(allowed) and abs_path.startswith(allowed + os.sep):
            return True
    
    # Check if sibling in an allowed directory
    parent_dir = os.path.dirname(abs_path)
    for allowed in self.allowed_abs_paths:
        allowed_dir = os.path.dirname(allowed)
        if parent_dir == allowed_dir:
            return True
    
    return False  # ❌ MASALAH: Masih return False
```

**Masalah Spesifik:**
1. `self.allowed_abs_paths` di-compute dari `affected_files` di `__init__` (line 310)
2. `_normalize_paths()` di `__init__` hanya include files yang **sudah ada** (`os.path.exists()`)
3. Ketika agent ingin **membuat file baru** (write_file), file belum ada → path tidak termasuk dalam `allowed_abs_paths`
4. Hasilnya: semua write_file SELALU diblock karena pathnya tidak ada di set!

### 3. **Konteks Dari Phase 3 & 4**

Dari `feature_by_request_agent_v2.py` line 431-436:

```python
middleware = create_phase4_middleware(
    feature_request=spec.intent_summary,
    affected_files=files_to_modify,  # ← Ini dari Phase 3
    codebase_root=codebase_path,
    enable_guardrail=False  # ← Currently disabled untuk workaround
)
```

**Phase 3** (`run_impact_analysis_phase`) hanya detect **existing files**:
```python
# Find Java files (for Spring Boot projects)
java_files = []
for root, dirs, files in os.walk(os.path.join(codebase_path, "src/main/java")):
    for file in files:  # ← Only existing files!
        if file.endswith(".java"):
```

Jadi `affected_files` hanya berisi file yang sudah ada, **TIDAK termasuk file baru** yang akan dibuat!

### 4. **Kombinasi Bug yang Fatal**

```
Feature Request: "Add new feature"
    ↓
Phase 3: Detect affected_files = ["UserController.java", "UserService.java"]
    ↓
Phase 4 Middleware: 
    - normalized_files = ["/path/UserController.java", "/path/UserService.java"]
    ↓
Agent decides: "Hmm, I need to create UserDTO.java to support this"
    ↓
Agent calls: write_file(path="src/main/java/dto/UserDTO.java", content="...")
    ↓
ToolCallValidationMiddleware.wrap_tool_call():
    - abs_path = "/codebase/src/main/java/dto/UserDTO.java"
    - _is_allowed() checks:
        1. Is path in allowed_abs_paths? NO (UserDTO.java tidak di list)
        2. Is path within allowed directory? 
           - Check: "/codebase/src/main/java/dto/UserDTO.java".startswith("/codebase/src/main/java/UserController.java" + os.sep)? NO
           - Allowed paths adalah FILES, bukan DIRECTORIES!
    ↓
Result: return False → BLOCK with "🛑 HARD MODE"
```

---

## 🐛 Masalah Spesifik di Code

### Problem 1: `_normalize_paths()` filter berdasarkan `os.path.exists()`

**File:** `middleware.py` line 473-486

```python
def _normalize_file_paths(...):
    for f in affected_files:
        if not f or f == "TBD - to be determined by impact analysis":
            continue
        
        abs_path = os.path.abspath(os.path.join(codebase_root, f))
        
        if os.path.exists(abs_path):  # ❌ FILTER: Skip non-existent files!
            normalized.add(abs_path)
```

**Impact:** File yang belum dibuat tidak bisa ditambah ke `normalized`, jadi guardrail tidak tahu file itu "allowed".

### Problem 2: `_is_allowed()` hanya check files, tidak check directories

**File:** `middleware.py` line 318-335

```python
def _is_allowed(self, abs_path: str) -> bool:
    # ... checks ...
    
    # Check if path is within an allowed directory
    for allowed in self.allowed_abs_paths:
        if os.path.isdir(allowed) and abs_path.startswith(allowed + os.sep):
            return True  # ✅ ini bagus TAPI...
```

**Impact:** Ini hanya work jika `allowed` adalah directory. Tapi di line 506:

```python
if not affected_files or all(f == "TBD..."):
    affected_files = [os.path.join(codebase_root, "src")]  # Fallback ke directory
```

Fallback ke directory ada, TAPI pada praktiknya, `affected_files` dari Phase 3 berisi **file paths**, bukan directories!

### Problem 3: Phase 3 tidak return directories, hanya files

**File:** `feature_by_request_agent_v2.py` line 409-419

```python
def run_impact_analysis_phase(...) -> Dict[str, Any]:
    # Find Java files (for Spring Boot projects)
    java_files = []
    for root, dirs, files in os.walk(os.path.join(codebase_path, "src/main/java")):
        for file in files:
            if file.endswith(".java"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, codebase_path)
                java_files.append(rel_path)  # ← individual files, not directories
```

---

## 📋 Rekomendasi Perbaikan

### **Solution A: Smart Directory Detection (Recommended)**

Ubah `_normalize_file_paths()` untuk extract directory patterns:

```python
def _normalize_file_paths(affected_files, codebase_root, expand_scope=True):
    normalized = set()
    directories = set()  # Track directories that contain allowed files
    
    for f in affected_files:
        if not f or f == "TBD - to be determined by impact analysis":
            continue
        
        abs_path = os.path.abspath(os.path.join(codebase_root, f))
        
        # Add the file itself (if exists)
        if os.path.exists(abs_path):
            normalized.add(abs_path)
            
        # IMPORTANT: Also extract and add the directory
        parent_dir = os.path.dirname(abs_path)
        if os.path.isdir(parent_dir):
            directories.add(parent_dir)  # ← Allow new files in same directory!
    
    # Convert directories to special markers or add them separately
    # Return both files AND directories
    return sorted(normalized), sorted(directories)
```

Update `ToolCallValidationMiddleware` untuk check both:

```python
def __init__(self, allowed_files, allowed_dirs, codebase_root, ...):
    self.allowed_files = set(allowed_files)
    self.allowed_dirs = set(allowed_dirs)  # ← NEW
    # ...

def _is_allowed(self, abs_path):
    # Check files
    if abs_path in self.allowed_abs_paths:
        return True
    
    # Check if in allowed directories
    for allowed_dir in self.allowed_abs_dirs:  # ← NEW
        if abs_path.startswith(allowed_dir + os.sep):
            return True
    
    return False
```

### **Solution B: Use expand_scope more intelligently**

Existing `expand_scope` logic (line 516-525) berusaha untuk ini TAPI hanya untuk specific directory names. Buat lebih general:

```python
if expand_scope:
    parent_dir = os.path.dirname(abs_path)
    # ALWAYS add parent directory, regardless of name
    if os.path.isdir(parent_dir):
        # Instead of adding individual files, mark this directory as "allowed"
        directories.add(parent_dir)
```

### **Solution C: Fix Phase 3 to return both files AND directories**

Modify `run_impact_analysis_phase()` untuk return:
```python
return {
    "files_to_modify": java_files,
    "directories_to_modify": [
        os.path.dirname(f) for f in java_files
    ],
    # ...
}
```

---

## 🔧 Why `enable_guardrail=False` Works

Ketika guardrail disabled:
1. `FileScopeGuardrail` dan `ToolCallValidationMiddleware` tidak ditambahkan ke middleware list (line 536-540)
2. Hanya `IntentReminderMiddleware` dan `TraceLoggingMiddleware` yang run
3. `IntentReminderMiddleware` hanya inject system message, tidak block tool calls
4. Tool calls dijalankan normal tanpa validation
5. Result: ✅ code updates berhasil

---

## 📊 Comparison: What Documentation Says vs Implementation

| Aspek | LangChain Docs | Implementasi Anda |
|-------|----------------|------------------|
| `wrap_tool_call` hook | Intercept dan modify tool execution | ✅ Correct implementation |
| Error handling | Return ToolMessage with error | ✅ Correct return type |
| Path validation | Should allow related files | ❌ Only validates exact files |
| Directory scope | Should support directory patterns | ⚠️ Partially implemented |
| New files creation | Should allow based on scope | ❌ Blocks because file doesn't exist yet |

**The middleware is correctly structured, tapi logic path validation-nya yang buggy!**

---

## ✅ Quick Fix Priority

1. **HIGH (Urgent):** Fix `_normalize_file_paths()` untuk juga extract dan validate directories, bukan hanya files
2. **MEDIUM:** Update Phase 3 untuk return directory scopes
3. **LOW:** Add configuration option untuk enable/disable new file creation

---

## 📝 Testing Strategy

Setelah fix, test dengan:

```bash
# Test 1: Create new file (should succeed)
python feature_by_request_agent_v2.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add new UserDTO.java in src/main/java/dto/" \
  --dry-run

# Test 2: Create file in unauthorized directory (should fail)
python feature_by_request_agent_v2.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Create /tmp/malicious.java" \
  --dry-run

# Test 3: Modify existing file (should succeed)
python feature_by_request_agent_v2.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add method to existing HelloController.java" \
  --dry-run
```

