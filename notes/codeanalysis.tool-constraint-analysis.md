# Deep Analysis: Why Agent Still Not Creating Files

## Observation from Output

```
✓ Tool call: ls
✓ Tool call: read_file  (x2)
✓ Tool call: edit_file  (HelloController.java)
✓ Tool call: write_todos
❌ NO write_file calls for new files!
```

## Why This Is Happening

### Problem 1: Agent's Perception
- Agent reads existing files (HelloController.java, Application.java)
- Agent sees: "They want me to enhance Spring Boot app"
- Agent thinks: "Edit existing controller is the way to add greeting service"
- Agent decides: "Adding GreetingService to HelloController solves the problem"

### Problem 2: Prompt Not Forcing write_file
Current unified_prompt says:
```
"✅ CREATE NEW FILES using write_file() ONLY"
"✅ DO NOT use edit_file in this phase"
```

But agent has:
- HelloController.java right there (readable, easy to edit)
- No explicit file path to create
- No hard constraint that prevents edit_file

### Problem 3: Tool Availability
Agent sees available tools:
- `ls` - to list files ✓ (used)
- `read_file` - to read code ✓ (used)
- `edit_file` - to modify existing ✓ (used instead of write_file!)
- `write_file` - to create new (NOT USED)
- `write_todos` - to plan (used)

**Why?** Agent followed easier path: enhance existing > create new

### Problem 4: Missing Absolute File Paths
The prompt says "Create files" but doesn't provide:
- Exact absolute paths ready to copy-paste
- Example write_file call with real paths
- Explicit order with full paths

## Real Root Cause

**Agent Capability vs. Instruction Following**
- Agent CAN do write_file
- Agent CAN create new files
- But there's no HARD CONSTRAINT preventing edit_file
- And edit_file to existing HelloController is "safer" choice

## Solution: Multi-Layer Constraints

### Constraint 1: Tool Filtering (Strongest)
```python
# Only allow these tools in generation phase
allowed_tools = {
    "write_file": {...},  # Only for creating NEW files
    "read_file": {...}     # Only for understanding existing
}
# Disable: edit_file, ls, write_todos
```

### Constraint 2: Explicit File Requirements
```python
# Don't say "create files", say "create THESE exact files":

EXACT FILES TO CREATE:

1. /Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo/src/main/java/com/example/springboot/model/Delivery.java
   - Package: com.example.springboot.model
   - Class name: Delivery (JPA Entity)
   - Required fields: id, trackingNumber, pickupAddress, deliveryAddress, status

2. /Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo/src/main/java/com/example/springboot/repository/DeliveryRepository.java
   - Package: com.example.springboot.repository
   - Interface extending JpaRepository<Delivery, Long>
   - Required methods: findByStatus, findByTrackingNumber

[... more files ...]

Create ONLY these files using write_file(). Do NOT modify HelloController.java.
```

### Constraint 3: Tool Call Validation
```python
# Before executing tool call:
if tool_call.name == "edit_file":
    # Check if target file is HelloController
    if "HelloController" in tool_call.args["path"]:
        REJECT: "Generation phase: do NOT edit HelloController"

if tool_call.name == "write_file":
    # Check if path is in allowed directories
    allowed_dirs = [".../model/", ".../repository/", ".../dto/", ...]
    if any(allowed_dir in path for allowed_dir in allowed_dirs):
        ALLOW
    else:
        REJECT: "Path must be in allowed layer directory"
```

## Why Current Approach Failed

### Current Fix (Not Enough)
✓ Combined 2 prompts into 1 (good, maintains agent state)
✓ Added constraint text "DO NOT use edit_file" (weak)
✓ Fixed extraction to get tool calls from messages (good)
❌ No tool filtering (agent can still use edit_file)
❌ No hard constraints (agent chooses easier path)
❌ No path validation (accepts any path)

### What's Needed for Real Fix

**Hard Constraints (Not Suggestions)**:
1. Tool whitelist: ONLY write_file + read_file allowed
2. Path validation: Must be in specific layer directories
3. Mandatory fields: path and content must not be empty
4. Pre-execution checks: Reject non-compliant calls before executing

## Implementation Plan

### Step 1: Add Tool Filtering to Agent
```python
# In create_code_synthesis_agent() or invoke_with_timeout()
def filter_tool_calls(tool_call, phase="generation"):
    if phase == "generation":
        # REJECT edit_file completely
        if tool_call["name"] == "edit_file":
            raise ValueError("edit_file not allowed in generation phase")
        
        # REQUIRE valid path for write_file
        if tool_call["name"] == "write_file":
            if not tool_call["args"].get("path") or not tool_call["args"].get("content"):
                raise ValueError("write_file requires both path and content")
```

### Step 2: Middleware or Agent Wrapper
```python
# Before invoke_with_timeout() returns results
def validate_and_filter_results(result):
    if "messages" in result:
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls"):
                for call in msg.tool_calls:
                    filter_tool_calls(call, phase="generation")
    return result
```

### Step 3: Enhanced Prompt with Explicit Paths
Replace generic "create files" with exact paths and examples.

## Expected Result After Fix

```
✓ Tool call: read_file (HelloController - understand patterns)
✓ Tool call: write_file (Delivery.java - new entity)
✓ Tool call: write_file (DeliveryRepository.java - new interface)
✓ Tool call: write_file (JpaDeliveryRepository.java - new impl)
✓ Tool call: write_file (DeliveryDTO.java - new dto)
... (more write_file calls)
❌ NO edit_file (rejected by constraints)
❌ NO ls (not needed)
❌ NO write_todos (not needed in generation)

Result: 10 new files created ✓
```

## Testing Strategy

1. **Before Fix:** Only edit_file works (current state) ❌
2. **Add Tool Filtering:** write_file works, edit_file rejected ✓
3. **Add Path Validation:** Only allowed paths accepted ✓
4. **Add Field Validation:** Empty fields rejected ✓
5. **Enhanced Prompt:** Explicit paths provided ✓
6. **Test:** Full execution creates all 10 files ✓
