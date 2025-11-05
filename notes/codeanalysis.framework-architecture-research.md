# Framework Architecture Research: Best Practices for Code Generation

## Executive Summary

Research menunjukkan bahwa setiap framework memiliki **architectural patterns yang berbeda**, namun semua mengikuti prinsip **separation of concerns** dan **layered architecture**. Agent V3 perlu di-customize dengan framework-specific instructions untuk generate best practice code.

---

## 1. SPRING BOOT (Java) - Layered Architecture Pattern

### Standard Structure
```
src/
├── main/java/com/example/
│   ├── controller/        # HTTP Layer
│   ├── service/           # Business Logic Layer
│   ├── repository/        # Data Access Layer
│   ├── model/             # Domain Models
│   ├── dto/               # Data Transfer Objects
│   └── exception/         # Exception Handling
└── test/java/
```

### Core Principles
- **Controller Layer**: Only HTTP routing, request/response mapping
- **Service Layer**: Business logic, validation, transactions
- **Repository Layer**: Database/data access abstractions
- **DTO Layer**: API contracts (request/response schemas)
- **Model Layer**: Domain entities

### Best Practices Pattern
```java
// 1. DTO for API Contract
@Data
public class OrderDTO {
    private String item;
    private int quantity;
    private double price;
}

// 2. Model for Business Logic
@Entity
public class Order {
    @Id
    private Long id;
    private String item;
    private int quantity;
    private double price;
}

// 3. Repository Interface
public interface OrderRepository extends JpaRepository<Order, Long> {}

// 4. Service Layer
@Service
public class OrderService {
    @Autowired
    private OrderRepository repository;
    
    public Order createOrder(OrderDTO dto) {
        Order order = new Order();
        // Business logic here
        return repository.save(order);
    }
}

// 5. Controller (HTTP Layer Only)
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    @Autowired
    private OrderService service;
    
    @PostMapping
    public ResponseEntity<OrderDTO> create(@RequestBody OrderDTO dto) {
        Order created = service.createOrder(dto);
        return ResponseEntity.created(uri).body(convert(created));
    }
}
```

### Spring Boot Instruction Template
```
SPRING BOOT CODE GENERATION INSTRUCTIONS:

1. ARCHITECTURE SEPARATION:
   - Controller: Only HTTP routing (@RestController, @GetMapping, etc)
   - Service: Business logic (@Service, @Transactional)
   - Repository: Data access (@Repository, extends JpaRepository)
   - DTO: API contracts (separate from entity models)
   - Model: JPA entities (@Entity, @Table)

2. SOLID PRINCIPLES:
   - Single Responsibility: Each class one purpose
   - Open/Closed: Extend service/repository, don't modify
   - Liskov Substitution: Use interface abstractions
   - Interface Segregation: Small focused interfaces
   - Dependency Inversion: Inject dependencies (@Autowired)

3. FILE STRUCTURE:
   - Create new files in appropriate packages
   - Use convention: controller/, service/, repository/, dto/, model/
   - Import only what's needed, no wildcard imports

4. EXISTING PATTERNS:
   [Analyze codebase for patterns, naming conventions, import styles]

5. TESTING:
   - Write testable code: dependency injection, pure functions
   - Service layer should be testable without database
   - Use @WebMvcTest for controller tests

6. CONFIGURATION:
   - No new dependencies (use what's in pom.xml)
   - Properties in application.properties/yml
   - Use Spring Boot auto-configuration (@EnableAutoConfiguration)

OUTPUT: Generate edit_file and write_file calls to:
   1. Create DTO in /dto/
   2. Create Service in /service/
   3. Create/Update Repository in /repository/
   4. Create/Update Controller in /controller/
   5. Use models from /model/ or /entity/
```

---

## 2. LARAVEL (PHP) - MVC + Repository Pattern

### Standard Structure
```
app/
├── Http/
│   ├── Controllers/       # Controllers
│   └── Requests/          # Form Requests (Validation)
├── Models/                # Eloquent Models
├── Repositories/          # Repository Pattern
├── Services/              # Business Logic
├── Exceptions/            # Custom Exceptions
└── Traits/                # Reusable traits
database/
├── migrations/            # Database schema
└── seeders/               # Data seeders
```

### Core Principles
- **Controllers**: Request handling, delegate to services
- **Models**: Eloquent ORM, relationships
- **Repositories**: Data access abstraction
- **Services**: Business logic, complex operations
- **Requests**: Validation rules (FormRequest)

### Best Practices Pattern
```php
// 1. Form Request (Validation)
class StoreOrderRequest extends FormRequest {
    public function rules() {
        return [
            'item' => 'required|string|max:255',
            'quantity' => 'required|integer|min:1',
            'price' => 'required|numeric|min:0',
        ];
    }
}

// 2. Model with Relationships
class Order extends Model {
    use HasFactory;
    protected $fillable = ['item', 'quantity', 'price'];
    
    public function user() {
        return $this->belongsTo(User::class);
    }
}

// 3. Repository Interface
interface OrderRepositoryInterface {
    public function getAll();
    public function create(array $data);
    public function update($id, array $data);
}

// 4. Repository Implementation
class OrderRepository implements OrderRepositoryInterface {
    public function __construct(Order $model) {
        $this->model = $model;
    }
    
    public function getAll() {
        return $this->model->all();
    }
    
    public function create(array $data) {
        return $this->model->create($data);
    }
}

// 5. Service Layer
class OrderService {
    public function __construct(private OrderRepository $repo) {}
    
    public function createOrder(array $data) {
        // Business logic
        return $this->repo->create($data);
    }
}

// 6. Controller (HTTP Layer)
class OrderController extends Controller {
    public function __construct(private OrderService $service) {}
    
    public function store(StoreOrderRequest $request) {
        $order = $this->service->createOrder($request->validated());
        return response()->json($order, 201);
    }
}
```

### Laravel Instruction Template
```
LARAVEL CODE GENERATION INSTRUCTIONS:

1. ARCHITECTURE PATTERN:
   - Controller: Request/response handling, delegate to service
   - Service: Business logic, validation, transactions
   - Repository: Data access layer abstraction
   - Model: Eloquent relationships, casts, accessors
   - Request: Validation rules (extend FormRequest)

2. LARAVEL CONVENTIONS:
   - Controllers in app/Http/Controllers/
   - Models in app/Models/
   - Services in app/Services/
   - Repositories in app/Repositories/
   - Use dependency injection in constructors
   - Type hint parameters for clarity

3. ELOQUENT PATTERNS:
   - Define relationships (belongsTo, hasMany, etc)
   - Use $fillable for mass assignment
   - Use accessors/mutators for transformations
   - Eager load relations to avoid N+1 queries

4. TESTING:
   - Use Pest or PHPUnit test structure
   - Mock repositories in controller tests
   - Test service layer with database

5. API STANDARDS:
   - Return JSON responses: response()->json($data, $status)
   - Use appropriate HTTP status codes (200, 201, 400, 404, etc)
   - Include error messages for failures

OUTPUT: Generate files:
   1. app/Http/Requests/StoreXyzRequest.php
   2. app/Repositories/XyzRepository.php
   3. app/Services/XyzService.php
   4. app/Models/Xyz.php (if new)
   5. app/Http/Controllers/XyzController.php (update)
```

---

## 3. GOLANG - Package-Based Architecture

### Standard Structure
```
project/
├── cmd/                   # Entry points
│   └── app/
│       └── main.go
├── internal/              # Private packages
│   ├── handler/           # HTTP handlers
│   ├── service/           # Business logic
│   ├── repository/        # Data access
│   ├── model/             # Domain models
│   └── config/            # Configuration
├── pkg/                   # Public reusable packages
├── migrations/            # Database migrations
└── tests/                 # Integration tests
```

### Core Principles
- **Package-based**: Everything is a package
- **Interfaces**: Define behavior, not implementation
- **Composition**: Embed types, not inheritance
- **Error handling**: Explicit error returns
- **Testing**: Table-driven tests

### Best Practices Pattern
```go
// 1. Model
package model

type Order struct {
    ID       int64
    Item     string
    Quantity int
    Price    float64
}

// 2. Repository Interface
package repository

import "context"

type OrderRepository interface {
    GetAll(ctx context.Context) ([]model.Order, error)
    Create(ctx context.Context, order model.Order) error
    GetByID(ctx context.Context, id int64) (model.Order, error)
}

// 3. Repository Implementation
type orderRepo struct {
    db *sql.DB
}

func (r *orderRepo) Create(ctx context.Context, order model.Order) error {
    // Database operation
    return nil
}

// 4. Service Layer
package service

type OrderService struct {
    repo repository.OrderRepository
}

func (s *OrderService) CreateOrder(ctx context.Context, order model.Order) error {
    // Business logic
    return s.repo.Create(ctx, order)
}

// 5. Handler (HTTP)
package handler

func (h *Handler) CreateOrder(w http.ResponseWriter, r *http.Request) {
    // Decode request
    // Call service
    // Encode response
}

// 6. Main
package main

func main() {
    // Initialize dependencies
    // Set up routes
    // Start server
    http.ListenAndServe(":8080", mux)
}
```

### Golang Instruction Template
```
GOLANG CODE GENERATION INSTRUCTIONS:

1. PACKAGE ORGANIZATION:
   - cmd/: Entry points only
   - internal/: Private packages (handler/, service/, repository/, model/)
   - pkg/: Public reusable packages
   - Each package is a separate directory with package.go files

2. INTERFACE-FIRST:
   - Define repository interfaces in repository/ package
   - Define service interfaces in service/ package
   - Implement interfaces in separate files or packages
   - Use composition over inheritance

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
   - Write table-driven tests

5. CONCURRENCY (if needed):
   - Use goroutines with contexts for cancellation
   - Use channels for communication between goroutines
   - Close channels to signal completion

6. TESTING:
   - Table-driven tests: []struct{ name string, args, expected }
   - Mock interfaces for unit testing
   - Use testing.T for test functions
   - Keep tests in *_test.go files

OUTPUT: Generate files in appropriate packages:
   1. internal/model/xyz.go
   2. internal/repository/repository.go (interface)
   3. internal/repository/xyz_repo.go (implementation)
   4. internal/service/service.go (interface)
   5. internal/service/xyz_service.go (implementation)
   6. internal/handler/xyz_handler.go
```

---

## 4. RAILS (Ruby) - Convention over Configuration

### Standard Structure
```
app/
├── controllers/          # Controllers
├── models/               # ActiveRecord Models
├── views/                # Templates (if needed)
├── services/             # Business logic
├── repositories/         # Data access patterns
└── serializers/          # Response serialization
config/
└── routes.rb             # Route definitions
db/
├── migrate/              # Migrations
└── schema.rb             # Schema definition
spec/                     # RSpec tests
```

### Core Principles
- **Convention over Configuration**: Follow Rails conventions
- **ActiveRecord**: Built-in ORM with migrations
- **Fat Model, Skinny Controller**: Logic in models/services
- **RESTful**: Follow REST conventions by default

### Best Practices Pattern
```ruby
# 1. Migration
class CreateOrders < ActiveRecord::Migration[7.0]
  def change
    create_table :orders do |t|
      t.string :item
      t.integer :quantity
      t.decimal :price
      t.references :user
      t.timestamps
    end
  end
end

# 2. Model with Validations
class Order < ApplicationRecord
  belongs_to :user
  
  validates :item, presence: true
  validates :quantity, presence: true, numericality: { only_integer: true }
  validates :price, presence: true, numericality: true
end

# 3. Service
class OrderService
  def initialize(order_params)
    @params = order_params
  end
  
  def create
    Order.create!(@params)
  end
end

# 4. Serializer
class OrderSerializer
  def initialize(order)
    @order = order
  end
  
  def as_json
    {
      id: @order.id,
      item: @order.item,
      quantity: @order.quantity,
      price: @order.price
    }
  end
end

# 5. Controller
class OrdersController < ApplicationController
  def create
    service = OrderService.new(order_params)
    order = service.create
    render json: OrderSerializer.new(order), status: :created
  end
  
  private
  def order_params
    params.require(:order).permit(:item, :quantity, :price)
  end
end

# 6. Routes
Rails.application.routes.draw do
  resources :orders, only: [:index, :create, :show]
end
```

### Rails Instruction Template
```
RAILS CODE GENERATION INSTRUCTIONS:

1. FOLLOW CONVENTIONS:
   - Models in app/models/
   - Controllers in app/controllers/
   - Services in app/services/
   - Use RESTful routing (resources :model_name)
   - Migrations in db/migrate/

2. MODEL PATTERNS:
   - Use ActiveRecord relationships (belongs_to, has_many)
   - Add validations for business rules
   - Use callbacks for automatic operations
   - Define scopes for common queries

3. CONTROLLER PATTERNS:
   - Follow CRUD actions: index, show, create, update, destroy
   - Extract business logic to services
   - Use strong parameters (params.require.permit)
   - Use render/redirect_to for responses

4. SERVICE OBJECTS:
   - Extract complex business logic to services
   - Services handle multi-step operations
   - Keep controllers thin and focused

5. DATABASE MIGRATIONS:
   - Create migrations for schema changes
   - Use reversible migrations (add/remove)
   - Name migrations descriptively

6. TESTING:
   - Use RSpec for test framework
   - Test models, controllers, and services separately
   - Use factories for test data (FactoryBot)

OUTPUT: Generate files:
   1. db/migrate/[timestamp]_create_xyz.rb
   2. app/models/xyz.rb
   3. app/services/xyz_service.rb
   4. app/controllers/xyz_controller.rb (update routes)
   5. spec/models/xyz_spec.rb (optional)
```

---

## 5. ASP.NET Core (C#) - Dependency Injection Pattern

### Standard Structure
```
Project/
├── Controllers/          # API Controllers
├── Services/             # Business logic
├── Data/                 # DbContext, repositories
├── Models/               # Domain models
├── DTOs/                 # Data transfer objects
├── Filters/              # Attributes, filters
├── Middleware/           # Custom middleware
└── Program.cs            # Configuration & DI setup
```

### Core Principles
- **Dependency Injection**: Built-in DI container
- **Controllers**: Lightweight, injected dependencies
- **Services**: Business logic with dependency injection
- **DbContext**: Entity Framework Core
- **DTOs**: API contracts separate from models

### Best Practices Pattern
```csharp
// 1. DTO
public class CreateOrderDto
{
    public string Item { get; set; }
    public int Quantity { get; set; }
    public decimal Price { get; set; }
}

// 2. Model
public class Order
{
    public int Id { get; set; }
    public string Item { get; set; }
    public int Quantity { get; set; }
    public decimal Price { get; set; }
}

// 3. Repository Interface
public interface IOrderRepository
{
    Task<List<Order>> GetAllAsync();
    Task<Order> CreateAsync(Order order);
    Task<Order> GetByIdAsync(int id);
}

// 4. DbContext
public class AppDbContext : DbContext
{
    public DbSet<Order> Orders { get; set; }
    
    protected override void OnConfiguring(DbContextOptionsBuilder options)
        => options.UseSqlServer(_connectionString);
}

// 5. Service
public interface IOrderService
{
    Task<OrderDto> CreateOrderAsync(CreateOrderDto dto);
}

public class OrderService : IOrderService
{
    private readonly IOrderRepository _repository;
    
    public OrderService(IOrderRepository repository)
    {
        _repository = repository;
    }
    
    public async Task<OrderDto> CreateOrderAsync(CreateOrderDto dto)
    {
        var order = new Order { Item = dto.Item, ... };
        await _repository.CreateAsync(order);
        return Map(order);
    }
}

// 6. Controller
[ApiController]
[Route("api/[controller]")]
public class OrdersController : ControllerBase
{
    private readonly IOrderService _service;
    
    public OrdersController(IOrderService service)
    {
        _service = service;
    }
    
    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateOrderDto dto)
    {
        var result = await _service.CreateOrderAsync(dto);
        return CreatedAtAction(nameof(Get), new { id = result.Id }, result);
    }
}

// 7. DI Setup (Program.cs)
builder.Services.AddScoped<IOrderRepository, OrderRepository>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddDbContext<AppDbContext>();
```

### ASP.NET Core Instruction Template
```
ASP.NET CORE CODE GENERATION INSTRUCTIONS:

1. DEPENDENCY INJECTION:
   - Register services in Program.cs (AddScoped/AddTransient/AddSingleton)
   - Inject dependencies via constructor
   - Use interfaces for abstraction

2. ARCHITECTURE LAYERS:
   - Controllers: HTTP handling only, inject IService
   - Services: Business logic, orchestration
   - Data: DbContext, repositories
   - Models: Domain entities (EF Core entities)
   - DTOs: API contracts (separate from models)

3. ASYNC/AWAIT:
   - Use async/await throughout
   - Return Task<T> from service/repository methods
   - Use await for database operations

4. ENTITY FRAMEWORK CORE:
   - Define DbSet<T> properties in DbContext
   - Use Fluent API for configurations
   - Create migrations for schema changes

5. VALIDATION:
   - Use data annotations on DTOs
   - Custom validators for complex rules
   - Validation filters in middleware

6. RESPONSE HANDLING:
   - Return appropriate HTTP status codes
   - Use CreatedAtAction for POST responses
   - Use Problem details for errors

OUTPUT: Generate files:
   1. DTOs/CreateXyzDto.cs
   2. Models/Xyz.cs
   3. Data/XyzRepository.cs (+ interface)
   4. Services/XyzService.cs (+ interface)
   5. Controllers/XyzController.cs
   6. Update Program.cs with DI registration
```

---

## 6. NEXT.JS (TypeScript/JavaScript) - Server Components & API Routes

### Standard Structure
```
app/
├── api/                  # API routes
│   └── [resource]/
│       ├── route.ts      # HTTP handlers
│       └── services.ts   # Business logic
├── components/           # React components
├── lib/                  # Utilities
│   ├── db.ts            # Database client
│   └── types.ts         # Type definitions
└── page.tsx             # Pages
public/                   # Static files
```

### Core Principles
- **API Routes**: Serverless functions in app/api/
- **Server Components**: By default (async/await)
- **TypeScript**: Strong typing
- **Middleware**: Request processing

### Best Practices Pattern
```typescript
// 1. Types
export interface Order {
  id: string;
  item: string;
  quantity: number;
  price: number;
}

export interface CreateOrderRequest {
  item: string;
  quantity: number;
  price: number;
}

// 2. Database/Repository
// lib/db.ts
import { Database } from '@/types';

export const db = new Database();

export class OrderRepository {
  async create(data: CreateOrderRequest): Promise<Order> {
    return db.orders.create(data);
  }
  
  async getAll(): Promise<Order[]> {
    return db.orders.findAll();
  }
}

// 3. Service
// app/api/orders/services.ts
import { OrderRepository } from '@/lib/db';

export class OrderService {
  constructor(private repo = new OrderRepository()) {}
  
  async createOrder(data: CreateOrderRequest): Promise<Order> {
    // Business logic
    return this.repo.create(data);
  }
}

// 4. API Route
// app/api/orders/route.ts
import { OrderService } from './services';
import { NextRequest, NextResponse } from 'next/server';

const service = new OrderService();

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const order = await service.createOrder(body);
    return NextResponse.json(order, { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create order' },
      { status: 400 }
    );
  }
}

export async function GET() {
  const orders = await service.getAll();
  return NextResponse.json(orders);
}
```

### Next.JS Instruction Template
```
NEXTJS CODE GENERATION INSTRUCTIONS:

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

3. SERVICE LAYER:
   - Business logic in services.ts files
   - Keep routes thin, delegate to services
   - Unit testable service logic
   - Error handling and validation

4. DATABASE:
   - ORM or database client in lib/db.ts
   - Repository pattern for data access
   - Use connection pooling for performance
   - Handle transactions for multi-step operations

5. MIDDLEWARE:
   - Request validation middleware
   - Authentication/authorization
   - CORS handling if needed

6. TESTING:
   - Jest + React Testing Library
   - Test services separately from routes
   - Mock database for unit tests

OUTPUT: Generate files:
   1. app/api/xyz/route.ts
   2. app/api/xyz/services.ts
   3. lib/types.ts (update)
   4. lib/db.ts (update)
```

---

## 7. IMPLEMENTATION STRATEGY FOR AGENT V3

### Instruction Prompt Template Architecture

```python
def create_code_synthesis_agent(
    codebase_path: str,
    feature_request: str,
    detected_framework: str,  # NEW: spring-boot, laravel, golang, rails, aspnet, nextjs
    files_to_modify: List[str]
):
    """
    Create synthesis agent with framework-specific instructions
    """
    
    # Map framework to instruction set
    framework_instructions = {
        'spring-boot': SPRING_BOOT_INSTRUCTIONS,
        'laravel': LARAVEL_INSTRUCTIONS,
        'golang': GOLANG_INSTRUCTIONS,
        'rails': RAILS_INSTRUCTIONS,
        'aspnet': ASPNET_INSTRUCTIONS,
        'nextjs': NEXTJS_INSTRUCTIONS,
    }
    
    # Get framework-specific prompt
    framework_prompt = framework_instructions.get(
        detected_framework,
        DEFAULT_INSTRUCTIONS
    )
    
    # Build synthesis prompt
    synthesis_prompt = f"""
    {framework_prompt}
    
    FEATURE REQUEST: {feature_request}
    
    FILES TO MODIFY:
    {format_files(files_to_modify)}
    
    CODEBASE CONTEXT:
    {analyze_codebase(codebase_path)}
    
    NOW IMPLEMENT THE FEATURE...
    """
    
    return create_deep_agent(
        system_prompt=synthesis_prompt,
        model=analysis_model,
        backend=FilesystemBackend(codebase_path),
        middleware=create_phase4_middleware(
            feature_request=feature_request,
            affected_files=files_to_modify
        )
    )
```

### Framework Detection Logic
```python
def detect_framework(codebase_path: str) -> str:
    """Detect framework from project structure"""
    
    detection_patterns = {
        'spring-boot': [
            'pom.xml',  # Maven
            'src/main/java',
            'build.gradle',  # Gradle
        ],
        'laravel': [
            'composer.json',
            'artisan',
            'app/Http/Controllers',
        ],
        'golang': [
            'go.mod',
            'go.sum',
            'cmd/',
            'internal/',
        ],
        'rails': [
            'Gemfile',
            'config/routes.rb',
            'app/controllers',
        ],
        'aspnet': [
            '.csproj',
            'Program.cs',
            'appsettings.json',
        ],
        'nextjs': [
            'package.json',  # with "next"
            'app/',
            'next.config.js',
        ],
    }
    
    for framework, patterns in detection_patterns.items():
        if all_patterns_exist(codebase_path, patterns):
            return framework
    
    return 'unknown'
```

### Modular Instruction System

**Option 1: Single Python File with Framework Configs**
```python
# framework_instructions.py

FRAMEWORK_CONFIGS = {
    'spring-boot': {
        'layers': ['controller', 'service', 'repository', 'dto', 'model'],
        'patterns': ['layered', 'dependency-injection'],
        'testing': 'junit5',
        'instructions': SPRING_BOOT_PROMPT,
    },
    'laravel': {
        'layers': ['controller', 'service', 'repository', 'model', 'request'],
        'patterns': ['mvc', 'service-layer'],
        'testing': 'pest',
        'instructions': LARAVEL_PROMPT,
    },
    # ... more frameworks
}
```

**Option 2: Separate Files (Scalable)**
```
frameworks/
├── __init__.py
├── base.py              # Base class
├── spring_boot.py
├── laravel.py
├── golang.py
├── rails.py
├── aspnet.py
└── nextjs.py
```

---

## 8. KEY INSIGHTS FROM RESEARCH

### Universal Patterns (All Frameworks)
✅ **Separation of Concerns**
- Controller/Handler ← HTTP only
- Service ← Business logic
- Repository ← Data access
- Model ← Domain entities
- DTO ← API contracts

✅ **Dependency Injection**
- Services injected into controllers
- Repositories injected into services
- Explicit dependencies in constructors

✅ **Testing Strategy**
- Unit test services independently
- Mock repositories in tests
- Integration tests for full flow

✅ **Error Handling**
- Explicit error returns
- Custom exception types
- Meaningful error messages

### Framework-Specific Considerations

| Framework | Key Pattern | Testing | Package Org |
|-----------|------------|---------|-------------|
| **Spring Boot** | Layered + Annotations | JUnit5 | Packages by domain |
| **Laravel** | Convention + Eloquent | Pest/PHPUnit | Convention-based |
| **Golang** | Interfaces + Composition | Table-driven | Go packages |
| **Rails** | Convention + Migrations | RSpec | Convention-based |
| **ASP.NET** | DI Container + async/await | xUnit | Folders by domain |
| **Next.js** | API Routes + Server Components | Jest + RTL | Feature-based |

---

## 9. IMPLEMENTATION PLAN

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create `frameworks/` module structure
- [ ] Implement framework detection logic
- [ ] Build base instruction template system
- [ ] Create Spring Boot instructions first

### Phase 2: Framework Coverage (Week 2-3)
- [ ] Implement Laravel instructions
- [ ] Implement Golang instructions
- [ ] Implement Rails instructions
- [ ] Implement ASP.NET instructions
- [ ] Implement Next.js instructions

### Phase 3: Testing & Validation (Week 4)
- [ ] Test each framework with sample feature requests
- [ ] Validate generated code matches framework conventions
- [ ] Document expected output for each framework
- [ ] Create regression tests

### Phase 4: Integration (Week 5)
- [ ] Update feature_by_request_agent_v3.py to use framework detection
- [ ] Update create_code_synthesis_agent to use framework-specific instructions
- [ ] Update middleware to framework-aware validation
- [ ] End-to-end testing across all frameworks

---

## 10. PLACEHOLDER STRUCTURE FOR FUTURE FRAMEWORKS

```python
# framework_instructions.py

class FrameworkInstruction(ABC):
    """Base class for framework-specific instructions"""
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return framework-specific system prompt"""
        pass
    
    @abstractmethod
    def get_file_patterns(self) -> Dict[str, str]:
        """Return file naming/location patterns"""
        pass
    
    @abstractmethod
    def get_layer_mapping(self) -> Dict[str, str]:
        """Return mapping of logical layers to directories"""
        pass
    
    @abstractmethod
    def validate_feature_request(self, feature: str) -> bool:
        """Validate if feature is appropriate for framework"""
        pass
    
    def generate_file_structure(self, feature_name: str) -> List[str]:
        """Generate expected files for feature"""
        pass

# Easy to add new framework:
class MyNewFrameworkInstruction(FrameworkInstruction):
    def get_system_prompt(self) -> str:
        return "MyFramework-specific instructions..."
    # ... implement other methods
```

---

## Conclusion

**Recommendation**: Implement modular, framework-specific instruction system that:

1. ✅ **Detects framework automatically** from project structure
2. ✅ **Applies best practices** for that specific framework
3. ✅ **Generates correct file structures** and patterns
4. ✅ **Follows framework conventions** (naming, packaging, testing)
5. ✅ **Enables easy addition** of new frameworks via plugins

This ensures V3 generates **production-quality code** that matches each framework's standards, not generic code that violates architectural principles.
