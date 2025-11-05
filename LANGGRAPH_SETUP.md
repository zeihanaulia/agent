# LangGraph Studio Setup - Feature-by-Request Agent V3

## Overview

Setup untuk menjalankan **Feature-by-Request Agent V3** di **LangGraph Studio** dengan dukungan untuk testing dan eksperimen real-time.

## Files Created/Modified

### 1. `langgraph.json` - Konfigurasi LangGraph

Sekarang dengan `input_schema` untuk simplified input:

```json
{
  "python_version": "3.11",
  "dependencies": ["."],
  "graphs": {
    "feature_request_workflow": {
      "path": "langgraph_entry:get_graph",
      "input_schema": {
        "type": "object",
        "properties": {
          "codebase_path": {
            "type": "string",
            "title": "Codebase Path",
            "description": "Absolute path to the codebase to analyze"
          },
          "feature_request": {
            "type": "string",
            "title": "Feature Request",
            "description": "The feature to implement (e.g., 'Add user authentication')"
          },
          "dry_run": {
            "type": "boolean",
            "title": "Dry Run",
            "description": "If true, show changes without applying them",
            "default": true
          }
        },
        "required": ["codebase_path", "feature_request"]
      }
    }
  },
  "env": ".env"
}
```

**Penjelasan:**
- `input_schema`: JSON Schema yang mendefinisikan input fields di Studio UI
- Only `codebase_path` dan `feature_request` yang required
- `dry_run` optional dengan default `true`
- Workflow otomatis populate semua fields lainnya

### 2. `langgraph.json` (Legacy) - Konfigurasi LangGraph
```json
{
  "python_version": "3.11",
  "dependencies": ["."],
  "graphs": {
    "feature_request_workflow": "langgraph_entry:get_graph"
  },
  "env": ".env"
}
```

**Penjelasan (sebelum update):**
- `python_version`: Versi Python yang digunakan
- `dependencies`: Path ke dependencies (current directory)
- `graphs`: Mapping nama graph ke fungsi yang expose graph
- `env`: File environment untuk variables seperti API keys

### 3. `langgraph_entry.py` - Entry Point untuk Studio

Entry point ini:
- ✅ Import workflow creation function tanpa side effects
- ✅ Setup model instance dengan credentials dari `.env`
- ✅ Expose `get_graph()` function untuk LangGraph CLI
- ✅ Fallback ke minimal dummy graph jika ada error
- ✅ Pass `analysis_model` ke workflow agar semua agents dapat menggunakannya

```python
# Handles import-time model setup
analysis_model = ChatOpenAI(
    api_key=SecretStr(api_key),
    model=model_name,
    base_url=api_base,
    temperature=temperature,
)

# Create and expose workflow
feature_request_workflow = create_feature_request_workflow(analysis_model)

def get_graph():
    return feature_request_workflow
```

### 4. `scripts/feature_by_request_agent_v3.py` - Workflow Script

**Key Changes:**
- ✅ Moved `argparse` ke dalam `main()` function (tidak jalankan saat import)
- ✅ Moved model setup ke dalam `main()` function
- ✅ Updated semua agent creation functions agar terima `analysis_model` parameter
- ✅ Updated `create_feature_request_workflow(analysis_model)` agar terima model
- ✅ Node functions menerima model dari workflow context

**Struktur Workflow:**
```
__start__ 
    ↓
analyze_context (Phase 1: Codebase analysis)
    ↓
parse_intent (Phase 2: Feature intent parsing)
    ↓
validate_structure (Phase 2A: Structure validation)
    ↓
analyze_impact (Phase 3: Architecture impact analysis)
    ↓
synthesize_code (Phase 4: Code generation)
    ↓
execute_changes (Phase 5: Apply changes)
    ↓
__end__
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install LangGraph CLI with in-memory runtime
pip install -U "langgraph-cli[inmem]"
```

### 2. Verify Setup

```bash
# Check if langgraph.json exists
ls -la langgraph.json

# Check if langgraph_entry.py exists
ls -la langgraph_entry.py

# Verify environment variables
cat .env | grep LITELLM
```

### 3. Run LangGraph Dev

```bash
cd /Users/zeihanaulia/Programming/research/agent

source .venv/bin/activate

langgraph dev
```

**Expected Output:**
```
✅ Registering graph with id 'feature_request_workflow'
✅ Server started in 4.31s
🎨 Opening Studio in your browser...
URL: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

## Studio Features

Once LangGraph Studio loads, you can:

### 1. **Simplified Input Form**
When you click "Create Run", you'll only see 3 input fields:
- **Codebase Path** (Required) - Full path to the codebase to analyze
- **Feature Request** (Required) - What feature to implement
- **Dry Run** (Optional) - Whether to just preview changes (default: true)

This is configured in `langgraph.json` with the `input_schema` setting.

All other AgentState fields are automatically populated by the workflow.

### 2. **View Workflow Graph**
### 2. **View Workflow Graph**
- See visual representation of all nodes and edges
- Click nodes to inspect their configuration
- View connection routes between phases

### 3. **Create Test Runs**
Instead of the full input form with 13 fields, you now only fill:
```json
{
  "codebase_path": "/Users/zeihanaulia/Programming/research/agent",
  "feature_request": "Add order management system",
  "dry_run": true
}
```

The workflow automatically populates the rest:
```json
{
  "codebase_path": "...",
  "feature_request": "...",
  "context_analysis": null,
  "feature_spec": null,
  "impact_analysis": null,
  "structure_assessment": null,
  "code_patches": null,
  "execution_results": null,
  "errors": [],
  "dry_run": true,
  "current_phase": "initialized",
  "human_approval_required": false,
  "framework": null
}
```

### 4. **Test Different Scenarios**
- Test with `dry_run: true` to see what would happen
- Test with different feature requests
- Test with different codebases

## Running from CLI vs Studio

### From CLI (Direct Execution)
```bash
cd /Users/zeihanaulia/Programming/research/agent

python scripts/feature_by_request_agent_v3.py \
  --codebase-path /Users/zeihanaulia/Programming/research/agent \
  --feature-request "Add order management" \
  --dry-run
```

### From Studio (Interactive Testing)
1. Run `langgraph dev`
2. Open Studio UI
3. Click "Create Run"
4. Fill in initial state
5. Click "Submit"
6. Watch execution in real-time

## Environment Variables Required

Update `.env` file:

```dotenv
# LiteLLM Configuration
LITELLM_API=your_api_base_url_here
LITELLM_VIRTUAL_KEY=your_api_key_here
LITELLM_MODEL=azure/gpt-4o-mini

# LangSmith (Optional, for tracing)
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_TRACING_V2=true
```

## Troubleshooting

### Issue: "workflow not found"
**Solution:** Check `langgraph_entry.py` is in project root and properly formatted

### Issue: "Missing environment variables"
**Solution:** Verify `.env` file has:
- `LITELLM_API`
- `LITELLM_VIRTUAL_KEY`
- `LITELLM_MODEL`

### Issue: "Import error on startup"
**Solution:** The fallback minimal graph should load. Check the error message for actual cause.

### Issue: Port 2024 already in use
**Solution:** Kill existing process or use different port:
```bash
lsof -i :2024
kill -9 <PID>

# Or use different port
langgraph dev --port 2025
```

## Next Steps

1. **Add Tool Integrations:** Add more specialized tools to agents
2. **Add Memory:** Implement conversation memory for multi-turn interactions
3. **Add State Persistence:** Save workflow state to database
4. **Add Webhooks:** Trigger workflows from external systems
5. **Add Testing:** Create test cases for workflow validation

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Studio Guide](https://langchain-ai.github.io/langgraph/studio/)
- [LangChain Python SDK](https://python.langchain.com/)
