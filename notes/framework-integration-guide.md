# Framework Integration Guide

## Overview

This guide provides comprehensive instructions for integrating new frameworks into the Agnostic Coding Agent system. Whether you're adding support for a new language, framework, or architectural pattern, this document will walk you through the complete integration process.

## Framework Integration Process

### Phase 1: Framework Analysis and Planning

#### 1.1 Framework Research
Before starting integration, thoroughly research the target framework:

```markdown
**Framework Analysis Checklist**
- [ ] Language and version requirements
- [ ] Project structure conventions
- [ ] Dependency management system
- [ ] Architectural patterns commonly used
- [ ] Code generation patterns
- [ ] Testing frameworks and conventions
- [ ] Documentation standards
- [ ] Community best practices
```

#### 1.2 Integration Planning
Create a comprehensive integration plan:

```python
# Example: FastAPI Integration Plan
integration_plan = {
    "framework": "FastAPI",
    "language": "Python",
    "version_support": ">=0.68.0",
    "components_needed": [
        "FastAPIDetector",
        "FastAPIPlacementRules", 
        "FastAPITemplateSet",
        "FastAPIPatternValidator"
    ],
    "templates_required": [
        "fastapi_router.j2",
        "pydantic_model.j2", 
        "sqlalchemy_schema.j2",
        "pytest_test.j2",
        "dependency_injection.j2"
    ],
    "detection_criteria": [
        "fastapi in requirements.txt/pyproject.toml",
        "FastAPI imports in main files",
        "Router pattern usage",
        "Pydantic model patterns"
    ]
}
```

### Phase 2: Framework Detection Implementation

#### 2.1 Create Framework Detector

Create a framework-specific detector class:

```python
# File: scripts/framework_detection/detectors/fastapi_detector.py

from typing import Optional, List, Dict
from dataclasses import dataclass
from pathlib import Path
import re

from ..base import FrameworkDetector, FrameworkInfo, DependencyInfo

@dataclass 
class FastAPIFrameworkInfo(FrameworkInfo):
    """FastAPI-specific framework information"""
    async_patterns: bool = False
    dependency_injection: bool = False
    database_integration: Optional[str] = None
    authentication_method: Optional[str] = None
    api_versioning: bool = False

class FastAPIDetector(FrameworkDetector):
    """Detects FastAPI framework and analyzes project structure"""
    
    def __init__(self):
        super().__init__()
        self.framework_name = "FastAPI"
        self.language = "Python"
        self.supported_versions = [">=0.68.0"]
    
    def can_detect(self, codebase_path: str) -> bool:
        """Quick check if this is likely a FastAPI project"""
        indicators = [
            self._has_fastapi_dependency(codebase_path),
            self._has_fastapi_imports(codebase_path),
            self._has_fastapi_app_structure(codebase_path)
        ]
        return any(indicators)
    
    def detect(self, codebase_path: str) -> Optional[FastAPIFrameworkInfo]:
        """Comprehensive FastAPI detection and analysis"""
        if not self.can_detect(codebase_path):
            return None
            
        # Analyze project structure
        project_structure = self._analyze_structure(codebase_path)
        
        # Detect dependencies
        dependencies = self._analyze_dependencies(codebase_path)
        
        # Analyze patterns
        patterns = self._analyze_patterns(codebase_path)
        
        # Build framework info
        return FastAPIFrameworkInfo(
            name="FastAPI",
            version=self._detect_version(codebase_path),
            language="Python",
            build_system=self._detect_build_system(codebase_path),
            project_structure=project_structure,
            dependencies=dependencies,
            async_patterns=patterns.get("async", False),
            dependency_injection=patterns.get("dependency_injection", False),
            database_integration=patterns.get("database", None),
            authentication_method=patterns.get("auth", None),
            api_versioning=patterns.get("versioning", False)
        )
    
    def _has_fastapi_dependency(self, path: str) -> bool:
        """Check for FastAPI in dependency files"""
        dependency_files = [
            "requirements.txt",
            "pyproject.toml", 
            "Pipfile",
            "setup.py"
        ]
        
        for file_name in dependency_files:
            file_path = Path(path) / file_name
            if file_path.exists():
                content = file_path.read_text()
                if re.search(r'fastapi[>=<\s]', content, re.IGNORECASE):
                    return True
        return False
    
    def _has_fastapi_imports(self, path: str) -> bool:
        """Check for FastAPI imports in Python files"""
        python_files = list(Path(path).rglob("*.py"))
        
        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                if re.search(r'from\s+fastapi\s+import|import\s+fastapi', content):
                    return True
            except (UnicodeDecodeError, PermissionError):
                continue
                
        return False
    
    def _has_fastapi_app_structure(self, path: str) -> bool:
        """Check for typical FastAPI app structure"""
        structure_indicators = [
            "main.py",
            "app.py", 
            "app/main.py",
            "src/main.py"
        ]
        
        for indicator in structure_indicators:
            file_path = Path(path) / indicator
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    if re.search(r'FastAPI\s*\(', content):
                        return True
                except (UnicodeDecodeError, PermissionError):
                    continue
                    
        return False
    
    def _analyze_patterns(self, path: str) -> Dict[str, any]:
        """Analyze FastAPI-specific patterns"""
        patterns = {}
        python_files = list(Path(path).rglob("*.py"))
        
        for file_path in python_files:
            try:
                content = file_path.read_text()
                
                # Check for async patterns
                if re.search(r'async\s+def', content):
                    patterns["async"] = True
                
                # Check for dependency injection
                if re.search(r'Depends\s*\(', content):
                    patterns["dependency_injection"] = True
                
                # Check for database integration
                if re.search(r'sqlalchemy|tortoise|databases', content, re.IGNORECASE):
                    patterns["database"] = "SQLAlchemy"
                elif re.search(r'mongodb|motor', content, re.IGNORECASE):
                    patterns["database"] = "MongoDB"
                
                # Check for authentication
                if re.search(r'HTTPBearer|OAuth2|JWT', content):
                    patterns["auth"] = "JWT/OAuth2"
                
                # Check for API versioning
                if re.search(r'router.*prefix.*v[0-9]', content):
                    patterns["versioning"] = True
                    
            except (UnicodeDecodeError, PermissionError):
                continue
        
        return patterns
```

#### 2.2 Register Framework Detector

Add the detector to the main detection system:

```python
# File: scripts/framework_detection/detector_registry.py

class DetectorRegistry:
    def __init__(self):
        self.detectors = {
            'java': [SpringBootDetector(), QuarkusDetector(), MicronautDetector()],
            'python': [FastAPIDetector(), DjangoDetector(), FlaskDetector()],
            'javascript': [ExpressDetector(), NestJSDetector(), KoaDetector()],
            'typescript': [AngularDetector(), ReactDetector(), VueDetector()]
        }
    
    def register_detector(self, language: str, detector: FrameworkDetector):
        """Register a new framework detector"""
        if language not in self.detectors:
            self.detectors[language] = []
        self.detectors[language].append(detector)
    
    def detect_framework(self, codebase_path: str) -> Optional[FrameworkInfo]:
        """Detect framework using all registered detectors"""
        primary_language = self._detect_primary_language(codebase_path)
        
        if primary_language in self.detectors:
            for detector in self.detectors[primary_language]:
                result = detector.detect(codebase_path)
                if result:
                    return result
                    
        return self._fallback_detection(codebase_path)
```

### Phase 3: Template System Integration

#### 3.1 Create Framework Templates

Develop comprehensive templates for the new framework:

```jinja2
{# File: templates/fastapi/router.j2 #}
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import {{ model_name }}, {{ model_name }}Create, {{ model_name }}Update
from ..services import {{ model_name.lower() }}_service
from ..models import {{ model_name }} as {{ model_name }}Model

router = APIRouter(
    prefix="/{{ endpoint_prefix }}",
    tags=["{{ tags|join('", "') }}"]
)

@router.get("/", response_model=List[{{ model_name }}])
async def get_{{ model_name.lower() }}s(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[{{ model_name }}]:
    """
    Retrieve {{ model_name.lower() }}s with pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    {{ model_name.lower() }}s = {{ model_name.lower() }}_service.get_{{ model_name.lower() }}s(
        db=db, skip=skip, limit=limit
    )
    return {{ model_name.lower() }}s

@router.get("/{{{ model_name.lower() }}_id}", response_model={{ model_name }})
async def get_{{ model_name.lower() }}(
    {{ model_name.lower() }}_id: int,
    db: Session = Depends(get_db)
) -> {{ model_name }}:
    """
    Get a specific {{ model_name.lower() }} by ID.
    """
    {{ model_name.lower() }} = {{ model_name.lower() }}_service.get_{{ model_name.lower() }}(
        db=db, {{ model_name.lower() }}_id={{ model_name.lower() }}_id
    )
    if not {{ model_name.lower() }}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{{ model_name }} not found"
        )
    return {{ model_name.lower() }}

@router.post("/", response_model={{ model_name }}, status_code=status.HTTP_201_CREATED)
async def create_{{ model_name.lower() }}(
    {{ model_name.lower() }}_data: {{ model_name }}Create,
    db: Session = Depends(get_db)
) -> {{ model_name }}:
    """
    Create a new {{ model_name.lower() }}.
    """
    return {{ model_name.lower() }}_service.create_{{ model_name.lower() }}(
        db=db, {{ model_name.lower() }}_data={{ model_name.lower() }}_data
    )

@router.put("/{{{ model_name.lower() }}_id}", response_model={{ model_name }})
async def update_{{ model_name.lower() }}(
    {{ model_name.lower() }}_id: int,
    {{ model_name.lower() }}_data: {{ model_name }}Update,
    db: Session = Depends(get_db)
) -> {{ model_name }}:
    """
    Update an existing {{ model_name.lower() }}.
    """
    {{ model_name.lower() }} = {{ model_name.lower() }}_service.update_{{ model_name.lower() }}(
        db=db, 
        {{ model_name.lower() }}_id={{ model_name.lower() }}_id,
        {{ model_name.lower() }}_data={{ model_name.lower() }}_data
    )
    if not {{ model_name.lower() }}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{{ model_name }} not found"
        )
    return {{ model_name.lower() }}

@router.delete("/{{{ model_name.lower() }}_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{{ model_name.lower() }}(
    {{ model_name.lower() }}_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a {{ model_name.lower() }}.
    """
    success = {{ model_name.lower() }}_service.delete_{{ model_name.lower() }}(
        db=db, {{ model_name.lower() }}_id={{ model_name.lower() }}_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{{ model_name }} not found"
        )
```

```jinja2
{# File: templates/fastapi/pydantic_model.j2 #}
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
{% if email_field %}from pydantic import EmailStr{% endif %}

class {{ model_name }}Base(BaseModel):
    """Base {{ model_name }} schema with common attributes"""
    {% for field in fields %}
    {% if field.required %}
    {{ field.name }}: {{ field.type }} = Field(
        {% if field.description %}description="{{ field.description }}"{% endif %}
        {% if field.example %}, example={{ field.example }}{% endif %}
        {% if field.constraints %}, {{ field.constraints }}{% endif %}
    )
    {% else %}
    {{ field.name }}: Optional[{{ field.type }}] = Field(
        None,
        {% if field.description %}description="{{ field.description }}"{% endif %}
        {% if field.example %}, example={{ field.example }}{% endif %}
        {% if field.constraints %}, {{ field.constraints }}{% endif %}
    )
    {% endif %}
    {% endfor %}

    {% for validation in validations %}
    @validator('{{ validation.field }}')
    def validate_{{ validation.field }}(cls, v):
        """{{ validation.description }}"""
        {{ validation.logic }}
        return v
    {% endfor %}

class {{ model_name }}Create({{ model_name }}Base):
    """Schema for creating a new {{ model_name }}"""
    {% for field in create_only_fields %}
    {{ field.name }}: {{ field.type }} = Field({{ field.default }})
    {% endfor %}

class {{ model_name }}Update({{ model_name }}Base):
    """Schema for updating an existing {{ model_name }}"""
    {% for field in fields %}
    {{ field.name }}: Optional[{{ field.type }}] = None
    {% endfor %}

class {{ model_name }}InDBBase({{ model_name }}Base):
    """Base schema for database representation"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class {{ model_name }}({{ model_name }}InDBBase):
    """Schema for {{ model_name }} in responses"""
    pass

class {{ model_name }}InDB({{ model_name }}InDBBase):
    """Schema for {{ model_name }} as stored in database"""
    pass
```

#### 3.2 Create Template Registry

Register templates with the template system:

```python
# File: scripts/template_engine/template_registry.py

class TemplateRegistry:
    def __init__(self):
        self.templates = {}
        self._register_default_templates()
    
    def register_framework_templates(self, framework: str, templates: Dict[str, str]):
        """Register templates for a specific framework"""
        if framework not in self.templates:
            self.templates[framework] = {}
        self.templates[framework].update(templates)
    
    def register_fastapi_templates(self):
        """Register FastAPI-specific templates"""
        fastapi_templates = {
            'router': 'fastapi/router.j2',
            'pydantic_model': 'fastapi/pydantic_model.j2',
            'sqlalchemy_schema': 'fastapi/sqlalchemy_schema.j2',
            'service': 'fastapi/service.j2',
            'test': 'fastapi/test.j2',
            'dependency': 'fastapi/dependency.j2',
            'main_app': 'fastapi/main_app.j2'
        }
        self.register_framework_templates('fastapi', fastapi_templates)
    
    def get_template(self, framework: str, template_type: str) -> Optional[str]:
        """Get template path for framework and type"""
        return self.templates.get(framework, {}).get(template_type)
```

### Phase 4: File Placement Rules

#### 4.1 Create Placement Rules

Implement framework-specific file placement logic:

```python
# File: scripts/file_placement/rules/fastapi_rules.py

from typing import Dict, List
from pathlib import Path

from ..base import PlacementRules, PlacementDecision, CodeArtifact

class FastAPIPlacementRules(PlacementRules):
    """FastAPI-specific file placement rules"""
    
    def __init__(self):
        self.structure_patterns = {
            'standard': {
                'app_root': 'app',
                'routers': 'app/routers',
                'schemas': 'app/schemas', 
                'models': 'app/models',
                'services': 'app/services',
                'database': 'app/database.py',
                'dependencies': 'app/dependencies.py',
                'main': 'app/main.py'
            },
            'src_based': {
                'app_root': 'src',
                'routers': 'src/routers',
                'schemas': 'src/schemas',
                'models': 'src/models', 
                'services': 'src/services',
                'database': 'src/database.py',
                'dependencies': 'src/dependencies.py',
                'main': 'src/main.py'
            }
        }
    
    def determine_placement(self, artifact: CodeArtifact, context) -> PlacementDecision:
        """Determine optimal file placement for FastAPI artifacts"""
        
        # Detect existing structure pattern
        structure = self._detect_structure_pattern(context.codebase_path)
        
        # Get placement rules for detected structure
        placement_map = self.structure_patterns[structure]
        
        # Determine specific placement based on artifact type
        placement_info = self._get_placement_for_artifact(artifact, placement_map)
        
        return PlacementDecision(
            target_directory=placement_info['directory'],
            filename=placement_info['filename'],
            imports=self._calculate_imports(artifact, placement_info, context),
            package_adjustments=[]
        )
    
    def _detect_structure_pattern(self, codebase_path: str) -> str:
        """Detect which structure pattern the project uses"""
        path = Path(codebase_path)
        
        # Check for app/ directory structure
        if (path / 'app').exists() and (path / 'app' / 'main.py').exists():
            return 'standard'
        
        # Check for src/ directory structure  
        if (path / 'src').exists() and (path / 'src' / 'main.py').exists():
            return 'src_based'
        
        # Default to standard structure
        return 'standard'
    
    def _get_placement_for_artifact(self, artifact: CodeArtifact, 
                                   placement_map: Dict[str, str]) -> Dict[str, str]:
        """Get specific placement for artifact type"""
        
        artifact_placement = {
            'router': {
                'directory': placement_map['routers'],
                'filename': f"{artifact.name.lower()}_router.py"
            },
            'pydantic_model': {
                'directory': placement_map['schemas'], 
                'filename': f"{artifact.name.lower()}_schema.py"
            },
            'sqlalchemy_model': {
                'directory': placement_map['models'],
                'filename': f"{artifact.name.lower()}_model.py"  
            },
            'service': {
                'directory': placement_map['services'],
                'filename': f"{artifact.name.lower()}_service.py"
            },
            'test': {
                'directory': 'tests',
                'filename': f"test_{artifact.name.lower()}.py"
            }
        }
        
        return artifact_placement.get(
            artifact.type, 
            {
                'directory': placement_map['app_root'],
                'filename': f"{artifact.name.lower()}.py"
            }
        )
    
    def _calculate_imports(self, artifact: CodeArtifact, 
                          placement_info: Dict[str, str], context) -> List[str]:
        """Calculate required imports for the artifact"""
        imports = []
        
        # Add framework-specific imports
        if artifact.type == 'router':
            imports.extend([
                'from fastapi import APIRouter, Depends, HTTPException',
                'from typing import List',
                'from sqlalchemy.orm import Session'
            ])
        elif artifact.type == 'pydantic_model':
            imports.extend([
                'from pydantic import BaseModel, Field',
                'from typing import Optional',
                'from datetime import datetime'
            ])
        elif artifact.type == 'service':
            imports.extend([
                'from sqlalchemy.orm import Session',
                'from typing import Optional, List'
            ])
        
        # Add project-specific imports based on dependencies
        imports.extend(self._calculate_project_imports(artifact, context))
        
        return imports
```

### Phase 5: Pattern Validation

#### 5.1 Create Framework Validator

Implement validation for framework-specific patterns:

```python
# File: scripts/validation/validators/fastapi_validator.py

from typing import List, Dict
import ast
import re

from ..base import PatternValidator, ValidationResult, ValidationIssue

class FastAPIPatternValidator(PatternValidator):
    """Validates FastAPI-specific code patterns and best practices"""
    
    def __init__(self):
        self.required_patterns = [
            'async_function_usage',
            'proper_dependency_injection',
            'response_model_definition',
            'http_exception_usage',
            'proper_status_codes'
        ]
        
        self.security_patterns = [
            'input_validation',
            'sql_injection_prevention', 
            'authentication_middleware',
            'cors_configuration'
        ]
    
    def validate(self, code_content: str, artifact_type: str) -> ValidationResult:
        """Validate FastAPI code patterns"""
        issues = []
        
        # Parse code for analysis
        try:
            tree = ast.parse(code_content)
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    severity='error',
                    message=f"Syntax error: {e.msg}",
                    line_number=e.lineno
                )]
            )
        
        # Validate artifact-specific patterns
        if artifact_type == 'router':
            issues.extend(self._validate_router_patterns(tree, code_content))
        elif artifact_type == 'pydantic_model':
            issues.extend(self._validate_pydantic_patterns(tree, code_content))
        elif artifact_type == 'service':
            issues.extend(self._validate_service_patterns(tree, code_content))
        
        # Validate common patterns
        issues.extend(self._validate_common_patterns(tree, code_content))
        
        # Validate security patterns
        issues.extend(self._validate_security_patterns(tree, code_content))
        
        return ValidationResult(
            is_valid=len([i for i in issues if i.severity == 'error']) == 0,
            issues=issues
        )
    
    def _validate_router_patterns(self, tree: ast.AST, code: str) -> List[ValidationIssue]:
        """Validate FastAPI router patterns"""
        issues = []
        
        # Check for async function definitions
        async_functions = [node for node in ast.walk(tree) 
                          if isinstance(node, ast.AsyncFunctionDef)]
        
        if not async_functions:
            issues.append(ValidationIssue(
                severity='warning',
                message="Consider using async functions for better performance",
                pattern='async_function_usage'
            ))
        
        # Check for proper HTTP exception usage
        if 'HTTPException' not in code:
            issues.append(ValidationIssue(
                severity='warning', 
                message="Consider adding proper error handling with HTTPException",
                pattern='http_exception_usage'
            ))
        
        # Check for response model definitions
        decorators = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                decorators.extend([d.attr for d in node.decorator_list 
                                 if hasattr(d, 'attr')])
        
        if 'response_model' not in str(decorators):
            issues.append(ValidationIssue(
                severity='info',
                message="Consider adding response_model for better API documentation",
                pattern='response_model_definition'
            ))
        
        return issues
    
    def _validate_pydantic_patterns(self, tree: ast.AST, code: str) -> List[ValidationIssue]:
        """Validate Pydantic model patterns"""
        issues = []
        
        # Check for field validation
        if 'Field(' not in code:
            issues.append(ValidationIssue(
                severity='info',
                message="Consider using Field() for better validation and documentation",
                pattern='field_usage'
            ))
        
        # Check for proper typing
        if 'Optional[' not in code and 'Union[' not in code:
            issues.append(ValidationIssue(
                severity='warning',
                message="Consider using proper type hints with Optional for nullable fields",
                pattern='type_hints'
            ))
        
        return issues
    
    def _validate_security_patterns(self, tree: ast.AST, code: str) -> List[ValidationIssue]:
        """Validate security patterns"""
        issues = []
        
        # Check for input validation
        if 'validator' not in code and artifact_type in ['pydantic_model', 'router']:
            issues.append(ValidationIssue(
                severity='warning',
                message="Consider adding input validation for security",
                pattern='input_validation'
            ))
        
        # Check for SQL injection prevention (if database queries present)
        if 'execute(' in code and 'f"' in code:
            issues.append(ValidationIssue(
                severity='error',
                message="Potential SQL injection vulnerability - use parameterized queries",
                pattern='sql_injection_prevention'
            ))
        
        return issues
```

### Phase 6: Integration Testing

#### 6.1 Create Integration Tests

Develop comprehensive tests for the new framework integration:

```python
# File: tests/integration/test_fastapi_integration.py

import pytest
import tempfile
import shutil
from pathlib import Path

from scripts.framework_detection.detectors.fastapi_detector import FastAPIDetector
from scripts.template_engine.fastapi_engine import FastAPITemplateEngine
from scripts.file_placement.rules.fastapi_rules import FastAPIPlacementRules

class TestFastAPIIntegration:
    """Integration tests for FastAPI framework support"""
    
    @pytest.fixture
    def fastapi_project(self):
        """Create a temporary FastAPI project for testing"""
        temp_dir = tempfile.mkdtemp()
        
        # Create FastAPI project structure
        project_path = Path(temp_dir) / "test_fastapi_project"
        project_path.mkdir()
        
        # Create basic FastAPI files
        (project_path / "requirements.txt").write_text("fastapi>=0.68.0\nuvicorn[standard]")
        
        app_dir = project_path / "app"
        app_dir.mkdir()
        
        (app_dir / "main.py").write_text("""
from fastapi import FastAPI
from .routers import users

app = FastAPI()
app.include_router(users.router)
""")
        
        routers_dir = app_dir / "routers"
        routers_dir.mkdir()
        (routers_dir / "__init__.py").write_text("")
        
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_fastapi_detection(self, fastapi_project):
        """Test FastAPI framework detection"""
        detector = FastAPIDetector()
        
        # Test detection capability
        assert detector.can_detect(str(fastapi_project))
        
        # Test detailed detection
        framework_info = detector.detect(str(fastapi_project))
        assert framework_info is not None
        assert framework_info.name == "FastAPI"
        assert framework_info.language == "Python"
    
    def test_template_generation(self, fastapi_project):
        """Test FastAPI template generation"""
        engine = FastAPITemplateEngine()
        
        context = {
            'model_name': 'User',
            'endpoint_prefix': 'users',
            'fields': [
                {'name': 'email', 'type': 'str', 'required': True},
                {'name': 'name', 'type': 'str', 'required': True},
                {'name': 'age', 'type': 'int', 'required': False}
            ]
        }
        
        # Test router generation
        router_code = engine.generate_router(context)
        assert 'APIRouter' in router_code
        assert '/users' in router_code
        assert 'async def' in router_code
        
        # Test Pydantic model generation
        model_code = engine.generate_pydantic_model(context)
        assert 'BaseModel' in model_code
        assert 'UserCreate' in model_code
        assert 'UserUpdate' in model_code
    
    def test_file_placement(self, fastapi_project):
        """Test FastAPI file placement"""
        placement_rules = FastAPIPlacementRules()
        
        from scripts.file_placement.base import CodeArtifact, ProjectContext
        
        context = ProjectContext(
            codebase_path=str(fastapi_project),
            framework_info={'name': 'FastAPI'}
        )
        
        # Test router placement
        router_artifact = CodeArtifact(name='User', type='router', content='...')
        placement = placement_rules.determine_placement(router_artifact, context)
        
        assert 'app/routers' in placement.target_directory
        assert placement.filename == 'user_router.py'
    
    def test_end_to_end_generation(self, fastapi_project):
        """Test complete end-to-end FastAPI code generation"""
        # This would test the complete workflow:
        # 1. Framework detection
        # 2. Specification parsing  
        # 3. Template selection
        # 4. Code generation
        # 5. File placement
        # 6. Validation
        
        # Implementation would use the actual agent workflow
        pass
```

#### 6.2 Performance Testing

```python
# File: tests/performance/test_fastapi_performance.py

import time
import pytest
from scripts.framework_detection.detectors.fastapi_detector import FastAPIDetector

class TestFastAPIPerformance:
    """Performance tests for FastAPI integration"""
    
    def test_detection_performance(self, large_fastapi_project):
        """Test framework detection performance on large projects"""
        detector = FastAPIDetector()
        
        start_time = time.time()
        framework_info = detector.detect(str(large_fastapi_project))
        detection_time = time.time() - start_time
        
        # Should complete detection within 5 seconds for large projects
        assert detection_time < 5.0
        assert framework_info is not None
    
    def test_template_generation_performance(self):
        """Test template generation performance"""
        engine = FastAPITemplateEngine()
        
        # Generate complex model with many fields
        context = {
            'model_name': 'ComplexModel',
            'fields': [{'name': f'field_{i}', 'type': 'str'} for i in range(100)]
        }
        
        start_time = time.time()
        code = engine.generate_pydantic_model(context)
        generation_time = time.time() - start_time
        
        # Should complete generation within 1 second
        assert generation_time < 1.0
        assert len(code) > 1000  # Ensure substantial code was generated
```

### Phase 7: Documentation

#### 7.1 Framework-Specific Documentation

Create comprehensive documentation for the new framework:

```markdown
# FastAPI Integration Guide

## Overview
The FastAPI integration provides comprehensive support for developing FastAPI applications with the Agnostic Coding Agent. This integration automatically detects FastAPI projects and generates framework-appropriate code following FastAPI best practices.

## Supported Features
- ✅ Automatic FastAPI project detection
- ✅ Async/await pattern support
- ✅ Pydantic model generation
- ✅ SQLAlchemy integration
- ✅ Dependency injection patterns
- ✅ Router and endpoint generation
- ✅ Authentication middleware
- ✅ API documentation generation

## Detection Criteria
The FastAPI detector identifies projects based on:
- FastAPI dependency in requirements.txt/pyproject.toml
- FastAPI imports in Python files
- FastAPI app instantiation patterns
- Typical FastAPI project structure

## Generated Code Patterns

### Router Generation
Generates FastAPI routers with:
- Async function definitions
- Proper dependency injection
- HTTP exception handling
- Response model definitions
- OpenAPI documentation

### Model Generation
Creates Pydantic models with:
- Base model inheritance
- Create/Update variations
- Field validation
- Type hints
- API documentation

### Service Layer
Generates service classes with:
- Database session handling
- Business logic separation
- Error handling
- Type annotations

## Configuration Options
```yaml
fastapi:
  async_by_default: true
  include_openapi_docs: true
  authentication_method: "jwt"
  database_integration: "sqlalchemy"
  testing_framework: "pytest"
```

## Best Practices Enforced
- Async/await usage for I/O operations
- Proper dependency injection
- Input validation with Pydantic
- HTTP status code usage
- Error handling with HTTPException
- API documentation with docstrings
```

#### 7.2 Update Main Documentation

Update the main documentation to include the new framework:

```python
# File: scripts/documentation/update_docs.py

def update_framework_support_docs():
    """Update documentation with new framework support"""
    
    supported_frameworks = {
        'java': ['Spring Boot', 'Quarkus', 'Micronaut'],
        'python': ['FastAPI', 'Django', 'Flask'],  # Added FastAPI
        'javascript': ['Express.js', 'Nest.js', 'Koa'],
        'typescript': ['Angular', 'React', 'Vue']
    }
    
    # Update README.md
    # Update architecture documentation
    # Update API reference
    # Update examples
```

### Phase 8: Deployment and Testing

#### 8.1 Integration Validation

```bash
#!/bin/bash
# File: scripts/validation/validate_fastapi_integration.sh

echo "Validating FastAPI integration..."

# Test framework detection
python -m pytest tests/integration/test_fastapi_detection.py -v

# Test template generation
python -m pytest tests/integration/test_fastapi_templates.py -v

# Test file placement
python -m pytest tests/integration/test_fastapi_placement.py -v

# Test end-to-end workflow
python -m pytest tests/integration/test_fastapi_e2e.py -v

# Performance tests
python -m pytest tests/performance/test_fastapi_performance.py -v

echo "FastAPI integration validation complete!"
```

#### 8.2 Sample Project Testing

Test the integration with real FastAPI projects:

```bash
# Test with existing FastAPI projects
python scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path /path/to/fastapi/project \
  --feature-request-spec dataset/spec/fastapi-user-management.md

# Verify generated code
python scripts/validation/verify_generated_code.py \
  --project-path /path/to/fastapi/project \
  --framework fastapi
```

## Advanced Integration Patterns

### Custom Framework Detection

For frameworks that require special detection logic:

```python
class CustomFrameworkDetector(FrameworkDetector):
    """Template for custom framework detection"""
    
    def detect(self, codebase_path: str) -> Optional[FrameworkInfo]:
        # Implement custom detection logic
        # Consider:
        # - Configuration files
        # - Import patterns  
        # - Project structure
        # - Dependency analysis
        # - Code patterns
        pass
```

### Template Inheritance

Create template hierarchies for related frameworks:

```python
class BaseWebFrameworkTemplates:
    """Base templates for web frameworks"""
    
    def get_base_templates(self):
        return {
            'controller_base': 'web/controller_base.j2',
            'model_base': 'web/model_base.j2',
            'service_base': 'web/service_base.j2'
        }

class FastAPITemplates(BaseWebFrameworkTemplates):
    """FastAPI-specific templates extending base web templates"""
    
    def get_templates(self):
        base_templates = self.get_base_templates()
        fastapi_templates = {
            'router': 'fastapi/router.j2',
            'pydantic_model': 'fastapi/pydantic_model.j2'
        }
        return {**base_templates, **fastapi_templates}
```

## Integration Checklist

Use this checklist when adding new framework support:

- [ ] **Research Phase Complete**
  - [ ] Framework patterns documented
  - [ ] Best practices identified
  - [ ] Community conventions understood

- [ ] **Detection Implementation**
  - [ ] Framework detector created
  - [ ] Detection logic tested
  - [ ] Performance validated

- [ ] **Template Development**
  - [ ] All necessary templates created
  - [ ] Templates follow framework conventions
  - [ ] Template variables documented

- [ ] **File Placement Rules**
  - [ ] Placement logic implemented
  - [ ] Framework structure respected
  - [ ] Import handling correct

- [ ] **Validation System**
  - [ ] Pattern validator created
  - [ ] Security patterns validated
  - [ ] Best practices enforced

- [ ] **Testing Complete**
  - [ ] Unit tests written
  - [ ] Integration tests passing
  - [ ] Performance tests satisfied
  - [ ] Real project testing done

- [ ] **Documentation Updated**
  - [ ] Framework guide written
  - [ ] API documentation updated
  - [ ] Examples provided
  - [ ] Main docs updated

- [ ] **Integration Deployed**
  - [ ] Framework registered in system
  - [ ] CI/CD updated
  - [ ] Deployment tested

Following this comprehensive integration guide ensures that new framework support is added systematically, maintains high quality, and integrates seamlessly with the existing agnostic agent system.