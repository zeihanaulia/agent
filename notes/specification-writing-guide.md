# Specification Writing Guide

## Overview

Writing effective specifications is crucial for getting high-quality code generation from the Agnostic Coding Agent. This guide covers best practices, templates, and examples for creating specifications that produce excellent results across any framework.

## Specification Structure

### Basic Template

```markdown
# [Feature Name]

## Feature Request
[Clear, concise description of what you want to build]

## Technical Requirements  
[Framework-specific or technology requirements]

## Data Models
[Data structures, schemas, or entities needed]

## API Design (if applicable)
[Endpoints, routes, or interfaces]

## Business Logic
[Rules, validations, and processing requirements]

## Testing Requirements
[Test scenarios and coverage expectations]

## Integration Points
[External services, databases, or dependencies]

## Performance Considerations (optional)
[Scalability, caching, optimization requirements]

## Security Requirements (optional)
[Authentication, authorization, data protection]
```

## Writing Effective Feature Requests

### ✅ Good Example
```markdown
# User Authentication System

## Feature Request
Implement a complete user authentication system with registration, login, logout, and password reset functionality. The system should support email-based authentication with secure password hashing and JWT token management.

## Technical Requirements
- Use framework's built-in authentication patterns
- Implement secure password hashing (bcrypt/scrypt)
- Generate and validate JWT tokens
- Include email verification workflow
- Add rate limiting for authentication endpoints
- Follow OWASP security guidelines

## Data Models
```json
{
  "User": {
    "id": "string/uuid",
    "email": "string (unique, validated)",
    "passwordHash": "string",
    "firstName": "string", 
    "lastName": "string",
    "isEmailVerified": "boolean",
    "createdAt": "datetime",
    "updatedAt": "datetime",
    "lastLoginAt": "datetime"
  },
  "AuthToken": {
    "id": "string/uuid",
    "userId": "string/uuid (foreign key)",
    "token": "string",
    "type": "enum (access, refresh, verification)",
    "expiresAt": "datetime",
    "isRevoked": "boolean"
  }
}
```

## API Design
- POST /auth/register - User registration
- POST /auth/login - User login
- POST /auth/logout - User logout  
- POST /auth/refresh - Token refresh
- POST /auth/forgot-password - Password reset request
- POST /auth/reset-password - Password reset confirmation
- GET /auth/verify-email/{token} - Email verification

## Business Logic
- Email validation using regex pattern
- Password strength validation (min 8 chars, special chars)
- Account lockout after 5 failed login attempts
- Token expiration: Access (15 min), Refresh (7 days)
- Email verification required before login
- Password reset tokens expire in 1 hour

## Testing Requirements
- Unit tests for all authentication methods
- Integration tests for complete auth flows
- Security tests for common vulnerabilities
- Performance tests for concurrent logins
- Test coverage minimum 90%
```

### ❌ Poor Example
```markdown
# Authentication

## Feature Request
Add login to the app.

## Requirements
- Users can log in
- Make it secure
- Add some tests
```

**Problems with poor example**:
- Vague requirements
- No technical details
- Missing data models
- No API specification
- Unclear security requirements

## Framework-Specific Considerations

### Java/Spring Boot Specifications

```markdown
## Technical Requirements
- Use Spring Security for authentication
- Implement UserDetailsService interface
- Configure JWT with @Configuration classes
- Add @PreAuthorize annotations for method security
- Use Spring Data JPA repositories
- Include @Valid annotations for input validation
- Add @RestController with proper @RequestMapping

## Integration Points
- H2/PostgreSQL database for user storage
- Redis for session management (optional)
- Email service for verification (JavaMail)
- Integration with Spring Boot Actuator for monitoring
```

### Python/FastAPI Specifications

```markdown
## Technical Requirements
- Use FastAPI dependency injection for authentication
- Implement Pydantic models for request/response validation
- Use async/await patterns throughout
- Add proper type hints for all functions
- Use SQLAlchemy with async session
- Include comprehensive docstrings
- Add OpenAPI/Swagger documentation

## Integration Points
- PostgreSQL/SQLite with SQLAlchemy ORM
- Redis for caching and session storage
- SMTP server for email notifications
- Pytest for testing framework
```

### Node.js/Express Specifications

```markdown
## Technical Requirements
- Use Express.js middleware for authentication
- Implement JWT strategy with passport.js
- Use async/await with proper error handling
- Add input validation with Joi or express-validator
- Use Mongoose/Prisma for database operations
- Include TypeScript definitions if applicable
- Add comprehensive JSDoc comments

## Integration Points
- MongoDB/PostgreSQL for data persistence
- Redis for session and caching
- Nodemailer for email services
- Jest/Mocha for testing framework
```

## Data Model Best Practices

### Comprehensive Data Definition

```json
{
  "Product": {
    "id": "uuid (primary key)",
    "sku": "string (unique, indexed)",
    "name": "string (required, 1-255 chars)",
    "description": "text (optional)",
    "price": "decimal (precision: 10,2, required)",
    "category": "string (required, enum: electronics|clothing|books)",
    "inventory": {
      "quantity": "integer (default: 0, min: 0)",
      "reserved": "integer (default: 0, min: 0)",
      "reorderPoint": "integer (default: 10)",
      "maxStock": "integer (default: 1000)"
    },
    "metadata": {
      "weight": "decimal (optional, unit: kg)",
      "dimensions": {
        "length": "decimal",
        "width": "decimal", 
        "height": "decimal"
      },
      "tags": "array of strings"
    },
    "status": "enum (active|inactive|discontinued, default: active)",
    "createdAt": "datetime (auto)",
    "updatedAt": "datetime (auto)",
    "createdBy": "uuid (foreign key to User)"
  }
}
```

### Relationships Definition

```markdown
## Data Relationships
- User (1) -> Orders (many): One user can have multiple orders
- Order (1) -> OrderItems (many): One order contains multiple items
- Product (1) -> OrderItems (many): One product can be in multiple orders
- Category (1) -> Products (many): One category contains multiple products
- User (1) -> Reviews (many): One user can write multiple reviews
- Product (1) -> Reviews (many): One product can have multiple reviews
```

## API Design Patterns

### RESTful API Specification

```markdown
## API Endpoints

### Product Management
- GET /api/products - List all products (with pagination, filtering, sorting)
  - Query params: page, limit, category, priceMin, priceMax, search, sortBy, order
  - Response: { products: Product[], pagination: { total, page, pages }, filters: {} }

- GET /api/products/{id} - Get product by ID
  - Path params: id (uuid)
  - Response: Product object or 404 error

- POST /api/products - Create new product (admin only)
  - Body: CreateProductRequest
  - Response: Created Product object (201) or validation errors (400)

- PUT /api/products/{id} - Update product (admin only) 
  - Path params: id (uuid)
  - Body: UpdateProductRequest
  - Response: Updated Product object or 404/400 errors

- DELETE /api/products/{id} - Delete product (admin only)
  - Path params: id (uuid) 
  - Response: 204 No Content or 404 error

### Inventory Management
- GET /api/products/{id}/inventory - Get inventory status
- PUT /api/products/{id}/inventory - Update inventory levels
- POST /api/products/{id}/inventory/reserve - Reserve inventory for order
- POST /api/products/{id}/inventory/release - Release reserved inventory

## Request/Response Schemas

### CreateProductRequest
```json
{
  "sku": "string (required, unique)",
  "name": "string (required, 1-255 chars)",
  "description": "string (optional)",
  "price": "number (required, > 0)",
  "category": "string (required, valid enum value)",
  "inventory": {
    "quantity": "integer (required, >= 0)",
    "reorderPoint": "integer (optional, default: 10)"
  }
}
```

### ErrorResponse
```json
{
  "error": {
    "code": "string (ERROR_CODE)",
    "message": "string (human readable)",
    "details": "object (validation errors or additional info)",
    "timestamp": "datetime",
    "path": "string (request path)"
  }
}
```
```

## Business Logic Specification

### Validation Rules

```markdown
## Validation Rules

### Product Validation
- SKU must be unique across all products
- Price must be positive number with max 2 decimal places
- Name cannot contain special characters except hyphens and apostrophes
- Category must be from predefined enum list
- Inventory quantity cannot be negative
- Description has 1000 character limit

### Business Rules
- Products cannot be deleted if they have pending orders
- Price changes require admin approval if increase > 20%
- Inventory below reorder point triggers automatic purchase order
- Discontinued products remain in system but hidden from public catalog
- Bulk operations limited to 100 items per request
```

### Error Handling

```markdown
## Error Handling Requirements

### HTTP Status Codes
- 200: Success with data
- 201: Resource created successfully
- 204: Success without response data
- 400: Bad request (validation errors)
- 401: Authentication required
- 403: Forbidden (authorization failed)
- 404: Resource not found
- 409: Conflict (duplicate SKU, etc.)
- 429: Rate limit exceeded
- 500: Internal server error

### Error Response Format
All errors should return consistent JSON format with:
- Error code for programmatic handling
- Human-readable error message
- Validation details when applicable
- Request correlation ID for debugging
- Suggested actions when possible
```

## Testing Specifications

### Comprehensive Testing Requirements

```markdown
## Testing Requirements

### Unit Tests (90% coverage minimum)
- All business logic methods
- Validation functions
- Data transformation utilities
- Error handling scenarios
- Edge cases and boundary conditions

### Integration Tests
- Complete API endpoint workflows
- Database operations and transactions
- External service integrations
- Authentication and authorization flows
- File upload/download operations

### Test Scenarios

#### Product Creation Tests
- Valid product creation with all fields
- Product creation with minimal required fields
- Duplicate SKU rejection
- Invalid data validation (negative price, etc.)
- Authorization checks (admin only)
- Database constraint validation

#### Inventory Management Tests
- Stock level updates
- Reservation and release workflows
- Concurrent inventory modifications
- Low stock notifications
- Bulk inventory operations

#### Error Handling Tests
- Invalid authentication tokens
- Malformed request bodies
- Database connection failures
- External service timeouts
- Rate limiting behavior

### Performance Tests
- Concurrent user scenarios (100+ users)
- Large dataset operations (10,000+ products)
- API response time requirements (< 200ms)
- Database query optimization validation
- Memory usage monitoring
```

## Framework Integration Examples

### Database Integration

```markdown
## Database Requirements

### Schema Definition
- Use framework's migration system for schema management
- Include proper indexes for performance
- Add foreign key constraints for data integrity
- Implement soft deletes for audit trails
- Include created_at/updated_at timestamps

### Query Optimization
- Use framework's query builder for complex queries
- Implement pagination for large datasets
- Add database indexes for frequently searched fields
- Use connection pooling for scalability
- Include query performance monitoring

### Transaction Management
- Wrap related operations in database transactions
- Implement proper rollback on errors
- Use framework's transaction decorators/context managers
- Handle deadlock scenarios gracefully
```

### Security Integration

```markdown
## Security Requirements

### Authentication
- Implement framework's standard authentication mechanism
- Use secure session management
- Add brute force protection
- Include password strength validation
- Implement account lockout policies

### Authorization
- Role-based access control (RBAC)
- Resource-level permissions
- API endpoint protection
- Data filtering based on user permissions
- Audit logging for sensitive operations

### Data Protection
- Input sanitization and validation
- SQL injection prevention
- XSS protection
- CSRF token implementation
- Sensitive data encryption at rest
```

## Common Pitfalls to Avoid

### ❌ Vague Specifications
```markdown
# Bad
Add user management features to the system.

# Good  
Implement complete user CRUD operations with role-based access control, 
including user registration, profile management, password reset, and 
admin user management capabilities.
```

### ❌ Missing Technical Details
```markdown
# Bad
Use a database for storage.

# Good
Use PostgreSQL database with SQLAlchemy ORM, including connection pooling,
migration scripts, and proper indexing for performance. Implement 
repository pattern for data access abstraction.
```

### ❌ Incomplete Data Models
```markdown
# Bad
User table with name and email.

# Good
User entity with complete field definitions, validation rules, 
relationships to other entities, indexes for performance, and 
audit fields for compliance.
```

## Specification Templates by Use Case

### CRUD Operations Template

```markdown
# [Entity] Management System

## Feature Request
Implement complete CRUD (Create, Read, Update, Delete) operations for [Entity] 
with [specific requirements like pagination, search, filtering].

## Technical Requirements
- Follow framework's standard patterns for [controllers/routes/handlers]
- Include input validation using framework's validation library
- Implement proper error handling and HTTP status codes
- Add comprehensive logging for operations
- Include unit and integration tests

## Data Models
[Complete entity definition with all fields, types, constraints]

## API Design
[Complete REST API specification with all endpoints]

## Business Logic
[Validation rules, business constraints, workflow requirements]

## Testing Requirements
[Specific test scenarios and coverage requirements]
```

### Microservice Integration Template

```markdown
# [Service] Integration

## Feature Request
Integrate with [external service] to provide [specific functionality] 
including error handling, retry logic, and fallback mechanisms.

## Technical Requirements
- Implement framework's HTTP client patterns
- Add circuit breaker for resilience
- Include request/response logging
- Implement proper timeout handling
- Add health check endpoints

## Integration Points
- External API: [URL and authentication details]
- Data transformation: [input/output mapping]
- Error handling: [specific error scenarios]
- Monitoring: [metrics and alerting]

## Testing Requirements
- Mock external service for unit tests
- Integration tests with test environment
- Error scenario testing
- Performance testing under load
```

## Quality Checklist

Before submitting a specification, verify:

- ✅ **Clear Feature Description**: Specific, actionable requirements
- ✅ **Complete Data Models**: All fields, types, relationships defined
- ✅ **Detailed API Specification**: Endpoints, parameters, responses
- ✅ **Business Logic**: Validation rules, workflows, constraints
- ✅ **Testing Requirements**: Unit, integration, performance tests
- ✅ **Framework Considerations**: Technology-specific requirements
- ✅ **Security Requirements**: Authentication, authorization, data protection
- ✅ **Error Handling**: Expected errors and response formats
- ✅ **Performance Considerations**: Scalability and optimization needs

---

*Well-written specifications lead to high-quality, maintainable code that follows best practices and integrates seamlessly with your existing codebase.*