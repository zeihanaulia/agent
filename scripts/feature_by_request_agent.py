"""
FEATURE-BY-REQUEST AGENT - Multi-Phase Implementation
======================================================

PURPOSE:
    This script implements a complete Feature-by-Request Agent that can:
    1. Analyze existing codebase structure and context
    2. Interpret user feature requests into structured specifications
    3. Perform impact analysis to identify affected files and dependencies
    4. Generate code patches and implementation plans
    5. Execute changes with validation and verification

    Uses DeepAgents framework with LangGraph orchestration for multi-phase workflows.

KEY CONCEPTS:
    1. Multi-Phase Agent Workflow: Context Extraction → Intent Parsing → Impact Analysis → Code Synthesis → Execution
    2. FilesystemBackend: Secure filesystem access with built-in tools
    3. Subagents: Specialized agents for each phase with context isolation
    4. Middleware: Guardrails, logging, and error handling
    5. LangGraph Orchestration: Durable execution and state management

ARCHITECTURE:
    Phase 1: Context Extraction Agent (existing analysis agent)
    Phase 2: Intent Parser Agent (extracts feature specs from user requests)
    Phase 3: Impact Analysis Agent (finds affected files and dependencies)
    Phase 4: Code Synthesis Agent (generates implementation patches)
    Phase 5: Execution & Verification Agent (applies changes with validation)

USAGE:
    python feature_by_request_agent.py --feature-request "Add user authentication endpoint"
    python feature_by_request_agent.py --analyze-only  # Just analyze codebase
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

# ==============================================================================
# DATA MODELS
# ==============================================================================

class FeatureSpec(BaseModel):
    """Structured specification of a feature request"""
    feature_name: str = Field(description="Name of the feature")
    intent_summary: str = Field(description="Summary of user intent")
    affected_files: List[str] = Field(default_factory=list, description="Files that need to be modified")
    new_files: List[str] = Field(default_factory=list, description="New files to create")
    modifications: List[Dict[str, Any]] = Field(default_factory=list, description="Specific modifications needed")
    notes: str = Field(default="", description="Additional implementation notes")

class AgentState(BaseModel):
    """State for the multi-phase agent workflow"""
    codebase_path: str
    feature_request: Optional[str] = None
    context_analysis: Optional[str] = None
    feature_spec: Optional[FeatureSpec] = None
    impact_analysis: Optional[Dict[str, Any]] = None
    code_patches: Optional[List[Dict[str, Any]]] = None
    execution_results: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    dry_run: bool = False

# Load environment variables from .env file
# Contains: LITELLM_MODEL, LITELLM_VIRTUAL_KEY, LITELLM_API
# Optional: LANGSMITH_API_KEY, LANGSMITH_PROJECT for observability
load_dotenv()

# ==============================================================================
# STEP 1: CONFIGURE THE AI MODEL
# ==============================================================================
# We need to set up the language model that will power our agent.
# This model will use the built-in tools from FilesystemBackend to analyze code.

# Get configuration from environment or use defaults
model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
api_key = os.getenv("LITELLM_VIRTUAL_KEY")
api_base = os.getenv("LITELLM_API")

# Validate that required environment variables are set
if not api_key or not api_base:
    raise ValueError(
        "Missing required environment variables:\n"
        "  LITELLM_VIRTUAL_KEY: LLM API key\n"
        "  LITELLM_API: LLM API base URL\n"
        "Please set these in your .env file or environment."
    )

# Parse arguments FIRST before setting up model
parser = argparse.ArgumentParser(description="Feature-by-Request Agent")
parser.add_argument(
    "--codebase-path",
    "-p",
    default=os.getenv("CODEBASE_PATH", "/Users/zeihanaulia/Programming/research/agent"),
    help="Path to the codebase to analyze"
)
parser.add_argument(
    "--feature-request",
    "-f",
    help="Feature request to implement (enables feature request mode)"
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Show what would be changed without making actual modifications"
)
parser.add_argument(
    "--model",
    default=None,
    help="OpenAI model to use (default from LITELLM_MODEL env var)"
)
parser.add_argument(
    "--temperature",
    type=float,
    default=None,
    help="Model temperature (0.0-1.0). If not specified, will be auto-set based on model type"
)

args = parser.parse_args()

# Apply user overrides to model_name
if args.model is not None:
    model_name = args.model



# ==============================================================================
# AGENT CREATION FUNCTIONS
# ==============================================================================

def create_context_analysis_agent(codebase_path: str) -> Any:
    """Create agent for Phase 1: Context Extraction"""
    backend = FilesystemBackend(root_dir=codebase_path)

    analysis_prompt = f"""\
You are a code analysis agent. Analyze this codebase quickly but thoroughly.

CODEBASE PATH: {codebase_path}

YOUR TASK:
1. Use ls to list the root directory structure
2. Identify the project type (Java/Maven, Python/Django, Node/Express, etc.)
3. Read key config files: pom.xml, package.json, requirements.txt, setup.py, build.gradle
4. List main source files and directories
5. Provide a clear 10-line summary with:
   - Project type and framework
   - Tech stack and dependencies
   - Main components and controllers/routes
   - Entry point and purpose

WORK EFFICIENTLY:
- Use ls to explore directory structure first
- Read config files to understand dependencies
- List key source files (don't read all of them)
- Be concise but informative

OUTPUT FORMAT:
Provide your analysis as a clear, structured overview suitable for a developer.
"""

    return create_deep_agent(
        system_prompt=analysis_prompt,
        model=analysis_model,
        backend=backend,
    )

def create_intent_parser_agent() -> Any:
    """Create agent for Phase 2: User Request Interpretation"""

    intent_prompt = """\
You are a software architect agent specialized in interpreting user feature requests.

Your job is to extract structured specifications from user requests and return them as JSON.

For a given feature request, extract:
- feature_name: Concise name of the feature
- intent_summary: What the user wants to achieve
- affected_files: Files that might need changes (based on common patterns)
- new_files: New files that might need to be created
- modifications: High-level description of changes needed
- notes: Any additional implementation considerations

Return result as valid JSON matching this schema:
{
  "feature_name": "string",
  "intent_summary": "string",
  "affected_files": ["string"],
  "new_files": ["string"],
  "modifications": [{"description": "string", "type": "string"}],
  "notes": "string"
}

Be specific but not overly prescriptive - focus on the user's intent.
"""

    return create_deep_agent(
        system_prompt=intent_prompt,
        model=analysis_model,
    )

def create_impact_analysis_agent(codebase_path: str) -> Any:
    """Create agent for Phase 3: Impact Analysis"""
    backend = FilesystemBackend(root_dir=codebase_path)

    impact_prompt = f"""\
You are an impact analysis agent. Your job is to analyze how a proposed feature will affect the existing codebase.

CODEBASE PATH: {codebase_path}

Given a feature specification, you need to:
1. Use grep and glob to find relevant files and code patterns
2. Identify dependencies and relationships
3. Assess the scope of changes required
4. Provide detailed impact analysis

Focus on:
- Files that contain related functionality
- Import dependencies that might be affected
- Database schemas or API endpoints that need changes
- Configuration files that might need updates

Return your analysis as structured information about affected components.
"""

    return create_deep_agent(
        system_prompt=impact_prompt,
        model=analysis_model,
        backend=backend,
    )

def create_code_synthesis_agent(codebase_path: str) -> Any:
    """Create agent for Phase 4: Code Synthesis & Diff Planning"""
    backend = FilesystemBackend(root_dir=codebase_path)

    synthesis_prompt = f"""\
You are a code synthesis agent. Your job is to generate implementation plans and code patches for features.

CODEBASE PATH: {codebase_path}

Given context analysis, feature specs, and impact analysis, you need to:
1. Read relevant existing code files
2. Generate minimal, correct code changes
3. Ensure consistency with existing architecture
4. Provide diff patches or new file contents

Focus on:
- Following existing code patterns and conventions
- Proper error handling and validation
- Integration with existing systems
- Minimal changes to achieve the feature

Generate patches using the edit_file and write_file tools.
"""

    return create_deep_agent(
        system_prompt=synthesis_prompt,
        model=analysis_model,
        backend=backend,
    )

def create_execution_agent(codebase_path: str, dry_run: bool = False) -> Any:
    """Create agent for Phase 5: Execution & Verification"""
    backend = FilesystemBackend(root_dir=codebase_path)

    execution_prompt = f"""\
You are an execution and verification agent. Your job is to apply code changes and verify correctness.

CODEBASE PATH: {codebase_path}
DRY RUN MODE: {dry_run}

Your tasks:
1. Apply the generated code patches using filesystem tools
2. Verify that changes are syntactically correct
3. Check that the implementation matches the specification
4. Report on the success/failure of the implementation

{'IN DRY RUN MODE: Show what would be changed without actually making changes.' if dry_run else 'Apply changes carefully and validate each step.'}

Report results including:
- Files modified
- Changes applied
- Verification status
- Any issues encountered
"""

    return create_deep_agent(
        system_prompt=execution_prompt,
        model=analysis_model,
        backend=backend,
    )
# ==============================================================================
# MULTI-PHASE WORKFLOW FUNCTIONS
# ==============================================================================

def run_context_analysis_phase(codebase_path: str) -> str:
    """Phase 1: Analyze codebase context"""
    print("🔍 Phase 1: Analyzing codebase context...")

    agent = create_context_analysis_agent(codebase_path)

    result = agent.invoke({
        "input": f"Please analyze the codebase at {codebase_path} and provide a comprehensive overview."
    })

    # Extract the final analysis
    if "messages" in result:
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_calls"):
                return str(msg.content)

    return "Context analysis failed to produce results."

def run_intent_parsing_phase(feature_request: str) -> FeatureSpec:
    """Phase 2: Parse user intent into structured specs"""
    print("🎯 Phase 2: Parsing feature request...")

    agent = create_intent_parser_agent()

    result = agent.invoke({
        "input": f"Parse this feature request into a structured specification: {feature_request}"
    })

    # Extract and parse JSON response
    if "messages" in result:
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                content = str(msg.content)
                try:
                    # Try to extract JSON from the response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        import json
                        data = json.loads(json_match.group())
                        return FeatureSpec(**data)
                except Exception as e:
                    print(f"Warning: Failed to parse intent response: {e}")

    # Fallback: create basic spec
    return FeatureSpec(
        feature_name="Unknown Feature",
        intent_summary=feature_request,
        notes="Failed to parse structured specification"
    )

def run_impact_analysis_phase(codebase_path: str, context: str, feature_spec: FeatureSpec) -> Dict[str, Any]:
    """Phase 3: Analyze impact of the feature"""
    print("📊 Phase 3: Analyzing feature impact...")

    agent = create_impact_analysis_agent(codebase_path)

    prompt = f"""
Context Analysis: {context}

Feature Spec: {feature_spec.model_dump_json()}

Please analyze the impact of implementing this feature on the codebase.
Identify affected files, dependencies, and implementation scope.
"""

    result = agent.invoke({"input": prompt})

    # Extract analysis results
    analysis = {}
    if "messages" in result:
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                analysis["details"] = str(msg.content)
                break

    return analysis

def run_code_synthesis_phase(codebase_path: str, context: str, feature_spec: FeatureSpec, impact: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Phase 4: Generate code patches"""
    print("⚙️ Phase 4: Synthesizing code implementation...")

    agent = create_code_synthesis_agent(codebase_path)

    prompt = f"""
Context: {context}

Feature Spec: {feature_spec.model_dump_json()}

Impact Analysis: {json.dumps(impact)}

Generate the code changes needed to implement this feature.
Provide specific patches using edit_file and write_file operations.
"""

    result = agent.invoke({"input": prompt})

    # Extract patches (this would need more sophisticated parsing in real implementation)
    patches = []
    if "messages" in result:
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    if call.get("name") in ["write_file", "edit_file"]:
                        patches.append({
                            "tool": call.get("name"),
                            "args": call.get("args", {}),
                            "description": "Generated by code synthesis agent"
                        })

    return patches

def run_execution_phase(codebase_path: str, patches: List[Dict[str, Any]], dry_run: bool) -> Dict[str, Any]:
    """Phase 5: Execute changes and verify"""
    print("🚀 Phase 5: Executing implementation..." if not dry_run else "👀 Phase 5: Dry run - showing changes...")

    agent = create_execution_agent(codebase_path, dry_run)

    prompt = f"""
Apply these code patches to implement the feature:

Patches: {json.dumps(patches)}

{'DRY RUN: Show what would be changed without making actual modifications.' if dry_run else 'Apply the changes and verify correctness.'}
"""

    result = agent.invoke({"input": prompt})

    execution_results = {"patches_applied": [], "verification_status": "unknown"}

    if "messages" in result:
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                execution_results["details"] = str(msg.content)
                break

    return execution_results

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Feature-by-Request Agent")
    parser.add_argument(
        "--codebase-path",
        "-p",
        default=os.getenv("CODEBASE_PATH", "/Users/zeihanaulia/Programming/research/agent"),
        help="Path to the codebase to analyze"
    )
    parser.add_argument(
        "--feature-request",
        "-f",
        help="Feature request to implement (enables feature request mode)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making actual modifications"
    )
    parser.add_argument(
        "--model",
        default=os.getenv("LITELLM_MODEL", "gpt-4o-mini"),
        help="OpenAI model to use (default from LITELLM_MODEL env var)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Model temperature (0.0-1.0). If not specified, will be auto-set based on model type"
    )

    args = parser.parse_args()

    # Set global variables
    global codebase_path, model_name, temperature
    codebase_path = os.path.abspath(args.codebase_path)
    model_name = args.model
    
    # Only override temperature if explicitly provided by user
    if args.temperature is not None:
        temperature = args.temperature
    # Otherwise, temperature is already set correctly based on model type (see line 72-80)

    # Determine mode
    is_feature_request_mode = args.feature_request is not None
    is_analysis_only = not is_feature_request_mode

    # Validate inputs
    if not os.path.exists(codebase_path):
        raise ValueError(f"Codebase path does not exist: {codebase_path}")

    if not os.path.isdir(codebase_path):
        raise ValueError(f"Codebase path is not a directory: {codebase_path}")

    print("=" * 80)
    print("🤖 FEATURE-BY-REQUEST AGENT")
    print("=" * 80)
    print(f"📁 Target Codebase: {codebase_path}")
    print(f"🛠️  Model: {model_name}")
    print(f"🌡️  Temperature: {temperature}")

    if is_feature_request_mode:
        print(f"🎯 Feature Request: {args.feature_request}")
        if args.dry_run:
            print("👀 Mode: Dry Run (no actual changes)")
        else:
            print("🚀 Mode: Implementation")
    else:
        print("🔍 Mode: Analysis Only")

    print("=" * 80)

    start_time = time.time()

    try:
        # Initialize state
        state = AgentState(
            codebase_path=codebase_path,
            feature_request=args.feature_request if is_feature_request_mode else None,
            dry_run=args.dry_run
        )

        # Phase 1: Context Analysis (always run)
        state.context_analysis = run_context_analysis_phase(codebase_path)

        if is_analysis_only:
            print("\n📊 CODEBASE ANALYSIS COMPLETE:")
            print("=" * 80)
            print(state.context_analysis)
            return

        # Phase 2: Intent Parsing
        state.feature_spec = run_intent_parsing_phase(args.feature_request)

        # Phase 3: Impact Analysis
        state.impact_analysis = run_impact_analysis_phase(
            codebase_path, state.context_analysis, state.feature_spec
        )

        # Phase 4: Code Synthesis
        state.code_patches = run_code_synthesis_phase(
            codebase_path, state.context_analysis, state.feature_spec, state.impact_analysis
        )

        # Phase 5: Execution
        state.execution_results = run_execution_phase(
            codebase_path, state.code_patches, state.dry_run
        )

        # Report final results
        print("\n" + "=" * 80)
        print("🎉 FEATURE IMPLEMENTATION COMPLETE")
        print("=" * 80)

        print(f"Feature: {state.feature_spec.feature_name}")
        print(f"Summary: {state.feature_spec.intent_summary}")
        print(f"Files Affected: {len(state.feature_spec.affected_files)}")
        print(f"New Files: {len(state.feature_spec.new_files)}")
        print(f"Patches Generated: {len(state.code_patches)}")

        if state.execution_results:
            print(f"Execution Status: {state.execution_results.get('verification_status', 'unknown')}")

        total_time = time.time() - start_time
        print(f"Total execution time: {total_time:.2f} seconds")

    except Exception as e:
        print(f"❌ Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
