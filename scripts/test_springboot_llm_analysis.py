#!/usr/bin/env python3
"""
Test script for LLM-enhanced Spring Boot analysis
"""

import os
import sys
sys.path.append('/Users/zeihanaulia/Programming/research/agent/scripts')

from coding_agent.flow_analize_context import analyze_context, AiderStyleRepoAnalyzer

def test_llm_analysis():
    """Test LLM-enhanced analysis on Spring Boot project"""
    print("🧪 Testing LLM-enhanced Spring Boot analysis")
    print("=" * 60)

    # Test state for Spring Boot analysis
    test_state = {
        "codebase_path": "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-ecommerce",
        "feature_request": "Add product management with CRUD endpoints and voucher system",
        "context_analysis": None,
        "feature_spec": None,
        "impact_analysis": None,
        "structure_assessment": None,
        "code_patches": None,
        "execution_results": None,
        "errors": [],
        "dry_run": True,
        "current_phase": "initialized",
        "human_approval_required": False,
        "framework": None
    }

    print("📊 BEFORE analysis:")
    print(f"  - Model: {os.getenv('LITELLM_MODEL', 'Not set')}")
    print(f"  - API: {os.getenv('LITELLM_API', 'Not set')}")
    print(f"  - Key configured: {'Yes' if os.getenv('LITELLM_VIRTUAL_KEY') else 'No'}")

    try:
        # Run the analysis
        result_state = analyze_context(test_state)

        print("\n📊 AFTER analysis:")
        print(f"  - Phase: {result_state['current_phase']}")
        print(f"  - Errors: {len(result_state['errors'])}")

        print("\n🔍 ANALYSIS RESULTS:")
        if result_state['context_analysis']:
            print(result_state['context_analysis'][:1000] + "..." if len(result_state['context_analysis']) > 1000 else result_state['context_analysis'])
        else:
            print("No analysis results generated")

        return result_state

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_llm_analysis()