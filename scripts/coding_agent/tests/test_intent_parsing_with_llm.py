#!/usr/bin/env python3
"""
TEST: flow_parse_intent with LLM Reasoning
============================================

Test flow_parse_intent dengan seed data dari codebase yang ada.
Harapan: 
1. LLM akan reasoning berdasarkan feature request
2. Detect framework (Spring Boot)
3. Generate structured todos dengan all phases
4. Infer new files yang diperlukan (ProductController, ProductService, etc)
5. Write todo tracking file
6. Output lengkap dengan clear reasoning

Test command:
    source .venv/bin/activate && python3 test_flow_parse_intent_v2.py
"""

import os
import sys
import json
from pathlib import Path

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from flow_parse_intent import (
    flow_parse_intent,
    generate_structured_todos,
    infer_new_files_needed,
    write_todo_file,
    FeatureSpec
)
from framework_instructions import detect_framework

# Load environment
load_dotenv()

# ==============================================================================
# TEST DATA
# ==============================================================================

CODEBASE_PATH = "dataset/codes/springboot-demo"
FEATURE_REQUEST = "Add product management feature with CRUD operations and search capability"

# ==============================================================================
# HELPER: Setup LLM Model with Reasoning
# ==============================================================================

def setup_llm_model(temperature: float = 0.7):
    """Setup LLM model using LiteLLM"""
    import litellm
    
    model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
    api_base = os.getenv("LITELLM_API")
    api_key = os.getenv("LITELLM_VIRTUAL_KEY")
    
    if not api_key:
        raise ValueError("LITELLM_VIRTUAL_KEY not found in environment")
    
    print(f"📦 Using model: {model_name}")
    print(f"🌡️  Temperature: {temperature}")
    print(f"📡 API Base: {api_base}\n")
    
    # Use ChatOpenAI with LiteLLM parameters
    from pydantic import SecretStr
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=SecretStr(api_key),
        base_url=api_base,
        default_headers={"Content-Type": "application/json"}
    )

# ==============================================================================
# TEST 1: Framework Detection
# ==============================================================================

def test_framework_detection():
    """Test 1: Framework detection from codebase"""
    print("=" * 80)
    print("TEST 1: Framework Detection")
    print("=" * 80)
    
    if not os.path.isdir(CODEBASE_PATH):
        print(f"❌ Codebase path not found: {CODEBASE_PATH}")
        return None
    
    try:
        framework = detect_framework(CODEBASE_PATH)
        print(f"✅ Framework detected: {framework}")
        print(f"   Framework str: {str(framework)}\n")
        return framework
    except Exception as e:
        print(f"❌ Framework detection failed: {e}\n")
        return None

# ==============================================================================
# TEST 2: Full flow_parse_intent with LLM Reasoning
# ==============================================================================

def test_flow_parse_intent():
    """Test 2: Full flow_parse_intent pipeline"""
    print("=" * 80)
    print("TEST 2: flow_parse_intent with LLM Reasoning")
    print("=" * 80)
    
    # Setup model
    model = setup_llm_model(temperature=0.7)
    framework = detect_framework(CODEBASE_PATH)
    
    # Create initial state
    state = {
        "codebase_path": CODEBASE_PATH,
        "feature_request": FEATURE_REQUEST,
        "context_analysis": """
            Spring Boot project with:
            - src/main/java structure
            - HelloController already exists
            - Basic application.properties configuration
            - Maven build system
            - Spring Web dependency
            - JPA/Hibernate for database
        """,
        "errors": []
    }
    
    print(f"📋 Feature Request: {FEATURE_REQUEST}\n")
    
    # Call flow_parse_intent
    result_state = flow_parse_intent(
        state,
        analysis_model=model,
        framework_detector=detect_framework
    )
    
    # Extract results
    feature_spec = result_state.get("feature_spec")
    errors = result_state.get("errors", [])
    
    if errors:
        print(f"❌ Errors encountered:")
        for err in errors:
            print(f"   - {err}\n")
        return None
    
    if not feature_spec:
        print("❌ No feature_spec generated\n")
        return None
    
    print("\n" + "=" * 80)
    print("TEST 2 RESULTS")
    print("=" * 80)
    
    # Print results
    print(f"✅ Feature Name: {feature_spec.feature_name}")
    print(f"✅ Intent Summary: {feature_spec.intent_summary[:100]}...")
    
    print(f"\n📁 Affected Files ({len(feature_spec.affected_files)}):")
    for af in feature_spec.affected_files[:5]:
        print(f"   - {af}")
    if len(feature_spec.affected_files) > 5:
        print(f"   ... and {len(feature_spec.affected_files) - 5} more")
    
    print(f"\n📄 New Files Planned ({len(feature_spec.new_files)}):")
    for nf in feature_spec.new_files:
        print(f"   - {nf}")
    
    print(f"\n📋 Modifications ({len(feature_spec.modifications)}):")
    for i, mod in enumerate(feature_spec.modifications[:3], 1):
        print(f"   {i}. {mod.get('description', 'N/A')[:60]}...")
    
    # Print new_files_planning details if available
    if feature_spec.new_files_planning:
        nfp = feature_spec.new_files_planning
        print(f"\n🏗️  Directory Structure ({len(nfp.directory_structure)}):")
        for dir_path, purpose in nfp.directory_structure.items():
            print(f"   - {dir_path}")
            print(f"     Purpose: {purpose}")
        
        print(f"\n🎯 Best Practices ({len(nfp.best_practices)}):")
        for bp in nfp.best_practices[:3]:
            print(f"   - {bp}")
        
        print(f"\n⚙️  Framework Conventions ({len(nfp.framework_conventions)}):")
        for fc in nfp.framework_conventions[:3]:
            print(f"   - {fc}")
        
        print(f"\n📦 Creation Order:")
        for co in nfp.creation_order[:5]:
            print(f"   - {co}")
    
    # Print todo_list details if available
    if feature_spec.todo_list:
        todo_list = feature_spec.todo_list
        print(f"\n✓ Todo List Generated:")
        print(f"   Total Tasks: {todo_list.total_tasks}")
        print(f"   Completed: {todo_list.completed_tasks}")
        print(f"   In Progress: {todo_list.in_progress_tasks}")
        print(f"   Pending: {todo_list.pending_tasks}")
        
        print(f"\n📋 Todo Items by Phase:")
        phases = {}
        for todo in todo_list.todos:
            if todo.phase not in phases:
                phases[todo.phase] = []
            phases[todo.phase].append(todo)
        
        for phase in ["analysis", "planning", "validation", "generation", "execution", "testing", "review"]:
            if phase in phases:
                print(f"   {phase.upper()} ({len(phases[phase])} items):")
                for todo in phases[phase][:2]:
                    print(f"      - [{todo.id:02d}] {todo.title} ({todo.status})")
                if len(phases[phase]) > 2:
                    print(f"      ... and {len(phases[phase]) - 2} more")
    
    print("\n✅ TEST 2 PASSED\n")
    return feature_spec

# ==============================================================================
# TEST 3: Infer New Files Needed
# ==============================================================================

def test_infer_new_files():
    """Test 3: Detailed new files inference"""
    print("=" * 80)
    print("TEST 3: Infer New Files Needed")
    print("=" * 80)
    
    model = setup_llm_model()
    framework = detect_framework(CODEBASE_PATH)
    
    print(f"📋 Feature Request: {FEATURE_REQUEST}")
    print(f"🔍 Framework: {framework}\n")
    
    # Call infer_new_files_needed
    suggestion = infer_new_files_needed(
        feature_request=FEATURE_REQUEST,
        context_analysis="Spring Boot with JPA/Hibernate",
        framework=framework,
        affected_files=[
            "src/main/java/com/example/springboot/HelloController.java"
        ]
    )
    
    print(f"📄 Suggested Files ({len(suggestion.suggested_files)}):")
    print()
    
    for i, sf in enumerate(suggestion.suggested_files, 1):
        print(f"   [{i}] {sf.filename}")
        print(f"       Type: {sf.file_type}")
        print(f"       Path: {sf.relative_path}")
        print(f"       Purpose: {sf.purpose}")
        print(f"       Layer: {sf.layer}")
        print(f"       SOLID Principles: {', '.join(sf.solid_principles)}")
        print(f"       Example Class: {sf.example_class_name}")
        print()
    
    print(f"🏗️  Directory Structure:")
    for dir_path, purpose in suggestion.directory_structure.items():
        print(f"   - {dir_path}")
        print(f"     {purpose}")
    
    print(f"\n📦 Creation Order:")
    for i, co in enumerate(suggestion.creation_order, 1):
        print(f"   {i}. {co}")
    
    print(f"\n🎯 Framework Conventions ({len(suggestion.framework_conventions)}):")
    for fc in suggestion.framework_conventions:
        print(f"   - {fc}")
    
    print("\n✅ TEST 3 PASSED\n")

# ==============================================================================
# TEST 4: Generate Structured Todos
# ==============================================================================

def test_generate_todos():
    """Test 4: Generate structured todos"""
    print("=" * 80)
    print("TEST 4: Generate Structured Todos")
    print("=" * 80)
    
    framework = detect_framework(CODEBASE_PATH)
    
    print(f"📋 Feature Request: {FEATURE_REQUEST}")
    print(f"🔍 Framework: {framework}\n")
    
    # Call generate_structured_todos
    todo_list = generate_structured_todos(
        feature_request=FEATURE_REQUEST,
        framework=framework,
        affected_files=["src/main/java/com/example/springboot/HelloController.java"],
        new_files=[
            "ProductEntity.java",
            "ProductDTO.java",
            "ProductRepository.java",
            "ProductService.java",
            "ProductController.java"
        ]
    )
    
    print(f"✅ Todo List Created:")
    print(f"   Total Tasks: {todo_list.total_tasks}")
    print(f"   Completed: {todo_list.completed_tasks}")
    print(f"   In Progress: {todo_list.in_progress_tasks}")
    print(f"   Pending: {todo_list.pending_tasks}")
    print(f"   Framework: {todo_list.framework}")
    
    # Group by phase
    phases = {}
    for todo in todo_list.todos:
        if todo.phase not in phases:
            phases[todo.phase] = []
        phases[todo.phase].append(todo)
    
    print(f"\n📋 Todos by Phase:")
    for phase in ["analysis", "planning", "validation", "generation", "execution", "testing", "review"]:
        if phase in phases:
            print(f"\n   {phase.upper()} ({len(phases[phase])} items):")
            for todo in phases[phase]:
                status_icon = {"completed": "✅", "in-progress": "🔄", "pending": "⏸️"}.get(todo.status, "•")
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(todo.priority, "•")
                print(f"      {status_icon} [{todo.id:02d}] {todo.title}")
                print(f"         Priority: {priority_icon} {todo.priority} | Effort: {todo.estimated_effort}")
                if todo.depends_on:
                    print(f"         Depends on: {todo.depends_on}")
                if todo.files_affected:
                    files = ", ".join(todo.files_affected[:2])
                    if len(todo.files_affected) > 2:
                        files += f" +{len(todo.files_affected) - 2}"
                    print(f"         Files: {files}")
                print()
    
    print("\n✅ TEST 4 PASSED\n")
    return todo_list

# ==============================================================================
# TEST 5: Write Todo File
# ==============================================================================

def test_write_todo_file():
    """Test 5: Write todo file to outputs"""
    print("=" * 80)
    print("TEST 5: Write Todo File")
    print("=" * 80)
    
    framework = detect_framework(CODEBASE_PATH)
    
    # Generate todo list
    todo_list = generate_structured_todos(
        feature_request=FEATURE_REQUEST,
        framework=framework,
        affected_files=["src/main/java/com/example/springboot/HelloController.java"],
        new_files=[
            "ProductEntity.java",
            "ProductDTO.java",
            "ProductRepository.java",
            "ProductService.java",
            "ProductController.java"
        ]
    )
    
    # Write todo file
    outputs_dir = "./outputs"
    os.makedirs(outputs_dir, exist_ok=True)
    
    try:
        filepath = write_todo_file(todo_list, outputs_dir)
        print(f"✅ Todo file written: {filepath}\n")
        
        # Print preview of file
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"📄 File Preview (first 30 lines):")
                print("-" * 80)
                for line in lines[:30]:
                    print(line)
                print("-" * 80)
                print(f"... ({len(lines)} total lines)\n")
    except Exception as e:
        print(f"❌ Failed to write todo file: {e}\n")
        return
    
    print("✅ TEST 5 PASSED\n")

# ==============================================================================
# TEST 6: End-to-End Integration Test
# ==============================================================================

def test_end_to_end():
    """Test 6: End-to-end integration"""
    print("=" * 80)
    print("TEST 6: End-to-End Integration")
    print("=" * 80)
    
    model = setup_llm_model(temperature=0.7)
    
    # State
    state = {
        "codebase_path": CODEBASE_PATH,
        "feature_request": FEATURE_REQUEST,
        "context_analysis": """
            Spring Boot project with:
            - src/main/java structure
            - HelloController already exists
            - Basic application.properties configuration
            - Maven build system
        """,
        "errors": []
    }
    
    print("🚀 Running full flow_parse_intent pipeline...\n")
    
    # Run flow
    result = flow_parse_intent(
        state,
        analysis_model=model,
        framework_detector=detect_framework
    )
    
    feature_spec = result.get("feature_spec")
    
    if not feature_spec:
        print("❌ flow_parse_intent failed\n")
        return
    
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    # Check all components are populated
    checks = {
        "Feature Name": (feature_spec.feature_name, len(feature_spec.feature_name) > 0),
        "Intent Summary": (feature_spec.intent_summary, len(feature_spec.intent_summary) > 0),
        "Affected Files": (feature_spec.affected_files, len(feature_spec.affected_files) > 0),
        "New Files": (feature_spec.new_files, len(feature_spec.new_files) > 0),
        "New Files Planning": (feature_spec.new_files_planning, feature_spec.new_files_planning is not None),
        "Todo List": (feature_spec.todo_list, feature_spec.todo_list is not None),
        "Modifications": (feature_spec.modifications, len(feature_spec.modifications) > 0),
    }
    
    all_passed = True
    for check_name, (value, is_valid) in checks.items():
        status = "✅" if is_valid else "❌"
        if isinstance(value, (list, str)) and len(str(value)) > 60:
            val_repr = f"{str(value)[:60]}..."
        else:
            val_repr = str(value)
        print(f"{status} {check_name}: {val_repr}")
        if not is_valid:
            all_passed = False
    
    if all_passed:
        print("\n✅ END-TO-END TEST PASSED\n")
    else:
        print("\n❌ END-TO-END TEST FAILED\n")
    
    return feature_spec

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "TEST: flow_parse_intent with LLM Reasoning".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        # Test 1: Framework detection
        framework = test_framework_detection()
        if not framework:
            print("⚠️  Skipping remaining tests (no framework detected)\n")
            return
        
        # Test 2: Full flow_parse_intent
        feature_spec = test_flow_parse_intent()
        
        # Test 3: Infer new files
        test_infer_new_files()
        
        # Test 4: Generate todos
        test_generate_todos()
        
        # Test 5: Write todo file
        test_write_todo_file()
        
        # Test 6: End-to-end
        test_end_to_end()
        
        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
