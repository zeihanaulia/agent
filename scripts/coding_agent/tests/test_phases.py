#!/usr/bin/env python3
"""
Phase-by-Phase Testing for Token Consumption Analysis
=======================================================

Test each phase separately to identify where tokens are being wasted.
"""

import os
import sys
import json
from pathlib import Path

# Add scripts to path
sys.path.insert(0, '/Users/zeihanaulia/Programming/research/agent/scripts/coding_agent')
os.chdir('/Users/zeihanaulia/Programming/research/agent/scripts/coding_agent')

# Import phases
from flow_analyze_context import AiderStyleRepoAnalyzer
from flow_parse_intent import flow_parse_intent
from models import setup_model
from analytics import detect_framework


def test_phase_1():
    """Phase 1: Context Analysis"""
    print("\n" + "="*80)
    print("🔍 PHASE 1: Context Analysis")
    print("="*80)
    
    codebase_path = "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo"
    
    analyzer = AiderStyleRepoAnalyzer(codebase_path, max_tokens=2048)
    context = analyzer.analyze_codebase()
    
    print("\n✓ Context Analysis Complete")
    print(f"  - Files analyzed: {len(context.get('file_map', []))} files")
    print(f"  - Context size: {len(str(context))} chars")
    print(f"  - Keys in context: {list(context.keys())}")
    
    # Show context summary
    if 'file_map' in context:
        print(f"  - File map entries: {len(context['file_map'])}")
    if 'dependencies' in context:
        print(f"  - Dependencies found: {len(context['dependencies'])}")
    
    return context


def test_phase_2(context, feature_request):
    """Phase 2: Intent Parsing"""
    print("\n" + "="*80)
    print("🎯 PHASE 2: Intent Parsing")
    print("="*80)
    
    codebase_path = "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo"
    framework_type = detect_framework(codebase_path)
    
    print(f"  - Framework detected: {framework_type}")
    print(f"  - Feature request: {feature_request[:80]}...")
    
    # Setup model for Phase 2
    _, _, model = setup_model()
    
    print(f"\n  📋 Running intent parser...")
    state = {
        "codebase_path": codebase_path,
        "feature_request": feature_request,
        "context_analysis": str(context)[:2000],  # Limit context to 2000 chars
        "full_analysis": context,  # Pass the full analysis from Phase 1
        "framework": None,
        "feature_spec": None,
        "errors": []
    }
    result_state = flow_parse_intent(
        state=state,
        analysis_model=model,
        framework_detector=detect_framework
    )
    
    spec = result_state.get("feature_spec")
    
    print(f"\n✓ Intent Parsing Complete")
    print(f"  - Feature name: {spec.feature_name if spec else 'N/A'}")
    print(f"  - Affected files: {len(spec.affected_files) if spec else 0}")
    print(f"  - New files planned: {len(spec.new_files) if spec else 0}")
    
    if spec and hasattr(spec, 'todo_list'):
        todo = spec.todo_list
        print(f"  - Todo items: {todo.total_tasks if hasattr(todo, 'total_tasks') else 'N/A'}")
    
    return spec


def test_phase_3(spec):
    """Phase 3: Impact Analysis"""
    print("\n" + "="*80)
    print("📊 PHASE 3: Impact Analysis")
    print("="*80)
    
    # Import Phase 3 flow
    from flow_analyze_impact import flow_analyze_impact
    from agents import create_impact_analysis_agent
    
    # Setup state for Phase 3
    state = {
        "codebase_path": "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo",
        "feature_spec": spec,
        "context_analysis": "minimal context",
        "framework": "FrameworkType.SPRING_BOOT",
        "errors": [],
        "current_phase": "intent_parsing_complete"
    }
    
    _, _, model = setup_model()
    
    print(f"  📋 Running impact analysis...")
    result_state = flow_analyze_impact(state, create_impact_analysis_agent, model)
    
    print(f"\n✓ Impact Analysis Complete")
    impact = result_state.get("impact_analysis", {})
    print(f"  - Files to modify: {len(impact.get('files_to_modify', []))}")
    print(f"  - Patterns found: {len(impact.get('patterns_to_follow', []))}")
    print(f"  - Constraints: {len(impact.get('constraints', []))}")
    
    return result_state


def main():
    """Run all phases sequentially"""
    print("\n" + "█"*80)
    print("█ TOKEN CONSUMPTION ANALYSIS - PHASE BY PHASE TEST")
    print("█"*80)
    
    feature_request = "Add product management system with full CRUD operations"
    
    # Phase 1
    try:
        context = test_phase_1()
        print("\n✅ Phase 1 PASSED")
    except Exception as e:
        print(f"\n❌ Phase 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Phase 2
    try:
        spec = test_phase_2(context, feature_request)
        print("\n✅ Phase 2 PASSED")
    except Exception as e:
        print(f"\n❌ Phase 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Phase 3
    try:
        result_state = test_phase_3(spec)
        print("\n✅ Phase 3 PASSED")
    except Exception as e:
        print(f"\n❌ Phase 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "█"*80)
    print("█ ALL PHASES COMPLETED SUCCESSFULLY")
    print("█"*80)


if __name__ == "__main__":
    main()
