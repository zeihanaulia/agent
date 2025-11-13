#!/usr/bin/env python3
"""
Test script for E2B Sandbox Integration
=======================================

Simple test to verify the sandbox functionality works before full integration.
"""

import os
import sys
from pathlib import Path

# Add the coding_agent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sandbox_executor import test_springboot_with_e2b, SandboxConfig

def main():
    """Test the sandbox executor with the Spring Boot project"""
    
    # Test project path
    project_path = "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo"
    
    if not os.path.exists(project_path):
        print(f"❌ Project path does not exist: {project_path}")
        sys.exit(1)
        
    print("🧪 Testing E2B Sandbox Integration")
    print("=" * 50)
    
    # Configure for testing
    config = SandboxConfig(
        max_retries=3,
        timeout=60,
        build_timeout=300,
        run_timeout=30
    )
    
    try:
        results = test_springboot_with_e2b(project_path, config)
        
        print("\n" + "="*50)
        print("📊 FINAL RESULTS")
        print("="*50)
        print(f"Success: {results['success']}")
        print(f"Iterations: {results['iterations']}")
        print(f"Final Status: {results['final_status']}")
        
        if results.get('error_analysis'):
            print("\n🔍 Error Analysis:")
            for analysis in results['error_analysis']:
                print(f"  Iteration {analysis['iteration']} ({analysis['phase']}): {analysis['error_type'].value}")
                print(f"    Details: {analysis['error_details']}")
                print(f"    Suggested fixes: {', '.join(analysis['suggested_fixes'])}")
                
        if results['success']:
            print("\n🎉 Sandbox integration test PASSED!")
            sys.exit(0)
        else:
            print("\n❌ Sandbox integration test FAILED!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()