# Agnostic Agent Implementation Plan - DeepAgents Integration

## 🎯 Implementation Strategy with DeepAgents/LangGraph

Based on research of successful agnostic coding agents and analysis of current specifications, here's the detailed implementation plan using DeepAgents middleware and LangGraph orchestration.

## 🔍 Current State Assessment

### Existing Specifications Analysis
```
/dataset/spec/:
├── crypto-monitoring-system.md (Python/FastAPI + AI/ML)
├── inventory-management-system.md (Java/Spring Boot + JPA)  
├── payroll-management-system.md (Java/Spring Boot + Complex Business Logic)
├── simple-case.md (Java/Spring Boot + Basic CRUD)
├── smart-delivery-routing-system.md (Multi-language potential)
└── ticketing-agent.md (Event-driven architecture)
```

### Framework Diversity Challenge
- **Languages**: Java, Python, potentially JavaScript/TypeScript, Go, etc.
- **Frameworks**: Spring Boot, FastAPI, potentially Express.js, Django, etc.
- **Architecture Patterns**: Layered, Hexagonal, Microservices, Event-driven
- **Complexity Levels**: Simple CRUD → Complex AI/ML systems

## 🚀 Phase 1: Enhanced Framework Detection (Week 1)

### 1.1 Universal Stack Detector
**File**: `analytics/universal_stack_detector.py`

```python
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import os
import json
import yaml
from pathlib import Path

@dataclass
class StackInfo:
    language: str
    framework: str
    version: Optional[str]
    architecture_pattern: str
    build_tool: str
    dependencies: List[str]
    test_framework: str
    database_type: str
    confidence_score: float

class UniversalStackDetector:
    def __init__(self):
        self.detectors = {
            'java': JavaStackDetector(),
            'python': PythonStackDetector(),
            'javascript': NodeJSStackDetector(),
            'typescript': TypeScriptStackDetector(),
            'go': GoStackDetector(),
            'rust': RustStackDetector()
        }
        
    def detect_stack(self, codebase_path: str) -> StackInfo:
        """
        Universal stack detection with confidence scoring
        """
        language = self._detect_primary_language(codebase_path)
        detector = self.detectors.get(language)
        
        if detector:
            return detector.detect_detailed_stack(codebase_path)
        
        # Fallback to generic detection
        return self._generic_detection(codebase_path, language)
```

### 1.2 Architecture Pattern Detection
**File**: `analytics/architecture_detector.py`

```python
class ArchitectureDetector:
    def __init__(self):
        self.patterns = {
            'layered': LayeredArchitectureDetector(),
            'hexagonal': HexagonalArchitectureDetector(),
            'microservices': MicroservicesDetector(),
            'event_driven': EventDrivenDetector(),
            'mvvm': MVVMDetector(),
            'mvc': MVCDetector()
        }
    
    def detect_architecture(self, codebase_analysis: Dict) -> str:
        """
        Detect architectural pattern from codebase structure
        """
        scores = {}
        
        for pattern_name, detector in self.patterns.items():
            scores[pattern_name] = detector.calculate_score(codebase_analysis)
            
        return max(scores, key=scores.get)
```

### 1.3 Integration with Existing Flow
**Update**: `flow_analyze_context.py`

```python
# Replace hardcoded detection with universal detector
from analytics.universal_stack_detector import UniversalStackDetector

class AiderStyleRepoAnalyzer:
    def __init__(self, codebase_path: str, max_tokens: int = 4096):
        self.codebase_path = codebase_path
        self.max_tokens = max_tokens
        self.stack_detector = UniversalStackDetector()  # NEW
        
    def analyze_codebase(self) -> Dict[str, Any]:
        # ... existing code ...
        
        # NEW: Enhanced stack detection
        stack_info = self.stack_detector.detect_stack(self.codebase_path)
        analysis_result['stack_info'] = stack_info
        
        return analysis_result
```

## 🚀 Phase 2: Dynamic Instruction System (Week 2)

### 2.1 Instruction Template Engine
**File**: `instructions/template_engine.py`

```python
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any

class InstructionTemplateEngine:
    def __init__(self, templates_dir: str = "instructions/templates"):
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        
    def generate_instructions(self, 
                            stack_info: StackInfo, 
                            task_type: str, 
                            context: Dict[str, Any]) -> str:
        """
        Generate framework-specific instructions from templates
        """
        template_name = f"{stack_info.framework.lower()}_{task_type}.j2"
        
        try:
            template = self.env.get_template(template_name)
            return template.render(
                stack_info=stack_info,
                context=context,
                **self._get_framework_helpers(stack_info.framework)
            )
        except TemplateNotFound:
            # Fallback to generic template
            return self._generate_generic_instructions(stack_info, task_type, context)
```

### 2.2 Framework-Specific Templates
**Directory**: `instructions/templates/`

```
templates/
├── spring_boot_entity_creation.j2
├── spring_boot_service_implementation.j2  
├── spring_boot_controller_implementation.j2
├── fastapi_model_creation.j2
├── fastapi_router_implementation.j2
├── fastapi_service_implementation.j2
├── express_js_route_creation.j2
└── generic_api_implementation.j2
```

**Example Template**: `spring_boot_entity_creation.j2`
```jinja2
# Spring Boot Entity Implementation Guidelines

## Architecture Context
- Framework: {{ stack_info.framework }} {{ stack_info.version }}
- Architecture: {{ stack_info.architecture_pattern }}
- Build Tool: {{ stack_info.build_tool }}

## Entity Creation Rules
1. Place entities in `{{ get_entity_package(context.project_structure) }}`
2. Use JPA annotations: @Entity, @Table, @Id, @GeneratedValue
3. Follow {{ stack_info.architecture_pattern }} patterns
4. Include validation annotations: @NotNull, @Size, @Email
5. Use Lombok: @Data, @NoArgsConstructor, @AllArgsConstructor

## Code Structure Template
```java
@Entity
@Table(name = "{{ context.entity_name.lower() }}s")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class {{ context.entity_name }} {
    {% for field in context.fields %}
    {{ generate_field(field) }}
    {% endfor %}
}
```

## Validation Rules
{{ generate_validation_rules(context.fields) }}
```

### 2.3 Integration with Flow
**Update**: `flow_synthesize_code.py`

```python
from instructions.template_engine import InstructionTemplateEngine

def flow_synthesize_code(state: AgentState, 
                        create_code_synthesis_agent, 
                        get_instruction,  # DEPRECATED  
                        analysis_model) -> AgentState:
    
    # NEW: Use template engine instead of hardcoded instructions
    template_engine = InstructionTemplateEngine()
    
    stack_info = state.get("stack_info")  # From enhanced analysis
    context = {
        "feature_spec": state["feature_spec"],
        "project_structure": state["full_analysis"]["structure"],
        "entity_name": extract_entity_name(state["feature_spec"]),
        "fields": extract_fields(state["feature_spec"])
    }
    
    # Generate dynamic instructions
    instructions = template_engine.generate_instructions(
        stack_info=stack_info,
        task_type="code_synthesis", 
        context=context
    )
    
    # ... rest of implementation
```

## 🚀 Phase 3: Enhanced Specification Processing with Research (Week 3)

### 3.1 Research-Enhanced Spec Parser
**File**: `spec_parsing/research_enhanced_parser.py`

```python
from tavily import TavilyClient
from typing import Dict, Any, List

class ResearchEnhancedSpecParser:
    def __init__(self, tavily_api_key: str):
        self.tavily_client = TavilyClient(api_key=tavily_api_key)
        self.base_parser = AgentBasedSpecParser()  # Existing parser
        
    def parse_with_research(self, spec_content: str, context: Dict) -> EnhancedSpecification:
        """
        Parse specification with automatic research enhancement
        """
        # 1. Basic parsing using existing agent-based parser
        base_spec = self.base_parser.parse_specification(spec_content)
        
        # 2. Identify knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps(base_spec, context)
        
        # 3. Research missing information
        research_results = self._conduct_research(knowledge_gaps)
        
        # 4. Enhance specification with research
        enhanced_spec = self._enhance_specification(base_spec, research_results)
        
        return enhanced_spec
        
    def _conduct_research(self, knowledge_gaps: List[str]) -> Dict[str, Any]:
        """
        Use Tavily to research missing context
        """
        research_results = {}
        
        for gap in knowledge_gaps:
            query = f"{gap} best practices implementation patterns"
            try:
                results = self.tavily_client.search(
                    query=query, 
                    search_depth="advanced",
                    max_results=3
                )
                research_results[gap] = self._extract_relevant_info(results)
            except Exception as e:
                print(f"Research failed for {gap}: {e}")
                
        return research_results
```

### 3.2 Knowledge Gap Detection
**File**: `spec_parsing/knowledge_gap_detector.py`

```python
class KnowledgeGapDetector:
    def __init__(self):
        self.gap_patterns = {
            'security': ['authentication', 'authorization', 'jwt', 'oauth'],
            'performance': ['caching', 'optimization', 'scaling', 'load balancing'],
            'database': ['migration', 'indexing', 'transaction', 'connection pool'],
            'testing': ['unit test', 'integration test', 'mocking', 'test coverage'],
            'deployment': ['docker', 'kubernetes', 'ci/cd', 'pipeline'],
            'monitoring': ['logging', 'metrics', 'tracing', 'alerting']
        }
        
    def detect_gaps(self, specification: Dict, stack_info: StackInfo) -> List[str]:
        """
        Detect knowledge gaps in specification
        """
        gaps = []
        
        # Check if critical areas are mentioned
        for area, keywords in self.gap_patterns.items():
            if not self._area_covered(specification, keywords):
                gaps.append(f"{stack_info.framework} {area}")
                
        return gaps
```

### 3.3 Integration with Flow Parse Intent
**Update**: `flow_parse_intent.py`

```python
from spec_parsing.research_enhanced_parser import ResearchEnhancedSpecParser

def flow_parse_intent(flow_state: Dict[str, Any], 
                     analysis_model,
                     framework_detector) -> Dict[str, Any]:
    
    # ... existing code ...
    
    # NEW: Enhanced parsing with research
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if tavily_api_key:
        enhanced_parser = ResearchEnhancedSpecParser(tavily_api_key)
        enhanced_spec = enhanced_parser.parse_with_research(
            spec_content=feature_request,
            context={
                "codebase_analysis": flow_state.get("full_analysis"),
                "stack_info": detected_stack_info
            }
        )
        
        # Merge enhanced information
        feature_spec.research_insights = enhanced_spec.research_insights
        feature_spec.best_practices = enhanced_spec.best_practices
        feature_spec.security_recommendations = enhanced_spec.security_recommendations
    
    # ... rest of implementation
```

## 🚀 Phase 4: Universal File Placement Engine (Week 4)

### 4.1 Dynamic Placement Engine
**File**: `placement/universal_placement_engine.py`

```python
class UniversalPlacementEngine:
    def __init__(self):
        self.placement_rules = {
            'spring_boot': SpringBootPlacementRules(),
            'fastapi': FastAPIPlacementRules(),
            'express_js': ExpressJSPlacementRules(),
            'django': DjangoPlacementRules()
        }
        
    def determine_placement(self, 
                          file_type: str, 
                          stack_info: StackInfo, 
                          project_structure: Dict,
                          context: Dict) -> PlacementDecision:
        """
        Determine file placement based on framework conventions
        """
        framework_key = f"{stack_info.framework.lower()}"
        rules = self.placement_rules.get(framework_key)
        
        if rules:
            return rules.get_placement(file_type, project_structure, context)
        
        # Fallback to convention-based placement
        return self._convention_based_placement(file_type, stack_info, project_structure)
```

### 4.2 Framework-Specific Placement Rules
**File**: `placement/spring_boot_rules.py`

```python
class SpringBootPlacementRules:
    def __init__(self):
        self.base_package_patterns = [
            "com.{company}.{project}",
            "com.example.{project}",  
            "org.{company}.{project}"
        ]
        
    def get_placement(self, file_type: str, structure: Dict, context: Dict) -> PlacementDecision:
        base_package = self._detect_base_package(structure)
        
        placements = {
            'entity': f"{base_package}.entity",
            'repository': f"{base_package}.repository", 
            'service': f"{base_package}.service",
            'controller': f"{base_package}.controller",
            'dto': f"{base_package}.dto",
            'config': f"{base_package}.config",
            'exception': f"{base_package}.exception"
        }
        
        package_path = placements.get(file_type, base_package)
        file_path = self._package_to_path(package_path)
        
        return PlacementDecision(
            file_path=file_path,
            package_declaration=package_path,
            imports=self._get_standard_imports(file_type),
            confidence=0.95
        )
```

## 🚀 Phase 5: LangGraph Orchestration Enhancement (Week 5)

### 5.1 Enhanced Workflow with Research
**Update**: `feature_by_request_agent_v3.py`

```python
def create_feature_request_workflow():
    """Enhanced workflow with research capabilities"""
    workflow = StateGraph(AgentState)

    # Add new research node
    workflow.add_node("research_context", research_context)
    workflow.add_node("analyze_context", analyze_context)  
    workflow.add_node("parse_intent", parse_intent)
    # ... existing nodes

    # Enhanced flow with research
    workflow.add_edge(START, "research_context")
    workflow.add_edge("research_context", "analyze_context")
    
    # ... rest of workflow
```

### 5.2 Research Context Node
**Function**: New node in workflow

```python
def research_context(state: AgentState) -> AgentState:
    """Node: Research Context Phase - Enhance understanding with external research"""
    print("🔬 Phase 0: Research context enhancement...")
    
    feature_request = state.get("feature_request")
    if not feature_request:
        return state
        
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            print("  ⚠️ Tavily API key not found, skipping research")
            return state
            
        research_agent = ResearchAgent(tavily_api_key)
        
        # Research relevant context
        research_results = research_agent.research_feature_context(
            feature_request=feature_request,
            context_hints=state.get("context_hints", [])
        )
        
        state["research_context"] = research_results
        print(f"  ✓ Research complete: {len(research_results.get('insights', []))} insights")
        
    except Exception as e:
        print(f"  ❌ Research failed: {e}")
        state["errors"].append(f"Research error: {str(e)}")
        
    return state
```

## 🚀 Phase 6: Multi-Agent Specialization (Week 6)

### 6.1 Specialized Agent Pool
**File**: `agents/specialized_pool.py`

```python
class SpecializedAgentPool:
    def __init__(self):
        self.agents = {
            'architecture': self._create_architecture_agent(),
            'security': self._create_security_agent(),
            'performance': self._create_performance_agent(),
            'database': self._create_database_agent(),
            'testing': self._create_testing_agent(),
            'deployment': self._create_deployment_agent()
        }
        
    def select_agents_for_task(self, 
                              task: Task, 
                              stack_info: StackInfo,
                              complexity: str) -> List[Agent]:
        """
        Select appropriate agents based on task requirements
        """
        selected_agents = ['architecture']  # Always include architecture
        
        # Task-based selection
        if task.involves_data_storage():
            selected_agents.append('database')
            
        if task.involves_user_authentication():
            selected_agents.append('security')
            
        if task.is_high_performance():
            selected_agents.append('performance')
            
        if complexity in ['medium', 'high']:
            selected_agents.append('testing')
            
        return [self.agents[agent_name] for agent_name in selected_agents]
```

### 6.2 Agent Coordination
**File**: `agents/coordinator.py`

```python
class AgentCoordinator:
    def __init__(self, agent_pool: SpecializedAgentPool):
        self.agent_pool = agent_pool
        
    def coordinate_implementation(self, 
                                task: Task, 
                                context: Dict) -> CoordinatedResult:
        """
        Coordinate multiple agents for complex tasks
        """
        agents = self.agent_pool.select_agents_for_task(
            task, 
            context['stack_info'], 
            context['complexity']
        )
        
        # Parallel execution for independent tasks
        parallel_results = []
        for agent in agents:
            if agent.can_run_parallel():
                result = agent.execute_async(task, context)
                parallel_results.append(result)
                
        # Sequential execution for dependent tasks  
        sequential_results = []
        for agent in agents:
            if not agent.can_run_parallel():
                # Use results from parallel agents
                enhanced_context = {**context, 'parallel_results': parallel_results}
                result = agent.execute(task, enhanced_context)
                sequential_results.append(result)
                
        return self._merge_results(parallel_results, sequential_results)
```

## 📊 Testing Strategy

### 6.1 Multi-Framework Test Suite
**File**: `tests/test_agnostic_agent.py`

```python
class TestAgnosticAgent:
    def test_spring_boot_spec(self):
        """Test with Java Spring Boot specification"""
        spec = load_spec("inventory-management-system.md")
        result = agent.process_specification(spec, codebase_path="spring-boot-project")
        
        assert result.framework == "spring_boot"
        assert result.language == "java"
        assert "JPA" in result.detected_technologies
        
    def test_fastapi_spec(self):
        """Test with Python FastAPI specification"""  
        spec = load_spec("crypto-monitoring-system.md")
        result = agent.process_specification(spec, codebase_path="fastapi-project")
        
        assert result.framework == "fastapi"
        assert result.language == "python"
        assert "Pydantic" in result.detected_technologies
        
    def test_unknown_framework_fallback(self):
        """Test fallback behavior for unknown frameworks"""
        spec = load_spec("novel-framework-spec.md") 
        result = agent.process_specification(spec, codebase_path="unknown-project")
        
        assert result.framework == "generic"
        assert len(result.research_insights) > 0
```

## 🚀 Implementation Timeline

### Week 1: Universal Detection
- [ ] Implement `UniversalStackDetector` 
- [ ] Add architecture pattern detection
- [ ] Integrate with existing analysis flow
- [ ] Test with all existing specifications

### Week 2: Dynamic Instructions
- [ ] Create instruction template engine
- [ ] Build framework-specific templates
- [ ] Integrate with code synthesis flow
- [ ] Test instruction generation

### Week 3: Research Enhancement
- [ ] Implement Tavily API integration
- [ ] Create knowledge gap detection
- [ ] Enhance specification parsing
- [ ] Test research capabilities

### Week 4: Universal Placement
- [ ] Build placement engine
- [ ] Create framework-specific rules
- [ ] Remove hardcoded placement logic
- [ ] Test with multiple frameworks

### Week 5: Workflow Enhancement
- [ ] Add research context node
- [ ] Enhance LangGraph orchestration
- [ ] Improve error handling
- [ ] End-to-end testing

### Week 6: Multi-Agent System
- [ ] Implement specialized agent pool
- [ ] Create agent coordinator
- [ ] Test complex specifications
- [ ] Performance optimization

## 🎯 Success Criteria

### Functional Requirements
1. ✅ **Framework Agnostic**: No hardcoded framework assumptions
2. ✅ **Research Enhanced**: Automatic context research with Tavily
3. ✅ **Dynamic Instructions**: Template-based instruction generation
4. ✅ **Universal Placement**: Convention-based file placement
5. ✅ **Multi-Agent**: Specialized agents for different concerns

### Quality Requirements
1. 🎯 **95%+ Framework Detection Accuracy**
2. 🎯 **100% Existing Spec Compatibility**
3. 🎯 **<2s Research Response Time**
4. 🎯 **Zero Hardcoded Framework Logic**
5. 🎯 **Extensible Architecture**

## 🔄 Continuous Improvement

### Metrics Collection
- Framework detection accuracy
- Implementation completeness per framework
- Research quality scoring
- User satisfaction feedback

### Feedback Loop
- Monitor specification processing success rates
- Collect framework coverage gaps
- Track research enhancement effectiveness
- Optimize template quality based on results

This plan transforms the current agent into a truly agnostic system that can handle any specification format, research missing context automatically, and implement solutions following framework-specific best practices without any hardcoded assumptions.