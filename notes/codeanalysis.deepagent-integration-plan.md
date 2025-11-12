# DeepAgents Integration Plan

## Current State
- ✅ `flow_analize_context.py` - Menggunakan **LiteLLM** untuk direct LLM calls
- ✅ `feature_by_request_agent_v3.py` - Simplified version (no LLM)
- ✅ Requirements sudah include `deepagents==0.2.0`

## Opportunity: DeepAgents Integration

### Benefits of DeepAgents
1. **Agent Reasoning** - Better structured thinking
2. **Tool Use** - Can call multiple tools for analysis
3. **Agentic Loop** - Iterative refinement of analysis
4. **State Management** - Better context tracking

### Current LiteLLM Usage in flow_analize_context.py
```python
# Line 129: Direct LiteLLM call
response = litellm.completion(
    model=self.model,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=max_tokens,
    temperature=1.0,
    api_key=os.getenv('LITELLM_VIRTUAL_KEY'),
    api_base=os.getenv('LITELLM_API')
)
```

### Proposed: DeepAgents Integration Points

#### 1. Replace Direct LLM Calls with DeepAgent
- `_reason_about_request()` - Use DeepAgent for request analysis
- `_rank_code_elements()` - Use DeepAgent for intelligent ranking
- `_generate_reasoned_summary()` - Use DeepAgent for summary generation

#### 2. DeepAgent Tool Definitions
```python
TOOLS = {
    "analyze_request": "Parse and understand user feature request",
    "rank_elements": "Determine importance of code elements",
    "suggest_placement": "Suggest where to place new code",
    "generate_summary": "Create context-aware analysis summary"
}
```

#### 3. Integration Pattern
```python
# Before (LiteLLM):
response = litellm.completion(model, messages, ...)

# After (DeepAgents):
agent = DeepAgent(tools=TOOLS, model=llm_model)
result = agent.run(request, tools_config)
```

### Implementation Phases

#### Phase 1: Research & Setup (CURRENT)
- [x] Identify integration points
- [ ] Study deepagents 0.2.0 API
- [ ] Create wrapper for LiteLLM + DeepAgents

#### Phase 2: Integration
- [ ] Replace `_reason_about_request()` with DeepAgent
- [ ] Update `_rank_code_elements()` with agent reasoning
- [ ] Test with sample codebases

#### Phase 3: Optimization
- [ ] Add caching for agent reasoning
- [ ] Optimize tool definitions
- [ ] Add monitoring/logging

### Migration Strategy

**Option A: Wrapper Class (Recommended)**
```python
class DeepAgentAnalyzer(AiderStyleRepoAnalyzer):
    def __init__(self, codebase_path, use_deep_agent=True):
        super().__init__(codebase_path)
        self.use_deep_agent = use_deep_agent
        if use_deep_agent:
            self.agent = self._initialize_deep_agent()
    
    def _reason_about_request(self, user_request):
        if self.use_deep_agent:
            return self._reason_with_deep_agent(user_request)
        else:
            return super()._reason_about_request(user_request)
```

**Option B: Direct Replacement**
- Modify existing `AiderStyleRepoAnalyzer` to use DeepAgents
- Simpler but less flexible

### Testing Strategy
1. Compare DeepAgent results vs LiteLLM results
2. Benchmark performance (speed, token usage)
3. Test with multiple codebases (Go, Java, Python, JS)
4. Validate reasoning quality

### Files to Modify
- `scripts/coding_agent/flow_analize_context.py` - Add DeepAgent integration
- `scripts/coding_agent/feature_by_request_agent_v3.py` - Optional: add DeepAgent variant
- `tests/` - Add integration tests

### Success Metrics
- [ ] DeepAgent successfully reasons about requests
- [ ] Better placeholder understanding
- [ ] Improved code placement suggestions
- [ ] Measurable improvement in analysis quality

## Next Steps
1. Study DeepAgents 0.2.0 documentation
2. Create sample DeepAgent workflow
3. Test with flow_analize_context.py
4. Measure and compare results
