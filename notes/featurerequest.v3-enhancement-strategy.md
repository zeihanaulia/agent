# V3 Agent Enhancement Strategy
## Making Agent "Project Structure Aware" and "Production-Ready"

**Goal**: V3 agent should NOT just add features to existing structure, but:
- ✅ Analyze if project structure follows best practices
- ✅ Propose refactoring if needed
- ✅ Generate/refactor code to production-ready standards
- ✅ Handle directory creation and project restructuring

**Status**: STRATEGY DOCUMENT (Implementation Plan)

---

## Current Problem

### Current Flow
```
Feature Request 
    ↓
Analyze context (reads existing files)
    ↓
Parse intent (creates plan)
    ↓
Impact analysis (finds files to modify)
    ↓
Synthesize code (generates code for those files)
    ↓
Execute (applies changes)
```

### Issue: No Structure Validation
- Agent analyzes existing structure but doesn't assess quality
- Agent adds feature to existing structure (good or bad)
- If structure is non-standard, agent perpetuates it
- No refactoring proposals
- Generates code matching existing bad patterns

### Example: springboot-demo
```
Current (WRONG):
  HelloController.java (120 lines with everything)
  ↓
  Add feature
  ↓
  HelloController.java (200 lines with MORE everything)
  
Expected (CORRECT):
  HelloController.java (only HTTP handlers)
  OrderService.java (business logic)
  OrderRepository.java (data access)
  OrderDTO.java (API contracts)
  Order.java (domain model)
```

---

## Solution: Three New Phases

### New Architecture
```
Feature Request
    ↓
Phase 1: Analyze context
    ↓
Phase 2A: STRUCTURE VALIDATION (NEW)
         ├─ Check if production-ready
         ├─ Identify violations
         ├─ Assess current architecture
         └─ Generate improvement plan
    ↓
Phase 2B: Parse intent (WITH STRUCTURE AWARENESS)
         ├─ Understand feature
         ├─ Plan WITH best practices in mind
         └─ Include refactoring if needed
    ↓
Phase 3: Impact analysis
    ↓
Phase 4: ENHANCED Synthesize code
         ├─ Create missing directories
         ├─ Refactor existing files (if needed)
         ├─ Generate new files with best practices
         └─ Update dependencies/config (if needed)
    ↓
Phase 5: Execute with structure preservation
```

---

## Implementation Details

### Phase 2A: Structure Validation Agent

#### What it does:
```python
def validate_project_structure(state: AgentState) -> AgentState:
    """NEW PHASE: Validate project structure against best practices"""
    
    # 1. Check framework
    framework = state["framework"]  # Already detected in parse_intent
    
    # 2. Get best practices for this framework
    if framework:
        instructions = get_instruction(framework)
        expected_layers = instructions.get_layer_mapping()  # e.g., controller/, service/, repo/
        expected_patterns = instructions.get_file_patterns()  # e.g., OrderController.java
    
    # 3. Scan actual project
    actual_structure = scan_project_structure(codebase_path)
    
    # 4. Compare and identify violations
    violations = assess_structure_conformance(
        actual_structure,
        expected_layers,
        expected_patterns
    )
    
    # 5. Generate assessment
    assessment = {
        "is_production_ready": len(violations) == 0,
        "violations": violations,
        "refactoring_needed": determine_refactoring_strategy(violations),
        "effort_level": "low" | "medium" | "high"
    }
    
    state["structure_assessment"] = assessment
    return state
```

#### Output Example (for springboot-demo):
```json
{
  "is_production_ready": false,
  "violations": [
    {
      "type": "missing_layer",
      "layer": "service",
      "severity": "high",
      "message": "No service layer found. Business logic should be in Service classes."
    },
    {
      "type": "missing_layer",
      "layer": "repository",
      "severity": "high",
      "message": "No repository layer found. Data access should be in Repository classes."
    },
    {
      "type": "code_in_controller",
      "file": "HelloController.java",
      "severity": "high",
      "message": "Data storage (ConcurrentHashMap) should not be in Controller. Move to Repository."
    },
    {
      "type": "nested_model",
      "file": "HelloController.java",
      "class": "Order",
      "severity": "medium",
      "message": "Domain model (Order) should be in separate model/ package."
    }
  ],
  "refactoring_needed": {
    "create_layers": ["service", "repository", "dto", "model"],
    "extract_classes": ["Order from HelloController"],
    "move_code": ["Data storage from Controller to Repository"],
    "add_interfaces": ["OrderService, OrderRepository"]
  },
  "effort_level": "medium"
}
```

---

### Phase 2B: Enhanced Intent Parser

#### What it does:
```python
def parse_intent_with_structure_awareness(state: AgentState) -> AgentState:
    """ENHANCED: Include structure improvements in implementation plan"""
    
    # Original intent parsing
    spec = parse_original_intent(state)
    
    # NEW: Include refactoring in implementation plan
    assessment = state.get("structure_assessment")
    
    if assessment and not assessment["is_production_ready"]:
        refactoring = assessment["refactoring_needed"]
        
        # Add refactoring tasks to spec.modifications
        spec.modifications.extend([
            {
                "type": "create_directory",
                "path": f"src/main/java/com/example/springboot/{layer}",
                "reason": f"Best practice: {layer} layer required"
            }
            for layer in refactoring.get("create_layers", [])
        ])
        
        spec.modifications.extend([
            {
                "type": "extract_class",
                "from": extraction["from_file"],
                "class": extraction["class_name"],
                "to": f"src/main/java/com/example/springboot/model/{extraction['class_name']}.java",
                "reason": "Move domain model to separate file"
            }
            for extraction in refactoring.get("extract_classes", [])
        ])
    
    state["feature_spec"] = spec
    return state
```

---

### Phase 4: Enhanced Code Synthesis

#### What it does:
```python
def synthesize_code_with_refactoring(state: AgentState) -> AgentState:
    """ENHANCED: Generate code AND handle structural refactoring"""
    
    assessment = state.get("structure_assessment", {})
    spec = state.get("feature_spec")
    
    # STEP 1: Create missing directories
    if assessment.get("refactoring_needed"):
        refactoring = assessment["refactoring_needed"]
        for layer in refactoring.get("create_layers", []):
            create_directory(f"{codebase_path}/src/main/java/com/example/springboot/{layer}")
    
    # STEP 2: Extract existing classes (if needed)
    for extraction in refactoring.get("extract_classes", []):
        agent_extract_class_from_file(
            from_file=extraction["from_file"],
            class_name=extraction["class_name"],
            to_file=extraction["to_file"]
        )
    
    # STEP 3: Generate new feature following best practices
    agent = create_code_synthesis_agent(...)
    
    prompt = f"""
{framework_prompt}

REFACTORING STATUS:
{assessment.get('violations', 'None')}

NEW DIRECTORIES CREATED:
{refactoring.get('create_layers', [])}

CLASSES EXTRACTED:
{refactoring.get('extract_classes', [])}

NOW implement the feature:
- Create files in appropriate layers (controller/, service/, repository/, dto/, model/)
- Use created directories
- Follow layer mapping and file patterns
- Ensure separation of concerns
- Use dependency injection between layers

Feature: {spec.intent_summary}
"""
    
    result = agent.invoke({"input": prompt})
    
    # Extract generated files
    # ... (existing code extraction logic)
    
    return state
```

---

## Key Components to Add

### 1. Structure Validator (New Module)
**File**: `scripts/structure_validator.py`

```python
def scan_project_structure(path: str) -> Dict[str, Any]:
    """Scan actual project structure"""
    # Returns: existing directories, files, classes, imports
    pass

def assess_structure_conformance(
    actual: Dict,
    expected_layers: Dict[str, str],
    expected_patterns: Dict[str, str]
) -> List[Dict]:
    """Compare actual vs expected, return violations"""
    # Returns: list of violations with severity
    pass

def determine_refactoring_strategy(
    violations: List[Dict]
) -> Dict[str, Any]:
    """Given violations, create refactoring plan"""
    # Returns: what to create, extract, move, add
    pass
```

### 2. Class Extractor (New Tool)
**Functionality**: Extract nested/misplaced classes from existing files

```python
def extract_class_to_file(
    source_file: str,
    class_name: str,
    target_directory: str
) -> str:
    """
    Extract class from source_file to separate file in target_directory
    Handle imports, dependencies, etc.
    """
    pass
```

### 3. Directory Creator
**Functionality**: Ensure layer directories exist

```python
def ensure_layer_directories(codebase_path: str, framework: str):
    """Create all required layer directories for framework"""
    pass
```

### 4. Enhanced LLM Prompts
**In synthesis agent**: Add special prompts for:
- Creating files in specific layers
- Following layer patterns
- Dependency injection between layers
- Avoiding code duplication

---

## LLM Prompt Enhancements

### Current Problem
```
STEP 2: IMPLEMENTATION

Modify HelloController.java to add the new endpoint
Follow existing endpoint patterns
```

**Issue**: Tells agent to follow existing (bad) patterns!

### Solution
```
STEP 2: IMPLEMENTATION

IMPORTANT: Project structure has been analyzed and improved:
- ✅ Created directories: src/main/java/com/example/springboot/{service,repository,dto,model}
- ✅ Extracted Order class to src/main/java/com/example/springboot/model/Order.java
- ✅ Ready to implement with layered architecture

RULES FOR THIS IMPLEMENTATION:
1. HTTP handling ONLY in controller/:
   - Accept @PostMapping, @GetMapping parameters
   - Validate input
   - Call service layer
   - Return response

2. Business logic in service/:
   - @Service annotation
   - Inject repository via constructor
   - Implement business rules
   - Handle domain logic

3. Data access in repository/:
   - @Repository annotation
   - Extend JpaRepository
   - Custom queries if needed
   - Direct database interaction only

4. API contracts in dto/:
   - Plain classes (no logic)
   - Use @JsonProperty annotations
   - Separate from domain model

5. Domain model in model/:
   - @Entity annotation (if using JPA)
   - Pure domain logic only
   - No framework annotations

FEATURE REQUEST: {feature}

NOW implement using this layered structure:
- Create {LayerName}Controller.java
- Create {LayerName}Service.java
- Create {LayerName}Repository.java
- Create {LayerName}DTO.java
- Update {LayerName}.java domain model

Generate production-ready code.
```

---

## Integration Points with Existing Code

### In `parse_intent` node:
```python
# BEFORE: Just detect framework
detected_framework = detect_framework(codebase_path)
state["framework"] = detected_framework

# AFTER: Add structure validation
detected_framework = detect_framework(codebase_path)
state["framework"] = detected_framework

# NEW: Validate structure
assessment = validate_project_structure(codebase_path, detected_framework)
state["structure_assessment"] = assessment

if not assessment["is_production_ready"]:
    print(f"⚠️  Project structure needs improvement: {len(assessment['violations'])} violations found")
    print("    Will refactor during implementation...")
```

### In `synthesize_code` node:
```python
# BEFORE: Just generate code
result = agent.invoke({"input": analysis_prompt})
result2 = agent.invoke({"input": implementation_prompt})

# AFTER: Refactor first, then generate
assessment = state.get("structure_assessment", {})

if assessment.get("refactoring_needed"):
    # Create directories
    for layer in assessment["refactoring_needed"].get("create_layers", []):
        os.makedirs(f"{codebase_path}/src/main/java/com/example/springboot/{layer}", exist_ok=True)
    
    # Extract classes (agent-assisted)
    for extraction in assessment["refactoring_needed"].get("extract_classes", []):
        # Use agent to extract classes
        pass

# Then generate with awareness of new structure
result = agent.invoke({"input": enhanced_prompt_with_structure_info})
```

---

## Example: Before & After

### Scenario: User says "Add order management API"

#### BEFORE (Current V3)
```
1. Analyze: Found HelloController.java
2. Parse intent: Plan to add endpoints
3. Impact: Modify HelloController.java
4. Synthesize: Add methods to HelloController
5. Result: Everything still in HelloController (BAD)
```

#### AFTER (Enhanced V3)
```
1. Analyze: Found HelloController.java
2. VALIDATE STRUCTURE: ❌ Not production-ready
   - Missing: service, repository, dto, model layers
   - Issue: Data storage in controller
   - Issue: Domain model nested in controller
   - Violations: 7 total
3. Plan: 
   - Create: service/, repository/, dto/, model/ directories
   - Extract: Order class to model/Order.java
   - Refactor: Move data storage logic plan
4. Parse intent (with structure awareness):
   - Add to plan: directory creation, class extraction
   - Add to plan: service/repository/controller generation
5. Impact: Multiple files to create + one to modify
6. Synthesize: 
   - Create directories
   - Extract Order class
   - Generate OrderService.java (service layer)
   - Generate OrderRepository.java (repository layer)
   - Generate OrderDTO.java (dto layer)
   - Generate/refactor OrderController.java (controller layer)
   - Update Order.java in model layer
7. Result: Production-ready layered architecture! ✅
```

---

## Benefits

### ✅ For Users
- Features always added to proper structure
- Project automatically improves over time
- No need to manually refactor
- Can request any feature, always get best practice

### ✅ For Code Quality
- Enforces SOLID principles
- Ensures separation of concerns
- Enables testing at each layer
- Scalable from start

### ✅ For Development Speed
- Agent handles boilerplate
- Agent handles refactoring
- Just focus on features
- Consistent architecture

### ✅ For Frameworks
- Each framework can have its own best practices
- Spring Boot, Django, Rails, etc. all supported
- Custom layer mapping per framework
- Production-ready from day 1

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Create structure_validator.py module
- [ ] Implement scan_project_structure()
- [ ] Implement assess_structure_conformance()
- [ ] Add to parse_intent node

### Phase 2: Refactoring
- [ ] Implement determine_refactoring_strategy()
- [ ] Create directory creation logic
- [ ] Create class extraction logic
- [ ] Integrate into synthesize_code

### Phase 3: LLM Prompts
- [ ] Update synthesis prompts with layer awareness
- [ ] Add constraints for layer adherence
- [ ] Add examples of each layer
- [ ] Test with feature requests

### Phase 4: Testing
- [ ] Test on springboot-demo: "Add order management"
- [ ] Verify directory creation
- [ ] Verify file generation
- [ ] Verify layer separation
- [ ] Verify code compiles

### Phase 5: Documentation
- [ ] Document structure validation output
- [ ] Document refactoring decisions
- [ ] Create before/after examples
- [ ] Update user guide

---

## Critical Considerations

### 1. Risk: Agent might break existing code during refactoring
**Mitigation**:
- Use `--dry-run` by default
- Show refactoring plan before execution
- Let human approve major refactoring
- Keep backups

### 2. Risk: Extraction might lose context
**Mitigation**:
- Parse AST (Abstract Syntax Tree) carefully
- Handle imports and dependencies
- Test extracted code still compiles
- Verify no functionality lost

### 3. Risk: Feature might be complex and span multiple layers
**Mitigation**:
- LLM agent understands layer responsibilities
- Prompts guide proper distribution
- Validation ensures separation
- Tests verify end-to-end functionality

### 4. Risk: Over-engineering for simple features
**Mitigation**:
- Only refactor if needed (production-ready check)
- Scale effort to feature complexity
- Don't refactor if it causes excessive changes
- Option to disable auto-refactoring

---

## Decision Points

### Q: Should agent auto-refactor or ask permission?
**A**: Propose refactoring, show plan, let user confirm (default: dry-run)

### Q: Should all violations be fixed or just critical?
**A**: Fix all violations for consistency (can tune severity threshold)

### Q: What if refactoring breaks tests?
**A**: Show test failures, let user approve or fix first

### Q: Should this be per-framework or generic?
**A**: Per-framework (each framework has its own best practices)

### Q: Can user skip refactoring and keep existing structure?
**A**: Yes, with warning: "Adding to non-standard structure may reduce code quality"

---

## Summary

**Current Issue**: V3 agent adds features to existing (possibly bad) structure

**Solution**: Make V3 structure-aware:
1. Validate project structure
2. Propose refactoring if needed
3. Generate code with proper layering
4. Create missing directories
5. Extract misplaced classes
6. Ensure separation of concerns

**Result**: Production-ready code every time, like GitHub Copilot but for whole projects!

**Effort**: Medium-High (3-5 new modules, prompt enhancements, validation logic)

**Impact**: High (transforms V3 from "feature adder" to "architecture enforcer")
