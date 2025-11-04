"""
FEATURE-BY-REQUEST AGENT - Multi-Phase Implementation V2
=========================================================

Simplified version with proper argument handling and model setup.
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, List, Any, Optional

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr

# Import middleware
sys.path.append(os.path.dirname(__file__))
from middleware import create_phase4_middleware, log_middleware_config

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

class AgentState(BaseModel):
    """State for the multi-phase workflow"""
    codebase_path: str
    feature_request: Optional[str] = None
    context_analysis: Optional[str] = None
    feature_spec: Optional[FeatureSpec] = None
    impact_analysis: Optional[Dict[str, Any]] = None
    code_patches: Optional[List[Dict[str, Any]]] = None
    execution_results: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    dry_run: bool = False

# ==============================================================================
# PARSE ARGUMENTS FIRST
# ==============================================================================

parser = argparse.ArgumentParser(description="Feature-by-Request Agent")
parser.add_argument("--codebase-path", "-p", 
                   default=os.getenv("CODEBASE_PATH", "/Users/zeihanaulia/Programming/research/agent"))
parser.add_argument("--feature-request", "-f", help="Feature request to implement")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--model", default=None, help="LLM model to use")
parser.add_argument("--temperature", type=float, default=None)

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
# AGENT CREATION FUNCTIONS
# ==============================================================================

def create_context_analysis_agent(codebase_path: str):
    """Phase 1: Context Extraction"""
    backend = FilesystemBackend(root_dir=codebase_path)
    prompt = f"""\
Analyze this codebase quickly but thoroughly.

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
    return create_deep_agent(system_prompt=prompt, model=analysis_model, backend=backend)

def create_intent_parser_agent():
    """Phase 2: Intent Parsing - Expert software engineer analyzing feature request"""
    prompt = """\
You are an expert software engineer analyzing a feature request.

Your task: Create a detailed implementation plan using write_todos tool.

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
    return create_deep_agent(system_prompt=prompt, model=analysis_model)

def create_impact_analysis_agent(codebase_path: str):
    """Phase 3: Impact Analysis - Expert architect analyzing codebase patterns"""
    backend = FilesystemBackend(root_dir=codebase_path)
    prompt = f"""\
You are an expert software architect. Analyze the codebase to understand implementation strategy.

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
    return create_deep_agent(system_prompt=prompt, model=analysis_model, backend=backend)

def create_code_synthesis_agent(codebase_path: str, middleware: Optional[List] = None):
    """Phase 4: Code Synthesis - Expert engineer generating testable, production-ready code"""
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
    return create_deep_agent(system_prompt=prompt, model=analysis_model, backend=backend, middleware=middleware)

def create_execution_agent(codebase_path: str, dry_run: bool):
    """Phase 5: Execution & Verification"""
    backend = FilesystemBackend(root_dir=codebase_path)
    mode = "DRY RUN" if dry_run else "APPLY CHANGES"
    prompt = f"""\
Apply code changes and verify correctness.

CODEBASE PATH: {codebase_path}
MODE: {mode}

Tasks:
1. Apply code patches using filesystem tools
2. Verify syntactic correctness
3. Check implementation matches specification
4. Report success/failure
"""
    return create_deep_agent(system_prompt=prompt, model=analysis_model, backend=backend)

# ==============================================================================
# WORKFLOW FUNCTIONS
# ==============================================================================

def run_context_analysis_phase(codebase_path: str) -> str:
    """Phase 1"""
    print("🔍 Phase 1: Analyzing codebase context...")
    agent = create_context_analysis_agent(codebase_path)
    result = agent.invoke({"input": f"Analyze {codebase_path}"})
    
    if "messages" in result:
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_calls"):
                return str(msg.content)
    return "Analysis failed."

def run_intent_parsing_phase(feature_request: str, context: str) -> FeatureSpec:
    """Phase 2: Expert analysis - create implementation plan with reasoning and todo tracking"""
    print("🎯 Phase 2: Expert analysis - creating implementation plan...")
    
    agent = create_intent_parser_agent()
    
    # Expert-level prompt with focus on reasoning, design patterns, and testability
    prompt = f"""
CODEBASE CONTEXT:
{context}

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
                affected_files.extend(file_matches)
    
    # Remove duplicates while preserving order
    affected_files = list(dict.fromkeys(affected_files))
    
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
    
    print(f"  ✓ Feature: {spec.feature_name[:50]}...")
    print(f"  ✓ Analysis steps: {len(todos_found)} tasks identified")
    print(f"  ✓ Affected files: {len(affected_files)} file(s)")
    if affected_files:
        for f in affected_files[:3]:
            print(f"    - {f}")
        if len(affected_files) > 3:
            print(f"    ... and {len(affected_files) - 3} more")
    
    return spec

def run_impact_analysis_phase(codebase_path: str, context: str, spec: FeatureSpec) -> Dict[str, Any]:
    """Phase 3: Expert architecture analysis - identify exact changes and patterns"""
    print("📊 Phase 3: Architecture analysis - identifying patterns and impact...")
    agent = create_impact_analysis_agent(codebase_path)
    
    prompt = f"""
FEATURE REQUEST: {spec.intent_summary}

TASK: Conduct expert architecture analysis:

1. **Current Architecture**: Analyze the existing code patterns, layers, and structure
2. **Technology Stack**: Identify frameworks, libraries, and patterns in use
3. **Design Patterns**: What patterns are already implemented? (MVC, Repository, Service, etc)
4. **Affected Files**: List EXACTLY which files need modification with reasons
5. **Code Patterns**: Show specific code examples of patterns to follow
6. **Dependencies**: List what's already available (no new dependencies!)
7. **Testing Strategy**: How should the new code be tested?
8. **Constraints**: Any limitations or best practices to follow?

Use write_todos to plan the impact analysis tasks if needed.
Be SPECIFIC - list file names, line numbers, and code patterns from the actual codebase.
"""
    result = agent.invoke({"input": prompt})
    
    analysis = {
        "files_to_modify": spec.affected_files,
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
    
    print(f"  ✓ Files to modify: {len(spec.affected_files)} file(s)")
    print(f"  ✓ Patterns identified: {len(analysis['patterns_to_follow'])} pattern(s)")
    print(f"  ✓ Analysis tasks: {len(analysis['todos'])} task(s)")
    
    return analysis

def run_code_synthesis_phase(codebase_path: str, context: str, spec: FeatureSpec, 
                             impact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Phase 4: Expert code generation with testability and design patterns"""
    print("⚙️ Phase 4: Expert code generation with testability and SOLID principles...")
    
    # Create middleware for Phase 4 agent
    middleware = create_phase4_middleware(
        feature_request=spec.intent_summary,
        affected_files=spec.affected_files,
        codebase_root=codebase_path
    )
    
    # Log middleware configuration
    log_middleware_config(spec.intent_summary, spec.affected_files)
    
    agent = create_code_synthesis_agent(codebase_path, middleware=middleware)
    
    files_to_modify = impact.get("files_to_modify", spec.affected_files)
    architecture = impact.get("architecture_insights", "")[:500]
    
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
"""
    
    _analysis_result = agent.invoke({"input": analysis_prompt})
    
    # Step 2: Agent implements based on plan
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

def run_execution_phase(codebase_path: str, patches: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
    """Phase 5"""
    mode = "DRY RUN" if dry_run else "EXECUTE"
    print(f"🚀 Phase 5: {mode}...")
    
    if not patches:
        print("  ℹ️ No patches to apply")
        return {"patches_applied": [], "verification_status": "no_patches"}
    
    print(f"  ℹ️ Applying {len(patches)} patch(es)...")
    
    # Extract file operations from patches
    results = {"patches_applied": [], "verification_status": "completed"}
    for patch in patches:
        tool_name = patch.get("tool")
        args = patch.get("args", {})
        file_path = args.get("path", "unknown")
        
        print(f"    - {tool_name}: {file_path}")
        results["patches_applied"].append(file_path)
    
    return results

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
    print("🤖 FEATURE-BY-REQUEST AGENT")
    print("=" * 80)
    print(f"📁 Codebase: {codebase_path}")
    print(f"🛠️  Model: {model_name}")
    print(f"🌡️  Temperature: {temperature}")
    
    is_feature_mode = args.feature_request is not None
    if is_feature_mode:
        print(f"🎯 Feature: {args.feature_request}")
        print(f"🏃 Mode: {'DRY RUN' if args.dry_run else 'IMPLEMENT'}")
    else:
        print("🔍 Mode: Analysis Only")
    print("=" * 80)

    start = time.time()
    
    try:
        state = AgentState(codebase_path=codebase_path, dry_run=args.dry_run,
                          feature_request=args.feature_request if is_feature_mode else None)

        # Phase 1: Always run analysis
        state.context_analysis = run_context_analysis_phase(codebase_path)

        if not is_feature_mode:
            print("\n📊 ANALYSIS COMPLETE:")
            print("=" * 80)
            print(state.context_analysis)
            return

        # Phase 2-5: Feature implementation workflow
        state.feature_spec = run_intent_parsing_phase(args.feature_request, state.context_analysis)
        state.impact_analysis = run_impact_analysis_phase(codebase_path, state.context_analysis, state.feature_spec)
        state.code_patches = run_code_synthesis_phase(codebase_path, state.context_analysis, 
                                                      state.feature_spec, state.impact_analysis)
        state.execution_results = run_execution_phase(codebase_path, state.code_patches, args.dry_run)

        # Report results
        print("\n" + "=" * 80)
        print("🎉 COMPLETE")
        print("=" * 80)
        print(f"Feature: {state.feature_spec.feature_name}")
        print(f"Files Affected: {len(state.feature_spec.affected_files)}")
        print(f"New Files: {len(state.feature_spec.new_files)}")
        print(f"Patches: {len(state.code_patches) if state.code_patches else 0}")
        print(f"Time: {time.time() - start:.2f}s")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
