# Visual Token Flow Analysis

## Current Token Flow (Problem)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FEATURE REQUEST                                  │
│         "Add order tracking feature for user visibility"            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │   Phase 1: Context Analysis            │
        │   ✓ Read directory structure           │
        │   ✓ Read config files (pom.xml, etc)   │
        │   ✓ List all files (314 files!)        │
        │   ✓ Analyze tech stack                 │
        │                                         │
        │   OUTPUT: context_analysis (50-100K)   │
        │   Time: 120-180 seconds                │
        └────────────┬─────────────────────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
      ▼                             ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│Phase 2: Intent Parsing  │  │Phase 3: Impact Analysis │
│                         │  │                         │
│INPUT:                   │  │INPUT:                   │
│ + context_analysis      │  │ + context_analysis ✗    │ (DUPLICATE)
│   (50-100K) ✗           │  │   (50-100K)             │
│ + feature_request       │  │ + feature_spec          │
│ + ALL file paths        │  │ + ALL file paths        │
│                         │  │                         │
│OUTPUT: Feature Spec     │  │OUTPUT: Architecture     │
│  + Task plan            │  │  Analysis               │
│  + Affected files       │  │                         │
│                         │  │Time: 300-400 seconds    │
│Time: 200-300 seconds    │  │                         │
└──────┬──────────────────┘  └──────┬──────────────────┘
       │                            │
       └────────────┬───────────────┘
                    │
                    ▼
        ┌────────────────────────────────────┐
        │Phase 4: Code Synthesis             │
        │                                     │
        │INPUT:                               │
        │ + context_analysis ✗ (DUPLICATE #3)│
        │   (50-100K)                         │
        │ + impact_analysis                  │
        │ + feature_spec                     │
        │ + ALL Java source files            │
        │                                     │
        │Agent reads 5-10 files × 10K tokens │
        │                                     │
        │OUTPUT: Code changes                │
        │                                     │
        │Time: 300-400 seconds               │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │Phase 5: Execution              │
        │                                 │
        │✓ Apply patches                 │
        │✓ Verify compilation            │
        │                                 │
        │Time: 100-200 seconds           │
        └────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │      TOTAL TOKEN USAGE         │
        │    1,369,427 TOKENS 🔴         │
        │    Latency: 605+ seconds       │
        └────────────────────────────────┘

KEY ISSUES:
  ✗ Context duplicated 4 times (Phases 2, 3, 4)
  ✗ All 314 files always considered
  ✗ No selective file filtering
  ✗ Backend can read unlimited files
  ✗ No caching between phases
```

---

## After Optimization (Solution)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FEATURE REQUEST                                  │
│         "Add order tracking feature for user visibility"            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────────────────────┐
        │   Phase 1: Context Analysis (ENHANCED)                │
        │   ✓ Read directory structure                          │
        │   ✓ Read config files (pom.xml, etc)                 │
        │   ✓ FILTER to relevant files (100 instead of 314)    │
        │   ✓ Analyze tech stack                               │
        │                                                        │
        │   OUTPUT:                                              │
        │   • context_analysis (50-100K) - for reference        │
        │   • cached_components:                                 │
        │     - framework: "Spring Boot 3.x"                    │
        │     - tech_stack: ["Java 17", "Maven", ...]          │
        │     - patterns: ["Service", "Controller", ...]        │
        │   • contexts:                                          │
        │     - for_intent_parsing (5-10K)                      │
        │     - for_impact_analysis (20-30K)                    │
        │     - for_code_synthesis (10-20K)                     │
        │                                                        │
        │   Time: 120-180 seconds (unchanged)                   │
        └────────────┬─────────────────────────────────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
      ▼                             ▼
┌──────────────────────────┐ ┌──────────────────────────┐
│Phase 2: Intent Parsing   │ │Phase 3: Impact Analysis  │
│(OPTIMIZED)               │ │(OPTIMIZED)               │
│                          │ │                          │
│INPUT:                    │ │INPUT:                    │
│ + cache: {framework,     │ │ + cache: {framework,     │
│          tech_stack,...} │ │          tech_stack,...} │
│ + context['intent'] ✓    │ │ + context['impact'] ✓    │
│   (5-10K instead 50K)    │ │   (20-30K instead 50K)   │
│ + feature_request        │ │ + FILTERED files         │
│ + TOP 100 files only ✓   │ │   (100 instead 314)      │
│   (not all 314)          │ │                          │
│                          │ │OUTPUT: Architecture      │
│OUTPUT: Feature Spec      │ │  Analysis (compact)      │
│                          │ │                          │
│Time: 120-150 seconds     │ │Time: 180-220 seconds     │
└──────┬───────────────────┘ └──────┬────────────────────┘
       │                            │
       └────────────┬───────────────┘
                    │
                    ▼
        ┌────────────────────────────────────┐
        │Phase 4: Code Synthesis             │
        │(OPTIMIZED)                          │
        │                                     │
        │INPUT:                               │
        │ + cache: {framework, ...} ✓         │
        │   (no duplicate)                    │
        │ + context['synthesis'] ✓            │
        │   (10-20K instead 50K)              │
        │ + impact_analysis                  │
        │ + feature_spec                     │
        │ + FILTERED Java source files       │
        │                                     │
        │Agent reads 5-10 files with limits  │
        │(controlled via PhaseAwareBackend)  │
        │                                     │
        │OUTPUT: Code changes (same quality) │
        │                                     │
        │Time: 180-220 seconds               │
        └────────────┬────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │Phase 5: Execution              │
        │                                 │
        │✓ Apply patches                 │
        │✓ Verify compilation            │
        │                                 │
        │Time: 100-200 seconds           │
        └────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │      TOTAL TOKEN USAGE         │
        │      600,000 TOKENS ✅          │
        │      (56% reduction!)           │
        │    Latency: 360+ seconds        │
        │    (40% faster!)                │
        └────────────────────────────────┘

KEY IMPROVEMENTS:
  ✓ Context NOT duplicated (used 1 time, components reused)
  ✓ Specialized contexts per phase (5-30K instead of 50-100K)
  ✓ Only TOP 100 relevant files (not all 314)
  ✓ Backend has file read limits
  ✓ Cache components reused across phases
  ✓ Total: 1.36M → 600K tokens (-56%)
```

---

## Token Distribution Comparison

### Current (Problem)

```
PHASE BREAKDOWN:

Phase 1 (Context):    50-100K  |████░░░░░░░░░░░░░░░░ (4%)
Phase 2 (Intent):     350K     |██████████████████░░░░ (26%)
Phase 3 (Impact):     600K     |██████████████████████ (44%)
Phase 4 (Synthesis):  400K     |███████████████░░░░░░░ (29%)
Phase 5 (Execute):    200K     |███████░░░░░░░░░░░░░░░ (15%)
─────────────────────────────────────────────────────────────
TOTAL:                1,600K   🔴 (100%)

PROBLEM AREAS:
  ⚠️ Phase 3 dominates (44%) - context analysis included
  ⚠️ Phase 2 large (26%) - full analysis in prompt
  ⚠️ Phase 4 large (29%) - synthesis includes everything
  ⚠️ Phases 2,3,4 total = 75% due to duplication
```

### After Optimization (Solution)

```
PHASE BREAKDOWN:

Phase 1 (Context):    50-100K  |██████░░░░░░░░░░░░░░░░ (9%)
Phase 2 (Intent):     150K     |██░░░░░░░░░░░░░░░░░░░░ (25%)
Phase 3 (Impact):     350K     |█████░░░░░░░░░░░░░░░░░ (58%)
Phase 4 (Synthesis):  250K     |███░░░░░░░░░░░░░░░░░░░ (42%)
Phase 5 (Execute):    200K     |███░░░░░░░░░░░░░░░░░░░ (33%)
─────────────────────────────────────────────────────────────
TOTAL:                600K     ✅ (100% - 56% REDUCTION)

IMPROVEMENTS:
  ✓ Phase 2 reduced by 57% (350K → 150K)
  ✓ Phase 3 reduced by 42% (600K → 350K)
  ✓ Phase 4 reduced by 38% (400K → 250K)
  ✓ No duplication (context used smartly)
  ✓ Better resource allocation
```

---

## Scale Comparison

```
SMALL PROJECT (springboot-demo, 25 files):
─────────────────────────────────────────
Current:   434,855 tokens (Test 1)
After:     200,000 tokens (-54% reduction)
Savings:   234,855 tokens per feature


MEDIUM PROJECT (casdoor, 314 files):
─────────────────────────────────────
Current:   1,369,427 tokens (Test 2)
After:     600,000 tokens (-56% reduction)
Savings:   769,427 tokens per feature


LARGE PROJECT (10K+ files):
─────────────────────────────
Current:   5,000,000+ tokens (not feasible)
After:     1,500,000 tokens (viable!)
Savings:   3,500,000+ tokens per feature
```

---

## Implementation Timeline

```
WEEK 1: Core Optimization (40-50% benefit)
┌────────────────────────────────────────┐
│ Strategy 1: Context Pruning            │
│ ✓ Split into 3 specialized summaries   │
│ ✓ 60-100K → 35-60K tokens             │
│                                        │
│ Strategy 3: Context Caching            │
│ ✓ Cache components (framework, etc)    │
│ ✓ Reuse across phases                  │
│ ✓ 30-40K additional savings            │
│                                        │
│ Result: 1.36M → 850K tokens (-38%)     │
└────────────────────────────────────────┘

WEEK 2: Enhanced Optimization (+15-20% benefit)
┌────────────────────────────────────────┐
│ Strategy 2: File Relevance Filtering   │
│ ✓ Filter to top 100 files only         │
│ ✓ 314 files → 100 files                │
│ ✓ File listing: 15-20K → 2-3K tokens  │
│ ✓ 200-300K additional savings          │
│                                        │
│ Result: 850K → 600K tokens (-56% total)│
└────────────────────────────────────────┘

OPTIONAL: Advanced Features (+20-30% benefit)
┌────────────────────────────────────────┐
│ Strategy 4: RAG-Style Backend          │
│ ✓ Read constraints per phase           │
│ ✓ File compression (large files)       │
│ ✓ 100-200K additional savings          │
│                                        │
│ Result: 600K → 400K tokens (-71% total)│
└────────────────────────────────────────┘
```

---

## Architecture Optimization

```
BEFORE: Linear Processing with Full Context
┌──────────────┐
│ Full Context │  (50-100K tokens)
│ (50-100K)    │
└────────┬─────┘
         │
         ▼
    ┌─────────────┐
    │ Phase 2     │ ─► Receives: Full context (50-100K)
    │ Intent      │     Uses: Framework, Tech Stack
    └─────────────┘     Wastes: 40-95K tokens
         │
         ▼
    ┌─────────────┐
    │ Phase 3     │ ─► Receives: Full context AGAIN (50-100K)
    │ Impact      │     Uses: File patterns
    └─────────────┘     Wastes: 25-80K tokens
         │
         ▼
    ┌─────────────┐
    │ Phase 4     │ ─► Receives: Full context AGAIN (50-100K)
    │ Synthesis   │     Uses: Code examples
    └─────────────┘     Wastes: 30-90K tokens

WASTE: 95-265K tokens across phases


AFTER: Smart Caching with Specialized Contexts
┌──────────────────────────────────────────┐
│ Context Analysis (Single Pass)           │
│ Output:                                  │
│ • cached_components: {framework, ..}     │
│   (Reusable: 5K tokens)                  │
│                                          │
│ • context['intent']: 5-10K tokens        │
│ • context['impact']: 20-30K tokens       │
│ • context['synthesis']: 10-20K tokens    │
└──────────────┬───────────────────────────┘
               │
      ┌────────┴────────┬────────────┐
      │                 │            │
      ▼                 ▼            ▼
   Phase 2          Phase 3        Phase 4
   Uses cache    Uses cache +     Uses cache +
   + intent      impact context   synthesis
   5-10K total   30-35K total     25-30K total
   (no waste)    (no waste)       (no waste)

SAVED: 95-265K tokens (-40-50%)
```

---

## Cost & Value Projection

```
CURRENT STATE:
─────────────────────────────────────────
Tokens per feature:        1,369,427
Cost per feature:          $684
Features per year:         12
Annual cost:               $8,208
Annual latency:            7,260 seconds (2 hours)


AFTER OPTIMIZATION:
─────────────────────────────────────────
Tokens per feature:        600,000 (-56%)
Cost per feature:          $300 (-56%)
Features per year:         12
Annual cost:               $3,600 (-$4,608!)
Annual latency:            4,320 seconds (1.2 hours)

BENEFITS BREAKDOWN:
┌─────────────────────────────────────────┐
│ 💰 Cost Savings:  $4,608/year            │
│ ⚡ Speed Gain:     2,940 seconds/year    │
│ 📈 Scalability:   Enables 10K+ files    │
│ 🎯 Quality:       Unchanged              │
│ 🛡️  Risk:         Minimal                │
│ 📅 Timeline:      2 weeks                │
└─────────────────────────────────────────┘

ROI ANALYSIS:
─────────────────────────────────────────
Development Cost:        $8,000 (2 weeks @ $100/hr)
Year 1 Savings:          $4,608
Break-even:              ~1.7 years
Multi-year Value:        Sustained indefinitely
```

---

## Risk Assessment

```
STRATEGY 1: Context Pruning
Risk Level: 🟢 MINIMAL
  ✓ Backward compatible (keeps original context)
  ✓ New components generated from existing analysis
  ✓ Can fallback to original context
  ✗ Must ensure summary accuracy

STRATEGY 2: File Filtering  
Risk Level: 🟡 LOW
  ✓ Filtering is independent logic
  ✓ Fallback to all files available
  ✓ Has whitelist for core files
  ✗ May miss some relevant files in edge cases
  ✗ Requires testing with different projects

STRATEGY 3: Context Caching
Risk Level: 🟢 MINIMAL
  ✓ Cache is additive, not replacing
  ✓ Original context still available
  ✓ Can validate cache components
  ✗ Must handle missing components gracefully

MITIGATION:
  ✓ Keep all changes backward compatible
  ✓ Add comprehensive logging
  ✓ Implement fallback mechanisms
  ✓ Run full test suite before & after
  ✓ Have rollback plan ready
```

---

## Success Metrics Dashboard

```
MEASUREMENT CHECKLIST:

Token Usage:
  □ Test 1: 434K → 200K tokens (-54%)
  □ Test 2: 1.36M → 600K tokens (-56%)
  □ Large project: 1.1M → 480K tokens (-56%)

Latency:
  □ Phase 1: ~150s (unchanged)
  □ Phase 2: ~150s → ~90s (-40%)
  □ Phase 3: ~300s → ~180s (-40%)
  □ Phase 4: ~350s → ~210s (-40%)
  □ Total: ~600s → ~360s (-40%)

Code Quality:
  □ Same Java code structure
  □ Same entity relationships
  □ Same service layer logic
  □ E2B tests all pass (8/8)
  □ Compilation succeeds

Behavior Preservation:
  □ Feature spec identical
  □ Implementation plans same
  □ Architecture patterns same
  □ Middleware guardrails active
  □ File generation same

Performance:
  □ Memory usage stable
  □ No new timeouts
  □ No failed requests
  □ Error rate unchanged

Document: ✓ Created (19K words across 3 files)
Status: ✓ Ready for Implementation
```

---

**Visual Reference Created**: 2025-11-05  
**For Details**: See accompanying analysis and implementation guide documents

