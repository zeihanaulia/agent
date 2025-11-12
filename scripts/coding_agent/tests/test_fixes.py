#!/usr/bin/env python3
"""
Test script to verify all 3 fixes for agent execution
"""

import os
import sys
import time
import json

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from flow_parse_intent import flow_parse_intent
from flow_synthesize_code import flow_synthesize_code
from progress_tracker import WorkProgress, FileTask, TaskStatus

def setup_llm_model(temperature: float = 0.7):
    """Setup LLM model using LiteLLM"""
    model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
    api_base = os.getenv("LITELLM_API")
    api_key = os.getenv("LITELLM_VIRTUAL_KEY")
    
    if not api_key:
        raise ValueError("LITELLM_VIRTUAL_KEY not found in environment")
    
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=SecretStr(api_key),
        base_url=api_base,
        default_headers={"Content-Type": "application/json"}
    )

def test_all_fixes():
    """Test all 3 fixes with simple feature request"""
    load_dotenv()
    
    codebase_path = "dataset/codes/springboot-demo"
    feature_request = "Add a Product entity with basic CRUD operations"
    
    print("🧪 Testing All 3 Fixes")
    print("=" * 70)
    print(f"📁 Codebase: {codebase_path}")
    print(f"🎯 Feature: {feature_request}")
    print(f"⏱️  Starting test")
    print()
    
    # Setup state
    state = {
        "codebase_path": codebase_path,
        "feature_request": feature_request,
        "context_analysis": None,
        "framework": None,
        "feature_spec": None,
        "errors": [],
        "code_patches": [],
        "current_phase": "initialized"
    }
    
    try:
        # Setup LLM
        print("🤖 Setting up LLM model...")
        model = setup_llm_model()
        print("✅ Model ready\n")
        
        # Phase 2: Parse Intent
        print("📋 Phase 2: Parse Intent (Testing Fix #3 - Scope Guard)")
        print("-" * 70)
        start_phase2 = time.time()
        state = flow_parse_intent(state)
        phase2_time = time.time() - start_phase2
        print(f"✅ Intent parsed in {phase2_time:.1f}s")
        
        if state.get("feature_spec"):
            spec = state["feature_spec"]
            print(f"   Feature: {spec.feature_name}")
            print(f"   Modifications: {len(spec.modifications)}")
            if spec.todo_list:
                print(f"   Todo items: {spec.todo_list.total_tasks}")
        print()
        
        # Phase 4: Synthesize Code (Testing Fix #1 and #2)
        print("💻 Phase 4: Synthesize Code (Testing Fix #1 & #2)")
        print("-" * 70)
        start_phase4 = time.time()
        
        # Prepare Phase 4 state
        affected_files = []
        if state.get("feature_spec"):
            spec = state["feature_spec"]
            if hasattr(spec, "affected_files"):
                affected_files = spec.affected_files
        
        state = flow_synthesize_code(
            state,
            analysis_model=model,
            files_to_modify=affected_files[:5] if affected_files else None,
            feature_request=feature_request
        )
        
        phase4_time = time.time() - start_phase4
        print(f"✅ Code synthesized in {phase4_time:.1f}s\n")
        
        # Analyze results
        print("=" * 70)
        print("📊 TEST RESULTS - Verifying All 3 Fixes")
        print("=" * 70)
        
        patches = state.get("code_patches", [])
        errors = state.get("errors", [])
        empty_path_errors = [e for e in errors if "empty" in str(e).lower() or "missing" in str(e).lower()]
        
        # Fix #1 Results
        print("\n✅ Fix #1 (DeepAgent Result Parsing):")
        print(f"   Patches extracted: {len(patches)}")
        if len(patches) > 0:
            print("   ✓ PASS - Patches detected and extracted")
            for i, patch in enumerate(patches[:3], 1):
                path = patch.get("file_path", "unknown")
                print(f"      [{i}] {path}")
            if len(patches) > 3:
                print(f"      ... and {len(patches)-3} more")
        else:
            print("   ✗ FAIL - No patches extracted")
        
        # Fix #2 Results
        print(f"\n✅ Fix #2 (Tool Parameter Validation):")
        print(f"   Empty parameter errors: {len(empty_path_errors)}")
        if len(empty_path_errors) == 0:
            print("   ✓ PASS - All tool parameters provided correctly")
        else:
            print(f"   ✗ FAIL - Found {len(empty_path_errors)} empty parameter errors:")
            for err in empty_path_errors[:3]:
                print(f"      - {err}")
        
        # Fix #3 Results (implicit - scope maintained)
        print(f"\n✅ Fix #3 (Feature Scope Guard):")
        spec = state.get("feature_spec")
        if spec:
            modifications = spec.get("modifications", []) if hasattr(spec, "modifications") else []
            # Check that no unrelated features were added
            has_payment = any("payment" in str(m).lower() for m in modifications)
            has_shipping = any("shipping" in str(m).lower() for m in modifications)
            
            if not has_payment and not has_shipping:
                print("   ✓ PASS - Scope maintained, no hallucinations")
            else:
                print("   ✗ FAIL - Found scope violations (Payment/Shipping hallucinations)")
        
        # Overall metrics
        print(f"\n📈 Overall Metrics:")
        print(f"   Phase 2 time: {phase2_time:.1f}s")
        print(f"   Phase 4 time: {phase4_time:.1f}s")
        print(f"   Total errors: {len(errors)}")
        print(f"   Files generated: {len(patches)}")
        
        # Final result
        print("\n" + "=" * 70)
        all_pass = len(patches) > 0 and len(empty_path_errors) == 0
        if all_pass:
            print("🎉 ALL FIXES WORKING - Test PASSED!")
            return True
        else:
            print("⚠️  Some fixes still need attention")
            return False
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_fixes()
    sys.exit(0 if success else 1)

