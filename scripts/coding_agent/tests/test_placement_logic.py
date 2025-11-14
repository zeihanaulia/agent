#!/usr/bin/env python3
"""
Test Placement Logic - Verify discovered packages vs hardcoded templates
"""

import sys
import json
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts" / "coding_agent"))

from flow_analyze_context import AiderStyleRepoAnalyzer

def test_placement_logic():
    """Test that placement logic uses discovered packages, not hardcoded templates"""
    
    print("=" * 80)
    print("🧪 TESTING PLACEMENT LOGIC")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    codebase_path = "dataset/codes/springboot-demo"
    print(f"📂 Analyzing: {codebase_path}")
    print()
    
    analyzer = AiderStyleRepoAnalyzer(codebase_path, max_tokens=4096)
    
    # Run full analysis to get structure
    print("🔍 Step 1: Analyzing codebase structure...")
    analysis_result = analyzer.analyze_codebase()
    
    structure = analysis_result.get("structure", {})
    discovered_packages = structure.get("java_packages", [])
    
    print(f"✅ Discovered {len(discovered_packages)} Java packages:")
    for pkg in discovered_packages:
        print(f"   • {pkg}")
    print()
    
    # Test placement inference
    feature_requests = [
        "Add Product entity for inventory management",
        "Create REST controller for product endpoints",
        "Implement ProductService for business logic"
    ]
    
    print("🎯 Step 2: Testing placement suggestions...")
    print()
    
    for idx, feature_request in enumerate(feature_requests, 1):
        print(f"Test {idx}: {feature_request}")
        print("-" * 80)
        
        placement_result = analyzer.infer_code_placement(
            feature_request=feature_request,
            analysis_result=analysis_result
        )
        
        suggestions = placement_result.get("placement_suggestions", [])
        discovery_method = placement_result.get("discovery_method", "unknown")
        
        print(f"  Discovery Method: {discovery_method}")
        print(f"  Suggestions: {len(suggestions)}")
        print()
        
        for suggestion in suggestions:
            print(f"  📍 Type: {suggestion.get('type')}")
            print(f"     Package: {suggestion.get('package')}")
            print(f"     Directory: {suggestion.get('directory')}")
            print(f"     Source: {suggestion.get('source')}")
            print()
        
        # Verify: Should NOT contain hardcoded 'com.example.entity' or 'com.example.controller'
        for suggestion in suggestions:
            package = suggestion.get('package', '')
            if package.startswith('com.example.') and not package.startswith('com.example.springboot'):
                print(f"  ❌ FAIL: Found hardcoded template package: {package}")
                print(f"     Expected: com.example.springboot.* (discovered)")
                return False
            elif package.startswith('com.example.springboot'):
                print(f"  ✅ PASS: Using discovered package: {package}")
        
        print()
    
    print("=" * 80)
    print("✅ ALL TESTS PASSED - Placement logic uses discovered packages!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_placement_logic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
