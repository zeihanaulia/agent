"""
Dedicated Sandbox Workflow - Standalone E2B Testing with Auto-Fix
=================================================================

Separate, reusable workflow specifically for E2B sandbox testing with:
- Build verification
- Runtime testing  
- Error detection & analysis
- LLM-powered auto-fix iterations
- Clear success/failure reporting

Can be used standalone or integrated into feature implementation workflows.
"""

import os
import sys
import time
from typing import Dict, Any, Optional, TypedDict

from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

# Add the scripts/coding_agent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from sandbox_executor import (
        SandboxConfig,
        SpringBootSandboxExecutor
    )
except ImportError:
    print("Error: Cannot import sandbox_executor. Make sure it's in the same directory.")
    sys.exit(1)


class SandboxState(TypedDict):
    """State for sandbox testing workflow"""
    codebase_path: str
    project_type: Optional[str]  # "springboot", "node", etc.
    max_iterations: int
    current_iteration: int
    build_results: list
    run_results: list  
    error_analysis: list
    auto_fix_attempts: list
    final_status: str  # "success", "failed", "max_iterations", "not_applicable"
    success: bool
    errors: list
    sandbox_config: Optional[Dict[str, Any]]
    

def detect_project_type(state: SandboxState) -> SandboxState:
    """
    Node: Detect project type to determine if sandbox testing is applicable
    """
    print("🔍 Phase: Detecting project type for sandbox compatibility...")
    
    codebase_path = state["codebase_path"]
    project_type = None
    
    try:
        # Check for Spring Boot project
        pom_path = os.path.join(codebase_path, "pom.xml")
        if os.path.exists(pom_path):
            with open(pom_path, 'r', encoding='utf-8') as f:
                pom_content = f.read()
                if "spring-boot" in pom_content.lower():
                    project_type = "springboot"
                    print("  ✅ Detected: Spring Boot Maven project")
                    
        # Check for Node.js project
        package_json_path = os.path.join(codebase_path, "package.json")
        if os.path.exists(package_json_path) and not project_type:
            project_type = "nodejs"
            print("  ✅ Detected: Node.js project")
            
        # Check for Python project
        if not project_type:
            python_files = []
            for root, dirs, files in os.walk(codebase_path):
                python_files.extend([f for f in files if f.endswith('.py')])
                if len(python_files) > 3:  # Has significant Python code
                    project_type = "python"
                    print("  ✅ Detected: Python project")
                    break
                    
        if not project_type:
            project_type = "unknown"
            print("  ⚠️ Unknown project type - sandbox testing may not be applicable")
            
        state["project_type"] = project_type
        return state
        
    except Exception as e:
        print(f"❌ Error detecting project type: {e}")
        state["errors"].append(f"Project type detection failed: {e}")
        state["project_type"] = "unknown"
        return state


def validate_sandbox_requirements(state: SandboxState) -> SandboxState:
    """
    Node: Validate that project meets requirements for sandbox testing
    """
    print("✅ Phase: Validating sandbox testing requirements...")
    
    project_type = state["project_type"]
    codebase_path = state["codebase_path"]
    
    validation_passed = True
    validation_errors = []
    
    try:
        if project_type == "springboot":
            # Check for required Spring Boot files
            required_files = [
                "pom.xml",
                "src/main/java"
            ]
            
            for req_file in required_files:
                full_path = os.path.join(codebase_path, req_file)
                if not os.path.exists(full_path):
                    validation_passed = False
                    validation_errors.append(f"Missing required file: {req_file}")
                    
            # Check for main application class
            src_main_java = os.path.join(codebase_path, "src", "main", "java")
            if os.path.exists(src_main_java):
                has_main_class = False
                for root, dirs, files in os.walk(src_main_java):
                    for file in files:
                        if file.endswith('.java'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    if '@SpringBootApplication' in content:
                                        has_main_class = True
                                        break
                            except UnicodeDecodeError:
                                continue
                    if has_main_class:
                        break
                        
                if not has_main_class:
                    validation_passed = False
                    validation_errors.append("No @SpringBootApplication main class found")
                    
        elif project_type == "nodejs":
            # Node.js validation logic
            required_files = ["package.json"]
            for req_file in required_files:
                if not os.path.exists(os.path.join(codebase_path, req_file)):
                    validation_passed = False
                    validation_errors.append(f"Missing required file: {req_file}")
                    
        elif project_type == "python":
            # Python validation logic
            python_files = []
            for root, dirs, files in os.walk(codebase_path):
                python_files.extend([f for f in files if f.endswith('.py')])
                
            if len(python_files) == 0:
                validation_passed = False
                validation_errors.append("No Python files found")
                
        else:
            validation_passed = False
            validation_errors.append(f"Unsupported project type: {project_type}")
            
        if validation_passed:
            print(f"  ✅ {(project_type or 'Unknown').title()} project validation passed")
        else:
            print(f"  ❌ Validation failed: {', '.join(validation_errors)}")
            state["errors"].extend(validation_errors)
            
        return state
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        state["errors"].append(f"Validation error: {e}")
        return state


def execute_sandbox_testing(state: SandboxState) -> SandboxState:
    """
    Node: Execute sandbox testing with auto-fix iterations
    """
    print("🧪 Phase: Executing sandbox testing with auto-fix...")
    
    project_type = state["project_type"]
    codebase_path = state["codebase_path"]
    max_iterations = state["max_iterations"]
    
    if project_type != "springboot":
        print(f"ℹ️ Sandbox testing not yet implemented for {project_type} projects")
        state["final_status"] = "not_applicable"
        state["success"] = True  # Don't treat as failure
        return state
        
    try:
        # Configure sandbox for Spring Boot
        config = SandboxConfig(
            max_retries=max_iterations,
            timeout=60,
            build_timeout=300,
            run_timeout=30
        )
        
        # Execute sandbox testing
        print(f"🚀 Starting sandbox testing with max {max_iterations} iterations...")
        
        with SpringBootSandboxExecutor(config) as executor:
            results = executor.test_project(codebase_path)
            
        # Extract results
        state["build_results"] = results.get("build_results", [])
        state["run_results"] = results.get("run_results", [])
        state["error_analysis"] = results.get("error_analysis", [])
        state["current_iteration"] = results.get("iterations", 0)
        state["final_status"] = results.get("final_status", "unknown")
        state["success"] = results.get("success", False)
        
        # Log detailed results
        print("\n" + "="*50)
        print("📊 SANDBOX TESTING RESULTS")
        print("="*50)
        print(f"✅ Success: {state['success']}")
        print(f"🔄 Iterations Used: {state['current_iteration']}/{max_iterations}")
        print(f"📋 Final Status: {state['final_status']}")
        print(f"🔨 Build Attempts: {len(state['build_results'])}")
        print(f"🏃 Run Attempts: {len(state['run_results'])}")
        print(f"🔍 Error Analysis: {len(state['error_analysis'])} entries")
        
        if not state["success"]:
            # Add summary error
            error_msg = f"Sandbox testing failed: {state['final_status']} after {state['current_iteration']} iterations"
            state["errors"].append(error_msg)
            print(f"❌ {error_msg}")
        else:
            print("🎉 Sandbox testing completed successfully!")
            
        print("="*50)
        
        return state
        
    except Exception as e:
        print(f"❌ Sandbox testing execution failed: {e}")
        state["errors"].append(f"Sandbox execution error: {e}")
        state["final_status"] = "execution_error"
        state["success"] = False
        return state


def summarize_results(state: SandboxState) -> SandboxState:
    """
    Node: Generate final summary of sandbox testing results
    """
    print("📋 Phase: Generating sandbox testing summary...")
    
    summary = {
        "project_type": state["project_type"],
        "success": state["success"],
        "final_status": state["final_status"],
        "iterations_used": state["current_iteration"],
        "max_iterations": state["max_iterations"],
        "total_errors": len(state["errors"]),
        "build_success_rate": 0,
        "run_success_rate": 0,
        "auto_fixes_applied": len(state["auto_fix_attempts"])
    }
    
    # Calculate success rates
    if state["build_results"]:
        successful_builds = sum(1 for r in state["build_results"] if r.success)
        summary["build_success_rate"] = successful_builds / len(state["build_results"])
        
    if state["run_results"]:
        successful_runs = sum(1 for r in state["run_results"] if r.success)
        summary["run_success_rate"] = successful_runs / len(state["run_results"])
    
    # Print summary
    print(f"  📊 Project Type: {summary['project_type']}")
    print(f"  ✅ Overall Success: {summary['success']}")
    print(f"  🎯 Final Status: {summary['final_status']}")
    print(f"  🔄 Iterations: {summary['iterations_used']}/{summary['max_iterations']}")
    
    if summary["build_success_rate"] > 0:
        print(f"  🔨 Build Success Rate: {summary['build_success_rate']:.1%}")
    if summary["run_success_rate"] > 0:
        print(f"  🏃 Run Success Rate: {summary['run_success_rate']:.1%}")
        
    if summary["auto_fixes_applied"] > 0:
        print(f"  🤖 Auto-fixes Applied: {summary['auto_fixes_applied']}")
        
    if summary["total_errors"] > 0:
        print(f"  ❌ Total Errors: {summary['total_errors']}")
        
    return state


# Conditional routing functions
def should_continue_after_detection(state: SandboxState) -> str:
    """Route after project type detection"""
    if state.get("errors"):
        return "summarize_results"
    if state["project_type"] == "unknown":
        return "summarize_results"
    return "validate_sandbox_requirements"


def should_continue_after_validation(state: SandboxState) -> str:
    """Route after validation"""
    if state.get("errors"):
        return "summarize_results"
    return "execute_sandbox_testing"


def should_continue_after_testing(state: SandboxState) -> str:
    """Route after testing execution"""
    return "summarize_results"


def create_sandbox_workflow():
    """
    Create dedicated sandbox testing workflow
    
    Returns:
        Compiled LangGraph workflow for sandbox testing
    """
    workflow = StateGraph(SandboxState)
    
    # Add nodes
    workflow.add_node("detect_project_type", detect_project_type)
    workflow.add_node("validate_sandbox_requirements", validate_sandbox_requirements)
    workflow.add_node("execute_sandbox_testing", execute_sandbox_testing)
    workflow.add_node("summarize_results", summarize_results)
    
    # Add edges
    workflow.add_edge(START, "detect_project_type")
    
    workflow.add_conditional_edges(
        "detect_project_type",
        should_continue_after_detection,
        {
            "validate_sandbox_requirements": "validate_sandbox_requirements",
            "summarize_results": "summarize_results"
        }
    )
    
    workflow.add_conditional_edges(
        "validate_sandbox_requirements", 
        should_continue_after_validation,
        {
            "execute_sandbox_testing": "execute_sandbox_testing",
            "summarize_results": "summarize_results"
        }
    )
    
    workflow.add_conditional_edges(
        "execute_sandbox_testing",
        should_continue_after_testing,
        {
            "summarize_results": "summarize_results"
        }
    )
    
    # Compile with checkpointer
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


def run_sandbox_testing(codebase_path: str, max_iterations: int = 10) -> Dict[str, Any]:
    """
    Standalone function to run sandbox testing workflow
    
    Args:
        codebase_path: Path to project directory
        max_iterations: Maximum auto-fix iterations
        
    Returns:
        Dictionary with testing results
    """
    
    print("🧪 Starting Dedicated Sandbox Testing Workflow")
    print("=" * 60)
    
    # Create workflow
    workflow = create_sandbox_workflow()
    
    # Initialize state
    initial_state: SandboxState = {
        "codebase_path": codebase_path,
        "project_type": None,
        "max_iterations": max_iterations,
        "current_iteration": 0,
        "build_results": [],
        "run_results": [],
        "error_analysis": [],
        "auto_fix_attempts": [],
        "final_status": "initialized",
        "success": False,
        "errors": [],
        "sandbox_config": None
    }
    
    # Execute workflow
    try:
        from langchain_core.runnables import RunnableConfig
        config: RunnableConfig = {"configurable": {"thread_id": f"sandbox_{int(time.time())}"}}
        
        start_time = time.time()
        final_state = workflow.invoke(initial_state, config)
        execution_time = time.time() - start_time
        
        print(f"\n🏁 Sandbox workflow completed in {execution_time:.2f}s")
        
        # Convert state to results dictionary
        results = {
            "success": final_state["success"],
            "final_status": final_state["final_status"],
            "project_type": final_state["project_type"],
            "iterations": final_state["current_iteration"],
            "max_iterations": final_state["max_iterations"],
            "build_results": final_state["build_results"],
            "run_results": final_state["run_results"],
            "error_analysis": final_state["error_analysis"],
            "errors": final_state["errors"],
            "execution_time": execution_time
        }
        
        return results
        
    except Exception as e:
        print(f"❌ Sandbox workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "final_status": "workflow_error",
            "error": str(e),
            "errors": [f"Workflow execution failed: {e}"]
        }


# For backward compatibility with existing flow_test_sandbox
def flow_test_sandbox(state: Dict[str, Any], max_iterations: int = 10) -> Dict[str, Any]:
    """
    Legacy wrapper for existing flow integration
    
    This function maintains backward compatibility with existing 
    feature_by_request_agent_v3.py integration points.
    """
    
    codebase_path = state.get("codebase_path")
    if not codebase_path:
        state["errors"] = state.get("errors", []) + ["No codebase path provided"]
        return state
        
    print("🔄 Using dedicated sandbox workflow via legacy wrapper...")
    
    # Run dedicated sandbox workflow
    results = run_sandbox_testing(codebase_path, max_iterations)
    
    # Map results back to expected format
    state["sandbox_results"] = results
    
    if not results["success"]:
        state["errors"] = state.get("errors", []) + results.get("errors", [])
        
    return state