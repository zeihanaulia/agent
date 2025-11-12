#!/usr/bin/env python3
"""
TEST: Enhanced validate_structure with Feedback Loop
======================================================

Test the new enhanced validator with iterative refinement.

Test features:
1. Validates plan from parse_intent
2. Checks for missing layers
3. Auto-creates directories
4. Validates SOLID principles mapping
5. Iterative refinement (max 3 rounds)
6. Production-readiness scoring
7. Feedback generation for parse_intent
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flow_validate_structure import (
    EnhancedStructureValidator,
    validate_structure_with_feedback,
    StructureViolation
)
from framework_instructions import detect_framework

# ==============================================================================
# TEST DATA
# ==============================================================================

CODEBASE_PATH = "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo"

# Mock feature spec from parse_intent
MOCK_FEATURE_SPEC = {
    "feature_name": "Add product management",
    "intent_summary": "Add product management feature with CRUD operations",
    "affected_files": [
        "src/main/java/com/example/springboot/HelloController.java",
        "src/main/java/com/example/springboot/Application.java"
    ],
    "new_files": [
        "ProductEntity.java",
        "ProductRepository.java",
        "ProductService.java",
        "ProductController.java",
        "ProductNotFoundException.java"
    ],
    "modifications": [],
    "notes": ""
}

# Mock new files planning from infer_new_files_needed
MOCK_NEW_FILES_PLANNING = {
    "suggested_files": [
        {
            "filename": "ProductEntity.java",
            "file_type": "entity",
            "layer": "model",
            "relative_path": "src/main/java/com/example/springboot/model",
            "purpose": "JPA entity representing Product domain model",
            "solid_principles": ["SRP", "OCP"],
            "example_class_name": "Product"
        },
        {
            "filename": "ProductDTO.java",
            "file_type": "dto",
            "layer": "dto",
            "relative_path": "src/main/java/com/example/springboot/dto",
            "purpose": "Data transfer objects for API contracts",
            "solid_principles": ["SRP"],
            "example_class_name": "ProductRequest, ProductResponse"
        },
        {
            "filename": "ProductRepository.java",
            "file_type": "repository",
            "layer": "repository",
            "relative_path": "src/main/java/com/example/springboot/repository",
            "purpose": "Spring Data JPA repository for data persistence",
            "solid_principles": ["SRP", "DIP"],
            "example_class_name": "ProductRepository"
        },
        {
            "filename": "ProductService.java",
            "file_type": "service",
            "layer": "service",
            "relative_path": "src/main/java/com/example/springboot/service",
            "purpose": "Business logic and service interface",
            "solid_principles": ["SRP", "OCP", "DIP"],
            "example_class_name": "ProductService, ProductServiceImpl"
        },
        {
            "filename": "ProductController.java",
            "file_type": "controller",
            "layer": "controller",
            "relative_path": "src/main/java/com/example/springboot/controller",
            "purpose": "REST API endpoints",
            "solid_principles": ["SRP", "DIP"],
            "example_class_name": "ProductController"
        }
    ],
    "directory_structure": {
        "src/main/java/com/example/springboot/model": "Domain models and entities",
        "src/main/java/com/example/springboot/repository": "Data access layer",
        "src/main/java/com/example/springboot/service": "Business logic layer",
        "src/main/java/com/example/springboot/controller": "REST API endpoints",
        "src/main/java/com/example/springboot/dto": "Data transfer objects",
        "src/main/java/com/example/springboot/exception": "Exception classes",
    },
    "best_practices": [
        "Separate concerns: Entity models should not contain business logic",
        "Use DTOs to decouple API contracts from entity models",
        "Implement Repository pattern for data access abstraction"
    ],
    "framework_conventions": [
        "Use @Entity, @Table for JPA entities",
        "Use @Repository for Spring Data repositories",
        "Use @Service for business logic beans"
    ],
    "creation_order": [
        "ProductEntity.java",
        "ProductRepository.java",
        "ProductService.java",
        "ProductController.java"
    ]
}

# ==============================================================================
# TEST 1: Validator Initialization
# ==============================================================================

def test_validator_init():
    """Test 1: Initialize validator"""
    print("=" * 80)
    print("TEST 1: Validator Initialization")
    print("=" * 80)
    
    if not os.path.isdir(CODEBASE_PATH):
        print(f"❌ Codebase not found: {CODEBASE_PATH}\n")
        return None
    
    framework = detect_framework(CODEBASE_PATH)
    print(f"✅ Framework detected: {framework}")
    
    validator = EnhancedStructureValidator(CODEBASE_PATH, framework)
    print(f"✅ Validator created")
    print(f"   Max validation rounds: {validator.MAX_VALIDATION_ROUNDS}\n")
    
    return validator

# ==============================================================================
# TEST 2: Initial Validation
# ==============================================================================

def test_initial_validation(validator):
    """Test 2: Initial validation of plan"""
    print("=" * 80)
    print("TEST 2: Initial Validation of Implementation Plan")
    print("=" * 80)
    
    print(f"📋 Feature: {MOCK_FEATURE_SPEC['feature_name']}")
    print(f"📄 New files planned: {len(MOCK_FEATURE_SPEC['new_files'])}")
    print(f"📁 Directory structure: {len(MOCK_NEW_FILES_PLANNING['directory_structure'])} dirs\n")
    
    assessment = validator._validate_structure(
        MOCK_FEATURE_SPEC,
        MOCK_NEW_FILES_PLANNING
    )
    
    print(f"✅ Initial Validation Complete:")
    print(f"   Score: {assessment.score:.1f}/100")
    print(f"   Production Ready: {assessment.is_production_ready}")
    print(f"   Violations: {len(assessment.violations)}")
    print(f"   Summary: {assessment.summary}\n")
    
    # Print violations
    if assessment.violations:
        print(f"📋 Violations Found ({len(assessment.violations)}):")
        for i, v in enumerate(assessment.violations[:5], 1):
            severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(v.severity, "•")
            print(f"\n   [{i}] {severity_icon} {v.violation_type.upper()}")
            print(f"       Location: {v.location}")
            print(f"       Message: {v.message}")
            print(f"       Fix: {v.suggested_fix}")
        
        if len(assessment.violations) > 5:
            print(f"\n   ... and {len(assessment.violations) - 5} more violations")
    
    print()
    return assessment

# ==============================================================================
# TEST 3: Validation and Refinement Loop
# ==============================================================================

def test_refinement_loop(validator):
    """Test 3: Full validation and refinement loop"""
    print("=" * 80)
    print("TEST 3: Validation & Refinement Loop (Max 3 Rounds)")
    print("=" * 80)
    print()
    
    assessment, production_ready, refinements = validator.validate_and_refine(
        MOCK_FEATURE_SPEC,
        MOCK_NEW_FILES_PLANNING
    )
    
    print(f"\n📊 Final Results:")
    print(f"   Rounds Completed: {len(validator.validation_history)}")
    print(f"   Final Score: {assessment.score:.1f}/100")
    print(f"   Production Ready: {'✅ Yes' if production_ready else '❌ No'}")
    print(f"   Total Violations: {len(assessment.violations)}")
    
    # Show progress
    print(f"\n📈 Validation Progress:")
    for round_num, hist in enumerate(validator.validation_history, 1):
        status = "✅ Ready" if hist.is_production_ready else "⚠️  Needs work"
        print(f"   Round {round_num}: Score {hist.score:.1f}/100 - {len(hist.violations)} violations - {status}")
    
    # Show refinements
    if refinements:
        print(f"\n🔧 Refinements Applied ({len(refinements)}):")
        for ref in refinements:
            print(f"   Round {ref['round']}:")
            if ref["violations_to_address"]:
                print(f"     Violations addressed: {len(ref['violations_to_address'])}")
            if ref["auto_fixes"]:
                print(f"     Auto fixes applied: {len(ref['auto_fixes'])}")
                for af in ref['auto_fixes']:
                    print(f"       - {af['type']}: {af['location']}")
    
    print()
    return assessment, production_ready

# ==============================================================================
# TEST 4: Integration with State
# ==============================================================================

def test_integration_with_state():
    """Test 4: Integration with workflow state"""
    print("=" * 80)
    print("TEST 4: Integration with Workflow State")
    print("=" * 80)
    print()
    
    # Mock workflow state
    state = {
        "codebase_path": CODEBASE_PATH,
        "feature_spec": type('obj', (object,), {**MOCK_FEATURE_SPEC, "new_files_planning": type('obj', (object,), MOCK_NEW_FILES_PLANNING)()})(),
        "framework": detect_framework(CODEBASE_PATH),
        "errors": []
    }
    
    print(f"📍 Initial State:")
    print(f"   codebase_path: {state['codebase_path']}")
    print(f"   framework: {state['framework']}")
    print(f"   feature_spec: {state['feature_spec'].feature_name}")
    print()
    
    # Run validation
    result_state = validate_structure_with_feedback(state, max_loops=3)
    
    print(f"✅ State Updated:")
    print(f"   current_phase: {result_state.get('current_phase', 'N/A')}")
    print(f"   errors: {len(result_state.get('errors', []))}")
    
    if "structure_assessment" in result_state:
        assess = result_state["structure_assessment"]
        print(f"   structure_assessment:")
        print(f"     - score: {assess['score']:.1f}/100")
        print(f"     - is_production_ready: {assess['is_production_ready']}")
        print(f"     - violations: {len(assess['violations'])}")
    
    if "validation_history" in result_state:
        print(f"   validation_history: {len(result_state['validation_history'])} rounds")
    
    if "structure_feedback" in result_state:
        print(f"   structure_feedback: {result_state['structure_feedback']['action']}")
    
    print()
    return result_state

# ==============================================================================
# TEST 5: Score Progression
# ==============================================================================

def test_score_progression(validator):
    """Test 5: Show score progression through rounds"""
    print("=" * 80)
    print("TEST 5: Score Progression Analysis")
    print("=" * 80)
    print()
    
    if not validator.validation_history:
        print("❌ No validation history found\n")
        return
    
    print("📊 Score Progression:")
    print()
    print("Round | Score | Violations | Status")
    print("------|-------|------------|--------")
    
    for round_num, hist in enumerate(validator.validation_history, 1):
        status = "✅ Ready" if hist.is_production_ready else "⚠️  Needs" if hist.score >= 70 else "❌ Poor"
        violations_count = len(hist.violations) if isinstance(hist.violations, list) else hist.violations
        print(f"  {round_num}   | {hist.score:5.1f} | {violations_count:10} | {status}")
    
    # Calculate trend
    if len(validator.validation_history) > 1:
        first_score = validator.validation_history[0].score
        last_score = validator.validation_history[-1].score
        improvement = last_score - first_score
        trend = "📈 Improved" if improvement > 0 else "📉 Worsened" if improvement < 0 else "➡️  Stable"
        print()
        print(f"{trend}: {abs(improvement):.1f} points")
    
    print()

# ==============================================================================
# TEST 6: Directory Creation
# ==============================================================================

def test_directory_creation():
    """Test 6: Verify directories were created"""
    print("=" * 80)
    print("TEST 6: Verify Directory Creation")
    print("=" * 80)
    print()
    
    # Check for created directories
    expected_dirs = [
        "src/main/java/com/example/springboot/model",
        "src/main/java/com/example/springboot/repository",
        "src/main/java/com/example/springboot/service",
        "src/main/java/com/example/springboot/controller",
        "src/main/java/com/example/springboot/dto",
        "src/main/java/com/example/springboot/exception",
    ]
    
    print("📁 Checking for created directories:")
    created_count = 0
    for dir_path in expected_dirs:
        full_path = os.path.join(CODEBASE_PATH, dir_path)
        exists = os.path.isdir(full_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {dir_path}")
        if exists:
            created_count += 1
    
    print()
    print(f"✅ Created: {created_count}/{len(expected_dirs)} directories\n")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "TEST: Enhanced validate_structure with Feedback Loop".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        # Test 1: Initialize validator
        validator = test_validator_init()
        if not validator:
            print("⚠️  Skipping remaining tests\n")
            return
        
        # Test 2: Initial validation
        assessment = test_initial_validation(validator)
        
        # Test 3: Refinement loop
        final_assessment, production_ready = test_refinement_loop(validator)
        
        # Test 4: Integration
        result_state = test_integration_with_state()
        
        # Test 5: Score progression
        test_score_progression(validator)
        
        # Test 6: Directory creation
        test_directory_creation()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print()
        print(f"✅ All tests completed successfully")
        print()
        print(f"📊 Final Metrics:")
        print(f"   - Validation rounds: {len(validator.validation_history)}")
        print(f"   - Final score: {final_assessment.score:.1f}/100")
        print(f"   - Production ready: {'✅ Yes' if production_ready else '❌ No'}")
        print(f"   - Total violations: {len(final_assessment.violations)}")
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
