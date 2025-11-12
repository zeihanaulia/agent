# Analyze Context Phase Refactoring

**Date**: November 11, 2025  
**File Modified**: `scripts/coding_agent/feature_by_request_agent_v3.py`  
**Status**: ✅ COMPLETED

## Summary

Refactored the `analyze_context` step (Phase 1) dalam `feature_by_request_agent_v3.py` untuk menggunakan implementasi Aider-style repository analyzer dari `flow_analize_context.py`.

## Changes Made

### 1. **Import Addition** (Lines 68-73)
```python
# Import Aider-style context analyzer for Phase 1
try:
    from flow_analize_context import AiderStyleRepoAnalyzer, infer_app_type
    HAS_AIDER_ANALYZER = True
except ImportError:
    HAS_AIDER_ANALYZER = False
    print("⚠️ Aider-style analyzer not available, will use fallback")
```

**Tujuan**: Mengimpor `AiderStyleRepoAnalyzer` class dan `infer_app_type` function dari `flow_analize_context.py` dengan graceful fallback jika module tidak tersedia.

### 2. **Function Replacement** (Lines 481-558)
Mengganti implementasi `analyze_context()` dengan 2 path:

#### Path A: Aider-Style Analysis (Primary)
- Menggunakan `AiderStyleRepoAnalyzer` untuk analisis mendalam
- Mengekstrak code tags menggunakan Tree-sitter atau regex fallback
- Melakukan ranking code elements berdasarkan frequency + PageRank
- Output terstruktur dengan:
  - Filesystem scan results
  - Code analysis (tags, definitions, references)
  - Project structure analysis
  - Architecture insights dengan `infer_app_type()`

#### Path B: Fallback Mode (Jika Aider tidak tersedia)
- Simple filesystem-based detection
- Project type inference dari config files
- File counting (Java, Python, JavaScript)
- Kompatibel dengan existing behavior

## Key Improvements

| Aspek | Sebelum | Sesudah |
|-------|--------|--------|
| Analyzer | Simple filesystem scan | Aider-style with code parsing |
| Code Tags | Tidak ada | ✅ Tag extraction with Tree-sitter |
| Element Ranking | Tidak ada | ✅ Frequency + Page Rank based |
| Architecture Inference | Manual | ✅ Intelligent via `infer_app_type()` |
| Fallback | Implicit error | ✅ Explicit graceful fallback |
| Output Detail | Basic | ✅ Rich with definitions, references |

## Workflow Integration

```
Phase 1: analyze_context (REFACTORED)
  ├─ If HAS_AIDER_ANALYZER:
  │  └─ AiderStyleRepoAnalyzer.analyze_codebase()
  │     ├─ _basic_filesystem_scan()
  │     ├─ _extract_code_tags()          [NEW: Tree-sitter/Regex]
  │     ├─ _analyze_dependencies()
  │     ├─ _analyze_api_patterns()
  │     ├─ _rank_code_elements()         [NEW: Frequency + PageRank]
  │     └─ _analyze_project_structure()
  │
  └─ Else (Fallback):
     └─ Simple filesystem scanning

Output: state["context_analysis"] (Summary String)
Next Phase: parse_intent
```

## Benefits

1. **Better Code Understanding**
   - Extract actual definitions and references dari code
   - Rank code elements by importance
   - More accurate component identification

2. **Framework Detection**
   - Intelligent project type inference
   - Application type detection (Spring Boot Web App, etc)
   - Better architecture understanding

3. **Graceful Degradation**
   - Aider-style primary path
   - Fallback ke simple filesystem scan
   - No breaking changes to existing flow

4. **Future-Ready**
   - Prepared untuk reasoning integration (`analyze_with_reasoning`)
   - Support untuk Tree-sitter advanced parsing
   - Token management ready

## Dependencies

- ✅ `flow_analize_context.py` (primary)
- ✅ `litellm` (optional, untuk LLM reasoning)
- ✅ `tree-sitter*` (optional, untuk advanced parsing)
- ✅ Standard: `os`, `pathlib`, etc

## Implementation Details

### Simplified Import (No Flag Needed)

```python
# Direct import - Aider-style analyzer is required
from flow_analize_context import AiderStyleRepoAnalyzer, infer_app_type

def analyze_context(state: AgentState) -> AgentState:
    analyzer = AiderStyleRepoAnalyzer(codebase_path, max_tokens=2048)
    analysis_result = analyzer.analyze_codebase()
    # ... continue with analysis
```

**Why simplified?**
- ✅ `flow_analize_context.py` adalah direct dependency (selalu ada)
- ✅ Tidak perlu flag complexity jika module pasti tersedia
- ✅ Code lebih clean dan readable
- ✅ Fewer branches = easier to maintain

## Testing

Untuk test, jalankan:

```bash
python scripts/coding_agent/feature_by_request_agent_v3.py \
  --codebase-path "/path/to/project" \
  --feature-request "Add product management"
```

Expected output:
```
🔍 Phase 1: Analyzing codebase context (Aider-style)...
  📊 Using Aider-style repository analyzer...
  ✓ Analysis complete
  ✓ Context saved for next phases
```

## Notes

- ✅ Removed `HAS_AIDER_ANALYZER` flag (unnecessary complexity)
- ✅ Direct import of AiderStyleRepoAnalyzer
- 📊 Output format compatible dengan downstream phases (parse_intent, analyze_impact, dll)

## Next Steps

- [ ] Integrate LLM-powered `analyze_with_reasoning()` ke dalam `parse_intent`
- [ ] Add caching untuk expensive code analysis operations
- [ ] Implement file mention detection untuk selective analysis
- [ ] Add profiling untuk performance optimization
