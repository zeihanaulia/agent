"""
Integration Wrapper for Combining Workflows
==========================================

Provides clean integration points for combining:
1. Main feature implementation workflow  
2. Dedicated sandbox testing workflow
3. Legacy compatibility functions

Enables both:
- Standalone usage of each workflow
- Integrated usage where sandbox testing follows feature implementation
"""

import os
from typing import Dict, Any, Optional

from flow_sandbox_workflow import run_sandbox_testing


def integrate_sandbox_testing(
    state: Dict[str, Any], 
    enable_sandbox: bool = True,
    max_iterations: int = 10
) -> Dict[str, Any]:
    """
    Clean integration point for adding sandbox testing to any workflow
    
    Args:
        state: Current workflow state (must contain 'codebase_path')
        enable_sandbox: Whether to run sandbox testing
        max_iterations: Maximum auto-fix iterations
        
    Returns:
        Updated state with sandbox results
    """
    
    if not enable_sandbox:
        print("ℹ️ Sandbox testing disabled - skipping")
        state["sandbox_skipped"] = True
        return state
        
    codebase_path = state.get("codebase_path")
    if not codebase_path:
        print("⚠️ No codebase path provided - skipping sandbox testing")
        state["sandbox_error"] = "No codebase path available"
        return state
        
    if not os.path.exists(codebase_path):
        print(f"⚠️ Codebase path does not exist: {codebase_path}")
        state["sandbox_error"] = f"Path does not exist: {codebase_path}"
        return state
        
    print(f"🧪 Integrating dedicated sandbox testing for: {codebase_path}")
    
    # Run dedicated sandbox workflow
    sandbox_results = run_sandbox_testing(codebase_path, max_iterations)
    
    # Add results to state
    state["sandbox_results"] = sandbox_results
    state["sandbox_success"] = sandbox_results.get("success", False)
    
    # Handle errors
    if not sandbox_results.get("success", False):
        sandbox_errors = sandbox_results.get("errors", [])
        existing_errors = state.get("errors", [])
        state["errors"] = existing_errors + sandbox_errors
        
        print(f"❌ Sandbox testing failed: {sandbox_results.get('final_status', 'unknown')}")
    else:
        print("✅ Sandbox testing completed successfully")
        
    return state


def should_run_sandbox_from_args(args: Any) -> bool:
    """
    Determine if sandbox testing should run based on command line arguments
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        True if sandbox testing should be enabled
    """
    
    # Check for explicit --sandbox flag
    if hasattr(args, 'sandbox') and args.sandbox:
        return True
        
    # Check for --test flag  
    if hasattr(args, 'test') and args.test:
        return True
        
    # Check for environment variable
    if os.getenv('ENABLE_SANDBOX_TESTING', '').lower() in ['true', '1', 'yes']:
        return True
        
    return False


def determine_integration_mode(state: Dict[str, Any]) -> str:
    """
    Determine how sandbox testing should be integrated
    
    Args:
        state: Current workflow state
        
    Returns:
        Integration mode: "standalone", "post_feature", "skip"
    """
    
    # Check if this is a direct sandbox request
    if state.get("mode") == "sandbox_only":
        return "standalone"
        
    # Check if feature implementation was successful
    if state.get("feature_implementation_success", False):
        return "post_feature"
        
    # Check if there are blocking errors
    if state.get("errors") and len(state.get("errors", [])) > 0:
        return "skip"
        
    # Default to post-feature testing
    return "post_feature"


class WorkflowIntegration:
    """
    Class for managing workflow integration patterns
    """
    
    def __init__(self, enable_sandbox: bool = True, max_iterations: int = 10):
        self.enable_sandbox = enable_sandbox
        self.max_iterations = max_iterations
        
    def add_sandbox_to_workflow(self, workflow, state_class):
        """
        Add sandbox testing nodes to existing workflow
        
        Args:
            workflow: LangGraph StateGraph instance
            state_class: State TypedDict class
            
        Returns:
            Modified workflow with sandbox integration
        """
        
        # Add sandbox integration node
        def integrated_sandbox_node(state):
            return integrate_sandbox_testing(
                state, 
                self.enable_sandbox, 
                self.max_iterations
            )
            
        workflow.add_node("integrated_sandbox_testing", integrated_sandbox_node)
        
        return workflow
        
    def create_conditional_edge(self, from_node: str, should_run_sandbox_func):
        """
        Create conditional edge for sandbox integration
        
        Args:
            from_node: Source node name
            should_run_sandbox_func: Function to determine if sandbox should run
            
        Returns:
            Tuple of (from_node, condition_func, edge_map)
        """
        
        def sandbox_routing(state):
            if should_run_sandbox_func(state):
                return "integrated_sandbox_testing"
            else:
                return "end_workflow"
                
        edge_map = {
            "integrated_sandbox_testing": "integrated_sandbox_testing",
            "end_workflow": "__end__"
        }
        
        return (from_node, sandbox_routing, edge_map)


# Example usage functions
def example_feature_workflow_with_sandbox():
    """
    Example of how to integrate sandbox testing into feature implementation workflow
    """
    from langgraph.graph import StateGraph, START
    from typing import TypedDict
    
    class ExampleState(TypedDict):
        codebase_path: str
        feature_request: str
        implementation_complete: bool
        errors: list
        sandbox_results: Optional[Dict[str, Any]]
        sandbox_success: bool
        
    def implement_feature(state: ExampleState) -> ExampleState:
        print("🛠️ Implementing feature...")
        # Feature implementation logic here
        state["implementation_complete"] = True
        return state
        
    def should_run_sandbox(state: ExampleState) -> str:
        if state["implementation_complete"] and not state.get("errors"):
            return "sandbox"
        return "end"
        
    # Create workflow
    workflow = StateGraph(ExampleState)
    
    # Add main nodes
    workflow.add_node("implement_feature", implement_feature)
    
    # Add sandbox integration using wrapper
    integration = WorkflowIntegration(enable_sandbox=True, max_iterations=10)
    workflow = integration.add_sandbox_to_workflow(workflow, ExampleState)
    
    # Add edges
    workflow.add_edge(START, "implement_feature")
    workflow.add_conditional_edges(
        "implement_feature",
        should_run_sandbox,
        {
            "sandbox": "integrated_sandbox_testing",
            "end": "__end__"
        }
    )
    workflow.add_edge("integrated_sandbox_testing", "__end__")
    
    return workflow.compile()


def example_standalone_sandbox_usage():
    """
    Example of running sandbox testing standalone
    """
    
    # Direct usage
    codebase_path = "/path/to/your/springboot/project"
    results = run_sandbox_testing(codebase_path, max_iterations=10)
    
    print("Sandbox Results:")
    print(f"  Success: {results['success']}")
    print(f"  Final Status: {results['final_status']}")
    print(f"  Iterations: {results['iterations']}")
    
    return results


# Legacy compatibility for existing code
def flow_test_sandbox(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Legacy wrapper for backward compatibility with existing flows
    
    This maintains the same interface as the original flow_test_sandbox
    function while using the new dedicated sandbox workflow internally.
    """
    max_iterations = kwargs.get('max_iterations', 10)
    return integrate_sandbox_testing(state, enable_sandbox=True, max_iterations=max_iterations)


def flow_skip_sandbox(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Legacy wrapper for skipping sandbox testing
    """
    return integrate_sandbox_testing(state, enable_sandbox=False)