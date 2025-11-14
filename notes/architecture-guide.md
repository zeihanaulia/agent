# Architecture Guide

## System Architecture Overview

The Framework-Agnostic Coding Agent represents a paradigm shift from hardcoded, framework-specific code generation to intelligent, adaptive systems that work with any technology stack. This document details the architectural principles, component design, and integration patterns that make this possible.

## Core Architectural Principles

### 1. Framework Agnosticism
**Principle**: The system should adapt to any framework without hardcoded assumptions  
**Implementation**: Dynamic detection, template-based generation, configurable patterns  
**Benefits**: Future-proof, technology-independent, reduced maintenance  

### 2. Intelligent Context Understanding
**Principle**: Deep comprehension of project structure, patterns, and conventions  
**Implementation**: Tree-sitter parsing, semantic analysis, external research integration  
**Benefits**: Higher quality outputs, framework compliance, best practice enforcement  

### 3. Multi-Agent Coordination
**Principle**: Specialized agents handle different aspects of development  
**Implementation**: Agent orchestration, task distribution, result synthesis  
**Benefits**: Expertise specialization, parallel processing, comprehensive coverage  

### 4. Extensible Template System
**Principle**: Framework-specific code generation through dynamic templates  
**Implementation**: Jinja2 templating, pattern libraries, customizable generation  
**Benefits**: Consistent outputs, maintainable patterns, easy framework addition  

## System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Framework-Agnostic Coding Agent                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │
│ │   Universal     │  │   Research      │  │   Dynamic Template  │   │
│ │   Framework     │  │   Integration   │  │   System           │   │
│ │   Detector      │  │   Engine        │  │                    │   │
│ │                 │  │                 │  │   ┌─────────────┐   │   │
│ │ ┌─────────────┐ │  │ ┌─────────────┐ │  │   │ Spring Boot │   │   │
│ │ │Tree-sitter  │ │  │ │ Tavily API  │ │  │   │ Templates   │   │   │
│ │ │Parsers      │ │  │ │ Integration │ │  │   └─────────────┘   │   │
│ │ └─────────────┘ │  │ └─────────────┘ │  │   ┌─────────────┐   │   │
│ │ ┌─────────────┐ │  │ ┌─────────────┐ │  │   │ FastAPI     │   │   │
│ │ │Dependency   │ │  │ │ Knowledge   │ │  │   │ Templates   │   │   │
│ │ │Analysis     │ │  │ │ Synthesis   │ │  │   └─────────────┘   │   │
│ │ └─────────────┘ │  │ └─────────────┘ │  │   ┌─────────────┐   │   │
│ │ ┌─────────────┐ │  │ ┌─────────────┐ │  │   │ Express.js  │   │   │
│ │ │Architecture │ │  │ │ Pattern     │ │  │   │ Templates   │   │   │
│ │ │Detection    │ │  │ │ Recognition │ │  │   └─────────────┘   │   │
│ │ └─────────────┘ │  │ └─────────────┘ │  │                     │   │
│ └─────────────────┘  └─────────────────┘  └─────────────────────┘   │
│          │                    │                         │           │
│          ▼                    ▼                         ▼           │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                  LangGraph Workflow Engine                      │ │
│ │                                                                 │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│ │ │ Analyze     │ │ Parse       │ │ Research    │ │ Synthesize  │ │ │
│ │ │ Context     │ │ Intent      │ │ Context     │ │ Code        │ │ │
│ │ │             │ │             │ │             │ │             │ │ │
│ │ │ • Framework │ │ • Spec      │ │ • Best      │ │ • Template  │ │ │
│ │ │   Detection │ │   Parsing   │ │   Practices │ │   Selection │ │ │
│ │ │ • Repo      │ │ • Agent     │ │ • Security  │ │ • Code Gen  │ │ │
│ │ │   Mapping   │ │   Based     │ │   Research  │ │ • File      │ │ │
│ │ │ • Pattern   │ │ • Intent    │ │ • Framework │ │   Placement │ │ │
│ │ │   Analysis  │ │   Extract   │ │   Docs      │ │ • Quality   │ │ │
│ │ │             │ │             │ │             │ │   Assurance │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                  │                                  │
│                                  ▼                                  │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                   Multi-Agent Coordination                      │ │
│ │                                                                 │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│ │ │Architecture │ │ Security    │ │ Performance │ │ Database    │ │ │
│ │ │Agent        │ │ Agent       │ │ Agent       │ │ Agent       │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│ │ │Testing      │ │ Deployment  │ │ Documentation │ │Coordination│ │ │
│ │ │Agent        │ │ Agent       │ │ Agent        │ │ Controller │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                  │                                  │
│                                  ▼                                  │
│ ┌─────────────────┐              │              ┌─────────────────┐ │
│ │   Universal     │              │              │    Quality      │ │
│ │   File          │              │              │    Assurance    │ │
│ │   Placement     │◄─────────────┴─────────────►│    Engine       │ │
│ │   Engine        │                             │                 │ │
│ │                 │                             │ ┌─────────────┐ │ │
│ │ ┌─────────────┐ │                             │ │ Syntax      │ │ │
│ │ │Maven/Gradle │ │                             │ │ Validation  │ │ │
│ │ │Structure    │ │                             │ │ └─────────────┘ │ │
│ │ └─────────────┘ │                             │ ┌─────────────┐ │ │
│ │ ┌─────────────┐ │                             │ │ Pattern     │ │ │
│ │ │Poetry/pip   │ │                             │ │ Compliance  │ │ │
│ │ │Structure    │ │                             │ │ └─────────────┘ │ │
│ │ └─────────────┘ │                             │ ┌─────────────┐ │ │
│ │ ┌─────────────┐ │                             │ │ Best        │ │ │
│ │ │npm/yarn     │ │                             │ │ Practice    │ │ │
│ │ │Structure    │ │                             │ │ Enforcement │ │ │
│ │ └─────────────┘ │                             │ └─────────────┘ │ │
│ └─────────────────┘                             └─────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Architecture

### 1. Universal Framework Detector

**Purpose**: Automatically identify technology stacks, build systems, and architectural patterns

#### 1.1 Technology Stack Detection
```python
class UniversalStackDetector:
    def __init__(self):
        self.parsers = self._initialize_parsers()
        self.detectors = {
            'java': JavaStackDetector(),
            'python': PythonStackDetector(), 
            'javascript': JavaScriptStackDetector(),
            'typescript': TypeScriptStackDetector(),
            'go': GoStackDetector(),
            'rust': RustStackDetector()
        }
    
    def detect_framework(self, codebase_path: str) -> FrameworkInfo:
        # Primary language detection
        language = self._detect_primary_language(codebase_path)
        
        # Framework-specific detection
        detector = self.detectors.get(language)
        if not detector:
            return self._fallback_detection(codebase_path)
            
        return detector.analyze(codebase_path)
    
    def _detect_primary_language(self, path: str) -> str:
        file_counts = defaultdict(int)
        for file_path in self._scan_files(path):
            lang = self._identify_language(file_path)
            file_counts[lang] += 1
        return max(file_counts.items(), key=lambda x: x[1])[0]
```

#### 1.2 Architecture Pattern Recognition
```python
class ArchitecturePatternDetector:
    def detect_patterns(self, codebase_info: CodebaseInfo) -> List[ArchitecturePattern]:
        patterns = []
        
        # Layered Architecture Detection
        if self._has_controller_service_repository(codebase_info):
            patterns.append(ArchitecturePattern.LAYERED)
            
        # Clean Architecture Detection  
        if self._has_domain_usecase_infrastructure(codebase_info):
            patterns.append(ArchitecturePattern.CLEAN)
            
        # Hexagonal Architecture Detection
        if self._has_ports_adapters_structure(codebase_info):
            patterns.append(ArchitecturePattern.HEXAGONAL)
            
        # Microservices Pattern Detection
        if self._has_service_mesh_indicators(codebase_info):
            patterns.append(ArchitecturePattern.MICROSERVICES)
            
        return patterns
```

### 2. Research Integration Engine

**Purpose**: Enhance context understanding through external research and knowledge synthesis

#### 2.1 Tavily API Integration
```python
class ResearchEnhancedSpecParser:
    def __init__(self, tavily_client: TavilyClient):
        self.tavily = tavily_client
        self.base_parser = AgentBasedSpecParser()
        self.knowledge_cache = KnowledgeCache()
    
    async def parse_specification(self, spec: str, context: ProjectContext) -> EnhancedSpecification:
        # Base specification parsing
        base_spec = await self.base_parser.parse(spec)
        
        # Research enhancement
        research_queries = self._generate_research_queries(base_spec, context)
        research_results = await self._conduct_research(research_queries)
        
        # Knowledge synthesis
        enhanced_context = self._synthesize_knowledge(base_spec, research_results)
        
        return EnhancedSpecification(
            base_specification=base_spec,
            research_context=enhanced_context,
            best_practices=research_results.best_practices,
            security_considerations=research_results.security_patterns,
            performance_optimizations=research_results.performance_patterns
        )
    
    async def _conduct_research(self, queries: List[ResearchQuery]) -> ResearchResults:
        results = []
        for query in queries:
            # Check cache first
            cached = self.knowledge_cache.get(query.cache_key)
            if cached and not cached.is_stale():
                results.append(cached)
                continue
                
            # Perform research via Tavily
            search_results = await self.tavily.search(
                query=query.search_term,
                search_depth="advanced",
                max_results=5,
                include_domains=["official_docs", "best_practices"]
            )
            
            # Process and cache results
            processed = self._process_search_results(search_results, query)
            self.knowledge_cache.set(query.cache_key, processed)
            results.append(processed)
            
        return ResearchResults(results)
```

#### 2.2 Knowledge Synthesis
```python
class KnowledgeSynthesizer:
    def synthesize_patterns(self, research_data: ResearchResults, framework: FrameworkInfo) -> SynthesizedPatterns:
        # Extract framework-specific patterns
        framework_patterns = self._extract_framework_patterns(research_data, framework)
        
        # Synthesize security patterns
        security_patterns = self._synthesize_security_patterns(research_data)
        
        # Synthesize performance patterns
        performance_patterns = self._synthesize_performance_patterns(research_data)
        
        # Create comprehensive pattern library
        return SynthesizedPatterns(
            framework_patterns=framework_patterns,
            security_patterns=security_patterns,
            performance_patterns=performance_patterns,
            integration_patterns=self._synthesize_integration_patterns(research_data)
        )
```

### 3. Dynamic Template System

**Purpose**: Generate framework-appropriate code using intelligent, configurable templates

#### 3.1 Template Engine Architecture
```python
class InstructionTemplateEngine:
    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.template_registry = TemplateRegistry()
        self.pattern_library = PatternLibrary()
    
    def generate_instruction(self, 
                           template_name: str, 
                           context: GenerationContext) -> GenerationInstruction:
        # Load framework-specific template
        template = self._load_template(template_name, context.framework)
        
        # Enhance context with patterns
        enhanced_context = self._enhance_context(context)
        
        # Generate instruction
        instruction_content = template.render(**enhanced_context)
        
        return GenerationInstruction(
            content=instruction_content,
            file_placement=self._determine_placement(context),
            quality_checks=self._define_quality_checks(context),
            test_requirements=self._define_test_requirements(context)
        )
```

#### 3.2 Framework-Specific Templates

**Spring Boot Entity Template** (`spring_boot_entity.j2`):
```java
package {{ package_name }}.entity;

import javax.persistence.*;
import javax.validation.constraints.*;
import java.time.LocalDateTime;
import java.util.Objects;

/**
 * {{ entity_description }}
 * 
 * @author Generated by Agnostic Coding Agent
 * @version 1.0
 */
@Entity
@Table(name = "{{ table_name }}")
public class {{ entity_name }} {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
{% for field in fields %}
    {% if field.validation %}
    @{{ field.validation }}
    {% endif %}
    {% if field.column_definition %}
    @Column({{ field.column_definition }})
    {% endif %}
    private {{ field.type }} {{ field.name }};
{% endfor %}

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // Default constructor
    public {{ entity_name }}() {}
    
    // Constructor with required fields
    public {{ entity_name }}({% for field in required_fields %}{{ field.type }} {{ field.name }}{% if not loop.last %}, {% endif %}{% endfor %}) {
        {% for field in required_fields %}
        this.{{ field.name }} = {{ field.name }};
        {% endfor %}
    }
    
{% for field in all_fields %}
    public {{ field.type }} get{{ field.name|title }}() {
        return {{ field.name }};
    }
    
    public void set{{ field.name|title }}({{ field.type }} {{ field.name }}) {
        this.{{ field.name }} = {{ field.name }};
    }
{% endfor %}

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        {{ entity_name }} that = ({{ entity_name }}) o;
        return Objects.equals(id, that.id);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
    
    @Override
    public String toString() {
        return "{{ entity_name }}{" +
                "id=" + id +
                {% for field in fields %}
                ", {{ field.name }}='" + {{ field.name }} + '\'' +
                {% endfor %}
                ", createdAt=" + createdAt +
                ", updatedAt=" + updatedAt +
                '}';
    }
}
```

**FastAPI Model Template** (`fastapi_model.j2`):
```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class {{ model_name }}Base(BaseModel):
    """Base {{ model_name }} model for shared attributes"""
    {% for field in base_fields %}
    {{ field.name }}: {{ field.type }} = Field(
        {% if field.description %}description="{{ field.description }}"{% endif %}
        {% if field.constraints %}, {{ field.constraints }}{% endif %}
    )
    {% endfor %}
    
    {% for field in validated_fields %}
    @validator('{{ field.name }}')
    def validate_{{ field.name }}(cls, v):
        {{ field.validation_code }}
        return v
    {% endfor %}

class {{ model_name }}Create({{ model_name }}Base):
    """Model for creating {{ model_name }}"""
    pass

class {{ model_name }}Update({{ model_name }}Base):
    """Model for updating {{ model_name }}"""
    {% for field in base_fields %}
    {{ field.name }}: Optional[{{ field.type }}] = None
    {% endfor %}

class {{ model_name }}InDB({{ model_name }}Base):
    """Model representing {{ model_name }} in database"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class {{ model_name }}({{ model_name }}InDB):
    """Public {{ model_name }} model"""
    pass

# SQLAlchemy Model
class {{ model_name }}Model(Base):
    __tablename__ = "{{ table_name }}"
    
    id = Column(Integer, primary_key=True, index=True)
    {% for field in database_fields %}
    {{ field.name }} = Column({{ field.sqlalchemy_type }}{% if field.constraints %}, {{ field.constraints }}{% endif %})
    {% endfor %}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 4. Multi-Agent Coordination System

**Purpose**: Orchestrate specialized agents for comprehensive development coverage

#### 4.1 Agent Coordination Architecture
```python
class AgentCoordinator:
    def __init__(self):
        self.agents = {
            'architecture': ArchitectureAgent(),
            'security': SecurityAgent(),
            'performance': PerformanceAgent(),
            'database': DatabaseAgent(),
            'testing': TestingAgent(),
            'deployment': DeploymentAgent(),
            'documentation': DocumentationAgent()
        }
        self.task_distributor = TaskDistributor()
        self.result_synthesizer = ResultSynthesizer()
    
    async def coordinate_feature_development(self, 
                                           specification: EnhancedSpecification,
                                           context: ProjectContext) -> CoordinatedResult:
        # Analyze requirements and distribute tasks
        task_distribution = self.task_distributor.analyze_and_distribute(
            specification, context
        )
        
        # Execute tasks in parallel where possible
        results = await self._execute_parallel_tasks(task_distribution)
        
        # Synthesize results with conflict resolution
        synthesized_result = self.result_synthesizer.synthesize(
            results, specification, context
        )
        
        # Validate comprehensive coverage
        validation_result = self._validate_coverage(synthesized_result)
        
        return CoordinatedResult(
            synthesized_result=synthesized_result,
            validation_result=validation_result,
            agent_contributions=results
        )
```

#### 4.2 Specialized Agent Implementations

**Architecture Agent**:
```python
class ArchitectureAgent(BaseAgent):
    def analyze_requirements(self, spec: EnhancedSpecification) -> ArchitectureAnalysis:
        return ArchitectureAnalysis(
            recommended_patterns=self._recommend_patterns(spec),
            layering_strategy=self._analyze_layering(spec),
            module_structure=self._design_modules(spec),
            integration_points=self._identify_integrations(spec)
        )
    
    def generate_architecture_code(self, analysis: ArchitectureAnalysis, 
                                 context: ProjectContext) -> ArchitectureCode:
        # Generate architectural components
        return ArchitectureCode(
            base_classes=self._generate_base_classes(analysis, context),
            interfaces=self._generate_interfaces(analysis, context), 
            configurations=self._generate_configurations(analysis, context),
            documentation=self._generate_architecture_docs(analysis)
        )
```

**Security Agent**:
```python
class SecurityAgent(BaseAgent):
    def analyze_security_requirements(self, spec: EnhancedSpecification) -> SecurityAnalysis:
        return SecurityAnalysis(
            authentication_strategy=self._analyze_auth_requirements(spec),
            authorization_patterns=self._analyze_authz_requirements(spec),
            data_protection=self._analyze_data_protection(spec),
            vulnerability_mitigations=self._identify_vulnerabilities(spec)
        )
    
    def generate_security_code(self, analysis: SecurityAnalysis,
                             context: ProjectContext) -> SecurityCode:
        return SecurityCode(
            auth_implementation=self._generate_auth_code(analysis, context),
            authorization_logic=self._generate_authz_code(analysis, context),
            security_configs=self._generate_security_configs(analysis, context),
            security_tests=self._generate_security_tests(analysis, context)
        )
```

### 5. Universal File Placement Engine

**Purpose**: Organize generated files according to framework conventions and best practices

#### 5.1 Framework-Aware Placement
```python
class UniversalPlacementEngine:
    def __init__(self):
        self.placement_rules = {
            'spring_boot': SpringBootPlacementRules(),
            'fastapi': FastAPIPlacementRules(),
            'express': ExpressPlacementRules(),
            'django': DjangoPlacementRules()
        }
    
    def determine_placement(self, 
                          code_artifact: CodeArtifact,
                          context: ProjectContext) -> PlacementDecision:
        # Get framework-specific placement rules
        rules = self.placement_rules.get(context.framework.name)
        if not rules:
            rules = self._create_generic_rules(context)
        
        # Determine optimal placement
        placement = rules.determine_placement(code_artifact, context)
        
        # Validate placement decision
        validation = self._validate_placement(placement, context)
        
        return PlacementDecision(
            target_path=placement.target_path,
            package_structure=placement.package_structure,
            import_adjustments=placement.import_adjustments,
            validation_result=validation
        )
```

#### 5.2 Framework-Specific Rules

**Spring Boot Placement Rules**:
```python
class SpringBootPlacementRules(PlacementRules):
    def determine_placement(self, artifact: CodeArtifact, context: ProjectContext) -> Placement:
        base_package = context.base_package_path
        
        placement_map = {
            'entity': f'{base_package}/entity',
            'repository': f'{base_package}/repository', 
            'service': f'{base_package}/service',
            'controller': f'{base_package}/controller',
            'dto': f'{base_package}/dto',
            'config': f'{base_package}/config',
            'exception': f'{base_package}/exception',
            'util': f'{base_package}/util',
            'test': f'src/test/java/{base_package.replace(".", "/")}'
        }
        
        return Placement(
            target_path=placement_map.get(artifact.type, base_package),
            package_declaration=self._generate_package_declaration(artifact, base_package),
            imports=self._calculate_required_imports(artifact, context)
        )
```

## Integration Patterns

### 1. LangGraph Workflow Integration

```python
def create_agnostic_workflow() -> CompiledGraph:
    workflow = StateGraph(AgnosticAgentState)
    
    # Add nodes with enhanced capabilities
    workflow.add_node("analyze_context", enhanced_analyze_context)
    workflow.add_node("research_context", research_enhanced_context)
    workflow.add_node("parse_intent", agent_based_parse_intent)
    workflow.add_node("coordinate_agents", multi_agent_coordination)
    workflow.add_node("synthesize_code", template_based_synthesis)
    workflow.add_node("place_files", universal_file_placement)
    workflow.add_node("validate_quality", comprehensive_validation)
    
    # Define enhanced workflow edges
    workflow.add_edge(START, "analyze_context")
    workflow.add_edge("analyze_context", "research_context")
    workflow.add_edge("research_context", "parse_intent")
    workflow.add_edge("parse_intent", "coordinate_agents")
    workflow.add_edge("coordinate_agents", "synthesize_code")
    workflow.add_edge("synthesize_code", "place_files")
    workflow.add_edge("place_files", "validate_quality")
    workflow.add_edge("validate_quality", END)
    
    return workflow.compile()
```

### 2. Enhanced Workflow Nodes

```python
async def enhanced_analyze_context(state: AgnosticAgentState) -> AgnosticAgentState:
    """Enhanced context analysis with universal framework detection"""
    
    # Universal framework detection
    detector = UniversalStackDetector()
    framework_info = detector.detect_framework(state.codebase_path)
    
    # Repository mapping with efficiency optimization
    repo_analyzer = AiderStyleRepoAnalyzer()
    repo_map = repo_analyzer.analyze_codebase(
        state.codebase_path, 
        framework_info=framework_info
    )
    
    # Architecture pattern detection
    arch_detector = ArchitecturePatternDetector()
    architecture_patterns = arch_detector.detect_patterns(framework_info, repo_map)
    
    return state.update(
        framework_info=framework_info,
        repository_map=repo_map,
        architecture_patterns=architecture_patterns,
        analysis_complete=True
    )

async def research_enhanced_context(state: AgnosticAgentState) -> AgnosticAgentState:
    """Research integration for enhanced context understanding"""
    
    research_engine = ResearchEnhancedSpecParser(
        tavily_client=TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    )
    
    # Enhance specification with research
    enhanced_spec = await research_engine.parse_specification(
        state.feature_specification,
        ProjectContext(
            framework_info=state.framework_info,
            repository_map=state.repository_map,
            architecture_patterns=state.architecture_patterns
        )
    )
    
    return state.update(
        enhanced_specification=enhanced_spec,
        research_complete=True
    )

async def multi_agent_coordination(state: AgnosticAgentState) -> AgnosticAgentState:
    """Multi-agent coordination for comprehensive coverage"""
    
    coordinator = AgentCoordinator()
    
    # Coordinate specialized agents
    coordination_result = await coordinator.coordinate_feature_development(
        state.enhanced_specification,
        ProjectContext.from_state(state)
    )
    
    return state.update(
        coordination_result=coordination_result,
        agent_contributions=coordination_result.agent_contributions,
        coordination_complete=True
    )
```

## Performance and Scalability

### 1. Repository Mapping Optimization

**Aider-Style Symbol Extraction**:
```python
class OptimizedRepoAnalyzer:
    def __init__(self):
        self.symbol_extractor = SymbolExtractor()
        self.dependency_graph = DependencyGraph()
        
    def analyze_codebase(self, path: str, framework_info: FrameworkInfo) -> OptimizedRepoMap:
        # Extract symbols instead of full content
        symbols = self.symbol_extractor.extract_symbols(path, framework_info.language)
        
        # Build dependency relationships
        dependencies = self.dependency_graph.build_graph(symbols)
        
        # Rank symbols by importance
        ranked_symbols = self._rank_symbols(symbols, dependencies)
        
        # Create token-efficient context
        return OptimizedRepoMap(
            symbols=ranked_symbols,
            dependencies=dependencies,
            token_count=self._calculate_token_count(ranked_symbols)
        )
```

### 2. Caching Strategy

```python
class IntelligentCache:
    def __init__(self):
        self.framework_cache = FrameworkDetectionCache()
        self.research_cache = ResearchCache()
        self.template_cache = TemplateCache()
        
    async def get_or_compute_framework_info(self, codebase_path: str) -> FrameworkInfo:
        cache_key = self._generate_cache_key(codebase_path)
        cached = self.framework_cache.get(cache_key)
        
        if cached and not self._is_stale(cached, codebase_path):
            return cached.framework_info
            
        # Compute and cache
        framework_info = await self._detect_framework(codebase_path)
        self.framework_cache.set(cache_key, framework_info)
        return framework_info
```

## Quality Assurance

### 1. Multi-Layer Validation

```python
class ComprehensiveValidator:
    def __init__(self):
        self.syntax_validator = SyntaxValidator()
        self.pattern_validator = PatternValidator()
        self.security_validator = SecurityValidator()
        self.performance_validator = PerformanceValidator()
        
    def validate_generated_code(self, generated_code: GeneratedCode,
                               context: ProjectContext) -> ValidationResult:
        validations = []
        
        # Syntax validation
        validations.append(self.syntax_validator.validate(generated_code))
        
        # Pattern compliance validation
        validations.append(self.pattern_validator.validate(generated_code, context))
        
        # Security validation
        validations.append(self.security_validator.validate(generated_code))
        
        # Performance validation
        validations.append(self.performance_validator.validate(generated_code))
        
        return ValidationResult.aggregate(validations)
```

## Extension Points

### 1. Adding New Framework Support

```python
class NewFrameworkIntegration:
    """Template for adding new framework support"""
    
    def create_framework_detector(self) -> FrameworkDetector:
        """Implement framework-specific detection logic"""
        return CustomFrameworkDetector()
    
    def create_placement_rules(self) -> PlacementRules:
        """Implement framework-specific file placement"""
        return CustomPlacementRules()
    
    def create_templates(self) -> TemplateSet:
        """Create framework-specific templates"""
        return CustomTemplateSet()
    
    def integrate_with_system(self):
        """Register with main system"""
        system = AgnosticAgentSystem()
        system.register_framework_support(
            framework_name="custom_framework",
            detector=self.create_framework_detector(),
            placement_rules=self.create_placement_rules(),
            templates=self.create_templates()
        )
```

This architecture provides a comprehensive, extensible foundation for framework-agnostic code generation that adapts to any technology stack while maintaining high quality and following best practices.