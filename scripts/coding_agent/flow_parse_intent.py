"""
FLOW PARSE INTENT - Phase 2 Intent Parsing Module
===================================================

Refactored from feature_by_request_agent_v3.py
Handles feature request analysis and implementation planning
"""

import os
import re
import argparse
import json
from typing import Dict, List, Any, Optional
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


class ProjectSpec(BaseModel):
    """Complete project specification with guidelines and rules"""
    project_name: str = Field(description="Name of the project")
    purpose: str = Field(description="Purpose and description of the project")
    language: str = Field(description="Programming language (Java, Python, etc.)")
    framework: str = Field(description="Framework (Spring Boot, Django, etc.)")
    build_tool: str = Field(description="Build tool (Gradle, Maven, etc.)")
    packaging: str = Field(description="Packaging type (JAR, WAR, etc.)")
    modules: List[str] = Field(default_factory=list, description="Project modules/layers")
    code_style_rules: Dict[str, Any] = Field(default_factory=dict, description="Code style and naming conventions")
    architecture_notes: Dict[str, Any] = Field(default_factory=dict, description="Architecture patterns and layering")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Baseline and optional dependencies")
    testing_guidelines: Dict[str, Any] = Field(default_factory=dict, description="Testing requirements and frameworks")
    workflow_guidelines: List[str] = Field(default_factory=list, description="Development workflow rules")
    dont_do_list: List[str] = Field(default_factory=list, description="Things to avoid")
    folder_structure: Dict[str, str] = Field(default_factory=dict, description="Expected folder structure")
    quality_checklist: List[str] = Field(default_factory=list, description="Quality assurance checklist")
    build_deploy_instructions: Dict[str, Any] = Field(default_factory=dict, description="Build and deployment instructions")
    security_guidelines: List[str] = Field(default_factory=list, description="Security requirements")


class FlowParseIntentState(dict):
    """State for parse_intent phase"""
    codebase_path: str
    feature_request: str
    context_analysis: str
    framework: Optional[Any]
    feature_spec: Optional[FeatureSpec]
    project_spec: Optional[ProjectSpec]  # Add project specification
    errors: List[str]


def read_project_specification(codebase_path: str) -> Optional[ProjectSpec]:
    """
    Read and parse project specification files from the codebase.
    Looks for files like studio.md, project.md, README.md, or any .md file containing project specs.

    Args:
        codebase_path: Root path of the codebase

    Returns:
        ProjectSpec instance if found and parsed, None otherwise
    """
    import os

    # Priority order for spec files
    spec_files = [
        "studio.md",
        "project.md",
        "specs.md",
        "guidelines.md",
        "README.md"
    ]

    spec_file_path = None

    # Search paths in order of priority:
    # 1. Agent root directory (where studio.md is located)
    # 2. Scripts directory (where coding agent files are)
    # 3. Codebase directory (target project)
    search_paths = [
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # Agent root: /Users/zeihanaulia/Programming/research/agent
        os.path.dirname(os.path.dirname(__file__)),  # Scripts dir: /Users/zeihanaulia/Programming/research/agent/scripts
        codebase_path  # Target codebase
    ]

    # First check for exact matches in priority order across all search paths
    for search_path in search_paths:
        if not os.path.isdir(search_path):
            continue

        for spec_file in spec_files:
            potential_path = os.path.join(search_path, spec_file)
            if os.path.isfile(potential_path):
                spec_file_path = potential_path
                print(f"  📋 Found project spec: {os.path.relpath(potential_path, search_path)} in {os.path.basename(search_path)}")
                break

        if spec_file_path:
            break

    # If no exact match, look for any .md file that might contain project specs
    if not spec_file_path:
        for search_path in search_paths:
            if not os.path.isdir(search_path):
                continue

            for root, dirs, files in os.walk(search_path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules', 'target', '.idea', '.vscode', 'logs', 'outputs', 'notebooks', 'dataset', 'gradio']]

                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                                # Check if this looks like a project specification file
                                if _is_project_spec_file(content):
                                    spec_file_path = file_path
                                    print(f"  📋 Found project spec: {os.path.relpath(file_path, search_path)} in {os.path.basename(search_path)}")
                                    break
                        except Exception:
                            continue

                if spec_file_path:
                    break

            if spec_file_path:
                break

    if not spec_file_path:
        return None

    try:
        with open(spec_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return _parse_project_spec_content(content)

    except Exception as e:
        print(f"⚠️ Failed to read project specification from {spec_file_path}: {e}")
        return None


def _is_project_spec_file(content: str) -> bool:
    """
    Check if a markdown file contains project specifications.

    Args:
        content: File content to check

    Returns:
        True if it looks like a project specification file
    """
    content_lower = content.lower()

    # Look for indicators that this is a project specification file
    indicators = [
        "## 🧠 project overview",
        "## 🧩 code style rules",
        "## 🧭 architecture notes",
        "## 🧱 dependencies",
        "## 🧪 testing guidelines",
        "## 🧩 don't do this",
        "## ✅ quality checklist",
        "## 🚀 build & deploy",
        "## 🔒 security guidelines",
        "spring boot",
        "java 17",
        "gradle",
        "maven",
        "package structure",
        "naming conventions"
    ]

    return any(indicator in content_lower for indicator in indicators)


def _parse_project_spec_content(content: str) -> ProjectSpec:
    """
    Parse markdown content into a ProjectSpec object using intelligent agent-based parsing.
    
    This function uses DeepAgents middleware with LangGraph state management for
    comprehensive document analysis, replacing the previous manual regex approach.

    Args:
        content: Markdown content to parse

    Returns:
        ProjectSpec instance with extracted information
    """
    from typing import TypedDict, List, Dict, Any, Optional
    from pydantic import BaseModel, Field
    from langchain.agents import create_agent
    from langchain.tools import tool
    import json
    import logging

    logger = logging.getLogger(__name__)

    # ========================================================================
    # PLANNED FOR v3.1: LangGraph Multi-Agent Integration
    # ========================================================================
    # SpecParsingState is prepared for future multi-agent persona-based 
    # routing architecture (Engineering Manager → Specialist Agents pattern).
    # 
    # Currently UNUSED in v2.x (uses untyped Dict state), but will serve as
    # the state schema for parse_intent node in LangGraph workflow for v3.1.
    # 
    # See: notes/codeanalysis.specparsingstate-future-langgraph-integration.md
    # ========================================================================
    class SpecParsingState(TypedDict):
        """
        State schema for specification parsing phase in LangGraph agent workflow.
        
        Prepared for v3.1+ multi-agent architecture. Will be nested in
        MultiAgentState["engineering_state"] for supervisor pattern routing.
        
        Attributes:
            content: Raw specification markdown being parsed
            parsed_sections: Breakdown of spec sections by component
            project_spec: Processed project specification object
            analysis_context: Context from codebase analysis phase
        
        Current Usage (v2.x): None - using untyped Dict state instead
        Future Usage (v3.1+): LangGraph node state with type safety
        """
        content: str
        parsed_sections: Dict[str, str]
        project_spec: Optional[ProjectSpec]
        analysis_context: Dict[str, Any]

    # Structured Output Models (Pydantic)
    class ProjectOverview(BaseModel):
        """Project overview information"""
        project_name: str = Field(description="Name of the project", default="Unknown")
        purpose: str = Field(description="Project purpose and description", default="")
        language: str = Field(description="Primary programming language", default="Java")
        framework: str = Field(description="Main framework being used", default="Spring Boot")
        build_tool: str = Field(description="Build tool (Maven/Gradle)", default="Gradle")
        packaging: str = Field(description="Packaging type (JAR/WAR)", default="JAR")
        modules: List[str] = Field(description="Project modules", default_factory=list)

    class ArchitectureInfo(BaseModel):
        """Architecture and design information"""
        layering: str = Field(description="Layered architecture pattern", default="")
        dto_placement: str = Field(description="DTO placement strategy", default="")
        service_pattern: str = Field(description="Service layer pattern", default="")
        validation_layer: str = Field(description="Validation approach", default="")
        exception_handling: str = Field(description="Exception handling strategy", default="")

    class DependencyInfo(BaseModel):
        """Dependency information"""
        baseline: List[str] = Field(description="Required baseline dependencies", default_factory=list)
        optional: List[str] = Field(description="Optional dependencies", default_factory=list)

    # Import LLM setup for consistent model configuration
    try:
        from models.llm_setup import setup_model
        _, _, llm_model = setup_model()
    except Exception as e:
        logger.warning(f"Failed to setup LLM model: {e}. Using fallback parser.")
        return _fallback_parse_project_spec(content)

    # Agent Tools for Document Analysis
    @tool
    def analyze_project_overview(content: str) -> str:
        """
        Analyze document content to extract project overview information.
        Looks for project details like name, purpose, language, framework, etc.
        """
        try:
            prompt = f"""
            Analyze the following project specification document and extract project overview information.
            
            Document content:
            {content[:4000]}  # Limit for token efficiency
            
            Extract and return a JSON object with the following fields:
            - project_name: Name of the project
            - purpose: Project purpose and description  
            - language: Primary programming language
            - framework: Main framework
            - build_tool: Build tool (Maven/Gradle/etc)
            - packaging: Packaging type (JAR/WAR/etc)
            - modules: List of project modules
            
            If information is not found, use reasonable defaults for the technology stack.
            Return only valid JSON.
            """
            
            response = llm_model.invoke([{"role": "user", "content": prompt}])
            return response.content # pyright: ignore[reportReturnType]
            
        except Exception as e:
            logger.warning(f"Error in analyze_project_overview: {e}")
            return json.dumps({
                "project_name": "Unknown",
                "purpose": "",
                "language": "Java", 
                "framework": "Spring Boot",
                "build_tool": "Gradle",
                "packaging": "JAR",
                "modules": []
            })

    @tool
    def extract_architecture_notes(content: str) -> str:
        """
        Extract architecture and design pattern information from the document.
        """
        try:
            prompt = f"""
            Analyze the following document for architecture and design information.
            
            Document content:
            {content[:4000]}
            
            Extract and return a JSON object with architecture information:
            - layering: Layered architecture approach
            - dto_placement: DTO placement strategy
            - service_pattern: Service layer pattern  
            - validation_layer: Validation approach
            - exception_handling: Exception handling strategy
            
            Return only valid JSON.
            """
            
            response = llm_model.invoke([{"role": "user", "content": prompt}])
            return response.content # pyright: ignore[reportReturnType]
            
        except Exception as e:
            logger.warning(f"Error in extract_architecture_notes: {e}")
            return json.dumps({
                "layering": "",
                "dto_placement": "",
                "service_pattern": "",
                "validation_layer": "",
                "exception_handling": ""
            })

    @tool
    def extract_dependencies_and_guidelines(content: str) -> str:
        """
        Extract dependencies, testing guidelines, and other technical requirements.
        """
        try:
            prompt = f"""
            Analyze the following document for dependencies and guidelines.
            
            Document content:
            {content[:4000]}
            
            Extract and return a JSON object with:
            - baseline_dependencies: List of required dependencies
            - optional_dependencies: List of optional dependencies
            - workflow_guidelines: List of workflow guidelines
            - quality_checklist: List of quality checklist items
            - security_guidelines: List of security guidelines
            - testing_guidelines: Testing framework information
            
            Return only valid JSON.
            """
            
            response = llm_model.invoke([{"role": "user", "content": prompt}])
            return response.content # pyright: ignore[reportReturnType]
            
        except Exception as e:
            logger.warning(f"Error in extract_dependencies_and_guidelines: {e}")
            return json.dumps({
                "baseline_dependencies": [],
                "optional_dependencies": [],
                "workflow_guidelines": [],
                "quality_checklist": [],
                "security_guidelines": [],
                "testing_guidelines": {}
            })

    # Create Agent-based Parser
    try:
        system_prompt = """
        You are an expert project specification parser. Your task is to analyze project 
        specification documents and extract structured information using the available tools.
        
        Use the tools to:
        1. Extract project overview information
        2. Identify architecture patterns and design notes  
        3. Parse dependencies and guidelines
        
        Combine the results from all tools to provide a comprehensive analysis.
        Be thorough but efficient - focus on the most important information.
        """
        
        agent = create_agent(
            model=llm_model,
            tools=[analyze_project_overview, extract_architecture_notes, extract_dependencies_and_guidelines],
            system_prompt=system_prompt
        )
        
        # Execute Agent Workflow
        result = agent.invoke({
            "messages": [{"role": "user", "content": f"Parse this project specification document:\n\n{content}"}]
        })
        
        # Extract tool outputs from agent messages
        project_overview_data = {}
        architecture_data = {}
        dependencies_data = {}
        
        for message in result.get("messages", []):
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call['name'] == 'analyze_project_overview':
                        # Find corresponding tool message
                        for msg in result["messages"]:
                            if hasattr(msg, 'tool_call_id') and msg.tool_call_id == tool_call['id']:
                                try:
                                    overview_dict = json.loads(msg.content)
                                    overview = ProjectOverview.model_validate(overview_dict)
                                    project_overview_data = overview.model_dump()
                                except Exception as e:
                                    logger.warning(f"Failed to parse project overview: {e}. Using defaults.")
                                    project_overview_data = ProjectOverview().model_dump()
                    elif tool_call['name'] == 'extract_architecture_notes':
                        for msg in result["messages"]:
                            if hasattr(msg, 'tool_call_id') and msg.tool_call_id == tool_call['id']:
                                try:
                                    arch_dict = json.loads(msg.content)
                                    arch_info = ArchitectureInfo.model_validate(arch_dict)
                                    architecture_data = arch_info.model_dump()
                                except Exception as e:
                                    logger.warning(f"Failed to parse architecture info: {e}. Using defaults.")
                                    architecture_data = ArchitectureInfo().model_dump()
                    elif tool_call['name'] == 'extract_dependencies_and_guidelines':
                        for msg in result["messages"]:
                            if hasattr(msg, 'tool_call_id') and msg.tool_call_id == tool_call['id']:
                                try:
                                    deps_dict = json.loads(msg.content)
                                    deps_info = DependencyInfo.model_validate(deps_dict)
                                    dependencies_data = deps_info.model_dump()
                                except Exception as e:
                                    logger.warning(f"Failed to parse dependency info: {e}. Using defaults.")
                                    dependencies_data = DependencyInfo().model_dump()
        
        # Build ProjectSpec from agent analysis
        spec = ProjectSpec(
            project_name=project_overview_data.get("project_name", "Unknown"),
            purpose=project_overview_data.get("purpose", ""),
            language=project_overview_data.get("language", "Java"),
            framework=project_overview_data.get("framework", "Spring Boot"),
            build_tool=project_overview_data.get("build_tool", "Gradle"),
            packaging=project_overview_data.get("packaging", "JAR"),
            modules=project_overview_data.get("modules", []),
            architecture_notes=architecture_data,
            dependencies={
                "baseline": dependencies_data.get("baseline_dependencies", []),
                "optional": dependencies_data.get("optional_dependencies", [])
            },
            workflow_guidelines=dependencies_data.get("workflow_guidelines", []),
            quality_checklist=dependencies_data.get("quality_checklist", []),
            security_guidelines=dependencies_data.get("security_guidelines", []),
            testing_guidelines=dependencies_data.get("testing_guidelines", {}),
            code_style_rules={},  # Can be enhanced with additional tool
            folder_structure={},  # Can be enhanced with additional tool  
            build_deploy_instructions={},  # Can be enhanced with additional tool
            dont_do_list=[]  # Can be enhanced with additional tool
        )
        
        logger.info(f"Successfully parsed project spec: {spec.project_name}")
        return spec
        
    except Exception as e:
        logger.error(f"Agent-based parsing failed: {e}")
        # Fallback to basic parsing
        return _fallback_parse_project_spec(content)


def _fallback_parse_project_spec(content: str) -> ProjectSpec:
    """
    Fallback parser for when agent-based parsing fails.
    Uses simple heuristics to extract basic information.
    """
    import re
    
    # Extract project name from title or filename patterns
    project_name = "Unknown"
    title_match = re.search(r'^#\s+(.+?)(?:\n|$)', content, re.MULTILINE)
    if title_match:
        project_name = title_match.group(1).strip()
    
    # Detect language and framework from content
    language = "Java"
    framework = "Spring Boot"
    
    if "typescript" in content.lower() or "node" in content.lower():
        language = "TypeScript"
        framework = "Node.js"
    elif "python" in content.lower() or "django" in content.lower():
        language = "Python" 
        framework = "Django"
    elif "react" in content.lower():
        language = "TypeScript"
        framework = "React"
    
    # Extract purpose from first paragraph or description
    purpose = ""
    lines = content.split('\n')
    for line in lines:
        if line.strip() and not line.startswith('#') and len(line.strip()) > 50:
            purpose = line.strip()[:200]  # First meaningful line, truncated
            break
    
    return ProjectSpec(
        project_name=project_name,
        purpose=purpose,
        language=language,
        framework=framework,
        build_tool="Gradle",
        packaging="JAR"
    )


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
    content += """
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


def format_file_map_for_prompt(file_map: Dict[str, Any], max_files: int = 20) -> str:
    """
    Format file_map from full_analysis into a readable prompt section.
    
    Args:
        file_map: Dictionary of {file_path: file_data} from analysis
        max_files: Maximum files to include
        
    Returns:
        Formatted string for prompt
    """
    if not file_map:
        return ""
    
    formatted_files = []
    for i, (file_path, file_data) in enumerate(list(file_map.items())[:max_files]):
        try:
            if isinstance(file_data, dict):
                content = file_data.get("content", "")
                lang = file_data.get("language", "unknown")
            else:
                content = str(file_data)
                lang = "unknown"
            
            # Limit content to 1000 chars per file in prompt
            truncated = content[:1000] if len(content) > 1000 else content
            if len(content) > 1000:
                truncated += f"\n... (truncated, {len(content)} total chars)"
            
            formatted_files.append(f"📄 {file_path} ({lang})\n{truncated}\n")
        except Exception as e:
            formatted_files.append(f"📄 {file_path} (error reading: {e})\n")
    
    if not formatted_files:
        return ""
    
    return "\n---\n".join(formatted_files)


def build_intent_prompt(
    feature_request: str,
    context_analysis: str,
    file_contents: str = "",
    project_spec: Optional[ProjectSpec] = None
) -> str:
    """
    Build the prompt for intent parsing analysis with structured JSON output.
    
    Args:
        feature_request: User's feature request
        context_analysis: Previous phase's context analysis
        file_contents: Actual source file contents from codebase analysis
        project_spec: Project specification loaded from markdown files
        
    Returns:
        Formatted prompt string
    """
    file_section = f"""
SOURCE CODE FROM CODEBASE:
{file_contents}

""" if file_contents else ""
    
    # Add project specification section if available
    project_spec_section = ""
    if project_spec:
        project_spec_section = f"""
PROJECT SPECIFICATIONS:
Project Name: {project_spec.project_name or 'Not specified'}
Purpose: {project_spec.purpose or 'Not specified'}
Language: {project_spec.language or 'Not specified'}
Framework: {project_spec.framework or 'Not specified'}
Build Tool: {project_spec.build_tool or 'Not specified'}
Packaging: {project_spec.packaging or 'Not specified'}

Code Style Rules:
{chr(10).join(f"- {rule}" for rule in (project_spec.code_style_rules or [])) or "Not specified"}

Architecture Notes:
{chr(10).join(f"- {note}" for note in (project_spec.architecture_notes or [])) or "Not specified"}

Dependencies:
{chr(10).join(f"- {dep}" for dep in (project_spec.dependencies or [])) or "Not specified"}

Testing Guidelines:
{chr(10).join(f"- {guideline}" for guideline in (project_spec.testing_guidelines or [])) or "Not specified"}

Workflow Guidelines:
{chr(10).join(f"- {guideline}" for guideline in (project_spec.workflow_guidelines or [])) or "Not specified"}

Don't Do List:
{chr(10).join(f"- {item}" for item in (project_spec.dont_do_list or [])) or "Not specified"}

Quality Checklist:
{chr(10).join(f"- {item}" for item in (project_spec.quality_checklist or [])) or "Not specified"}

"""
    
    prompt = f"""
CODEBASE CONTEXT:
{context_analysis}

{project_spec_section}{file_section}

FEATURE REQUEST:
{feature_request}

As an expert software engineer and domain analyst, analyze this feature request and provide a structured JSON response.

**DOMAIN ANALYSIS PROCESS:**
1. **Identify Business Domain**: What industry/business domain does this feature belong to?
   - Library Management, E-commerce, Banking, Healthcare, Inventory, etc.
   - Explain your reasoning for choosing this domain

2. **Extract Domain Entities**: What are the core business entities in this domain?
   - List 2-5 primary entities with their business meaning
   - Focus on nouns that represent business concepts/objects

3. **Business Rules & Constraints**: What are key business rules?
   - Validation rules, relationships, constraints

**REQUIRED JSON OUTPUT FORMAT:**
Return ONLY a valid JSON object with this exact structure:
{{
  "domain_analysis": {{
    "identified_domain": "string - business domain name",
    "domain_reasoning": "string - why you chose this domain",
    "confidence_score": "high|medium|low - how confident you are"
  }},
  "entities": [
    {{
      "name": "string - entity name (TitleCase)",
      "description": "string - what this entity represents",
      "business_rules": ["array of strings - key business rules"]
    }}
  ],
  "implementation_notes": {{
    "primary_entity": "string - most important entity for this feature",
    "suggested_architecture": "string - brief architecture recommendation",
    "complexity_estimate": "low|medium|high"
  }},
  "clarifying_questions": ["array of strings - questions that need clarification"]
}}

**IMPORTANT:**
- Return ONLY the JSON object, no additional text
- Ensure JSON is valid and properly formatted
- Focus on business domain understanding, not technical implementation
- Be specific about domain and entities
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
    
    # ===== PHASE 1: ANALYSIS =====
    todos.append(TodoItem(
        id=todo_id,
        title="Analyze existing codebase structure",
        description="Scan codebase for existing patterns, frameworks, and architecture",
        phase="analysis",
        status="completed",
        priority="high",
        depends_on=[],
        estimated_effort="medium"
    ))
    todo_id += 1
    
    todos.append(TodoItem(
        id=todo_id,
        title="Detect framework and patterns",
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


def extract_entities_from_section(feature_request: str, section_keywords: Optional[List[str]] = None) -> List[str]:
    """
    Extract domain entities from structured markdown sections like "## 🧩 Core Entities".
    
    This function looks for sections that explicitly list the main business entities
    in a specification. It parses bullet points and returns cleaned entity names.
    
    Args:
        feature_request: The full specification text
        section_keywords: Keywords to search for section markers (default: ['core entities', 'main entities', 'domain entities'])
        
    Returns:
        List of entity names extracted from the section, or empty list if not found
        
    References:
        - Information Extraction patterns: https://en.wikipedia.org/wiki/Information_extraction
        - LangChain structured output: https://python.langchain.com/docs/guides/structured_output/
    """
    if section_keywords is None:
        section_keywords = ['core entities', 'main entities', 'domain entities', 'entities', 'models']
    
    entities = []
    
    # Look for markdown section headers (e.g., "## 🧩 Core Entities")
    for keyword in section_keywords:
        # Case-insensitive search for section header
        pattern = r'#{1,3}\s+.*?' + re.escape(keyword) + r'.*?\n(.*?)(?=\n#{1,3}|\Z)'
        matches = re.findall(pattern, feature_request, re.IGNORECASE | re.DOTALL)
        
        if matches:
            section_content = matches[0]
            
            # Extract bullet points (*, -, •, or numbered lists)
            # Format can be: "* EntityName — description" or "- **EntityName** — description" or "1. EntityName"
            # Handle markdown bold: **EntityName** and also plain names
            bullet_pattern = r'[*\-•]\s+(?:\*\*)?([A-Za-z][A-Za-z0-9]+(?:[A-Za-z0-9]*)?)\*\*?\s*[—\-:\.]?'
            bullets = re.findall(bullet_pattern, section_content)
            
            # Also try numbered list format
            if not bullets:
                numbered_pattern = r'\d+\.\s+(?:\*\*)?([A-Za-z][A-Za-z0-9]+(?:[A-Za-z0-9]*)?)\*\*?\s*[—\-:\.]?'
                bullets = re.findall(numbered_pattern, section_content)
            
            # Capitalize properly (PascalCase)
            for bullet in bullets:
                # Keep existing capitalization if already PascalCase
                if re.match(r'^[A-Z][a-z]+(?:[A-Z][a-z]+)*$', bullet):
                    entities.append(bullet)
                else:
                    # Convert to PascalCase: "courier" → "Courier", "package_delivery" → "PackageDelivery"
                    parts = re.split(r'[_\s-]', bullet)
                    pascal_case = ''.join(word.capitalize() for word in parts if word)
                    if pascal_case:
                        entities.append(pascal_case)
            
            if entities:
                break
    
    return list(dict.fromkeys(entities))  # Remove duplicates, preserve order


def extract_entities_via_llm(feature_request: str, excluded_terms: Optional[set] = None) -> List[str]:
    """
    Extract domain entities using LLM SEMANTIC REASONING.
    
    This is the PRIMARY extraction method. LLM semantic understanding is critical because:
    - Regex cannot handle case variations (courier vs Courier)
    - Regex cannot understand domain semantics (what is a "core entity")
    - LLM uses transformer embeddings to understand entity relationships
    - LLM can reason about business context
    
    This function REQUIRES a working LLM. If LLM is not available, it RAISES an error
    because entity extraction is a HARD DEPENDENCY on semantic understanding.
    
    Args:
        feature_request: The full specification text
        excluded_terms: Terms to filter out from results (technical terms)
        
    Returns:
        List of extracted domain entities in PascalCase
        
    Raises:
        RuntimeError: If LLM is not available or API keys not configured
        
    References:
        - LangChain + LiteLLM integration
        - Semantic entity extraction: https://en.wikipedia.org/wiki/Information_extraction
    """
    if excluded_terms is None:
        excluded_terms = set()
    
    try:
        import os
        import litellm
        
        # Setup LLM from environment configuration
        llm_model = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
        llm_api_key = os.getenv("LITELLM_VIRTUAL_KEY")
        llm_api_base = os.getenv("LITELLM_API")
        
        if not llm_api_key:
            raise RuntimeError("LITELLM_VIRTUAL_KEY environment variable not set")
        
        system_prompt = """You are an expert software architect analyzing business requirements.
Your task is to identify ONLY the MAIN BUSINESS ENTITIES (not technical components).

Focus on:
- Core domain concepts (what the business manages)
- Entities mentioned multiple times in specification
- Things that would have their own database table/class
- Main actors, resources, and workflows

DO NOT include:
- Technical/framework terms (API, REST, Controller, Service, DTO, Repository, etc.)
- Adjectives or qualifiers (detailed, comprehensive, full, new, old, etc.)
- Action words or verbs (create, generate, manage, process, etc.)
- Data format names (JSON, CSV, PDF, XML, etc.)
- System/infrastructure terms (database, system, implementation, etc.)

Return as valid JSON: {"entities": ["Entity1", "Entity2", ...]} in PascalCase."""
        
        user_prompt = f"""Extract main business entities from this specification.
Be thorough - if something appears multiple times and represents a core domain concept, it's likely an entity.

Specification:
---
{feature_request[:3000]}
---

Remember: Semantic reasoning, not pattern matching. Understand the DOMAIN, not just the WORDS.
Return ONLY valid JSON with no additional text."""
        
        # Call LiteLLM - use temperature=1 (gpt-5 doesn't support temperature=0)
        response = litellm.completion(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            api_key=llm_api_key,
            api_base=llm_api_base,
            temperature=1.0  # gpt-5 doesn't support temperature=0, use 1.0 for deterministic behavior
        )
        
        # Extract response text - robustly handle different response formats
        response_text = None
        try:
            # Try attribute access first
            response_text = response.choices[0].message.content  # type: ignore
        except (AttributeError, TypeError, IndexError):
            try:
                # Try dict access
                response_text = response['choices'][0]['message']['content']  # type: ignore
            except (KeyError, TypeError):
                # Fallback to string conversion
                response_text = str(response)
        
        if not response_text:
            raise ValueError(f"Could not extract text from LLM response: {response}")
        
        # Parse JSON from response
        json_match = re.search(r'\{[^{}]*"entities"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            entities = result.get('entities', [])
        else:
            raise ValueError(f"Could not parse JSON from LLM response:\n{response_text}")
        
        # Filter out excluded technical terms
        entities = [e for e in entities if e.lower() not in excluded_terms]
        
        return entities
    
    except ImportError as e:
        raise RuntimeError(
            f"LLM extraction requires LiteLLM and LangChain. Missing: {e}\n"
            f"Install with: pip install litellm langchain"
        ) from e
    
    except Exception as e:
        import os as os_module
        raise RuntimeError(
            f"Entity extraction FAILED - LLM is a HARD DEPENDENCY.\n"
            f"Error: {str(e)}\n"
            f"Ensure LLM configuration:\n"
            f"  - LITELLM_MODEL (currently: {os_module.getenv('LITELLM_MODEL')})\n"
            f"  - LITELLM_VIRTUAL_KEY (set: {bool(os_module.getenv('LITELLM_VIRTUAL_KEY'))})\n"
            f"  - LITELLM_API (currently: {os_module.getenv('LITELLM_API')})\n"
            f"Semantic entity extraction requires LLM reasoning (regex does NOT work for arbitrary domains)."
        ) from e


def extract_entities_semantic_rule_based(feature_request: str, excluded_terms: Optional[set] = None) -> List[str]:
    """
    Extract domain entities using SEMANTIC RULE-BASED ANALYSIS (no hardcoded patterns).
    
    This function uses dynamic business context analysis to identify entities:
    - Analyzes word frequency and co-occurrence patterns
    - Uses semantic clustering to group related terms
    - Applies domain-aware filtering without hardcoded keywords
    - Leverages linguistic patterns for entity recognition
    
    This is a fallback method when LLM is not available, providing semantic
    understanding without requiring external API calls.
    
    Args:
        feature_request: The full specification text
        excluded_terms: Terms to filter out from results (technical terms)
        
    Returns:
        List of extracted domain entities in PascalCase
        
    References:
        - Natural Language Processing for entity extraction
        - Semantic analysis techniques: https://en.wikipedia.org/wiki/Semantic_analysis
    """
    if excluded_terms is None:
        excluded_terms = set()
    
    import re
    from collections import Counter
    
    # Convert to lowercase for analysis but preserve original for output
    text_lower = feature_request.lower()
    
    # STEP 1: Extract candidate terms using linguistic patterns
    candidates = []
    
    # Pattern 1: Noun phrases (common entity indicators)
    # Look for sequences that might be entities
    noun_patterns = [
        r'\b[a-z]+(?:\s+[a-z]+){0,2}\b',  # 1-3 word sequences
    ]
    
    for pattern in noun_patterns:
        matches = re.findall(pattern, text_lower)
        candidates.extend(matches)
    
    # STEP 2: Semantic filtering - remove technical and common words
    semantic_candidates = []
    for candidate in candidates:
        words = candidate.split()
        
        # Skip if contains excluded technical terms
        if any(word in excluded_terms for word in words):
            continue
            
        # Skip common English words and articles
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
            'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'what', 'when',
            'where', 'why', 'how', 'all', 'some', 'any', 'every', 'most', 'many', 'much', 'few',
            'little', 'first', 'last', 'next', 'new', 'old', 'good', 'bad', 'big', 'small', 'long',
            'short', 'high', 'low', 'right', 'left', 'full', 'empty', 'open', 'closed', 'hot', 'cold'
        }
        
        if not any(word in common_words for word in words):
            semantic_candidates.append(candidate)
    
    # STEP 3: Frequency analysis - entities are mentioned multiple times
    term_freq = Counter(semantic_candidates)
    
    # STEP 4: Semantic clustering - group related terms
    # Simple approach: terms that appear together frequently
    term_pairs = []
    sentences = re.split(r'[.!?]+', feature_request)
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        found_terms = []
        for term in semantic_candidates:
            if term in sentence_lower:
                found_terms.append(term)
        
        # Record co-occurrences
        for i, term1 in enumerate(found_terms):
            for term2 in found_terms[i+1:]:
                term_pairs.append((term1, term2))
    
    pair_freq = Counter(term_pairs)
    
    # STEP 5: Score candidates based on multiple semantic factors
    scored_candidates = []
    
    for candidate, freq in term_freq.items():
        score = 0
        
        # Frequency score (mentioned multiple times = likely entity)
        score += freq * 2
        
        # Length score (longer terms more specific)
        words = candidate.split()
        if len(words) > 1:
            score += len(words)
        
        # Capitalization patterns in original text (proper nouns)
        original_matches = re.findall(re.escape(candidate), feature_request, re.IGNORECASE)
        capitalized_count = sum(1 for match in original_matches if match[0].isupper())
        score += capitalized_count
        
        # Semantic connections (terms that appear with other candidates)
        connections = sum(1 for pair, count in pair_freq.items() 
                         if candidate in pair)
        score += connections * 0.5
        
        scored_candidates.append((candidate, score))
    
    # STEP 6: Select top candidates and convert to PascalCase
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    entities = []
    for candidate, score in scored_candidates[:10]:  # Top 10 candidates
        if score >= 2:  # Minimum threshold
            # Convert to PascalCase
            words = candidate.split()
            pascal_case = ''.join(word.capitalize() for word in words)
            
            # Ensure it's a valid entity name (starts with capital, alphanumeric)
            if re.match(r'^[A-Z][A-Za-z0-9]*$', pascal_case):
                entities.append(pascal_case)
    
    # Remove duplicates while preserving order
    entities = list(dict.fromkeys(entities))
    
    return entities


def extract_entities_from_spec(feature_request: str, analysis_model: Any = None) -> Dict[str, List[str]]:
    """
    Extract all DOMAIN entities from specification using SEMANTIC REASONING.

    Strategy:
    1. Try LLM semantic extraction first (when available) - handles arbitrary specs
    2. If LLM not available or fails, use rule-based semantic extraction - no hardcoded patterns
    3. Extract from structured section ("## 🧩 Core Entities") as final fallback

    This function NEVER fails - it always returns entities using the best available method.

    Args:
        feature_request: The full specification text containing entity definitions
        analysis_model: Optional LLM model for semantic extraction

    Returns:
        Dictionary with domain entities, services, controllers, and DTOs
    """
    entities = []

    # Technical terms to exclude from results
    excluded_terms = {
        # Technical/Framework terms
        'implement', 'comprehensive', 'operations', 'audit', 'trail', 'tracking', 'system',
        'rest', 'controller', 'api', 'endpoints', 'entity', 'repository', 'service', 'tests',
        'crud', 'operations', 'layer', 'pattern', 'models', 'classes', 'interfaces', 'abstract',
        'beans', 'annotations', 'validation', 'error', 'handling', 'logging', 'transactions',
        'security', 'testing', 'unit', 'integration', 'test', 'request', 'response', 'dto',
        'jpa', 'database', 'persistence', 'logic', 'business', 'concerns',
        'requirements', 'features', 'implementation', 'architecture', 'structure', 'patterns',

        # Adjectives & Qualifiers
        'full', 'complete', 'comprehensive', 'entire', 'whole', 'partial', 'total',
        'monthly', 'annual', 'daily', 'weekly', 'periodic', 'yearly',
        'large', 'small', 'big', 'massive', 'robust', 'simple',
        'new', 'old', 'latest', 'advanced', 'basic', 'detailed', 'brief',
        'automated', 'manual', 'automatic', 'dynamic', 'static',
        'active', 'inactive', 'enabled', 'disabled', 'available',

        # Action words
        'generate', 'create', 'export', 'import', 'delete', 'update', 'retrieve',
        'manage', 'handle', 'process', 'analyze', 'report', 'document', 'monitor',
        'implement', 'develop', 'design', 'support', 'provide', 'enable',

        # Data/Format words
        'pdf', 'csv', 'json', 'xml', 'text', 'binary', 'data', 'document',
        'record', 'entry', 'item', 'value', 'number', 'string', 'flag'
    }

    # STRATEGY 1: Try LLM semantic extraction first (when available)
    if analysis_model:
        try:
            entities = extract_entities_via_llm(feature_request, excluded_terms)
            if entities:
                print(f"✓ LLM extracted {len(entities)} entities via semantic reasoning")
            else:
                print("⚠ LLM available but returned no entities, trying rule-based extraction")
        except Exception as e:
            print(f"⚠ LLM extraction failed: {e}, falling back to rule-based extraction")

    # STRATEGY 2: Rule-based semantic extraction (no hardcoded patterns)
    if not entities:
        try:
            entities = extract_entities_semantic_rule_based(feature_request, excluded_terms)
            if entities:
                print(f"✓ Rule-based extracted {len(entities)} entities via semantic analysis")
        except Exception as e:
            print(f"⚠ Rule-based extraction failed: {e}, trying structured section extraction")

    # STRATEGY 3: Try structured section extraction as final fallback
    if not entities:
        section_entities = extract_entities_from_section(feature_request)
        if section_entities:
            entities = section_entities
            print(f"✓ Extracted {len(entities)} entities from structured section (## 🧩 Core Entities)")
        else:
            print("⚠ No entities found from any extraction method")

    # Remove duplicates while preserving order
    entities = list(dict.fromkeys(entities))

    # Generate corresponding services, controllers, and DTOs
    services = []
    controllers = []
    dtos = []

    for entity in entities:
        service_name = entity + 'Service'
        controller_name = entity + 'Controller'
        dto_name = entity + 'DTO'

        services.append(service_name)
        controllers.append(controller_name)
        dtos.append(dto_name)

    return {
        'entities': entities,
        'services': services,
        'controllers': controllers,
        'dtos': dtos
    }


def create_framework_planner_subagent(analysis_model: Any) -> Any:
    """
    Create a subagent specialized in dynamic framework planning.
    This subagent replaces hardcoded logic with LLM-driven reasoning.

    Args:
        analysis_model: LLM model instance

    Returns:
        Subagent for framework planning
    """
    if not analysis_model:
        raise ValueError("Analysis model required for framework planning subagent")

    system_prompt = """You are a Senior Software Architect specializing in framework-specific implementation planning.

Your expertise covers ALL major frameworks dynamically:
- Spring Boot (Java)
- Django (Python)
- Node.js/Express (JavaScript)
- React/Next.js (JavaScript)
- .NET Core (C#)
- Flask/FastAPI (Python)
- And any other framework

Given a feature request, entities, and framework, you dynamically determine:
1. Required file structure and naming conventions
2. SOLID principles application for that framework
3. Framework-specific best practices and patterns
4. Layer organization (Controller/Service/Repository/DTO)
5. Testing structure and conventions
6. Configuration and dependency management

Key capabilities:
- Understand framework conventions without hardcoded rules
- Apply appropriate design patterns for each framework
- Generate proper file paths and naming
- Consider framework-specific annotations, decorators, or configurations
- Plan for scalability and maintainability within framework constraints

Always reason about the specific framework's patterns and conventions."""

    # ✅ Best practice: Define subagent with complete metadata following DeepAgents patterns
    framework_planner_config = {
        "name": "framework_planner",
        "description": "Specializes in dynamic framework planning for Spring Boot, Django, Node.js, React, and other major frameworks. Creates detailed file structures, applies SOLID principles, and follows framework-specific conventions.",
        "system_prompt": system_prompt,
        "tools": [],  # Framework planning is reasoning-based, no additional tools needed
        "model": analysis_model,
        "middleware": []  # Could add custom middleware for framework analysis if needed
    }

    return create_deep_agent(**framework_planner_config)


def plan_files_with_subagent(
    feature_request: str,
    detected_entities: List[str],
    framework: str,
    context_analysis: str = "",
    project_spec: Optional[ProjectSpec] = None,
    subagent_model: Any = None
) -> NewFilesPlanningSuggestion:
    """
    Use subagent to dynamically plan file structure instead of hardcoded logic.

    Args:
        feature_request: The feature specification
        detected_entities: List of domain entities
        framework: Detected framework (Spring Boot, Django, etc.)
        context_analysis: Codebase context
        project_spec: Project specifications
        subagent_model: LLM model for subagent

    Returns:
        Dynamic file planning based on framework reasoning
    """
    if not subagent_model:
        # Fallback to basic structure if no model
        return _create_basic_file_structure(detected_entities, framework)

    try:
        # Create framework planner subagent
        framework_planner = create_framework_planner_subagent(subagent_model)

        # Build comprehensive planning prompt with output control strategy
        planning_prompt = f"""
Analyze this feature request and create a comprehensive file structure plan.

FRAMEWORK: {framework}
FEATURE REQUEST:
{feature_request}

DETECTED ENTITIES: {', '.join(detected_entities)}

CONTEXT ANALYSIS:
{context_analysis}

PROJECT SPECIFICATIONS:
{project_spec.framework if project_spec else 'Not specified'}
{chr(10).join(project_spec.architecture_notes) if project_spec and project_spec.architecture_notes else ''}

Based on the {framework} framework conventions, create a detailed file planning that includes:

1. **File Structure**: Complete directory layout following {framework} patterns
2. **Entity Files**: Proper naming and organization for each entity
3. **Layer Separation**: Controller/Service/Repository/DTO layers
4. **SOLID Principles**: How each principle applies in {framework}
5. **Framework Conventions**: Specific annotations, decorators, configurations
6. **Testing Structure**: Test file organization and naming
7. **Best Practices**: Framework-specific patterns and anti-patterns

Return your analysis in this JSON format:
{{
  "framework_analysis": {{
    "framework": "{framework}",
    "architecture_pattern": "layered|hexagonal|clean|etc",
    "key_conventions": ["list of framework-specific conventions"],
    "layering_strategy": "description of how layers are organized"
  }},
  "file_structure": {{
    "base_package": "com.example.app or src/app etc",
    "directories": {{
      "directory_name": "purpose_description"
    }},
    "creation_order": ["file1.java", "file2.java", ...]
  }},
  "entity_files": [
    {{
      "entity": "EntityName",
      "files": [
        {{
          "type": "entity|model",
          "path": "src/main/java/com/example/Entity.java",
          "purpose": "JPA entity class",
          "solid_principles": ["SRP", "OCP"],
          "framework_patterns": ["@Entity", "@Table", "lombok"]
        }}
      ]
    }}
  ],
  "solid_principles": {{
    "srp": ["how SRP is applied in {framework}"],
    "ocp": ["extension points in {framework}"],
    "lsp": ["inheritance patterns"],
    "isp": ["interface segregation approach"],
    "dip": ["dependency injection patterns"]
  }},
  "best_practices": [
    "framework-specific best practice 1",
    "framework-specific best practice 2"
  ],
  "framework_conventions": [
    "convention 1 with explanation",
    "convention 2 with explanation"
  ],
  "testing_approach": {{
    "test_framework": "JUnit/Mockito or pytest/unittest etc",
    "test_structure": "description of test organization",
    "mocking_strategy": "how to mock dependencies"
  }}
}}

CRITICAL OUTPUT REQUIREMENTS (DeepAgents Best Practice):
- Return ONLY valid JSON, no additional text or explanations
- Include all reasoning within the JSON structure itself
- Ensure framework-specific details are comprehensive and accurate
- If uncertain about framework conventions, use generic best practices
- All file paths must follow the target framework's conventions
- Entity names must match the detected_entities list provided

Focus on {framework} best practices and patterns. Be specific about file paths, naming conventions, and framework features.
"""

        # Invoke subagent for planning
        response = framework_planner.invoke({
            "messages": [{"role": "user", "content": planning_prompt}]
        })

        # Parse subagent response
        if response and "messages" in response:
            for msg in response["messages"]:
                if hasattr(msg, 'content') and msg.content:
                    try:
                        import json
                        planning_result = json.loads(msg.content)

                        # Convert to NewFilesPlanningSuggestion format
                        return _convert_subagent_result_to_suggestion(
                            planning_result, detected_entities, framework
                        )
                    except json.JSONDecodeError: # pyright: ignore[reportPossiblyUnboundVariable]
                        continue

        # Fallback if parsing fails
        print("⚠ Subagent planning failed, using basic structure")
        return _create_basic_file_structure(detected_entities, framework)

    except Exception as e:
        print(f"⚠ Framework planning subagent failed: {e}, using basic structure")
        return _create_basic_file_structure(detected_entities, framework)


def _convert_subagent_result_to_suggestion(
    planning_result: Dict,
    detected_entities: List[str],
    framework: str
) -> NewFilesPlanningSuggestion:
    """Convert subagent JSON result to NewFilesPlanningSuggestion format."""

    suggested_files = []
    directory_structure = {}
    creation_order = []
    best_practices = []
    framework_conventions = []

    # Extract directory structure
    if "file_structure" in planning_result:
        fs = planning_result["file_structure"]
        directory_structure.update(fs.get("directories", {}))

        # Extract creation order
        creation_order = fs.get("creation_order", [])

    # Extract entity files
    if "entity_files" in planning_result:
        for entity_data in planning_result["entity_files"]:
            entity_name = entity_data["entity"]
            for file_info in entity_data["files"]:
                # Extract directory path and join with /
                path_parts = file_info["path"].split("/")
                relative_path = "/".join(path_parts[:-1]) if len(path_parts) > 1 else "."
                filename = path_parts[-1]
                
                suggested_files.append(FilePlacementSuggestion(
                    file_type=file_info["type"],
                    relative_path=relative_path,  # ✓ Now a string
                    filename=filename,
                    purpose=file_info["purpose"],
                    solid_principles=file_info.get("solid_principles", []),
                    example_class_name=entity_name,
                    layer=file_info["type"]
                ))

    # Extract best practices and conventions
    best_practices = planning_result.get("best_practices", [])
    framework_conventions = planning_result.get("framework_conventions", [])

    # Add SOLID principles from analysis
    if "solid_principles" in planning_result:
        solid = planning_result["solid_principles"]
        for principle, applications in solid.items():
            best_practices.extend([f"{principle.upper()}: {app}" for app in applications])

    return NewFilesPlanningSuggestion(
        suggested_files=suggested_files,
        directory_structure=directory_structure,
        best_practices=best_practices,
        framework_conventions=framework_conventions,
        creation_order=creation_order
    )


def _create_basic_file_structure(
    detected_entities: List[str],
    framework: str
) -> NewFilesPlanningSuggestion:
    """Fallback basic file structure when subagent fails."""

    suggested_files = []
    directory_structure = {}
    creation_order = []
    best_practices = ["Apply SOLID principles", "Write unit tests", "Use dependency injection"]
    framework_conventions = [f"Follow {framework} best practices"]

    # Basic structure for any framework
    for entity in detected_entities:
        # Model/Entity
        suggested_files.append(FilePlacementSuggestion(
            file_type="entity",
            relative_path="src/main/java/com/example/model" if "java" in framework.lower() else "models",
            filename=f"{entity}.java" if "java" in framework.lower() else f"{entity}.py",
            purpose=f"Domain entity for {entity}",
            solid_principles=["SRP"],
            example_class_name=entity,
            layer="model"
        ))

        # Service
        suggested_files.append(FilePlacementSuggestion(
            file_type="service",
            relative_path="src/main/java/com/example/service" if "java" in framework.lower() else "services",
            filename=f"{entity}Service.java" if "java" in framework.lower() else f"{entity}_service.py",
            purpose=f"Business logic for {entity}",
            solid_principles=["SRP", "DIP"],
            example_class_name=f"{entity}Service",
            layer="service"
        ))

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
    
    feature_request = state.get("feature_request")
    codebase_path = state.get("codebase_path")
    context_analysis = state.get("context_analysis", "")
    full_analysis = state.get("full_analysis", {})  # ✓ GET FULL ANALYSIS FROM PHASE 1
    
    # Validation
    if not feature_request:
        state["errors"].append("No feature request provided")
        return state
    
    if not codebase_path:
        state["errors"].append("No codebase path provided")
        return state
    
    # Load project specifications from markdown files
    project_spec = read_project_specification(codebase_path)
    if project_spec:
        print(f"  📋 Project spec loaded: {project_spec.project_name}")
        state["project_spec"] = project_spec
    else:
        print("  ℹ️  No project specification found, using generic guidelines")
        state["project_spec"] = None
    
    # Extract actual file contents from full analysis if available
    file_contents = ""
    if full_analysis and "file_map" in full_analysis:
        try:
            file_map = full_analysis["file_map"]
            file_contents = format_file_map_for_prompt(file_map, max_files=20)  # ✓ FORMAT FILES
            if file_contents:
                print(f"  ✓ {len(file_map)} files available for context")
        except Exception as e:
            print(f"  ⚠️  Failed to extract file contents: {e}")
            file_contents = ""
    else:
        print("  ℹ️  No full analysis available, will use context summary only")
    
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
    else:
        # Try to detect framework from full_analysis or context_analysis
        if full_analysis and "results" in full_analysis and "basic_info" in full_analysis["results"]:
            detected_framework = full_analysis["results"]["basic_info"].get("framework")
        if not detected_framework and context_analysis:
            # Simple detection from context
            context_lower = context_analysis.lower()
            if "spring boot" in context_lower or "spring_boot" in context_lower:
                detected_framework = "Spring Boot"
            elif "django" in context_lower:
                detected_framework = "Django"
            elif "react" in context_lower:
                detected_framework = "React"
            elif "node" in context_lower or "express" in context_lower:
                detected_framework = "Node.js"
        
        if detected_framework:
            print(f"  🔍 Framework detected: {detected_framework}")
        else:
            print("  ℹ️  No specific framework detected, using generic patterns")
            detected_framework = "Generic"
    
    # STEP 1: Deep Specification Analysis using DeepAgent (maximized reasoning)
    print("\n  🧠 Step 1: Deep specification analysis (maximizing agent reasoning depth)...")
    deep_analysis_result = None
    import time
    
    if analysis_model:
        start_time = time.time()  # Initialize timing
        try:
            start_time = time.time()
            print("    📝 Creating spec analyzer agent...")
            # Create spec analyzer agent for comprehensive feature understanding
            spec_analyzer = create_spec_analyzer_agent(analysis_model)
            agent_creation_time = time.time() - start_time
            print(f"    ✓ Spec analyzer agent created ({agent_creation_time:.2f}s)")
            
            start_time = time.time()
            print("    📋 Building comprehensive analysis prompt...")
            # Build comprehensive analysis prompt
            deep_analysis_prompt = build_comprehensive_spec_analysis_prompt(
                feature_request,
                context_analysis,
                project_spec
            )
            prompt_build_time = time.time() - start_time
            print(f"    ✓ Analysis prompt built ({len(deep_analysis_prompt)} characters, {prompt_build_time:.2f}s)")
            
            start_time = time.time()
            print("    🤖 Invoking DeepAgent for deep reasoning...")
            # Run deep analysis through DeepAgent
            deep_result = spec_analyzer.invoke({
                "messages": [{"role": "user", "content": deep_analysis_prompt}]
            })
            agent_invocation_time = time.time() - start_time
            print(f"    ✓ DeepAgent invocation complete ({agent_invocation_time:.2f}s)")
            
            start_time = time.time()
            print("    🔍 Extracting and parsing analysis results...")
            # Extract analysis result
            if deep_result and "messages" in deep_result:
                print(f"    📨 Found {len(deep_result['messages'])} messages in response")
                for msg_idx, msg in enumerate(deep_result["messages"]):
                    if hasattr(msg, 'content') and msg.content:
                        msg_content = msg.content
                        print(f"    📄 Processing message {msg_idx + 1} ({len(msg_content)} characters)")
                        
                        # Show first 200 characters of raw response for debugging
                        print(f"    🔎 Raw response preview: {msg_content[:200]}{'...' if len(msg_content) > 200 else ''}")
                        
                        # Try to parse as JSON with improved extraction
                        import json
                        try:
                            print("    🔧 Attempting direct JSON parse...")
                            # Strategy 1: Try direct JSON parse first
                            deep_analysis_result = json.loads(msg_content)
                            print("    ✓ Direct JSON parse successful")
                        except json.JSONDecodeError as direct_err:
                            print(f"    ⚠️ Direct JSON parse failed: {str(direct_err)[:100]}")
                            try:
                                print("    🔧 Attempting bracket-based JSON extraction...")
                                # Strategy 2: Look for JSON object by finding matching braces
                                start_idx = msg_content.find('{')
                                if start_idx != -1:
                                    print(f"    📍 Found opening brace at position {start_idx}")
                                    # Find matching closing brace by counting braces
                                    brace_count = 0
                                    for i in range(start_idx, len(msg_content)):
                                        if msg_content[i] == '{':
                                            brace_count += 1
                                        elif msg_content[i] == '}':
                                            brace_count -= 1
                                            if brace_count == 0:
                                                json_str = msg_content[start_idx:i+1]
                                                print(f"    📍 Extracted JSON substring ({len(json_str)} characters)")
                                                deep_analysis_result = json.loads(json_str)
                                                print("    ✓ Bracket-based JSON parse successful")
                                                break
                                else:
                                    print("    ❌ No opening brace found in response")
                            except (json.JSONDecodeError, IndexError) as bracket_err:
                                print(f"    ❌ Bracket-based parse failed: {str(bracket_err)[:100]}")
                                deep_analysis_result = None
                        
                        # Process result if parsing succeeded
                        if deep_analysis_result:
                            print("    📊 Processing parsed analysis results...")
                            try:
                                feature_count = deep_analysis_result.get('deep_analysis', {}).get('feature_count', '?')
                                parsing_time = time.time() - start_time
                                print(f"    ✓ Deep analysis complete - identified {feature_count} feature areas ({parsing_time:.2f}s)")
                                
                                # Print identified features
                                if "identified_features" in deep_analysis_result:
                                    features = deep_analysis_result["identified_features"]
                                    print(f"    📊 Feature areas detected ({len(features)} total):")
                                    for feature in features:
                                        feature_name = feature.get('feature_name', 'Unknown')
                                        priority = feature.get('priority', 'unknown')
                                        print(f"      - {feature_name} (Phase: {priority})")
                                else:
                                    print("    ⚠️ No 'identified_features' found in analysis result")
                                
                                break
                            except (KeyError, TypeError) as extract_err:
                                parsing_time = time.time() - start_time
                                print(f"    ❌ Failed to extract features from analysis: {str(extract_err)[:100]} ({parsing_time:.2f}s)")
                                deep_analysis_result = None
                        else:
                            parsing_time = time.time() - start_time
                            print(f"    ❌ JSON parsing failed completely ({parsing_time:.2f}s)")
            else:
                parsing_time = time.time() - start_time
                print(f"    ❌ No valid messages found in DeepAgent response ({parsing_time:.2f}s)")
            
            if not deep_analysis_result:
                print("    ⚠️ Deep analysis incomplete - will use standard analysis")
        
        except Exception as e:
            total_time = time.time() - start_time if 'start_time' in locals() else 0
            print(f"    ❌ Deep spec analysis failed: {str(e)[:150]} ({total_time:.2f}s) - will use standard analysis")
            deep_analysis_result = None
    else:
        print("    ℹ️ Model not configured for deep analysis - using standard approach")
    
    # STEP 1.5: Extract detected entities from deep analysis results
    detected_entities = []
    if deep_analysis_result:
        print("\n  🧩 Step 1.5: Extracting entities from deep analysis...")
        try:
            # Extract entities from identified_features
            for feature in deep_analysis_result.get('identified_features', []):
                core_entities = feature.get('core_entities', [])
                if isinstance(core_entities, list):
                    detected_entities.extend(core_entities)
                    feature_name = feature.get('feature_name', 'Feature')
                    print(f"    ✓ Feature '{feature_name}' has {len(core_entities)} entities")
            
            # Also extract from entity_map if available and no entities found yet
            if not detected_entities and 'entity_map' in deep_analysis_result:
                entity_map = deep_analysis_result['entity_map']
                if isinstance(entity_map, dict):
                    detected_entities.extend(entity_map.keys())
                    print(f"    ✓ Extracted {len(entity_map)} entities from entity_map")
            
            # Deduplicate while preserving order
            detected_entities = list(dict.fromkeys(detected_entities))
            
            if detected_entities:
                print(f"    ✓ Total detected entities: {len(detected_entities)}")
                for entity in detected_entities[:10]:
                    print(f"      - {entity}")
                if len(detected_entities) > 10:
                    print(f"      ... and {len(detected_entities) - 10} more")
            else:
                print("    ⚠️ No entities extracted from deep analysis")
        except Exception as e:
            print(f"    ⚠️ Failed to extract entities from deep analysis: {e}")
            detected_entities = []
    
    # STEP 2: Standard intent parsing and file analysis
    print("\n  🔍 Step 2: Standard intent parsing and file analysis...")
    prompt = build_intent_prompt(feature_request, context_analysis, file_contents, project_spec)
    
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
            print("  ✓ Standard analysis complete")
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
    
    # STEP 3: Plan new files needed based on detected entities and framework
    print("\n  📋 Step 3: Planning new files for implementation...")
    new_files_planning = None
    new_files = []
    
    if detected_entities or deep_analysis_result:
        try:
            print(f"    🤖 Inferring new files for {len(detected_entities)} detected entities...")
            # Pass analysis_model as subagent_model so it can generate framework-specific files
            new_files_planning = infer_new_files_needed(
                feature_request=feature_request,
                context_analysis=context_analysis,
                framework=detected_framework,
                affected_files=affected_files,
                llm_response=response_text,
                project_spec=project_spec,
                analysis_model=analysis_model  # ✓ Pass the model for subagent planning
            )
            
            if new_files_planning and new_files_planning.suggested_files:
                # Extract file paths from suggestions
                for file_suggestion in new_files_planning.suggested_files:
                    file_path = os.path.join(
                        file_suggestion.relative_path if isinstance(file_suggestion.relative_path, str) else "/".join(file_suggestion.relative_path),
                        file_suggestion.filename
                    )
                    new_files.append(file_path)
                
                print(f"    ✓ Planned {len(new_files)} new files for creation")
                for nf in new_files[:8]:
                    print(f"      - {nf}")
                if len(new_files) > 8:
                    print(f"      ... and {len(new_files) - 8} more")
            else:
                print("    ℹ️ No specific new files planned from suggestions")
        
        except Exception as e:
            print(f"    ⚠️ New files planning failed: {str(e)[:150]}")
            new_files_planning = None
            new_files = []
    else:
        print("    ℹ️ No entities detected - skipping new files planning")
    
    # STEP 4: Generate structured todo list
    print("\n  📋 Step 4: Generating structured todo list...")
    todo_list = None
    try:
        todo_list = generate_structured_todos(
            feature_request=feature_request,
            framework=detected_framework,
            affected_files=affected_files,
            new_files=new_files
        )
        if todo_list:
            print(f"    ✓ Generated {todo_list.total_tasks} structured tasks")
            print(f"      - Completed: {todo_list.completed_tasks}")
            print(f"      - In Progress: {todo_list.in_progress_tasks}")
            print(f"      - Pending: {todo_list.pending_tasks}")
    except Exception as e:
        print(f"    ⚠️ Todo list generation failed: {e}")
        todo_list = None
    
    # Create FeatureSpec with all analysis results
    spec = FeatureSpec(
        feature_name=feature_request[:100] if feature_request else "Unknown Feature",
        intent_summary=feature_request[:300] if feature_request else "",
        affected_files=affected_files,
        new_files=new_files,
        new_files_planning=new_files_planning,
        modifications=[
            {
                "description": f"{t.get('content', 'Task')}",
                "type": t.get('status', 'pending')
            }
            for t in todos_found
        ] if todos_found else [],
        notes="Generated by intent parsing phase",
        todo_list=todo_list
    )
    
    # Set the feature spec in state
    state["feature_spec"] = spec
    
    # Set current phase
    state["current_phase"] = "intent_parsed"
    
    return state


def infer_new_files_needed(
    feature_request: str,
    context_analysis: str,
    framework: Optional[Any],
    affected_files: List[str],
    llm_response: Optional[str] = None,
    project_spec: Optional[ProjectSpec] = None,
    analysis_model: Optional[Any] = None
) -> NewFilesPlanningSuggestion:
    """
    Infer what new files need to be created for a feature based on the request and framework.
    Uses LLM domain reasoning to identify entities dynamically instead of hardcoded keywords.
    Performs deep spec reasoning to identify ALL features mentioned.
    
    Args:
        feature_request: The feature request text
        context_analysis: Context analysis from Phase 1
        framework: Detected framework (e.g., "FrameworkType.SPRING_BOOT")
        affected_files: Files that will be affected
        llm_response: LLM response containing domain analysis and entity identification
        project_spec: Project specification loaded from markdown files
        
    Returns:
        NewFilesPlanningSuggestion with detailed file planning
    """
    import re
    import json
    
    request_lower = feature_request.lower()
    
    # Deep spec reasoning: extract ALL entities mentioned in the spec
    spec_entities = extract_entities_from_spec(feature_request)
    
    # Use spec-based entities as primary source (deep reasoning from spec)
    detected_entities = spec_entities['entities']
    
    # If spec reasoning found entities, use them; otherwise fallback to LLM or keyword extraction
    if not detected_entities:
        # Extract entities from LLM response if available
        detected_entities_from_llm = []
    
        if llm_response:
            # Try to extract domain entities from LLM reasoning
            response_lower = llm_response.lower()
            
            # Look for entity mentions in the LLM response
            # Common patterns: "entities: Book, Author, Publisher" or "Book, Author, ISBN"
            
            # First try to parse JSON response for structured domain analysis
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group())
                    
                    # Extract entities from structured JSON
                    if "entities" in json_data:
                        for entity in json_data["entities"]:
                            if "name" in entity:
                                detected_entities_from_llm.append(entity["name"])
                    
                    # If no entities in JSON, try domain-specific extraction
                    if not detected_entities_from_llm and "domain_analysis" in json_data:
                        domain = json_data["domain_analysis"].get("identified_domain", "").lower()
                        
                        # Use domain-aware entity extraction instead of hardcoded domains
                        # Extract entities based on common business domains dynamically
                        if any(keyword in domain for keyword in ["library", "book", "literature", "publishing"]):
                            detected_entities_from_llm.extend(["Book", "Author", "Publisher", "Genre"])
                        elif any(keyword in domain for keyword in ["banking", "finance", "financial", "money", "account"]):
                            detected_entities_from_llm.extend(["Account", "Transaction", "Customer"])
                        elif any(keyword in domain for keyword in ["inventory", "retail", "ecommerce", "shopping", "product"]):
                            detected_entities_from_llm.extend(["Product", "Category", "Supplier"])
                        elif any(keyword in domain for keyword in ["healthcare", "medical", "hospital", "patient"]):
                            detected_entities_from_llm.extend(["Patient", "Doctor", "Appointment", "Prescription"])
                        elif any(keyword in domain for keyword in ["education", "school", "university", "student"]):
                            detected_entities_from_llm.extend(["Student", "Course", "Grade", "Enrollment"])
                        elif any(keyword in domain for keyword in ["hr", "human resources", "employee", "staff"]):
                            detected_entities_from_llm.extend(["Employee", "Department", "Position", "Salary"])
                        elif any(keyword in domain for keyword in ["logistics", "shipping", "delivery", "warehouse"]):
                            detected_entities_from_llm.extend(["Order", "Shipment", "Warehouse", "Vehicle"])
                        # Add more domain patterns as needed, but keep it extensible
            except (json.JSONDecodeError, KeyError):
                # Fallback to regex extraction if JSON parsing fails
                pass
            
            # Fallback regex patterns if JSON parsing didn't work
            if not detected_entities_from_llm:
                entity_patterns = [
                    r'entities?:?\s*([^.]+?)(?:\n|$)',
                    r'domain-specific.*?:?\s*([^.]+?)(?:\n|$)',
                    r'(?:book|author|publisher|isbn|genre|shelf|borrower|loan|account|transaction|customer|balance|loan|credit|product|category|supplier|stock|warehouse|order|patient|doctor|appointment|prescription|student|course|grade|enrollment)',
                ]
                
                for pattern in entity_patterns:
                    matches = re.findall(pattern, response_lower, re.IGNORECASE)
                    for match in matches:
                        # Extract individual entities from the match
                        words = re.findall(r'\b([A-Z][a-z]+)\b', match)
                        detected_entities_from_llm.extend(words)
            
            # Remove duplicates while preserving order
            detected_entities_from_llm = list(dict.fromkeys(detected_entities_from_llm))
            detected_entities = detected_entities_from_llm
        
        # Fallback to old logic if no entities found from LLM
        if not detected_entities:
            # Extract entity names from feature request using old method
            entity_keywords = ["inventory", "product", "user", "order", "item", "customer", "category", "payment", "cart", "voucher", "admin", "auth", "login", "account", "profile"]
            
            for entity in entity_keywords:
                if entity in request_lower:
                    detected_entities.append(entity.title())  # Title case for class names
            
            # If no specific entities detected, try to extract from common patterns
            if not detected_entities:
                # Look for capitalized words that might be entity names
                words = re.findall(r'\b[A-Z][a-z]+\b', feature_request)
                detected_entities = list(set(words))[:3]  # Take up to 3 unique entities
        
        # Default to "Book" for book management, or "Inventory" if still no entities found
        if not detected_entities:
            if "book" in request_lower:
                detected_entities = ["Book"]
            else:
                detected_entities = ["Inventory"]
    
    # Use detected entities as primary source
    # (Note: primary_entity no longer needed as we iterate through ALL detected_entities)
    
    # Detect framework from context or parameter
    framework_str = str(framework).lower() if framework else "generic"

    # Use subagent for dynamic framework planning instead of hardcoded logic
    # WHY SUBAGENT: This isolates complex multi-step planning work from main agent context
    # Prevents context bloat when analyzing multiple frameworks and their conventions
    try:
        print("  🤖 Using subagent for dynamic framework planning (context isolation)...")
        framework_str = str(framework) if framework else "Generic"
        return plan_files_with_subagent(
            feature_request=feature_request,
            detected_entities=detected_entities,
            framework=framework_str,
            context_analysis=context_analysis,
            project_spec=project_spec,
            subagent_model=analysis_model  # ✓ Pass the LLM model for framework-specific planning
        )
    except Exception as e:
        print(f"  ⚠️  Subagent planning failed: {e}")
        print("  📋 Falling back to basic file structure...")
        framework_str = str(framework) if framework else "Generic"
        return _create_basic_file_structure(
            detected_entities=detected_entities,
            framework=framework_str
        )    # Generate structured todo list for user tracking


# ==============================================================================
# ALTERNATIVE: INTENT PARSER AGENT (DeepAgent version)
# ==============================================================================

def build_comprehensive_spec_analysis_prompt(
    feature_request: str,
    context_analysis: str = "",
    project_spec: Optional[ProjectSpec] = None
) -> str:
    """
    Build a detailed prompt for deep specification analysis BEFORE implementation planning.
    This prompt helps agent reason deeply about specification to:
    - Identify ALL features mentioned (not just first keyword)
    - Understand relationships between features
    - Recognize domain-specific patterns
    - Create comprehensive implementation plan spanning all features
    
    Args:
        feature_request: The full feature specification
        context_analysis: Context from codebase analysis
        project_spec: Project specification from markdown files
        
    Returns:
        Comprehensive analysis prompt for DeepAgent
    """
    
    project_context = ""
    if project_spec:
        project_context = f"""
PROJECT SPECIFICATIONS:
- Project: {project_spec.project_name}
- Purpose: {project_spec.purpose}
- Framework: {project_spec.framework}
- Language: {project_spec.language}
- Build Tool: {project_spec.build_tool}
- Modules: {', '.join(project_spec.modules) if project_spec.modules else 'Not specified'}

Architecture Notes:
{chr(10).join(f"  - {note}" for note in (project_spec.architecture_notes or [])) or "  Not specified"}

Code Style Rules:
{chr(10).join(f"  - {rule}" for rule in (project_spec.code_style_rules or [])) or "  Not specified"}

Dependencies:
{chr(10).join(f"  - {dep}" for dep in (project_spec.dependencies or [])) or "  Not specified"}

Testing Guidelines:
{chr(10).join(f"  - {guideline}" for guideline in (project_spec.testing_guidelines or [])) or "  Not specified"}

Don't Do List (AVOID):
{chr(10).join(f"  - {item}" for item in (project_spec.dont_do_list or [])) or "  Not specified"}
"""
    
    prompt = f"""
You are a Principal Architect and Domain Expert analyzing a comprehensive feature specification.

Your goal: Perform DEEP REASONING about the specification BEFORE planning implementation.

{'CODEBASE CONTEXT:' + chr(10) + context_analysis if context_analysis else ""}

{project_context}

FEATURE SPECIFICATION TO ANALYZE:
{feature_request}

---

DEEP ANALYSIS PROCESS (Think step-by-step, showing your reasoning):

### STEP 1: COMPREHENSIVE FEATURE IDENTIFICATION
- What are ALL the features/use cases mentioned in this specification?
- Don't just scan the first keyword - read the ENTIRE specification carefully
- List each feature area explicitly, even if they appear to be related to one domain
- Example: For an inventory system, identify SEPARATE feature areas like:
  * Product Management (Feature Area 1)
  * Category Management (Feature Area 2)
  * Inventory Operations (Feature Area 3)
  These may be related but are distinct implementation areas

**Questions to ask yourself:**
- How many distinct business processes does this specification describe?
- What are the main nouns (entities/resources) mentioned? (Product, Category, Inventory, etc.)
- What operations apply to each entity? (CRUD operations, validations, workflows)
- Are there sub-systems or specialized areas within the specification?

### STEP 2: ENTITY & RELATIONSHIP MAPPING
- For each feature area identified, what are the core business entities?
- What are the relationships between entities?
- What are the constraints and validation rules?
- What workflows involve multiple entities?

**For each feature area, create a mini-specification:**
- Entity Name: [exact name as mentioned in spec]
- Purpose: [what business problem it solves]
- Operations: [CRUD operations + special operations]
- Relationships: [how it relates to other entities]
- Validation Rules: [business constraints]
- Special Features: [audit trails, timestamps, soft deletes, etc.]

### STEP 3: ARCHITECTURE & LAYERING IMPACT
- How would each feature area impact the application architecture?
- Are there shared concerns across feature areas?
- What's the dependency order? (Should some be built before others?)
- Are there integration points between features?

### STEP 4: IMPLEMENTATION STRATEGY (PHASED APPROACH)
- Should these feature areas be implemented in parallel or sequence?
- What's the optimal build order based on dependencies?
- Which feature area is the foundation (Phase 1)?
- What builds on top of the foundation?

**Propose a phase-based strategy:**
- Phase 1: [Foundation feature area and why]
- Phase 2: [Next feature area that depends on Phase 1]
- Phase 3: [Integration and additional features]
- Phase 4+: [Additional features, if any]

### STEP 5: SOLID PRINCIPLES APPLICATION
- How would you apply each SOLID principle to this multi-feature system?
- SRP: Separate concerns → What goes in each class/service?
- OCP: Open/Closed → How to handle future extensions per feature?
- LSP: Liskov Substitution → Any abstract base patterns?
- ISP: Interface Segregation → What specific interfaces per feature?
- DIP: Dependency Inversion → What depends on what?

### STEP 6: COMPREHENSIVE TODO BREAKDOWN
- For each feature area, break down into:
  1. Analysis & Design tasks
  2. Core Entity/Model tasks
  3. Repository/Persistence tasks
  4. Service/Business Logic tasks
  5. Controller/API tasks
  6. Testing tasks
  7. Integration tasks

- **CRITICAL**: Identify cross-feature dependencies (e.g., Category needed before Product inventory operations)

---

RETURN YOUR ANALYSIS IN THIS JSON FORMAT:

{{
  "deep_analysis": {{
    "specification_summary": "string - 1-2 sentence summary of what this spec describes",
    "feature_count": "number - how many distinct feature areas",
    "complexity_assessment": "simple|moderate|complex - overall complexity",
    "integration_points": "number - how many integration points between features"
  }},
  "identified_features": [
    {{
      "feature_name": "string - name of feature area (e.g., 'Product Management')",
      "priority": "phase1|phase2|phase3|phase4 - implementation phase",
      "core_entities": ["array of entity names"],
      "operations": ["array of operations - CRUD, validations, etc"],
      "dependencies": ["array of feature names this depends on"],
      "estimated_tasks": "number - rough estimate of tasks needed",
      "key_patterns": ["array of design patterns applicable"]
    }}
  ],
  "entity_map": {{
    "entity_name": {{
      "description": "business meaning",
      "primary_feature_area": "which feature area owns this entity",
      "relationships": ["entity names this relates to"],
      "operations": ["CRUD and special operations"]
    }}
  }},
  "implementation_phases": [
    {{
      "phase_number": 1,
      "phase_name": "string - descriptive name",
      "feature_areas": ["array of feature areas"],
      "rationale": "why these are Phase 1",
      "deliverables": ["key deliverables"],
      "estimated_effort": "small|medium|large|xlarge"
    }}
  ],
  "solid_principles_plan": {{
    "srp_separation": ["what classes/services for separation of concerns"],
    "ocp_extension_points": ["how to make system open for extension"],
    "lsp_patterns": ["any base patterns or inheritance"],
    "isp_interfaces": ["key interfaces for feature areas"],
    "dip_abstractions": ["key abstractions to depend on"]
  }},
  "todo_structure": {{
    "total_estimated_tasks": "number - total across all phases",
    "phases": [
      {{
        "phase": "analysis|planning|validation|generation|execution|testing|review",
        "feature_area": "string - which feature area",
        "task_count": "number",
        "key_tasks": ["array of main tasks"]
      }}
    ]
  }},
  "risk_assessment": {{
    "potential_issues": ["array of risks"],
    "mitigation": ["array of mitigation strategies"],
    "integration_risks": ["array of integration risks if any"]
  }},
  "clarifying_questions": [
    "array of questions that need clarification from product owner"
  ]
}}

CRITICAL REMINDERS:
- Do NOT leave any feature mentioned in the spec unanalyzed
- Perform DEEP reasoning - show your thinking process
- Identify ALL entities, not just obvious ones
- Consider relationships and dependencies
- Return ONLY the JSON response, no other text
- Ensure JSON is valid and properly formatted
"""
    
    return prompt


def create_spec_analyzer_agent(analysis_model: Any):
    """
    Create a DeepAgent specialized in deep specification analysis.
    This agent performs comprehensive reasoning about feature specifications
    BEFORE implementation planning.
    
    Args:
        analysis_model: LLM model instance
        
    Returns:
        DeepAgent instance for spec analysis
    """
    if not analysis_model:
        raise ValueError("Analysis model not provided")
    
    system_prompt = """You are a Principal Solutions Architect specializing in deep specification analysis.

Your expertise:
- Domain-driven design and business domain understanding
- Feature decomposition and scope management
- Architecture pattern recognition
- SOLID principles application
- Multi-feature integration planning

Your role: Analyze feature specifications comprehensively BEFORE implementation.

For each specification:
1. Identify ALL distinct feature areas (read carefully - don't miss any)
2. Map entities and their relationships
3. Understand business workflows and constraints
4. Plan phased implementation based on dependencies
5. Apply SOLID principles to guide architecture
6. Provide comprehensive task breakdown

Think DEEPLY about the specification. Consider:
- Hidden complexity and integration points
- Domain-specific patterns and conventions
- Architectural implications of feature interactions
- Long-term maintainability and extensibility

Provide structured analysis that helps developers understand EXACTLY what to build."""
    
    return create_deep_agent(
        system_prompt=system_prompt,
        model=analysis_model
    )


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


if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Environment variables loaded from .env")
    except ImportError:
        print("⚠️ python-dotenv not installed, using system environment variables")

    # Setup model for standalone execution (same as orchestrator)
    try:
        from models import setup_model
        model_name, temperature, analysis_model = setup_model()
        print(f"✓ Model initialized: {model_name} (temp: {temperature})")
    except Exception as e:
        print(f"⚠️ Model setup failed: {e} - will use rule-based fallback")
        analysis_model = None

    parser = argparse.ArgumentParser(description='Parse intent from feature request')
    parser.add_argument('--codebase-path', required=True, help='Path to analyze')
    parser.add_argument('--feature-request', help='Feature request text')
    parser.add_argument('--feature-request-spec', help='Path to markdown file containing feature request specification')
    parser.add_argument('--context-analysis', help='Context analysis from Phase 1 (optional)')
    
    args = parser.parse_args()
    
    # Validate that either feature-request or feature-request-spec is provided
    if not args.feature_request and not args.feature_request_spec:
        parser.error("Either --feature-request or --feature-request-spec must be provided")
    
    if args.feature_request and args.feature_request_spec:
        parser.error("Cannot specify both --feature-request and --feature-request-spec")
    
    # Read feature request from file if specified
    feature_request = args.feature_request
    if args.feature_request_spec:
        try:
            with open(args.feature_request_spec, 'r', encoding='utf-8') as f:
                full_content = f.read().strip()
            
            # Check if there's a "## 🎯 Feature Request" section
            if "## 🎯 Feature Request" in full_content:
                # Extract the Feature Request section
                sections = full_content.split("## 🎯 Feature Request")
                if len(sections) > 1:
                    feature_section = sections[1].split("---")[0].strip()  # Take until separator
                    # Remove the header and clean up
                    feature_request = feature_section.replace("## 🎯 Feature Request", "").strip()
                    print("✓ Loaded feature request from '## 🎯 Feature Request' section")
                else:
                    feature_request = full_content
                    print(f"✓ Loaded entire feature request spec from: {args.feature_request_spec}")
            else:
                feature_request = full_content
                print(f"✓ Loaded entire feature request spec from: {args.feature_request_spec}")
                
        except Exception as e:
            print(f"❌ Failed to read feature request spec from {args.feature_request_spec}: {e}")
            import sys
            sys.exit(1)

    # Read actual files from codebase for proper file_map
    file_map = {}
    try:
        import os
        # Scan for Java files in the codebase
        for root, dirs, files in os.walk(args.codebase_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules', 'target', '.idea', '.vscode']]
            
            for file in files:
                if file.endswith('.java'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, args.codebase_path)
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            file_map[rel_path] = {
                                "content": content,
                                "language": "java",
                                "size": len(content)
                            }
                    except Exception as e:
                        print(f"Warning: Could not read {rel_path}: {e}")
        
        print(f"✓ Loaded {len(file_map)} files from codebase")
    except Exception as e:
        print(f"⚠️ Failed to load files from codebase: {e}")
        file_map = {}

    # Create initial state
    state = {
        "codebase_path": args.codebase_path,
        "feature_request": feature_request,
        "context_analysis": args.context_analysis or "",
        "full_analysis": {
            "file_map": file_map,  # ✓ ADD ACTUAL FILE CONTENTS
            "reasoning": {
                "request_type": "unknown",
                "entities": [],
                "actions": [],
                "technologies": [],
                "scope": "full",
                "priority_areas": [],
                "estimated_complexity": "medium",
                "llm_insights": ""
            },
            "analysis_plan": {
                "analyses_to_run": [
                    "basic_filesystem_scan",
                    "tag_extraction",
                    "dependency_analysis",
                    "api_patterns",
                    "structure_analysis"
                ],
                "token_budget": {
                    "basic_filesystem_scan": 409,
                    "tag_extraction": 409,
                    "dependency_analysis": 409,
                    "api_patterns": 409,
                    "structure_analysis": 409
                },
                "focus_files": [],
                "skip_analyses": []
            },
            "results": {
                "basic_info": {
                    "project_type": "Java/Maven",
                    "framework": "Spring Boot",
                    "tech_stack": [
                        f"Java ({len(file_map)} files)"
                    ],
                    "main_dirs": [
                        "target",
                        "src"
                    ],
                    "key_files": [],
                    "source_files_count": len(file_map)
                },
                "code_analysis": {
                    "tags_by_file": {},
                    "definitions": {},
                    "references": {},
                    "total_tags": 0
                },
                "dependencies": {
                    "external_libs": [],
                    "internal_modules": [],
                    "frameworks_detected": [],
                    "database_drivers": [],
                    "api_clients": []
                },
                "api_patterns": {
                    "endpoints": [],
                    "http_methods": [],
                    "api_frameworks": [],
                    "database_patterns": [],
                    "middleware_patterns": []
                },
                "structure": {
                    "entry_points": [],
                    "config_files": [],
                    "test_directories": [],
                    "source_directories": [],
                    "architecture_patterns": []
                }
            },
            "summary": f"🎯 ANALYSIS FOR: Unknown\n📊 Scope: full | Complexity: medium\n🎯 Focus Areas: \n\n🏗️ PROJECT OVERVIEW:\n  • Type: Java/Maven\n  • Framework: Spring Boot\n  • Tech Stack: Java ({len(file_map)} files)\n  • Source Files: {len(file_map)}\n\n📝 CODE ANALYSIS:\n  • Files Loaded: {len(file_map)}\n\n🎫 ANALYSIS COMPLETE | Tokens Used: 0",
            "tokens_used": 0
        },
        "errors": []
    }

    # Run intent parsing
    result_state = flow_parse_intent(state, analysis_model=analysis_model)

    print("\n🎯 INTENT PARSING RESULTS:")
    print("=" * 60)

    # Display feature spec
    feature_spec = result_state.get("feature_spec")
    if feature_spec:
        print("📋 FEATURE SPECIFICATION:")
        print(f"  • Feature Name: {feature_spec.feature_name}")
        print(f"  • Intent Summary: {feature_spec.intent_summary}")
        print(f"  • Framework: {result_state.get('framework', 'Unknown')}")
        print(f"  • Affected Files: {len(feature_spec.affected_files)}")
        for af in feature_spec.affected_files[:5]:
            print(f"    - {af}")
        if len(feature_spec.affected_files) > 15:
            print(f"    ... and {len(feature_spec.affected_files) - 5} more")
        print(f"  • New Files: {len(feature_spec.new_files)}")
        for nf in feature_spec.new_files[:5]:
            print(f"    - {nf}")
        if len(feature_spec.new_files) > 5:
            print(f"    ... and {len(feature_spec.new_files) - 5} more")
        print()

        # Display todo list summary
        if feature_spec.todo_list:
            todo_list = feature_spec.todo_list
            print("📊 TODO LIST SUMMARY:")
            print(f"  • Total Tasks: {todo_list.total_tasks}")
            print(f"  • Completed: {todo_list.completed_tasks}")
            print(f"  • In Progress: {todo_list.in_progress_tasks}")
            print(f"  • Pending: {todo_list.pending_tasks}")
            print(f"  • Framework: {todo_list.framework or 'Generic'}")
            print()

    # Display errors if any
    if result_state.get("errors"):
        print("❌ ERRORS:")
        for error in result_state["errors"]:
            print(f"  • {error}")
        print()

    # Display current phase
    print(f"🏁 CURRENT PHASE: {result_state.get('current_phase', 'unknown')}")

    print("\n🛠️ FULL ANALYSIS DETAILS:")
    # print(json.dumps(result_state, indent=2, default=str))
    print()

    print("\n✅ Intent parsing analysis completed successfully!")

    """_summary_
    Example usage:

    # Using feature request text directly:
    source .venv/bin/activate && python3 scripts/coding_agent/flow_parse_intent.py --codebase-path dataset/codes/springboot-demo --feature-request "Add inventory management system..." --context-analysis "Spring Boot project..."
    
    # Using feature request from markdown file:
    source .venv/bin/activate && python3 scripts/coding_agent/flow_parse_intent.py --codebase-path dataset/codes/springboot-demo --feature-request-spec scripts/coding_agent/studio.md --context-analysis "Spring Boot project..."
    """
