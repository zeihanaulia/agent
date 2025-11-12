#!/usr/bin/env python3
"""
Quick Context Flow Analysis
============================

Check if context properly flows from Phase 1 → Phase 2 → Phase 3 → Phase 4
"""

import os
import sys

sys.path.insert(0, '/Users/zeihanaulia/Programming/research/agent/scripts/coding_agent')
os.chdir('/Users/zeihanaulia/Programming/research/agent/scripts/coding_agent')

from flow_analyze_context import AiderStyleRepoAnalyzer, infer_app_type
from analytics import detect_framework


def test_context_flow():
    """Test how context flows through phases"""
    print("\n" + "="*80)
    print("CONTEXT FLOW ANALYSIS")
    print("="*80)
    
    codebase_path = "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo"
    
    # Phase 1: Analyze context
    print("\n📍 PHASE 1: Context Analysis")
    print("-" * 80)
    
    analyzer = AiderStyleRepoAnalyzer(codebase_path, max_tokens=2048)
    context = analyzer.analyze()
    
    context_size_kb = len(str(context)) / 1024
    print(f"✓ Context generated: {context_size_kb:.2f} KB")
    print(f"  Keys: {list(context.keys())}")
    
    # Check what's in context
    if 'file_map' in context:
        file_map = context['file_map']
        print(f"  - File map: {len(file_map)} files")
        if file_map:
            sample_files = list(file_map.items())[:2]
            for fname, fdata in sample_files:
                print(f"    • {fname}: {type(fdata).__name__}")
    
    if 'structured_summary' in context:
        summary = context['structured_summary']
        print(f"  - Summary size: {len(str(summary))} chars")
        print(f"    Content: {str(summary)[:100]}...")
    
    # Check framework detection
    print("\n📍 PHASE 2: Framework Detection")
    print("-" * 80)
    
    framework = detect_framework(codebase_path)
    print(f"✓ Framework: {framework}")
    
    # Show what gets passed to Phase 2
    print("\n📍 WHAT PHASE 1 PASSES TO PHASE 2")
    print("-" * 80)
    print("Context keys that Phase 2 receives:")
    for key in context.keys():
        value = context[key]
        if isinstance(value, dict):
            print(f"  • {key}: dict with {len(value)} keys")
        elif isinstance(value, list):
            print(f"  • {key}: list with {len(value)} items")
        elif isinstance(value, str):
            print(f"  • {key}: str with {len(value)} chars")
        else:
            print(f"  • {key}: {type(value).__name__}")
    
    # Show file_map in detail
    print("\n📍 DETAILED: file_map Contents")
    print("-" * 80)
    if 'file_map' in context:
        file_map = context['file_map']
        print(f"Total files: {len(file_map)}")
        for i, (fname, fdata) in enumerate(file_map.items(), 1):
            if isinstance(fdata, dict):
                print(f"  {i}. {fname}")
                print(f"     Keys: {list(fdata.keys())}")
                if 'content' in fdata:
                    content_size = len(fdata['content'])
                    print(f"     Content size: {content_size} bytes")
            else:
                print(f"  {i}. {fname}: {type(fdata).__name__} ({len(str(fdata))} chars)")
    
    return context


if __name__ == "__main__":
    try:
        context = test_context_flow()
        print("\n" + "="*80)
        print("✅ Analysis Complete")
        print("="*80)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
