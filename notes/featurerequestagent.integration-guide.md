# Integration Guide: Middleware into feature_by_request_agent_v2.py

## 🎯 Quick Summary

**What changed:**
- Created `middleware.py` with 3 LangChain middleware classes
- These need to be integrated into Phase 4 agent creation

**Files to modify:**
- `feature_by_request_agent_v2.py` - Add middleware imports + factory function usage

**Testing:**
- Run same command as before, verify correct files are modified

---

## 📝 Step-by-Step Integration

### Step 1: Import Middleware

At top of `feature_by_request_agent_v2.py`, add:

```python
from middleware import (
    IntentReminderMiddleware,
    FileScopeGuardrail,
    ToolCallValidationMiddleware,
    create_phase4_middleware,
    log_middleware_config,
)
```

---

### Step 2: Create Helper Function

Add this function to replace old `create_code_synthesis_agent`:

```python
def create_code_synthesis_agent_v2(
    codebase_path: str,
    feature_request: str,
    affected_files: List[str]
):
    """
    Phase 4: Code Synthesis with Intent Reminder + Guardrails
    
    This version includes middleware to:
    1. Remind model of feature request at every model call
    2. Validate output doesn't mention unauthorized files
    3. Block file operations outside allowed scope
    """
    backend = FilesystemBackend(root_dir=codebase_path)
    
    # Create middleware stack
    middleware = create_phase4_middleware(
        feature_request=feature_request,
        affected_files=affected_files,
        codebase_root=codebase_path
    )
    
    prompt = f"""\
You are an expert software engineer implementing a feature with production-quality standards.

CODEBASE: {codebase_path}

Your task:
1. Read existing code files to understand patterns, naming conventions, imports
2. Plan implementation using write_todos with specific file changes
3. Follow SOLID principles:
   - Single Responsibility: Each class/function has one purpose
   - Open/Closed: Open for extension, closed for modification
   - Liskov Substitution: Proper inheritance and interface design
   - Interface Segregation: Small, focused interfaces
   - Dependency Inversion: Depend on abstractions, not concrete implementations
4. Use appropriate design patterns (Factory, Strategy, Decorator, etc)
5. Write testable code: dependency injection, pure functions, isolated concerns
6. Use edit_file and write_file tools to implement changes
7. Follow existing code style exactly (naming, formatting, structure)
8. DO NOT add new dependencies - use only what's already in pom.xml/package.json
9. Ensure code compiles/runs immediately without config changes

Generate production-grade code that fellow engineers would be proud to review.

REMINDER: You have middleware that will:
- Remind you of the primary objective before each model call
- Block any file edits outside the allowed scope
- Validate your output for scope violations

Trust these guardrails and focus on implementing the feature correctly.
"""
    
    # Pass middleware to agent
    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model,
        backend=backend,
        middleware=middleware  # ← CRITICAL ADDITION
    )
```

---

### Step 3: Update Phase 4 Function

Replace `run_code_synthesis_phase` with new version:

```python
def run_code_synthesis_phase_v2(
    codebase_path: str,
    context: str,
    spec: FeatureSpec,
    impact: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Phase 4: Expert code generation with Intent Reminder + Guardrails
    
    Now includes middleware to prevent agent deviation and file scope violations.
    """
    print("⚙️ Phase 4: Expert code generation with intent reminder & guardrails...")
    
    files_to_modify = impact.get("files_to_modify", spec.affected_files)
    architecture = impact.get("architecture_insights", "")[:500]
    
    # Log middleware configuration
    log_middleware_config(spec.intent_summary, files_to_modify)
    
    # Create agent WITH middleware
    agent = create_code_synthesis_agent_v2(
        codebase_path=codebase_path,
        feature_request=spec.intent_summary,  # ← Pass feature request
        affected_files=files_to_modify  # ← Pass allowed files
    )
    
    # Multi-step expert implementation
    # Step 1: Agent analyzes and plans
    print("  📋 Step 1: Agent analyzing code patterns and planning implementation...")
    analysis_prompt = f"""
FEATURE REQUEST: {spec.intent_summary}

FILES TO MODIFY: {', '.join(files_to_modify[:3])}

STEP 1: ANALYSIS & PLANNING

1. Use read_file to examine each file in FILES TO MODIFY
2. Understand the existing code structure, naming conventions, imports, and patterns
3. Identify classes, interfaces, methods, and their responsibilities
4. Use write_todos to create a detailed implementation plan with:
   - Task: Understand [file] - purpose and current implementation
   - Task: Identify patterns - what design patterns are used
   - Task: Plan changes to [file] - exactly what needs to change
   - Task: Implement [method/class] - with specific code requirements
   - Task: Create tests for [functionality]

ARCHITECTURE CONTEXT:
{architecture}

Be thorough in understanding before planning implementation.

IMPORTANT: Stay focused on the feature request. Your middleware will remind you
and block any deviations. Only modify the allowed files listed above.
"""
    
    _analysis_result = agent.invoke({"input": analysis_prompt})
    
    # Step 2: Agent implements based on plan
    print("  🛠️  Step 2: Agent implementing changes with guardrails...")
    implementation_prompt = f"""
FEATURE: {spec.intent_summary}
FILES: {', '.join(files_to_modify[:3])}

STEP 2: IMPLEMENTATION

NOW implement the changes using write_file and edit_file tools:

1. FOLLOW SOLID PRINCIPLES:
   - Single Responsibility: Each class has one clear purpose
   - Open/Closed: Extensible, minimal changes to existing code
   - Liskov Substitution: Use proper inheritance and interfaces
   - Interface Segregation: Small, focused interfaces
   - Dependency Inversion: Depend on abstractions, not implementations

2. CODE QUALITY STANDARDS:
   - Match existing code style exactly (naming, formatting, structure)
   - Use existing imports and dependencies only
   - Write testable code: use dependency injection, pure functions
   - Add meaningful comments for complex logic
   - Ensure code compiles immediately

3. IMPLEMENTATION FOCUS:
   - ONLY modify these files: {', '.join(files_to_modify[:3])}
   - DO NOT create new files (except if explicitly in feature request)
   - DO NOT modify files outside the list above
   - Follow existing patterns and conventions
   - Use existing Spring Boot starter-web and starter-test (already in pom.xml)
   - Code must be production-ready and testable

4. SPECIFIC REQUIREMENTS:
   - Feature request: {spec.intent_summary}
   - Use only existing dependencies
   - Code must be production-ready and testable

Generate the actual code implementation NOW.

Remember: Middleware is validating your work.
- Before each model call: reminded of feature + allowed files
- After model calls: your output checked for scope violations
- Tool calls: validated before execution

Focus on implementing the feature correctly within these constraints.
"""
    
    result2 = agent.invoke({"input": implementation_prompt})
    
    # Extract patches from implementation step
    patches = []
    if "messages" in result2:
        for msg in result2.get("messages", []):
            if hasattr(msg, "tool_calls"):
                for call in getattr(msg, "tool_calls", []):
                    if call.get("name") in ["write_file", "edit_file"]:
                        patches.append({
                            "tool": call.get("name"),
                            "args": call.get("args", {}),
                            "description": "Generated patch"
                        })
            
            if hasattr(msg, "content") and msg.content and patches:
                print(f"  ✓ Generated {len(patches)} code change(s)")
                for p in patches:
                    file_path = p['args'].get('path', 'unknown')
                    print(f"    - {p['tool']}: {file_path}")
                return patches
    
    if not patches and "messages" in result2:
        for msg in reversed(result2.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                content_str = str(msg.content)[:300]
                print(f"  ℹ️ Agent response: {content_str}")
                break
    
    return patches
```

---

### Step 4: Update Main Function Call

In the `main()` function, change the Phase 4 call:

```python
def main():
    # ... existing code ...
    
    if not is_feature_mode:
        print("\n📊 ANALYSIS COMPLETE:")
        print("=" * 80)
        print(state.context_analysis)
        return

    # Phase 2-5: Feature implementation workflow
    state.feature_spec = run_intent_parsing_phase(args.feature_request, state.context_analysis)
    state.impact_analysis = run_impact_analysis_phase(codebase_path, state.context_analysis, state.feature_spec)
    
    # ← UPDATED: Use v2 with middleware
    state.code_patches = run_code_synthesis_phase_v2(
        codebase_path,
        state.context_analysis,
        state.feature_spec,
        state.impact_analysis
    )
    
    state.execution_results = run_execution_phase(codebase_path, state.code_patches, args.dry_run)
    
    # ... rest of main ...
```

---

### Step 5: Remove Old Function

Delete the old `create_code_synthesis_agent()` and `run_code_synthesis_phase()` functions.

---

## 🧪 Testing

### Test Command

```bash
source .venv/bin/activate && timeout 150 python scripts/feature_by_request_agent_v2.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add a new API endpoint /api/users/by-role that returns users filtered by role"
```

### Expected Output

```
🤖 FEATURE-BY-REQUEST AGENT
================================================================================
📁 Codebase: /Users/.../dataset/codes/springboot-demo
🛠️  Model: gpt-5-mini
🌡️  Temperature: 1.0
🎯 Feature: Add a new API endpoint /api/users/by-role...
🏃 Mode: IMPLEMENT
================================================================================

🔍 Phase 1: Analyzing codebase context...
  ✓ Project: Java Spring Boot application
  ✓ Framework: Spring Boot 2.7+
  
🎯 Phase 2: Expert analysis - creating implementation plan...
  ✓ Feature: Add a new API endpoint...
  ✓ Analysis steps: 5 tasks identified
  ✓ Affected files: 2 file(s)
    - src/main/java/com/example/HelloController.java
    - src/main/java/com/example/UserService.java

📊 Phase 3: Architecture analysis - identifying patterns and impact...
  ✓ Files to modify: 2 file(s)
  ✓ Patterns identified: 3 pattern(s)
  ✓ Analysis tasks: 4 task(s)

⚙️ Phase 4: Expert code generation with intent reminder & guardrails...
🔧 Middleware Configuration:
  Feature: Add a new API endpoint /api/users/by-role...
  Allowed files: 2 file(s)
    • src/main/java/com/example/HelloController.java
    • src/main/java/com/example/UserService.java
  📋 Step 1: Agent analyzing code patterns...
  🛠️  Step 2: Agent implementing changes with guardrails...
  ✓ Generated 2 code change(s)
    - edit_file: src/main/java/com/example/HelloController.java
    - edit_file: src/main/java/com/example/UserService.java

🚀 Phase 5: EXECUTE...
  ℹ️ Applying 2 patch(es)...
    - edit_file: src/main/java/com/example/HelloController.java
    - edit_file: src/main/java/com/example/UserService.java

================================================================================
🎉 COMPLETE
================================================================================
Feature: Add a new API endpoint /api/users/by-role
Files Affected: 2
New Files: 0
Patches: 2
Time: 45.23s
```

### Key Verification Points

✅ **No GreetingService.java created**  
✅ **Only HelloController.java and UserService.java modified**  
✅ **Files listed in "Allowed files" section**  
✅ **Middleware logs show feature reminders injected**  
✅ **Phase 4 completes without guardrail violations**

---

## 🔍 Debugging Middleware

### Check LangSmith Traces

Look for middleware decisions in LangSmith:

1. **Before Model Hooks**: Should see injected reminder messages
   - Content: "🎯 PRIMARY OBJECTIVE", "📁 ALLOWED FILES"

2. **After Model Hooks**: Should see validation checks
   - Content: "File scope validation passed" or "BLOCKED"

3. **Tool Call Validation**: Should see path checks
   - Tool: "wrap_tool_call"
   - Args: "path" validation

### Manual Verification

```bash
# Check if GreetingService.java exists
ls -la dataset/codes/springboot-demo/src/main/java/com/example/GreetingService.java
# Should return: "No such file"

# Check if HelloController was modified
grep -n "by-role" dataset/codes/springboot-demo/src/main/java/com/example/HelloController.java
# Should return: Line with endpoint definition
```

---

## 🎯 Success Criteria

| Criterion | Before | After | Status |
|-----------|--------|-------|--------|
| Creates GreetingService.java | ❌ YES | ✅ NO | [To Test] |
| Modifies HelloController.java | ❌ NO | ✅ YES | [To Test] |
| Only touches allowed files | ❌ NO | ✅ YES | [To Test] |
| Feature correctly implemented | ❌ NO | ✅ YES | [To Test] |
| Phase 4 completes <2 min | ❌ NO | ✅ YES | [To Test] |

---

## 📚 Files Modified

| File | Change | Type |
|------|--------|------|
| `middleware.py` | Created | New |
| `feature_by_request_agent_v2.py` | Added imports, new functions, updated main | Updated |
| `SOLUTION_ARCHITECTURE.md` | Created | New |
| `MIDDLEWARE_IMPLEMENTATION_PLAN.md` | Created | New |

---

## 🚀 Next Steps

1. ✅ **Review** this integration guide
2. ✅ **Integrate** middleware into v2 using steps above
3. ✅ **Test** on springboot-demo
4. ✅ **Verify** no GreetingService.java created
5. ✅ **Check** LangSmith traces for middleware decisions
6. ✅ **Document** results in issue tracking
