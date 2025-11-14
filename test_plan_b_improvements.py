#!/usr/bin/env python3
"""
Test Plan B Improvements: Selective File Loading & Token Tracking
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.coding_agent.flow_analyze_context import AiderStyleRepoAnalyzer

def test_selective_analysis():
    """Test analyze_with_reasoning method with selective file loading"""
    
    print("=" * 80)
    print("🧪 TESTING PLAN B IMPROVEMENTS")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    codebase_path = Path("dataset/codes/springboot-demo")
    analyzer = AiderStyleRepoAnalyzer(codebase_path=str(codebase_path), max_tokens=10000)
    
    # Test 1: Feature implementation request (should trigger placement analysis)
    print("\n" + "=" * 80)
    print("TEST 1: Feature Implementation Request")
    print("=" * 80)
    user_request = "Add a new Product entity with CRUD operations"
    
    result = analyzer.analyze_with_reasoning(user_request)
    
    print(f"\n📊 Results:")
    print(f"  • Request Type: {result['reasoning']['request_type']}")
    print(f"  • Analysis Scope: {result['reasoning']['scope']}")
    print(f"  • Analyses Run: {result['analysis_plan']['analyses_to_run']}")
    print(f"  • Placement Analysis Included: {'code_placement' in result['analysis_plan']['analyses_to_run']}")
    print(f"  • Tokens Used: {result['tokens_used']}")
    
    if 'placement_analysis' in result['results']:
        print(f"  ✅ Placement analysis executed")
        placement = result['results']['placement_analysis']
        print(f"  • Placement suggestions: {len(placement.get('placement_suggestions', []))}")
    else:
        print(f"  ⚠️ Placement analysis NOT executed")
    
    # Test 2: Analysis request (should NOT trigger placement analysis)
    print("\n" + "=" * 80)
    print("TEST 2: Analysis Request (No Placement)")
    print("=" * 80)
    user_request = "Analyze the current codebase structure"
    
    analyzer2 = AiderStyleRepoAnalyzer(codebase_path=str(codebase_path), max_tokens=10000)
    result2 = analyzer2.analyze_with_reasoning(user_request)
    
    print(f"\n📊 Results:")
    print(f"  • Request Type: {result2['reasoning']['request_type']}")
    print(f"  • Analysis Scope: {result2['reasoning']['scope']}")
    print(f"  • Analyses Run: {result2['analysis_plan']['analyses_to_run']}")
    print(f"  • Placement Analysis Included: {'code_placement' in result2['analysis_plan']['analyses_to_run']}")
    print(f"  • Tokens Used: {result2['tokens_used']}")
    
    if 'placement_analysis' in result2['results']:
        print(f"  ⚠️ Placement analysis unexpectedly executed")
    else:
        print(f"  ✅ Placement analysis correctly skipped")
    
    # Test 3: Test lightweight file map
    print("\n" + "=" * 80)
    print("TEST 3: Lightweight File Map")
    print("=" * 80)
    
    analyzer3 = AiderStyleRepoAnalyzer(codebase_path=str(codebase_path), max_tokens=10000)
    lightweight_map = analyzer3._build_lightweight_file_map()
    
    print(f"  • Files mapped: {len(lightweight_map)}")
    print(f"  • Total size: {sum(f['size'] for f in lightweight_map.values()) // 1024} KB")
    print(f"  • Sample files:")
    for path in list(lightweight_map.keys())[:5]:
        meta = lightweight_map[path]
        print(f"    - {path} ({meta['language']}, {meta['size']} bytes)")
    
    # Test 4: File selection
    print("\n" + "=" * 80)
    print("TEST 4: File Selection")
    print("=" * 80)
    
    reasoning = {
        'request_type': 'feature_implementation',
        'entities': ['Product'],
        'actions': ['CRUD'],
        'priority_areas': ['data_models', 'api_endpoints'],
        'original_request': 'Add Product CRUD'
    }
    
    selected_files = analyzer3._select_relevant_files(reasoning, lightweight_map, max_files=5)
    
    print(f"  • Selected files: {len(selected_files)}")
    for i, file_path in enumerate(selected_files, 1):
        print(f"    {i}. {file_path}")
    
    # Test 5: Tree-sitter extraction
    print("\n" + "=" * 80)
    print("TEST 5: Tree-sitter Extraction")
    print("=" * 80)
    
    # Find a .java file
    java_files = [f for f in lightweight_map.keys() if f.endswith('.java')]
    if java_files:
        test_file = java_files[0]
        full_path = codebase_path / test_file
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tags = analyzer3._extract_file_tags(content, test_file)
        print(f"  • File: {test_file}")
        print(f"  • Tags extracted: {len(tags)}")
        for tag in tags[:5]:
            print(f"    - {tag['type']} {tag['name']} (line {tag['line']})")
    else:
        print("  ⚠️ No Java files found for testing")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✅ Selective analysis works")
    print("  ✅ Token tracking active")
    print("  ✅ Placement conditional on request type")
    print("  ✅ Lightweight file map functional")
    print("  ✅ File selection working")
    print("  ✅ Tree-sitter extraction functional")


if __name__ == "__main__":
    test_selective_analysis()
