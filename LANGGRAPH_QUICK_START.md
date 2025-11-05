# LangGraph Studio - Quick Start Guide

## 🚀 Start Dev Server

```bash
cd /Users/zeihanaulia/Programming/research/agent
source .venv/bin/activate
langgraph dev
```

**Wait for output:**
```
✅ Registering graph with id 'feature_request_workflow'
✅ Server started in 4.31s
🎨 Opening Studio in your browser...
```

## 📝 Studio Input Form

When you create a run, fill only 3 fields:

| Field | Type | Required | Example |
|-------|------|----------|---------|
| **Codebase Path** | string | ✅ Yes | `/Users/zeihanaulia/Programming/research/agent` |
| **Feature Request** | string | ✅ Yes | `Add user authentication with JWT` |
| **Dry Run** | boolean | ❌ No | `true` (default) |

**That's it!** The workflow auto-populates other fields.

## 🔄 Workflow Phases

```
1️⃣  analyze_context         → Analyze codebase structure & tech stack
2️⃣  parse_intent            → Parse feature requirements
2️⃣A validate_structure      → Check project structure compliance  
3️⃣  analyze_impact          → Identify affected files & patterns
4️⃣  synthesize_code         → Generate implementation code
5️⃣  execute_changes         → Apply changes or show dry run
✅  handle_error/end_workflow → Finish execution
```

## 📊 Monitor Execution

In Studio UI:
1. Click any node to inspect inputs/outputs
2. Step through execution
3. View agent reasoning and tool calls
4. Check state transformations between phases

## 🔧 CLI vs Studio

### CLI (Direct)
```bash
python scripts/feature_by_request_agent_v3.py \
  --codebase-path /path/to/codebase \
  --feature-request "Add order management" \
  --dry-run
```

### Studio (Interactive)
1. `langgraph dev`
2. Fill 3 fields in UI
3. Click Submit
4. Watch real-time execution with debugging

## ⚙️ Environment Setup

Create or update `.env`:
```dotenv
LITELLM_API=your_api_base_url_here
LITELLM_VIRTUAL_KEY=your_key_here
LITELLM_MODEL=azure/gpt-4o-mini
```

## 📋 Files

| File | Purpose |
|------|---------|
| `langgraph.json` | Configuration with simplified input schema |
| `langgraph_entry.py` | Entry point for Studio |
| `scripts/feature_by_request_agent_v3.py` | Main workflow implementation |
| `LANGGRAPH_SETUP.md` | Full documentation |

## 🐛 Troubleshooting

**"workflow not found"**
- Check `langgraph.json` is in project root
- Run `langgraph dev` from correct directory

**"Port 2024 already in use"**
```bash
lsof -i :2024
kill -9 <PID>
```

**"Missing environment variables"**
- Verify `.env` has LITELLM_API and LITELLM_VIRTUAL_KEY
- Run from same directory as `.env`

## 🎯 Example Run

1. Start server:
   ```bash
   langgraph dev
   ```

2. Fill input form:
   ```
   Codebase Path: /Users/zeihanaulia/Programming/research/agent
   Feature Request: Add REST API endpoint for user profile management
   Dry Run: true
   ```

3. Click Submit

4. Watch 5+ phases execute automatically:
   - Analyze your codebase
   - Parse requirements
   - Validate structure
   - Analyze impact
   - Generate code
   - Show preview

## 📚 More Info

See `LANGGRAPH_SETUP.md` for complete documentation.
