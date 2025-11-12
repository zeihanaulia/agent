# Task Separation: flow_analize_context vs flow_parse_intent

## 🎯 Clear Separation of Concerns

### **Phase 1: flow_analize_context (Context Analysis)**
**Responsibility:** Understand existing codebase

✅ **What it DOES:**
- Scan filesystem & project structure
- Detect framework (Spring Boot, Django, etc)
- Extract code tags & dependencies
- Analyze project architecture patterns
- Provide GENERAL recommendations for new code placement via `infer_code_placement()`

❌ **What it DOES NOT do:**
- Parse specific feature requests
- Extract task/todo items
- Plan which NEW files specifically needed
- Understand feature requirements
- Suggest SOLID principles per file

---

### **Phase 2: flow_parse_intent (Intent Parsing)**
**Responsibility:** Understand feature request & plan implementation

✅ **What it DOES:**
- Extract todos from feature request
- Analyze feature complexity & requirements
- Detect what KIND of files needed (entity, service, controller, etc)
- Plan SPECIFIC new files based on feature
- Apply SOLID principles per file type
- Define creation order (dependency-aware)
- Suggest best practices for implementation

❌ **What it DOES NOT do:**
- Scan entire codebase (that's Phase 1)
- General architecture analysis
- Code tag extraction
- Framework detection (uses result from Phase 1)

---

## 📊 Comparison Table

| Aspect | Phase 1 (Analyze) | Phase 2 (Parse Intent) |
|--------|-------------------|----------------------|
| **Input** | Codebase path | Feature request + context from Phase 1 |
| **Output** | context_analysis | feature_spec + new_files_planning |
| **Scope** | GENERAL (whole project) | SPECIFIC (this feature) |
| **Focus** | Understanding existing | Planning implementation |
| **File Placement** | Generic suggestions | Precise file list with purposes |
| **SOLID** | Not applied | Applied per file type |
| **Todos** | ❌ NO | ✅ YES |
| **Affected Files** | ❌ NO | ✅ YES |
| **New Files** | Generic patterns | ✅ Specific files planned |
| **Framework Knowledge** | Basic detection | Deep (Spring layers, Django apps, etc) |

---

## 🔄 Data Flow (No Overlap)

```
PHASE 1: flow_analize_context
├─ INPUT: codebase_path
├─ ACTION: Scan filesystem, detect patterns
└─ OUTPUT:
   ├─ context_analysis (string)
   ├─ framework (string: "Spring Boot")
   └─ infer_code_placement() method (for reference)

    ↓ (PASS TO PHASE 2)

PHASE 2: flow_parse_intent
├─ INPUT:
│  ├─ feature_request (from user)
│  ├─ context_analysis (FROM PHASE 1)
│  ├─ framework (FROM PHASE 1)
│  └─ affected_files (existing)
├─ ACTION:
│  ├─ Extract todos from feature
│  ├─ Analyze feature requirements
│  ├─ Plan SPECIFIC new files (not generic)
│  ├─ Apply SOLID principles
│  └─ Define creation order
└─ OUTPUT:
   ├─ feature_spec (with todos + affected_files + new_files)
   └─ new_files_planning (detailed suggestions)

NO REDUNDANCY: Phase 2 uses Phase 1 output, doesn't re-scan
```

---

## ✅ NO OVERLAPS - VERIFIED

### Phase 1 ONLY Tasks:
- ✓ `AiderStyleRepoAnalyzer` class (full analyzer)
- ✓ `_basic_filesystem_scan()` 
- ✓ `_extract_code_tags()`
- ✓ `_analyze_dependencies()`
- ✓ `analyze_codebase()` (comprehensive)
- ✓ Reasoning with LLM about request type
- ✓ Token management

### Phase 2 ONLY Tasks:
- ✓ `FilePlacementSuggestion` model
- ✓ `NewFilesPlanningSuggestion` model
- ✓ `infer_new_files_needed()` (feature-specific)
- ✓ `_extract_entity_names()` (from feature request)
- ✓ `_extract_service_names()` (from feature request)
- ✓ `_extract_controller_names()` (from feature request)
- ✓ `_extract_dto_names()` (from feature request)
- ✓ Todo extraction from LLM response
- ✓ SOLID principles per file
- ✓ Best practices per framework

---

## 🎯 Example: Demonstrating Separation

**Scenario:** Add order management

### Phase 1 Output:
```
context_analysis:
  "Spring Boot 3.x project
   Existing: UserService, ProductService
   Architecture: MVC with service layer
   Tech Stack: Java, Spring Boot, JPA"
   
framework: "Spring Boot"
```

### Phase 2 Input + Output:
```
feature_request: "Add order management endpoint"

OUTPUT:
new_files = [
  OrderEntity.java (src/main/java/com/app/entity/)
  OrderRepository.java (src/main/java/com/app/repository/)
  OrderService.java (src/main/java/com/app/service/)
  OrderController.java (src/main/java/com/app/controller/)
  OrderDTO.java (src/main/java/com/app/dto/)
]

Order: entity → repository → dto → service → controller

SOLID: [SRP, OCP, DI] per file
```

✅ **Phase 1** provided context about framework
✅ **Phase 2** planned specific files for THIS feature
❌ **NO redundancy** - each phase has clear role

---

## 📌 Summary

| | Phase 1 | Phase 2 |
|---|---------|---------|
| **Role** | Understand codebase | Plan feature implementation |
| **Reuse** | Scan once per project | Called for each feature |
| **Output Type** | Static analysis | Dynamic planning |
| **Dependency** | Independent | Depends on Phase 1 |
| **Overlap Risk** | ❌ NONE | ✅ ZERO |

**Clean separation ensures:**
- ✅ No duplicate code
- ✅ Each phase has clear responsibility
- ✅ Efficient reuse of Phase 1 results
- ✅ Scalable for multiple features
