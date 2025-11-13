"""
Sandbox Testing Flow - E2B Integration for Feature Request Agent
===============================================================

Integrates E2B sandbox testing capabilities into the LangGraph workflow
with intelligent error analysis and automated fixing.
"""

import os
from typing import Dict, Any

from sandbox_executor import (
    SandboxConfig,
    test_springboot_with_e2b
)


def flow_test_sandbox(state: Dict[str, Any], max_iterations: int = 10) -> Dict[str, Any]:
    """
    LangGraph workflow node for testing projects in E2B sandbox
    
    Args:
        state: Agent state containing codebase_path and other context
        max_iterations: Maximum number of fix iterations to attempt
        
    Returns:
        Updated state with sandbox test results
    """
    
    print("🧪 Phase: E2B Sandbox Testing")
    print("=" * 50)
    
    codebase_path = state.get("codebase_path")
    if not codebase_path:
        state["errors"].append("No codebase path provided for sandbox testing")
        return state
        
    # Detect if this is a Spring Boot project
    if not _is_springboot_project(codebase_path):
        print("ℹ️  Non-Spring Boot project detected. Skipping E2B sandbox testing.")
        state["sandbox_results"] = {
            "skipped": True,
            "reason": "Not a Spring Boot project",
            "success": True  # Don't treat as failure
        }
        return state
        
    print(f"🎯 Testing Spring Boot project: {codebase_path}")
    
    # Configure sandbox based on agent settings
    config = SandboxConfig(
        max_retries=max_iterations,
        timeout=60,
        build_timeout=300,
        run_timeout=30
    )
    
    try:
        # Execute sandbox testing
        results = test_springboot_with_e2b(codebase_path, config)
        
        # Add results to state
        state["sandbox_results"] = results
        
        # Log results
        _log_sandbox_results(results)
        
        # If testing failed, add to errors but don't stop workflow
        if not results.get("success"):
            final_status = results.get('final_status', 'unknown')
            
            # Provide more specific error messages based on final status
            if final_status == 'critical_error':
                error_msg = "Critical application startup error detected - iterations stopped early"
            elif final_status == 'critical_build_error':
                error_msg = "Critical build error detected - iterations stopped early"
            elif final_status == 'max_iterations_reached':
                error_msg = f"Sandbox testing failed after {results.get('iterations', 0)} iterations - max retries reached"
            else:
                error_msg = f"Sandbox testing failed after {results.get('iterations', 0)} iterations - Status: {final_status}"
                
            state["errors"].append(error_msg)
            
            # Add detailed error analysis for LLM to potentially use
            if results.get('error_analysis'):
                state["sandbox_error_analysis"] = results['error_analysis']
                
        return state
        
    except Exception as e:
        error_msg = f"Sandbox testing execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        state["errors"].append(error_msg)
        state["sandbox_results"] = {
            "success": False,
            "error": str(e),
            "final_status": "execution_error"
        }
        return state


def should_run_sandbox_test(state: Dict[str, Any]) -> str:
    """
    Conditional routing function to determine if sandbox testing should run
    
    Returns:
        "test_sandbox" if sandbox testing should run
        "skip_sandbox" to skip sandbox testing
    """
    
    # Check if sandbox testing was explicitly requested
    if state.get("run_sandbox_test", False):
        return "test_sandbox"
        
    # Check if this is a Spring Boot project
    codebase_path = state.get("codebase_path")
    if codebase_path and _is_springboot_project(codebase_path):
        return "test_sandbox"
        
    return "skip_sandbox"


def _is_springboot_project(codebase_path: str) -> bool:
    """Check if the codebase is a Spring Boot project"""
    
    try:
        # Check for pom.xml with Spring Boot dependencies
        pom_path = os.path.join(codebase_path, "pom.xml")
        if os.path.exists(pom_path):
            with open(pom_path, 'r', encoding='utf-8') as f:
                pom_content = f.read()
                return "spring-boot" in pom_content.lower()
                
        # Check for gradle build files
        gradle_paths = [
            os.path.join(codebase_path, "build.gradle"),
            os.path.join(codebase_path, "build.gradle.kts")
        ]
        
        for gradle_path in gradle_paths:
            if os.path.exists(gradle_path):
                with open(gradle_path, 'r', encoding='utf-8') as f:
                    gradle_content = f.read()
                    if "spring-boot" in gradle_content.lower():
                        return True
                        
        # Check for Spring Boot main class
        src_main_java = os.path.join(codebase_path, "src", "main", "java")
        if os.path.exists(src_main_java):
            for root, dirs, files in os.walk(src_main_java):
                for file in files:
                    if file.endswith(".java"):
                        java_file = os.path.join(root, file)
                        try:
                            with open(java_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if "@SpringBootApplication" in content:
                                    return True
                        except UnicodeDecodeError:
                            continue
                            
    except Exception as e:
        print(f"⚠️ Error checking if Spring Boot project: {e}")
        
    return False


def _log_sandbox_results(results: Dict[str, Any]) -> None:
    """Log detailed sandbox test results"""
    
    print("\n" + "="*50)
    print("📊 SANDBOX TEST RESULTS")
    print("="*50)
    
    print(f"✅ Success: {results.get('success', False)}")
    print(f"🔄 Iterations: {results.get('iterations', 0)}")
    print(f"📋 Final Status: {results.get('final_status', 'unknown')}")
    
    # Build results summary
    build_results = results.get('build_results', [])
    if build_results:
        successful_builds = sum(1 for r in build_results if r.success)
        print(f"🔨 Build Results: {successful_builds}/{len(build_results)} successful")
        
    # Run results summary
    run_results = results.get('run_results', [])
    if run_results:
        successful_runs = sum(1 for r in run_results if r.success)
        print(f"🏃 Run Results: {successful_runs}/{len(run_results)} successful")
        
    # Error analysis
    error_analysis = results.get('error_analysis', [])
    if error_analysis:
        print("\n🔍 Error Analysis:")
        error_types = {}
        for analysis in error_analysis:
            error_type = analysis.get('error_type')
            if error_type:
                error_types[error_type.value] = error_types.get(error_type.value, 0) + 1
                
        for error_type, count in error_types.items():
            print(f"  • {error_type}: {count} occurrence(s)")
            
    print("="*50)


def create_sandbox_test_node(max_iterations: int = 10):
    """
    Factory function to create a sandbox test node with specific configuration
    
    Args:
        max_iterations: Maximum number of fix iterations to attempt
        
    Returns:
        Configured sandbox test function
    """
    
    def sandbox_test_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return flow_test_sandbox(state, max_iterations)
        
    return sandbox_test_node


# Skip sandbox node for conditional routing
def skip_sandbox_test(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node that skips sandbox testing"""
    print("⏭️  Skipping sandbox testing")
    state["sandbox_results"] = {
        "skipped": True,
        "reason": "Sandbox testing not required for this project type",
        "success": True
    }
    return state