# framework_instructions.py
# ========================
# Framework-specific instruction templates for code generation

from abc import ABC, abstractmethod
from typing import Dict, List
from enum import Enum

class FrameworkType(Enum):
    """Supported frameworks"""
    SPRING_BOOT = "spring-boot"
    LARAVEL = "laravel"
    GOLANG = "golang"
    RAILS = "rails"
    ASPNET = "aspnet-core"
    NEXTJS = "nextjs"
    UNKNOWN = "unknown"


class FrameworkInstruction(ABC):
    """
    Base class for framework-specific instructions.
    
    Each framework implementation defines:
    - System prompt with architecture guidelines
    - File patterns and locations
    - Layer mapping (controller, service, etc)
    - Validation rules
    - Best practices enforcement
    """
    
    framework_name: str
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return framework-specific system prompt with architecture guidelines"""
        pass
    
    @abstractmethod
    def get_layer_mapping(self) -> Dict[str, str]:
        """
        Return mapping of logical layers to directory patterns.
        
        Example:
        {
            'controller': 'src/main/java/com/example/controller/',
            'service': 'src/main/java/com/example/service/',
            'repository': 'src/main/java/com/example/repository/',
            'model': 'src/main/java/com/example/model/',
        }
        """
        pass
    
    @abstractmethod
    def get_file_patterns(self) -> Dict[str, str]:
        """
        Return file naming patterns for each layer.
        
        Example:
        {
            'controller': '{name}Controller.java',
            'service': '{name}Service.java',
            'repository': '{name}Repository.java',
            'model': '{name}.java',
        }
        """
        pass
    
    @abstractmethod
    def validate_feature_request(self, feature_request: str) -> bool:
        """Validate if feature request is appropriate for this framework"""
        pass
    
    def detect_from_path(self, codebase_path: str) -> bool:
        """
        Detect if codebase matches this framework.
        Override in subclass with specific detection logic.
        """
        return False
    
    def get_expected_files(self, feature_name: str) -> List[str]:
        """
        Generate list of expected files for a feature.
        
        Returns file paths that agent should create/modify.
        """
        files = []
        layer_mapping = self.get_layer_mapping()
        file_patterns = self.get_file_patterns()
        
        for layer, pattern in file_patterns.items():
            if layer in layer_mapping:
                filename = pattern.format(name=feature_name)
                filepath = layer_mapping[layer] + filename
                files.append(filepath)
        
        return files


# ==============================================================================
# SPRING BOOT (Java) Implementation
# ==============================================================================

class SpringBootInstruction(FrameworkInstruction):
    framework_name = "Spring Boot"
    
    def get_system_prompt(self) -> str:
        return """
SPRING BOOT BEST PRACTICES - CODE GENERATION INSTRUCTIONS
=========================================================

1. ARCHITECTURE LAYERS (Separation of Concerns):
   - Controller Layer: HTTP routing only (@RestController, @GetMapping, @PostMapping, etc)
   - Service Layer: Business logic (@Service, @Transactional)
   - Repository Layer: Data access (@Repository, extends JpaRepository)
   - DTO Layer: API contracts (separate from entities)
   - Model Layer: JPA entities (@Entity, @Table)

2. SOLID PRINCIPLES:
   - Single Responsibility: Each class has ONE purpose only
   - Open/Closed: Extend behavior via services/repositories, don't modify existing
   - Liskov Substitution: Use interface abstractions properly
   - Interface Segregation: Small, focused interfaces
   - Dependency Inversion: Inject dependencies (@Autowired), depend on interfaces

3. FILE ORGANIZATION:
   - Controllers in: src/main/java/com/example/controller/
   - Services in: src/main/java/com/example/service/
   - Repositories in: src/main/java/com/example/repository/
   - DTOs in: src/main/java/com/example/dto/
   - Models in: src/main/java/com/example/model/

4. CODE PATTERNS:
   - Use @RestController for API endpoints
   - Inject service via @Autowired in constructor (preferred) or field
   - Return ResponseEntity<T> for flexible HTTP responses
   - Use DTOs for request/response bodies
   - Entity models only for database (not for API)

5. EXISTING CODEBASE PATTERNS:
   [Analyze for] naming conventions, package structure, import styles, 
   existing service/repository patterns, test structure, Spring Boot version

6. TESTING:
   - Use @WebMvcTest for controller tests
   - Use @SpringBootTest for integration tests
   - Mock service layer in controller tests
   - Keep service logic testable (no static, minimal dependencies)

7. CONFIGURATION:
   - NO new Maven dependencies - use only what's in pom.xml
   - Use application.properties or application.yml for config
   - Rely on Spring Boot auto-configuration (@EnableAutoConfiguration)

IMPLEMENTATION FOCUS:
- Generate production-ready code matching Spring Boot conventions
- Follow existing code style exactly (naming, formatting, imports)
- Ensure code compiles immediately without additional setup
- Each class should have single, clear responsibility
- Use inheritance/interfaces for reusability, not duplication
        """
    
    def get_layer_mapping(self) -> Dict[str, str]:
        return {
            'controller': 'src/main/java/com/example/springboot/controller/',
            'service': 'src/main/java/com/example/springboot/service/',
            'repository': 'src/main/java/com/example/springboot/repository/',
            'dto': 'src/main/java/com/example/springboot/dto/',
            'model': 'src/main/java/com/example/springboot/model/',
        }
    
    def get_file_patterns(self) -> Dict[str, str]:
        return {
            'controller': '{name}Controller.java',
            'service': '{name}Service.java',
            'repository': '{name}Repository.java',
            'dto': '{name}DTO.java',
            'model': '{name}.java',
        }
    
    def validate_feature_request(self, feature_request: str) -> bool:
        """Validate feature is appropriate for Spring Boot REST API"""
        # Accept most features - REST endpoints, data operations, etc
        return len(feature_request) > 10
    
    def detect_from_path(self, codebase_path: str) -> bool:
        """Detect Spring Boot project from path"""
        import os
        indicators = ['pom.xml', 'build.gradle', 'src/main/java', 'application.properties']
        return any(os.path.exists(os.path.join(codebase_path, ind)) for ind in indicators)


# ==============================================================================
# LARAVEL (PHP) Implementation
# ==============================================================================

class LaravelInstruction(FrameworkInstruction):
    framework_name = "Laravel"
    
    def get_system_prompt(self) -> str:
        return """
LARAVEL BEST PRACTICES - CODE GENERATION INSTRUCTIONS
=====================================================

1. ARCHITECTURE LAYERS:
   - Controller: Request handling, delegate to service
   - Service: Business logic, validation, transactions
   - Repository: Data access abstraction (optional but recommended)
   - Model: Eloquent relationships, validations
   - Request: Form validation (extend FormRequest)

2. LARAVEL CONVENTIONS:
   - Use Eloquent ORM for database access
   - Define relationships in models (belongsTo, hasMany, etc)
   - Use $fillable array for mass assignment
   - Leverage validation rules in FormRequest
   - Follow Laravel naming conventions (models singular, tables plural)

3. FILE ORGANIZATION:
   - Controllers: app/Http/Controllers/
   - Models: app/Models/
   - Services: app/Services/
   - Requests: app/Http/Requests/
   - Repositories: app/Repositories/ (optional)

4. CODE PATTERNS:
   - Controllers extend Controller base class
   - Use dependency injection in constructors
   - Type hint parameters for clarity
   - Return JSON responses: response()->json($data, $status)
   - Use appropriate HTTP status codes (200, 201, 400, 404, etc)

5. DATABASE:
   - Define relationships in models (belongsTo, hasMany, hasManyThrough)
   - Use migrations for schema changes
   - Use eager loading to avoid N+1 queries (with(), withCount())
   - Use scopes for common queries

6. TESTING:
   - Use Pest or PHPUnit for tests
   - Mock repositories in controller tests
   - Test service layer with database
   - Use factories for test data

7. EXISTING CODEBASE PATTERNS:
   [Analyze for] naming conventions, model relationships, service patterns,
   existing validation rules, error handling approach

IMPLEMENTATION FOCUS:
- Generate idiomatic Laravel code
- Follow framework conventions strictly
- Use Eloquent relationships properly
- Keep controllers thin, services thick
        """
    
    def get_layer_mapping(self) -> Dict[str, str]:
        return {
            'controller': 'app/Http/Controllers/',
            'service': 'app/Services/',
            'repository': 'app/Repositories/',
            'model': 'app/Models/',
            'request': 'app/Http/Requests/',
        }
    
    def get_file_patterns(self) -> Dict[str, str]:
        return {
            'controller': '{name}Controller.php',
            'service': '{name}Service.php',
            'repository': '{name}Repository.php',
            'model': '{name}.php',
            'request': 'Store{name}Request.php',
        }
    
    def validate_feature_request(self, feature_request: str) -> bool:
        """Validate feature for Laravel"""
        return len(feature_request) > 10
    
    def detect_from_path(self, codebase_path: str) -> bool:
        """Detect Laravel project"""
        import os
        indicators = ['composer.json', 'artisan', 'app/Http/Controllers']
        return any(os.path.exists(os.path.join(codebase_path, ind)) for ind in indicators)


# ==============================================================================
# GOLANG Implementation
# ==============================================================================

class GolangInstruction(FrameworkInstruction):
    framework_name = "Golang"
    
    def get_system_prompt(self) -> str:
        return """
GOLANG BEST PRACTICES - CODE GENERATION INSTRUCTIONS
====================================================

1. PACKAGE ORGANIZATION:
   - cmd/: Entry points only (main package)
   - internal/: Private packages (handler/, service/, repository/, model/)
   - pkg/: Public reusable packages
   - Each package is a directory with appropriate naming

2. INTERFACE-FIRST DESIGN:
   - Define repository interface in repository/ package
   - Define service interface in service/ package
   - Implement interfaces in separate files
   - Use composition over inheritance
   - Small, focused interfaces (good naming with -er suffix)

3. ERROR HANDLING:
   - Return error as last return value: (result, error)
   - Check errors explicitly: if err != nil { return err }
   - Wrap errors with context: fmt.Errorf("operation failed: %w", err)
   - Define custom error types for specific errors

4. IDIOMATIC GO:
   - Use MixedCaps for exported names (exported = Capitalized)
   - Use lowercase for unexported package functions
   - Keep functions small and focused
   - Use defer for resource cleanup
   - Avoid global state, use structs for state

5. CONCURRENCY:
   - Use goroutines with contexts for cancellation
   - Use channels for communication between goroutines
   - Respect context timeouts and cancellation
   - Close channels to signal completion

6. TESTING:
   - Table-driven tests: []struct{ name, args, expected }
   - Mock interfaces for unit testing
   - Use testing.T for test functions
   - Keep tests in *_test.go files
   - Use interfaces to make code testable

7. EXISTING CODEBASE PATTERNS:
   [Analyze for] package structure, interface patterns, error handling,
   concurrency patterns, testing approach

IMPLEMENTATION FOCUS:
- Generate idiomatic, production-ready Go code
- Respect package boundaries and isolation
- Use interfaces for testability
- Follow Go conventions strictly (fmt, naming, error handling)
        """
    
    def get_layer_mapping(self) -> Dict[str, str]:
        return {
            'model': 'internal/model/',
            'repository': 'internal/repository/',
            'service': 'internal/service/',
            'handler': 'internal/handler/',
        }
    
    def get_file_patterns(self) -> Dict[str, str]:
        return {
            'model': '{name}.go',
            'repository': '{name}_repo.go',
            'service': '{name}_service.go',
            'handler': '{name}_handler.go',
        }
    
    def validate_feature_request(self, feature_request: str) -> bool:
        """Validate feature for Go"""
        return len(feature_request) > 10
    
    def detect_from_path(self, codebase_path: str) -> bool:
        """Detect Golang project"""
        import os
        indicators = ['go.mod', 'go.sum', 'cmd/', 'internal/']
        return any(os.path.exists(os.path.join(codebase_path, ind)) for ind in indicators)


# ==============================================================================
# RAILS (Ruby) Implementation
# ==============================================================================

class RailsInstruction(FrameworkInstruction):
    framework_name = "Rails"
    
    def get_system_prompt(self) -> str:
        return """
RAILS BEST PRACTICES - CODE GENERATION INSTRUCTIONS
===================================================

1. RAILS CONVENTIONS:
   - Models: app/models/
   - Controllers: app/controllers/
   - Views: app/views/ (if needed)
   - Services: app/services/
   - Migrations: db/migrate/
   - Follow convention over configuration

2. MODEL PATTERNS:
   - Use ActiveRecord relationships (belongs_to, has_many)
   - Add validations for business rules
   - Use callbacks for automatic operations
   - Define scopes for common queries
   - Use has_secure_password for auth (if needed)

3. CONTROLLER PATTERNS:
   - Follow CRUD actions: index, show, create, update, destroy
   - Use strong parameters (params.require.permit)
   - Extract business logic to services
   - Use appropriate HTTP status codes
   - Render/redirect_to for responses

4. SERVICE OBJECTS:
   - Extract complex business logic to services
   - Services handle multi-step operations
   - Keep controllers thin and focused
   - One service per domain concern

5. DATABASE MIGRATIONS:
   - Create migrations for schema changes
   - Use reversible migrations (add/remove)
   - Name migrations descriptively
   - Include timestamps and associations

6. TESTING:
   - Use RSpec for testing framework
   - Test models, controllers, and services separately
   - Use factories for test data (FactoryBot)
   - Mock external dependencies

7. EXISTING CODEBASE PATTERNS:
   [Analyze for] Rails version, testing framework, service patterns,
   model relationships, validation approaches

IMPLEMENTATION FOCUS:
- Follow Rails conventions strictly
- Generate migrations for schema changes
- Use idiomatic Ruby patterns
- Keep code DRY (Don't Repeat Yourself)
        """
    
    def get_layer_mapping(self) -> Dict[str, str]:
        return {
            'model': 'app/models/',
            'controller': 'app/controllers/',
            'service': 'app/services/',
            'migration': 'db/migrate/',
        }
    
    def get_file_patterns(self) -> Dict[str, str]:
        return {
            'model': '{name}.rb',
            'controller': '{name}s_controller.rb',
            'service': '{name}_service.rb',
            'migration': '[timestamp]_create_{names}.rb',
        }
    
    def validate_feature_request(self, feature_request: str) -> bool:
        """Validate feature for Rails"""
        return len(feature_request) > 10
    
    def detect_from_path(self, codebase_path: str) -> bool:
        """Detect Rails project"""
        import os
        indicators = ['Gemfile', 'config/routes.rb', 'app/controllers']
        return any(os.path.exists(os.path.join(codebase_path, ind)) for ind in indicators)


# ==============================================================================
# ASP.NET Core (C#) Implementation
# ==============================================================================

class AspNetInstruction(FrameworkInstruction):
    framework_name = "ASP.NET Core"
    
    def get_system_prompt(self) -> str:
        return """
ASP.NET CORE BEST PRACTICES - CODE GENERATION INSTRUCTIONS
==========================================================

1. DEPENDENCY INJECTION:
   - Register services in Program.cs (AddScoped/AddTransient/AddSingleton)
   - Inject dependencies via constructor parameters
   - Use interfaces for abstraction (IXyzService, IXyzRepository)
   - Avoid static methods and global state

2. ARCHITECTURE LAYERS:
   - Controllers: HTTP handling only, inject IService
   - Services: Business logic, orchestration
   - Data: DbContext, repositories, Entity Framework
   - Models: Domain entities (EF Core entities)
   - DTOs: API contracts (separate from models)

3. ASYNC/AWAIT:
   - Use async/await throughout codebase
   - Return Task<T> from service/repository methods
   - Use await for database operations
   - Avoid blocking calls (Result, Wait)

4. ENTITY FRAMEWORK CORE:
   - Define DbSet<T> properties in DbContext
   - Use Fluent API for configurations
   - Create migrations for schema changes
   - Use change tracking and SaveChangesAsync

5. VALIDATION:
   - Use data annotations on DTOs ([Required], [StringLength], etc)
   - Custom validators for complex rules
   - Validation filters/middleware
   - ModelState validation in controllers

6. RESPONSE HANDLING:
   - Return appropriate HTTP status codes (200, 201, 400, 404, 500)
   - Use CreatedAtAction for POST responses
   - Use Problem details for error responses
   - Consistent response formats

7. EXISTING CODEBASE PATTERNS:
   [Analyze for] .NET version, EF version, naming conventions,
   existing service patterns, DI setup, error handling

IMPLEMENTATION FOCUS:
- Generate clean, async-first C# code
- Follow C# naming conventions (PascalCase for public)
- Use dependency injection consistently
- Type-safe and null-safe code (nullable reference types)
        """
    
    def get_layer_mapping(self) -> Dict[str, str]:
        return {
            'controller': 'Controllers/',
            'service': 'Services/',
            'repository': 'Data/Repositories/',
            'model': 'Models/',
            'dto': 'DTOs/',
        }
    
    def get_file_patterns(self) -> Dict[str, str]:
        return {
            'controller': '{name}Controller.cs',
            'service': '{name}Service.cs',
            'repository': '{name}Repository.cs',
            'model': '{name}.cs',
            'dto': '{name}Dto.cs',
        }
    
    def validate_feature_request(self, feature_request: str) -> bool:
        """Validate feature for ASP.NET Core"""
        return len(feature_request) > 10
    
    def detect_from_path(self, codebase_path: str) -> bool:
        """Detect ASP.NET Core project"""
        import os
        indicators = ['.csproj', 'Program.cs', 'appsettings.json']
        return any(os.path.exists(os.path.join(codebase_path, ind)) for ind in indicators)


# ==============================================================================
# NEXT.JS (TypeScript) Implementation
# ==============================================================================

class NextJsInstruction(FrameworkInstruction):
    framework_name = "Next.js"
    
    def get_system_prompt(self) -> str:
        return """
NEXTJS BEST PRACTICES - CODE GENERATION INSTRUCTIONS
====================================================

1. API ROUTE STRUCTURE:
   - API routes in app/api/[resource]/route.ts
   - Named exports: GET, POST, PUT, DELETE, PATCH
   - Use NextRequest and NextResponse
   - Handle errors with proper HTTP status codes

2. TYPESCRIPT:
   - Define types in lib/types.ts
   - Use type annotations for function parameters/returns
   - Export types for shared use
   - Use interfaces for API contracts
   - Strict null checking enabled

3. SERVICE LAYER:
   - Business logic in services.ts files
   - Keep routes thin, delegate to services
   - Unit testable service logic
   - Error handling and validation
   - Use async/await for async operations

4. DATABASE:
   - ORM or database client in lib/db.ts
   - Repository pattern for data access
   - Use connection pooling for performance
   - Handle transactions for multi-step operations

5. MIDDLEWARE:
   - Request validation in routes
   - Authentication/authorization handling
   - Error middleware for consistent error responses
   - CORS handling if needed

6. TESTING:
   - Jest + React Testing Library
   - Test services separately from routes
   - Mock database for unit tests
   - Use vitest for fast testing

7. EXISTING CODEBASE PATTERNS:
   [Analyze for] TypeScript setup, API patterns, database client,
   error handling, testing framework

IMPLEMENTATION FOCUS:
- Generate TypeScript-first code (no any types)
- Use async/await consistently
- Type-safe API contracts
- Production-ready error handling
        """
    
    def get_layer_mapping(self) -> Dict[str, str]:
        return {
            'route': 'app/api/[resource]/',
            'service': 'app/api/[resource]/',
            'repository': 'lib/db/',
            'types': 'lib/',
        }
    
    def get_file_patterns(self) -> Dict[str, str]:
        return {
            'route': 'route.ts',
            'service': 'services.ts',
            'repository': '{name}_repo.ts',
            'types': 'types.ts',
        }
    
    def validate_feature_request(self, feature_request: str) -> bool:
        """Validate feature for Next.js"""
        return len(feature_request) > 10
    
    def detect_from_path(self, codebase_path: str) -> bool:
        """Detect Next.js project"""
        import os
        # Check for next.js project markers
        package_json = os.path.join(codebase_path, 'package.json')
        if os.path.exists(package_json):
            try:
                import json
                with open(package_json, 'r') as f:
                    content = json.load(f)
                    return 'next' in content.get('dependencies', {})
            except Exception:
                pass
        return os.path.exists(os.path.join(codebase_path, 'app/')) and \
               os.path.exists(os.path.join(codebase_path, 'next.config.js'))


# ==============================================================================
# Framework Registry & Detection
# ==============================================================================

FRAMEWORK_REGISTRY = {
    FrameworkType.SPRING_BOOT: SpringBootInstruction(),
    FrameworkType.LARAVEL: LaravelInstruction(),
    FrameworkType.GOLANG: GolangInstruction(),
    FrameworkType.RAILS: RailsInstruction(),
    FrameworkType.ASPNET: AspNetInstruction(),
    FrameworkType.NEXTJS: NextJsInstruction(),
}


def detect_framework(codebase_path: str) -> FrameworkType:
    """
    Detect framework from codebase structure.
    
    Args:
        codebase_path: Root path of the codebase
    
    Returns:
        FrameworkType: Detected framework type
    """
    for framework_type, instruction in FRAMEWORK_REGISTRY.items():
        if instruction.detect_from_path(codebase_path):
            return framework_type
    
    return FrameworkType.UNKNOWN


def get_instruction(framework_type: FrameworkType) -> FrameworkInstruction:
    """
    Get framework instruction instance.
    
    Args:
        framework_type: Type of framework
    
    Returns:
        FrameworkInstruction: Framework-specific instruction object
    """
    return FRAMEWORK_REGISTRY.get(framework_type, SpringBootInstruction())
