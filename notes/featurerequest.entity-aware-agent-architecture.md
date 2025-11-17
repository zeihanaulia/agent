# 🧠 Entity-Aware Agent Architecture

**Date Created:** November 14, 2025  
**Status:** 📋 Planning Phase  
**Priority:** 🔴 Critical - Fixes fundamental agent behavior flaw

---

## 📋 Table of Contents

1. [Problem Statement](#-problem-statement)
2. [Root Cause Analysis](#-root-cause-analysis)
3. [Solution Design](#-solution-design)
4. [Implementation Phases](#-implementation-phases)
5. [Expected Workflow](#-expected-workflow)
6. [Testing Strategy](#-testing-strategy)
7. [Multi-Language Support](#-multi-language-support)

---

## 🔴 Problem Statement

### Current Behavior (WRONG)

**User Request:**
```
"Add inventory management with stock tracking. Products should have stock levels, 
and orders should validate available stock before creation."
```

**Agent Output:**
```
✓ Created 14 new files in com.example.inventory package:
  - Inventory.java
  - InventoryEntity.java
  - InventoryService.java
  - InventoryController.java
  - InventoryRepository.java
  - InventoryDTO.java
  ... (8 more files)
```

**Problem:** Agent created entirely new "inventory" domain instead of updating existing `Product.java` entity with stock fields.

---

### Expected Behavior (CORRECT)

**Agent Should:**

1. **Discover existing entities** in codebase (Product, Order, User, etc.)
2. **Compare request entities** with existing entities
3. **Perform impact analysis**:
   - "Product" mentioned in request → exists in codebase → **EXTEND** existing Product.java
   - "Inventory" management logic → doesn't exist → **CREATE** new InventoryService.java
4. **Update existing files** instead of creating duplicates

**Expected Output:**
```
✓ Discovered 3 existing entities: Product, Order, User
✓ Impact Analysis:
  - Product entity exists → will ADD stock fields (stockLevel, stockStatus)
  - Order entity exists → will ADD stock validation logic
  - InventoryService needed → will CREATE new service for business logic

✓ Modified: Product.java (added stockLevel, stockStatus, lastRestocked)
✓ Modified: Order.java (added validateStock() method)
✓ Created: InventoryService.java (stock tracking business logic)
✓ Created: InventoryController.java (stock management endpoints)
```

---

## 🔍 Root Cause Analysis

### Critical Files

| File | Function | Issue |
|------|----------|-------|
| `flow_parse_intent.py` | `extract_entities_from_spec()` (L1692) | Extracts entities from request text ONLY, never checks existing codebase |
| `flow_parse_intent.py` | `infer_new_files_needed()` (L2527) | Plans new files based on request entities without existing entity context |
| `feature_by_request_agent_v3.py` | `analyze_context()` | Only analyzes file structure, doesn't discover existing entities |

### Missing Workflow Phase

```
Current Flow (BROKEN):
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Analyze Context                                    │
│   → Scans file structure only                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Parse Intent                                       │
│   → Extract entities from REQUEST TEXT ONLY ❌              │
│   → No cross-reference with existing codebase              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2.5: Infer New Files                                  │
│   → Plans ALL entities as NEW files ❌                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Impact Analysis                                    │
│   → Too late - entities already determined                  │
└─────────────────────────────────────────────────────────────┘

Result: Always creates new domains instead of updating existing code
```

---

## 💡 Solution Design

### New Workflow (CORRECT)

```
Fixed Flow:
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Analyze Context                                    │
│   → Scans file structure                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 1.5: Discover Existing Entities ✅ NEW               │
│   → Scan existing domain entities (Product, Order, User)    │
│   → Extract entity fields and relationships                 │
│   → Store in state['existing_entities']                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Parse Intent                                       │
│   → Extract entities from request                           │
│   → COMPARE with existing entities ✅                       │
│   → Categorize: entities_to_extend vs entities_to_create    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2.5: Entity Impact Analysis ✅ NEW                   │
│   → For each entity, decide: modify existing or create new? │
│   → Use SubAgent for deep reasoning                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2.6: Infer New Files (Enhanced)                       │
│   → Plan modifications for existing entities                │
│   → Plan new files only for truly new entities              │
└─────────────────────────────────────────────────────────────┘

Result: Updates existing code when appropriate, creates new code when needed
```

---

## 🏗️ Implementation Phases

### Phase 1: Foundation (High Priority)

#### Task 2: Implement `discover_existing_entities()` in `flow_analyze_context.py`

**Function Signature:**
```python
def discover_existing_entities(
    codebase_path: str, 
    framework: str,
    language: str = "java"
) -> Dict[str, Any]:
    """
    Discover all existing domain entities in the codebase.
    
    Supports multiple languages:
    - Java: @Entity classes, POJOs in model/domain/entity packages
    - Python: dataclasses, Pydantic models, SQLAlchemy models
    - Go: structs with json tags
    - Rust: structs with serde
    
    Args:
        codebase_path: Root path of codebase
        framework: Framework type (Spring Boot, FastAPI, Gin, Axum, etc.)
        language: Programming language (java, python, go, rust)
    
    Returns:
        {
            'entities': ['Product', 'Order', 'User'],
            'entity_files': {
                'Product': 'src/main/java/com/example/model/Product.java',
                'Order': 'src/main/java/com/example/model/Order.java'
            },
            'entity_fields': {
                'Product': ['id', 'name', 'description', 'price', 'stock'],
                'Order': ['id', 'userId', 'productId', 'quantity', 'totalPrice']
            },
            'entity_relationships': {
                'Order': ['references Product', 'references User']
            }
        }
    """
```

**Implementation Strategy:**

1. **Java (Spring Boot)**:
   ```python
   # Scan directories: model/, entity/, domain/
   # Look for @Entity annotation or common patterns
   # Use tree-sitter to parse Java AST
   # Extract: class names, fields with types, @OneToMany/@ManyToOne relationships
   ```

2. **Python (FastAPI/Django)**:
   ```python
   # Scan for: dataclasses, Pydantic BaseModel, SQLAlchemy models
   # Look for @dataclass, class Meta, __tablename__
   # Extract: class names, field annotations, relationships
   ```

3. **Go**:
   ```python
   # Scan for structs with json tags
   # Look for gorm tags or common ORM patterns
   # Extract: struct names, fields with types
   ```

4. **Rust**:
   ```python
   # Scan for structs with #[derive(Serialize, Deserialize)]
   # Look for diesel or sea-orm patterns
   # Extract: struct names, fields
   ```

**Example Output:**
```json
{
  "entities": ["Product", "Order", "User"],
  "entity_files": {
    "Product": "src/main/java/com/example/model/Product.java",
    "Order": "src/main/java/com/example/model/Order.java",
    "User": "src/main/java/com/example/model/User.java"
  },
  "entity_fields": {
    "Product": {
      "id": "Long",
      "name": "String",
      "description": "String",
      "price": "BigDecimal",
      "stock": "Integer"
    },
    "Order": {
      "id": "Long",
      "userId": "Long",
      "productId": "Long",
      "quantity": "Integer",
      "totalPrice": "BigDecimal"
    }
  },
  "entity_relationships": {
    "Order": ["@ManyToOne Product", "@ManyToOne User"]
  }
}
```

---

#### Task 3: Update Phase 1 in `feature_by_request_agent_v3.py`

**File:** `scripts/coding_agent/feature_by_request_agent_v3.py`

**Modification in `analyze_context()` function:**

```python
def analyze_context(state: AgentState) -> AgentState:
    """Node: Context Analysis Phase - Fast file system based analysis"""
    print("📂 Phase 1: Context analysis - understanding codebase structure...")
    
    # ... existing context analysis code ...
    
    # ✅ NEW: Discover existing entities
    codebase_path = state["codebase_path"]
    framework = result_state.get("framework", "Spring Boot")
    language = result_state.get("language", "java")
    
    print("  🔍 Discovering existing domain entities...")
    existing_entities = discover_existing_entities(codebase_path, framework, language)
    
    state["existing_entities"] = existing_entities
    state["current_phase"] = "context_analysis_complete"
    
    # Print discovery results
    if existing_entities and existing_entities.get('entities'):
        print(f"  ✓ Discovered {len(existing_entities['entities'])} existing entities:")
        for entity in existing_entities['entities'][:5]:
            file_path = existing_entities['entity_files'].get(entity, 'unknown')
            field_count = len(existing_entities['entity_fields'].get(entity, {}))
            print(f"    - {entity} ({field_count} fields) in {os.path.basename(file_path)}")
        if len(existing_entities['entities']) > 5:
            print(f"    ... and {len(existing_entities['entities']) - 5} more entities")
    else:
        print("  ℹ️  No existing entities found (new project)")
    
    return state
```

---

### Phase 2: Entity Matching (High Priority)

#### Task 4: Modify `extract_entities_from_spec()` in `flow_parse_intent.py`

**File:** `scripts/coding_agent/flow_parse_intent.py`

**Function Enhancement:**

```python
def extract_entities_from_spec(
    feature_request: str, 
    analysis_model: Any = None,
    existing_entities: Optional[Dict[str, Any]] = None  # ✅ NEW PARAMETER
) -> Dict[str, List[str]]:
    """
    Extract domain entities from feature specification text.
    Cross-references with existing entities to determine modification vs creation.
    
    Args:
        feature_request: The full specification text
        analysis_model: Optional LLM model for semantic extraction
        existing_entities: Dictionary of existing entities from Phase 1.5
    
    Returns:
        {
            'entities': ['Product', 'Inventory'],  # All entities mentioned
            'entities_to_extend': ['Product'],     # ✅ Modify existing
            'entities_to_create': ['Inventory'],   # ✅ Create new
            'existing_context': {                  # ✅ Context for decisions
                'Product': {
                    'file': 'Product.java',
                    'current_fields': ['id', 'name', 'price', 'stock'],
                    'action': 'extend'
                }
            }
        }
    """
    
    # Extract entities from request (existing logic)
    entities = []
    
    if analysis_model:
        entities = extract_entities_via_llm(feature_request, excluded_terms)
    
    if not entities:
        entities = extract_entities_semantic_rule_based(feature_request, excluded_terms)
    
    # ✅ NEW: Cross-reference with existing entities
    entities_to_extend = []
    entities_to_create = []
    existing_context = {}
    
    if existing_entities and existing_entities.get('entities'):
        existing_entity_names = existing_entities['entities']
        
        for entity in entities:
            # Check if entity exists in codebase
            if entity in existing_entity_names:
                entities_to_extend.append(entity)
                existing_context[entity] = {
                    'file': existing_entities['entity_files'].get(entity),
                    'current_fields': list(existing_entities['entity_fields'].get(entity, {}).keys()),
                    'action': 'extend',
                    'relationships': existing_entities.get('entity_relationships', {}).get(entity, [])
                }
                print(f"  ✓ Entity '{entity}' exists → will EXTEND existing file")
            else:
                entities_to_create.append(entity)
                existing_context[entity] = {
                    'action': 'create'
                }
                print(f"  ✓ Entity '{entity}' is new → will CREATE new files")
    else:
        # No existing entities, all are new
        entities_to_create = entities.copy()
        for entity in entities:
            existing_context[entity] = {'action': 'create'}
    
    # Generate services, controllers, DTOs
    services = [e + 'Service' for e in entities]
    controllers = [e + 'Controller' for e in entities]
    dtos = [e + 'DTO' for e in entities]
    
    return {
        'entities': entities,
        'entities_to_extend': entities_to_extend,      # ✅ NEW
        'entities_to_create': entities_to_create,      # ✅ NEW
        'existing_context': existing_context,          # ✅ NEW
        'services': services,
        'controllers': controllers,
        'dtos': dtos
    }
```

---

#### Task 5: Update `infer_new_files_needed()` in `flow_parse_intent.py`

**File:** `scripts/coding_agent/flow_parse_intent.py`

**Function Enhancement:**

```python
def infer_new_files_needed(
    feature_request: str,
    context_analysis: str,
    framework: Optional[Any],
    affected_files: List[str],
    llm_response: Optional[str] = None,
    project_spec: Optional[ProjectSpec] = None,
    analysis_model: Optional[Any] = None,
    existing_entities: Optional[Dict[str, Any]] = None  # ✅ NEW PARAMETER
) -> NewFilesPlanningSuggestion:
    """
    Infer what new files need to be created AND what existing files need modification.
    
    Now supports:
    - Creating new entities (when entity doesn't exist)
    - Extending existing entities (when entity exists in codebase)
    - Mixed operations (some extend, some create)
    """
    
    # Extract entities with existing entity context
    spec_entities = extract_entities_from_spec(
        feature_request, 
        analysis_model=analysis_model,
        existing_entities=existing_entities  # ✅ Pass existing entities
    )
    
    # Separate entities by action
    entities_to_extend = spec_entities.get('entities_to_extend', [])
    entities_to_create = spec_entities.get('entities_to_create', [])
    existing_context = spec_entities.get('existing_context', {})
    
    files_to_modify = []
    files_to_create = []
    modifications = []
    
    # ✅ Plan modifications for existing entities
    for entity in entities_to_extend:
        entity_info = existing_context.get(entity, {})
        entity_file = entity_info.get('file')
        current_fields = entity_info.get('current_fields', [])
        
        if entity_file:
            files_to_modify.append(entity_file)
            modifications.append({
                'file': entity_file,
                'entity': entity,
                'action': 'add_fields',
                'current_fields': current_fields,
                'description': f"Extend {entity} entity with new fields from feature request"
            })
            print(f"  📝 Will modify existing: {entity_file}")
    
    # ✅ Plan new files for new entities
    framework_str = str(framework) if framework else "Generic"
    
    for entity in entities_to_create:
        # Use existing subagent planning for new entities
        new_files_plan = plan_files_with_subagent(
            feature_request=feature_request,
            detected_entities=[entity],
            framework=framework_str,
            context_analysis=context_analysis,
            project_spec=project_spec,
            subagent_model=analysis_model
        )
        
        files_to_create.extend(new_files_plan.files_to_create)
        print(f"  📄 Will create new files for: {entity}")
    
    # Combine results
    return NewFilesPlanningSuggestion(
        files_to_create=files_to_create,
        files_to_modify=files_to_modify,         # ✅ NEW
        modifications=modifications,              # ✅ NEW
        reasoning=f"Found {len(entities_to_extend)} existing entities to extend, "
                  f"{len(entities_to_create)} new entities to create",
        framework=framework_str,
        entities_discovered=spec_entities['entities']
    )
```

---

#### Task 9: Update Phase 2 in `feature_by_request_agent_v3.py`

**File:** `scripts/coding_agent/feature_by_request_agent_v3.py`

**Modification in `parse_intent()` function:**

```python
def parse_intent(state: AgentState) -> AgentState:
    print("🎯 Phase 2: Expert analysis - creating implementation plan (using flow_parse_intent)...")
    
    # ... existing code ...
    
    try:
        # Use flow_parse_intent for structured intent parsing
        flow_state = {
            "codebase_path": codebase_path,
            "feature_request": feature_request,
            "context_analysis": context_analysis,
            "full_analysis": full_analysis,
            "existing_entities": state.get("existing_entities", {}),  # ✅ NEW: Pass existing entities
            "framework": None,
            "feature_spec": None,
            "errors": []
        }
        
        # Call flow_parse_intent with analysis_model
        result_state = flow_parse_intent(
            flow_state,
            analysis_model=analysis_model,
            framework_detector=detect_framework
        )
        
        # ... rest of existing code ...
```

---

### Phase 3: Impact Analysis SubAgent (Medium Priority)

#### Task 6: Create `analyze_entity_impact()` SubAgent

**File:** `scripts/coding_agent/flow_parse_intent.py`

**New Function:**

```python
def analyze_entity_impact(
    feature_request: str,
    request_entities: List[str],
    existing_entities: Dict[str, Any],
    analysis_model: Any
) -> Dict[str, Dict[str, Any]]:
    """
    Use SubAgent with DeepAgents for deep reasoning about entity modifications.
    
    Analyzes:
    - Should we extend existing entity or create new domain?
    - What fields need to be added to existing entities?
    - What relationships exist between entities?
    - What business logic changes are needed?
    
    Args:
        feature_request: The feature request text
        request_entities: Entities extracted from request
        existing_entities: Existing entities discovered in Phase 1.5
        analysis_model: LLM model for reasoning
    
    Returns:
        Impact analysis for each entity with recommended actions
    """
    from langchain_core.prompts import ChatPromptTemplate
    
    # Build context about existing entities
    existing_context = []
    for entity in existing_entities.get('entities', []):
        fields = existing_entities['entity_fields'].get(entity, {})
        field_list = ', '.join([f"{name}: {type_}" for name, type_ in fields.items()])
        existing_context.append(f"  - {entity} ({field_list})")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert software architect analyzing entity impacts.
Your task is to determine whether to extend existing entities or create new ones.

DECISION CRITERIA:
1. EXTEND existing entity if:
   - Request mentions entity by name (e.g., "Products should have stock levels" → extend Product)
   - New fields naturally belong to existing entity
   - No architectural reason to separate concerns

2. CREATE new entity if:
   - Request introduces entirely new domain concept
   - Separation of concerns requires new entity
   - Complex relationship better modeled separately

Provide reasoning for each decision."""),
        ("user", """Feature Request:
{feature_request}

Existing Entities in Codebase:
{existing_entities_context}

Entities Mentioned in Request:
{request_entities}

For each entity mentioned in the request, analyze:
1. Does it match an existing entity? (exact match or semantic match)
2. Should we extend existing or create new?
3. What fields/methods need to be added?
4. What relationships are affected?

Return analysis in JSON format:
{{
  "EntityName": {{
    "decision": "extend" | "create",
    "reason": "explanation",
    "target_file": "path/to/file.java" (if extending),
    "fields_to_add": ["field1: Type1", "field2: Type2"],
    "methods_to_add": ["methodName1", "methodName2"],
    "relationships": ["relationship descriptions"]
  }}
}}""")
    ])
    
    # Invoke LLM for reasoning
    chain = prompt | analysis_model
    
    result = chain.invoke({
        "feature_request": feature_request,
        "existing_entities_context": "\n".join(existing_context),
        "request_entities": ", ".join(request_entities)
    })
    
    # Parse JSON response
    import json
    import re
    
    content = result.content if hasattr(result, 'content') else str(result)
    
    # Extract JSON from response
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        impact_analysis = json.loads(json_match.group())
        return impact_analysis
    
    # Fallback: simple heuristic if LLM fails
    fallback_analysis = {}
    for entity in request_entities:
        if entity in existing_entities.get('entities', []):
            fallback_analysis[entity] = {
                "decision": "extend",
                "reason": "Entity exists in codebase",
                "target_file": existing_entities['entity_files'].get(entity),
                "fields_to_add": [],
                "methods_to_add": [],
                "relationships": []
            }
        else:
            fallback_analysis[entity] = {
                "decision": "create",
                "reason": "New entity not found in codebase",
                "fields_to_add": [],
                "methods_to_add": [],
                "relationships": []
            }
    
    return fallback_analysis
```

---

## 🧪 Expected Workflow

### Scenario 1: Initial Project Creation

**Command:**
```bash
source .venv/bin/activate && python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request-spec dataset/spec/simple-case.md
```

**Expected Output:**

```
================================================================================
🤖 FEATURE-BY-REQUEST AGENT V3 (IMPROVED)
================================================================================
📁 Codebase: dataset/codes/springboot-demo
🎯 Feature: Simple Product API — Project Specification
🏃 Mode: IMPLEMENT
================================================================================

📂 Phase 1: Context analysis - understanding codebase structure...
  ✓ Analyzed codebase in 2.3s
  ✓ Framework detected: Spring Boot 3.3
  ✓ Language detected: Java 17
  🔍 Discovering existing domain entities...
  ℹ️  No existing entities found (new project)

🎯 Phase 2: Expert analysis - creating implementation plan...
  ✓ Extracted 1 entities from spec: Product
  ✓ Entity 'Product' is new → will CREATE new files
  ✓ Planned 7 new files for creation:
    - src/main/java/com/example/productapi/model/Product.java
    - src/main/java/com/example/productapi/repository/ProductRepository.java
    - src/main/java/com/example/productapi/service/ProductService.java
    - src/main/java/com/example/productapi/service/ProductServiceImpl.java
    - src/main/java/com/example/productapi/controller/ProductController.java
    - src/main/resources/application.properties
    - pom.xml

🏗️  Phase 3: Impact analysis - identifying patterns...
  ✓ Architecture: Layered (Controller-Service-Repository-Model)
  ✓ Patterns: REST API, JPA Repository, Dependency Injection
  ✓ Files to modify: 0 (new project)
  ✓ Files to create: 7

🧩 Phase 4: Code generation...
  ✓ Generated 7 code change(s)

✅ Phase 5: Execution complete
  ✓ Created: Product.java
  ✓ Created: ProductRepository.java
  ✓ Created: ProductService.java
  ✓ Created: ProductServiceImpl.java
  ✓ Created: ProductController.java
  ✓ Created: application.properties
  ✓ Created: pom.xml

🎉 Feature implementation complete in 45.2s
```

---

### Scenario 2: Follow-up Feature Request (CRITICAL TEST)

**Command:**
```bash
source .venv/bin/activate && python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add inventory management with stock tracking. Products should have stock levels, and orders should validate available stock before creation. Add stock update endpoints and low stock notifications."
```

**Expected Output (AFTER FIX):**

```
================================================================================
🤖 FEATURE-BY-REQUEST AGENT V3 (IMPROVED)
================================================================================
📁 Codebase: dataset/codes/springboot-demo
🎯 Feature: Add inventory management with stock tracking...
🏃 Mode: IMPLEMENT
================================================================================

📂 Phase 1: Context analysis - understanding codebase structure...
  ✓ Analyzed codebase in 1.8s
  ✓ Framework detected: Spring Boot 3.3
  ✓ Language detected: Java 17
  🔍 Discovering existing domain entities...
  ✓ Discovered 3 existing entities:
    - Product (5 fields) in Product.java
    - Order (5 fields) in Order.java
    - User (4 fields) in User.java

🎯 Phase 2: Expert analysis - creating implementation plan...
  ✓ Extracted 3 entities from spec: Product, Inventory, Order
  ✓ Entity 'Product' exists → will EXTEND existing file
  ✓ Entity 'Inventory' is new → will CREATE new files
  ✓ Entity 'Order' exists → will EXTEND existing file

🔍 Phase 2.5: Entity Impact Analysis (SubAgent reasoning)...
  🤖 Analyzing entity relationships and modifications...
  ✓ Product: EXTEND (add stockLevel, stockStatus, lastRestocked)
  ✓ Inventory: CREATE (new domain for stock management logic)
  ✓ Order: EXTEND (add validateStock() method)

  ✓ Files to modify: 2
    - src/main/java/com/example/productapi/model/Product.java
    - src/main/java/com/example/productapi/model/Order.java
  ✓ Files to create: 4
    - src/main/java/com/example/productapi/service/InventoryService.java
    - src/main/java/com/example/productapi/service/InventoryServiceImpl.java
    - src/main/java/com/example/productapi/controller/InventoryController.java
    - src/main/java/com/example/productapi/dto/StockUpdateRequest.java

🏗️  Phase 3: Impact analysis - identifying patterns...
  ✓ Architecture: Layered (Controller-Service-Repository-Model)
  ✓ Existing patterns: REST API, JPA Repository, Dependency Injection
  ✓ Will follow existing patterns for new inventory service

🧩 Phase 4: Code generation...
  ✓ Generated 6 code change(s):
    - edit_file: Product.java (add stock fields)
    - edit_file: Order.java (add stock validation)
    - write_file: InventoryService.java
    - write_file: InventoryServiceImpl.java
    - write_file: InventoryController.java
    - write_file: StockUpdateRequest.java

✅ Phase 5: Execution complete
  ✓ Modified: Product.java (+3 fields: stockLevel, stockStatus, lastRestocked)
  ✓ Modified: Order.java (+1 method: validateStock())
  ✓ Created: InventoryService.java
  ✓ Created: InventoryServiceImpl.java
  ✓ Created: InventoryController.java
  ✓ Created: StockUpdateRequest.java

📊 Summary:
  - Files modified: 2
  - Files created: 4
  - Total changes: 6
  - Existing entities extended: 2 (Product, Order)
  - New domains created: 1 (Inventory)

🎉 Feature implementation complete in 38.7s
```

**Key Differences (Before vs After):**

| Aspect | Before (WRONG) | After (CORRECT) |
|--------|----------------|-----------------|
| Product entity | Created new file | Modified existing file |
| Order entity | Ignored | Modified existing file |
| Files created | 14 files | 4 files |
| Files modified | 0 files | 2 files |
| Architecture | Duplicated domain | Extended existing + new service |

---

## 🧪 Testing Strategy

### Test Case 1: New Project from Scratch

**Input:** `dataset/spec/simple-case.md` (Product API)  
**Expected:** Create all files (no existing entities)

**Validation:**
- ✅ 7 files created
- ✅ 0 files modified
- ✅ Product entity created properly

---

### Test Case 2: Extend Existing Entity

**Input:** "Add stock tracking to products"  
**Existing:** Product.java already exists  
**Expected:** Modify Product.java, don't create new files

**Validation:**
- ✅ Product.java modified (added stockLevel, stockStatus)
- ✅ 0 new Product files created
- ✅ Only supporting files created (InventoryService, Controller)

---

### Test Case 3: Mixed Operations

**Input:** "Add Order management with payment tracking"  
**Existing:** Product.java exists, Order doesn't exist  
**Expected:** Create Order entity, extend Product with orderHistory

**Validation:**
- ✅ Product.java modified
- ✅ Order.java created
- ✅ OrderService, OrderController created

---

### Test Case 4: Multi-Language Support

**Test 4a: Python/FastAPI**
```bash
python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/fastapi-demo \
  --feature-request "Add user authentication with JWT"
```

**Expected:**
- Detect existing User model (Pydantic)
- Extend User with password_hash, is_active
- Create AuthService, TokenService

**Test 4b: Go/Gin**
```bash
python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/gin-demo \
  --feature-request "Add product categories"
```

**Expected:**
- Detect existing Product struct
- Extend Product with CategoryID field
- Create Category struct and handlers

---

## 🌍 Multi-Language Support

### Language Detection Strategy

```python
def detect_language(codebase_path: str) -> str:
    """Detect programming language from codebase."""
    
    # Check for language-specific files
    if os.path.exists(os.path.join(codebase_path, "pom.xml")) or \
       os.path.exists(os.path.join(codebase_path, "build.gradle")):
        return "java"
    
    elif os.path.exists(os.path.join(codebase_path, "requirements.txt")) or \
         os.path.exists(os.path.join(codebase_path, "pyproject.toml")):
        return "python"
    
    elif os.path.exists(os.path.join(codebase_path, "go.mod")):
        return "go"
    
    elif os.path.exists(os.path.join(codebase_path, "Cargo.toml")):
        return "rust"
    
    elif os.path.exists(os.path.join(codebase_path, "package.json")):
        return "javascript"  # or TypeScript
    
    # Fallback: count file extensions
    file_counts = {}
    for root, dirs, files in os.walk(codebase_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            file_counts[ext] = file_counts.get(ext, 0) + 1
    
    # Most common extension determines language
    if file_counts:
        most_common = max(file_counts, key=file_counts.get)
        ext_to_lang = {
            '.java': 'java',
            '.py': 'python',
            '.go': 'go',
            '.rs': 'rust',
            '.js': 'javascript',
            '.ts': 'typescript'
        }
        return ext_to_lang.get(most_common, 'unknown')
    
    return 'unknown'
```

---

### Entity Discovery by Language

#### Java (Spring Boot)

```python
def discover_java_entities(codebase_path: str) -> Dict[str, Any]:
    """Discover Java entities using tree-sitter or AST parsing."""
    
    # Search directories
    search_paths = [
        "src/main/java/**/model",
        "src/main/java/**/entity",
        "src/main/java/**/domain"
    ]
    
    entities = {}
    
    for search_path in search_paths:
        java_files = glob.glob(os.path.join(codebase_path, search_path, "*.java"), recursive=True)
        
        for java_file in java_files:
            # Parse Java file
            with open(java_file, 'r') as f:
                content = f.read()
            
            # Look for @Entity annotation or common patterns
            if '@Entity' in content or 'public class' in content:
                # Extract class name
                class_match = re.search(r'public\s+class\s+(\w+)', content)
                if class_match:
                    class_name = class_match.group(1)
                    
                    # Extract fields
                    field_pattern = r'private\s+(\w+(?:<[\w,\s]+>)?)\s+(\w+);'
                    fields = {}
                    for match in re.finditer(field_pattern, content):
                        field_type = match.group(1)
                        field_name = match.group(2)
                        fields[field_name] = field_type
                    
                    entities[class_name] = {
                        'file': os.path.relpath(java_file, codebase_path),
                        'fields': fields,
                        'is_entity': '@Entity' in content
                    }
    
    return entities
```

---

#### Python (FastAPI/Django)

```python
def discover_python_entities(codebase_path: str) -> Dict[str, Any]:
    """Discover Python entities (Pydantic models, dataclasses, SQLAlchemy)."""
    
    # Search directories
    search_paths = [
        "**/*models.py",
        "**/models/**/*.py",
        "**/*schema.py",
        "**/schemas/**/*.py"
    ]
    
    entities = {}
    
    for search_path in search_paths:
        py_files = glob.glob(os.path.join(codebase_path, search_path), recursive=True)
        
        for py_file in py_files:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Look for Pydantic BaseModel
            pydantic_pattern = r'class\s+(\w+)\(BaseModel\):'
            for match in re.finditer(pydantic_pattern, content):
                class_name = match.group(1)
                
                # Extract fields (simplified - could use AST for better parsing)
                # Look for type annotations after class definition
                class_content = content[match.end():]
                field_pattern = r'(\w+):\s*([\w\[\]]+)'
                fields = {}
                for field_match in re.finditer(field_pattern, class_content):
                    if not field_match.group(1).startswith('__'):
                        fields[field_match.group(1)] = field_match.group(2)
                
                entities[class_name] = {
                    'file': os.path.relpath(py_file, codebase_path),
                    'fields': fields,
                    'type': 'pydantic'
                }
            
            # Look for dataclasses
            dataclass_pattern = r'@dataclass\s+class\s+(\w+):'
            for match in re.finditer(dataclass_pattern, content):
                class_name = match.group(1)
                # Extract fields similarly
                entities[class_name] = {
                    'file': os.path.relpath(py_file, codebase_path),
                    'type': 'dataclass'
                }
    
    return entities
```

---

#### Go

```python
def discover_go_entities(codebase_path: str) -> Dict[str, Any]:
    """Discover Go structs with json tags."""
    
    # Search for Go files
    go_files = glob.glob(os.path.join(codebase_path, "**/*.go"), recursive=True)
    
    entities = {}
    
    for go_file in go_files:
        with open(go_file, 'r') as f:
            content = f.read()
        
        # Look for struct definitions
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{([^}]+)\}'
        
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            struct_body = match.group(2)
            
            # Extract fields with json tags
            field_pattern = r'(\w+)\s+(\w+(?:\[\]\w+)?)\s+`json:"(\w+)"`'
            fields = {}
            for field_match in re.finditer(field_pattern, struct_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                fields[field_name] = field_type
            
            # Only include structs with json tags (likely models)
            if fields:
                entities[struct_name] = {
                    'file': os.path.relpath(go_file, codebase_path),
                    'fields': fields
                }
    
    return entities
```

---

#### Rust

```python
def discover_rust_entities(codebase_path: str) -> Dict[str, Any]:
    """Discover Rust structs with Serialize/Deserialize."""
    
    # Search for Rust files
    rs_files = glob.glob(os.path.join(codebase_path, "**/*.rs"), recursive=True)
    
    entities = {}
    
    for rs_file in rs_files:
        with open(rs_file, 'r') as f:
            content = f.read()
        
        # Look for structs with derive macros
        # Pattern: #[derive(Serialize, Deserialize)] followed by struct
        struct_pattern = r'#\[derive\([^)]*(?:Serialize|Deserialize)[^)]*\)\]\s+pub\s+struct\s+(\w+)\s*\{([^}]+)\}'
        
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            struct_body = match.group(2)
            
            # Extract fields
            field_pattern = r'pub\s+(\w+):\s+([\w<>]+)'
            fields = {}
            for field_match in re.finditer(field_pattern, struct_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                fields[field_name] = field_type
            
            entities[struct_name] = {
                'file': os.path.relpath(rs_file, codebase_path),
                'fields': fields
            }
    
    return entities
```

---

## 📊 Success Metrics

### Before Implementation

- ❌ Agent creates new domains for existing entities
- ❌ 0% entity reuse rate
- ❌ High code duplication
- ❌ Violates DRY principle

### After Implementation

- ✅ Agent extends existing entities when appropriate
- ✅ 80%+ entity reuse rate (modify existing instead of create new)
- ✅ Minimal code duplication
- ✅ Follows real software development practices
- ✅ Multi-language support (Java, Python, Go, Rust)

---

## 📅 Implementation Timeline

| Phase | Tasks | Priority | Estimated Time |
|-------|-------|----------|----------------|
| **Phase 1: Foundation** | Tasks 2, 3 | 🔴 High | 4-6 hours |
| **Phase 2: Entity Matching** | Tasks 4, 5, 9 | 🔴 High | 6-8 hours |
| **Phase 3: Impact Analysis** | Task 6 | 🟡 Medium | 4-6 hours |
| **Phase 4: Multi-Language** | Task 7 | 🟡 Medium | 8-10 hours |
| **Phase 5: Testing** | Tasks 8, 10 | 🟢 Low | 4-6 hours |

**Total Estimated Time:** 26-36 hours

---

## 🎯 Next Steps

1. ✅ Review this documentation
2. ⏳ Start with Phase 1: Implement `discover_existing_entities()` for Java
3. ⏳ Test with simple-case.md spec
4. ⏳ Implement Phase 2: Entity matching logic
5. ⏳ Test with inventory management follow-up request
6. ⏳ Add multi-language support progressively

---

## 📚 References

- DeepAgents Documentation: FilesystemMiddleware, SubAgentMiddleware
- Root Cause Analysis: `notes/codeanalysis.agent-root-causes-visual.md`
- Current Implementation: `scripts/coding_agent/flow_parse_intent.py`
- Workflow Orchestrator: `scripts/coding_agent/feature_by_request_agent_v3.py`

---

**Last Updated:** November 14, 2025  
**Status:** 📋 Ready for Implementation
