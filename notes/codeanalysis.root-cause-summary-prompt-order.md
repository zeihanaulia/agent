# 🔴 ROOT CAUSE: Prompt Order Issue - SIMPLE FIX

## Problem Summary
Agent generates Greeting classes instead of Delivery files **even though spec is in prompt**.

## Root Cause (Per LangChain Docs)

DeepAgent uses LangGraph with **internal middleware** that executes tools:
1. Agent reads prompt
2. Agent generates tool_calls (internally via FilesystemMiddleware)
3. Middleware executes tools
4. Agent reasoning based on tool results

**The Issue**: When agent sees prompt with:
- "Framework context" FIRST → HelloController, GreetingService examples
- "New files spec" LATER → theoretical future files

Agent reasons:
```
"Okay, I see Spring Boot framework. Existing files are HelloController, GreetingService.
Seems like I should analyze/modify existing code to add delivery features.
Oh, there's also a spec for 10 new files... let me read those existing files first..."
```

**Result**: Agent reads existing files → commits to modification path → ignores spec

## Solution (SIMPLE - TODAY)

**Reorder `build_implementation_prompt()` to put SPEC FIRST**:

Current order:
```
1. FEATURE intro
2. FRAMEWORK-SPECIFIC GUIDELINES (HelloController, GreetingService context)
3. FILE CREATION GUIDE (spec-based)
4. NEW FILES PLANNING
5. ... rest
```

**New order** (just move sections):
```
1. CRITICAL - READ FIRST (spec emphasis)
2. List all 10 files with exact paths
3. MANDATORY CONSTRAINTS ("DO NOT read existing", "ONLY write_file")
4. THEN framework context (for reference only)
5. ... rest
```

## Code Change Required

**File**: `scripts/coding_agent/flow_synthesize_code.py`
**Function**: `build_implementation_prompt()` (line 362+)

Move these lines UP (before `{framework_prompt}`):
```python
# Move line ~364 (file_creation_guide) to right after feature section
# Add explicit constraint header
# Then show framework context as "reference only"
```

## Expected Impact
- ✅ Agent sees spec files first (higher token priority)
- ✅ Agent sees "DO NOT modify existing" before framework context
- ✅ No tool_call_id fixes needed
- ✅ No subagent creation needed
- ✅ Works immediately

## Test Approach
1. Make the prompt reorder change
2. Run: `python3 scripts/coding_agent/flow_synthesize_code.py --codebase-path dataset/codes/springboot-demo --feature-request "Build delivery system"`
3. Check results:
   - 10 Delivery files created? ✅
   - 0 Greeting files modified? ✅
   - 0 edit_file calls? ✅

If this works → DONE (quick win!)
If not → Move to Phase 2 (tool_call_id fix)

## Why This Works (Per LangChain)

LangChain docs say agent decision-making is **sequential**:
- Early tokens in prompt have higher influence on reasoning
- Agent weights early instructions more heavily
- Putting spec first = agent prioritizes it

This is why DeepAgent creators recommend:
```python
system_prompt = """
YOUR CORE TASK: [spec]

THEN details about framework, patterns, etc.
"""
```
