#!/usr/bin/env python3
"""
Test script for the new agent-based project specification parser.
Tests against crypto-monitoring-system.md to verify comprehensive parsing.
"""

import sys
import os

# Add the scripts directory to Python path
scripts_path = os.path.join(os.path.dirname(__file__), 'scripts', 'coding_agent')
sys.path.insert(0, scripts_path)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent_parser():
    """Test the agent-based parser with crypto-monitoring-system.md"""
    
    # Import here to ensure path is set
    try:
        from flow_parse_intent import _parse_project_spec_content
    except ImportError as e:
        logger.error(f"Could not import parser: {e}")
        return None
    
    # Read the crypto monitoring specification
    spec_path = "/Users/zeihanaulia/Programming/research/agent/dataset/spec/crypto-monitoring-system.md"
    
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("=== CRYPTO MONITORING SYSTEM SPEC ===")
        print(f"Specification length: {len(content)} characters")
        print(f"First 500 characters:\n{content[:500]}...")
        print("\n" + "="*50 + "\n")
        
        # Test the new agent-based parser
        print("Testing agent-based parser...")
        spec = _parse_project_spec_content(content)
        
        print("=== PARSING RESULTS ===")
        print(f"Project Name: {spec.project_name}")
        print(f"Purpose: {spec.purpose}")
        print(f"Language: {spec.language}")
        print(f"Framework: {spec.framework}")
        print(f"Build Tool: {spec.build_tool}")
        print(f"Packaging: {spec.packaging}")
        print(f"Modules: {spec.modules}")
        
        print("\nArchitecture Notes:")
        for key, value in spec.architecture_notes.items():
            print(f"  {key}: {value}")
            
        print("\nDependencies:")
        print(f"  Baseline: {spec.dependencies.get('baseline', [])}")
        print(f"  Optional: {spec.dependencies.get('optional', [])}")
        
        print("\nWorkflow Guidelines:")
        for guideline in spec.workflow_guidelines:
            print(f"  - {guideline}")
            
        print("\nQuality Checklist:")
        for item in spec.quality_checklist:
            print(f"  - {item}")
            
        print("\nSecurity Guidelines:")
        for guideline in spec.security_guidelines:
            print(f"  - {guideline}")
            
        print("\nTesting Guidelines:")
        for key, value in spec.testing_guidelines.items():
            print(f"  {key}: {value}")
        
        return spec
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_old_vs_new_parser():
    """Compare old manual parser vs new agent-based parser"""
    
    # Test with a simple spec that the old parser could handle
    simple_spec = """
# Test Project

## 🧠 project overview
name: crypto-monitoring-system  
purpose: A comprehensive cryptocurrency monitoring and analysis platform
language: Java
framework: Spring Boot
build tool: Maven
packaging: JAR

modules:
  - crypto-data-collector
  - price-analysis-engine
  - alert-manager
  - portfolio-tracker

## 🧭 architecture notes
layering: Hexagonal architecture with domain-driven design
dto placement: Separate request/response DTOs in web layer
service pattern: Domain services with clear boundaries
validation layer: Bean validation in web layer, business validation in domain
exception handling: Global exception handler with custom exceptions
"""
    
    print("=== SIMPLE SPEC COMPARISON ===")
    print("Testing simple spec with both parsers...\n")
    
    # Test new parser
    try:
        new_result = _parse_project_spec_content(simple_spec)
        print("NEW PARSER RESULTS:")
        print(f"  Project: {new_result.project_name}")
        print(f"  Purpose: {new_result.purpose}")
        print(f"  Language: {new_result.language}")
        print(f"  Framework: {new_result.framework}")
        print()
    except Exception as e:
        print(f"NEW PARSER FAILED: {e}")
    
    # Import original parsing functions for comparison
    try:
        from flow_parse_intent import _extract_markdown_sections, _extract_after_colon
        sections = _extract_markdown_sections(simple_spec)
        
        print("OLD PARSER SECTIONS:")
        for key, value in sections.items():
            print(f"  {key}: {value[:100]}...")
        print()
    except Exception as e:
        print(f"OLD PARSER COMPARISON FAILED: {e}")

if __name__ == "__main__":
    print("Testing Agent-Based Project Specification Parser\n")
    
    # Set up environment variable for OpenAI API (if not already set)
    if not os.environ.get('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY not set. Parser may fail.")
        print("Please set your OpenAI API key to test the agent-based parser.\n")
    
    # Test with comprehensive crypto specification
    result = test_agent_parser()
    
    if result:
        print("\n" + "="*50)
        print("SUCCESS: Agent parser successfully processed comprehensive specification!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("FAILED: Agent parser could not process specification")
        print("="*50)
    
    print("\n" + "-"*50)
    
    # Test simple spec comparison
    test_old_vs_new_parser()