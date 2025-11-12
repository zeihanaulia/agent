#!/usr/bin/env python3
"""
Test script for running LLM-enhanced context analysis on Spring Boot project
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flow_analyze_context import analyze_context, AgentState

def run_llm_context_analysis():
    """Run LLM-enhanced context analysis on Spring Boot project"""

    # Initialize state for Spring Boot project
    initial_state: AgentState = {
        'codebase_path': '/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo',
        'feature_request': 'Add product management feature with CRUD operations',
        'context_analysis': None,
        'feature_spec': None,
        'impact_analysis': None,
        'structure_assessment': None,
        'code_patches': None,
        'execution_results': None,
        'errors': [],
        'dry_run': True,
        'current_phase': 'initialized',
        'human_approval_required': False,
        'framework': None
    }

    print("🚀 Running LLM-Enhanced Context Analysis")
    print("=" * 60)
    print(f"📁 Codebase: {initial_state['codebase_path']}")
    print(f"🎯 Feature: {initial_state['feature_request']}")
    print(f"🤖 LLM Analysis: Enabled")
    print()

    # Phase 1: Context Analysis (LLM-enhanced)
    print("📊 Phase 1: Context Analysis")
    print("-" * 30)

    try:
        context_state = analyze_context(initial_state)
        print("✅ Context analysis completed")
        print()

        # Display results
        print("📈 Analysis Results")
        print("=" * 60)
        print(f"🏗️ Framework Detected: {context_state.get('framework', 'Unknown')}")
        print(f"📊 Context Analysis: {'✅ Completed' if context_state['context_analysis'] else '❌ Failed'}")
        print(f"❌ Errors: {len(context_state['errors'])} encountered")

        if context_state['errors']:
            print("\n🚨 Errors Encountered:")
            for error in context_state['errors']:
                print(f"  - {error}")

        if context_state['context_analysis']:
            print("\n🔍 LLM-Enhanced Analysis Output:")
            print("-" * 40)
            print(context_state['context_analysis'])

        return context_state

    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return None

if __name__ == "__main__":
    run_llm_context_analysis()