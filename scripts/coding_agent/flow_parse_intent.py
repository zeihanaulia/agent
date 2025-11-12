"""
FLOW PARSE INTENT - Phase 2 Intent Parsing Module
===================================================

Refactored from feature_by_request_agent_v3.py
Handles feature request analysis and implementation planning
"""

import os
import re
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

# ==============================================================================
# DATA MODELS
# ==============================================================================

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


class TodoList(BaseModel):
    """Complete todo list for a feature"""
    feature_name: str = Field(description="Name of the feature")
    feature_request: str = Field(description="Original feature request")
    framework: Optional[str] = Field(default=None, description="Detected framework")
    total_tasks: int = Field(description="Total number of tasks")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    in_progress_tasks: int = Field(default=0, description="Number of in-progress tasks")
    pending_tasks: int = Field(default=0, description="Number of pending tasks")
    todos: List[TodoItem] = Field(default_factory=list, description="List of all todo items")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class FilePlacementSuggestion(BaseModel):
    """Suggestion for a new file to be created"""
    file_type: str = Field(description="Type of file: entity, service, repository, controller, dto, config, test")
    relative_path: str = Field(description="Relative path in project: src/main/java/com/app/service")
    filename: str = Field(description="Filename with extension: ProductService.java")
    purpose: str = Field(description="Purpose of this file")
    solid_principles: List[str] = Field(default_factory=list, description="SOLID principles applied: SRP, OCP, DIP")
    example_class_name: str = Field(description="Example class name for this file")
    layer: str = Field(description="Architectural layer: controller, service, model, repository, dto")


class NewFilesPlanningSuggestion(BaseModel):
    """Complete new files planning with architecture and best practices"""
    suggested_files: List[FilePlacementSuggestion] = Field(description="List of files to create")
    directory_structure: Dict[str, str] = Field(description="Directory structure needed")
    best_practices: List[str] = Field(description="Best practices for this feature")
    framework_conventions: List[str] = Field(description="Framework-specific conventions")
    creation_order: List[str] = Field(description="Order to create files (dependency-aware)")


class FeatureSpec(BaseModel):
    """Structured specification of a feature request"""
    feature_name: str = Field(description="Name of the feature")
    intent_summary: str = Field(description="Summary of user intent")
    affected_files: List[str] = Field(default_factory=list)
    new_files: List[str] = Field(default_factory=list)
    modifications: List[Dict[str, Any]] = Field(default_factory=list)
    notes: str = Field(default="")
    todo_list: Optional[TodoList] = Field(default=None, description="Structured todo list")
    new_files_planning: Optional[NewFilesPlanningSuggestion] = Field(default=None, description="Detailed new files planning")


class FlowParseIntentState(dict):
    """State for parse_intent phase"""
    codebase_path: str
    feature_request: str
    context_analysis: str
    framework: Optional[Any]
    feature_spec: Optional[FeatureSpec]
    errors: List[str]


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def extract_tasks_from_response(response_text: str) -> List[Dict[str, str]]:
    """
    Extract task/todo items from LLM response.
    
    Args:
        response_text: Raw text from LLM response
        
    Returns:
        List of task dictionaries with 'content' and 'status'
    """
    todos_found = []
    
    if not response_text:
        return todos_found
    
    content_str = str(response_text)
    
    # Extract tasks/todos from response (look for bullet points or numbered items)
    # Line pattern: "- Task description" or "  - Task description"
    task_pattern = r'^\s*[-*]\s+(.+?)$'
    for line in content_str.split('\n'):
        match = re.match(task_pattern, line, re.MULTILINE)
        if match:
            todos_found.append({
                "content": line.strip(),
                "status": "pending"
            })
    
    return todos_found


def extract_files_from_response(response_text: str, codebase_path: str) -> List[str]:
    """
    Extract file paths from LLM response and validate they exist.
    
    Args:
        response_text: Raw text from LLM response
        codebase_path: Root path of codebase
        
    Returns:
        List of valid file paths found in codebase
    """
    affected_files = []
    
    if not response_text:
        return affected_files
    
    content_str = str(response_text)
    
    # Find file paths - more comprehensive pattern
    file_matches = re.findall(
        r'(?:src/|\.?/)?[a-zA-Z0-9_\-./]*\.(?:java|py|js|go|ts|tsx|jsx|xml|gradle|properties|yml|yaml)',
        content_str
    )
    
    # Validate each file match exists in codebase
    for fm in file_matches:
        full_path = os.path.join(codebase_path, fm)
        if os.path.isfile(full_path):
            affected_files.append(fm)
    
    return affected_files


def scan_codebase_for_files(codebase_path: str) -> List[str]:
    """
    Scan codebase for source files when LLM doesn't detect them.
    Prioritizes Java files for Spring Boot projects.
    
    Args:
        codebase_path: Root path of codebase
        
    Returns:
        List of source files found
    """
    source_files = []
    
    # Try Java files first (Spring Boot pattern)
    java_src_path = os.path.join(codebase_path, "src/main/java")
    if os.path.isdir(java_src_path):
        for root, dirs, files in os.walk(java_src_path):
            for file in files:
                if file.endswith(".java"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, codebase_path)
                    source_files.append(rel_path)
    
    # Try Python files
    if not source_files:
        for root, dirs, files in os.walk(codebase_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules']]
            
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, codebase_path)
                    source_files.append(rel_path)
    
    return source_files


def write_todo_file(
    todo_list: TodoList,
    output_dir: str = "./outputs"
) -> str:
    """
    Write TodoList to a markdown file for user tracking.
    
    Args:
        todo_list: TodoList instance to write
        output_dir: Directory to write todo file
        
    Returns:
        Path to written file
    """
    import os
    from datetime import datetime
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename from feature name
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in todo_list.feature_name)
    safe_name = safe_name.replace("_", "-").lower()[:50]
    filename = f"todo-{safe_name}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Build markdown content
    content = f"""# TODO List: {todo_list.feature_name}

**Feature Request:** {todo_list.feature_request}  
**Framework:** {todo_list.framework or 'Generic'}  
**Created:** {todo_list.created_at}  
**Last Updated:** {todo_list.updated_at}

---

## 📊 Progress Summary

| Status | Count | % |
|--------|-------|---|
| ✅ Completed | {todo_list.completed_tasks} | {int(todo_list.completed_tasks / todo_list.total_tasks * 100) if todo_list.total_tasks > 0 else 0}% |
| ⏳ In Progress | {todo_list.in_progress_tasks} | {int(todo_list.in_progress_tasks / todo_list.total_tasks * 100) if todo_list.total_tasks > 0 else 0}% |
| ⏸️ Pending | {todo_list.pending_tasks} | {int(todo_list.pending_tasks / todo_list.total_tasks * 100) if todo_list.total_tasks > 0 else 0}% |
| **TOTAL** | **{todo_list.total_tasks}** | **100%** |

**Overall Progress:** {int(todo_list.completed_tasks / todo_list.total_tasks * 100) if todo_list.total_tasks > 0 else 0}%

---

## 📋 Detailed Todo List

"""
    
    # Group todos by phase
    phases = {}
    for todo in todo_list.todos:
        if todo.phase not in phases:
            phases[todo.phase] = []
        phases[todo.phase].append(todo)
    
    phase_order = ["analysis", "planning", "validation", "generation", "execution", "testing", "review"]
    phase_emojis = {
        "analysis": "🔍",
        "planning": "📐",
        "validation": "✓",
        "generation": "⚙️",
        "execution": "▶️",
        "testing": "🧪",
        "review": "👀"
    }
    
    for phase in phase_order:
        if phase in phases:
            emoji = phase_emojis.get(phase, "•")
            content += f"\n### {emoji} Phase: {phase.title()}\n\n"
            
            for todo in phases[phase]:
                # Status icon
                if todo.status == "completed":
                    status_icon = "✅"
                elif todo.status == "in-progress":
                    status_icon = "🔄"
                else:
                    status_icon = "⏸️"
                
                # Priority indicator
                priority_indicator = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(todo.priority, "•")
                
                # Build todo item
                content += f"#### {status_icon} [{todo.id:02d}] {todo.title}\n\n"
                content += f"**Status:** {todo.status} | **Priority:** {priority_indicator} {todo.priority} | **Effort:** {todo.estimated_effort}\n\n"
                content += f"**Description:** {todo.description}\n\n"
                
                if todo.depends_on:
                    deps = ", ".join(f"[#{dep:02d}]" for dep in todo.depends_on)
                    content += f"**Depends on:** {deps}\n\n"
                
                if todo.files_affected:
                    files = ", ".join(f"`{f}`" for f in todo.files_affected[:5])
                    if len(todo.files_affected) > 5:
                        files += f" + {len(todo.files_affected) - 5} more"
                    content += f"**Files Affected:** {files}\n\n"
                
                if todo.notes:
                    content += f"**Notes:** {todo.notes}\n\n"
                
                content += "---\n\n"
    
    # Add footer
    content += f"""
## 🎯 Quick Reference

### By Phase Completion
"""
    
    for phase in phase_order:
        if phase in phases:
            phase_todos = phases[phase]
            completed = sum(1 for t in phase_todos if t.status == "completed")
            total = len(phase_todos)
            percent = int(completed / total * 100) if total > 0 else 0
            bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
            content += f"- **{phase.title()}:** `{bar}` {completed}/{total} ({percent}%)\n"
    
    content += f"""

### By Priority
- **🔴 High Priority:** {sum(1 for t in todo_list.todos if t.priority == 'high')} items
- **🟡 Medium Priority:** {sum(1 for t in todo_list.todos if t.priority == 'medium')} items
- **🟢 Low Priority:** {sum(1 for t in todo_list.todos if t.priority == 'low')} items

### Blocking Tasks
"""
    
    # Find tasks with unmet dependencies
    blocking = []
    for t in todo_list.todos:
        if t.status != "completed" and t.depends_on:
            for dep_id in t.depends_on:
                dep_todo = next((dt for dt in todo_list.todos if dt.id == dep_id), None)
                if dep_todo and dep_todo.status != "completed":
                    blocking.append(t)
                    break
    
    if blocking:
        for todo in blocking:
            content += f"- [#{todo.id:02d}] {todo.title} (blocked by: {', '.join(f'[#{d:02d}]' for d in todo.depends_on)})\n"
    else:
        content += "- None (all dependencies satisfied)\n"
    
    content += f"""

---

**Generated by:** Feature-by-Request Agent V3  
**File:** {filepath}  
**How to use:** Update task statuses as work progresses. Run agent again to regenerate with updated progress.

"""
    
    # Write file
    with open(filepath, 'w') as f:
        f.write(content)
    
    return filepath


def build_intent_prompt(
    feature_request: str,
    context_analysis: str
) -> str:
    """
    Build the prompt for intent parsing analysis.
    
    Args:
        feature_request: User's feature request
        context_analysis: Previous phase's context analysis
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""
CODEBASE CONTEXT:
{context_analysis}

FEATURE REQUEST:
{feature_request}

As an expert software engineer, analyze this feature request:

1. **Understand the requirement**: What is being asked? What are the acceptance criteria?
2. **Assess impact**: Which architectural layers are affected? (UI, API, Business Logic, Data, etc)
3. **Design approach**: What design patterns would be appropriate? (MVC, Factory, Strategy, Decorator, etc)
4. **Testability**: How can this be tested effectively? (Unit tests, Integration tests, E2E tests)
5. **File analysis**: Which ACTUAL files need changes based on codebase patterns?

List implementation tasks in this format:
- Task 1: description
- Task 2: description
And list relevant files found in codebase.

Be specific about file paths and technical decisions.
"""
    return prompt


def create_feature_spec(
    feature_request: str,
    todos_found: List[Dict[str, str]],
    affected_files: List[str]
) -> FeatureSpec:
    """
    Create a FeatureSpec from analysis results.
    
    Args:
        feature_request: Original feature request
        todos_found: List of tasks identified
        affected_files: List of affected files
        
    Returns:
        FeatureSpec instance
    """
    spec = FeatureSpec(
        feature_name=feature_request[:60],
        intent_summary=feature_request,
        affected_files=affected_files if affected_files else ["TBD - to be determined by impact analysis"],
        new_files=[],
        modifications=[
            {
                "description": f"{t.get('content', 'Task')}",
                "type": t.get('status', 'pending')
            }
            for t in todos_found
        ] if todos_found else []
    )
    return spec


def generate_structured_todos(
    feature_request: str,
    framework: Optional[str] = None,
    affected_files: Optional[List[str]] = None,
    new_files: Optional[List[str]] = None
) -> TodoList:
    """
    Generate a structured, trackable todo list from feature request.
    Creates todos for each phase: analysis, planning, validation, generation, execution, testing, review.
    
    Args:
        feature_request: The feature request text
        framework: Detected framework (Spring Boot, Django, etc)
        affected_files: Files that will be affected
        new_files: Files that will be created
        
    Returns:
        TodoList with structured todo items
    """
    from datetime import datetime
    
    todos = []
    todo_id = 1
    
    # Extract key entities and operations from feature request
    request_lower = feature_request.lower()
    
    # ===== PHASE 1: ANALYSIS =====
    todos.append(TodoItem(
        id=todo_id,
        title="Analyze existing codebase structure",
        description=f"Scan codebase for existing patterns, frameworks, and architecture",
        phase="analysis",
        status="completed",
        priority="high",
        depends_on=[],
        estimated_effort="medium"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title=f"Detect framework and patterns",
        description=f"Framework detected: {framework or 'Generic'}. Identify layering patterns and conventions",
        phase="analysis",
        status="completed",
        priority="high",
        depends_on=[todo_id - 1],
        estimated_effort="small"
    ))
    todo_id += 1
    
    # ===== PHASE 2: PLANNING =====
    todos.append(TodoItem(
        id=todo_id,
        title="Parse feature requirements",
        description=f"Analyze: {feature_request}",
        phase="planning",
        status="completed",
        priority="high",
        depends_on=[todo_id - 1],
        estimated_effort="medium"
    ))
    phase2_start = todo_id
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Identify new files needed",
        description=f"Plan creation of {len(new_files) if new_files else 'new'} files with SOLID principles",
        phase="planning",
        status="pending",
        priority="high",
        depends_on=[phase2_start],
        files_affected=new_files or [],
        estimated_effort="medium"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Map SOLID principles per file",
        description="Identify which SOLID principles apply to each file: SRP, OCP, LSP, ISP, DIP",
        phase="planning",
        status="pending",
        priority="high",
        depends_on=[todo_id - 1],
        files_affected=new_files or [],
        estimated_effort="medium"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Create implementation plan",
        description="Define step-by-step implementation strategy with dependency resolution",
        phase="planning",
        status="pending",
        priority="high",
        depends_on=[todo_id - 1],
        estimated_effort="medium"
    ))
    phase2_end = todo_id
    todo_id += 1
    
    # ===== PHASE 3: VALIDATION =====
    todos.append(TodoItem(
        id=todo_id,
        title="Validate project structure",
        description="Check if all required directories exist and follow conventions",
        phase="validation",
        status="pending",
        priority="high",
        depends_on=[phase2_end],
        estimated_effort="small"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Verify framework conventions",
        description="Ensure proposed changes follow framework best practices",
        phase="validation",
        status="pending",
        priority="high",
        depends_on=[todo_id - 1],
        estimated_effort="small"
    ))
    phase3_end = todo_id
    todo_id += 1
    
    # ===== PHASE 4: GENERATION =====
    if new_files:
        for new_file in new_files:
            file_name = new_file.split('/')[-1] if '/' in new_file else new_file
            todos.append(TodoItem(
                id=todo_id,
                title=f"Generate {file_name}",
                description=f"Create {file_name} with proper structure and SOLID principles applied",
                phase="generation",
                status="pending",
                priority="high",
                depends_on=[phase3_end],
                files_affected=[new_file],
                estimated_effort="medium"
            ))
            todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Generate unit tests",
        description="Create comprehensive unit tests for new functionality",
        phase="generation",
        status="pending",
        priority="high",
        depends_on=[todo_id - 1] if new_files else [phase3_end],
        estimated_effort="large"
    ))
    phase4_end = todo_id
    todo_id += 1
    
    # ===== PHASE 5: EXECUTION =====
    todos.append(TodoItem(
        id=todo_id,
        title="Write generated files to file system",
        description=f"Write {len(new_files) if new_files else 'new'} files to correct locations",
        phase="execution",
        status="pending",
        priority="high",
        depends_on=[phase4_end],
        files_affected=new_files or [],
        estimated_effort="small"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Update existing files",
        description=f"Modify {len(affected_files) if affected_files else '0'} affected files with new logic",
        phase="execution",
        status="pending",
        priority="high",
        depends_on=[todo_id - 1],
        files_affected=affected_files or [],
        estimated_effort="medium"
    ))
    phase5_end = todo_id
    todo_id += 1
    
    # ===== PHASE 6: TESTING =====
    todos.append(TodoItem(
        id=todo_id,
        title="Run unit tests",
        description="Execute all unit tests and verify they pass",
        phase="testing",
        status="pending",
        priority="high",
        depends_on=[phase5_end],
        estimated_effort="small"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Run integration tests",
        description="Execute integration tests to verify component interactions",
        phase="testing",
        status="pending",
        priority="high",
        depends_on=[todo_id - 1],
        estimated_effort="small"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Verify compilation",
        description="Ensure all files compile without errors or warnings",
        phase="testing",
        status="pending",
        priority="high",
        depends_on=[todo_id - 1],
        estimated_effort="small"
    ))
    phase6_end = todo_id
    todo_id += 1
    
    # ===== PHASE 7: REVIEW =====
    todos.append(TodoItem(
        id=todo_id,
        title="Code review and SOLID verification",
        description="Verify all SOLID principles are applied correctly",
        phase="review",
        status="pending",
        priority="high",
        depends_on=[phase6_end],
        estimated_effort="medium"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Final documentation and sign-off",
        description="Complete documentation and mark feature ready for deployment",
        phase="review",
        status="pending",
        priority="high",
        depends_on=[todo_id - 1],
        estimated_effort="small"
    ))
    
    # Count statuses
    completed = sum(1 for t in todos if t.status == "completed")
    in_progress = sum(1 for t in todos if t.status == "in-progress")
    pending = sum(1 for t in todos if t.status == "pending")
    
    now = datetime.now().isoformat()
    
    todo_list = TodoList(
        feature_name=feature_request[:60],
        feature_request=feature_request,
        framework=framework,
        total_tasks=len(todos),
        completed_tasks=completed,
        in_progress_tasks=in_progress,
        pending_tasks=pending,
        todos=todos,
        created_at=now,
        updated_at=now
    )
    
    return todo_list


def infer_new_files_needed(
    feature_request: str,
    context_analysis: str,
    framework: Optional[str] = None,
    affected_files: Optional[List[str]] = None
) -> NewFilesPlanningSuggestion:
    """
    Infer what new files need to be created for a feature based on the request and framework.
    Includes SOLID principles mapping and best practices.
    
    Args:
        feature_request: The feature request text
        context_analysis: Context analysis from Phase 1
        framework: Detected framework (e.g., "FrameworkType.SPRING_BOOT")
        affected_files: Files that will be affected
        
    Returns:
        NewFilesPlanningSuggestion with detailed file planning
    """
    request_lower = feature_request.lower()
    
    # Detect framework from context or parameter
    framework_str = str(framework).lower() if framework else "generic"
    is_spring_boot = "spring_boot" in framework_str or "spring boot" in context_analysis.lower()
    is_django = "django" in framework_str or "django" in context_analysis.lower()
    is_nodejs = "node" in framework_str or "express" in framework_str or ("node" in context_analysis.lower())
    
    # Feature analysis
    has_entity = any(word in request_lower for word in ["product", "user", "order", "item", "entity", "model", "entity", "class", "object"])
    has_api = any(word in request_lower for word in ["endpoint", "api", "rest", "http", "post", "get", "put", "delete", "crud"])
    has_service = any(word in request_lower for word in ["service", "business", "logic", "operation", "processing"])
    has_dto = any(word in request_lower for word in ["request", "response", "dto", "transfer", "json", "serialize"])
    has_config = any(word in request_lower for word in ["config", "setting", "configure", "setup", "initialization"])
    has_test = any(word in request_lower for word in ["test", "testing", "unittest", "integration"])
    
    suggested_files = []
    directory_structure = {}
    creation_order = []
    best_practices = []
    framework_conventions = []
    
    # ============ SPRING BOOT ============
    if is_spring_boot:
        base_path = "src/main/java/com/example/springboot"
        
        # Entity/Model
        if has_entity:
            suggested_files.append(FilePlacementSuggestion(
                file_type="entity",
                relative_path=f"{base_path}/model",
                filename="ProductEntity.java",
                purpose="JPA entity representing domain model",
                solid_principles=["SRP", "OCP"],
                example_class_name="Product",
                layer="model"
            ))
            directory_structure[f"{base_path}/model"] = "Domain models and entities"
            creation_order.append("ProductEntity.java")
        
        # DTO
        if has_dto:
            suggested_files.append(FilePlacementSuggestion(
                file_type="dto",
                relative_path=f"{base_path}/dto",
                filename="ProductDTO.java",
                purpose="Data transfer objects for API contracts",
                solid_principles=["SRP"],
                example_class_name="ProductRequest, ProductResponse",
                layer="dto"
            ))
            directory_structure[f"{base_path}/dto"] = "Data transfer objects"
            creation_order.append("ProductDTO.java")
        
        # Repository
        if has_entity:
            suggested_files.append(FilePlacementSuggestion(
                file_type="repository",
                relative_path=f"{base_path}/repository",
                filename="ProductRepository.java",
                purpose="Spring Data JPA repository for data persistence",
                solid_principles=["SRP", "DIP"],
                example_class_name="ProductRepository",
                layer="repository"
            ))
            directory_structure[f"{base_path}/repository"] = "Data access layer"
            creation_order.append("ProductRepository.java")
        
        # Service
        if has_service or has_api:
            suggested_files.append(FilePlacementSuggestion(
                file_type="service",
                relative_path=f"{base_path}/service",
                filename="ProductService.java",
                purpose="Business logic and service interface",
                solid_principles=["SRP", "OCP", "DIP"],
                example_class_name="ProductService, ProductServiceImpl",
                layer="service"
            ))
            directory_structure[f"{base_path}/service"] = "Business logic layer"
            creation_order.append("ProductService.java")
            creation_order.append("ProductServiceImpl.java")
        
        # Controller
        if has_api:
            suggested_files.append(FilePlacementSuggestion(
                file_type="controller",
                relative_path=f"{base_path}/controller",
                filename="ProductController.java",
                purpose="REST API endpoints",
                solid_principles=["SRP", "DIP"],
                example_class_name="ProductController",
                layer="controller"
            ))
            directory_structure[f"{base_path}/controller"] = "REST API endpoints"
            creation_order.append("ProductController.java")
        
        # Exception handling
        suggested_files.append(FilePlacementSuggestion(
            file_type="exception",
            relative_path=f"{base_path}/exception",
            filename="ProductNotFoundException.java",
            purpose="Custom exception handling",
            solid_principles=["SRP"],
            example_class_name="ProductNotFoundException",
            layer="exception"
        ))
        directory_structure[f"{base_path}/exception"] = "Exception classes"
        creation_order.append("ProductNotFoundException.java")
        
        # Tests
        if has_test:
            suggested_files.append(FilePlacementSuggestion(
                file_type="test",
                relative_path="src/test/java/com/example/springboot",
                filename="ProductServiceTest.java",
                purpose="Unit tests for services",
                solid_principles=["SRP"],
                example_class_name="ProductServiceTest",
                layer="test"
            ))
            directory_structure["src/test/java/com/example/springboot"] = "Unit tests"
        
        # Spring Boot specific conventions
        framework_conventions.extend([
            "Use @Entity, @Table for JPA entities",
            "Use @Repository for Spring Data repositories",
            "Use @Service for business logic beans",
            "Use @RestController for REST endpoints",
            "Use @Transactional for transaction management",
            "Use constructor-based dependency injection (@Autowired on constructor)",
            "Use @NotBlank, @NotNull, @Positive for validation",
            "Use Optional<T> for nullable returns",
            "Return ResponseEntity<T> from controller methods",
            "Use @ExceptionHandler for error handling",
            "Follow package naming: com.example.springboot.{layer}",
            "Use Lombok annotations (@Data, @Getter, @Setter, @NoArgsConstructor)",
            "Apply @JsonProperty for JSON serialization control"
        ])
        
        best_practices.extend([
            "Separate concerns: Entity models should not contain business logic",
            "Use DTOs to decouple API contracts from entity models",
            "Implement Repository pattern for data access abstraction",
            "Use Service layer for business logic orchestration",
            "Apply SRP: Each class has single responsibility",
            "Apply OCP: Open for extension, closed for modification",
            "Apply DIP: Depend on abstractions (interfaces), not concrete implementations",
            "Inject dependencies via constructor (not field injection)",
            "Use proper HTTP status codes: 200 OK, 201 Created, 204 No Content, 400 Bad Request, 404 Not Found, 500 Server Error",
            "Validate input at API boundary",
            "Add proper logging and exception handling",
            "Write meaningful test cases",
            "Document API with OpenAPI/Swagger",
            "Consider pagination for list endpoints"
        ])
    
    # ============ DJANGO ============
    elif is_django:
        # Similar logic for Django (Models, Views, Serializers, URLconf)
        framework_conventions.extend([
            "Use Django ORM for database models",
            "Use Django REST Framework for serializers",
            "Use ViewSets or APIViews for endpoints",
            "Use proper HTTP status codes via rest_framework.status"
        ])
    
    # ============ NODE.JS / EXPRESS ============
    elif is_nodejs:
        # Similar logic for Node.js
        framework_conventions.extend([
            "Use async/await for asynchronous operations",
            "Use middleware for cross-cutting concerns",
            "Use proper HTTP status codes",
            "Use Express routing for endpoints"
        ])
    
    # Common best practices
    if not best_practices:
        best_practices.extend([
            "Separate concerns: Models, Views/Controllers, Services",
            "Apply SOLID principles throughout",
            "Write unit tests for each component",
            "Use dependency injection",
            "Handle errors gracefully",
            "Validate input early",
            "Use meaningful names and documentation",
            "Keep functions small and focused"
        ])
    
    return NewFilesPlanningSuggestion(
        suggested_files=suggested_files,
        directory_structure=directory_structure,
        best_practices=best_practices,
        framework_conventions=framework_conventions,
        creation_order=creation_order
    )


# ==============================================================================
# MAIN FLOW_PARSE_INTENT FUNCTION
# ==============================================================================

def flow_parse_intent(
    state: Dict[str, Any],
    analysis_model: Any = None,
    framework_detector: Any = None
) -> Dict[str, Any]:
    """
    Phase 2: Parse Intent - Analyze feature request and create implementation plan.
    
    Args:
        state: Current workflow state
        analysis_model: LLM model instance for analysis
        framework_detector: Function to detect project framework
        
    Returns:
        Updated state with feature_spec and current_phase
    """
    print("🎯 Phase 2: Expert analysis - creating implementation plan...")
    
    feature_request = state.get("feature_request")
    codebase_path = state.get("codebase_path")
    context_analysis = state.get("context_analysis", "")
    
    # Validation
    if not feature_request:
        state["errors"].append("No feature request provided")
        return state
    
    if not codebase_path:
        state["errors"].append("No codebase path provided")
        return state
    
    # Detect framework early - helps with intent parsing
    detected_framework = None
    if framework_detector:
        try:
            detected_framework = framework_detector(codebase_path)
            if detected_framework:
                print(f"  🔍 Framework detected: {detected_framework}")
            else:
                print("  ℹ️  No specific framework detected, using generic patterns")
        except Exception as e:
            print(f"  ⚠️  Framework detection failed: {e}")
    
    state["framework"] = detected_framework
    
    # Build analysis prompt
    prompt = build_intent_prompt(feature_request, context_analysis)
    
    # Extract todos and analysis from response
    todos_found = []
    affected_files = []
    response_text = ""
    
    # Call LLM for analysis
    if analysis_model:
        try:
            # Direct LLM call - faster and won't hang
            response = analysis_model.invoke([HumanMessage(content=prompt)])
            response_text = response.content if hasattr(response, 'content') else str(response)
            print("  ✓ LLM analysis complete")
        except Exception as e:
            print(f"  ⚠️  LLM call failed: {e} - using filesystem-based analysis only")
            response_text = ""
    else:
        print("  ⚠️  Model not configured - using filesystem-based analysis only")
        response_text = ""
    
    # Extract tasks from response
    if response_text:
        todos_found = extract_tasks_from_response(response_text)
        affected_files = extract_files_from_response(response_text, codebase_path)
    
    # Remove duplicates while preserving order
    affected_files = list(dict.fromkeys(affected_files))
    
    # If no valid files detected from model output, scan filesystem
    if not affected_files:
        affected_files = scan_codebase_for_files(codebase_path)
    
    # Create FeatureSpec with analysis results
    spec = create_feature_spec(feature_request, todos_found, affected_files)
    
    # Generate new files planning with SOLID principles and best practices
    try:
        new_files_planning = infer_new_files_needed(
            feature_request=feature_request,
            context_analysis=context_analysis,
            framework=detected_framework,
            affected_files=affected_files
        )
        spec.new_files_planning = new_files_planning
        spec.new_files = [f.filename for f in new_files_planning.suggested_files]
        
        print(f"  📄 New files planned: {len(spec.new_files)} files")
        for nf in spec.new_files:
            print(f"     - {nf}")
    except Exception as e:
        print(f"  ⚠️  Failed to generate new files planning: {e}")
        spec.new_files_planning = None
    
    # Generate structured todo list for user tracking
    todo_list = generate_structured_todos(
        feature_request=feature_request,
        framework=detected_framework,
        affected_files=affected_files,
        new_files=spec.new_files
    )
    spec.todo_list = todo_list
    
    # Write todo file to outputs directory
    try:
        # Get outputs directory - use codebase_path/outputs or ./outputs
        outputs_dir = os.path.join(codebase_path, "outputs")
        if not os.path.isdir(outputs_dir):
            outputs_dir = "./outputs"
        
        todo_filepath = write_todo_file(todo_list, outputs_dir)
        print(f"  ✓ Todo list written to: {todo_filepath}")
    except Exception as e:
        print(f"  ⚠️  Failed to write todo file: {e}")
    
    state["feature_spec"] = spec
    state["current_phase"] = "flow_parse_intent_complete"
    
    # Summary output
    print(f"  ✓ Feature: {spec.feature_name[:50]}...")
    print(f"  ✓ Analysis steps: {len(todos_found)} tasks identified")
    print(f"  ✓ Affected files: {len(affected_files)} file(s)")
    print(f"  ✓ Todo items: {todo_list.total_tasks} items ({todo_list.completed_tasks} completed, {todo_list.pending_tasks} pending)")
    
    return state


# ==============================================================================
# ALTERNATIVE: INTENT PARSER AGENT (DeepAgent version)
# ==============================================================================

def create_intent_parser_agent(analysis_model: Any):
    """
    Create a DeepAgent for intent parsing (alternative to direct LLM).
    Uses write_todos tool for structured task planning.
    
    Args:
        analysis_model: LLM model instance
        
    Returns:
        DeepAgent instance
    """
    if not analysis_model:
        raise ValueError("Analysis model not provided")
    
    prompt = """\
You are an expert software engineer analyzing feature requests.

Your task: Create detailed implementation plans using write_todos tool.

SCOPE CONSTRAINT - CRITICAL:
Only implement EXACTLY what the user asks for. Do NOT add features beyond the request:
- If user asks for "Add Product entity", implement ONLY the Product entity
- If user asks for "Product management features", implement ONLY Product CRUD and basic queries
- DO NOT add Payment processing, Shipping, Authentication, or other unrelated features
- DO NOT suggest features not explicitly requested
- Focus on the single feature the user asked for

For each feature request:
1. Break down the feature into concrete implementation steps (SCOPE-LIMITED)
2. Identify which files need changes based on codebase structure
3. Consider design patterns that would be appropriate
4. Plan for testability from the start
5. Identify dependencies and potential impacts

Use write_todos to create a structured task list with:
- Analysis tasks (understand current code, patterns, architecture)
- Design tasks (select patterns, plan changes)
- Implementation tasks (create/modify files)
- Testing tasks (create/update tests)
- Verification tasks (ensure compilation, functionality)

Be thorough, thoughtful, and follow SOLID principles and clean code practices.
ALWAYS STAY WITHIN SCOPE - No feature creep or hallucinations.
"""
    
    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model
    )
