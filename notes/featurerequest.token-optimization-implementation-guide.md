# Token Optimization Implementation Guide
**Status**: Ready to Implement  
**Priority**: Phase 1 (Strategies 1 & 3) - Start Here  
**Estimated Time**: 1-2 weeks  

---

## 🎯 Strategy 1: Context Pruning (PHASE 1)

### Current Architecture (Problem)
```
Phase 1: Context Analysis
└─ Output: context_analysis (50-100K tokens)
   ├─ Full directory tree
   ├─ All config file contents
   ├─ All file listings
   └─ Complete tech stack analysis

↓ (PROBLEM: Full analysis passed to all downstream phases)

Phase 2: Intent Parsing
├─ Input: context_analysis (50-100K tokens) ← DUPLICATE
├─ Uses: Only architecture overview
└─ Could need: 5-10K tokens instead

Phase 3: Impact Analysis  
├─ Input: context_analysis (50-100K tokens) ← DUPLICATE #2
├─ Uses: File patterns + directories
└─ Could need: 20-30K tokens instead

Phase 4: Code Synthesis
├─ Input: context_analysis (50-100K tokens) ← DUPLICATE #3
├─ Uses: Key file examples + patterns
└─ Could need: 10-20K tokens instead
```

### New Architecture (Solution)
```python
# In Phase 1: Analyze Once, Generate 3 Summaries

def analyze_context(state: AgentState) -> AgentState:
    """Phase 1 - Enhanced with context specialization"""
    
    # Step 1: Perform full analysis (as before)
    agent = create_context_analysis_agent(codebase_path)
    full_analysis = agent.invoke(...)  # 50-100K tokens
    
    # Step 2: NEW - Generate 3 specialized summaries
    context_summaries = generate_specialized_summaries(full_analysis)
    
    state["context_analysis"] = full_analysis  # Keep for reference
    state["contexts"] = {
        "for_intent_parsing": context_summaries.intent_context,      # 5-10K
        "for_impact_analysis": context_summaries.impact_context,    # 20-30K
        "for_code_synthesis": context_summaries.synthesis_context   # 10-20K
    }
    
    return state

def generate_specialized_summaries(full_analysis: str) -> ContextSummaries:
    """
    Extract focused summaries for each phase.
    Uses lightweight regex/parsing, not LLM (free operation).
    """
    
    return ContextSummaries(
        # For Intent Parsing: Just overview
        intent_context=extract_summary(
            full_analysis,
            include=["framework", "tech_stack", "architecture_style", "layer_structure"],
            exclude=["full_file_listings", "line_counts", "detailed_patterns"]
        ),
        
        # For Impact Analysis: File structure + patterns
        impact_context=extract_summary(
            full_analysis,
            include=["file_structure", "directory_patterns", "naming_conventions", 
                    "design_patterns_used", "key_dependencies"],
            exclude=["config_details", "tech_stack_versions"]
        ),
        
        # For Code Synthesis: Concrete examples
        synthesis_context=extract_summary(
            full_analysis,
            include=["key_files_list", "code_patterns", "import_conventions", 
                    "annotation_patterns"],
            exclude=["full_analysis", "all_file_listings"]
        )
    )


# Then use in downstream phases:

def parse_intent(state: AgentState) -> AgentState:
    """Phase 2 - Use specialized context"""
    
    # BEFORE (Problem):
    # prompt = f"CONTEXT:\n{state['context_analysis']}\n..."  # 50-100K tokens
    
    # AFTER (Solution):
    prompt = f"""
CODEBASE CONTEXT:
{state['contexts']['for_intent_parsing']}  # Only 5-10K tokens instead of 50-100K

FEATURE REQUEST:
{state['feature_request']}

...rest of prompt
"""
    
    agent = create_intent_parser_agent()
    result = agent.invoke({"input": prompt})
    
    return state

def analyze_impact(state: AgentState) -> AgentState:
    """Phase 3 - Use specialized context (not full analysis)"""
    
    # BEFORE:
    # full_codebase_info = state['context_analysis']  # 50-100K
    
    # AFTER:
    focused_context = state['contexts']['for_impact_analysis']  # 20-30K
    
    prompt = f"""
CODEBASE STRUCTURE:
{focused_context}

FEATURE REQUEST: {state['feature_request']}

...rest of prompt
"""
    
    agent = create_impact_analysis_agent(codebase_path)
    result = agent.invoke({"input": prompt})
    
    return state

def synthesize_code(state: AgentState) -> AgentState:
    """Phase 4 - Use synthesis-specific context"""
    
    # BEFORE:
    # all_context = state['context_analysis']  # 50-100K
    
    # AFTER:
    code_patterns = state['contexts']['for_code_synthesis']  # 10-20K
    
    prompt = f"""
CODE PATTERNS TO FOLLOW:
{code_patterns}

FEATURE REQUEST: {state['feature_request']}

...rest of prompt
"""
    
    agent = create_code_synthesis_agent(codebase_path)
    result = agent.invoke({"input": prompt})
    
    return state
```

### Expected Impact
```
Before: 1,369,427 tokens (Test 2)
After Phase 1 Pruning:

  Phase 1: 50-100K (unchanged)
  Phase 2: 350K → 150K (200K saved)
  Phase 3: 600K → 350K (250K saved)
  Phase 4: 400K → 250K (150K saved)
  Phase 5: 200K (unchanged)
  ─────────────────────────
  Total: ~900K tokens (-34% = ~470K saved)
```

### Implementation Checklist
- [ ] Add `ContextSummaries` data class
- [ ] Add `generate_specialized_summaries()` function
- [ ] Add `extract_summary()` helper function
- [ ] Update Phase 1 to generate 3 summaries
- [ ] Update Phase 2 prompt to use `contexts['for_intent_parsing']`
- [ ] Update Phase 3 prompt to use `contexts['for_impact_analysis']`
- [ ] Update Phase 4 prompt to use `contexts['for_code_synthesis']`
- [ ] Test: Run Test 1, 2, 3 and compare outputs
- [ ] Measure token usage before/after
- [ ] Document in code with examples

---

## 📦 Strategy 3: Context Caching (PHASE 1)

### Problem
Each phase receives context as RAW STRING in prompt (not reusable).

### Solution
```python
# Add to AgentState

class AgentState(TypedDict):
    """Enhanced with cached context components"""
    
    # Existing
    codebase_path: str
    feature_request: Optional[str]
    context_analysis: Optional[str]
    contexts: Optional[Dict[str, str]]  # From Strategy 1
    
    # NEW - Cached components (not full strings)
    cached_context_components: Optional[Dict[str, Any]] = None


# Create cache structure in Phase 1

def analyze_context(state: AgentState) -> AgentState:
    """Extract cacheable components"""
    
    # After analysis, extract components
    components = extract_cache_components(state["context_analysis"])
    
    state["cached_context_components"] = {
        "framework": components["framework"],              # "Spring Boot 3.x"
        "tech_stack": components["tech_stack"],           # ["Java 17", "Maven", "Spring Data"]
        "architecture_style": components["architecture"], # "Layered MVC"
        "key_directories": components["key_dirs"],        # ["src/main/java", "src/test/java"]
        "file_count": components["file_count"],           # 25
        "detected_patterns": components["patterns"],      # ["Repository", "Service", "Controller"]
    }
    
    return state


# Use cached components instead of text

def parse_intent(state: AgentState) -> AgentState:
    """Use cached components"""
    
    cache = state.get("cached_context_components", {})
    
    # BEFORE:
    # prompt = f"{state['context_analysis']}..."  # Full text (50-100K)
    
    # AFTER:
    prompt = f"""
CODEBASE INFO:
- Framework: {cache.get("framework", "Unknown")}
- Tech Stack: {", ".join(cache.get("tech_stack", []))}
- Architecture: {cache.get("architecture_style", "Unknown")}
- Key Patterns: {", ".join(cache.get("detected_patterns", []))}
- Total Files: {cache.get("file_count", "Unknown")}

{state['contexts']['for_intent_parsing']}

FEATURE REQUEST: {state['feature_request']}
...
"""
    # Now only 15-20K tokens instead of 60-100K
```

### Expected Impact
```
Combined with Strategy 1:

Phase 2: 150K → 90K (60K saved by using cache)
Phase 3: 350K → 280K (70K saved by using cache)
Phase 4: 250K → 180K (70K saved by using cache)

Total additional savings: ~200K tokens
```

### Implementation Checklist
- [ ] Add `cached_context_components` to `AgentState`
- [ ] Add `extract_cache_components()` function
- [ ] Update Phase 1 to extract and cache components
- [ ] Update Phase 2 prompt to use cache + specialized context
- [ ] Update Phase 3 prompt to use cache + specialized context
- [ ] Update Phase 4 prompt to use cache + specialized context
- [ ] Test output quality (should be identical)
- [ ] Measure token usage

---

## 🔍 Strategy 2: File Relevance Filtering (PHASE 2)

### Problem
All files listed and analyzed; most irrelevant to feature request.

### Solution
```python
from typing import List, Dict, Set
import re

class FileRelevanceFilter:
    """Intelligently filter files based on feature request"""
    
    # Framework-specific patterns
    FRAMEWORK_PATTERNS = {
        "java_spring": {
            "model": ["model/", "entity/", "domain/"],
            "service": ["service/", "business/"],
            "controller": ["controller/", "api/", "rest/"],
            "repository": ["repository/", "dao/"],
            "dto": ["dto/", "payload/", "request/", "response/"],
            "config": ["config/", "configuration/"],
            "util": ["util/", "utility/", "helper/"]
        },
        "go": {
            "model": ["model/", "models/"],
            "handler": ["handler/", "handlers/", "api/"],
            "service": ["service/", "services/"],
            "repository": ["repo/", "repository/"],
            "config": ["config/", "configuration/"]
        },
        "python_django": {
            "model": ["models/"],
            "view": ["views/"],
            "serializer": ["serializers/"],
            "url": ["urls/"],
            "form": ["forms/"]
        }
    }
    
    # Keywords for different feature types
    FEATURE_KEYWORDS = {
        "auth": {"auth", "security", "login", "user", "permission", "role"},
        "payment": {"payment", "transaction", "billing", "invoice", "order"},
        "tracking": {"tracking", "status", "history", "notification", "event"},
        "search": {"search", "filter", "query", "index", "elasticsearch"},
        "cache": {"cache", "redis", "memory", "distributed"},
        "async": {"async", "queue", "job", "scheduler", "worker"},
    }
    
    def get_relevant_files(
        self, 
        feature_request: str, 
        all_files: List[str],
        framework: str = "java_spring",
        max_files: int = 100
    ) -> List[str]:
        """
        Filter and rank files by relevance to feature request.
        
        Strategy:
        1. Extract keywords from feature request
        2. Score each file based on keywords + framework patterns
        3. Return top N files by score
        """
        
        # Step 1: Extract keywords from feature
        request_lower = feature_request.lower()
        
        # Find which feature category this is
        feature_category = self._categorize_feature(request_lower)
        keywords = self.FEATURE_KEYWORDS.get(feature_category, set())
        keywords.update(self._extract_keywords(request_lower))
        
        # Step 2: Score each file
        file_scores: Dict[str, float] = {}
        
        for file_path in all_files:
            score = 0.0
            file_lower = file_path.lower()
            
            # Keyword matching
            for keyword in keywords:
                if keyword in file_lower:
                    score += 10.0  # High weight for keyword match
            
            # Framework pattern matching
            for layer, patterns in self.FRAMEWORK_PATTERNS.get(framework, {}).items():
                for pattern in patterns:
                    if pattern in file_lower:
                        # Score differently by layer importance
                        layer_weight = {
                            "model": 8,      # Always relevant
                            "service": 7,    # Usually relevant
                            "controller": 6, # Often relevant
                            "repository": 5, # Sometimes relevant
                            "dto": 4,        # Sometimes relevant
                            "config": 3,     # Rarely relevant
                            "util": 2,       # Usually not relevant
                        }.get(layer, 1)
                        score += layer_weight
            
            # Penalize test files unless explicitly testing
            if "test" in file_lower and "test" not in request_lower:
                score *= 0.5
            
            file_scores[file_path] = score
        
        # Step 3: Rank and limit
        ranked_files = sorted(
            file_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return top N files
        relevant_files = [f[0] for f in ranked_files[:max_files]]
        
        # Ensure we have core files (Service, Repository, Entity)
        core_files = self._ensure_core_files(relevant_files, all_files, framework)
        relevant_files.extend([f for f in core_files if f not in relevant_files])
        
        return relevant_files[:max_files]
    
    def _categorize_feature(self, request: str) -> str:
        """Categorize feature request to feature type"""
        for category, keywords in self.FEATURE_KEYWORDS.items():
            if any(kw in request for kw in keywords):
                return category
        return "general"
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract relevant keywords from text"""
        # Simple: split on non-word chars and get longer words
        words = re.findall(r'\b\w{4,}\b', text.lower())
        # Filter out common stop words
        stop_words = {"that", "this", "with", "from", "have", "been", "should"}
        return {w for w in words if w not in stop_words}
    
    def _ensure_core_files(
        self,
        current_files: List[str],
        all_files: List[str],
        framework: str
    ) -> List[str]:
        """Ensure core architectural files are included"""
        
        core_patterns = {
            "java_spring": ["Application.java", "pom.xml"],
            "go": ["main.go"],
            "python_django": ["settings.py", "manage.py"]
        }
        
        patterns = core_patterns.get(framework, [])
        core_files = []
        
        for pattern in patterns:
            for f in all_files:
                if f.endswith(pattern) and f not in current_files:
                    core_files.append(f)
        
        return core_files


# Usage in Phase 1

def analyze_context(state: AgentState) -> AgentState:
    """Phase 1 - With file filtering"""
    
    codebase_path = state["codebase_path"]
    feature_request = state.get("feature_request", "")
    
    # Get ALL files first
    all_files = list_all_files(codebase_path)  # Could be 100-1000+ files
    
    # NEW: Filter to relevant files only
    filter = FileRelevanceFilter()
    relevant_files = filter.get_relevant_files(
        feature_request,
        all_files,
        framework=detected_framework,
        max_files=100  # Limit to top 100
    )
    
    # Then analyze only relevant files
    state["relevant_files"] = relevant_files
    
    # Perform context analysis on filtered files
    agent = create_context_analysis_agent(codebase_path)
    
    # Modify agent to only analyze relevant_files
    result = agent.invoke({
        "input": f"Analyze {codebase_path}",
        "filter_files": relevant_files  # New parameter
    })
    
    state["context_analysis"] = result
    
    return state
```

### Expected Token Savings
```
Before: All 314 files listed = 15-20K tokens
After: Top 100 files listed = 3-5K tokens

Savings per phase: 10-15K tokens
Phases affected: 1, 2, 3 = 30-45K tokens total saved
```

### Implementation Checklist
- [ ] Create `FileRelevanceFilter` class
- [ ] Add `get_relevant_files()` method with keyword extraction
- [ ] Add `_categorize_feature()` helper
- [ ] Add `_extract_keywords()` helper
- [ ] Add `_ensure_core_files()` helper
- [ ] Update Phase 1 to filter files
- [ ] Update Phase 3 to filter files
- [ ] Test: Verify relevant files selected for known features
- [ ] Test: Run full workflow with filtering
- [ ] Measure: Compare file listings before/after

---

## 📊 Combined Implementation Order

### Week 1: Core Optimization
```
Day 1-2: Implement Strategy 1 (Context Pruning)
  - Add ContextSummaries class
  - Implement generate_specialized_summaries()
  - Update Phase 1 output
  - Update Phase 2, 3, 4 prompts

Day 3: Implement Strategy 3 (Context Caching)
  - Add cached_context_components to AgentState
  - Extract cache components in Phase 1
  - Update Phase 2, 3, 4 to use cache

Day 4: Test & Validate
  - Run Test 1, 2, 3
  - Compare outputs with baseline
  - Measure token usage
  - Document improvements

Day 5: Refine & Polish
  - Fix any issues found
  - Add error handling
  - Document patterns for future
```

### Week 2: Enhanced Optimization
```
Day 1-2: Implement Strategy 2 (File Filtering)
  - Create FileRelevanceFilter class
  - Add keyword extraction
  - Add framework pattern matching
  - Add scoring logic

Day 3: Integration
  - Update Phase 1 to use filter
  - Update Phase 3 to use filter
  - Add fallback for small codebases

Day 4: Test & Validate
  - Run Test 1, 2, 3 with filtering
  - Verify correct files selected
  - Measure additional token savings

Day 5: Documentation
  - Write implementation summary
  - Document lessons learned
  - Prepare for deployment
```

---

## 🔄 Testing Strategy

### Before Changes
```bash
# Baseline measurements
python scripts/feature_by_request_agent_v3.py --feature-request "Test feature"
# Note: token_count, latency, outputs
```

### After Each Implementation
```bash
# Validate behavior preserved
python scripts/test_order_tracking_e2b.py
# Should see: All 8 tests pass

# Measure improvements
python scripts/feature_by_request_agent_v3.py --feature-request "Test feature"
# Compare: token_count reduction, latency improvement
```

### Quality Checks
- [ ] Same code generated (no behavioral change)
- [ ] E2B tests still pass
- [ ] Compilation still works
- [ ] No warnings/errors in output
- [ ] Token usage decreased by expected %
- [ ] Latency decreased accordingly

---

## ⚠️ Rollback Plan

If issues found:
```bash
# Keep original file
git stash

# Revert to last known good
git checkout feature_by_request_agent_v3.py

# Run tests to verify
python scripts/test_order_tracking_e2b.py
```

---

## 📈 Success Metrics

**Phase 1 Target** (After Strategies 1 & 3):
- ✅ 40-50% token reduction
- ✅ Same code quality output
- ✅ E2B tests still pass
- ✅ 10-15% latency improvement

**Phase 2 Target** (After Adding Strategy 2):
- ✅ Additional 15-20% token reduction (54-63% total)
- ✅ Still same behavior
- ✅ 20-30% latency improvement

**Success Criteria**:
- ✅ Test 1: 434K → 200K tokens (54% reduction)
- ✅ Test 2: 1.36M → 600K tokens (56% reduction)
- ✅ Large project: 1.1M → 480K tokens (56% reduction)

---

## 📝 Notes for Implementation

1. **Preserve Backward Compatibility**
   - Keep original `context_analysis` field
   - New optimizations are additive
   - Can revert if needed

2. **Error Handling**
   - Fallback to old behavior if new components missing
   - Log warnings if filtering too aggressive
   - Add validation for cache components

3. **Testing**
   - Run full test suite after each strategy
   - Compare outputs character-for-character
   - Measure tokens and latency

4. **Documentation**
   - Add docstrings explaining cache components
   - Comment filtering logic with examples
   - Document assumptions (framework type, etc)

---

**Next Step**: Start with Strategy 1 implementation (Context Pruning)

