# 📊 Entity-Aware Agent - Implementation Summary

**Created:** November 14, 2025  
**Status:** ✅ Documentation Complete, ⏳ Implementation Pending

---

## 🎯 Objective

Fix critical agent behavior flaw where the agent **always creates new domains** instead of **updating existing code** when appropriate.

---

## 📋 Problem Example

### Current Behavior (WRONG ❌)

**User Request:**
```
"Add inventory management with stock tracking. Products should have 
stock levels, and orders should validate available stock before creation."
```

**Agent Output:**
```
✓ Created 14 new files in com.example.inventory package:
  - Inventory.java
  - InventoryEntity.java  
  - InventoryService.java
  - InventoryController.java
  ... (10 more files)
```

**Problem:** Agent ignored existing `Product.java` and `Order.java` entities!

---

### Expected Behavior (CORRECT ✅)

**Agent Should Output:**
```
✓ Discovered 3 existing entities: Product, Order, User
✓ Impact Analysis:
  - Product exists → EXTEND with stock fields
  - Order exists → EXTEND with stock validation
  - Inventory logic → CREATE new service

✓ Modified: Product.java (+3 fields: stockLevel, stockStatus, lastRestocked)
✓ Modified: Order.java (+1 method: validateStock())
✓ Created: InventoryService.java
✓ Created: InventoryController.java
```

**Result:** 2 files modified, 2 files created (instead of 14 new files)

---

## 🔍 Root Cause

### Files with Issues

| File | Function | Line | Issue |
|------|----------|------|-------|
| `flow_parse_intent.py` | `extract_entities_from_spec()` | 1692 | Extracts entities from request text only, never checks existing codebase |
| `flow_parse_intent.py` | `infer_new_files_needed()` | 2527 | Plans new files without existing entity context |
| `feature_by_request_agent_v3.py` | `analyze_context()` | ~200 | Only scans file structure, doesn't discover entities |

### Missing Workflow Phase

```
Current (BROKEN):
Phase 1: Analyze Context → file structure only
Phase 2: Parse Intent → extract entities from request ❌
Phase 2.5: Plan Files → all entities as NEW ❌

Should be:
Phase 1: Analyze Context → file structure
Phase 1.5: Discover Entities → scan existing entities ✅ NEW
Phase 2: Parse Intent → compare request vs existing ✅ ENHANCED
Phase 2.5: Impact Analysis → modify or create? ✅ NEW
Phase 2.6: Plan Files → modifications + creations ✅ ENHANCED
```

---

## 💡 Solution Architecture

### New Workflow Components

#### 1. Entity Discovery (Phase 1.5)

**Function:** `discover_existing_entities()` in `flow_analyze_context.py`

**Purpose:** Scan codebase for existing domain entities

**Output:**
```python
{
  'entities': ['Product', 'Order', 'User'],
  'entity_files': {
    'Product': 'src/main/java/com/example/model/Product.java',
    'Order': 'src/main/java/com/example/model/Order.java'
  },
  'entity_fields': {
    'Product': {'id': 'Long', 'name': 'String', 'price': 'BigDecimal', 'stock': 'Integer'},
    'Order': {'id': 'Long', 'userId': 'Long', 'productId': 'Long', 'quantity': 'Integer'}
  }
}
```

**Supports:**
- ✅ Java (Spring Boot) - @Entity classes
- ✅ Python (FastAPI/Django) - Pydantic models, dataclasses
- ✅ Go - structs with json tags
- ✅ Rust - structs with Serialize/Deserialize

---

#### 2. Entity Comparison (Phase 2 Enhancement)

**Function:** `extract_entities_from_spec()` enhanced in `flow_parse_intent.py`

**New Logic:**
```python
# Extract entities from request
request_entities = ['Product', 'Inventory', 'Order']

# Compare with existing
existing_entities = ['Product', 'Order', 'User']

# Categorize
entities_to_extend = ['Product', 'Order']  # ✅ Modify existing
entities_to_create = ['Inventory']         # ✅ Create new
```

**Output:**
```python
{
  'entities': ['Product', 'Inventory', 'Order'],
  'entities_to_extend': ['Product', 'Order'],     # NEW ✅
  'entities_to_create': ['Inventory'],            # NEW ✅
  'existing_context': {                           # NEW ✅
    'Product': {
      'file': 'Product.java',
      'current_fields': ['id', 'name', 'price', 'stock'],
      'action': 'extend'
    }
  }
}
```

---

#### 3. File Planning (Phase 2.6 Enhancement)

**Function:** `infer_new_files_needed()` enhanced in `flow_parse_intent.py`

**New Logic:**
```python
# Plan modifications for existing entities
for entity in entities_to_extend:
    files_to_modify.append(entity_file)
    print(f"📝 Will modify: {entity_file}")

# Plan creation for new entities
for entity in entities_to_create:
    files_to_create.extend(plan_new_entity_files(entity))
    print(f"📄 Will create files for: {entity}")
```

**Output:**
```python
NewFilesPlanningSuggestion(
    files_to_create=['InventoryService.java', 'InventoryController.java'],
    files_to_modify=['Product.java', 'Order.java'],  # NEW ✅
    modifications=[...]                               # NEW ✅
)
```

---

## 📝 Implementation Tasks

### Priority 1: Foundation (Tasks 2, 3)

✅ **Task 1:** Documentation  
- [x] Main architecture doc: `featurerequest.entity-aware-agent-architecture.md`
- [x] Quick reference: `featurerequest.entity-aware-quick-reference.md`

⏳ **Task 2:** Implement `discover_existing_entities()`
- File: `scripts/coding_agent/flow_analyze_context.py`
- Add function to scan and extract entities
- Support Java first, then expand to other languages

⏳ **Task 3:** Update Phase 1
- File: `scripts/coding_agent/feature_by_request_agent_v3.py`
- Modify `analyze_context()` to call entity discovery
- Store results in `state["existing_entities"]`

---

### Priority 2: Entity Matching (Tasks 4, 5, 9)

⏳ **Task 4:** Enhance `extract_entities_from_spec()`
- File: `scripts/coding_agent/flow_parse_intent.py`
- Add `existing_entities` parameter
- Add comparison logic for entities_to_extend vs entities_to_create

⏳ **Task 5:** Enhance `infer_new_files_needed()`
- File: `scripts/coding_agent/flow_parse_intent.py`
- Add `existing_entities` parameter
- Plan modifications AND creations (not just creations)

⏳ **Task 9:** Update Phase 2
- File: `scripts/coding_agent/feature_by_request_agent_v3.py`
- Modify `parse_intent()` to pass existing_entities to flow

---

### Priority 3: Advanced Features (Tasks 6, 7)

⏳ **Task 6:** Create `analyze_entity_impact()` SubAgent
- Deep reasoning: should we extend or create?
- Use LLM to analyze entity relationships

⏳ **Task 7:** Multi-language support
- Python entity discovery (Pydantic, dataclasses)
- Go entity discovery (structs with json tags)
- Rust entity discovery (structs with derive macros)

---

### Priority 4: Testing (Tasks 8, 10)

⏳ **Task 8:** Test with simple-case.md
- Initial project creation (no existing entities)
- Follow-up request (should modify existing)

⏳ **Task 10:** Validation tests
- Verify Product entity updates (not new inventory domain)
- Verify Order entity updates (stock validation)

---

## 🧪 Test Plan

### Test 1: Initial Project Creation

**Command:**
```bash
source .venv/bin/activate && \
python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request-spec dataset/spec/simple-case.md
```

**Expected Output:**
```
📂 Phase 1: Context analysis...
  🔍 Discovering existing domain entities...
  ℹ️  No existing entities found (new project)

🎯 Phase 2: Expert analysis...
  ✓ Extracted 1 entities from spec: Product
  ✓ Entity 'Product' is new → will CREATE new files
  ✓ Planned 7 new files

✅ Phase 5: Execution complete
  ✓ Created: Product.java
  ✓ Created: ProductService.java
  ✓ Created: ProductController.java
  ... (4 more files)
```

---

### Test 2: Follow-up Request (CRITICAL)

**Command:**
```bash
source .venv/bin/activate && \
python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add inventory management with stock tracking. Products should have stock levels, and orders should validate available stock before creation."
```

**Expected Output (AFTER FIX):**
```
📂 Phase 1: Context analysis...
  🔍 Discovering existing domain entities...
  ✓ Discovered 3 existing entities:
    - Product (5 fields) in Product.java
    - Order (5 fields) in Order.java
    - User (4 fields) in User.java

🎯 Phase 2: Expert analysis...
  ✓ Extracted 3 entities from spec: Product, Inventory, Order
  ✓ Entity 'Product' exists → will EXTEND existing file
  ✓ Entity 'Inventory' is new → will CREATE new files
  ✓ Entity 'Order' exists → will EXTEND existing file

  ✓ Files to modify: 2
    - Product.java
    - Order.java
  ✓ Files to create: 4
    - InventoryService.java
    - InventoryServiceImpl.java
    - InventoryController.java
    - StockUpdateRequest.java

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
```

**Success Criteria:**
- ✅ Product.java MODIFIED (not created new)
- ✅ Order.java MODIFIED (not ignored)
- ✅ Only 4 new files created (not 14)
- ✅ No "com.example.inventory" domain created

---

## 📊 Success Metrics

| Metric | Before | Target | Status |
|--------|--------|--------|--------|
| Entity reuse rate | 0% | 80%+ | ⏳ To implement |
| Files modified for inventory request | 0 | 2 | ⏳ To test |
| Files created for inventory request | 14 | 4-6 | ⏳ To test |
| Existing entity detection | ❌ Never | ✅ Always | ⏳ To implement |
| Multi-language support | ❌ None | ✅ Java, Python, Go, Rust | ⏳ To implement |

---

## 📚 Documentation Files

| File | Purpose | Status |
|------|---------|--------|
| `featurerequest.entity-aware-agent-architecture.md` | Complete architecture documentation | ✅ Created |
| `featurerequest.entity-aware-quick-reference.md` | Quick implementation guide | ✅ Created |
| `featurerequest.entity-aware-implementation-summary.md` | This file - overall summary | ✅ Created |

---

## 🎯 Next Steps

1. **Review Documentation** (30 min)
   - Read architecture doc for complete understanding
   - Review quick reference for implementation details

2. **Start Implementation** (4-6 hours)
   - Task 2: Implement `discover_existing_entities()` for Java
   - Task 3: Update `analyze_context()` to call discovery
   - Test with simple-case.md

3. **Entity Matching** (6-8 hours)
   - Task 4: Enhance `extract_entities_from_spec()`
   - Task 5: Enhance `infer_new_files_needed()`
   - Task 9: Update `parse_intent()`
   - Test with inventory management request

4. **Validation** (2-4 hours)
   - Run both test scenarios
   - Verify success criteria
   - Document results

---

## 🚨 Common Issues to Watch

1. **Entity not discovered**
   - Check search paths match project structure
   - Verify regex patterns match entity declarations

2. **Entity discovered but not matched**
   - Check entity name comparison (case-sensitive?)
   - Verify `existing_entities` passed through all phases

3. **Planning creation instead of modification**
   - Debug `entities_to_extend` vs `entities_to_create` logic
   - Verify `files_to_modify` returned correctly

4. **Modifications not executed**
   - Check Phase 5 execution logic handles `files_to_modify`
   - Verify `edit_file` tool called for modifications

---

## 📅 Estimated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Documentation | 2-3 hours | ✅ Complete |
| Foundation (Tasks 2-3) | 4-6 hours | ⏳ Pending |
| Entity Matching (Tasks 4-5, 9) | 6-8 hours | ⏳ Pending |
| Testing (Tasks 8, 10) | 4-6 hours | ⏳ Pending |
| Advanced Features (Tasks 6-7) | 8-10 hours | ⏳ Optional |
| **Total** | **24-33 hours** | **8% complete** |

---

**Last Updated:** November 14, 2025  
**Version:** 1.0  
**Status:** 📋 Ready for Implementation

---

## 📞 Quick Links

- **Architecture Doc:** `notes/featurerequest.entity-aware-agent-architecture.md`
- **Quick Reference:** `notes/featurerequest.entity-aware-quick-reference.md`
- **Root Cause Analysis:** See "Root Cause" section in Architecture Doc
- **Code Examples:** See "Key Code Snippets" in Quick Reference
- **Test Scenarios:** See "Expected Workflow" in Architecture Doc
