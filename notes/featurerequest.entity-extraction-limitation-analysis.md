# Entity Extraction Limitation Analysis: Hardcoded vs Dynamic Approach

**Date:** November 12, 2025  
**Status:** CRITICAL - Hardcoded approach cannot scale to new domains

---

## Problem Statement

The current `extract_entities_from_spec()` function uses a **hardcoded priority_entities list**:

```python
priority_entities = [
    ('inventorytransaction', 'InventoryTransaction'),
    ('product', 'Product'),
    ('customer', 'Customer'),
    ('user', 'User'),
    ('supplier', 'Supplier'),
    # ... 6 more hardcoded entities
]
```

### Real-world Failure Case

**Spec:** `smart-delivery-routing-system.md`  
**Entities in Spec (from "## 🧩 Core Entities" section):**
- Courier ✅ Could be detected
- Vehicle ✅ Could be detected
- PackageDelivery ❌ **MISSED** - not in hardcoded list
- RoutePlan ❌ **MISSED** - not in hardcoded list
- GeoPoint ❌ **MISSED** - not in hardcoded list
- NotificationEvent ❌ **MISSED** - not in hardcoded list

**Actual Output:**
```
📊 Detected entities from spec: Customer
📄 New files planned: 1 files
   - CustomerNotFoundException.java
```

**Expected Output:**
```
📊 Detected entities from spec: Courier, Vehicle, PackageDelivery, RoutePlan, GeoPoint, NotificationEvent, Customer
📄 New files planned: 42 files (6 files per entity)
```

---

## Root Cause Analysis

### Why Hardcoding Failed

1. **Domain Blindness**: Different domains have different entity patterns
   - Inventory domain: Product, Supplier, Warehouse, Order
   - Delivery domain: Courier, Vehicle, RoutePlan, GeoPoint
   - Payment domain: Transaction, Account, Invoice, Receipt
   - HR domain: Employee, Department, Payroll, Attendance

2. **Specification Scanning Limitation**: Only falls back to regex if priority entities don't match
   - When regex extracts: Customer, Courier, Vehicle, PackageDelivery, RoutePlan
   - But `Customer` in priority_entities list matches first → short-circuits to only `['Customer']`
   - Regex fallback never runs because early exit

3. **Scalability Problem**: Adding all possible entities = infinite hardcoded list

---

## Current Implementation Flow (BROKEN)

```
1. Check priority_entities list (hardcoded):
   ✓ 'customer' found in spec_lower → Add 'Customer'
   
2. Early Exit (PROBLEM):
   Since found_entities = ['Customer'], return ['Customer']
   
3. Skip Regex Fallback:
   The regex extraction that would find ALL entities is NEVER EXECUTED
   
Result: Only 1 entity extracted instead of 6
```

---

## Solution Approach: LLM-Based Entity Extraction

### Why LLM-Based Works Better

LLMs excel at understanding context and can recognize:
- **Domain-specific entities** (Courier, Vehicle, RoutePlan)
- **Business concepts** (even with lowercase mentions)
- **Entity relationships** ("couriers responsible for deliveries" → Courier-PackageDelivery relationship)
- **Plural/singular variations** (delivery/deliveries → PackageDelivery entity)

### Proposed Architecture

```
extract_entities_from_spec(feature_request: str)
    ↓
    1. Try Priority Keywords (fast path for known domains)
       - If 3+ priority keywords found → use them
       - If < 3 found → try LLM path
    ↓
    2. LLM-Based Extraction (fallback for new domains)
       - Parse "## 🧩 Core Entities" section if present
       - OR ask LLM: "What are the main business entities?"
       - Filter with excluded_terms
    ↓
    3. Regex Extraction (final fallback)
       - All CamelCase words
       - Filtered by excluded_terms
```

### Code Changes Required

#### Before (Current - BROKEN):
```python
# First pass: Check for priority entities
found_entities = []
for keyword, entity_name in priority_entities:
    if keyword in spec_lower:
        found_entities.append(entity_name)

if found_entities:  # ← EARLY EXIT BUG
    entities = found_entities
else:
    # Regex extraction - NEVER REACHED for smart-delivery spec
```

#### After (Proposed - FIXED):
```python
# First pass: Check for priority entities
found_entities = []
for keyword, entity_name in priority_entities:
    if keyword in spec_lower:
        found_entities.append(entity_name)

# Only short-circuit if we found MANY priority entities (3+)
if len(found_entities) >= 3:
    entities = found_entities
else:
    # Try structured section extraction: "## 🧩 Core Entities"
    section_entities = extract_entities_from_section(feature_request, "Core Entities")
    
    if section_entities:
        entities = section_entities
    else:
        # Try LLM-based extraction (if available)
        if llm_available():
            entities = llm_extract_entities(feature_request, excluded_terms)
        else:
            # Final fallback: Regex
            entities = regex_extract_entities(feature_request, excluded_terms)
```

---

## Implementation Plan

### Phase 1: Structured Section Extraction (IMMEDIATE - No LLM needed)
- Add function: `extract_entities_from_section(spec, section_name)`
- Parses markdown sections like "## 🧩 Core Entities"
- Extract bullet points as entity names
- **Fixes smart-delivery-routing-system spec immediately**

### Phase 2: LLM-Based Extraction (MEDIUM - Uses existing LLM)
- Use existing `create_deep_agent()` call
- Ask: "Extract main business entities from this spec"
- Parse JSON response with entity list
- **Handles arbitrary domain specs**

### Phase 3: Regex Improvement (BONUS - No LLM)
- Improve capitalization detection
- Handle compound names (PackageDelivery, RoutePlan)
- Better POS filtering

---

## Testing Strategy

### Test Case 1: Inventory Domain (Existing - Should Still Pass)
```
Spec: payroll-management-system.md
Expected: Employee, Department, Attendance, Overtime, PayrollTransaction, Payslip, TaxRate
Current: ✓ PASSES (7/7 entities)
```

### Test Case 2: Delivery Domain (Current - FAILS)
```
Spec: smart-delivery-routing-system.md
Expected: Courier, Vehicle, PackageDelivery, RoutePlan, GeoPoint, NotificationEvent
Current: ✗ FAILS (1/6 entities detected)
After Phase 1 Fix: ✓ SHOULD PASS (section extraction)
```

### Test Case 3: Unknown Domain (Future)
```
Spec: new-domain-spec.md (no markdown structure)
Expected: LLM extracts entities
After Phase 2: ✓ SHOULD PASS (LLM extraction)
```

---

## Decision Matrix

| Approach | Speed | Accuracy | Scalability | Cost |
|----------|-------|----------|-------------|------|
| Hardcoded (Current) | Fast ⚡ | Poor ❌ | None 📉 | $0 |
| Structured Parsing | Very Fast ⚡⚡ | Excellent ✅ | Good 📈 | $0 |
| LLM-Based | Slow 🐢 | Excellent ✅ | Excellent ✅ | $ |
| Regex Only | Fast ⚡ | Medium ⚠️ | Medium 📊 | $0 |

**Recommendation:** Phase 1 (Structured) + Phase 2 (LLM fallback) = Best balance

---

## References

- **NLP Best Practices**: Information Extraction patterns (https://en.wikipedia.org/wiki/Information_extraction)
- **LangChain Approach**: Structured output extraction (https://python.langchain.com/docs/guides/structured_output/)
- **Domain Adaptation**: NER systems must be retrained for new domains (Poibeau & Kosseim, 2001)

---

## Next Steps

1. ✅ **Identify Problem** (This document)
2. ⏭️ **Implement Phase 1**: Add `extract_entities_from_section()` function
3. ⏭️ **Test Phase 1**: Verify smart-delivery spec extracts all 6 entities
4. ⏭️ **Implement Phase 2**: Add LLM fallback
5. ⏭️ **Final Testing**: Validate all 3 test cases pass

