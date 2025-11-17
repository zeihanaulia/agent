"""
DOMAIN REASONING CHAIN - Enhanced LLM Reasoning for Domain Architecture Decisions
================================================================================

Implements chain-of-thought reasoning with structured output for better domain architecture decisions.
Uses Pydantic models and step-by-step reasoning to determine whether to:
1. Extend existing entities vs create new ones
2. Follow spec intent precisely vs make architectural exceptions
3. Apply proper domain-driven design patterns

Key Features:
- Multi-step reasoning chain
- Structured output validation
- Spec compliance analysis
- Domain architecture decision-making
- Enhanced LLM reasoning patterns

Dependencies:
- LangChain ChatOpenAI (NOT litellm.completion)
- Pydantic for structured output
- Chain-of-thought prompting patterns
"""

import os
import logging
from typing import List, Dict, Optional, Literal, Union, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

logger = logging.getLogger(__name__)


# ==============================================================================
# STRUCTURED OUTPUT MODELS
# ==============================================================================

class ReasoningStep(BaseModel):
    """Individual step in chain-of-thought reasoning"""
    step_number: int = Field(description="Step number in reasoning chain")
    question: str = Field(description="Question being addressed in this step")
    analysis: str = Field(description="Detailed analysis for this step")
    conclusion: str = Field(description="Conclusion reached in this step")
    confidence: float = Field(description="Confidence level 0.0-1.0", ge=0.0, le=1.0)


class SpecIntentAnalysis(BaseModel):
    """Analysis of specification intent and explicit instructions"""
    has_explicit_instructions: bool = Field(description="Whether spec contains explicit domain structure instructions")
    intent_phrases: List[str] = Field(description="Key phrases indicating spec intent")
    explicit_instructions: List[str] = Field(description="Clear instructions found in spec")
    domain_constraints: List[str] = Field(description="Domain constraints or limitations specified")
    extension_targets: List[str] = Field(description="Entities specified for extension")
    creation_prohibitions: List[str] = Field(description="Things spec says NOT to create")


class EntityDecision(BaseModel):
    """Decision about a specific entity"""
    entity_name: str = Field(description="Name of the entity")
    decision_type: Literal["extend", "create", "ignore"] = Field(description="Action to take")
    rationale: str = Field(description="Reasoning behind the decision")
    spec_compliance: bool = Field(description="Whether this follows spec instructions")
    architectural_soundness: float = Field(description="How architecturally sound 0.0-1.0", ge=0.0, le=1.0)
    existing_entity_reference: Optional[str] = Field(None, description="Existing entity to extend if applicable")


class DomainArchitectureReasoning(BaseModel):
    """Complete reasoning chain for domain architecture decisions"""
    feature_request_summary: str = Field(description="Summary of the feature request")
    
    # Chain-of-thought reasoning steps
    reasoning_chain: List[ReasoningStep] = Field(description="Step-by-step reasoning process")
    
    # Structured analysis components
    spec_intent: SpecIntentAnalysis = Field(description="Analysis of specification intent")
    existing_entities_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Analysis of existing entities and their purposes (various formats accepted)")
    
    # Final decisions
    entity_decisions: List[EntityDecision] = Field(description="Decisions for each entity")
    
    # Summary
    architectural_approach: str = Field(description="Overall architectural approach chosen")
    spec_compliance_score: float = Field(description="How well decisions follow spec 0.0-1.0", ge=0.0, le=1.0)
    reasoning_quality: float = Field(description="Quality of reasoning process 0.0-1.0", ge=0.0, le=1.0)
    final_recommendation: str = Field(description="Final recommendation summary")


# ==============================================================================
# CHAIN-OF-THOUGHT REASONING IMPLEMENTATION
# ==============================================================================

class DomainReasoningChain:
    """
    Enhanced LLM reasoning chain for domain architecture decisions.
    
    Implements multi-step reasoning with structured output to improve
    domain structure decisions and spec compliance.
    """
    
    def __init__(self, model_config: Optional[Dict[str, str]] = None):
        """
        Initialize the reasoning chain with LLM configuration.
        
        Args:
            model_config: Optional model configuration override
        """
        # Use environment or provided configuration
        self.model_config = model_config or {
            "model": os.getenv("LITELLM_MODEL", "gpt-4o-mini"),
            "api_key": os.getenv("LITELLM_VIRTUAL_KEY"),
            "base_url": os.getenv("LITELLM_API"),
        }
        
        if not self.model_config["api_key"]:
            raise RuntimeError("LITELLM_VIRTUAL_KEY environment variable not set")
        
        # Initialize ChatOpenAI with structured output support
        model_name = self.model_config.get("model") or "gpt-4o-mini"
        self.llm = ChatOpenAI(
            api_key=SecretStr(self.model_config["api_key"]),
            model=model_name,
            base_url=self.model_config["base_url"],
            temperature=0.1,  # Lower for more consistent reasoning
        )
    
    def analyze_domain_structure(
        self,
        feature_request: str,
        existing_entities: Dict[str, str],
        spec_file_content: Optional[str] = None
    ) -> DomainArchitectureReasoning:
        """
        Perform comprehensive domain architecture reasoning.
        
        Args:
            feature_request: The feature specification to analyze
            existing_entities: Dict of entity_name -> description of existing entities
            spec_file_content: Optional full specification content for context
            
        Returns:
            Complete structured reasoning analysis
        """
        # Create structured output model - prefer function_calling method for better compatibility
        try:
            structured_llm = self.llm.with_structured_output(
                DomainArchitectureReasoning,
                method="function_calling",
            )
        except TypeError:
            # Some older versions don't accept method arg; fallback to default
            structured_llm = self.llm.with_structured_output(DomainArchitectureReasoning)
        
        # Construct comprehensive prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(feature_request, existing_entities, spec_file_content)
        
        # Execute reasoning chain
        try:
            result = structured_llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            # Validate result
            if not isinstance(result, DomainArchitectureReasoning):
                raise ValueError(f"Expected DomainArchitectureReasoning, got {type(result)}")
            
            logger.info(f"Domain reasoning completed with {len(result.reasoning_chain)} steps")
            return result
            
        except Exception as e:
            logger.error(f"Domain reasoning failed: {e}")
            raise RuntimeError(f"Failed to complete domain architecture reasoning: {e}") from e
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for chain-of-thought reasoning"""
        return """You are an expert software architect specializing in domain-driven design and specification analysis.

Your task is to perform CHAIN-OF-THOUGHT REASONING for domain architecture decisions using a structured, step-by-step approach.

CORE PRINCIPLES:
1. SPECIFICATION INTENT IS PARAMOUNT - Always honor explicit instructions in specifications
2. DOMAIN-DRIVEN DESIGN - Apply proper DDD patterns and entity relationships
3. ARCHITECTURAL SOUNDNESS - Balance spec compliance with good architecture
4. TRANSPARENT REASONING - Show your thought process clearly at each step

CHAIN-OF-THOUGHT PROCESS:
You MUST follow this reasoning chain with clear steps:

Step 1: SPECIFICATION INTENT ANALYSIS
- Question: "What does the specification explicitly instruct me to do?"
- Analysis: Extract key phrases like "No new domain entities needed", "extend existing X", "modify existing Y"
- Conclusion: Determine if spec gives explicit domain structure guidance

Step 2: EXISTING ENTITIES ANALYSIS
- Question: "What entities already exist and what are their purposes?"
- Analysis: Understand current domain model and entity responsibilities
- Conclusion: Identify extension points and gaps in current model

Step 3: DOMAIN MODELING ANALYSIS
- Question: "What domain concepts are involved in this feature?"
- Analysis: Identify business entities, value objects, and domain services needed
- Conclusion: Map feature requirements to domain model concepts

Step 4: ARCHITECTURAL DECISION MAKING
- Question: "Should I extend existing entities or create new ones?"
- Analysis: Evaluate each option against spec intent, DDD principles, and architectural quality
- Conclusion: Make specific decisions for each entity with clear rationale

Step 5: SPEC COMPLIANCE VALIDATION
- Question: "Do my decisions align with specification requirements?"
- Analysis: Verify each decision against explicit spec instructions
- Conclusion: Confirm spec compliance or document justified deviations

DECISION CRITERIA:
- If spec says "No new entities" -> ONLY extend existing entities
- If spec says "Modify existing X" -> ONLY modify X, don't create new entities
- If spec says "Extension of X functionality" -> Extend X, not create separate entities
- If spec is silent -> Apply best DDD practices for new vs existing entities

OUTPUT FORMAT: 
Provide structured JSON following the DomainArchitectureReasoning schema with:
- Complete reasoning_chain with numbered steps
- Detailed spec_intent analysis
- Individual entity_decisions with rationale
- Overall architectural_approach and recommendation"""
    
    def _build_user_prompt(
        self,
        feature_request: str,
        existing_entities: Dict[str, str],
        spec_file_content: Optional[str] = None
    ) -> str:
        """Build the user prompt with context"""
        
        # Format existing entities
        entities_context = ""
        if existing_entities:
            entities_context = "\nEXISTING ENTITIES:\n"
            for entity, description in existing_entities.items():
                entities_context += f"- {entity}: {description}\n"
        
        # Add spec file context if available
        spec_context = ""
        if spec_file_content:
            spec_context = f"\n\nFULL SPECIFICATION CONTENT:\n{spec_file_content}"
        
        return f"""Please analyze this feature request and make domain architecture decisions using chain-of-thought reasoning.

FEATURE REQUEST TO ANALYZE:
---
{feature_request}
---
{entities_context}{spec_context}

INSTRUCTIONS:
1. Follow the 5-step chain-of-thought process outlined in the system prompt
2. Pay special attention to ANY explicit instructions in the specification
3. For each step, provide detailed analysis and clear conclusions
4. Make specific decisions about each entity (extend vs create vs ignore)
5. Ensure all decisions align with specification intent
6. Return structured JSON following the DomainArchitectureReasoning schema

CRITICAL: If the specification contains phrases like:
- "No new domain entities needed"
- "Modify the existing [Entity] entity"  
- "Extension of existing [Entity] functionality"
- "Expected Implementation: Modify existing..."

Then you MUST follow those instructions precisely. The specification's explicit guidance takes precedence over general architectural preferences.

Begin your chain-of-thought reasoning now:"""
    
    def extract_entities_with_reasoning(
        self,
        feature_request: str,
        existing_entities: Dict[str, str],
        spec_file_content: Optional[str] = None
    ) -> tuple[List[str], DomainArchitectureReasoning]:
        """
        Extract entities using enhanced reasoning, returning both entities and reasoning chain.
        
        Args:
            feature_request: Feature specification to analyze
            existing_entities: Known existing entities
            spec_file_content: Optional full spec content
            
        Returns:
            Tuple of (extracted_entities, reasoning_analysis)
        """
        # Perform full reasoning analysis
        reasoning = self.analyze_domain_structure(feature_request, existing_entities, spec_file_content)
        
        # Extract entities based on decisions
        extracted_entities = []
        for decision in reasoning.entity_decisions:
            if decision.decision_type in ["extend", "create"]:
                extracted_entities.append(decision.entity_name)
        
        logger.info(f"Extracted {len(extracted_entities)} entities using reasoning chain")
        return extracted_entities, reasoning


# ==============================================================================
# INTEGRATION FUNCTIONS
# ==============================================================================

def enhanced_entity_extraction_with_reasoning(
    feature_request: str,
    existing_entities: Optional[Dict[str, str]] = None,
    spec_file_content: Optional[str] = None,
    excluded_terms: Optional[set] = None
) -> tuple[List[str], DomainArchitectureReasoning]:
    """
    Enhanced entity extraction using chain-of-thought reasoning.
    
    This is the RECOMMENDED approach for entity extraction as it provides:
    - Structured reasoning chain for transparency
    - Better spec compliance through intent analysis  
    - Architectural decision documentation
    - Higher quality domain modeling
    
    Args:
        feature_request: Feature specification to analyze
        existing_entities: Optional dict of entity_name -> description
        spec_file_content: Optional full specification content
        excluded_terms: Optional set of terms to exclude
        
    Returns:
        Tuple of (extracted_entities, reasoning_analysis)
        
    Raises:
        RuntimeError: If LLM configuration is invalid
        ValueError: If reasoning chain fails
    """
    if existing_entities is None:
        existing_entities = {}
    
    if excluded_terms is None:
        excluded_terms = set()
    
    try:
        # Initialize reasoning chain
        reasoning_chain = DomainReasoningChain()
        
        # Perform extraction with reasoning
        entities, reasoning = reasoning_chain.extract_entities_with_reasoning(
            feature_request=feature_request,
            existing_entities=existing_entities,
            spec_file_content=spec_file_content
        )
        
        # Filter excluded terms
        entities = [e for e in entities if e.lower() not in excluded_terms]
        
        return entities, reasoning
        
    except Exception as e:
        logger.error(f"Enhanced entity extraction failed: {e}")
        raise RuntimeError(f"Enhanced entity extraction with reasoning failed: {e}") from e


def get_reasoning_summary(reasoning: DomainArchitectureReasoning) -> str:
    """
    Generate a human-readable summary of the reasoning chain.
    
    Args:
        reasoning: The reasoning analysis to summarize
        
    Returns:
        Formatted summary string
    """
    summary = "🧠 Domain Architecture Reasoning Summary\n"
    summary += f"{'='*50}\n\n"
    
    # Feature summary
    summary += f"📋 Feature: {reasoning.feature_request_summary}\n\n"
    
    # Spec compliance
    summary += f"📜 Spec Compliance Score: {reasoning.spec_compliance_score:.1f}/1.0\n"
    summary += f"🏗️  Architectural Approach: {reasoning.architectural_approach}\n\n"
    
    # Intent analysis
    if reasoning.spec_intent.has_explicit_instructions:
        summary += "⚠️  Explicit Spec Instructions Found:\n"
        for instruction in reasoning.spec_intent.explicit_instructions:
            summary += f"   • {instruction}\n"
        summary += "\n"

    # Existing entities analysis (flexible formats)
    if reasoning.existing_entities_analysis:
        summary += "🏷️ Existing Entities Analysis:\n"
        e = reasoning.existing_entities_analysis
        if isinstance(e, dict):
            # Handle formats like {"Product": "desc"} or {"entities": [{}, {}]}
            if "entities" in e and isinstance(e["entities"], list):
                for ent in e["entities"]:
                    name = ent.get("name") or ent.get("entity") or ent.get("id") or "UNKNOWN"
                    purpose = ent.get("purpose") or ent.get("description") or ent.get("desc") or str(ent)
                    summary += f"   • {name}: {purpose}\n"
            else:
                for k, v in e.items():
                    summary += f"   • {k}: {v}\n"
        else:
            # If it's some other type, just stringify it
            summary += f"   • {e}\n"
        summary += "\n"
    
    # Entity decisions
    summary += "🎯 Entity Decisions:\n"
    for decision in reasoning.entity_decisions:
        action_emoji = {"extend": "🔧", "create": "✨", "ignore": "❌"}
        emoji = action_emoji.get(decision.decision_type, "❓")
        summary += f"   {emoji} {decision.entity_name}: {decision.decision_type.upper()}\n"
        summary += f"      Rationale: {decision.rationale}\n"
        if decision.existing_entity_reference:
            summary += f"      Extending: {decision.existing_entity_reference}\n"
        summary += f"      Spec Compliant: {'✅' if decision.spec_compliance else '❌'}\n\n"
    
    # Final recommendation
    summary += f"💡 Final Recommendation:\n{reasoning.final_recommendation}\n\n"
    
    # Reasoning steps (summary)
    summary += f"🔍 Reasoning Chain ({len(reasoning.reasoning_chain)} steps):\n"
    for step in reasoning.reasoning_chain:
        summary += f"   {step.step_number}. {step.question}\n"
        summary += f"      → {step.conclusion}\n"
    
    return summary


# ==============================================================================
# EXAMPLE USAGE AND TESTING
# ==============================================================================

if __name__ == "__main__":
    """
    Example usage of the domain reasoning chain.
    
    Run this script to test the reasoning capabilities:
    python domain_reasoning_chain.py
    """
    
    # Example configuration
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
    
    try:
        print("🧪 Testing Domain Reasoning Chain...")
        print("=" * 50)
        
        # Run enhanced extraction
        entities, reasoning = enhanced_entity_extraction_with_reasoning(
            feature_request=example_feature_request,
            existing_entities=example_existing_entities
        )
        
        print(f"\n🎯 Extracted Entities: {entities}")
        print("\n" + get_reasoning_summary(reasoning))
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\nEnsure environment variables are set:")
        print("- LITELLM_MODEL")
        print("- LITELLM_VIRTUAL_KEY") 
        print("- LITELLM_API")