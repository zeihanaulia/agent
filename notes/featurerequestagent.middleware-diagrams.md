# Middleware Architecture Diagrams & Flowcharts

## 🎯 Problem Visualization

### Current Behavior (Buggy - v2)

```
USER REQUEST: "Add endpoint /api/users/by-role"
  ↓
PHASE 4: Code Synthesis (NO MIDDLEWARE)
  ↓
MODEL CALL 1:
  Input: Generic prompt (no context about MUST use HelloController.java)
  ↓
TOOL CALL 1: read_file("HelloController.java")
  Agent reads current code... ✓
  ↓
MODEL CALL 2: Process file content
  ❌ MODEL FORGOT primary intent
  ❌ No reminder about scope
  Output: "I'll create GreetingService.java to greet users"
  ↓
TOOL CALL 2: write_file("GreetingService.java", ...)
  ❌ NO VALIDATION
  File created ✗
  ↓
RESULT: ❌ WRONG FILE CREATED
  - GreetingService.java exists (wrong)
  - HelloController.java unchanged (wrong)
  - Feature NOT implemented
```

---

### Fixed Behavior (With Middleware)

```
USER REQUEST: "Add endpoint /api/users/by-role"
  ↓
PHASE 4: Code Synthesis (WITH MIDDLEWARE)
  ↓
MODEL CALL 1:
  [before_model] → Inject intent reminder
    "🎯 PRIMARY: Add /api/users/by-role"
    "📁 ALLOWED: HelloController.java, UserService.java"
  ↓
  Input: Prompt + reminder (CLEAR INTENT)
  ↓
TOOL CALL 1: read_file("HelloController.java")
  [wrap_tool_call] → Validate path
    "HelloController.java in allowed?" → YES ✓
  Agent reads current code ✓
  ↓
MODEL CALL 2: Process file content
  [before_model] → Inject reminder AGAIN
    "🎯 PRIMARY: Add /api/users/by-role" (REPEAT)
  ↓
  Input: Previous context + reminder (FOCUSED)
  Output: "I'll add method to HelloController.java"
  ↓
  [after_model] → Validate output
    "Only mentions allowed files?" → YES ✓
  ↓
TOOL CALL 2: edit_file("HelloController.java", ...)
  [wrap_tool_call] → Validate path
    "HelloController.java in allowed?" → YES ✓
  File modified ✓
  ↓
RESULT: ✅ CORRECT FILE MODIFIED
  - GreetingService.java NOT created ✓
  - HelloController.java correctly modified ✓
  - Feature implemented ✓
```

---

## 🔄 Middleware Execution Pipeline

### Simplified View

```
┌─────────────────────────────────────────────────────────────────┐
│                         PHASE 4 AGENT                           │
│                    (Code Synthesis with Middleware)             │
└─────────────────────────────────────────────────────────────────┘

                            ↓ START

    ┌───────────────────────────────────────────────────────────┐
    │ [1] BEFORE MODEL HOOK                                     │
    │ IntentReminderMiddleware.before_model()                   │
    │                                                            │
    │ Prepend to state["messages"]:                             │
    │   - "🎯 PRIMARY OBJECTIVE"                                │
    │   - "📁 ALLOWED FILES"                                    │
    │   - "⚠️  CONSTRAINTS"                                     │
    └───────────────────────────────────────────────────────────┘
                            ↓

    ┌───────────────────────────────────────────────────────────┐
    │ [2] MODEL CALL                                            │
    │ LLM processes messages with injected reminder             │
    │ (Model can't "forget" - reminder is always there)         │
    └───────────────────────────────────────────────────────────┘
                            ↓

    ┌───────────────────────────────────────────────────────────┐
    │ [3] AFTER MODEL HOOK                                      │
    │ FileScopeGuardrail.after_model()                          │
    │                                                            │
    │ Check model output for unauthorized file mentions         │
    │ If violation detected: jump_to="end" BLOCKS execution     │
    └───────────────────────────────────────────────────────────┘
                            ↓

    ┌───────────────────────────────────────────────────────────┐
    │ [4] WRAP TOOL CALL HOOK                                   │
    │ ToolCallValidationMiddleware.wrap_tool_call()             │
    │                                                            │
    │ For write_file / edit_file:                               │
    │   - Extract path from tool arguments                      │
    │   - Check against allowed_files set                       │
    │   - If path NOT allowed: Return error message             │
    │   - If path allowed: Execute tool                         │
    └───────────────────────────────────────────────────────────┘
                            ↓

    ┌───────────────────────────────────────────────────────────┐
    │ [5] TOOL EXECUTION                                        │
    │ (Only if passed all 3 layers)                             │
    │ write_file or edit_file executes                          │
    └───────────────────────────────────────────────────────────┘
                            ↓

    [Loop back to before_model for next model call]
    (Reminder injected again automatically)
                            ↓

    ┌───────────────────────────────────────────────────────────┐
    │ [6] REPEAT UNTIL COMPLETION                               │
    │ Model might call multiple tools                           │
    │ Each iteration goes through all hooks                      │
    │ Each iteration, reminder is re-injected                    │
    └───────────────────────────────────────────────────────────┘
                            ↓

                            END
```

---

## 🛡️ Defense Layers Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEFENSE IN DEPTH ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────┘

LAYER 1: INTENTION ENFORCEMENT
┌───────────────────────────────────────────────────────────────────┐
│ Hook: before_model                                                │
│ Component: IntentReminderMiddleware                               │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐  │
│ │ Inject system message at START of model call               │  │
│ │                                                             │  │
│ │ "🎯 PRIMARY OBJECTIVE: Add /api/users/by-role endpoint"   │  │
│ │ "📁 ALLOWED FILES:                                         │  │
│ │    • HelloController.java                                  │  │
│ │    • UserService.java"                                    │  │
│ │ "⚠️ DO NOT create GreetingService.java"                    │  │
│ └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│ Effect: Model "sees" constraints in every LLM call               │
│ Weakness: Model might still ignore (theoretical)                 │
│ Strength: Constant, automatic reinforcement                       │
└───────────────────────────────────────────────────────────────────┘

                            ↓ (Model responds)

LAYER 2: OUTPUT VALIDATION
┌───────────────────────────────────────────────────────────────────┐
│ Hook: after_model                                                 │
│ Component: FileScopeGuardrail                                    │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐  │
│ │ Check model output for file path mentions:                 │  │
│ │                                                             │  │
│ │ if "GreetingService.java" in output:                      │  │
│ │   ❌ VIOLATION DETECTED                                     │  │
│ │   return {"jump_to": "end"}  # STOP EXECUTION              │  │
│ │   Insert: "BLOCKED: File not allowed"                     │  │
│ │                                                             │  │
│ │ if only allowed files mentioned:                           │  │
│ │   ✅ OUTPUT VALID                                           │  │
│ │   return None  # Continue normally                         │  │
│ └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│ Effect: Catches violations BEFORE tool execution                 │
│ Weakness: Model might not explicitly mention file name           │
│ Strength: Second line of defense, catches explicit violations    │
└───────────────────────────────────────────────────────────────────┘

                      ↓ (Tool call decided)

LAYER 3: EXECUTION GUARD
┌───────────────────────────────────────────────────────────────────┐
│ Hook: wrap_tool_call                                              │
│ Component: ToolCallValidationMiddleware                           │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐  │
│ │ Intercept tool execution (before actual filesystem access) │  │
│ │                                                             │  │
│ │ if tool_name in ["write_file", "edit_file"]:              │  │
│ │   abs_path = normalize(tool_args["path"])                 │  │
│ │                                                             │  │
│ │   if abs_path NOT in allowed_paths:                       │  │
│ │     ❌ VIOLATION DETECTED                                   │  │
│ │     return ToolMessage("BLOCKED: Path not allowed")       │  │
│ │     Tool NOT executed                                      │  │
│ │                                                             │  │
│ │   if abs_path in allowed_paths:                           │  │
│ │     ✅ PATH AUTHORIZED                                     │  │
│ │     return handler(request)  # Execute tool               │  │
│ │                                                             │  │
│ │ else:  # Not a file-modifying tool                        │  │
│ │   return handler(request)  # Let other tools through       │  │
│ └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│ Effect: Bulletproof - NO unauthorized file operations possible   │
│ Weakness: None (operates at execution level)                     │
│ Strength: Hardest to bypass, final enforcement                   │
└───────────────────────────────────────────────────────────────────┘

                      ↓ (Tool executes or blocked)

RESULT: Triply-enforced constraints
```

---

## 📊 State Mutation During Phase 4

### Timeline

```
TIME=0: Agent Initialize
┌──────────────────────────────────────────────────┐
│ state = {                                        │
│   "messages": [HumanMessage("user prompt")],     │
│   "codebase_path": "...",                        │
│   "feature_request": "Add endpoint /api/users/..." │
│   "affected_files": ["HelloController.java", ...]  │
│ }                                                │
└──────────────────────────────────────────────────┘

TIME=1: before_model Hook
┌──────────────────────────────────────────────────┐
│ state["messages"] MUTATED:                       │
│ [                                                │
│   SystemMessage("🎯 PRIMARY OBJECTIVE..."),   ← INJECTED
│   SystemMessage("📁 ALLOWED FILES..."),        ← INJECTED
│   HumanMessage("user prompt")                    │
│ ]                                                │
│                                                  │
│ Effect: Model sees constraints at TOP of context │
└──────────────────────────────────────────────────┘

TIME=2: Model Call 1
┌──────────────────────────────────────────────────┐
│ LLM Input: All 3 messages (including reminders)  │
│ LLM Output: AIMessage("I'll read HelloController") │
│                                                  │
│ state["messages"] += [AIMessage(...)]            │
└──────────────────────────────────────────────────┘

TIME=3: after_model Hook
┌──────────────────────────────────────────────────┐
│ Validate: "HelloController" in allowed? → YES ✓  │
│ No mutations needed                              │
└──────────────────────────────────────────────────┘

TIME=4: wrap_tool_call Hook
┌──────────────────────────────────────────────────┐
│ Tool: read_file("HelloController.java")          │
│ Validate: Path in allowed? → YES ✓               │
│ Execute: handler(request)                        │
│ Result: ToolMessage(file_content)                │
│                                                  │
│ state["messages"] += [ToolMessage(...)]          │
└──────────────────────────────────────────────────┘

TIME=5: before_model Hook (Again!)
┌──────────────────────────────────────────────────┐
│ state["messages"] MUTATED AGAIN:                 │
│ Check: Already has reminder? → NO (already       │
│        injected one is still there!)              │
│ No duplicate injection (by design)                │
│                                                  │
│ Effect: Reminder still active for next model call │
└──────────────────────────────────────────────────┘

TIME=6: Model Call 2
┌──────────────────────────────────────────────────┐
│ LLM Input: [Reminders, prev output, tool result] │
│ LLM Output: AIMessage("I'll add method...")      │
│                                                  │
│ state["messages"] += [AIMessage(...)]            │
└──────────────────────────────────────────────────┘

TIME=7: after_model Hook
┌──────────────────────────────────────────────────┐
│ Validate: "HelloController" in allowed? → YES ✓  │
│ No violations detected                           │
└──────────────────────────────────────────────────┘

TIME=8: wrap_tool_call Hook
┌──────────────────────────────────────────────────┐
│ Tool: edit_file("HelloController.java", code)    │
│ Validate: Path in allowed? → YES ✓               │
│ Execute: handler(request)                        │
│ Result: ToolMessage(success)                     │
└──────────────────────────────────────────────────┘

FINAL: State after Phase 4
┌──────────────────────────────────────────────────┐
│ state["messages"] contains:                      │
│ 1. SystemMessage(reminders)                      │
│ 2. HumanMessage(original input)                  │
│ 3. AIMessage(model output 1)                     │
│ 4. ToolMessage(read_file result)                 │
│ 5. AIMessage(model output 2)                     │
│ 6. ToolMessage(edit_file result)                 │
│                                                  │
│ File System:                                     │
│ ✓ HelloController.java: MODIFIED                 │
│ ✗ GreetingService.java: NOT CREATED              │
│                                                  │
│ Result: SUCCESS ✓                                │
└──────────────────────────────────────────────────┘
```

---

## 🔄 Middleware Composition

### Stacking Order

```
Middleware Stack = [
    IntentReminderMiddleware      (Index 0)
    FileScopeGuardrail            (Index 1)
    ToolCallValidationMiddleware  (Index 2)
]

Hook Execution Order:
  before_agent:  [0 → 1 → 2]  (forward)
  before_model:  [0 → 1 → 2]  (forward) ← Intent reminder here
  wrap_tool_call: [0 → 1 → 2] (forward) ← Tool validation here
  after_model:   [2 → 1 → 0]  (reverse) ← Output validation here
  after_agent:   [2 → 1 → 0]  (reverse)

Each middleware can:
  ✓ Inspect state/request
  ✓ Modify state/request
  ✓ Return {"jump_to": "end"} to stop execution
  ✓ Call next middleware or return early
```

---

## 🎓 Concept Map

```
                    FEATURE REQUEST
                          ↓
                   user_intent: str
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
  INTENT REMINDER                  FILE SCOPE CONSTRAINTS
  (before_model)                   (after_model + wrap_tool_call)
        ↓                                   ↓
  Model sees:                       Model output checked:
  - Primary objective               - Only mentioned allowed files?
  - Allowed files                   - File paths validated before execution
  - Constraints                     - Tool calls intercepted and validated
        ↓                                   ↓
   Model stays                      Model deviations
   focused                          prevented
        ↓                                   ↓
  ┌─────────────────────────────────────────┐
  │                                         │
  │         CORRECT IMPLEMENTATION           │
  │                                         │
  │  • HelloController.java MODIFIED ✓      │
  │  • GreetingService.java NOT CREATED ✓   │
  │  • Feature endpoint added correctly ✓   │
  │                                         │
  └─────────────────────────────────────────┘
```

---

**These diagrams help visualize how the 3 middleware layers work together to keep the agent focused and prevent unauthorized file operations.**
