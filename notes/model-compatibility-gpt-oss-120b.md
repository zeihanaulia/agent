# Model Compatibility: GPT-OSS-120b Support

## Issue
- Model: `gpt-oss-120b`
- Problem: Model doesn't follow strict LangChain chat protocol
- Symptom: JSON parsing failures when extracting `<repo_map>` output
- Error: `json.decoder.JSONDecodeError: Expecting value`

## Root Cause
- GPT-OSS-120b returns tool calls in a non-standard format
- Response structure doesn't match LangChain's expected agent protocol
- Tool outputs get mixed with actual response text

Example broken output:
```
<|start|>assistant<|channel|>analysis to=functions.search_files code<|message|>{"root":"", ...}
```

## Solution
Added conditional handling in `scripts/code_analize/analyze_project.py`:

```python
is_gpt120_oss = "gpt-oss-120b" in model_name.lower()

# Temperature adjustment for stability
temperature=0.2 if not is_gpt120_oss else 0.1

# Error handling with fallback
if is_gpt120_oss:
    try:
        repo_map = json.loads(json_str)
    except json.JSONDecodeError:
        # Return fallback repo_map instead of crashing
        repo_map = {
            "structure": "Auto-generated from directory listing",
            "languages": [],
            ...
        }
else:
    # Standard models use strict XML format
    repo_map = json.loads(json_str)
```

## Recommended Models
✅ **Working well:**
- `gpt-5-mini` - Reliable, fast, follows protocol strictly
- `azure/gpt-4` - Stable, comprehensive
- `openai/gpt-4-turbo` - Production grade

❌ **Not recommended for this use case:**
- `azure/gpt-oss-120b` - Non-standard tool calling format

## How to Switch Models
Edit `.env`:
```dotenv
# Disable OSS model
# LITELLM_MODEL=azure/gpt-oss-120b

# Enable recommended model
LITELLM_MODEL=gpt-5-mini
```

## Files Modified
- `scripts/code_analize/analyze_project.py` - Added `is_gpt120_oss` condition
- `.env` - Switched to `gpt-5-mini`
- `answer/answer_agent.py` - Tools support for accurate file reading
- `planner/planner_agent.py` - Enhanced prompts with strict instructions

## Backward Compatibility
✅ Maintained - Code includes `is_gpt120_oss` condition but doesn't break existing models
✅ No changes to core analysis logic
✅ `gpt-5-mini` works without modifications
