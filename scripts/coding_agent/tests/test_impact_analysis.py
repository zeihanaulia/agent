#!/usr/bin/env python3
"""
Test script for Phase 3: Impact Analysis
=========================================

Tests the flow_analyze_impact.py functionality with mock agents.
Focus: Architecture pattern recognition and file impact analysis.
"""

import sys
import os
from unittest.mock import Mock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flow_analyze_impact import flow_analyze_impact
from feature_by_request_agent_v3 import AgentState, FeatureSpec


def create_mock_impact_analysis_agent(codebase_path: str, analysis_model):
    """Create mock impact analysis agent for testing"""
    mock_agent = Mock()
    mock_agent.invoke.return_value = {
        "patterns_to_follow": ["REST API", "Service Layer", "Repository Pattern"],
        "architecture_insights": "Spring Boot MVC architecture detected",
        "risks_identified": ["Database schema changes required"],
        "estimated_complexity": "medium"
    }
    return mock_agent


def create_mock_analysis_model():
    """Create mock analysis model"""
    return Mock()


def test_impact_analysis_with_valid_spec():
    """Test impact analysis with valid feature spec"""
    print("🧪 Testing Impact Analysis with Valid Spec")
    print("-" * 50)

    # Create test state
    state: AgentState = {
        'codebase_path': '/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo',
        'feature_request': 'Add product management with CRUD operations',
        'context_analysis': 'Spring Boot project with MVC architecture',
        'feature_spec': FeatureSpec(
            feature_name='Product Management',
            intent_summary='Add product management with CRUD operations',
            affected_files=['ProductController.java', 'ProductService.java', 'Product.java'],
            new_files=['ProductController.java', 'ProductService.java', 'Product.java']
        ),
        'impact_analysis': None,
        'structure_assessment': None,
        'code_patches': None,
        'execution_results': None,
        'errors': [],
        'dry_run': True,
        'current_phase': 'structure_validation_complete',
        'human_approval_required': False,
        'framework': 'spring-boot'
    }

    # Run impact analysis
    result_state = flow_analyze_impact(
        state,
        create_mock_impact_analysis_agent,
        create_mock_analysis_model()
    )

    # Verify results
    assert result_state['impact_analysis'] is not None, "Impact analysis should be populated"
    assert 'patterns_to_follow' in result_state['impact_analysis'], "Should identify patterns"
    assert 'files_to_modify' in result_state['impact_analysis'], "Should identify files to modify"
    assert result_state['current_phase'] == 'impact_analysis_complete', "Phase should be complete"
    assert len(result_state['errors']) == 0, f"No errors expected, got: {result_state['errors']}"

    print("  ✅ Impact analysis completed successfully")
    print(f"  📊 Patterns identified: {len(result_state['impact_analysis']['patterns_to_follow'])}")
    print(f"  📁 Files to modify: {len(result_state['impact_analysis']['files_to_modify'])}")

    return True


def test_impact_analysis_without_spec():
    """Test impact analysis when no feature spec is available"""
    print("\n🧪 Testing Impact Analysis without Feature Spec")
    print("-" * 50)

    # Create test state without feature spec
    state: AgentState = {
        'codebase_path': '/test/path',
        'feature_request': 'Test feature',
        'context_analysis': None,
        'feature_spec': None,  # No feature spec
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

    # Run impact analysis
    result_state = flow_analyze_impact(
        state,
        create_mock_impact_analysis_agent,
        create_mock_analysis_model()
    )

    # Verify error handling
    assert result_state['impact_analysis'] is None, "Impact analysis should not be populated"
    assert len(result_state['errors']) == 1, "Should have one error"
    assert "No feature spec available" in result_state['errors'][0], "Should mention missing feature spec"

    print("  ✅ Error handling works correctly")
    print(f"  ❌ Expected error: {result_state['errors'][0]}")

    return True


def test_impact_analysis_with_agent_error():
    """Test impact analysis with agent error simulation"""
    print("\n🧪 Testing Impact Analysis with Agent Error")
    print("-" * 50)

    def failing_agent_factory(codebase_path: str, analysis_model):
        """Create agent that raises exception"""
        mock_agent = Mock()
        mock_agent.invoke.side_effect = Exception("Agent connection failed")
        return mock_agent

    # Create test state
    state: AgentState = {
        'codebase_path': '/test/path',
        'feature_request': 'Test feature',
        'context_analysis': None,
        'feature_spec': FeatureSpec(
            feature_name='Test Feature',
            intent_summary='Test implementation',
            affected_files=['Test.java'],
            new_files=[]
        ),
        'impact_analysis': None,
        'structure_assessment': None,
        'code_patches': None,
        'execution_results': None,
        'errors': [],
        'dry_run': True,
        'current_phase': 'structure_validation_complete',
        'human_approval_required': False,
        'framework': None
    }

    # Run impact analysis
    result_state = flow_analyze_impact(
        state,
        failing_agent_factory,
        create_mock_analysis_model()
    )

    # Verify error handling
    assert result_state['impact_analysis'] is None, "Impact analysis should not be populated"
    assert len(result_state['errors']) == 1, "Should have one error"
    assert "Impact analysis error" in result_state['errors'][0], "Should mention impact analysis error"

    print("  ✅ Error handling works correctly")
    print(f"  ❌ Expected error: {result_state['errors'][0]}")

    return True


def main():
    """Run all impact analysis tests"""
    print("🚀 Testing Phase 3: Impact Analysis")
    print("=" * 60)

    test_results = []

    try:
        # Test 1: Valid spec
        success1 = test_impact_analysis_with_valid_spec()
        test_results.append(("Valid Feature Spec", success1))

        # Test 2: No spec
        success2 = test_impact_analysis_without_spec()
        test_results.append(("Missing Feature Spec", success2))

        # Test 3: Agent error
        success3 = test_impact_analysis_with_agent_error()
        test_results.append(("Agent Error Handling", success3))

        # Summary
        print("\n" + "=" * 60)
        print("📊 IMPACT ANALYSIS TEST RESULTS")
        print("=" * 60)

        passed = 0
        for test_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} - {test_name}")
            if success:
                passed += 1

        print("\n" + "=" * 60)
        if passed == len(test_results):
            print("🎉 ALL IMPACT ANALYSIS TESTS PASSED!")
            print("\nCoverage:")
            print("  ✅ Architecture pattern recognition")
            print("  ✅ File impact identification")
            print("  ✅ Error handling (missing spec)")
            print("  ✅ Error handling (agent failures)")
            print("  ✅ State management and phase transitions")
            return True
        else:
            print(f"⚠️  {passed}/{len(test_results)} tests passed")
            return False

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)