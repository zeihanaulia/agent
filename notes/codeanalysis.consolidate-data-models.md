# Improvement Guide: Consolidate Data Models

**Status:** Proposal for Implementation  
**Priority:** HIGH (Critical for maintainability)  
**Effort Estimate:** 3-4 hours  
**Impact:** Reduces complexity, clarifies architecture, improves maintainability  

---

## 🎯 Problem Statement

Current implementation has **3 separate data structures** with overlapping information:

```
FeatureSpec (in feature_by_request_agent_v3.py)
    ├─ feature_name
    ├─ intent_summary
    ├─ affected_files
    ├─ new_files
    ├─ modifications
    ├─ notes
    ├─ todo_list ← SHOULDN'T BE HERE
    └─ new_files_planning ← SHOULDN'T BE HERE

TodoList (in flow_parse_intent.py)
    ├─ feature_name ← DUPLICATE
    ├─ feature_request ← DUPLICATE (same as intent_summary)
    ├─ framework ← BELONGS IN FeatureSpec
    ├─ total_tasks
    ├─ todos
    └─ created_at

NewFilesPlanningSuggestion (in flow_parse_intent.py)
    ├─ suggested_files
    ├─ directory_structure
    ├─ best_practices
    ├─ framework_conventions
    └─ creation_order
```

**Problems:**
- Data scattered across 3 models
- Confusing what is "source of truth"
- Nested structures are hard to work with
- Difficult to serialize/deserialize
- Inconsistent naming (feature_name vs feature_request)
- TodoList shouldn't be nested in FeatureSpec

---

## ✅ Proposed Solution

### Create Single Source of Truth: `ImplementationPlan`

```python
# Location: scripts/coding_agent/flow_parse_intent.py

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class FilePlacementSuggestion(BaseModel):
    """Suggestion for a new file to be created"""
    file_type: str = Field(description="Type of file: entity, service, repository, controller, dto, config, test")
    relative_path: str = Field(description="Relative path in project: src/main/java/com/app/service")
    filename: str = Field(description="Filename with extension: ProductService.java")
    purpose: str = Field(description="Purpose of this file")
    solid_principles: List[str] = Field(default_factory=list, description="SOLID principles applied: SRP, OCP, DIP")
    example_class_name: str = Field(description="Example class name for this file")
    layer: str = Field(description="Architectural layer: controller, service, model, repository, dto")


class TodoItem(BaseModel):
    """Individual todo item for tracking"""
    id: int = Field(description="Todo item ID")
    title: str = Field(description="Short title of the task")
    description: str = Field(description="Detailed description")
    phase: str = Field(description="Phase: analysis, planning, validation, generation, execution, testing, review")
    status: str = Field(default="pending", description="pending, in-progress, completed, blocked")
    priority: str = Field(default="medium", description="high, medium, low")
    depends_on: List[int] = Field(default_factory=list, description="IDs of tasks this depends on")
    files_affected: List[str] = Field(default_factory=list, description="Files involved in this task")
    estimated_effort: str = Field(default="medium", description="small, medium, large")
    notes: str = Field(default="")


class ImplementationPlan(BaseModel):
    """
    UNIFIED MODEL: Single source of truth for feature implementation planning.
    
    Contains:
    - Feature metadata
    - File structure and organization
    - Implementation tasks and tracking
    - Architecture guidelines
    - Framework conventions
    """
    
    # ========== FEATURE METADATA ==========
    feature_name: str = Field(description="Name of the feature (first 60 chars of request)")
    feature_request: str = Field(description="Full original feature request from user")
    framework: Optional[str] = Field(default=None, description="Detected framework (spring-boot, django, etc)")
    
    # ========== FILES & STRUCTURE ==========
    affected_files: List[str] = Field(
        default_factory=list,
        description="Existing files that will be modified"
    )
    
    new_files: List[FilePlacementSuggestion] = Field(
        default_factory=list,
        description="New files to create with full metadata"
    )
    
    directory_structure: Dict[str, str] = Field(
        default_factory=dict,
        description="Directory structure needed: path -> purpose mapping"
    )
    
    creation_order: List[str] = Field(
        default_factory=list,
        description="Order to create files (dependency-aware)"
    )
    
    # ========== IMPLEMENTATION TASKS ==========
    todos: List[TodoItem] = Field(
        default_factory=list,
        description="All implementation tasks across all phases"
    )
    
    current_phase: str = Field(
        default="planning",
        description="Current phase: analysis, planning, validation, generation, execution, testing, review"
    )
    
    # ========== GUIDELINES & STANDARDS ==========
    best_practices: List[str] = Field(
        default_factory=list,
        description="Best practices for this feature and framework"
    )
    
    framework_conventions: List[str] = Field(
        default_factory=list,
        description="Framework-specific conventions and patterns"
    )
    
    solid_principles_mapping: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="SOLID principles per file: {filename -> [principles]}"
    )
    
    # ========== METADATA ==========
    timestamp_created: str = Field(description="ISO format timestamp when created")
    timestamp_updated: str = Field(description="ISO format timestamp when last updated")
    
    # ========== OPTIONAL FIELDS ==========
    modifications: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed modifications to existing files"
    )
    
    notes: str = Field(
        default="",
        description="Additional notes or observations"
    )
    
    # ========== STATISTICS ==========
    total_tasks: int = Field(default=0, description="Total number of todo items")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    in_progress_tasks: int = Field(default=0, description="Number of in-progress tasks")
    pending_tasks: int = Field(default=0, description="Number of pending tasks")


# Helper functions for the new model

def create_implementation_plan(
    feature_request: str,
    framework: Optional[str] = None,
    affected_files: Optional[List[str]] = None,
    new_files: Optional[List[FilePlacementSuggestion]] = None
) -> ImplementationPlan:
    """Create a new implementation plan"""
    
    now = datetime.now().isoformat()
    
    plan = ImplementationPlan(
        feature_name=feature_request[:60],
        feature_request=feature_request,
        framework=framework,
        affected_files=affected_files or [],
        new_files=new_files or [],
        timestamp_created=now,
        timestamp_updated=now
    )
    
    return plan


def update_todo_status(
    plan: ImplementationPlan,
    todo_id: int,
    new_status: str,
    notes: str = ""
) -> ImplementationPlan:
    """Update a todo item status and refresh statistics"""
    
    for todo in plan.todos:
        if todo.id == todo_id:
            todo.status = new_status
            if notes:
                todo.notes = notes
            break
    
    # Recalculate statistics
    completed = sum(1 for t in plan.todos if t.status == "completed")
    in_progress = sum(1 for t in plan.todos if t.status == "in-progress")
    pending = sum(1 for t in plan.todos if t.status == "pending")
    
    plan.completed_tasks = completed
    plan.in_progress_tasks = in_progress
    plan.pending_tasks = pending
    plan.total_tasks = len(plan.todos)
    plan.timestamp_updated = datetime.now().isoformat()
    
    return plan


def persist_implementation_plan(
    plan: ImplementationPlan,
    output_dir: str = "./outputs"
) -> str:
    """Save plan to JSON file for tracking and resumption"""
    import os
    import json
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename from feature name
    safe_name = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in plan.feature_name
    )
    safe_name = safe_name.replace("_", "-").lower()[:50]
    filename = f"plan-{safe_name}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON
    with open(filepath, 'w') as f:
        f.write(plan.model_dump_json(indent=2))
    
    return filepath


def load_implementation_plan(filepath: str) -> ImplementationPlan:
    """Load a previously saved plan from JSON file"""
    import json
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return ImplementationPlan(**data)
```

---

## 🔄 Migration Path

### Step 1: Update flow_parse_intent.py

**Before:**
```python
def flow_parse_intent(state: Dict[str, Any], ...) -> Dict[str, Any]:
    # Creates 3 separate structures
    spec = FeatureSpec(...)
    todo_list = generate_structured_todos(...)
    new_files_planning = infer_new_files_needed(...)
    
    spec.todo_list = todo_list
    spec.new_files_planning = new_files_planning
    
    state["feature_spec"] = spec
    return state
```

**After:**
```python
def flow_parse_intent(state: Dict[str, Any], ...) -> Dict[str, Any]:
    # Creates single unified structure
    plan = create_implementation_plan(
        feature_request=feature_request,
        framework=detected_framework,
        affected_files=affected_files
    )
    
    # Add files
    plan.new_files = new_files_suggestions.suggested_files
    plan.directory_structure = new_files_suggestions.directory_structure
    plan.creation_order = new_files_suggestions.creation_order
    plan.framework_conventions = new_files_suggestions.framework_conventions
    plan.best_practices = new_files_suggestions.best_practices
    
    # Add todos
    plan.todos = todos
    plan.total_tasks = len(todos)
    plan.completed_tasks = sum(1 for t in todos if t.status == "completed")
    plan.pending_tasks = sum(1 for t in todos if t.status == "pending")
    
    # Add SOLID mapping
    plan.solid_principles_mapping = {
        f.filename: f.solid_principles for f in plan.new_files
    }
    
    state["implementation_plan"] = plan
    return state
```

### Step 2: Update feature_by_request_agent_v3.py

**Before:**
```python
# In AgentState:
feature_spec: Optional[FeatureSpec]

# In parse_intent node:
state["feature_spec"] = spec

# In synthesize_code node:
feature_spec = state.get("feature_spec")
affected_files = feature_spec.affected_files
new_files = feature_spec.new_files
todo_list = feature_spec.todo_list
```

**After:**
```python
# In AgentState:
implementation_plan: Optional[ImplementationPlan]

# In parse_intent node:
state["implementation_plan"] = plan

# In synthesize_code node:
plan = state.get("implementation_plan")
affected_files = plan.affected_files
new_files = [f.filename for f in plan.new_files]
todos = plan.todos
framework_conventions = plan.framework_conventions
```

### Step 3: Update downstream phases

All phases (validate_structure, analyze_impact, synthesize_code, execute_changes) need to:
1. Read from `state["implementation_plan"]`
2. Update `plan.current_phase` as progress
3. Update `plan.todos` status as complete
4. Write back to `state["implementation_plan"]`

---

## 📝 Updated Workflow

```python
def parse_intent(state: AgentState) -> AgentState:
    # ... analysis code ...
    
    # Create implementation plan
    plan = create_implementation_plan(
        feature_request=feature_request,
        framework=framework,
        affected_files=affected_files
    )
    
    # Populate all fields from inference functions
    plan.new_files = [...]
    plan.directory_structure = {...}
    plan.todos = generate_structured_todos(...)
    plan.best_practices = [...]
    plan.framework_conventions = [...]
    
    state["implementation_plan"] = plan
    return state

def validate_structure(state: AgentState) -> AgentState:
    plan = state["implementation_plan"]
    
    # Use framework from plan
    assessment = validate_project_structure(
        codebase_path,
        framework=plan.framework
    )
    
    # Update plan with assessment
    plan.current_phase = "structure_validation_complete"
    
    state["implementation_plan"] = plan
    return state

def analyze_impact(state: AgentState) -> AgentState:
    plan = state["implementation_plan"]
    
    # Use all info from plan
    impact = analyze_architecture(
        affected_files=plan.affected_files,
        new_files=[f.filename for f in plan.new_files]
    )
    
    # Mark planning phase todos as complete
    for todo in plan.todos:
        if todo.phase == "planning":
            todo.status = "completed"
    
    plan.current_phase = "impact_analysis_complete"
    state["implementation_plan"] = plan
    return state

def synthesize_code(state: AgentState) -> AgentState:
    plan = state["implementation_plan"]
    
    # Generate code with all context
    patches = generate_code(
        feature_request=plan.feature_request,
        new_files=plan.new_files,
        conventions=plan.framework_conventions,
        best_practices=plan.best_practices
    )
    
    # Mark generation phase todos as in-progress
    for todo in plan.todos:
        if todo.phase == "generation":
            todo.status = "in-progress"
    
    plan.current_phase = "code_synthesis_complete"
    state["implementation_plan"] = plan
    state["code_patches"] = patches
    return state

def execute_changes(state: AgentState) -> AgentState:
    plan = state["implementation_plan"]
    
    # Execute patches
    results = execute_patches(state["code_patches"])
    
    # Mark execution phase todos as complete
    for todo in plan.todos:
        if todo.phase == "execution":
            todo.status = "completed"
    
    # Persist plan for tracking
    output_file = persist_implementation_plan(plan)
    print(f"Plan saved: {output_file}")
    
    plan.current_phase = "execution_complete"
    state["implementation_plan"] = plan
    return state
```

---

## 🎯 Benefits

### Before (3 Models)
```
❌ Data scattered
❌ Confusing what is source of truth
❌ Nested structures hard to serialize
❌ Different naming conventions
❌ Difficult to track progress
❌ Can't easily persist and resume
```

### After (1 Model)
```
✅ Single source of truth
✅ Clear field relationships
✅ Easy to serialize to JSON
✅ Consistent naming
✅ Progress tracking built-in
✅ Can persist and resume workflows
✅ Simpler downstream code
✅ Easier testing
✅ Better documentation
```

---

## 🚀 Implementation Checklist

- [ ] Create `ImplementationPlan` class in `flow_parse_intent.py`
- [ ] Create helper functions (create, update, persist, load)
- [ ] Update `flow_parse_intent()` to return `ImplementationPlan`
- [ ] Update `AgentState` to use `implementation_plan`
- [ ] Update `parse_intent()` node
- [ ] Update `validate_structure()` node
- [ ] Update `analyze_impact()` node
- [ ] Update `synthesize_code()` node
- [ ] Update `execute_changes()` node
- [ ] Update `handle_error()` node
- [ ] Remove old `FeatureSpec` references from feature_by_request_agent_v3.py
- [ ] Update all tests
- [ ] Test end-to-end workflow
- [ ] Verify data integrity during persistence/loading

---

## ⏱️ Estimated Timeline

- Phase 1: Model definition (30 min)
- Phase 2: Update flow_parse_intent (45 min)
- Phase 3: Update feature_by_request_agent_v3.py (1.5 hours)
- Phase 4: Update all phases (1 hour)
- Phase 5: Testing and verification (45 min)

**Total:** ~4 hours

---

## 📝 Notes

1. Keep old structures as backwards-compatibility wrapper temporarily
2. Test each phase independently after update
3. Verify serialization/deserialization works
4. Test persistence and resumption
5. Update documentation
