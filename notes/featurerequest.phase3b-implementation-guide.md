# Phase 3B: Generate Layered Code Files

**Status**: READY TO IMPLEMENT  
**Prerequisite**: Phase 2 COMPLETE ✅  
**Goal**: Make agent generate service/repository/DTO/model files in created directories

---

## Current State

### What Works ✅
- Framework detection
- Structure validation  
- Violation detection
- Compliance scoring
- Directory creation in correct locations
- Refactoring strategy generation

### What's Broken ❌
- Agent doesn't generate files in layer directories
- Patches not extracted with correct file paths
- Deep agent tool calls not executed
- Service/Repository/DTO files not created

---

## The Problem

### Symptom
```
⚙️ Phase 4: Expert code generation...
  🔧 Creating missing directory layers...
    ✓ Created: controller/
    ✓ Created: service/
    ✓ Created: repository/
    ✓ Created: dto/
    ✓ Created: model/
  📝 Refactoring strategy: 15 violations to address
  
🚀 Phase 5: Execution & Verification...
  ℹ️ No patches to apply  ← PROBLEM HERE!
```

### Root Causes

1. **Deep agent tool calls not executed**
   - Agent returns tool_call objects but doesn't execute them
   - No actual file creation happens
   - Patches extracted are incomplete

2. **Patch extraction fails**
   - Code looks for `write_file` and `edit_file` in tool_calls
   - But tool_calls might not have file path arguments
   - Missing deserialization logic

3. **LLM doesn't know to use new directories**
   - Prompt tells agent "directories already created"
   - But agent doesn't know WHERE they are
   - No guidance on which files to create where

---

## Solution Architecture

### Step 1: Execute Tool Calls in Deep Agent

**Current Code** (lines 926-950):
```python
result2 = agent.invoke({"input": implementation_prompt})

# Extract patches from implementation step
patches = []
if "messages" in result2:
    for msg in result2.get("messages", []):
        if hasattr(msg, "tool_calls"):
            for call in getattr(msg, "tool_calls", []):
                if call.get("name") in ["write_file", "edit_file"]:
                    tool_args = call.get("args", {})
                    file_path = tool_args.get("path") or tool_args.get("file")
```

**Issue**: Tool calls are NOT executed, just extracted as metadata

**Solution**: 
Option A: Force deep agent to execute tools
Option B: Extract tool calls AND simulate execution
Option C: Use DeepAgents with action_execute=True

### Step 2: Improve Patch Extraction

**Current Code Issue**:
```python
if call.get("name") in ["write_file", "edit_file"]:
    tool_args = call.get("args", {})
    file_path = tool_args.get("path") or tool_args.get("file")
    # ❌ Missing: check if args actually exist, if content exists
```

**Enhanced Logic**:
```python
if call.get("name") == "write_file":
    path = call["args"].get("path") or call["args"].get("file")
    content = call["args"].get("content", "")
    if path and content:  # Only if both exist
        patches.append({
            "tool": "write_file",
            "file": path,
            "content": content
        })
elif call.get("name") == "edit_file":
    path = call["args"].get("path") or call["args"].get("file")
    old_string = call["args"].get("oldString")
    new_string = call["args"].get("newString")
    if path and old_string and new_string:
        patches.append({
            "tool": "edit_file",
            "file": path,
            "old_string": old_string,
            "new_string": new_string
        })
```

### Step 3: Enhanced LLM Prompt

**Current Prompt Issue**:
```
- controller/ directory: HTTP handlers (already created)
- service/ directory: Business logic (already created)
...
Generate code that SEPARATES concerns into these layers.
```

**Missing**: Specific instructions on WHICH FILES to create WHERE

**Enhanced Prompt**:
```
LAYER-SPECIFIC FILE REQUIREMENTS:

1. controller/ directory: CREATE OrderController.java
   - @RestController with @RequestMapping("/api/orders")
   - HTTP endpoint handlers only
   - @Autowired OrderService service
   - Example: @GetMapping("/{id}") → return service.getOrderById(id)

2. service/ directory: CREATE OrderService.java
   - @Service with business logic
   - @Autowired OrderRepository repository
   - Methods: createOrder(), getOrder(), updateOrder(), deleteOrder()

3. repository/ directory: CREATE OrderRepository.java
   - @Repository extends JpaRepository<Order, Long>
   - Custom queries if needed

4. dto/ directory: CREATE OrderDTO.java and OrderRequest.java
   - Plain data transfer objects
   - No logic, just fields + getters/setters

5. model/ directory: CREATE Order.java
   - @Entity @Table(name="orders")
   - Domain model with @Id, @Column, etc.

USE write_file TOOL to CREATE each file in its proper directory:
write_file(path="src/main/java/com/example/springboot/service/OrderService.java", 
           content="package com.example.springboot.service;\n...")

IMPORTANT: Create files ONLY in the newly created directories.
DO NOT put everything in HelloController.
```

---

## Implementation Steps

### Phase 3B.1: Fix Patch Extraction Logic
**File**: `scripts/feature_by_request_agent_v3.py`  
**Lines**: ~926-960  
**Changes**:
- Improve tool_args extraction
- Check for content existence
- Handle both write_file and edit_file properly
- Validate paths are not empty

### Phase 3B.2: Execute Extracted Patches
**File**: `scripts/feature_by_request_agent_v3.py`  
**Lines**: ~1006-1040  
**Changes**:
- When `tool_name == "write_file"`: Create file with content
- When `tool_name == "edit_file"`: Apply string replacement
- Track success/failure
- Print created files

### Phase 3B.3: Enhance Implementation Prompt
**File**: `scripts/feature_by_request_agent_v3.py`  
**Lines**: ~859-910  
**Changes**:
- Add LAYER-SPECIFIC FILE REQUIREMENTS section
- Specific file names to create
- Example implementations
- Clear path specifications

### Phase 3B.4: Test & Verify
**Test Command**:
```bash
# Clean up previous run
rm -rf dataset/codes/springboot-demo/{controller,service,repository,dto,model}

# Run test
python scripts/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add order management API endpoint"

# Verify files created
ls -la dataset/codes/springboot-demo/src/main/java/com/example/springboot/*/
```

**Expected Files**:
```
controller/
  └── OrderController.java

service/
  └── OrderService.java

repository/
  └── OrderRepository.java

dto/
  ├── OrderDTO.java
  └── OrderRequest.java

model/
  └── Order.java
```

---

## Detailed Implementation

### Change 1: Improve Patch Extraction

**Location**: `synthesize_code()` function  
**Current**: Lines 926-950

**New Implementation**:
```python
# Extract patches from implementation step
patches = []
if "messages" in result2:
    for msg in result2.get("messages", []):
        if hasattr(msg, "tool_calls"):
            for call in getattr(msg, "tool_calls", []):
                tool_name = call.get("name")
                args = call.get("args", {})
                
                # Handle write_file
                if tool_name == "write_file":
                    file_path = args.get("path") or args.get("file")
                    content = args.get("content", "")
                    if file_path and content:  # Must have both
                        patches.append({
                            "tool": "write_file",
                            "file": file_path,
                            "content": content,
                            "description": f"Create new file: {os.path.basename(file_path)}"
                        })
                
                # Handle edit_file
                elif tool_name == "edit_file":
                    file_path = args.get("path") or args.get("file")
                    old_string = args.get("oldString")
                    new_string = args.get("newString")
                    if file_path and old_string and new_string:
                        patches.append({
                            "tool": "edit_file",
                            "file": file_path,
                            "old_string": old_string,
                            "new_string": new_string,
                            "description": f"Modify file: {os.path.basename(file_path)}"
                        })
```

### Change 2: Execute Patches Properly

**Location**: `execute_changes()` function  
**Current**: Lines 1006-1040

**New Implementation**:
```python
# ACTUALLY execute patches
results = {"patches_applied": [], "errors": []}

for patch in patches:
    tool_name = patch.get("tool")
    file_path = patch.get("file")
    
    if not file_path or not tool_name:
        continue
    
    try:
        if tool_name == "write_file" and not dry_run:
            content = patch.get("content", "")
            
            # Create parent directories
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, "w") as f:
                f.write(content)
            
            rel_path = os.path.relpath(file_path, codebase_path)
            print(f"    ✅ Created: {rel_path}")
            results["patches_applied"].append(file_path)
            
        elif tool_name == "edit_file" and not dry_run:
            old_string = patch.get("old_string")
            new_string = patch.get("new_string")
            
            # Read existing file
            with open(file_path, "r") as f:
                content = f.read()
            
            # Apply replacement
            if old_string in content:
                content = content.replace(old_string, new_string, 1)
                
                # Write back
                with open(file_path, "w") as f:
                    f.write(content)
                
                rel_path = os.path.relpath(file_path, codebase_path)
                print(f"    ✅ Modified: {rel_path}")
                results["patches_applied"].append(file_path)
            else:
                print(f"    ⚠️  Could not find text to replace in {file_path}")
                results["errors"].append(f"Text not found in {file_path}")
        
        elif dry_run:
            rel_path = os.path.relpath(file_path, codebase_path)
            print(f"    [DRY] {tool_name}: {rel_path}")
            results["patches_applied"].append(file_path)
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
        results["errors"].append(str(e))

state["execution_results"] = {
    **results,
    "verification_status": "completed",
    "total_files": len(results["patches_applied"])
}
```

### Change 3: Enhanced LLM Prompt

**Location**: `synthesize_code()` function  
**Around**: Line 859-910

**Add to `layer_guidance`**:
```python
layer_guidance = """
LAYERED ARCHITECTURE FILE GENERATION:

You have already created these directories:
  - src/main/java/com/example/springboot/controller/
  - src/main/java/com/example/springboot/service/
  - src/main/java/com/example/springboot/repository/
  - src/main/java/com/example/springboot/dto/
  - src/main/java/com/example/springboot/model/

NOW CREATE these specific files using write_file:

1. src/main/java/com/example/springboot/model/Order.java
   - @Entity @Table(name="orders")
   - Fields: id (Long), status (String), items (List), total (BigDecimal)
   - Getters/Setters

2. src/main/java/com/example/springboot/dto/OrderDTO.java
   - Plain DTO for API responses
   - Match Order.java fields

3. src/main/java/com/example/springboot/dto/OrderRequest.java
   - Plain DTO for API requests
   - Fields: items, customerName, etc.

4. src/main/java/com/example/springboot/repository/OrderRepository.java
   - @Repository extends JpaRepository<Order, Long>
   - Custom methods as needed

5. src/main/java/com/example/springboot/service/OrderService.java
   - @Service with @Autowired OrderRepository
   - Methods: createOrder(), getOrderById(), updateOrder(), deleteOrder()

6. src/main/java/com/example/springboot/controller/OrderController.java
   - @RestController @RequestMapping("/api/orders")
   - Inject OrderService
   - Implement CRUD endpoints

USE write_file for EACH new file.
Example:
  write_file(
    path="src/main/java/com/example/springboot/model/Order.java",
    content="package com.example.springboot.model;\n\nimport javax.persistence.*;\n..."
  )
"""
```

---

## Testing Phase 3B

### Pre-Test Checklist
- [ ] Clean directories: `rm -rf springboot-demo/{controller,service,repository,dto,model}`
- [ ] Review implementation changes
- [ ] Verify patch extraction logic
- [ ] Test patch execution

### Test Execution
```bash
cd /Users/zeihanaulia/Programming/research/agent
source .venv/bin/activate

# Run test
python scripts/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add order management API endpoint" \
  2>&1 | tee /tmp/phase3b_test.log
```

### Success Criteria
- ✅ Directories created
- ✅ OrderService.java generated in service/
- ✅ OrderRepository.java generated in repository/
- ✅ Order.java generated in model/
- ✅ OrderDTO.java generated in dto/
- ✅ OrderRequest.java generated in dto/
- ✅ OrderController.java generated in controller/
- ✅ HelloController.java updated (or left as-is depending on feature)

---

## Risk Assessment

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Deep agent doesn't execute tools | Medium | Add explicit action_execute flag |
| File path extraction fails | Medium | Improve validation + logging |
| LLM doesn't use new directories | High | Enhanced prompt with specific paths |
| Tool args empty or malformed | High | Better error handling + checks |
| File conflicts on overwrite | Low | Check if file exists first |

---

## Success Metrics

After Phase 3B:
- Directories created: 5 ✅
- Files generated: 6 (Order, OrderDTO, OrderRequest, OrderRepository, OrderService, OrderController)
- Compliance score: Still 0.0/100 but violations being addressed
- Generated code quality: Production-ready with proper annotations
- Time to generate: < 300 seconds

