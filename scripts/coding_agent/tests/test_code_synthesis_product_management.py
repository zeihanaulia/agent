import sys
import os
from typing import Dict, Any

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'coding_agent'))

try:
    from flow_synthesize_code import flow_synthesize_code
    from flow_parse_intent import FeatureSpec, TodoList, TodoItem
except ImportError as e:
    print(f"⚠️  Import error (will try alternative import): {e}")
    # Will handle in main()

# ============================================================================
# PREDEFINED STATE (Simulate Phase 1-3 outputs)
# ============================================================================

def create_predefined_state() -> Dict[str, Any]:
    """Create predefined AgentState for Phase 4 testing"""
    
    # Phase 1: Context Analysis
    context_analysis = """
Spring Boot Project Structure:
- src/main/java/com/example/springboot/
  - Application.java
  - HelloController.java
- pom.xml with spring-boot-starter-web, spring-boot-starter-data-jpa

Current Framework: Spring Boot (Spring MVC + JPA)
Database: H2 (in-memory)
API Pattern: RESTful with @RestController
    """
    
    # Phase 2: Feature Spec (parse_intent output)
    feature_spec = FeatureSpec(
        feature_name="Product Management CRUD",
        intent_summary="Add product management feature with CRUD operations",
        affected_files=["src/main/java/com/example/springboot/HelloController.java"],
        new_files=[
            "ProductEntity.java",
            "ProductDTO.java",
            "ProductRepository.java",
            "ProductService.java",
            "ProductController.java"
        ],
        modifications=[
            {"description": "Add product repository interface", "type": "pending"},
            {"description": "Add product service layer", "type": "pending"},
            {"description": "Add product REST controller", "type": "pending"}
        ]
    )
    
    # Add todo_list to feature_spec
    todos = [
        TodoItem(id=1, title="Analyze existing code patterns", phase="analysis", status="completed"),
        TodoItem(id=2, title="Identify Spring Boot conventions", phase="analysis", status="completed"),
        TodoItem(id=3, title="Design ProductEntity with JPA", phase="generation", status="pending"),
        TodoItem(id=4, title="Create ProductDTO for responses", phase="generation", status="pending"),
        TodoItem(id=5, title="Generate ProductRepository interface", phase="generation", status="pending"),
        TodoItem(id=6, title="Implement ProductService with business logic", phase="generation", status="pending"),
        TodoItem(id=7, title="Create ProductController with REST endpoints", phase="generation", status="pending"),
    ]
    
    feature_spec.todo_list = TodoList(
        feature_name="Product Management CRUD",
        feature_request="Add product management feature with CRUD operations",
        framework="SPRING_BOOT",
        total_tasks=7,
        completed_tasks=2,
        in_progress_tasks=0,
        pending_tasks=5,
        todos=todos
    )
    
    # Simulate new_files_planning
    class FilePlacementSuggestion:
        def __init__(self, filename, location, layer, solid_principles):
            self.filename = filename
            self.location = location
            self.layer = layer
            self.solid_principles = solid_principles
    
    class NewFilesPlanningSuggestion:
        def __init__(self):
            self.suggested_files = [
                FilePlacementSuggestion(
                    "ProductDTO.java",
                    "src/main/java/com/example/springboot/dto/ProductDTO.java",
                    "dto",
                    ["Single Responsibility", "Open/Closed"]
                ),
                FilePlacementSuggestion(
                    "ProductEntity.java",
                    "src/main/java/com/example/springboot/model/ProductEntity.java",
                    "model",
                    ["Single Responsibility"]
                ),
                FilePlacementSuggestion(
                    "ProductRepository.java",
                    "src/main/java/com/example/springboot/repository/ProductRepository.java",
                    "repository",
                    ["Dependency Inversion", "Interface Segregation"]
                ),
                FilePlacementSuggestion(
                    "ProductService.java",
                    "src/main/java/com/example/springboot/service/ProductService.java",
                    "service",
                    ["Single Responsibility", "Dependency Inversion"]
                ),
                FilePlacementSuggestion(
                    "ProductController.java",
                    "src/main/java/com/example/springboot/controller/ProductController.java",
                    "controller",
                    ["Single Responsibility"]
                ),
            ]
            self.creation_order = [f.filename for f in self.suggested_files]
            self.best_practices = [
                "Separate concerns into layers",
                "Use dependency injection",
                "Follow Spring Boot conventions"
            ]
            self.framework_conventions = [
                "Use @Entity for domain models",
                "Use @Repository for data access",
                "Use @Service for business logic",
                "Use @RestController for API endpoints"
            ]
    
    feature_spec.new_files_planning = NewFilesPlanningSuggestion()
    
    # Phase 3: Impact Analysis (analyze_impact output)
    impact_analysis = {
        "files_to_modify": [
            "src/main/java/com/example/springboot/HelloController.java"
        ],
        "architecture_insights": "Spring Boot project using MVC pattern with controller. Need to add layered architecture with service and repository patterns.",
        "patterns_to_follow": [
            "Repository Pattern - Data access abstraction",
            "Service Layer Pattern - Business logic encapsulation",
            "Dependency Injection - Spring @Autowired",
            "JPA Entity Pattern - Domain modeling"
        ],
        "testing_approach": "Unit tests for service layer (Mockito), Integration tests for controller (MockMvc). Test CRUD operations.",
        "constraints": [
            "Use only existing dependencies in pom.xml",
            "Follow Spring Boot naming conventions",
            "Use H2 in-memory database (no schema changes needed)",
            "Maintain RESTful API design",
            "Add proper exception handling"
        ],
        "todos": [
            "Create Product entity with id, name, price, quantity",
            "Create ProductDTO for API responses",
            "Create ProductRepository with CRUD methods",
            "Create ProductService with business logic",
            "Create ProductController with REST endpoints"
        ]
    }
    
    # Phase 2A: Structure Assessment
    structure_assessment = {
        "is_production_ready": False,
        "score": 30.0,
        "violations": [
            {"type": "missing_layer", "message": "Missing 'service/' layer directory"},
            {"type": "missing_layer", "message": "Missing 'repository/' layer directory"},
            {"type": "missing_layer", "message": "Missing 'dto/' layer directory"},
            {"type": "missing_layer", "message": "Missing 'model/' layer directory"},
        ],
        "refactoring_plan": {
            "create_layers": ["service", "repository", "dto", "model"],
            "effort_level": "medium"
        }
    }
    
    # Construct AgentState
    state = {
        "codebase_path": "dataset/codes/springboot-demo",
        "feature_request": "Add product management feature with CRUD operations",
        "context_analysis": context_analysis,
        "feature_spec": feature_spec,
        "impact_analysis": impact_analysis,
        "structure_assessment": structure_assessment,
        "framework": "SPRING_BOOT",
        "code_patches": None,
        "execution_results": None,
        "errors": [],
        "dry_run": False,
        "current_phase": "ready_for_synthesis",
        "human_approval_required": False,
    }
    
    return state


def mock_create_code_synthesis_agent(codebase_path, model, files_to_modify=None, feature_request=None):
    """Mock agent factory"""
    from scripts.coding_agent.deep_agent import create_deep_agent
    
    prompt = f"""
You are an expert Spring Boot developer.
Generate complete, production-ready code for: {feature_request}
Use the provided tools to read files and write new code.
Follow SOLID principles and Spring Boot best practices.
"""
    return create_deep_agent(system_prompt=prompt, model=model)


def mock_get_instruction(framework):
    """Mock instruction getter"""
    class MockInstruction:
        def get_system_prompt(self):
            return "Spring Boot best practices: layered architecture, dependency injection, RESTful API design"
        
        def get_layer_mapping(self):
            return {
                "controller": "REST API endpoints",
                "service": "Business logic",
                "repository": "Data access",
                "model": "Domain entities",
                "dto": "Data transfer objects"
            }
        
        def get_file_patterns(self):
            return {
                "Entity": "*Entity.java",
                "DTO": "*DTO.java",
                "Repository": "*Repository.java",
                "Service": "*Service.java",
                "Controller": "*Controller.java"
            }
    
    return MockInstruction()


# ============================================================================
# MAIN TEST
# ============================================================================

def main():
    print("=" * 80)
    print("🧪 PHASE 4 DIRECT TEST")
    print("=" * 80)
    print()
    
    # Create predefined state
    print("📊 Creating predefined AgentState from Phase 1-3...")
    state = create_predefined_state()
    print("  ✓ State created")
    print()
    
    # Log predefined state
    print("📋 Predefined State Summary:")
    print(f"  ✅ Feature: {state['feature_spec'].intent_summary}")
    print(f"  ✅ New files: {len(state['feature_spec'].new_files)}")
    print(f"  ✅ Affected files: {len(state['feature_spec'].affected_files)}")
    print(f"  ✅ Impact patterns: {len(state['impact_analysis']['patterns_to_follow'])}")
    print(f"  ✅ Constraints: {len(state['impact_analysis']['constraints'])}")
    print(f"  ✅ Todo tasks: {state['feature_spec'].todo_list.total_tasks}")
    print()
    
    # Setup model
    print("🔧 Setting up LLM model...")
    from langchain_openai import AzureChatOpenAI
    
    model = AzureChatOpenAI(
        model="gpt-4-mini",
        api_version="2025-01-01",
        temperature=1.0
    )
    print("  ✓ Model ready")
    print()
    
    # Run Phase 4
    print("=" * 80)
    print("🚀 Running Phase 4: flow_synthesize_code()")
    print("=" * 80)
    print()
    
    try:
        result_state = flow_synthesize_code(
            state,
            create_code_synthesis_agent=mock_create_code_synthesis_agent,
            get_instruction=mock_get_instruction,
            analysis_model=model
        )
        
        print()
        print("=" * 80)
        print("✅ PHASE 4 COMPLETE")
        print("=" * 80)
        print()
        
        # Report results
        patches = result_state.get("code_patches", [])
        print("📊 Results:")
        print(f"  Patches generated: {len(patches)}")
        if patches:
            for p in patches:
                print(f"    - {p['tool']}: {p.get('file', 'unknown')}")
        else:
            print("    (No patches generated)")
        
        print()
        print(f"  Current phase: {result_state.get('current_phase')}")
        if result_state.get("errors"):
            print(f"  Errors: {len(result_state['errors'])}")
            for err in result_state["errors"][:3]:
                print(f"    - {err}")
        else:
            print("  Errors: None")
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR IN PHASE 4")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
