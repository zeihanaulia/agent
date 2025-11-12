"""
FEATURE-BY-REQUEST AGENT - Multi-Phase Implementation V3
=========================================================

Improved version with LangGraph orchestration, supervisor pattern, and full DeepAgents middleware stack.
"""

import argparse
import os
import sys
import time
from typing import Dict, List, Any, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

# Import centralized modules (NEW: consolidated from multiple files)
from agents import (  # NEW
    create_impact_analysis_agent,
    create_code_synthesis_agent,
)
from analytics import detect_framework  # NEW: consolidated framework detection
from models import setup_model  # NEW: consolidated LLM setup

# Import framework instructions for framework-aware code generation
from framework_instructions import get_instruction  # pyright: ignore[reportAssignmentType]

# Import enhanced structure validator with feedback loop (Phase 2A)
from flow_validate_structure import validate_structure_with_feedback  # pyright: ignore[reportAssignmentType]

# Import Aider-style context analyzer for Phase 1
from flow_analyze_context import AiderStyleRepoAnalyzer, infer_app_type  # pyright: ignore[reportAssignmentType]

# Import Intent Parser for Phase 2
from flow_parse_intent import (  # pyright: ignore[reportAssignmentType]
    flow_parse_intent
)

# Import phase-specific flows (NEW: separated concerns)
from flow_analyze_impact import flow_analyze_impact  # pyright: ignore[reportAssignmentType]
from flow_synthesize_code import flow_synthesize_code  # pyright: ignore[reportAssignmentType]
from flow_execute_changes import flow_execute_changes  # pyright: ignore[reportAssignmentType]

# Import workflow routing (NEW: conditional logic)
from workflow_routing import (  # pyright: ignore[reportAssignmentType]
    should_continue_to_intent_parsing,
    should_continue_to_structure_validation,
    should_continue_to_code_synthesis,
    should_continue_to_execution,
    handle_error,
    end_workflow
)

# Load environment variables
load_dotenv()


def configure_tracing_runtime() -> None:
    """
    Apply LangSmith tracing best practices so runs finish cleanly.

    Docs recommend disabling background callbacks in short-lived/serverless style
    processes to make sure traces flush before the worker exits:
    https://docs.smith.langchain.com/observability/how_to_guides/trace_with_langgraph
    """
    tracing_enabled = os.getenv("LANGSMITH_TRACING_V2", "false").lower() == "true"
    if not tracing_enabled:
        return

    if os.getenv("LANGCHAIN_CALLBACKS_BACKGROUND") is None:
        # Foreground callbacks ensure LangSmith finishes each run before the script exits
        os.environ["LANGCHAIN_CALLBACKS_BACKGROUND"] = "false"
        print("✅ LangSmith tracing: forcing LANGCHAIN_CALLBACKS_BACKGROUND=false (flush callbacks synchronously)")


# Ensure tracing env defaults are applied as soon as the module loads
configure_tracing_runtime()

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
    todo_list: Optional[Any] = Field(default=None, description="Structured todo list from Phase 2")
    new_files_planning: Optional[Any] = Field(default=None, description="Detailed new files planning from Phase 2")

class AgentState(TypedDict):
    """State for the multi-phase workflow"""
    codebase_path: str
    feature_request: Optional[str]
    context_analysis: Optional[str]
    feature_spec: Optional[FeatureSpec]
    impact_analysis: Optional[Dict[str, Any]]
    structure_assessment: Optional[Dict[str, Any]]
    code_patches: Optional[List[Dict[str, Any]]]
    execution_results: Optional[Dict[str, Any]]
    errors: List[str]
    dry_run: bool
    current_phase: str
    human_approval_required: bool
    framework: Optional[Any]  # Can be FrameworkType enum or str or None

# ==============================================================================
# GLOBAL VARIABLES (initialized in main)
# ==============================================================================

args = None  # Will be set by parse_arguments()
analysis_model = None  # Will be set by setup_model()
model_name = None  # Will be set by setup_model()
temperature = None  # Will be set by setup_model()
# ==============================================================================
# TIMEOUT HANDLING HELPERS
# ==============================================================================

def invoke_with_timeout(agent, input_data, timeout_seconds=30):
    """
    Invoke agent with timeout protection to prevent indefinite hanging.
    
    Returns:
    - dict: agent result if successful
    - None: if timeout occurs (caller should use fallback)
    - Raises: Exception if error occurs
    """
    import threading
    
    result_container = {"status": "pending", "data": None, "error": None}
    
    def worker():
        try:
            result_container["data"] = agent.invoke(input_data)
            result_container["status"] = "success"
        except Exception as e:
            result_container["status"] = "error"
            result_container["error"] = str(e)
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if result_container["status"] == "pending":
        print(f"  ⚠️  Agent invoke timeout after {timeout_seconds}s - switching to fast mode")
        return None
    
    if result_container["status"] == "error":
        raise Exception(result_container["error"])
    
    return result_container["data"]


# ==============================================================================
# PARSE ARGUMENTS FUNCTION
# ==============================================================================

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Feature-by-Request Agent V3")
    parser.add_argument("--codebase-path", "-p",
                       default=os.getenv("CODEBASE_PATH", "/Users/zeihanaulia/Programming/research/agent"))
    parser.add_argument("--feature-request", "-f", help="Feature request to implement")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", default=None, help="LLM model to use")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--enable-human-loop", action="store_true", help="Enable human-in-the-loop approval")

    return parser.parse_args()


# ==============================================================================
# SETUP MODEL FUNCTION
# ==============================================================================

# setup_model() is now imported from models.llm_setup


# ==============================================================================
# AGENT CREATION
# ==============================================================================

# create_impact_analysis_agent()
# create_code_synthesis_agent()
# create_execution_agent()
# All are now imported from agents.agent_factory


# ==============================================================================
# WORKFLOW NODES
# ==============================================================================

def analyze_context(state: AgentState) -> AgentState:
    """Node: Context Analysis Phase - Aider-style analysis for codebase understanding"""
    print("🔍 Phase 1: Analyzing codebase context (Aider-style)...")
    
    codebase_path = state["codebase_path"]

    try:
        print("  📊 Using Aider-style repository analyzer...")
        analyzer = AiderStyleRepoAnalyzer(codebase_path, max_tokens=2048)
        analysis_result = analyzer.analyze_codebase()

        basic = analysis_result["basic_info"]
        code_analysis = analysis_result["code_analysis"]
        ranked = analysis_result["ranked_elements"]
        structure = analysis_result["structure"]

        summary = f"""
PROJECT ANALYSIS (Aider-Style Analysis):

FILESYSTEM SCAN:
- Type: {basic['project_type']}
- Framework: {basic['framework']}
- Tech Stack: {', '.join(basic['tech_stack']) if basic['tech_stack'] else 'Mixed'}
- Total Source Files: {basic['source_files_count']}
- Root Directories: {', '.join(basic['main_dirs'][:5])}

CODE ANALYSIS:
- Tags Extracted: {code_analysis['total_tags']} from {len(code_analysis['tags_by_file'])} files
- Definitions: {len(code_analysis['definitions'])}
- References: {len(code_analysis['references'])}

PROJECT STRUCTURE:
- Entry Points: {', '.join(structure['entry_points']) if structure['entry_points'] else 'None detected'}
- Test Directories: {len(structure['test_directories'])}
- Source Directories: {len(structure['source_directories'])}

ARCHITECTURE INSIGHTS:
1. **Application Type**: {infer_app_type(basic, structure)}
2. **Main Components**: {', '.join([name for name, _ in ranked['top_elements'][:3]])}
3. **Technology Stack**: {', '.join(basic['tech_stack']) if basic['tech_stack'] else 'Unknown'}
"""
        
        state["context_analysis"] = summary
        state["current_phase"] = "context_analysis_complete"
        
        print("  ✓ Analysis complete")
        print("  ✓ Context saved for next phases")
        
        return state
        
    except Exception as e:
        print(f"  ❌ Error during context analysis: {e}")
        import traceback
        traceback.print_exc()
        state["errors"].append(f"Context analysis error: {str(e)}")
        state["context_analysis"] = f"Error: {str(e)}"
        return state


def parse_intent(state: AgentState) -> AgentState:
    print("🎯 Phase 2: Expert analysis - creating implementation plan (using flow_parse_intent)...")
    feature_request = state.get("feature_request")
    codebase_path = state["codebase_path"]
    context_analysis = state.get("context_analysis", "")

    if not feature_request:
        state["errors"].append("No feature request provided")
        return state

    try:
        # Use flow_parse_intent for structured intent parsing
        flow_state = {
            "codebase_path": codebase_path,
            "feature_request": feature_request,
            "context_analysis": context_analysis,
            "framework": None,
            "feature_spec": None,
            "errors": []
        }
        
        # Call flow_parse_intent with analysis_model
        result_state = flow_parse_intent(
            flow_state,
            analysis_model=analysis_model,
            framework_detector=detect_framework
        )
        
        # Extract results from flow_parse_intent
        feature_spec = result_state.get("feature_spec")
        detected_framework = result_state.get("framework")
        errors = result_state.get("errors", [])
        
        if errors:
            state["errors"].extend(errors)
            print(f"  ⚠️  Errors during parsing: {errors}")
        
        # Update state with results
        if feature_spec:
            # Convert to AgentState FeatureSpec format - preserve all fields
            spec = FeatureSpec(
                feature_name=feature_spec.feature_name,
                intent_summary=feature_spec.intent_summary,
                affected_files=feature_spec.affected_files,
                new_files=feature_spec.new_files,
                modifications=feature_spec.modifications,
                notes=feature_spec.notes,
                todo_list=getattr(feature_spec, 'todo_list', None),
                new_files_planning=getattr(feature_spec, 'new_files_planning', None)
            )
            state["feature_spec"] = spec
            state["framework"] = detected_framework
            state["current_phase"] = "intent_parsing_complete"
            
            # Print results
            print(f"  ✓ Feature: {spec.feature_name[:50]}...")
            print(f"  ✓ Affected files: {len(spec.affected_files)} file(s)")
            print(f"  ✓ New files planned: {len(spec.new_files)} file(s)")
            if feature_spec.todo_list:
                print(f"  ✓ Todo items: {feature_spec.todo_list.total_tasks} items ({feature_spec.todo_list.completed_tasks} completed)")
        else:
            state["errors"].append("Failed to create feature spec from intent parsing")
            
    except Exception as e:
        print(f"  ❌ Error during intent parsing: {e}")
        import traceback
        traceback.print_exc()
        state["errors"].append(f"Intent parsing error: {str(e)}")

    return state

def validate_structure(state: AgentState) -> AgentState:
    """Node: Structure Validation Phase with Feedback Loop (Phase 2A)
    
    Enhanced validation with:
    - Iterative refinement (max 3 rounds)
    - Auto-fix for missing directories
    - Production-readiness scoring
    - Feedback loop back to parse_intent if needed
    """
    print("🏗️ Phase 2A: Structure Validation with Iterative Refinement...")
    
    # Use enhanced validator with feedback loop
    state = validate_structure_with_feedback(state, max_loops=3) # pyright: ignore[reportArgumentType, reportAssignmentType]
    
    return state

def analyze_impact(state: AgentState) -> AgentState:
    """Node: Impact Analysis Phase (delegate to flow_analyze_impact)"""
    return flow_analyze_impact(state, create_impact_analysis_agent, analysis_model)

def synthesize_code(state: AgentState) -> AgentState:
    """Node: Code Synthesis Phase (delegate to flow_synthesize_code)"""
    return flow_synthesize_code(state, create_code_synthesis_agent, get_instruction, analysis_model)

def execute_changes(state: AgentState, enable_human_loop: bool = False) -> AgentState:
    """Node: Execution Phase with Human Approval (delegate to flow_execute_changes)"""
    return flow_execute_changes(state, enable_human_loop=enable_human_loop)

# ==============================================================================
# WORKFLOW CREATION
# ==============================================================================

def create_feature_request_workflow():
    """Create the LangGraph workflow for feature request implementation"""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_context", analyze_context)
    workflow.add_node("parse_intent", parse_intent)
    workflow.add_node("validate_structure", validate_structure)
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
        should_continue_to_structure_validation,
        {
            "validate_structure": "validate_structure",
            "handle_error": "handle_error"
        }
    )

    workflow.add_edge("validate_structure", "analyze_impact")

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
    global args, analysis_model, model_name, temperature
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup model
    model_name, temperature, analysis_model = setup_model(
        model_override=args.model,
        temperature_override=args.temperature
    )
    
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
            "structure_assessment": None,
            "code_patches": None,
            "execution_results": None,
            "errors": [],
            "dry_run": args.dry_run,
            "current_phase": "initialized",
            "human_approval_required": False,
            "framework": None
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
