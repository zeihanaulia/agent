"""
LangGraph Entry Point for Studio Integration
=============================================

This module handles:
1. Loading environment variables and model setup (import-time)
2. Creating workflow instance with proper model injection
3. Exposing get_graph() function for LangGraph CLI/Studio
4. Fallback to minimal dummy graph if errors occur
"""

import os
import sys
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Load environment variables - use explicit path
# First try current directory, then parent directory
env_path = None
if os.path.isfile(".env"):
    env_path = ".env"
elif os.path.isfile("../.env"):
    env_path = "../.env"

if env_path:
    result = load_dotenv(env_path)
    print(f"✅ Loaded .env from: {os.path.abspath(env_path)}")
else:
    print("⚠️  .env not found - will check environment variables only")

# ============================================================================
# SETUP MODEL AT IMPORT TIME (required for Studio)
# ============================================================================

def setup_model():
    """Setup LLM model with credentials from environment"""
    try:
        # Get model name from environment
        model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
        
        # Get API credentials
        api_key = os.getenv("LITELLM_VIRTUAL_KEY")
        api_base = os.getenv("LITELLM_API")
        
        if not api_key or not api_base:
            print("⚠️  Warning: Missing LITELLM_VIRTUAL_KEY or LITELLM_API in .env")
            print("   Studio will work but agents will fail at runtime")
            return None
        
        # Determine temperature based on model type
        is_reasoning = any(kw in model_name.lower() for kw in ["gpt-5", "5-mini", "oss", "120b", "reasoning"])
        temperature = 1.0 if is_reasoning else 0.7
        
        # Create model instance with error handling
        # For LiteLLM proxy, we need to pass default_headers with X-Api-Key
        model = ChatOpenAI(
            api_key=SecretStr(api_key),
            model=model_name,
            base_url=api_base,
            temperature=temperature,
            default_headers={
                "X-Api-Key": api_key,
                "Authorization": f"Bearer {api_key}"
            }
        )
        
        print(f"✅ LLM Model initialized: {model_name} (temp={temperature})")
        return model
        
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️  Model initialization warning: {error_msg[:100]}")
        print("   This is normal if API credentials aren't valid yet")
        print("   Studio will still load - agents will fail at runtime")
        return None


# Initialize model at import time
try:
    analysis_model = setup_model()
except Exception as e:
    print(f"❌ Error setting up model: {e}")
    analysis_model = None

# ============================================================================
# IMPORT WORKFLOW CREATION FUNCTION
# ============================================================================

try:
    # Import from the main script (without running main())
    # We need to import the function, not execute it
    import importlib.util
    
    spec = importlib.util.spec_from_file_location(
        "feature_by_request_agent_v3",
        "/Users/zeihanaulia/Programming/research/agent/scripts/feature_by_request_agent_v3.py"
    )
    
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        # Don't execute if __name__ == "__main__" in the module
        sys.modules["feature_by_request_agent_v3"] = module
        spec.loader.exec_module(module)
        
        # Get the workflow creation function
        create_feature_request_workflow = module.create_feature_request_workflow
        
        print("✅ Workflow creation function imported successfully")
    else:
        raise ImportError("Could not load spec for feature_by_request_agent_v3")
        
except Exception as e:
    print(f"⚠️  Warning: Could not import workflow: {e}")
    create_feature_request_workflow = None

# ============================================================================
# CREATE WORKFLOW INSTANCE
# ============================================================================

def create_workflow_with_model():
    """Create the workflow with the initialized model"""
    if not create_feature_request_workflow:
        print("❌ Cannot create workflow: function not imported")
        return None
    
    # Model is optional - agents will fail at runtime if it's None, but graph can still be created
    try:
        # CRITICAL: Call setup_model() in the imported module to set global variables
        # This ensures analysis_model, model_name, and temperature are set before workflow creation
        import sys
        feature_module = sys.modules.get("feature_by_request_agent_v3")
        if feature_module and hasattr(feature_module, 'setup_model'):
            try:
                model_name, temperature, model = feature_module.setup_model()
                print(f"✅ Model setup in workflow module: {model_name}")
            except Exception as e:
                print(f"⚠️  Model setup failed in workflow: {e}")
        
        # Create workflow - pass model if available, agents will handle None model gracefully
        workflow = create_feature_request_workflow()
        print("✅ Workflow instance created")
        return workflow
    except ValueError as e:
        # Model validation error - this is expected and not fatal for graph creation
        if "Model not configured" in str(e):
            print(f"⚠️  {e}")
            print("   Studio graph will load but agents will fail at runtime")
            return None
        raise
    except Exception as e:
        print(f"❌ Error creating workflow: {e}")
        import traceback
        traceback.print_exc()
        return None


# Create the workflow instance
_workflow_instance: Optional[object] = None

def get_graph():
    """
    Expose graph for LangGraph Studio/CLI
    
    This is called by LangGraph when loading the graph.
    Returns the compiled workflow graph.
    """
    global _workflow_instance
    
    if _workflow_instance is None:
        _workflow_instance = create_workflow_with_model()
    
    if _workflow_instance is None:
        # Fallback: return minimal dummy graph
        print("⚠️  Returning minimal dummy graph (workflow creation failed)")
        from langgraph.graph import StateGraph, START
        from typing import TypedDict
        
        class ErrorState(TypedDict):
            error: str
        
        dummy_graph = StateGraph(ErrorState)
        dummy_graph.add_node("error", lambda state: {"error": "Workflow failed to load"})
        dummy_graph.add_edge(START, "error")
        return dummy_graph.compile()
    
    return _workflow_instance


# ============================================================================
# DEBUG INFO (printed when module is imported)
# ============================================================================

if __name__ != "__main__":
    print("\n" + "=" * 80)
    print("🚀 LangGraph Entry Point Initialized")
    print("=" * 80)
    print(f"📁 Project Root: /Users/zeihanaulia/Programming/research/agent")
    print(f"🤖 Model Status: {'✅ Configured' if analysis_model else '⚠️  Not configured'}")
    print(f"📊 Workflow Status: {'✅ Ready' if create_feature_request_workflow else '⚠️  Not loaded'}")
    print("=" * 80 + "\n")
