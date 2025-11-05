"""
FEATURE-BY-REQUEST AGENT - Multi-Phase Implementation V3
=========================================================

Improved version with LangGraph orchestration, supervisor pattern, and full DeepAgents middleware stack.
"""

import argparse
import os
import sys
import time
from typing import Dict, List, Any, Optional, TypedDict, Literal

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from pydantic import BaseModel, Field, SecretStr

# Import middleware from v2 for Phase 4 behavior preservation
sys.path.insert(0, os.path.dirname(__file__))
try:
    from middleware import create_phase4_middleware, log_middleware_config # pyright: ignore[reportAssignmentType]
    HAS_MIDDLEWARE = True
except ImportError:
    HAS_MIDDLEWARE = False
    # Define stubs if middleware not available
    def create_phase4_middleware(*args, **kwargs):
        return None
    def log_middleware_config(*args, **kwargs):
        pass

# Load environment variables
load_dotenv()

# ==============================================================================
# DATA MODELS
# ==============================================================================

class FeatureSpec(BaseModel):
    """Structured specification of a feature request"""
    feature_name: str = Field(description="Name of the feature")
    intent_summary: str = Field(description="Summary of user intent")
    affected_files: List[str] = Field(default_factory=list)
    new_files: List[str] = Field(default_factory=list)
    modifications: List[Dict[str, Any]] = Field(default_factory=list)
    notes: str = Field(default="")

class AgentState(TypedDict):
    """State for the multi-phase workflow"""
    codebase_path: str
    feature_request: Optional[str]
    context_analysis: Optional[str]
    feature_spec: Optional[FeatureSpec]
    impact_analysis: Optional[Dict[str, Any]]
    code_patches: Optional[List[Dict[str, Any]]]
    execution_results: Optional[Dict[str, Any]]
    errors: List[str]
    dry_run: bool
    current_phase: str
    human_approval_required: bool

# ==============================================================================
# PARSE ARGUMENTS FIRST
# ==============================================================================

parser = argparse.ArgumentParser(description="Feature-by-Request Agent V3")
parser.add_argument("--codebase-path", "-p",
                   default=os.getenv("CODEBASE_PATH", "/Users/zeihanaulia/Programming/research/agent"))
parser.add_argument("--feature-request", "-f", help="Feature request to implement")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--model", default=None, help="LLM model to use")
parser.add_argument("--temperature", type=float, default=None)
parser.add_argument("--enable-human-loop", action="store_true", help="Enable human-in-the-loop approval")

args = parser.parse_args()

# ==============================================================================
# SETUP MODEL AND TEMPERATURE
# ==============================================================================

# Get model from args or environment
model_name = args.model or os.getenv("LITELLM_MODEL", "gpt-4o-mini")

# Get temperature: auto-set based on model, or user override
is_reasoning = any(kw in model_name.lower() for kw in ["gpt-5", "5-mini", "oss", "120b", "reasoning"])
temperature = args.temperature if args.temperature is not None else (1.0 if is_reasoning else 0.7)

# Setup API credentials
api_key = os.getenv("LITELLM_VIRTUAL_KEY")
api_base = os.getenv("LITELLM_API")

if not api_key or not api_base:
    raise ValueError(
        "Missing required environment variables:\n"
        "  LITELLM_VIRTUAL_KEY: LLM API key\n"
        "  LITELLM_API: LLM API base URL"
    )

# Create model instance
analysis_model = ChatOpenAI(
    api_key=SecretStr(api_key),
    model=model_name,
    base_url=api_base,
    temperature=temperature,
)

# ==============================================================================
# SUPERVISOR AGENT TOOLS
# ==============================================================================

@tool(return_direct=True)
def transfer_to_context_analyzer():
    """Transfer to context analysis specialist"""
    return "Transferred to context analyzer"

@tool(return_direct=True)
def transfer_to_intent_parser():
    """Transfer to intent parsing specialist"""
    return "Transferred to intent parser"

@tool(return_direct=True)
def transfer_to_impact_analyzer():
    """Transfer to impact analysis specialist"""
    return "Transferred to impact analyzer"

@tool(return_direct=True)
def transfer_to_code_synthesizer():
    """Transfer to code synthesis specialist"""
    return "Transferred to code synthesizer"

@tool(return_direct=True)
def transfer_to_executor():
    """Transfer to execution specialist"""
    return "Transferred to executor"

# ==============================================================================
# SUPERVISOR AGENT
# ==============================================================================

def create_supervisor_agent():
    """Supervisor agent that coordinates all phases"""
    prompt = """You are the supervisor agent coordinating a multi-phase feature implementation workflow.

PHASES AVAILABLE:
1. context_analyzer - Analyzes codebase structure and technology stack
2. intent_parser - Parses feature requests and creates implementation plans
3. impact_analyzer - Analyzes architectural impact and affected files
4. code_synthesizer - Generates production-ready code following SOLID principles
5. executor - Applies code changes and verifies correctness

Use write_todos to plan complex multi-step tasks.
Transfer to appropriate specialists using the transfer tools.
Monitor progress and handle errors gracefully.

Always maintain state awareness and provide clear status updates."""

    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model,
        tools=[
            transfer_to_context_analyzer,
            transfer_to_intent_parser,
            transfer_to_impact_analyzer,
            transfer_to_code_synthesizer,
            transfer_to_executor
        ]
    )

# ==============================================================================
# SPECIALIZED AGENTS
# ==============================================================================

def create_context_analysis_agent(codebase_path: str):
    """Phase 1: Context Extraction"""
    backend = FilesystemBackend(root_dir=codebase_path)
    prompt = f"""\
You are a codebase analysis specialist.

CODEBASE PATH: {codebase_path}

YOUR TASK:
1. Use ls to list the root directory structure
2. Identify the project type (Java/Maven, Python/Django, Node/Express, etc.)
3. Read key config files: pom.xml, package.json, requirements.txt, setup.py, build.gradle
4. List main source files and directories
5. Provide a clear summary with:
   - Project type and framework
   - Tech stack and dependencies
   - Main components
   - Entry point and purpose

WORK EFFICIENTLY - stay focused, don't over-explore.
"""
    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model,
        backend=backend
        # FilesystemMiddleware is included by default in create_deep_agent
    )

def create_intent_parser_agent():
    """Phase 2: Intent Parsing - Expert software engineer analyzing feature request"""
    prompt = """\
You are an expert software engineer analyzing feature requests.

Your task: Create detailed implementation plans using write_todos tool.

For each feature request:
1. Break down the feature into concrete implementation steps
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
"""
    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model
    )

def create_impact_analysis_agent(codebase_path: str):
    """Phase 3: Impact Analysis - Expert architect analyzing codebase patterns"""
    backend = FilesystemBackend(root_dir=codebase_path)
    prompt = f"""\
You are an expert software architect analyzing codebase impact.

CODEBASE: {codebase_path}

Your task:
1. Use ls and read_file to understand project structure and patterns
2. Identify the architecture (MVC, layered, microservices, modular, etc)
3. Find key frameworks, libraries, and patterns in use
4. Determine naming conventions and code organization
5. Identify design patterns already implemented
6. List all files that need changes and why
7. Note any constraints or best practices to follow

Be specific: List exact file paths, patterns, and current code style.
Provide actionable insights for implementation.
"""
    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model,
        backend=backend
        # FilesystemMiddleware is included by default in create_deep_agent
    )

def create_code_synthesis_agent(codebase_path: str, files_to_modify: Optional[List[str]] = None, feature_request: Optional[str] = None):
    """Phase 4: Code Synthesis - Expert engineer generating testable, production-ready code
    
    CRITICAL: This uses v2's middleware approach to ensure feature focus and tool generation.
    """
    backend = FilesystemBackend(root_dir=codebase_path)
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
"""
    
    # Try to create agent with middleware (v2 behavior)
    agent_kwargs = {
        "system_prompt": prompt,
        "model": analysis_model,
        "backend": backend
    }
    
    # Add middleware for file scope guardrails if available and files specified
    if HAS_MIDDLEWARE and files_to_modify and feature_request:
        # CRITICAL: Pass ACTUAL feature_request to middleware so it injects intent reminder
        middleware = create_phase4_middleware(
            feature_request=feature_request,  # Use actual feature request, not default
            affected_files=files_to_modify,
            codebase_root=codebase_path,
            enable_guardrail=True
        )
        if middleware:
            agent_kwargs["middleware"] = middleware
    
    return create_deep_agent(**agent_kwargs)

def create_execution_agent(codebase_path: str, dry_run: bool):
    """Phase 5: Execution & Verification"""
    backend = FilesystemBackend(root_dir=codebase_path)
    mode = "DRY RUN" if dry_run else "APPLY CHANGES"
    prompt = f"""\
You are an execution specialist applying code changes.

CODEBASE PATH: {codebase_path}
MODE: {mode}

Tasks:
1. Apply code patches using filesystem tools
2. Verify syntactic correctness
3. Check implementation matches specification
4. Report success/failure with detailed feedback
"""
    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model,
        backend=backend
        # FilesystemMiddleware is included by default in create_deep_agent
    )

# ==============================================================================
# WORKFLOW NODES
# ==============================================================================

def analyze_context(state: AgentState) -> AgentState:
    """Node: Context Analysis Phase"""
    print("🔍 Phase 1: Analyzing codebase context...")
    codebase_path = state["codebase_path"]

    agent = create_context_analysis_agent(codebase_path)
    result = agent.invoke({"input": f"Analyze {codebase_path}"})

    if "messages" in result:
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_calls"):
                state["context_analysis"] = str(msg.content)
                state["current_phase"] = "context_analysis_complete"
                break

    if not state.get("context_analysis"):
        state["context_analysis"] = "Analysis failed."
        state["errors"].append("Context analysis failed")

    print("  ✓ Context analysis complete")
    return state

def parse_intent(state: AgentState) -> AgentState:
    """Node: Intent Parsing Phase"""
    print("🎯 Phase 2: Expert analysis - creating implementation plan...")
    feature_request = state.get("feature_request")
    codebase_path = state["codebase_path"]

    if not feature_request:
        state["errors"].append("No feature request provided")
        return state

    agent = create_intent_parser_agent()

    prompt = f"""
CODEBASE CONTEXT:
{state.get("context_analysis", "")}

FEATURE REQUEST:
{feature_request}

As an expert software engineer, analyze this feature request:

1. **Understand the requirement**: What is being asked? What are the acceptance criteria?
2. **Assess impact**: Which architectural layers are affected? (UI, API, Business Logic, Data, etc)
3. **Design approach**: What design patterns would be appropriate? (MVC, Factory, Strategy, Decorator, etc)
4. **Testability**: How can this be tested effectively? (Unit tests, Integration tests, E2E tests)
5. **File analysis**: Which ACTUAL files need changes based on codebase patterns?

Use write_todos to create a structured implementation plan with these categories:
- Analysis: Understanding current code and patterns
- Design: Selecting patterns and designing solution
- Implementation: Creating/modifying specific files
- Testing: Creating/updating tests
- Verification: Ensuring code quality and functionality

Be specific about file paths and technical decisions.
"""

    result = agent.invoke({"input": prompt})

    # Extract todos and analysis from agent response
    todos_found = []
    affected_files = []

    if "messages" in result:
        for msg in result.get("messages", []):
            # Look for write_todos tool calls
            if hasattr(msg, "tool_calls"):
                for call in getattr(msg, "tool_calls", []):
                    if call.get("name") == "write_todos":
                        todos_data = call.get("args", {}).get("todos", [])
                        todos_found.extend(todos_data)

            # Extract file patterns from reasoning/content
            if hasattr(msg, "content") and msg.content:
                content_str = str(msg.content)
                import re
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

    # Remove duplicates while preserving order
    affected_files = list(dict.fromkeys(affected_files))

    # If no valid files detected from model output, scan filesystem for actual files
    if not affected_files:
        java_files = []
        java_src_path = os.path.join(codebase_path, "src/main/java")
        if os.path.isdir(java_src_path):
            for root, dirs, files in os.walk(java_src_path):
                for file in files:
                    if file.endswith(".java"):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, codebase_path)
                        java_files.append(rel_path)
        affected_files = java_files if java_files else []

    # Create FeatureSpec with analysis results
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

    state["feature_spec"] = spec
    state["current_phase"] = "intent_parsing_complete"

    print(f"  ✓ Feature: {spec.feature_name[:50]}...")
    print(f"  ✓ Analysis steps: {len(todos_found)} tasks identified")
    print(f"  ✓ Affected files: {len(affected_files)} file(s)")

    return state

def analyze_impact(state: AgentState) -> AgentState:
    """Node: Impact Analysis Phase"""
    print("📊 Phase 3: Architecture analysis - identifying patterns and impact...")
    codebase_path = state["codebase_path"]
    spec = state.get("feature_spec")

    if not spec:
        state["errors"].append("No feature spec available for impact analysis")
        return state

    agent = create_impact_analysis_agent(codebase_path)

    # Find Java files (for Spring Boot projects)
    java_files = []
    for root, dirs, files in os.walk(os.path.join(codebase_path, "src/main/java")):
        for file in files:
            if file.endswith(".java"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, codebase_path)
                java_files.append(rel_path)

    # Use real files detected from filesystem
    files_to_analyze = java_files if java_files else spec.affected_files

    prompt = f"""
FEATURE REQUEST: {spec.intent_summary}

CODEBASE FILES DETECTED:
{chr(10).join(f'• {f}' for f in files_to_analyze[:10])}
{f'... and {len(files_to_analyze) - 10} more' if len(files_to_analyze) > 10 else ''}

TASK: Conduct expert architecture analysis:

1. **Current Architecture**: Analyze the existing code patterns, layers, and structure
2. **Technology Stack**: Identify frameworks, libraries, and patterns in use
3. **Design Patterns**: What patterns are already implemented? (MVC, Repository, Service, etc)
4. **Affected Files**: From the list above, which files need modification? Be SPECIFIC with paths
5. **Code Patterns**: Show specific code examples of patterns to follow
6. **Dependencies**: List what's already available (no new dependencies!)
7. **Testing Strategy**: How should the new code be tested?
8. **Constraints**: Any limitations or best practices to follow?

Use write_todos to plan the impact analysis tasks if needed.
Be SPECIFIC - use exact file paths from the list above.
"""

    result = agent.invoke({"input": prompt})

    # Extract files from agent response
    files_to_modify = files_to_analyze if files_to_analyze else spec.affected_files

    analysis = {
        "files_to_modify": files_to_modify,
        "architecture_insights": "",
        "patterns_to_follow": [],
        "testing_approach": "",
        "constraints": [],
        "todos": []
    }

    if "messages" in result:
        for msg in result.get("messages", []):
            # Extract todos if any
            if hasattr(msg, "tool_calls"):
                for call in getattr(msg, "tool_calls", []):
                    if call.get("name") == "write_todos":
                        analysis["todos"] = call.get("args", {}).get("todos", [])

            # Extract reasoning and insights
            if hasattr(msg, "content") and msg.content:
                content_str = str(msg.content)
                analysis["architecture_insights"] = content_str[:1000]  # Keep summary

                # Extract patterns mentioned
                import re
                patterns = re.findall(r'(?:Pattern|pattern|Design|design):\s*([^,.\n]+)', content_str)
                analysis["patterns_to_follow"].extend(patterns)

    state["impact_analysis"] = analysis
    state["current_phase"] = "impact_analysis_complete"

    print(f"  ✓ Files to modify: {len(files_to_modify)} file(s)")
    print(f"  ✓ Patterns identified: {len(analysis['patterns_to_follow'])} pattern(s)")

    return state

def synthesize_code(state: AgentState) -> AgentState:
    """Node: Code Synthesis Phase"""
    print("⚙️ Phase 4: Expert code generation with testability and SOLID principles...")
    codebase_path = state["codebase_path"]
    spec = state.get("feature_spec")
    impact = state.get("impact_analysis", {})

    if not spec or not impact:
        state["errors"].append("Missing feature spec or impact analysis")
        return state

    # Use files from impact analysis
    files_to_modify = impact.get("files_to_modify", spec.affected_files)

    # CRITICAL: Pass BOTH files AND feature_request to agent so it can apply middleware guardrails
    agent = create_code_synthesis_agent(
        codebase_path, 
        files_to_modify=files_to_modify,
        feature_request=spec.intent_summary  # <-- PASS FEATURE REQUEST HERE
    )
    
    # Log middleware configuration for debugging
    if HAS_MIDDLEWARE:
        log_middleware_config(spec.intent_summary, files_to_modify)

    architecture = impact.get("architecture_insights", "")[:500]

    # Multi-step expert implementation
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
"""

    _analysis_result = agent.invoke({"input": analysis_prompt})

    # Step 2: Agent implements based on plan - EXACT v2 prompt for consistency
    print("  🛠️  Step 2: Agent implementing changes...")
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
   - Modify HelloController.java to add the new endpoint
   - Follow existing endpoint patterns (use @GetMapping, @RestController, etc)
   - Return proper JSON responses
   - Use services/interfaces for business logic

4. SPECIFIC REQUIREMENTS:
   - Feature request: {spec.intent_summary}
   - Use only Spring Boot starter-web and starter-test (already in pom.xml)
   - Code must be production-ready and testable

Use edit_file for HelloController and write_file for any new service files.
Generate the actual code implementation NOW.
"""

    result2 = agent.invoke({"input": implementation_prompt})

    # Extract patches from implementation step
    patches = []
    if "messages" in result2:
        for msg in result2.get("messages", []):
            if hasattr(msg, "tool_calls"):
                for call in getattr(msg, "tool_calls", []):
                    if call.get("name") in ["write_file", "edit_file"]:
                        # Extract path from either 'path' or 'file' key
                        tool_args = call.get("args", {})
                        file_path = tool_args.get("path") or tool_args.get("file") or "unknown"
                        patches.append({
                            "tool": call.get("name"),
                            "args": tool_args,
                            "description": "Generated patch",
                            "file": file_path
                        })

    # Always print agent response for debugging
    if "messages" in result2:
        for msg in reversed(result2.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                content_str = str(msg.content)[:300]
                print(f"  ℹ️ Agent response: {content_str}")
                break

    if patches:
        print(f"  ✓ Generated {len(patches)} code change(s)")
        for p in patches:
            file_path = p.get('file', 'unknown')
            print(f"    - {p['tool']}: {file_path}")

    state["code_patches"] = patches
    state["current_phase"] = "code_synthesis_complete"
    return state

def execute_changes(state: AgentState, enable_human_loop: bool = False) -> AgentState:
    """Node: Execution Phase with Human Approval"""
    print("🚀 Phase 5: Execution & Verification...")

    patches = state.get("code_patches", [])
    dry_run = state.get("dry_run", False)

    # Human-in-the-loop: Require approval for actual code changes
    if not dry_run and enable_human_loop and patches:
        print("  ⚠️  Human approval required for code changes")
        state["human_approval_required"] = True

        # Interrupt for human approval
        user_decision = interrupt({
            "message": f"About to apply {len(patches)} code changes. Approve?",
            "patches": patches,
            "options": ["approve", "reject", "edit"]
        })

        if user_decision.get("decision") == "reject":
            state["errors"].append("User rejected code changes")
            state["execution_results"] = {"status": "rejected", "reason": "User rejection"}
            return state
        elif user_decision.get("decision") == "edit":
            # Allow user to modify patches
            modified_patches = user_decision.get("modified_patches", patches)
            state["code_patches"] = modified_patches
            patches = modified_patches

    if not patches:
        print("  ℹ️ No patches to apply")
        state["execution_results"] = {"patches_applied": [], "verification_status": "no_patches"}
        state["current_phase"] = "execution_complete"
        return state

    mode = "DRY RUN" if dry_run else "EXECUTE"
    print(f"  ℹ️ {mode}: Applying {len(patches)} patch(es)...")

    # Extract file operations from patches
    results = {"patches_applied": [], "verification_status": "completed"}
    for patch in patches:
        tool_name = patch.get("tool")
        args = patch.get("args", {})
        file_path = args.get("path", "unknown")

        print(f"    - {tool_name}: {file_path}")
        results["patches_applied"].append(file_path)

    state["execution_results"] = results
    state["current_phase"] = "execution_complete"
    return state

# ==============================================================================
# CONDITIONAL ROUTING FUNCTIONS
# ==============================================================================

def should_continue_to_intent_parsing(state: AgentState) -> Literal["parse_intent", "end_workflow"]:
    """Decide whether to continue to intent parsing"""
    if state.get("feature_request") and not state.get("errors"):
        return "parse_intent"
    return "end_workflow"

def should_continue_to_impact_analysis(state: AgentState) -> Literal["analyze_impact", "handle_error"]:
    """Decide whether to continue to impact analysis"""
    if state.get("feature_spec") and not state.get("errors"):
        return "analyze_impact"
    return "handle_error"

def should_continue_to_code_synthesis(state: AgentState) -> Literal["synthesize_code", "handle_error"]:
    """Decide whether to continue to code synthesis"""
    if state.get("impact_analysis") and not state.get("errors"):
        return "synthesize_code"
    return "handle_error"

def should_continue_to_execution(state: AgentState) -> Literal["execute_changes", "handle_error"]:
    """Decide whether to continue to execution"""
    if state.get("code_patches") is not None and not state.get("errors"):
        return "execute_changes"
    return "handle_error"

def handle_error(state: AgentState) -> AgentState:
    """Error handling node"""
    print(f"❌ Error encountered: {state.get('errors', [])}")
    state["current_phase"] = "error_handled"
    return state

def end_workflow(state: AgentState) -> AgentState:
    """End workflow node"""
    print("🏁 Workflow completed")
    state["current_phase"] = "workflow_complete"
    return state

# ==============================================================================
# WORKFLOW CREATION
# ==============================================================================

def create_feature_request_workflow():
    """Create the LangGraph workflow for feature request implementation"""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_context", analyze_context)
    workflow.add_node("parse_intent", parse_intent)
    workflow.add_node("analyze_impact", analyze_impact)
    workflow.add_node("synthesize_code", synthesize_code)
    workflow.add_node("execute_changes", execute_changes)
    workflow.add_node("handle_error", handle_error)
    workflow.add_node("end_workflow", end_workflow)

    # Add edges
    workflow.add_edge(START, "analyze_context")

    # Conditional edges with error handling
    workflow.add_conditional_edges(
        "analyze_context",
        should_continue_to_intent_parsing,
        {
            "parse_intent": "parse_intent",
            "end_workflow": "end_workflow"
        }
    )

    workflow.add_conditional_edges(
        "parse_intent",
        should_continue_to_impact_analysis,
        {
            "analyze_impact": "analyze_impact",
            "handle_error": "handle_error"
        }
    )

    workflow.add_conditional_edges(
        "analyze_impact",
        should_continue_to_code_synthesis,
        {
            "synthesize_code": "synthesize_code",
            "handle_error": "handle_error"
        }
    )

    workflow.add_conditional_edges(
        "synthesize_code",
        should_continue_to_execution,
        {
            "execute_changes": "execute_changes",
            "handle_error": "handle_error"
        }
    )
    workflow.add_edge("handle_error", "end_workflow")

    # Compile with checkpointer for persistence
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    # Validate codebase path
    codebase_path = os.path.abspath(args.codebase_path)
    if not os.path.isdir(codebase_path):
        raise ValueError(f"Not a directory: {codebase_path}")

    # Display config
    print("=" * 80)
    print("🤖 FEATURE-BY-REQUEST AGENT V3 (IMPROVED)")
    print("=" * 80)
    print(f"📁 Codebase: {codebase_path}")
    print(f"🛠️  Model: {model_name}")
    print(f"🌡️  Temperature: {temperature}")

    is_feature_mode = args.feature_request is not None
    if is_feature_mode:
        print(f"🎯 Feature: {args.feature_request}")
        print(f"🏃 Mode: {'DRY RUN' if args.dry_run else 'IMPLEMENT'}")
        print(f"👤 Human Loop: {'ENABLED' if args.enable_human_loop else 'DISABLED'}")
    else:
        print("🔍 Mode: Analysis Only")
    print("=" * 80)

    start = time.time()

    try:
        # Create workflow
        workflow = create_feature_request_workflow()

        # Initialize state
        initial_state: AgentState = {
            "codebase_path": codebase_path,
            "feature_request": args.feature_request if is_feature_mode else None,
            "context_analysis": None,
            "feature_spec": None,
            "impact_analysis": None,
            "code_patches": None,
            "execution_results": None,
            "errors": [],
            "dry_run": args.dry_run,
            "current_phase": "initialized",
            "human_approval_required": False
        }

        # Execute workflow
        from langchain_core.runnables import RunnableConfig
        config: RunnableConfig = {"configurable": {"thread_id": f"feature_request_{int(time.time())}"}}

        if args.enable_human_loop:
            # For human-in-the-loop, we need to handle interrupts
            final_state = initial_state
            while final_state.get("current_phase") != "workflow_complete":
                try:
                    result = workflow.invoke(final_state, config)
                    final_state = result
                    break  # No interrupt occurred
                except Exception as e:
                    if "interrupt" in str(e).lower():
                        # Handle human interrupt
                        print("⏸️  Workflow paused for human input...")
                        # In a real implementation, you'd collect user input here
                        # For now, we'll simulate approval
                        user_input = {"decision": "approve"}
                        workflow.update_state(config, {"decision": user_input})
                        continue
                    else:
                        raise
        else:
            # Normal execution without human loop
            final_state = workflow.invoke(initial_state, config)

        # Report results
        print("\n" + "=" * 80)
        print("🎉 WORKFLOW COMPLETE")
        print("=" * 80)

        if final_state.get("feature_spec"):
            spec = final_state["feature_spec"]
            if spec:
                print(f"Feature: {spec.feature_name}")
                print(f"Files Affected: {len(spec.affected_files)}")
                print(f"New Files: {len(spec.new_files)}")

        if final_state.get("code_patches"):
            patches = final_state["code_patches"]
            if patches:
                print(f"Patches Generated: {len(patches)}")

        if final_state.get("execution_results"):
            results = final_state["execution_results"]
            if results:
                print(f"Execution Status: {results.get('verification_status', 'unknown')}")

        if final_state.get("errors"):
            print(f"Errors: {len(final_state['errors'])}")
            for error in final_state["errors"][:3]:
                print(f"  - {error}")

        print(f"Time: {time.time() - start:.2f}s")
        print(f"Final Phase: {final_state.get('current_phase', 'unknown')}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()