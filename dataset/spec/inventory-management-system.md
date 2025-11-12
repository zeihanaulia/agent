# Inventory Management System - Project Specification

## 🎯 Feature Request

Implement comprehensive inventory management system with full CRUD operations including Product entity, repository, service layer, and REST controller with endpoints for creating, reading, updating, and deleting products with complete audit trail tracking.

**Requirements:**
- REST endpoints: `/api/products` (GET, POST), `/api/products/{id}` (GET, PUT, DELETE)
- Entity: Product with SKU, name, description, price, stockQuantity, minStockLevel, category fields
- Repository: JPA repository for data access with custom queries
- Service: Business logic with interface + implementation pattern
- Controller: REST endpoints with proper validation and error handling
- DTOs: Separate ProductRequest/ProductResponse DTOs
- Audit Trail: InventoryTransaction entity tracking all stock movements
- Tests: Comprehensive unit and integration tests
- Follow all code style rules and architecture patterns defined above

---

## 🧠 Project Overview
A comprehensive inventory management system for tracking products, stock levels, and warehouse operations with full CRUD operations, audit trails, and REST API endpoints.

## Technical Stack
- **Language**: Java 17+
- **Framework**: Spring Boot 3.x
- **Build Tool**: Maven
- **Database**: H2 (dev) / PostgreSQL (prod)
- **Architecture**: Layered Architecture (Controller → Service → Repository)

## Core Entities & Relationships

### Product Entity
```java
@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String sku;

    @Column(nullable = false)
    private String name;

    @Column(length = 1000)
    private String description;

    @Column(nullable = false)
    private BigDecimal price;

    @Column(nullable = false)
    private Integer stockQuantity;

    @Column(nullable = false)
    private Integer minStockLevel;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;

    @Column(nullable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;
}
```

### Category Entity
```java
@Entity
@Table(name = "categories")
public class Category {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String name;

    @Column(length = 500)
    private String description;

    @OneToMany(mappedBy = "category", cascade = CascadeType.ALL)
    private List<Product> products;
}
```

### InventoryTransaction Entity (Audit Trail)
```java
@Entity
@Table(name = "inventory_transactions")
public class InventoryTransaction {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    private Product product;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TransactionType type; // IN, OUT, ADJUSTMENT

    @Column(nullable = false)
    private Integer quantity;

    @Column(nullable = false)
    private Integer previousStock;

    @Column(nullable = false)
    private Integer newStock;

    @Column(length = 500)
    private String notes;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    @Column(nullable = false)
    private String performedBy;
}
```

## API Endpoints Specification

### Product Management
```
POST   /api/products          - Create new product
GET    /api/products          - List all products (paginated)
GET    /api/products/{id}     - Get product by ID
PUT    /api/products/{id}     - Update product
DELETE /api/products/{id}     - Delete product
GET    /api/products/search   - Search products by name/SKU
GET    /api/products/low-stock - Get products below minimum stock
```

### Category Management
```
POST   /api/categories        - Create new category
GET    /api/categories        - List all categories
GET    /api/categories/{id}   - Get category by ID
PUT    /api/categories/{id}   - Update category
DELETE /api/categories/{id}   - Delete category
```

### Inventory Operations
```
POST   /api/inventory/adjust  - Adjust stock levels
GET    /api/inventory/transactions - Get transaction history
GET    /api/inventory/alerts  - Get low stock alerts
POST   /api/inventory/stock-in - Stock in operation
POST   /api/inventory/stock-out - Stock out operation
```

## Implementation Requirements

### Data Transfer Objects (DTOs)
- `ProductDTO` - for API requests/responses
- `CategoryDTO` - for API requests/responses
- `InventoryAdjustmentDTO` - for stock adjustments
- `ProductSummaryDTO` - for list views

### Service Layer
- `ProductService` - business logic for products
- `CategoryService` - business logic for categories
- `InventoryService` - inventory operations and audit trail

### Repository Layer
- `ProductRepository` - extends JpaRepository
- `CategoryRepository` - extends JpaRepository
- `InventoryTransactionRepository` - extends JpaRepository

### Controller Layer
- `ProductController` - REST endpoints for products
- `CategoryController` - REST endpoints for categories
- `InventoryController` - REST endpoints for inventory operations

## Validation Rules

### Product Validation
- SKU: required, unique, alphanumeric, max 50 chars
- Name: required, max 255 chars
- Description: optional, max 1000 chars
- Price: required, positive decimal
- Stock Quantity: required, non-negative integer
- Min Stock Level: required, positive integer

### Business Rules
- Cannot delete product if it has inventory transactions
- Stock adjustments must include reason/notes
- Low stock alerts when quantity <= minStockLevel
- All operations must be audited with user tracking

## Code Style & Conventions

### Naming Conventions
- Classes: PascalCase (ProductService, ProductController)
- Methods: camelCase (findById, saveProduct)
- Variables: camelCase (productName, stockQuantity)
- Constants: UPPER_SNAKE_CASE (MAX_NAME_LENGTH)
- Packages: lowercase (com.example.inventory)

### Code Structure
```
src/main/java/com/example/inventory/
├── controller/
│   ├── ProductController.java
│   ├── CategoryController.java
│   └── InventoryController.java
├── service/
│   ├── ProductService.java
│   ├── CategoryService.java
│   └── InventoryService.java
├── repository/
│   ├── ProductRepository.java
│   ├── CategoryRepository.java
│   └── InventoryTransactionRepository.java
├── model/
│   ├── Product.java
│   ├── Category.java
│   └── InventoryTransaction.java
├── dto/
│   ├── ProductDTO.java
│   ├── CategoryDTO.java
│   └── InventoryAdjustmentDTO.java
└── exception/
    └── ResourceNotFoundException.java
```

## Dependencies (pom.xml)

```xml
<dependencies>
    <!-- Spring Boot Starters -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>

    <!-- Database -->
    <dependency>
        <groupId>com.h2database</groupId>
        <artifactId>h2</artifactId>
        <scope>runtime</scope>
    </dependency>

    <!-- Utilities -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>

    <!-- Testing -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

## Configuration (application.yml)

```yaml
spring:
  application:
    name: inventory-management-system

  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
    username: sa
    password:

  jpa:
    hibernate:
      ddl-auto: create-drop
    show-sql: true
    properties:
      hibernate:
        format_sql: true

  h2:
    console:
      enabled: true

server:
  port: 8080

logging:
  level:
    com.example.inventory: DEBUG
    org.springframework.web: DEBUG
```

## Testing Strategy

### Unit Tests
- Service layer: business logic testing
- Repository layer: data access testing
- Controller layer: endpoint testing with MockMvc

### Integration Tests
- Full API testing with TestRestTemplate
- Database integration testing
- End-to-end workflow testing

### Test Examples
```java
@SpringBootTest
@AutoConfigureMockMvc
class ProductControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldCreateProduct() throws Exception {
        ProductDTO productDTO = new ProductDTO();
        productDTO.setSku("TEST-001");
        productDTO.setName("Test Product");
        productDTO.setPrice(new BigDecimal("29.99"));
        productDTO.setStockQuantity(100);
        productDTO.setMinStockLevel(10);

        mockMvc.perform(post("/api/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(productDTO)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.sku").value("TEST-001"));
    }
}
```

## Security Considerations

### Input Validation
- All inputs validated using Bean Validation
- SQL injection prevention via JPA
- XSS protection in responses

### Authentication (Future)
- JWT-based authentication
- Role-based access control
- API key authentication for external systems

## Performance Requirements

### Database Indexing
- SKU column indexed for fast lookups
- Category relationships properly indexed
- Transaction timestamps indexed for audit queries

### API Performance
- Pagination for list endpoints
- Response caching where appropriate
- Database connection pooling

## Deployment & DevOps

### Docker Configuration
```dockerfile
FROM openjdk:17-jdk-slim
WORKDIR /app
COPY target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java","-jar","/app/app.jar"]
```

### CI/CD Pipeline
1. Build with Maven
2. Run unit tests
3. Run integration tests
4. Build Docker image
5. Deploy to staging
6. Run smoke tests
7. Deploy to production

## Monitoring & Observability

### Health Checks
- Database connectivity
- Disk space monitoring
- Memory usage tracking

### Logging
- Structured logging with SLF4J
- Request/response logging
- Error tracking with correlation IDs

### Metrics
- Request count and latency
- Database query performance
- Business metrics (products created, transactions processed)

## Future Enhancements

### Phase 2 Features
- Barcode scanning integration
- Supplier management
- Purchase order system
- Reporting dashboard
- Multi-warehouse support

### Phase 3 Features
- Mobile app companion
- Real-time inventory sync
- Advanced analytics
- Integration with e-commerce platforms
- Automated reordering system

---

## Implementation Priority

1. **HIGH**: Core CRUD operations for products and categories
2. **HIGH**: Basic inventory tracking and audit trail
3. **MEDIUM**: REST API with proper HTTP status codes
4. **MEDIUM**: Input validation and error handling
5. **MEDIUM**: Unit and integration tests
6. **LOW**: Advanced features (search, filtering, pagination)
7. **LOW**: Performance optimization and monitoring

## Success Criteria

- All CRUD operations working correctly
- Comprehensive test coverage (>80%)
- Clean, maintainable code following SOLID principles
- Proper API documentation with OpenAPI/Swagger
- Successful deployment to staging environment
- Performance benchmarks met (response time <200ms for simple queries)