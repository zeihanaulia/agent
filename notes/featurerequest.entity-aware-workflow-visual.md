# 🔄 Entity-Aware Agent - Workflow Comparison

**Visual comparison of current (broken) vs new (fixed) workflow**

---

## ❌ Current Workflow (BROKEN)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       USER FEATURE REQUEST                          │
│  "Add inventory management with stock tracking.                     │
│   Products should have stock levels..."                             │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Analyze Context                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Scan file structure                                         │
│ Output:                                                              │
│   • Framework: Spring Boot                                          │
│   • Language: Java                                                  │
│   • Files: 15 Java files found                                      │
│                                                                      │
│ ⚠️  PROBLEM: Only scans structure, doesn't discover entities       │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Parse Intent                                               │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Extract entities from REQUEST TEXT ONLY                     │
│ Output:                                                              │
│   • Entities: ['Product', 'Inventory', 'Order']                     │
│                                                                      │
│ ❌ CRITICAL FLAW: No check if entities already exist in codebase   │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2.5: Infer New Files                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Plan files for ALL entities as NEW                          │
│ Output:                                                              │
│   • New package: com.example.inventory                              │
│   • Files to create: 14 new files                                   │
│     - Inventory.java         (duplicate domain!)                    │
│     - InventoryEntity.java   (duplicate domain!)                    │
│     - Product.java           (ALREADY EXISTS!)                      │
│     - ProductService.java    (ALREADY EXISTS!)                      │
│     - Order.java             (ALREADY EXISTS!)                      │
│     ... 9 more files                                                │
│                                                                      │
│ ❌ WRONG: Plans to CREATE files that should be MODIFIED            │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Impact Analysis                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Analyze architecture patterns                               │
│ Output:                                                              │
│   • Architecture: Layered (Controller-Service-Repository)           │
│   • Files to modify: 0 (none - too late!)                           │
│                                                                      │
│ ⚠️  TOO LATE: Entities already determined, can't change plan       │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Code Synthesis                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Generate code for planned files                             │
│ Output:                                                              │
│   • 14 code changes generated                                       │
│   • All write_file (no edit_file)                                   │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 5: Execution                                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Result:                                                              │
│   ✓ Created: com/example/inventory/Inventory.java                   │
│   ✓ Created: com/example/inventory/InventoryEntity.java             │
│   ✓ Created: com/example/inventory/Product.java    ❌ DUPLICATE!   │
│   ✓ Created: com/example/inventory/Order.java      ❌ DUPLICATE!   │
│   ... 10 more files created                                         │
│                                                                      │
│   Files modified: 0                                                 │
│   Files created: 14                                                 │
│   Code duplication: HIGH ❌                                         │
└─────────────────────────────────────────────────────────────────────┘

RESULT: ❌ Created entirely new "inventory" domain instead of updating 
         existing Product and Order entities!
```

---

## ✅ New Workflow (FIXED)

```
┌─────────────────────────────────────────────────────────────────────┐
│                       USER FEATURE REQUEST                          │
│  "Add inventory management with stock tracking.                     │
│   Products should have stock levels..."                             │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Analyze Context                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Scan file structure                                         │
│ Output:                                                              │
│   • Framework: Spring Boot                                          │
│   • Language: Java                                                  │
│   • Files: 15 Java files found                                      │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1.5: Discover Existing Entities ✨ NEW                       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Scan codebase for existing domain entities                  │
│ Method: discover_existing_entities()                                │
│ Output:                                                              │
│   • Discovered 3 existing entities:                                 │
│     - Product (5 fields) in model/Product.java                      │
│       Fields: id, name, description, price, stock                   │
│     - Order (5 fields) in model/Order.java                          │
│       Fields: id, userId, productId, quantity, totalPrice           │
│     - User (4 fields) in model/User.java                            │
│       Fields: id, username, email, createdAt                        │
│                                                                      │
│   • Stored in state["existing_entities"]                            │
│                                                                      │
│ ✅ SUCCESS: Existing entities discovered and documented             │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2: Parse Intent (ENHANCED) ✨                                │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Extract entities from request AND compare with existing     │
│ Method: extract_entities_from_spec(existing_entities=...)           │
│                                                                      │
│ Step 1: Extract from request                                        │
│   • Request entities: ['Product', 'Inventory', 'Order']             │
│                                                                      │
│ Step 2: Compare with existing ✨ NEW                               │
│   • Existing entities: ['Product', 'Order', 'User']                 │
│                                                                      │
│ Step 3: Categorize ✨ NEW                                          │
│   • entities_to_extend: ['Product', 'Order']  ← MODIFY EXISTING    │
│   • entities_to_create: ['Inventory']         ← CREATE NEW         │
│                                                                      │
│ Output:                                                              │
│   ✓ Entity 'Product' exists → will EXTEND existing file            │
│   ✓ Entity 'Order' exists → will EXTEND existing file              │
│   ✓ Entity 'Inventory' is new → will CREATE new files              │
│                                                                      │
│ ✅ SUCCESS: Smart categorization based on existing codebase         │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2.5: Entity Impact Analysis ✨ NEW                           │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Deep reasoning about entity modifications (SubAgent)        │
│ Method: analyze_entity_impact()                                     │
│                                                                      │
│ Analysis for Product entity:                                        │
│   • Decision: EXTEND                                                │
│   • Reason: Request mentions "Products should have stock levels"    │
│   • Target file: model/Product.java                                 │
│   • Fields to add: stockLevel, stockStatus, lastRestocked           │
│   • Methods to add: updateStock(), isLowStock()                     │
│                                                                      │
│ Analysis for Order entity:                                          │
│   • Decision: EXTEND                                                │
│   • Reason: Request mentions "orders should validate stock"         │
│   • Target file: model/Order.java                                   │
│   • Methods to add: validateStock()                                 │
│                                                                      │
│ Analysis for Inventory:                                             │
│   • Decision: CREATE                                                │
│   • Reason: New business logic domain, separate from Product        │
│   • Files to create: InventoryService, InventoryController          │
│                                                                      │
│ ✅ SUCCESS: Smart decisions based on business logic reasoning       │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 2.6: Infer New Files (ENHANCED) ✨                           │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Plan modifications AND creations                            │
│ Method: infer_new_files_needed(existing_entities=...)               │
│                                                                      │
│ Files to MODIFY (extend existing):                                  │
│   📝 model/Product.java                                             │
│      Action: add_fields                                             │
│      Current: id, name, description, price, stock                   │
│      Add: stockLevel, stockStatus, lastRestocked                    │
│                                                                      │
│   📝 model/Order.java                                               │
│      Action: add_method                                             │
│      Add: validateStock()                                           │
│                                                                      │
│ Files to CREATE (new entities):                                     │
│   📄 service/InventoryService.java                                  │
│   📄 service/InventoryServiceImpl.java                              │
│   📄 controller/InventoryController.java                            │
│   📄 dto/StockUpdateRequest.java                                    │
│                                                                      │
│ Summary:                                                             │
│   • Files to modify: 2                                              │
│   • Files to create: 4                                              │
│   • Total changes: 6 (vs 14 in old workflow!)                       │
│                                                                      │
│ ✅ SUCCESS: Efficient plan that reuses existing code                │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Impact Analysis                                            │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Analyze architecture patterns and constraints               │
│ Output:                                                              │
│   • Architecture: Layered (Controller-Service-Repository)           │
│   • Patterns: REST API, JPA Repository, Dependency Injection        │
│   • Files to modify: 2 (Product.java, Order.java)                   │
│   • Files to create: 4 (Inventory service layer)                    │
│                                                                      │
│ ✅ Now has complete context for implementation                      │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 4: Code Synthesis                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Action: Generate code for modifications and creations               │
│ Output:                                                              │
│   • 6 code changes generated:                                       │
│     - edit_file: Product.java (add stock fields)                    │
│     - edit_file: Order.java (add stock validation)                  │
│     - write_file: InventoryService.java                             │
│     - write_file: InventoryServiceImpl.java                         │
│     - write_file: InventoryController.java                          │
│     - write_file: StockUpdateRequest.java                           │
│                                                                      │
│ ✅ Mix of edit_file and write_file operations                       │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 5: Execution                                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ Result:                                                              │
│   ✅ Modified: model/Product.java                                   │
│      (+3 fields: stockLevel, stockStatus, lastRestocked)            │
│                                                                      │
│   ✅ Modified: model/Order.java                                     │
│      (+1 method: validateStock())                                   │
│                                                                      │
│   ✅ Created: service/InventoryService.java                         │
│   ✅ Created: service/InventoryServiceImpl.java                     │
│   ✅ Created: controller/InventoryController.java                   │
│   ✅ Created: dto/StockUpdateRequest.java                           │
│                                                                      │
│ Summary:                                                             │
│   • Files modified: 2                                               │
│   • Files created: 4                                                │
│   • Total changes: 6                                                │
│   • Existing entities extended: 2 (Product, Order)                  │
│   • New domains created: 1 (Inventory service layer)                │
│   • Code duplication: MINIMAL ✅                                    │
└─────────────────────────────────────────────────────────────────────┘

RESULT: ✅ Extended existing Product and Order entities, created only 
         necessary Inventory service layer. No duplicate domains!
```

---

## 📊 Key Differences

| Aspect | Old Workflow | New Workflow | Improvement |
|--------|--------------|--------------|-------------|
| **Entity Discovery** | ❌ None | ✅ Phase 1.5 discovers all existing entities | Context-aware |
| **Entity Comparison** | ❌ Never checks existing | ✅ Compares request vs existing | Smart categorization |
| **Impact Analysis** | ❌ Too late to change plan | ✅ Early phase with SubAgent reasoning | Informed decisions |
| **File Planning** | ❌ All files as NEW | ✅ Modifications + Creations | Efficient reuse |
| **Files Modified** | 0 | 2 (Product, Order) | Extends existing |
| **Files Created** | 14 (with duplicates) | 4 (only new) | No duplication |
| **Code Reuse** | 0% | 80%+ | Follows DRY |
| **Architecture** | ❌ Creates duplicate domains | ✅ Extends existing + new services | Clean separation |

---

## 🎯 Visual Summary

### Before (Current)

```
Request → Extract Entities → Plan ALL as NEW → Create 14 files (with duplicates)
          (from request only)   (no context)
```

### After (Fixed)

```
Request → Discover Existing → Compare Entities → Impact Analysis → Plan Smart
          (scan codebase)     (extend vs create) (SubAgent)        (modify + create)
                                                                    ↓
                                                            Modify 2, Create 4
                                                            (no duplicates)
```

---

## 🔑 Critical New Components

1. **`discover_existing_entities()`** - Scans codebase for existing entities
2. **`extract_entities_from_spec(existing_entities=...)`** - Compares with existing
3. **`analyze_entity_impact()`** - SubAgent for deep reasoning
4. **`infer_new_files_needed(existing_entities=...)`** - Plans modifications + creations

---

**Last Updated:** November 14, 2025  
**Status:** Ready for implementation
