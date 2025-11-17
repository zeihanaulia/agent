# 🚀 Entity-Aware Agent - Quick Reference

**Status:** 📋 Implementation Guide  
**Target:** Make agent extend existing code instead of always creating new domains

---

## ⚡ Quick Start

### Problem in 30 Seconds

**Current behavior:**
```
Request: "Add inventory to products"
Agent: Creates com.example.inventory domain (14 new files) ❌
```

**Expected behavior:**
```
Request: "Add inventory to products"
Agent: Modifies Product.java (adds stock fields) ✅
       Creates InventoryService.java (business logic) ✅
```

---

## 🎯 Implementation Checklist

### Phase 1: Foundation (HIGH PRIORITY)

- [ ] **Task 2:** Create `discover_existing_entities()` in `flow_analyze_context.py`
  - Location: After `ContextAnalyzer` class
  - Function: Scan codebase for existing entities (Product, Order, User, etc.)
  - Output: `{'entities': [...], 'entity_files': {...}, 'entity_fields': {...}}`

- [ ] **Task 3:** Update `analyze_context()` in `feature_by_request_agent_v3.py`
  - Location: Line ~200-300 (in analyze_context function)
  - Add: Call `discover_existing_entities()` after context analysis
  - Store: `state["existing_entities"] = existing_entities`

---

### Phase 2: Entity Matching (HIGH PRIORITY)

- [ ] **Task 4:** Modify `extract_entities_from_spec()` in `flow_parse_intent.py`
  - Location: Line 1692
  - Add parameter: `existing_entities: Optional[Dict[str, Any]] = None`
  - Add logic: Compare request entities vs existing entities
  - Return: `{'entities_to_extend': [...], 'entities_to_create': [...]}`

- [ ] **Task 5:** Update `infer_new_files_needed()` in `flow_parse_intent.py`
  - Location: Line 2527
  - Add parameter: `existing_entities: Optional[Dict[str, Any]] = None`
  - Add logic: Plan modifications for existing, creation for new
  - Return: `NewFilesPlanningSuggestion` with `files_to_modify` field

- [ ] **Task 9:** Update `parse_intent()` in `feature_by_request_agent_v3.py`
  - Location: Line 289
  - Modify: Pass `existing_entities` to `flow_parse_intent()`
  - Add to flow_state: `"existing_entities": state.get("existing_entities", {})`

---

### Phase 3: Testing (MEDIUM PRIORITY)

- [ ] **Task 8:** Test with simple-case.md
  - Command: `python3 scripts/coding_agent/feature_by_request_agent_v3.py --codebase-path dataset/codes/springboot-demo --feature-request-spec dataset/spec/simple-case.md`
  - Expected: Create Product API from scratch (no existing entities)

- [ ] **Task 8b:** Test with follow-up request
  - Command: `python3 scripts/coding_agent/feature_by_request_agent_v3.py --codebase-path dataset/codes/springboot-demo --feature-request "Add inventory management..."`
  - Expected: MODIFY Product.java (not create new inventory domain)

---

## 📝 Key Code Snippets

### Snippet 1: Discover Existing Entities (Java)

```python
def discover_existing_entities(codebase_path: str, framework: str, language: str = "java") -> Dict[str, Any]:
    """Discover existing domain entities in codebase."""
    
    if language.lower() == "java":
        # Search for entity files
        search_paths = [
            "src/main/java/**/model/*.java",
            "src/main/java/**/entity/*.java",
            "src/main/java/**/domain/*.java"
        ]
        
        entities = {}
        entity_files = {}
        entity_fields = {}
        
        for search_path in search_paths:
            java_files = glob.glob(os.path.join(codebase_path, search_path), recursive=True)
            
            for java_file in java_files:
                with open(java_file, 'r') as f:
                    content = f.read()
                
                # Extract class name
                class_match = re.search(r'public\s+class\s+(\w+)', content)
                if class_match:
                    class_name = class_match.group(1)
                    
                    # Extract fields
                    field_pattern = r'private\s+(\w+)\s+(\w+);'
                    fields = {}
                    for match in re.finditer(field_pattern, content):
                        field_type = match.group(1)
                        field_name = match.group(2)
                        fields[field_name] = field_type
                    
                    entities.append(class_name)
                    entity_files[class_name] = os.path.relpath(java_file, codebase_path)
                    entity_fields[class_name] = fields
        
        return {
            'entities': entities,
            'entity_files': entity_files,
            'entity_fields': entity_fields,
            'entity_relationships': {}
        }
    
    # Add support for other languages later
    return {'entities': [], 'entity_files': {}, 'entity_fields': {}}
```

---

### Snippet 2: Entity Comparison Logic

```python
# In extract_entities_from_spec()

entities_to_extend = []
entities_to_create = []

if existing_entities and existing_entities.get('entities'):
    existing_entity_names = existing_entities['entities']
    
    for entity in request_entities:
        if entity in existing_entity_names:
            entities_to_extend.append(entity)
            print(f"  ✓ Entity '{entity}' exists → will EXTEND")
        else:
            entities_to_create.append(entity)
            print(f"  ✓ Entity '{entity}' is new → will CREATE")
else:
    entities_to_create = request_entities.copy()

return {
    'entities': request_entities,
    'entities_to_extend': entities_to_extend,  # NEW
    'entities_to_create': entities_to_create,  # NEW
    # ... rest
}
```

---

### Snippet 3: Plan Modifications vs Creation

```python
# In infer_new_files_needed()

spec_entities = extract_entities_from_spec(
    feature_request, 
    analysis_model=analysis_model,
    existing_entities=existing_entities  # PASS EXISTING
)

files_to_modify = []
files_to_create = []

# Plan modifications for existing entities
for entity in spec_entities.get('entities_to_extend', []):
    entity_file = existing_entities['entity_files'].get(entity)
    if entity_file:
        files_to_modify.append(entity_file)
        print(f"  📝 Will modify: {entity_file}")

# Plan new files for new entities
for entity in spec_entities.get('entities_to_create', []):
    # Create new files for this entity
    new_files = plan_new_entity_files(entity, framework)
    files_to_create.extend(new_files)
    print(f"  📄 Will create files for: {entity}")

return NewFilesPlanningSuggestion(
    files_to_create=files_to_create,
    files_to_modify=files_to_modify,  # NEW
    # ... rest
)
```

---

## 🧪 Test Scenarios

### Scenario 1: Initial Project

```bash
# Create Product API from scratch
python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request-spec dataset/spec/simple-case.md
```

**Expected:**
- ℹ️ No existing entities found
- ✅ Create Product.java, ProductService, ProductController, etc.

---

### Scenario 2: Extend Existing (CRITICAL TEST)

```bash
# Add inventory to existing Product
python3 scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path dataset/codes/springboot-demo \
  --feature-request "Add inventory management with stock tracking. Products should have stock levels, and orders should validate available stock before creation."
```

**Expected:**
- ✓ Discovered 1 existing entity: Product
- ✓ Entity 'Product' exists → will EXTEND
- 📝 Will modify: Product.java
- 📄 Will create: InventoryService.java, InventoryController.java
- ❌ Should NOT create: com.example.inventory domain

---

## 🔍 Debugging Tips

### Check if entities are discovered

Add debug print in `analyze_context()`:
```python
existing_entities = discover_existing_entities(codebase_path, framework, language)
print(f"DEBUG: Found entities: {existing_entities.get('entities', [])}")
```

### Check if comparison happens

Add debug print in `extract_entities_from_spec()`:
```python
print(f"DEBUG: Request entities: {request_entities}")
print(f"DEBUG: Existing entities: {existing_entities.get('entities', [])}")
print(f"DEBUG: To extend: {entities_to_extend}")
print(f"DEBUG: To create: {entities_to_create}")
```

### Check if files are planned correctly

Add debug print in `infer_new_files_needed()`:
```python
print(f"DEBUG: Files to modify: {files_to_modify}")
print(f"DEBUG: Files to create: {files_to_create}")
```

---

## 📊 Success Criteria

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Entity reuse | 0% | 80%+ | ⏳ To implement |
| Modify existing files | Never | When appropriate | ⏳ To implement |
| Code duplication | High | Low | ⏳ To implement |
| Files created for inventory request | 14 | 4-6 | ⏳ To test |

---

## 🚨 Common Pitfalls

1. **Forgetting to pass `existing_entities`**
   - Symptom: No entities discovered, everything created as new
   - Fix: Check all function calls pass `existing_entities` parameter

2. **Entity name mismatch**
   - Symptom: "Product" in request, "ProductEntity" in code → not matched
   - Fix: Add fuzzy matching (Product, ProductEntity, ProductModel all match)

3. **Not detecting entities**
   - Symptom: Entities exist but not discovered
   - Fix: Check search paths match your project structure

4. **Planning creation instead of modification**
   - Symptom: Files planned for creation when should be modified
   - Fix: Check `entities_to_extend` logic in `extract_entities_from_spec()`

---

## 📚 Files to Modify

| File | Function | Change |
|------|----------|--------|
| `flow_analyze_context.py` | NEW: `discover_existing_entities()` | Add function |
| `feature_by_request_agent_v3.py` | `analyze_context()` | Call discovery, store in state |
| `flow_parse_intent.py` | `extract_entities_from_spec()` | Add parameter, comparison logic |
| `flow_parse_intent.py` | `infer_new_files_needed()` | Add parameter, plan modifications |
| `feature_by_request_agent_v3.py` | `parse_intent()` | Pass existing_entities to flow |

---

## 🎯 Next Action

Start with **Task 2**: Implement `discover_existing_entities()` for Java.

```bash
# Open the file
code scripts/coding_agent/flow_analyze_context.py

# Add function after ContextAnalyzer class (around line 500)
# Use Snippet 1 from this document
```

---

**Last Updated:** November 14, 2025  
**Quick Reference Version:** 1.0
