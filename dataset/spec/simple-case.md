# 📦 Simple Product API — Project Specification

## 🎯 Objective

Buat REST API sederhana untuk mengelola data produk dengan fitur:

* Create product
* Read product by ID
* List all products
* Update product
* Delete product

Tujuan: jadi *boilerplate minimalis* untuk belajar atau mengetes coding agent.

---

## 🧱 Stack

| Layer     | Tech                                |
| --------- | ----------------------------------- |
| Language  | Java 17                             |
| Framework | Spring Boot 3.3                     |
| DB        | H2 (in-memory)                      |
| Build     | Maven                               |
| Tooling   | Spring Data JPA, Validation, Lombok |

---

## 🧩 Entity: Product

```java
@Entity
@Table(name = "products")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    private String description;

    @Column(nullable = false)
    private BigDecimal price;

    private Integer stock;
}
```

---

## 🚏 API Endpoints

| Method | Path                 | Description        |
| ------ | -------------------- | ------------------ |
| POST   | `/api/products`      | Create new product |
| GET    | `/api/products`      | Get all products   |
| GET    | `/api/products/{id}` | Get product by ID  |
| PUT    | `/api/products/{id}` | Update product     |
| DELETE | `/api/products/{id}` | Delete product     |

---

## 🧠 Service Layer

```java
public interface ProductService {
    Product create(Product product);
    List<Product> getAll();
    Product getById(Long id);
    Product update(Long id, Product updated);
    void delete(Long id);
}
```

---

## 💬 Controller Example

```java
@RestController
@RequestMapping("/api/products")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService service;

    @PostMapping
    public ResponseEntity<Product> create(@Valid @RequestBody Product product) {
        return ResponseEntity.status(HttpStatus.CREATED).body(service.create(product));
    }

    @GetMapping
    public List<Product> getAll() {
        return service.getAll();
    }

    @GetMapping("/{id}")
    public Product getById(@PathVariable Long id) {
        return service.getById(id);
    }

    @PutMapping("/{id}")
    public Product update(@PathVariable Long id, @RequestBody Product updated) {
        return service.update(id, updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

---

## ⚙️ Repository

```java
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByNameContainingIgnoreCase(String name);
}
```

---

## 🧪 Example Request & Response

### Create Product

**POST /api/products**

```json
{
  "name": "Keyboard",
  "description": "Mechanical RGB keyboard",
  "price": 650000,
  "stock": 50
}
```

**Response (201)**

```json
{
  "id": 1,
  "name": "Keyboard",
  "description": "Mechanical RGB keyboard",
  "price": 650000,
  "stock": 50
}
```

---

## 🧩 application.properties

```properties
spring.datasource.url=jdbc:h2:mem:testdb
spring.datasource.driverClassName=org.h2.Driver
spring.jpa.hibernate.ddl-auto=create-drop
spring.jpa.show-sql=true
spring.h2.console.enabled=true
```

---

## ✅ Success Criteria

* Semua endpoint berfungsi dan mengikuti HTTP status konvensi.
* CRUD dasar bekerja penuh (tanpa error 500).
* Struktur folder clean:

  ```
  src/main/java/com/example/productapi/
    ├── controller/
    ├── service/
    ├── repository/
    ├── model/
  ```
* Bisa jalan via `mvn spring-boot:run`.

