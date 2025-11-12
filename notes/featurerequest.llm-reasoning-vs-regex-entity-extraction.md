# LLM Reasoning vs Regex: Bagaimana LLM Memahami Entities

**Date:** November 12, 2025  
**Status:** Analysis & Understanding  
**Language:** Indonesian (penjelasan teknis dalam bahasa Indonesia)

---

## Pertanyaan Awal

> "Regex juga gak bener, bagaimana Claude code bisa paham apakah dibalik layar ada regex juga? Kan tidak itu semua LLM yang melakukan reasoning"

**Terjemahan:** Regex juga tidak bekerja dengan baik, bagaimana Claude Code bisa memahami? Apakah di belakang layar ada regex juga? Tidak, LLM melakukan reasoning (penalaran)

---

## Penjelasan: Bagaimana LLM Bekerja (Semantic Reasoning)

### 1. REGEX = Pattern Matching (Deterministic)

**Cara Kerja Regex:**
```python
# Regex adalah PATTERN MATCHING - deterministic, tidak ada "pemahaman"
pattern = r'\b([A-Z][a-z]+)\b'
matches = re.findall(pattern, text)

# Contoh:
text = "The Courier delivered the Package to the Customer"
# Regex hanya melihat: "The", "Courier", "Package", "Customer"
# Tidak tahu: Courier = ENTITY, "The" dan "Package" = juga ENTITY tapi tidak memulai dengan huruf besar
```

**Limitation Regex:**
- ❌ Hanya cocok dengan PATTERN fisik (huruf besar, spasi, karakter)
- ❌ Tidak bisa membedakan "Courier" (entity) vs "Customer" (juga entity)
- ❌ Gagal dengan lowercase: "courier", "package", "customer"
- ❌ Gagal dengan variasi: "the courier's vehicle", "a package delivery"
- ❌ Tidak memahami KONTEKS atau SEMANTIK

### 2. LLM = Semantic Reasoning (Non-deterministic)

**Cara Kerja LLM (Claude, GPT-4, dst):**

```
INPUT: "Build a system for couriers delivering packages"

LLM THINKING (Transparent via Extended Thinking):
1. "Membaca teks secara semantik (makna, bukan hanya pola)"
2. "Mengidentifikasi konsep bisnis:
   - 'couriers' = orang/aktor dalam sistem
   - 'packages' = barang yang dikelola
   - 'delivering' = aksi/proses"
3. "Reasoning tentang entity:
   - Courier = ENTITY (ada dalam banyak use case: dispatch, tracking, payment)
   - Package = ENTITY (ada dalam: tracking, delivery, confirmation)
   - Customer = ENTITY (implied: who receives the package)"
4. "Mengeluarkan reasoning:"

   Courier adalah entity karena:
   - Disebutkan multiple times dalam spec
   - Merupakan ACTOR dalam sistem (driver, driver assignment)
   - Memiliki properties: name, location, vehicle, status
   - Memiliki relationships: assigned_deliveries, route_plan

OUTPUT: ["Courier", "Package", "Customer", "DeliveryJob", "Vehicle", "Route"]
```

**Key Insight:**
- ✅ LLM membaca SEMANTIK (makna), bukan hanya pola
- ✅ LLM bisa memahami konteks: "courier" lowercase = sama dengan "Courier" uppercase
- ✅ LLM bisa inference: "driver" = similar to "Courier" (sinonim)
- ✅ LLM tahu entity properties dan relationships
- ✅ LLM bisa reason: "apakah ini entity atau adjective?"

---

## Cara Kerja LLM Semantic Extraction

### Architecture: Structured Output dalam LangChain

LangChain menggunakan **Structured Output** feature yang memaksa LLM untuk return JSON dalam format tertentu:

```python
# STRUCTURED OUTPUT approach (LangChain v1.0+)
from pydantic import BaseModel

class EntityExtractionResult(BaseModel):
    """Schema yang diharapkan dari LLM"""
    entities: list[str]  # ["Courier", "Vehicle", "Package", ...]
    reasoning: str       # Penjelasan why
    confidence: float    # 0-1

# LLM HARUS return sesuai schema ini
model_with_structure = llm.with_structured_output(
    EntityExtractionResult,
    method="json_schema"  # Gunakan provider's structured output
)

response = model_with_structure.invoke("""
Extract main business entities from:
"Build a delivery routing system for couriers managing packages..."
""")

# Output:
# EntityExtractionResult(
#   entities=["Courier", "Package", "Vehicle", "RoutePlan", "GeoPoint", "NotificationEvent"],
#   reasoning="These are core domain concepts mentioned multiple times...",
#   confidence=0.95
# )
```

### Behind the Scenes: Tiga Metode

LangChain mendukung 3 metode untuk structured output:

| Method | Bagaimana | Kecepatan | Cost |
|--------|-----------|----------|------|
| **json_schema** | Provider native (OpenAI, Anthropic) - LLM forced output JSON schema | ⚡ Fast | $$ |
| **function_calling** | LLM calls a "tool" yang return structured data | ⚡ Fast | $ |
| **json_mode** | LLM hanya generate valid JSON (deprecated) | ⚡ Fast | $ |

**OpenAI/Claude Native Support:**
```
User: "Extract entities"
           ↓
LLM Backend: "I'll use my native structured output mode"
           ↓
Output constraint: "Return ONLY valid JSON matching schema"
           ↓
Result: 100% JSON compliance (NO parsing needed)
```

---

## Perbedaan Fundamental

### Regex Approach
```python
def extract_with_regex(text):
    # Pattern: uppercase letter followed by lowercase letters
    pattern = r'\b([A-Z][a-z]+)\b'
    return re.findall(pattern, text)

# Input: "smart delivery and route optimization for couriers"
# Output: []  # EMPTY! Karena tidak ada PascalCase
# Problem: Regex tidak memahami semantik
```

### LLM Approach (Claude/GPT-4)
```python
def extract_with_llm(text):
    # Send ke Claude dengan instruction
    prompt = f"""
    Analyze this text and extract business entities.
    Return JSON: {{"entities": ["Entity1", "Entity2", ...]}}
    
    Text: {text}
    """
    
    response = llm.invoke(prompt)
    # Claude UNDERSTANDS:
    # - "delivery" = refers to DeliveryJob entity
    # - "route" = refers to RoutePlan entity  
    # - "couriers" = refers to Courier entity (plural)
    # - These are core domain concepts
    
    return ["Delivery", "Route", "Courier", "Optimization", "Vehicle"]
    # Tidak hanya blind pattern matching!
```

---

## Cara Claude Code Memahami Entities

### Mechanism: Transformer + Attention

Claude (dan LLM lainnya) adalah **Transformer-based model**:

```
1. TOKENIZATION: Text dipecah menjadi token (subword units)
   "couriers delivering packages" →
   ["couriers", "delivering", "packages"]

2. EMBEDDING: Setiap token diubah jadi vector (representation matematika)
   "Courier" → [-0.23, 0.45, -0.78, ..., 0.12]
   "Vehicle" → [0.11, -0.34, 0.56, ..., 0.89]
   
   Vector ini capture MEANING (semantik):
   - Courier ≈ nearby vectors: "driver", "person", "actor"
   - Vehicle ≈ nearby vectors: "car", "transport", "asset"

3. ATTENTION: Model lihat relationships antar tokens
   Query: "Extract entities"
   Claude's attention:
   - Focus on: nouns, repeated words, domain-specific terms
   - De-focus: articles ("the"), prepositions ("for"), adjectives
   
4. CONTEXT REASONING:
   If seen in training: many examples of "Courier" as entity
   Claude bisa inference: "courier" (lowercase) = juga entity

5. OUTPUT GENERATION:
   Based on reasoning, generate JSON array entities
```

### Contoh Real: Smart Delivery Spec

```
Input Text:
"Build a system for couriers managing deliveries with optimized routes..."

Claude's Internal Reasoning:
┌─────────────────────────────────────────────────────────┐
│ TOKEN ANALYSIS:                                         │
│ - "couriers" → NOUN + ROLE (repeated 5x in spec)     │
│ - "deliveries" → NOUN + CORE-CONCEPT (10x mentions)   │
│ - "routes" → NOUN + OPTIMIZATION-CONCEPT (8x mentions)│
│ - "optimization" → ADJECTIVE-LIKE + PROCESS           │
│                                                         │
│ ENTITY CLASSIFICATION:                                 │
│ - couriers → Courier ✓ (repeated, core role)          │
│ - deliveries → Delivery or PackageDelivery ✓          │
│ - routes → RoutePlan ✓ (optimization context)        │
│ - vehicles → Vehicle ✓ (inferred from "couriers")    │
│ - customers → Customer ✓ (inferred from "delivering")│
│ - locations → GeoPoint ✓ (inferred from "routes")   │
│ - notifications → Notification ✓ (inferred from "status updates")
└─────────────────────────────────────────────────────────┘

Output: ["Courier", "Delivery", "RoutePlan", "Vehicle", 
         "Customer", "GeoPoint", "Notification"]
```

**Mengapa Claude bisa paham?**
1. ✅ **Training data:** Trained on millions of specs dan entity extraction examples
2. ✅ **Semantic vectors:** Memahami relationships antar kata (courier ≈ driver ≈ person)
3. ✅ **Pattern recognition:** Tahu pattern entity extraction dari training
4. ✅ **Context understanding:** Bisa reasoning tentang domain knowledge
5. ✅ **Structured output:** Forced ke JSON schema yang predictable

---

## Mengapa Regex TIDAK Bisa Kerja untuk Smart Delivery

### Masalah 1: Lowercase Entity Names

```
Spec text: "couriers delivering packages across cities"

Regex: r'\b([A-Z][a-z]+)\b'
Match: []  # EMPTY

Why regex gagal:
- "couriers" dimulai dengan 'c' (lowercase)
- Pattern hanya match huruf besar di awal
- Tidak bisa detect: "courier" = "Courier" (sama entity, beda casing)

LLM approach:
- Claude: "Oh, 'couriers' = plural dari 'courier' = business concept = ENTITY"
- Auto-capitalize: "Courier"
```

### Masalah 2: Entities Not in Priority List

```
Hardcoded priority list dalam code:
['customer', 'user', 'product', 'order', 'warehouse', 'supplier', ...]

Smart delivery spec:
'courier', 'vehicle', 'packagedelivery', 'routeplan', 'geopoint', 'notification'

Result: ❌ MISMATCH - tidak ada di list, tidak terdeteksi

Regex fallback:
r'\b([A-Z][a-z]+)\b' 
- Hanya match PascalCase
- Spec uses lowercase = tidak ketemu

LLM approach:
- Tidak peduli dengan priority list
- Semantic understanding: "courier ini adalah entity di domain delivery"
- Auto-detect dari context
```

### Masalah 3: No Semantic Understanding

```
Regex tidak bisa distinguish:

Text: "The delivery job requires detailed planning"

Regex output: ["The", "Delivery", "Job", "Requires", "Detailed", "Planning"]
# ERROR: "The" dan "Requires" bukan entity!

LLM output: ["Delivery", "Job", "Planning"]
# atau: ["PackageDelivery", "DeliveryJob", "RoutePlan"]
# Bisa rename dan combine berdasarkan semantic understanding
```

---

## Architecture Recommendation: Hybrid Approach

```python
def extract_entities_hybrid(spec: str) -> List[str]:
    """
    Multi-strategy entity extraction menggunakan:
    1. Structured Section Parsing (fastest, no LLM)
    2. LLM Semantic Extraction (accurate, uses tokens)
    3. Regex Fallback (lowest quality, but always works)
    """
    
    # STRATEGY 1: Try structured section (no inference needed)
    entities = extract_from_section(spec, "Core Entities")
    if entities:
        return entities  # Found 6/6 entities, done!
    
    # STRATEGY 2: Use LLM for semantic extraction (best accuracy)
    try:
        entities = extract_via_llm(spec)
        if entities:
            return entities  # LLM found entities via reasoning
    except:
        pass  # LLM not available
    
    # STRATEGY 3: Fall back to regex (lowest quality)
    return extract_via_regex(spec)
```

### Why This is Better

| Strategy | Speed | Accuracy | Cost | Deterministic |
|----------|-------|----------|------|---------------|
| Structured Parsing | ⚡⚡⚡ | ✅ Excellent | $0 | ✓ Yes |
| LLM Semantic | 🐢 | ✅ Excellent | $$$ | ✗ No |
| Regex | ⚡⚡ | ❌ Poor | $0 | ✓ Yes |

**Best Practice:**
1. **Deterministic first** (Structured): Fast, cheap, predictable
2. **Then semantic** (LLM): Accurate for complex specs
3. **Finally fallback** (Regex): Always has something

---

## References

### LangChain Structured Output
- https://python.langchain.com/docs/guides/structured_output/
- Method: `json_schema` (OpenAI), `function_calling` (all providers), `json_mode` (deprecated)
- Pydantic models untuk schema definition
- Automatic validation dan parsing

### Claude API Documentation
- https://docs.anthropic.com/claude/reference/getting-started-with-the-api
- Core capability: **Tool use** (untuk structured output)
- Extended thinking: Transparent reasoning process
- Native structured output support via API

### Information Extraction Theory
- https://en.wikipedia.org/wiki/Information_extraction
- NER (Named Entity Recognition) vs Entity Extraction
- Gazetteer-based vs ML-based extraction
- Semantic vs pattern-based approaches

### Transformer Architecture (Behind LLM)
- Attention mechanism: Fokus pada relationships antar kata
- Embeddings: Semantic vectors (mathematical representation)
- Token predictions: Auto-regressive generation

---

## Key Takeaways

### 1. Regex = Blind Pattern Matching
```
❌ Hanya cocok dengan pattern fisik
❌ Tidak memahami semantik/makna
❌ Gagal dengan case variations
❌ Tidak scalable untuk new domains
```

### 2. LLM = Semantic Understanding
```
✅ Memahami MAKNA dan KONTEKS
✅ Bisa handle case variations (courier, Courier, COURIER)
✅ Semantic relationships (courier ≈ driver ≈ person)
✅ Scalable untuk arbitrary domains
✅ Reasoning transparent (extended thinking)
```

### 3. Best Practice Architecture
```
Structured Parsing (Fastest)
    ↓ (if not found)
LLM Semantic Extraction (Most Accurate)
    ↓ (if LLM unavailable)
Regex Fallback (Always Works)
```

### 4. Why Current Approach Fails
```
Priority Entity List:
- inventory, product, customer, user, supplier, etc.
- ❌ Hardcoded untuk inventory domain
- ❌ Tidak scalable ke delivery domain

Smart Delivery Spec:
- courier, vehicle, packagedelivery, routeplan, geopoint, notification
- ❌ Tidak di priority list
- ❌ Regex fallback gagal (lowercase)
- ❌ Need semantic understanding

Solution:
- ✅ Extract dari structured "## 🧩 Core Entities" section
- ✅ Or use LLM untuk semantic understanding
- ✅ Remove hardcoded priority list
```

---

## Implementasi Next Step

1. **Structured Section Parsing** (Already done)
   - Parse markdown `## 🧩 Core Entities` section
   - Extract bullet points as entity names
   - No LLM needed, deterministic

2. **LLM-Based Extraction** (Need OpenAI/Anthropic API)
   - Use LangChain's `with_structured_output()`
   - Send spec to Claude with entity extraction instruction
   - Return Pydantic model dengan list entities

3. **Remove Hardcoding**
   - Delete `priority_entities` list
   - No more domain-specific tuning needed
   - Auto-discover entities dari setiap spec

