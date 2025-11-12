# Quick Reference: Coding Agent Module Structure

**Last Updated:** November 11, 2025

---

## 📁 Module Organization

### Workflow Phases (flow_ prefix)
```
flow_analyze_context.py
  └─ Phase 1: Analyze codebase context
     • Uses Aider-style analysis
     • Detects framework & tech stack
     • Produces: context_analysis

flow_parse_intent.py  
  └─ Phase 2: Parse feature request intent
     • Creates structured plan
     • Identifies affected files
     • Produces: feature_spec, todo_list, new_files

flow_validate_structure.py
  └─ Phase 2A: Validate architecture structure
     • Iterative refinement (3 rounds)
     • Auto-fix missing directories
     • Scoring: 0-100
     • Produces: structure_assessment, violations
```

### Main Orchestrator
```
feature_by_request_agent_v3.py
  └─ LangGraph workflow coordinator
     • Manages all 6 phases
     • State machine with conditional routing
     • CLI: --codebase-path, --feature-request, --dry-run
```

### Support Modules
```
framework_instructions.py
  └─ Framework-specific rules & patterns
     • Spring Boot, Django, Node.js, etc.
     • Layer mapping & file patterns
     • Detection & conventions

middleware.py
  └─ Phase 4 guardrails & middleware
     • IntentReminderMiddleware
     • FileScopeGuardrail
     • ToolCallValidationMiddleware
```

---

## 🔄 Workflow Flow

```
START
  ↓
Phase 1: flow_analyze_context
  • Filesystem scan
  • Framework detection
  • Result: context_analysis
  ↓
Phase 2: flow_parse_intent
  • Feature intent analysis
  • File identification
  • Result: feature_spec, todo_list, new_files
  ↓
Phase 2A: flow_validate_structure
  • Architecture validation
  • Iterative refinement
  • Result: structure_assessment, violations
  ↓
Phase 3: analyze_impact (in main agent)
  • Impact analysis
  • Pattern identification
  • Result: impact_analysis
  ↓
Phase 4: synthesize_code (in main agent)
  • Code generation
  • Middleware guardrails applied
  • Result: code_patches
  ↓
Phase 5: execute_changes (in main agent)
  • Apply patches to filesystem
  • Verify changes
  • Result: execution_results
  ↓
END
```

---

## 📚 Key Functions

### flow_analyze_context.py
- `AiderStyleRepoAnalyzer(codebase_path, max_tokens)` - Main analyzer
- `infer_app_type(basic, structure)` - App type detection
- `analyze_with_reasoning()` - LLM-enhanced analysis

### flow_parse_intent.py
- `flow_parse_intent(state, analysis_model, framework_detector)` - Main function
- `generate_structured_todos()` - Create task list
- `infer_new_files_needed()` - Identify new files
- `write_todo_file()` - Persist todos to markdown

### flow_validate_structure.py
- `EnhancedStructureValidator` - Main validator class
- `validate_structure_with_feedback()` - Iterative validation
- `_validate_spring_boot()` - Framework-specific validation
- `_apply_refinement()` - Auto-fix missing directories

### feature_by_request_agent_v3.py
- `create_feature_request_workflow()` - Build LangGraph
- `analyze_context()` - Phase 1 node
- `parse_intent()` - Phase 2 node
- `validate_structure()` - Phase 2A node
- `analyze_impact()` - Phase 3 node
- `synthesize_code()` - Phase 4 node
- `execute_changes()` - Phase 5 node

---

## 🚀 Quick Start

### Run Full Workflow
```bash
cd /Users/zeihanaulia/Programming/research/agent
source .venv/bin/activate
python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add user authentication"
```

### Run with Options
```bash
# Dry-run mode (no file changes)
--dry-run

# Enable human approval loop
--enable-human-loop

# Specify model
--model gpt-4o-mini

# Set temperature
--temperature 0.7
```

### Run Tests
```bash
python3 test_validate_structure_enhanced.py
python3 test_flow_parse_intent_v2.py
```

---

## 📊 State Machine

### AgentState TypedDict
```python
{
    "codebase_path": str,
    "feature_request": Optional[str],
    "context_analysis": Optional[str],          # Phase 1 output
    "feature_spec": Optional[FeatureSpec],      # Phase 2 output
    "structure_assessment": Optional[Dict],     # Phase 2A output
    "impact_analysis": Optional[Dict],          # Phase 3 output
    "code_patches": Optional[List[Dict]],       # Phase 4 output
    "execution_results": Optional[Dict],        # Phase 5 output
    "errors": List[str],
    "dry_run": bool,
    "current_phase": str,
    "framework": Optional[str]
}
```

---

## 🎯 Naming Convention

### Pattern
```
flow_<phase_name>.py
```

### Current Phases
- ✅ `flow_analyze_context.py` - Analyze
- ✅ `flow_parse_intent.py` - Parse Intent
- ✅ `flow_validate_structure.py` - Validate Structure

### Future Phases (if needed)
- `flow_<new_phase>.py` - Follow same pattern

---

## 🔧 Framework Support

### Supported Frameworks
- ✅ Spring Boot (Java)
- ✅ Django (Python) 
- ✅ Node.js/Express
- ✅ Rails (Ruby)
- ✅ Laravel (PHP)
- ✅ Go
- ✅ ASP.NET (C#)
- ✅ Next.js (JavaScript/TypeScript)

### Framework Detection
Auto-detected from:
- `pom.xml` → Spring Boot
- `package.json` → Node.js/Next.js
- `requirements.txt` → Django/Python
- `Gemfile` → Rails
- `composer.json` → Laravel
- `go.mod` → Go
- `.csproj` → ASP.NET

---

## 📝 Adding New Phases

To add a new workflow phase:

1. Create file: `flow_<phase_name>.py`
2. Implement phase function in `feature_by_request_agent_v3.py`
3. Add node: `workflow.add_node("<phase_name>", <function>)`
4. Add edge: Connect to previous phase
5. Update README.md with new phase

---

## 🐛 Debugging Tips

### Enable Verbose Logging
```python
# In feature_by_request_agent_v3.py
print("🔍 [DEBUG]", variable_name)
```

### Check State at Each Phase
```python
# Print state after each phase
print(f"Current phase: {state['current_phase']}")
print(f"Errors: {state['errors']}")
```

### Test Individual Phases
```python
# Create test state
test_state = {
    "codebase_path": "...",
    "feature_request": "...",
    # ... other fields
}

# Call phase directly
result = flow_analyze_context.analyze_with_reasoning(test_state)
```

---

## 📚 Related Documentation

- `codeanalysis.flow-naming-convention.md` - Naming details
- `codeanalysis.phase2-completion-summary.md` - Phase details
- `codeanalysis.validate-structure-enhanced-completion.md` - Validation details
- `README.md` in coding_agent folder - Full documentation

---

## ✨ Version Info

- **Agent Version:** V3 (LangGraph-based)
- **Phases:** 6 (including Phase 2A)
- **Last Refactor:** November 11, 2025
- **Naming Convention:** flow_ prefix for phase implementations
- **Status:** Production-ready

---

**For more details, see README.md in scripts/coding_agent/ folder.**
