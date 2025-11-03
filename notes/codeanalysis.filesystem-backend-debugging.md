# FilesystemBackend Debugging & Troubleshooting

## 🐛 Issue: Agent Stuck in Pending State

### Symptoms
- Agent shows `Pending` status in LangSmith
- No progress in tool execution
- Agent doesn't respond or times out

### Root Causes & Solutions

#### 1. **Model API Configuration Issues** ❌
**Problem**: API key or base URL is invalid/missing

**Fixes**:
```bash
# Check environment variables
echo "LITELLM_MODEL=$LITELLM_MODEL"
echo "LITELLM_API=$LITELLM_API"
echo "LITELLM_VIRTUAL_KEY=***" # (don't print actual key)

# Verify .env file exists and has correct values
cat .env | grep -E "LITELLM_|LANGSMITH_"
```

**Code Fix** (already applied):
```python
# Validate environment before creating model
if not api_key or not api_base:
    raise ValueError("Missing required environment variables")
    
# Use SecretStr for API key
analysis_model = ChatOpenAI(
    api_key=SecretStr(api_key),  # ✅ Correct
    # api_key=lambda: api_key,   # ❌ Avoid lambda
)
```

#### 2. **FilesystemBackend Not Initialized Correctly** ❌
**Problem**: Backend failed to initialize with root_dir

**Fixes**:
```python
# ✅ Validate path before backend initialization
if not os.path.exists(codebase_path):
    raise ValueError(f"Path does not exist: {codebase_path}")

if not os.path.isdir(codebase_path):
    raise ValueError(f"Path is not a directory: {codebase_path}")

# Convert to absolute path
codebase_path = os.path.abspath(codebase_path)

# Initialize backend with error handling
try:
    backend = FilesystemBackend(root_dir=codebase_path)
except Exception as e:
    raise RuntimeError(f"Backend initialization failed: {str(e)}") from e
```

#### 3. **Agent Initialization Failure** ❌
**Problem**: create_deep_agent() fails silently or returns invalid agent

**Fixes**:
```python
# ✅ Add error handling to agent creation
try:
    agent = create_deep_agent(
        system_prompt=analysis_prompt,
        model=analysis_model,
        backend=backend,
    )
except Exception as e:
    raise RuntimeError(f"Agent creation failed: {str(e)}") from e
```

#### 4. **Infinite Loop or Tool Execution Issues** ❌
**Problem**: Agent calls tools but never responds

**Possible Causes**:
- Tools take too long to respond
- Agent is stuck waiting for tool results
- Backend tools not working as expected

**Debug Strategy**:
```bash
# 1. Check LangSmith trace for tool calls
#    Look at: Tools → grep, ls, read_file calls
#    Check if they have responses or are stuck

# 2. Run with verbose mode to see tool calls
#    Check if glob/grep patterns work

# 3. Test backend tools directly (next section)
```

### Testing FilesystemBackend Tools Directly

Create a test script `test_backend.py`:

```python
from deepagents.backends import FilesystemBackend
import os

# Test path
test_path = "/path/to/project"

print(f"Testing FilesystemBackend with: {test_path}")
print(f"Path exists: {os.path.exists(test_path)}")
print(f"Is directory: {os.path.isdir(test_path)}")

# Initialize backend
try:
    backend = FilesystemBackend(root_dir=test_path)
    print("✅ Backend initialized successfully")
except Exception as e:
    print(f"❌ Backend init failed: {e}")
    exit(1)

# Test ls tool
try:
    result = backend.ls_info("/")
    print(f"✅ ls_info('/') returned {len(result)} items")
except Exception as e:
    print(f"❌ ls_info failed: {e}")

# Test glob tool
try:
    result = backend.glob_info("**/*.py", path="/")
    print(f"✅ glob_info found {len(result)} Python files")
except Exception as e:
    print(f"❌ glob_info failed: {e}")

# Test grep tool
try:
    result = backend.grep_raw("TODO", path="/", glob="**/*.py")
    print(f"✅ grep_raw found results: {len(result)} matches")
except Exception as e:
    print(f"❌ grep_raw failed: {e}")
```

Run it:
```bash
python test_backend.py
```

### Debugging Checklist

- [ ] Environment variables set correctly
- [ ] API key is valid and not expired
- [ ] Codebase path exists and is absolute
- [ ] LangSmith trace shows tool calls being made
- [ ] Backend tools respond with results (not stuck)
- [ ] No infinite loops in tool execution
- [ ] Model can generate valid tool calls
- [ ] Agent has max_iterations limit (if applicable)

### LangSmith Trace Analysis

When checking LangSmith trace:

1. **Look at the Tool Call Chain**:
   ```
   ✅ Good: ls → read_file → glob → grep → response
   ❌ Bad: ls → (stuck) or ls → error → (no recovery)
   ```

2. **Check Tool Response Times**:
   ```
   ✅ Good: Each tool 0.1-2s
   ❌ Bad: Tool takes 60+ seconds or infinite
   ```

3. **Look for Error Messages**:
   - `Invalid regex pattern`
   - `File not found`
   - `Permission denied`
   - `Path escapes root_dir`

4. **Check Model Responses**:
   - Is model generating valid tool calls?
   - Are tool calls properly formatted?
   - Does model handle tool errors correctly?

### Common Error Messages & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Path escapes root_dir` | Tool trying to access outside root | Check system prompt - may be too permissive |
| `Invalid regex pattern` | Bad regex in grep | Ensure pattern is valid Python regex |
| `File not found` | File doesn't exist in root_dir | Use glob first to find files |
| `Permission denied` | No read permission | Check OS file permissions |
| `Empty result` | No matches found | Pattern may be too specific |

### Comparison: Custom Tools vs FilesystemBackend

**Custom Tools Issues**:
- ✅ Same basic functionality
- ❌ Manual error handling
- ❌ Manual path validation
- ❌ No security out-of-box
- ❌ Need to debug all issues manually

**FilesystemBackend Issues**:
- ✅ All error handling built-in
- ✅ Security features automatic
- ✅ Professional tool implementation
- ❌ Requires understanding BackendProtocol
- ❌ Need to properly configure root_dir

### Why FilesystemBackend Might Seem "Stuck"

1. **Model Configuration Issue**
   - Using lambda for api_key ❌ (Fixed)
   - Wrong API endpoint
   - Invalid model name

2. **Backend Not Responding**
   - Path doesn't exist
   - No read permissions
   - OS filesystem issues

3. **Tool Execution Issues**
   - Regex patterns too complex
   - Large files taking time
   - Network issues with remote FS

4. **Agent Logic Issues**
   - System prompt too verbose
   - Too many tool calls
   - Circular tool dependencies

### Verification Steps

```bash
# 1. Test Python imports
python -c "from deepagents.backends import FilesystemBackend; print('✅ Import OK')"

# 2. Check environment
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'MODEL: {os.getenv(\"LITELLM_MODEL\")}'); print(f'API: {os.getenv(\"LITELLM_API\")}')"

# 3. Test backend directly (use test_backend.py above)

# 4. Run with increased verbosity
LANGSMITH_TRACING=true python scripts/code_analysis.py

# 5. Check LangSmith project for details
#    https://smith.langchain.com/
```

---

## ✅ Fixes Applied in v2

1. **Model Initialization**
   - Changed: `api_key=lambda: api_key` → `api_key=SecretStr(api_key)`
   - Added: API key validation before model creation

2. **Path Handling**
   - Added: Path existence check
   - Added: Directory validation
   - Added: Conversion to absolute path

3. **Backend Initialization**
   - Added: Try-except error handling
   - Added: Detailed error messages

4. **Agent Invocation**
   - Added: Exception handling for timeouts
   - Added: Better error reporting
   - Added: Debugging suggestions

5. **Result Extraction**
   - Added: Result structure validation
   - Added: Detailed diagnostic messages
   - Added: Hints for troubleshooting

---

**Last Updated**: November 3, 2025
**Framework**: LangChain DeepAgents v0.2+
**Reference**: See `codeanalysis.filesystem-backend-*.md` for full documentation
