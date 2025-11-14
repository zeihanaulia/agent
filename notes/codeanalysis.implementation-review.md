# Review Implementasi Code Lo (Updated) 🔍

Oke, gw review lagi implementasi terbaru lo. Let me breakdown improvement yang udah lo lakuin dan yang masih perlu diperbaiki.

---

```python
def _execute_selective_analysis(self, plan: Dict[str, Any]) -> Dict[str, Any]:
    /* Lines 12-20 omitted */
```
**Good!** Lo udah actively track tokens. Tapi ada **issue** - explained below.

```python
if request_type in ['feature_implementation', 'refactoring']:
    plan['analyses_to_run'].append('code_placement')
```
**Perfect!** Placement analysis cuma run kalau emang needed.

```python
def _extract_json_from_llm_response(self, llm_response: str) -> Optional[Dict[str, Any]]:
    # Handles markdown blocks, preambles, etc.
```
**Great!** Lo udah handle edge cases dari LLM response.

### 4. **Tree-sitter with Fallback** ✅
```python
def _extract_file_tags(self, content: str, file_path: str) -> list:
    if ext in self.parsers and TREE_SITTER_AVAILABLE:
        try:
            return self._extract_tags_with_tree_sitter(...)
        except Exception as e:
            print(f"  ⚠️ Tree-sitter failed, falling back to regex")
    return self._extract_tags_with_regex(...)
```
**Excellent!** Tree-sitter first, regex fallback.

### 5. **Lightweight File Map Method Added** ✅
```python
def _build_lightweight_file_map(self) -> Dict[str, Dict[str, Any]]:
    /* Lines 53-59 omitted */
```
**Good!** Metadata-only approach.

### 6. **File Selection Methods** ✅
```python
def _select_relevant_files(...) -> list:
    # Try LLM first
    if LLM_AVAILABLE:
        /* Line 68 omitted */
    # Fallback to keywords
    return self._keyword_select_files(...)
```
**Solid!** Two-tier selection strategy.

---

```python
def analyze_with_reasoning(self, user_request: str) -> Dict[str, Any]:
    /* Lines 82-85 omitted */
```

**Problem:** Lo bikin methods `_select_relevant_files()` dan `_load_selected_files()` tapi **NEVER CALLED**!

**Current flow:**
```
analyze_with_reasoning()
  → _execute_selective_analysis()
    → _extract_code_tags()  ❌ Still scans ALL files
    → _basic_filesystem_scan()  ❌ Still walks entire tree
```

**Expected flow:**
```
analyze_with_reasoning()
  → _build_lightweight_file_map()  ✅ Metadata only
  → _select_relevant_files()        ✅ Pick top 10
  → _load_selected_files()          ✅ Load only those 10
  → Analyze ONLY loaded files
```

**Fix:**

```python
def analyze_with_reasoning(self, user_request: str) -> Dict[str, Any]:
    """Main entry point with ACTUAL file selection"""
    
    # Step 1: Build lightweight map (NO content loading)
    print("📂 Building lightweight file map...")
    self.repo_map = self._build_lightweight_file_map()
    
    # Step 2: Reason about request
    print("🤔 Reasoning about request...")
    reasoning = self._reason_about_request(user_request)
    
    # Step 3: Create plan
    print("📋 Creating analysis plan...")
    plan = self._create_analysis_plan(reasoning)
    
    # Step 4: SELECT relevant files (KEY STEP!)
    print("🎯 Selecting relevant files...")
    relevant_files = self._select_relevant_files(
        reasoning,
        self.repo_map,
        max_files=10
    )
    
    # Step 5: LOAD only selected files
    print(f"📖 Loading {len(relevant_files)} selected files...")
    file_contents = self._load_selected_files(relevant_files)
    
    # Step 6: Execute analysis on SELECTED files only
    print("🔍 Analyzing selected files...")
    results = self._execute_selective_analysis(
        plan,
        file_contents=file_contents,  /* Lines 141-142 omitted */
        repo_map=self.repo_map
    )
    
    # Step 7: Generate summary
    summary = self._generate_reasoned_summary(results, reasoning)
    
    return {
        'reasoning': reasoning,
        'selected_files': relevant_files,  /* Lines 150-151 omitted */
        'file_contents': file_contents,
        'results': results,
        'summary': summary,
        'tokens_used': self.current_tokens
    }
```

**Then update `_execute_selective_analysis` to use selected files:**

```python
def _execute_selective_analysis(
    self,
    plan: Dict[str, Any],
    file_contents: Dict[str, str] = None,  # ✅ NEW parameter
    repo_map: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Execute analysis on SELECTED files only"""
    results = {}
    self.current_tokens = 0
    
    for analysis in plan['analyses_to_run']:
        /* Lines 172-193 omitted */
    
    return results

def _extract_tags_from_selected(self, file_contents: Dict[str, str]) -> Dict[str, Any]:
    """Extract tags from SELECTED files only"""
    print(f"  📝 Extracting tags from {len(file_contents)} selected files...")
    
    tags_by_file = {}
    definitions = defaultdict(list)
    references = defaultdict(list)
    
    for file_path, content in file_contents.items():
        /* Lines 206-213 omitted */
    
    return {
        "tags_by_file": tags_by_file,
        "definitions": dict(definitions),
        "references": dict(references),
        "total_tags": sum(len(tags) for tags in tags_by_file.values())
    }

def _basic_info_from_map(self, repo_map: Dict[str, Any]) -> Dict[str, Any]:
    """Get basic info from repo map (no filesystem walking)"""
    context = {
        "project_type": "Unknown",
        "framework": "Unknown",
        "tech_stack": [],
        "main_dirs": [],
        "key_files": [],
        "source_files_count": len(repo_map)
    }
    
    # Detect project type from config files
    has_pom_xml = 'pom.xml' in repo_map
    has_package_json = 'package.json' in repo_map
    # ... rest of detection logic ...
    
    # Count by language
    java_count = sum(1 for f in repo_map.values() if f['language'] == 'java')
    python_count = sum(1 for f in repo_map.values() if f['language'] == 'python')
    # ... etc ...
    
    return context
```

---

```python
def token_count(self, text: str) -> int:
    /* Lines 252-253 omitted */
```

**Problem:** 
- Character count / 4 is **very rough** approximation
- Different for different languages/models
- GPT-4 tokenizer averages ~0.75 chars/token (not 4!)

**Better approach:**

```python
def __init__(self, ...):
    # Try to load actual tokenizer
    try:
        /* Lines 267-268 omitted */
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.use_accurate_counting = True
    except ImportError:
        self.tokenizer = None
        self.use_accurate_counting = False
        print("  ⚠️ tiktoken not available, using rough estimation")

def token_count(self, text: str) -> int:
    """Count tokens accurately if possible"""
    if not text:
        /* Line 278 omitted */
    
    if self.use_accurate_counting and self.tokenizer:
        /* Lines 281-284 omitted */
    
    # Fallback: More accurate estimation
    # GPT models average ~0.75 chars/token (not 4!)
    return max(1, int(len(text) * 0.75))
```

---

```python
# Check budget
budget = plan.get('token_budget', {}).get(analysis, float('inf'))
if tokens_used > budget:
    /* Lines 299-300 omitted */
```

**Problem:** Lo check budget tapi gak actually stop kalau exceeded.

**Fix:**

```python
/* Lines 308-309 omitted */
budget = plan.get('token_budget', {}).get(analysis, float('inf'))
if tokens_used > budget:
    /* Lines 311-315 omitted */

# Also check total budget
if self.current_tokens > self.max_tokens:
    /* Lines 319-321 omitted */
```

---

```python
def analyze_codebase(self) -> Dict[str, Any]:
    /* Lines 330-333 omitted */
```

**Problem:** Method `analyze_codebase()` bypasses the selective analysis entirely.

**Decision needed:**
1. **Option A:** Remove `analyze_codebase()`, use only `analyze_with_reasoning()`
2. **Option B:** Make `analyze_codebase()` also use selective approach
3. **Option C:** Keep it for "full scan" use cases, but rename to `analyze_codebase_full()`

**Recommended: Option A**

```python
# Remove analyze_codebase() entirely
# Always use analyze_with_reasoning() which is smarter

# If you need full scan for some reason, make it explicit:
def analyze_codebase_full(self, max_files: int = None) -> Dict[str, Any]:
    /* Lines 351-356 omitted */
```

---

```python
def _create_real_llm_model(self):
    /* Lines 365-366 omitted */
```

**Observation:** Lo switch dari `litellm` ke `ChatOpenAI`. This is fine, tapi inconsistent dengan docstring yang mention LiteLLM.

**Suggestion:** Pick one and be consistent:

```python
# OPTION 1: Pure LiteLLM (simpler, more direct)
def _create_real_llm_model(self):
    /* Lines 376-394 omitted */

# OPTION 2: LangChain (if you need more features)
# Keep current implementation but update docstring
```

---

```text
User Request: "Add inventory system"
  → analyze_with_reasoning()
    → _extract_code_tags()
      → Walks ALL 1000 files
      → Extracts tags from ALL files
      → Tokens: ~500,000
```

```text
User Request: "Add inventory system"
  → analyze_with_reasoning()
    → _build_lightweight_file_map()  (~1MB metadata, ~100 tokens)
    → _select_relevant_files()        (LLM selection: ~300 tokens)
    → _load_selected_files(10)        (~5,000 tokens for 10 files)
    → /* Line 421 omitted */
Total: /* Lines 422-423 omitted */`

---

Mau gw bikinin **complete working version** dengan semua fixes ini?
