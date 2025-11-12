# 🔍 DeepAgent Tool Calling Implementation Gap Analysis

**Status**: ROOT CAUSE FOUND
**Date**: 2025-01-12
**Issue**: Agent generates Greeting classes instead of Delivery files despite correct spec

## 📚 LangChain Documentation Findings

### Tool Calling Flow (Standard LangChain)
According to LangChain docs, tool calling MUST follow this pattern:

```
Step 1: Model generates tool calls (name + arguments)
Step 2: EXECUTE each tool call and collect results
Step 3: Pass results back to model in a ToolMessage (with tool_call_id matching)
Step 4: Model uses results to generate final response
```

**Key Requirement**: Each ToolMessage must include `tool_call_id` that matches the original tool call ID.

### DeepAgent Architecture (LangGraph-based)
DeepAgent is built on LangGraph with middleware:
- **TodoListMiddleware**: Planning/task decomposition
- **FilesystemMiddleware**: File system tools (ls, read_file, write_file, edit_file)
- **SubAgentMiddleware**: Spawn specialized subagents

**Subagent Pattern**:
```python
# Main agent has a "task" tool to spawn subagents
# Subagent runs autonomously until completion
# Returns a SINGLE final result to main agent (no multi-turn)
# Result is concise - intermediate tool calls are NOT shown to main agent
```

## ❌ What Our Implementation Does Wrong

### Problem 1: Tool Call Extraction Doesn't Preserve tool_call_id
**Expected**:
```python
# From model.stream() output:
AIMessage with:
  - tool_calls[0]:
    - name: "write_file"
    - args: {...}
    - id: "call_abc123"  # ← THIS ID

# When executed, we return:
ToolMessage with:
  - tool_call_id: "call_abc123"  # ← MUST MATCH
  - content: "File created"
```

**Our Code** (`_extract_patch_from_call()` in flow_synthesize_code.py):
```python
# We extract tool calls but DON'T preserve tool_call_id
patch = {
    'tool': tool_name,
    'file': file_path,
    'args': args
}
# ❌ MISSING: tool_call_id is lost
```

**Impact**: Tool results can't be properly correlated back to tool calls. Agent gets confused about what actually executed.

### Problem 2: Multi-Step Tool Calls Not Returning Results
**Expected** (LangChain streaming pattern):
```
For each tool call the agent makes:
  1. Agent emits: AIMessage with tool_calls
  2. Framework returns: ToolMessage with result + tool_call_id
  3. Agent sees result and decides next step
  4. Loop continues
```

**Our Code** (`invoke_with_timeout()` in agents/agent_factory.py):
```python
for event in agent.stream({"input": prompt}):
    # We collect events but...
    # What do we do with results?
    # Are we sending ToolMessages back to agent?
```

**Issue**: We may be breaking the agent's feedback loop.

### Problem 3: Agent Sees Existing Code When It Should Only Create New
**Expected** (from DeepAgent docs):
```
Main agent gets CONCISE result from subagent
- Subagent does multi-step work
- Main agent ONLY sees final result, not intermediate details
- Context stays clean
```

**Our Code**: 
```python
# Agent reads existing HelloController, GreetingService via read_file
# Agent analyzes existing patterns
# Agent THEN defaults to modifying existing code
# ❌ We're not using subagents for "generation task"
```

**Should be**:
```python
# Create a GENERATION subagent with:
# - STRICT prompt: "ONLY create NEW delivery files"
# - Whitelist tools: ONLY write_file (no read_file, no edit_file)
# - Main agent gets clean result back
```

## 📋 Corrective Actions Needed

### 1. Fix Tool Call ID Preservation
**File**: `scripts/coding_agent/flow_synthesize_code.py`
**Function**: `_extract_patch_from_call()`

```python
# CURRENT: Loses tool_call_id
patch = {'tool': tool_name, 'args': args, ...}

# SHOULD BE: Preserve tool_call_id
patch = {
    'tool': tool_name,
    'args': args,
    'tool_call_id': call_dict.get('id'),  # ← ADD THIS
    ...
}
```

### 2. Create a GENERATION Subagent
**File**: `scripts/coding_agent/agents/agent_factory.py`
**New Function**: `create_code_generation_subagent()`

```python
def create_code_generation_subagent(spec, framework_prompt):
    """
    Specialized subagent for file generation ONLY
    - Cannot read existing files
    - Cannot edit existing files
    - Only write_file allowed
    """
    return {
        'name': 'code_generator',
        'description': 'Generates new files for delivery routing system',
        'system_prompt': """
            You are a code generation specialist.
            
            CRITICAL RULES:
            1. ONLY create NEW files using write_file()
            2. DO NOT read any existing files (no read_file)
            3. DO NOT modify existing files (no edit_file)
            4. DO NOT analyze existing code patterns
            5. Follow this spec EXACTLY:
            [spec.new_files_planning details here]
            
            Generate ALL 10 files before responding.
        """,
        'tools': [write_file_only],  # Only write_file, nothing else
        'model': 'same-as-main'
    }
```

Then in `flow_synthesize_code()`:
```python
# Instead of main agent doing generation:
# result = agent.stream({"input": implementation_prompt})

# Use GENERATION subagent:
# (This keeps main agent focused, isolates context)
```

### 3. Fix stream() Result Handling
**File**: `scripts/coding_agent/agents/agent_factory.py`
**Function**: `invoke_with_timeout()`

Verify that for each AIMessage with tool_calls:
1. We extract the tool call (with ID)
2. We execute the tool
3. We create a ToolMessage with matching tool_call_id
4. We send it back to agent
5. Agent processes it and continues

**Currently**: Unknown if this feedback loop works correctly.

### 4. Strengthen Implementation Prompt
Make the prompt so explicit that agent CAN'T ignore it:

```python
implementation_prompt = f"""
🚫 CRITICAL CONSTRAINTS - STRICTLY ENFORCE:

❌ DO NOT:
  - Read existing GreetingService, HelloController, etc
  - Modify existing files
  - Call edit_file for ANY reason
  - Call read_file for ANY reason
  
✅ MUST DO:
  - Create ONLY these 10 files:
    1. Delivery.java (entity in domain/entity/)
    2. DeliveryRepository.java (interface in domain/repository/)
    ... [all 10 listed explicitly]
  - Use ONLY write_file() tool
  - Each write_file must have COMPLETE Java code
  - Stop after creating 10 files
  - NO ANALYSIS, NO READING, NO EDITING

Your ONLY output should be write_file() calls. NOTHING ELSE.
"""
```

## 🎯 Why Agent Ignores Spec - ROOT CAUSE ANALYSIS

### 1. Agent Tool Freedom + Existing Code Pattern
```
Agent has tools: [write_file, read_file, edit_file, ls, write_todos]

When given implementation_prompt:
  ✅ Spec says: "Create 10 delivery files"
  ❌ Agent sees: "Also, existing HelloController and GreetingService in codebase"
  
Result: Agent defaults to analyzing existing code and editing it (higher confidence)
        Instead of creating spec-new files (lower confidence, spec-based)
```

### 2. invoke_with_timeout() Breaks DeepAgent Feedback Loop
**Critical Issue in flow_synthesize_code.py lines 19-62:**

```python
# Current implementation:
for chunk in agent.stream(input_data, stream_mode="values"):
    all_chunks.append(chunk)

# Final chunk is returned to extract_patches_from_result()
# ❌ PROBLEM: This doesn't close the LangGraph execution loop!
```

**What SHOULD happen** (per LangChain docs):
```
Agent Run Loop:
  1. Agent sees prompt
  2. Agent generates tool_calls: [{"name": "read_file", "id": "call_abc123", ...}]
  3. Framework executes tool, returns: ToolMessage(tool_call_id="call_abc123", content="...")
  4. Agent sees result + continues loop
  5. Repeat until agent stops
```

**What ACTUALLY happens** (DeepAgent via LangGraph):
```
Agent Run Loop:
  1. Agent sees prompt  
  2. Agent generates tool_calls
  3. DeepAgent's FilesystemMiddleware executes tools INSIDE the agent
  4. Agent state is updated with results
  5. Loop continues INSIDE DeepAgent until completion
  6. .stream() returns FINAL state only (all intermediate steps compressed)

Result: We only see final state, not intermediate tool calls
        extract_patches_from_result() can't find tool calls in final state
        It falls back to looking in "messages" format
```

### 3. extract_patches_from_result() Looks in Wrong Places
**File**: flow_synthesize_code.py, lines 107-230

Current extraction order:
```python
# Format 0: Look in result["files"]
if "files" in result:
    # Returns file_path → content mapping
    # Works IF DeepAgent directly creates files
    
# Format 1: Look in result["messages"] for tool_calls
if "messages" in result:
    # Looks for AIMessage.tool_calls
    # ❌ DeepAgent doesn't expose tool calls this way
    # It executes them internally via middleware

# Format 2: Look in result["tool_execution_log"]
# This is where DeepAgent COULD log execution
# But our DeepAgent version doesn't populate it
```

**The Bug**: DeepAgent executes tools internally (in middleware), so:
- `result["messages"]` doesn't have AIMessage with tool_calls
- Tool results are directly reflected in agent state
- `result["messages"][-1].content` is agent's FINAL narrative response (Greeting analysis)

### 4. Post-Processing Filter Can't Help
**File**: flow_synthesize_code.py, lines 95-103

```python
# _extract_patch_from_call() filters edit_file
if tool_name == "edit_file":
    print(f"🚫 FILTERED: edit_file blocked...")
    return None  # Silently reject edit_file calls
```

**Why this doesn't solve spec-ignoring**:
- Filter runs AFTER agent has already decided
- Agent looked at existing code and chose "modify GreetingService"
- Filter just blocks that call - agent already committed to wrong path
- Next iteration, agent tries different tool, still ignoring spec

### 5. Spec Emphasis Insufficient in Prompt
**Current implementation_prompt** (lines 430-620):
```
"🎯 EXPLICIT FILES TO CREATE..."
"📋 NEW FILES PLANNING..."
"📝 GENERATION PHASE EXECUTION CHECKLIST..."
```

**Problem**: All this is AFTER
```
"FRAMEWORK LAYER MAPPING: ... controller, service, repository, dto, model"
"AVAILABLE FILES TO MODIFY: src/main/java/com/example/demo/HelloController.java"
```

Agent's reasoning path:
1. See "FRAMEWORK LAYER MAPPING" - familiar structure
2. See "AVAILABLE FILES TO MODIFY: HelloController" - existing code
3. See "Create delivery files" - spec
4. Pattern match: Existing code is more concrete than spec
5. **Conclusion**: "I'll analyze HelloController and suggest delivery patterns"
6. **Action**: read_file(HelloController), then edit_file() or write_todos()

### 6. Tool_call_id Not Preserved Causes Fallback
**File**: flow_synthesize_code.py, line 104

```python
def _extract_patch_from_call(call_dict, progress):
    patch = {
        'tool': call_dict.get('name'),
        'args': call_dict.get('arguments'),
        'file': ...,
        ...
    }
    # ❌ Missing: 'tool_call_id': call_dict.get('id')
    # This ID is needed to correlate results back to calls
```

**Impact**: When tool results come back with `tool_call_id="call_abc123"`, we can't match them to original calls.

## ✅ RECOMMENDED FIX: Reorder Prompt for Context Isolation

**FASTEST FIX** (not perfect, but works immediately):

Place spec emphasis BEFORE framework context in `build_implementation_prompt()`:

```python
implementation_prompt = f"""
CRITICAL - READ FIRST:
=======================
YOUR TASK: Create ONLY these 10 NEW files for delivery routing system:

1. Delivery.java (src/main/java/com/example/delivery/domain/entity/)
2. DeliveryRepository.java (src/main/java/com/example/delivery/domain/repository/)
3. JpaDeliveryRepository.java (src/main/java/com/example/delivery/adapters/persistence/)
4. DeliveryDTO.java (src/main/java/com/example/delivery/application/dto/)
5. Courier.java (src/main/java/com/example/delivery/domain/entity/)
6. CourierRepository.java (src/main/java/com/example/delivery/domain/repository/)
7. CourierPositionDTO.java (src/main/java/com/example/delivery/application/dto/)
8. Route.java (src/main/java/com/example/delivery/domain/entity/)
9. RouteOptimizer.java (src/main/java/com/example/delivery/domain/service/)
10. GraphHopperRouteOptimizer.java (src/main/java/com/example/delivery/adapters/optimization/)

MANDATORY CONSTRAINTS:
✅ ONLY use write_file() tool
✅ DO NOT read any existing files
✅ DO NOT edit any existing files
✅ DO NOT modify GreetingService, HelloController, or any existing code
✅ DO NOT use edit_file, read_file, ls, write_todos
✅ Stop after creating 10 files

---

FRAMEWORK CONTEXT (for reference only):
{framework_prompt}

---

NEW FILES PLANNING:
{new_files_section}

[rest of prompt...]
"""
```

**Why this works**:
1. Spec comes FIRST in token count → agent focuses on it
2. Explicit "DO NOT edit existing" prevents pattern matching
3. File list with paths → no ambiguity
4. Constraints before framework context → stronger precedence

### Alternative Fix: Create Generation Subagent (Proper Implementation)

**For production**: Create subagent with tool whitelist

```python
# In agent_factory.py
def create_generation_subagent(spec, framework_prompt):
    """
    Specialized subagent for ONLY creating new files
    - Cannot read existing files
    - Cannot edit existing files  
    - Tools: [write_file only]
    """
    return {
        'name': 'code_generator',
        'description': 'Creates new files for delivery routing system',
        'system_prompt': f"""
            You are a code generator specialist.
            
            Your ONLY job: Create these 10 new files:
            {spec.new_files_planning}
            
            STRICT RULES:
            1. ONLY call write_file()
            2. Generate complete Java code for each file
            3. No analysis, no reading, no editing
            4. Stop after 10 files
        """,
        'tools': [write_file_tool],  # Only this tool available
        'model': 'same-as-main'
    }

# Then in flow_synthesize_code.py:
# Instead of:
# result2 = agent.stream({"input": implementation_prompt})

# Use:
# result2 = agent.stream({"input": "Use task() to delegate to code_generator subagent for creating new delivery files"})
# Main agent delegates to specialized subagent
# Main agent gets back: "Created 10 files successfully"
# Context stays clean, spec is enforced
```

## ✅ Recommended Solution Path (Progressive)

**Phase 1** (IMMEDIATE - TODAY): Reorder prompt
- Move spec to top of implementation_prompt
- Add explicit "DO NOT modify existing code" constraint
- Add file list with exact paths
- Test predefined mode → verify if this alone solves it

**Phase 2** (IF Phase 1 doesn't work): Fix tool_call_id preservation
- Add `'tool_call_id': call_dict.get('id')` in _extract_patch_from_call()
- Ensure ToolMessages are properly correlated

**Phase 3** (IF still not working): Create generation subagent
- Implement proper tool whitelist via subagent
- Only write_file available
- Isolates generation from analysis

**Phase 4**: Test fully
- Run predefined mode
- Verify 10 delivery files created
- Verify 0 Greeting files
- Verify 0 edit_file calls

## 📖 References
- LangChain Tool Calling: https://docs.langchain.com/oss/python/langchain/models
- DeepAgent Subagents: https://docs.langchain.com/oss/python/deepagents/subagents
- Tool Message Pattern: Each ToolMessage MUST have tool_call_id matching original call.id
