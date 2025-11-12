"""
PHASE 3: IMPACT ANALYSIS - Architecture Pattern Recognition
===========================================================

Responsible for:
- Analyzing codebase architecture and patterns
- Identifying files affected by feature request
- Extracting design patterns in use
- Building architecture insights for code synthesis
"""

import os
import re
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from feature_by_request_agent_v3 import AgentState


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


def extract_patterns_from_content(content_str: str) -> List[str]:
    """Extract design patterns mentioned in content"""
    patterns = re.findall(r'(?:Pattern|pattern|Design|design):\s*([^,.\n]+)', content_str)
    return patterns


def find_java_files(codebase_path: str) -> List[str]:
    """Find all Java files in a Spring Boot project"""
    java_files = []
    java_src_dir = os.path.join(codebase_path, "src/main/java")
    
    if os.path.isdir(java_src_dir):
        for root, dirs, files in os.walk(java_src_dir):
            for file in files:
                if file.endswith(".java"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, codebase_path)
                    java_files.append(rel_path)
    
    return java_files


def build_analysis_prompt(feature_request: str, files_to_analyze: List[str]) -> str:
    """Build the architecture analysis prompt for the agent"""
    return f"""
FEATURE REQUEST: {feature_request}

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

Be SPECIFIC - use exact file paths from the list above.
"""


def parse_agent_response(result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse agent response and extract insights
    
    Returns:
        Dictionary with architecture_insights and patterns_to_follow
    """
    analysis = {
        "files_to_modify": [],
        "architecture_insights": "",
        "patterns_to_follow": [],
        "testing_approach": "",
        "constraints": [],
        "todos": []
    }
    
    if result and "messages" in result:
        for msg in result.get("messages", []):
            # Extract reasoning and insights
            if hasattr(msg, "content") and msg.content:
                content_str = str(msg.content)
                analysis["architecture_insights"] = content_str[:1000]  # Keep summary
                
                # Extract patterns mentioned
                patterns = extract_patterns_from_content(content_str)
                analysis["patterns_to_follow"].extend(patterns)
    
    return analysis


def flow_analyze_impact(state: "AgentState", create_impact_analysis_agent, analysis_model) -> "AgentState":
    """
    Phase 3: Impact Analysis - Identify architecture patterns and affected files
    
    Args:
        state: Current workflow state
        create_impact_analysis_agent: Factory function to create impact analysis agent
        analysis_model: LLM model instance for analysis
    
    Returns:
        Updated state with impact_analysis results
    """
    print("📊 Phase 3: Architecture analysis - identifying patterns and impact...")
    
    codebase_path = state["codebase_path"]
    spec = state.get("feature_spec")

    if not spec:
        state["errors"].append("No feature spec available for impact analysis")
        return state

    try:
        agent = create_impact_analysis_agent(codebase_path, analysis_model)
        
        # Find Java files (for Spring Boot projects)
        java_files = find_java_files(codebase_path)
        
        # Use real files detected from filesystem
        files_to_analyze = java_files if java_files else spec.affected_files
        
        # Build and execute analysis prompt
        prompt = build_analysis_prompt(spec.intent_summary, files_to_analyze)
        
        # Use timeout-protected invoke to prevent hanging
        result = invoke_with_timeout(agent, {"input": prompt}, timeout_seconds=30)
        
        # Extract files from agent response or use default files_to_analyze
        files_to_modify = files_to_analyze if files_to_analyze else spec.affected_files
        
        # Parse agent response
        analysis = parse_agent_response(result)
        analysis["files_to_modify"] = files_to_modify
        
        state["impact_analysis"] = analysis
        state["current_phase"] = "impact_analysis_complete"
        
        print(f"  ✓ Files to modify: {len(files_to_modify)} file(s)")
        print(f"  ✓ Patterns identified: {len(analysis['patterns_to_follow'])} pattern(s)")
        
    except Exception as e:
        print(f"  ❌ Error during impact analysis: {e}")
        import traceback
        traceback.print_exc()
        state["errors"].append(f"Impact analysis error: {str(e)}")

    return state
