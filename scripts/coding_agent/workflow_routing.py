"""
WORKFLOW ROUTING - Conditional Logic for Phase Transitions
===========================================================

Responsible for:
- Conditional routing between workflow phases
- Error handling and fallback routing
- Workflow termination decisions
"""

from typing import Literal, Dict, Any


def should_continue_to_intent_parsing(state: Dict[str, Any]) -> Literal["parse_intent", "end_workflow"]:
    """
    Decide whether to continue to intent parsing after context analysis
    
    Proceeds if:
    - Feature request is provided
    - No errors occurred in analysis
    """
    if state.get("feature_request") and not state.get("errors"):
        return "parse_intent"
    return "end_workflow"


def should_continue_to_structure_validation(state: Dict[str, Any]) -> Literal["validate_structure", "handle_error"]:
    """
    Decide whether to validate structure after intent parsing
    
    Proceeds if:
    - Feature spec was created
    - No errors occurred in parsing
    """
    if state.get("feature_spec") and not state.get("errors"):
        return "validate_structure"
    return "handle_error"


def should_continue_to_code_synthesis(state: Dict[str, Any]) -> Literal["synthesize_code", "handle_error"]:
    """
    Decide whether to synthesize code after impact analysis
    
    Proceeds if:
    - Impact analysis completed
    - No errors occurred
    """
    if state.get("impact_analysis") and not state.get("errors"):
        return "synthesize_code"
    return "handle_error"


def should_continue_to_execution(state: Dict[str, Any]) -> Literal["execute_changes", "handle_error"]:
    """
    Decide whether to execute changes after code synthesis
    
    Proceeds if:
    - Code patches were generated (even if empty list)
    - No errors occurred
    """
    if state.get("code_patches") is not None and not state.get("errors"):
        return "execute_changes"
    return "handle_error"


def handle_error(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Error handling node - log errors and terminate gracefully
    
    Args:
        state: Current workflow state
    
    Returns:
        State with error phase marked
    """
    errors = state.get('errors', [])
    print(f"❌ Error encountered: {errors}")
    state["current_phase"] = "error_handled"
    return state


def end_workflow(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Workflow termination node - log completion and cleanup
    
    Args:
        state: Current workflow state
    
    Returns:
        State with workflow complete phase marked
    """
    print("🏁 Workflow completed")
    state["current_phase"] = "workflow_complete"
    return state
