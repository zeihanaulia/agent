# API Reference

## Core API Classes and Interfaces

### Framework Detection API

#### `UniversalStackDetector`

**Purpose**: Automatically detect technology stacks and frameworks in codebases.

```python
class UniversalStackDetector:
    """Universal framework detection with support for multiple languages and frameworks"""
    
    def __init__(self):
        self.parsers: Dict[str, TreeSitterParser]
        self.detectors: Dict[str, FrameworkDetector]
    
    def detect_framework(self, codebase_path: str) -> FrameworkInfo:
        """
        Detect the primary framework used in a codebase.
        
        Args:
            codebase_path: Absolute path to the codebase directory
            
        Returns:
            FrameworkInfo: Detected framework information
            
        Raises:
            DetectionError: If framework detection fails
            FileNotFoundError: If codebase path doesn't exist
        """
        
    def detect_all_frameworks(self, codebase_path: str) -> List[FrameworkInfo]:
        """
        Detect all frameworks present in a multi-framework codebase.
        
        Args:
            codebase_path: Absolute path to the codebase directory
            
        Returns:
            List[FrameworkInfo]: All detected frameworks
        """
        
    def get_supported_frameworks(self) -> Dict[str, List[str]]:
        """
        Get list of all supported frameworks by language.
        
        Returns:
            Dict mapping languages to framework lists
        """
```

#### `FrameworkInfo`

**Purpose**: Data structure containing comprehensive framework information.

```python
@dataclass
class FrameworkInfo:
    """Complete framework information"""
    
    name: str                              # Framework name (e.g., "Spring Boot")
    version: Optional[str]                 # Detected version
    language: str                          # Primary language (e.g., "Java")
    build_system: BuildSystem              # Build system info
    project_structure: ProjectStructure    # Directory structure
    dependencies: List[DependencyInfo]     # External dependencies
    architecture_patterns: List[str]       # Detected patterns
    conventions: FrameworkConventions      # Naming and structure conventions
    
    @property
    def is_web_framework(self) -> bool:
        """Check if this is a web framework"""
        
    @property
    def supports_async(self) -> bool:
        """Check if framework supports async patterns"""
        
    def get_template_context(self) -> Dict[str, Any]:
        """Get context data for template rendering"""
```

#### `BuildSystem`

**Purpose**: Information about project build and dependency management.

```python
@dataclass 
class BuildSystem:
    """Build system configuration"""
    
    name: str                    # Build system name (maven, gradle, pip, npm)
    version: Optional[str]       # Build system version
    config_files: List[str]      # Configuration file paths
    source_directories: List[str] # Source code directories
    test_directories: List[str]   # Test directories
    output_directory: str         # Build output directory
    
    def get_dependency_command(self, package: str) -> str:
        """Get command to add a new dependency"""
        
    def get_build_command(self) -> str:
        """Get command to build the project"""
        
    def get_test_command(self) -> str:
        """Get command to run tests"""
```

### Template System API

#### `InstructionTemplateEngine`

**Purpose**: Dynamic template-based code generation system.

```python
class InstructionTemplateEngine:
    """Dynamic template engine for framework-specific code generation"""
    
    def __init__(self):
        self.jinja_env: Environment
        self.template_registry: TemplateRegistry
        self.pattern_library: PatternLibrary
    
    def generate_instruction(self, 
                           template_name: str,
                           context: GenerationContext) -> GenerationInstruction:
        """
        Generate code generation instruction from template.
        
        Args:
            template_name: Name of template to use
            context: Generation context with variables
            
        Returns:
            GenerationInstruction: Complete instruction for code generation
            
        Raises:
            TemplateNotFoundError: If template doesn't exist
            TemplateRenderError: If template rendering fails
        """
        
    def register_template(self, 
                         framework: str,
                         template_type: str, 
                         template_path: str):
        """
        Register a new template for a framework.
        
        Args:
            framework: Framework name
            template_type: Type of template (controller, model, etc.)
            template_path: Path to Jinja2 template file
        """
        
    def get_available_templates(self, framework: str) -> List[str]:
        """
        Get list of available templates for a framework.
        
        Args:
            framework: Framework name
            
        Returns:
            List of template types available
        """
```

#### `GenerationContext`

**Purpose**: Context data for template rendering.

```python
@dataclass
class GenerationContext:
    """Context for code generation"""
    
    framework: FrameworkInfo           # Framework information
    specification: EnhancedSpecification # Feature specification
    project_context: ProjectContext   # Project-specific context
    template_variables: Dict[str, Any] # Template variables
    
    def add_variable(self, name: str, value: Any):
        """Add a template variable"""
        
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a template variable"""
        
    def merge_context(self, other: 'GenerationContext'):
        """Merge another context into this one"""
```

#### `GenerationInstruction`

**Purpose**: Complete instruction for code generation.

```python
@dataclass
class GenerationInstruction:
    """Complete code generation instruction"""
    
    content: str                      # Generated code content
    file_placement: PlacementDecision # Where to place the file
    quality_checks: List[QualityCheck] # Quality validation requirements
    test_requirements: List[TestRequirement] # Testing requirements
    dependencies: List[str]           # Additional dependencies needed
    
    def validate_instruction(self) -> ValidationResult:
        """Validate the instruction completeness"""
        
    def execute_instruction(self, target_path: str) -> ExecutionResult:
        """Execute the instruction to generate code"""
```

### Research Integration API

#### `ResearchEnhancedSpecParser`

**Purpose**: Specification parsing enhanced with external research.

```python
class ResearchEnhancedSpecParser:
    """Specification parser with Tavily research integration"""
    
    def __init__(self, tavily_client: TavilyClient):
        self.tavily: TavilyClient
        self.base_parser: AgentBasedSpecParser
        self.knowledge_cache: KnowledgeCache
    
    async def parse_specification(self, 
                                 spec: str,
                                 context: ProjectContext) -> EnhancedSpecification:
        """
        Parse specification with research enhancement.
        
        Args:
            spec: Raw specification text
            context: Project context for targeted research
            
        Returns:
            EnhancedSpecification: Specification enhanced with research
            
        Raises:
            ParseError: If specification parsing fails
            ResearchError: If external research fails
        """
        
    async def research_topic(self, 
                           topic: str,
                           framework: str) -> ResearchResults:
        """
        Research a specific topic for a framework.
        
        Args:
            topic: Research topic (e.g., "authentication patterns")
            framework: Target framework
            
        Returns:
            ResearchResults: Compiled research information
        """
        
    def get_cached_research(self, query_key: str) -> Optional[ResearchResults]:
        """Get cached research results"""
        
    def clear_cache(self, older_than_hours: int = 24):
        """Clear cached research older than specified hours"""
```

#### `EnhancedSpecification`

**Purpose**: Specification enhanced with external research context.

```python
@dataclass
class EnhancedSpecification:
    """Specification enhanced with research context"""
    
    base_specification: ParsedSpecification   # Original parsed spec
    research_context: ResearchContext        # External research data
    best_practices: List[BestPractice]        # Framework best practices
    security_considerations: List[SecurityPattern] # Security patterns
    performance_optimizations: List[PerformancePattern] # Performance patterns
    
    def get_feature_requirements(self) -> List[FeatureRequirement]:
        """Extract feature requirements from specification"""
        
    def get_technical_constraints(self) -> List[TechnicalConstraint]:
        """Extract technical constraints"""
        
    def get_quality_requirements(self) -> QualityRequirements:
        """Extract quality and testing requirements"""
```

#### `TavilyClient`

**Purpose**: Client for Tavily API research integration.

```python
class TavilyClient:
    """Client for Tavily API integration"""
    
    def __init__(self, api_key: str):
        self.api_key: str
        self.base_url: str = "https://api.tavily.com"
        
    async def search(self,
                    query: str,
                    search_depth: str = "advanced",
                    max_results: int = 5,
                    include_domains: Optional[List[str]] = None) -> SearchResults:
        """
        Search for information using Tavily API.
        
        Args:
            query: Search query
            search_depth: Search depth ("basic" or "advanced")
            max_results: Maximum number of results
            include_domains: Domains to include in search
            
        Returns:
            SearchResults: Search results from Tavily
            
        Raises:
            TavilyAPIError: If API request fails
        """
        
    async def get_research_summary(self, topic: str) -> ResearchSummary:
        """Get a research summary for a topic"""
        
    def get_rate_limit_status(self) -> RateLimitStatus:
        """Get current rate limit status"""
```

### Multi-Agent Coordination API

#### `AgentCoordinator`

**Purpose**: Orchestrate multiple specialized agents for comprehensive development.

```python
class AgentCoordinator:
    """Coordinates multiple specialized agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent]
        self.task_distributor: TaskDistributor
        self.result_synthesizer: ResultSynthesizer
    
    async def coordinate_feature_development(self,
                                           specification: EnhancedSpecification,
                                           context: ProjectContext) -> CoordinatedResult:
        """
        Coordinate multiple agents to implement a feature.
        
        Args:
            specification: Enhanced feature specification
            context: Project context
            
        Returns:
            CoordinatedResult: Synthesized results from all agents
            
        Raises:
            CoordinationError: If agent coordination fails
        """
        
    def register_agent(self, agent_type: str, agent: BaseAgent):
        """Register a specialized agent"""
        
    def get_available_agents(self) -> List[str]:
        """Get list of available agent types"""
        
    async def execute_parallel_tasks(self, 
                                   tasks: List[AgentTask]) -> List[AgentResult]:
        """Execute multiple agent tasks in parallel"""
```

#### `BaseAgent`

**Purpose**: Base class for specialized agents.

```python
class BaseAgent(ABC):
    """Base class for specialized agents"""
    
    def __init__(self, agent_type: str):
        self.agent_type: str
        self.capabilities: List[str]
        
    @abstractmethod
    async def analyze_requirements(self, 
                                 specification: EnhancedSpecification) -> AgentAnalysis:
        """Analyze requirements from agent's perspective"""
        
    @abstractmethod
    async def generate_code(self,
                          analysis: AgentAnalysis,
                          context: ProjectContext) -> AgentCodeResult:
        """Generate code based on analysis"""
        
    @abstractmethod
    def validate_result(self, result: AgentCodeResult) -> ValidationResult:
        """Validate the agent's generated code"""
        
    def get_dependencies(self) -> List[str]:
        """Get agent's dependencies on other agents"""
        
    def get_priority(self) -> int:
        """Get agent's execution priority (1-10, 1 = highest)"""
```

#### Specialized Agent Implementations

**`ArchitectureAgent`**

```python
class ArchitectureAgent(BaseAgent):
    """Specialized agent for architectural concerns"""
    
    async def analyze_requirements(self, spec: EnhancedSpecification) -> ArchitectureAnalysis:
        """
        Analyze architectural requirements.
        
        Returns:
            ArchitectureAnalysis: Recommended patterns and structure
        """
        
    async def generate_architecture_code(self,
                                       analysis: ArchitectureAnalysis,
                                       context: ProjectContext) -> ArchitectureCode:
        """Generate architectural components"""
        
    def recommend_patterns(self, spec: EnhancedSpecification) -> List[ArchitecturePattern]:
        """Recommend architectural patterns"""
```

**`SecurityAgent`**

```python
class SecurityAgent(BaseAgent):
    """Specialized agent for security concerns"""
    
    async def analyze_security_requirements(self, 
                                          spec: EnhancedSpecification) -> SecurityAnalysis:
        """Analyze security requirements and threats"""
        
    async def generate_security_code(self,
                                   analysis: SecurityAnalysis,
                                   context: ProjectContext) -> SecurityCode:
        """Generate security-related code"""
        
    def identify_vulnerabilities(self, code: str) -> List[SecurityVulnerability]:
        """Identify potential security vulnerabilities"""
```

### File Placement API

#### `UniversalPlacementEngine`

**Purpose**: Framework-aware file organization and placement.

```python
class UniversalPlacementEngine:
    """Universal file placement engine for all frameworks"""
    
    def __init__(self):
        self.placement_rules: Dict[str, PlacementRules]
        
    def determine_placement(self,
                          code_artifact: CodeArtifact,
                          context: ProjectContext) -> PlacementDecision:
        """
        Determine optimal file placement for a code artifact.
        
        Args:
            code_artifact: Code to be placed
            context: Project context
            
        Returns:
            PlacementDecision: Where and how to place the file
            
        Raises:
            PlacementError: If placement cannot be determined
        """
        
    def register_placement_rules(self, framework: str, rules: PlacementRules):
        """Register placement rules for a framework"""
        
    def validate_placement(self, 
                         placement: PlacementDecision,
                         context: ProjectContext) -> ValidationResult:
        """Validate a placement decision"""
```

#### `PlacementRules`

**Purpose**: Framework-specific file placement logic.

```python
class PlacementRules(ABC):
    """Abstract base for framework-specific placement rules"""
    
    @abstractmethod
    def determine_placement(self,
                          artifact: CodeArtifact,
                          context: ProjectContext) -> PlacementDecision:
        """Determine placement for an artifact"""
        
    @abstractmethod
    def get_package_name(self,
                        artifact: CodeArtifact,
                        context: ProjectContext) -> str:
        """Get appropriate package/namespace name"""
        
    @abstractmethod
    def calculate_imports(self,
                        artifact: CodeArtifact,
                        placement: PlacementDecision,
                        context: ProjectContext) -> List[ImportStatement]:
        """Calculate required imports"""
        
    def validate_placement(self, placement: PlacementDecision) -> ValidationResult:
        """Validate placement decision"""
```

#### `PlacementDecision`

**Purpose**: Complete file placement decision with all metadata.

```python
@dataclass
class PlacementDecision:
    """Complete file placement decision"""
    
    target_directory: str              # Target directory path
    filename: str                      # Target filename
    package_name: Optional[str]        # Package/namespace name
    imports: List[ImportStatement]     # Required imports
    file_template: Optional[str]       # File template to use
    metadata: Dict[str, Any]          # Additional metadata
    
    def get_full_path(self, base_path: str) -> str:
        """Get complete file path"""
        
    def validate_decision(self) -> ValidationResult:
        """Validate the placement decision"""
        
    def apply_placement(self, base_path: str, content: str) -> bool:
        """Apply the placement decision"""
```

### Quality Assurance API

#### `ComprehensiveValidator`

**Purpose**: Multi-layer code quality validation.

```python
class ComprehensiveValidator:
    """Comprehensive code quality validation"""
    
    def __init__(self):
        self.syntax_validator: SyntaxValidator
        self.pattern_validator: PatternValidator
        self.security_validator: SecurityValidator
        self.performance_validator: PerformanceValidator
        
    def validate_generated_code(self,
                               generated_code: GeneratedCode,
                               context: ProjectContext) -> ValidationResult:
        """
        Perform comprehensive validation of generated code.
        
        Args:
            generated_code: Code to validate
            context: Project context for validation
            
        Returns:
            ValidationResult: Comprehensive validation results
        """
        
    def validate_syntax(self, code: str, language: str) -> SyntaxValidationResult:
        """Validate code syntax"""
        
    def validate_patterns(self, code: str, framework: str) -> PatternValidationResult:
        """Validate framework-specific patterns"""
        
    def validate_security(self, code: str) -> SecurityValidationResult:
        """Validate security aspects"""
        
    def validate_performance(self, code: str) -> PerformanceValidationResult:
        """Validate performance aspects"""
```

#### `ValidationResult`

**Purpose**: Comprehensive validation results.

```python
@dataclass
class ValidationResult:
    """Comprehensive validation results"""
    
    is_valid: bool                     # Overall validation status
    issues: List[ValidationIssue]      # All validation issues
    warnings: List[ValidationWarning]  # Non-critical warnings
    suggestions: List[ValidationSuggestion] # Improvement suggestions
    metrics: ValidationMetrics         # Quality metrics
    
    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        """Get issues filtered by severity"""
        
    def get_error_count(self) -> int:
        """Get count of error-level issues"""
        
    def get_summary(self) -> str:
        """Get validation summary"""
        
    def to_json(self) -> str:
        """Serialize to JSON"""
```

### LangGraph Workflow API

#### `AgnosticAgentState`

**Purpose**: State management for the agnostic agent workflow.

```python
@dataclass
class AgnosticAgentState:
    """State for agnostic agent workflow"""
    
    # Input data
    codebase_path: str
    feature_specification: str
    
    # Analysis results
    framework_info: Optional[FrameworkInfo] = None
    repository_map: Optional[RepositoryMap] = None
    architecture_patterns: List[str] = field(default_factory=list)
    
    # Enhanced specification
    enhanced_specification: Optional[EnhancedSpecification] = None
    research_context: Optional[ResearchContext] = None
    
    # Agent coordination
    coordination_result: Optional[CoordinatedResult] = None
    agent_contributions: Dict[str, AgentResult] = field(default_factory=dict)
    
    # Generated code
    generated_artifacts: List[CodeArtifact] = field(default_factory=list)
    placement_decisions: List[PlacementDecision] = field(default_factory=list)
    
    # Quality assurance
    validation_results: List[ValidationResult] = field(default_factory=list)
    
    # Status flags
    analysis_complete: bool = False
    research_complete: bool = False
    coordination_complete: bool = False
    synthesis_complete: bool = False
    validation_complete: bool = False
    
    def update(self, **kwargs) -> 'AgnosticAgentState':
        """Update state with new values"""
        
    def get_progress_percentage(self) -> float:
        """Get completion percentage"""
        
    def is_complete(self) -> bool:
        """Check if workflow is complete"""
```

#### Workflow Node Functions

**`enhanced_analyze_context`**

```python
async def enhanced_analyze_context(state: AgnosticAgentState) -> AgnosticAgentState:
    """
    Enhanced context analysis with universal framework detection.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with analysis results
        
    Raises:
        AnalysisError: If context analysis fails
    """
```

**`research_enhanced_context`**

```python
async def research_enhanced_context(state: AgnosticAgentState) -> AgnosticAgentState:
    """
    Research integration for enhanced context understanding.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with research results
        
    Raises:
        ResearchError: If research enhancement fails
    """
```

**`multi_agent_coordination`**

```python
async def multi_agent_coordination(state: AgnosticAgentState) -> AgnosticAgentState:
    """
    Multi-agent coordination for comprehensive coverage.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with coordination results
        
    Raises:
        CoordinationError: If agent coordination fails
    """
```

**`template_based_synthesis`**

```python
async def template_based_synthesis(state: AgnosticAgentState) -> AgnosticAgentState:
    """
    Template-based code synthesis.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with generated code
        
    Raises:
        SynthesisError: If code synthesis fails
    """
```

**`universal_file_placement`**

```python
async def universal_file_placement(state: AgnosticAgentState) -> AgnosticAgentState:
    """
    Universal file placement based on framework conventions.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with placement decisions
        
    Raises:
        PlacementError: If file placement fails
    """
```

### Configuration API

#### `SystemConfiguration`

**Purpose**: System-wide configuration management.

```python
class SystemConfiguration:
    """System-wide configuration management"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file: Optional[str]
        self.config: Dict[str, Any]
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        
    def set(self, key: str, value: Any):
        """Set configuration value"""
        
    def reload_config(self):
        """Reload configuration from file"""
        
    def save_config(self):
        """Save current configuration to file"""
        
    def get_framework_config(self, framework: str) -> FrameworkConfig:
        """Get framework-specific configuration"""
        
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
```

#### `FrameworkConfig`

**Purpose**: Framework-specific configuration.

```python
@dataclass
class FrameworkConfig:
    """Framework-specific configuration"""
    
    templates_enabled: bool = True
    validation_level: str = "strict"  # strict, moderate, loose
    async_by_default: bool = False
    include_tests: bool = True
    documentation_style: str = "auto"
    custom_patterns: Dict[str, Any] = field(default_factory=dict)
    
    def validate_config(self) -> ValidationResult:
        """Validate framework configuration"""
```

### Error Handling

#### Exception Hierarchy

```python
class AgnosticAgentError(Exception):
    """Base exception for agnostic agent errors"""
    pass

class DetectionError(AgnosticAgentError):
    """Framework detection errors"""
    pass

class TemplateError(AgnosticAgentError):
    """Template-related errors"""
    pass

class TemplateNotFoundError(TemplateError):
    """Template not found"""
    pass

class TemplateRenderError(TemplateError):
    """Template rendering error"""
    pass

class ResearchError(AgnosticAgentError):
    """Research integration errors"""
    pass

class CoordinationError(AgnosticAgentError):
    """Agent coordination errors"""
    pass

class PlacementError(AgnosticAgentError):
    """File placement errors"""
    pass

class ValidationError(AgnosticAgentError):
    """Validation errors"""
    pass

class SynthesisError(AgnosticAgentError):
    """Code synthesis errors"""
    pass
```

## Usage Examples

### Basic Framework Detection

```python
from scripts.framework_detection import UniversalStackDetector

detector = UniversalStackDetector()
framework_info = detector.detect_framework("/path/to/project")

print(f"Framework: {framework_info.name}")
print(f"Version: {framework_info.version}")
print(f"Language: {framework_info.language}")
print(f"Build System: {framework_info.build_system.name}")
```

### Template-Based Code Generation

```python
from scripts.template_engine import InstructionTemplateEngine

engine = InstructionTemplateEngine()
context = GenerationContext(
    framework=framework_info,
    template_variables={
        'model_name': 'User',
        'fields': [
            {'name': 'email', 'type': 'str'},
            {'name': 'name', 'type': 'str'}
        ]
    }
)

instruction = engine.generate_instruction('entity', context)
result = instruction.execute_instruction("/path/to/target")
```

### Multi-Agent Coordination

```python
from scripts.agent_coordination import AgentCoordinator

coordinator = AgentCoordinator()
result = await coordinator.coordinate_feature_development(
    enhanced_specification, project_context
)

for agent_type, contribution in result.agent_contributions.items():
    print(f"{agent_type}: {contribution.summary}")
```

### Complete Workflow Execution

```python
from scripts.coding_agent.feature_by_request_agent_v3 import create_agnostic_workflow

workflow = create_agnostic_workflow()
result = await workflow.ainvoke({
    "codebase_path": "/path/to/project",
    "feature_specification": specification_text
})

print(f"Generated {len(result['generated_artifacts'])} code artifacts")
print(f"Validation status: {result['validation_complete']}")
```

This API reference provides comprehensive documentation for all major components of the Framework-Agnostic Coding Agent system, enabling developers to understand and extend the system effectively.