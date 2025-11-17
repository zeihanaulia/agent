#!/usr/bin/env python3
"""
Demo: Enhanced Domain Reasoning Chain Structure
Shows the reasoning chain structure without requiring actual LLM calls
"""
import sys
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # optional: we'll check and suggest installation
import argparse

# Ensure the repository root is on sys.path so imports like `scripts.coding_agent...` work
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

# Load .env file automatically if present and python-dotenv is installed
dotenv_path = repo_root / ".env"
if dotenv_path.exists():
    if load_dotenv:
        # This returns True/False if actual variables were loaded
        loaded = load_dotenv(dotenv_path)
        if loaded:
            print(f"✅ Loaded environment variables from {dotenv_path}")
        else:
            print(f"⚠️  Found {dotenv_path}, but no variables were loaded (check formatting)")
    else:
        print("⚠️  `python-dotenv` not installed. Install it or source the .env file to load environment variables:")
        print("    pip install python-dotenv")
        print(f"    source {dotenv_path}  # or . {dotenv_path}")

# environment variables are now loaded (if python-dotenv is present), no further action needed

from coding_agent.domain_reasoning_chain import (  # noqa: E402 - sys.path intentionally modified above
    DomainArchitectureReasoning,
    ReasoningStep,
    SpecIntentAnalysis,
    EntityDecision,
    get_reasoning_summary,
    enhanced_entity_extraction_with_reasoning,
    # DomainReasoningChain,  # Not used in this demo
)

def create_demo_reasoning():
    """
    Create a demo reasoning analysis to show the structure and capabilities.
    This demonstrates what the enhanced reasoning chain would produce.
    """
    
    # Example reasoning steps showing chain-of-thought process
    reasoning_steps = [
        ReasoningStep(
            step_number=1,
            question="What does the specification explicitly instruct me to do?",
            analysis="The specification contains clear explicit instructions: 'No new domain entities needed' and 'Modify the existing Product entity'. This indicates the spec wants extension of existing entities, not creation of new ones.",
            conclusion="Specification explicitly prohibits new entity creation and requires Product entity extension.",
            confidence=0.95
        ),
        ReasoningStep(
            step_number=2,
            question="What entities already exist and what are their purposes?", 
            analysis="Existing entities: Product (core product with id, name, description, price), User (authentication/authorization). Product is the main business entity that handles product information.",
            conclusion="Product entity exists and is suitable for extension with stock management functionality.",
            confidence=0.90
        ),
        ReasoningStep(
            step_number=3,
            question="What domain concepts are involved in this feature?",
            analysis="The feature involves inventory/stock management concepts: currentStock, reorderPoint, lastRestocked. These are attributes that logically belong to Product entity as they describe product state.",
            conclusion="Stock management attributes are natural extensions of Product entity, not separate domain concepts.",
            confidence=0.85
        ),
        ReasoningStep(
            step_number=4, 
            question="Should I extend existing entities or create new ones?",
            analysis="Given explicit spec instructions against new entities, existing Product entity structure, and logical fit of stock attributes to Product, extension is the clear choice.",
            conclusion="Extend Product entity with stock management fields. Do NOT create separate Inventory entity.",
            confidence=0.98
        ),
        ReasoningStep(
            step_number=5,
            question="Do my decisions align with specification requirements?",
            analysis="Decision to extend Product aligns perfectly with 'No new domain entities needed' and 'Modify existing Product entity' instructions. Avoids creating separate Inventory domain.",
            conclusion="Decisions are fully compliant with specification intent and requirements.",
            confidence=1.0
        )
    ]
    
    # Spec intent analysis
    spec_intent = SpecIntentAnalysis(
        has_explicit_instructions=True,
        intent_phrases=[
            "No new domain entities needed",
            "Modify the existing Product entity",
            "This is an extension of existing Product functionality"
        ],
        explicit_instructions=[
            "Modify existing Product entity by adding: currentStock, reorderPoint, lastRestocked",
            "This is an extension of existing Product functionality, not a separate inventory system"
        ],
        domain_constraints=[
            "No creation of new domain entities",
            "Must use existing Product entity structure"
        ],
        extension_targets=["Product"],
        creation_prohibitions=["Inventory", "Stock", "InventoryItem"]
    )
    
    # Entity decisions
    entity_decisions = [
        EntityDecision(
            entity_name="Product",
            decision_type="extend",
            rationale="Specification explicitly states 'Modify the existing Product entity' and 'No new domain entities needed'. Stock management attributes (currentStock, reorderPoint, lastRestocked) are natural extensions of Product entity.",
            spec_compliance=True,
            architectural_soundness=0.95,
            existing_entity_reference="Product"
        )
    ]
    
    # Complete reasoning analysis
    reasoning = DomainArchitectureReasoning(
        feature_request_summary="Inventory Management Extension - Add stock management fields to existing Product entity",
        reasoning_chain=reasoning_steps,
        spec_intent=spec_intent,
        existing_entities_analysis={
            "Product": "Core business entity with id, name, description, price. Perfect candidate for stock management extension.",
            "User": "Authentication entity, not relevant to inventory feature."
        },
        entity_decisions=entity_decisions,
        architectural_approach="Entity Extension Pattern - Extend existing Product entity with stock management attributes following specification constraints",
        spec_compliance_score=1.0,
        reasoning_quality=0.92,
        final_recommendation="EXTEND Product entity with currentStock, reorderPoint, and lastRestocked fields. Do NOT create separate Inventory domain entities. This follows specification intent precisely while maintaining clean domain architecture."
    )
    
    return reasoning

def main():
    print("🧠 Domain Reasoning Chain Demo")
    print("=" * 50)
    print("This demonstrates the enhanced LLM reasoning structure")
    print("that would be used for domain architecture decisions.\n")
    
    # Create demo reasoning
    reasoning = create_demo_reasoning()
    
    # Show extracted entities based on decisions
    extracted_entities = []
    for decision in reasoning.entity_decisions:
        if decision.decision_type in ["extend", "create"]:
            extracted_entities.append(decision.entity_name)
    
    print(f"🎯 Extracted Entities: {extracted_entities}")
    print()
    
    # Show reasoning summary
    print(get_reasoning_summary(reasoning))
    
    print("\n" + "=" * 50)
    print("✅ This reasoning chain would ensure:")
    print("   • Specification compliance (follows 'No new entities' instruction)")  
    print("   • Transparent decision-making process")
    print("   • Architectural quality assessment")
    print("   • Step-by-step reasoning documentation")
    print("   • Domain-driven design principles")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo for Domain Reasoning Chain")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM-backed reasoning instead of static demo")
    args = parser.parse_args()

    if args.use_llm:
        # Attempt to call LLM-backed reasoning; fallback to static demo on error
        example_feature_request = """
        # Inventory Management Extension

        ## Overview
        No new domain entities needed. Modify the existing Product entity to include stock management fields.

        ## Expected Implementation
        Modify existing Product entity by adding:
        - currentStock (Integer)
        - reorderPoint (Integer)
        - lastRestocked (LocalDateTime)

        This is an extension of existing Product functionality, not a separate inventory system.
        """

        example_existing_entities = {
            "Product": "Core product entity with id, name, description, price fields",
            "User": "User entity for authentication and authorization"
        }

        # Quick environment check before attempting to call LLM
        if not os.environ.get("LITELLM_VIRTUAL_KEY"):
            print("⚠️  LITELLM_VIRTUAL_KEY environment variable not set. Skipping LLM demo and falling back to static demo.")
            main()
            sys.exit(0)

        try:
            # Use the helper that calls the LLM (DomainReasoningChain)
            entities, reasoning = enhanced_entity_extraction_with_reasoning(
                feature_request=example_feature_request,
                existing_entities=example_existing_entities,
            )

            print("🧪 LLM Domain Reasoning Chain (live)")
            print("=" * 50)
            print(f"🎯 Extracted Entities: {entities}\n")
            print(get_reasoning_summary(reasoning))

        except Exception as e:
            print(f"❌ LLM-backed demo failed: {e}")
            print("Falling back to static demo...\n")
            main()

    else:
        main()