# Chapter 2 — Introducing E2B Sandbox

## Ringkasan Umum
Bab ini memperkenalkan E2B sebagai **compute layer untuk AI agents**, platform cloud yang menyediakan sandbox terisolasi untuk menjalankan kode Python secara aman. Melalui implementasi praktis, kita belajar bagaimana mengintegrasikan E2B ke dalam workflow AI agents untuk eksekusi kode yang aman dan terkontrol.

---

## Apa itu E2B?
E2B (Execute Code in Browser) adalah **platform cloud computing** yang menyediakan sandbox terisolasi untuk menjalankan kode Python oleh AI agents.

> *"E2B provides secure cloud environments where AI agents can safely execute Python code, access filesystems, and run computations without compromising security."*

### Kenapa Penting untuk AI Agents?
- **Isolasi Keamanan**: Kode dijalankan di environment terpisah dari sistem host
- **Filesystem Access**: AI agents bisa membuat, membaca, dan mengelola file
- **Real-time Execution**: Mendukung streaming output untuk interaksi real-time
- **Resource Management**: Sandbox bisa dibuat dan dihancurkan sesuai kebutuhan

### Bagaimana E2B Bekerja (Under the Hood)
Ketika Anda memanggil:

```python
from e2b_code_interpreter import Sandbox
sandbox = Sandbox.create()
execution = sandbox.run_code("print('Hello world')")
```

E2B melakukan:

1. **Create Sandbox** — spins up a tiny cloud VM (~150 ms startup)
2. **Mount Filesystem** — isolated `/app` directory untuk session Anda
3. **Run Code** — executes commands (`run_code`, `run`, or `commands.run`) di dalam sandbox
4. **Stream Output** — sends `stdout`, `stderr`, dan `error` kembali ke client SDK
5. **Destroy Sandbox** — releases resources otomatis atau saat Anda memanggil `sandbox.close()`

**Secara Internal:**
- Sandboxes dibangun di atas **Firecracker-based micro-VMs** (fast, secure, multi-tenant)
- Setiap sandbox memiliki CPU/RAM quota sendiri
- Mendukung multiple concurrent sandboxes per user/session
- Optional **persistence mode** untuk reuse environment yang sama across runs

---

## E2B API dan Libraries

### 1. e2b (General Sandbox)
Library utama untuk operasi sandbox umum, terutama filesystem operations.

```python
from e2b import Sandbox as GeneralSandbox

# Membuat sandbox
sandbox = GeneralSandbox.create()

# Operasi filesystem
sandbox.files.write("/path/to/file.txt", "content")
content = sandbox.files.read("/path/to/file.txt")
sandbox.files.make_dir("/new/directory")

# Cleanup
sandbox.kill()
```

### 2. e2b-code-interpreter (Code Execution)
Library khusus untuk eksekusi kode Python dengan fitur streaming output.

```python
from e2b_code_interpreter import Sandbox as CodeInterpreterSandbox

# Membuat sandbox
sandbox = CodeInterpreterSandbox.create()

# Eksekusi kode
execution = sandbox.run_code("print('Hello, World!')")

# Mengakses output
print(execution.logs.stdout)  # Output print statements
print(execution.text)         # Return value dari expressions

# Cleanup
sandbox.kill()
```

---

## Basic Python Example

```python
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

load_dotenv()

sbx = Sandbox.create()
sbx.set_timeout(60)

execution = sbx.run_code("print('hello world')")
print("stdout:", execution.logs.stdout)
print("stderr:", execution.logs.stderr)

if execution.error:
    print("Error name:", execution.error.name)
    print("Error value:", execution.error.value)
    print("Traceback:", execution.error.traceback)
else:
    print("✅ Execution successful")
```

```

### Output
```
stdout: ['hello world\n']
stderr: []
✅ Execution successful
```

---

## Learning Steps Implementation

### Step 4: Hello Sandbox
Langkah pertama: membuat code interpreter sandbox dan menjalankan program sederhana.

```python
from e2b_code_interpreter import Sandbox as CodeInterpreterSandbox

def step_4_hello_sandbox():
    sandbox = CodeInterpreterSandbox.create()
    execution = sandbox.run_code("print('Hello from E2B sandbox!')")
    print("Output:", ''.join(execution.logs.stdout).strip())
    sandbox.kill()
```

**Konsep Kunci:**
- `Sandbox.create()` untuk inisialisasi sandbox
- `run_code()` untuk eksekusi kode Python
- `execution.logs.stdout` berisi output dari print statements

### Step 5: Filesystem Experiment
Demonstrasi operasi filesystem menggunakan general sandbox.

```python
from e2b import Sandbox as GeneralSandbox

def step_5_filesystem_experiment():
    sandbox = GeneralSandbox.create()

    # Membuat direktori
    sandbox.files.make_dir("/home/user/experiment")

    # Menulis file
    sandbox.files.write("/home/user/experiment/hello.txt", "Hello from E2B!")

    # Membaca file
    content = sandbox.files.read("/home/user/experiment/hello.txt")
    print("File content:", content)

    # Listing direktori
    files = sandbox.files.list("/home/user/experiment")
    print("Directory contents:", [f.name for f in files])

    sandbox.kill()
```

**Konsep Kunci:**
- General sandbox untuk operasi filesystem
- `files.make_dir()`, `files.write()`, `files.read()`, `files.list()`
- Path absolute di dalam sandbox environment

### Step 6: Streaming Output
Menangani output real-time dengan callback functions.

```python
def step_6_streaming_output():
    sandbox = CodeInterpreterSandbox.create()

    def on_stdout(message):
        print(f"Streaming: {message}")

    code = """
import time
for i in range(5):
    print(f"Message {i+1}")
    time.sleep(0.5)
"""

    execution = sandbox.run_code(code, on_stdout=on_stdout)
    sandbox.kill()
```

**Konsep Kunci:**
- Parameter `on_stdout` untuk callback streaming
- Berguna untuk monitoring eksekusi kode yang berjalan lama
- Callback dipanggil untuk setiap chunk output

### Step 7: Close Sandbox
Demonstrasi cleanup resources yang proper.

```python
def step_7_close_sandbox():
    sandbox1 = CodeInterpreterSandbox.create()
    sandbox2 = GeneralSandbox.create()

    # Menggunakan sandboxes...

    # Selalu cleanup
    sandbox1.kill()
    sandbox2.kill()
```

**Konsep Kunci:**
- `kill()` method untuk terminate sandbox
- Penting untuk resource management dan cost control
- Selalu gunakan try/finally blocks

---

## Reason-Execute-Reflect Loop (AI Coding Agent Pattern)

Best practice untuk AI coding agents adalah **loop architecture**:

```
1️⃣ LLM generates code
2️⃣ Run code in E2B sandbox
3️⃣ Capture stdout/stderr/error
4️⃣ If error → LLM reasons and fixes
5️⃣ Re-run fixed code
```

### Example (Python + OpenAI)

```python
from e2b_code_interpreter import Sandbox
from openai import OpenAI

llm = OpenAI(api_key="sk-...")
sbx = Sandbox.create()

def run_and_reflect(code: str):
    result = sbx.run_code(code)
    if result.error:
        feedback = f"Compiler error:\n{result.error.traceback}"
    else:
        feedback = f"Output:\n{result.logs.stdout}"

    reasoning = llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a coding assistant that fixes code errors."},
            {"role": "user", "content": feedback}
        ]
    )
    return reasoning.choices[0].message.content
```

---

## Multi-Language Support & Templates

E2B mendukung **multi-language sandboxes** melalui sistem *templates* yang powerful. Templates mendefinisikan environment lengkap dari sebuah sandbox — base image, packages, working directory, dan startup commands.

### Built-in Language Support

| Language   | Template | Example Run Command               | Use Case |
| ---------- | -------- | --------------------------------- | -------- |
| Python     | `python` | `sandbox.run_code("print('hi')")` | Code execution, data analysis |
| Node.js    | `node`   | `sandbox.run("node app.js")`      | JavaScript/TypeScript apps |
| Go         | `golang` | `sandbox.run("go build main.go")` | Go development, compilation |
| Bash / CLI | `ubuntu` | `sandbox.run("ls -la")`           | System administration, CLI tools |

### Custom Templates

Custom templates memungkinkan Anda membangun runtime apapun (Java, Rust, PHP, dll.) dengan environment yang fully customized.

📚 Dokumentasi: [https://e2b.dev/docs/template/quickstart](https://e2b.dev/docs/template/quickstart)

#### E2B v2 Template API (Python SDK)

E2B v2 menggunakan **SDK-based template creation** dengan Python code, bukan Dockerfile approach seperti versi sebelumnya. Template dapat didefinisikan menggunakan **sync** atau **async** API.

**`template_dev.py`** (Development Template - Sync API)
```python
from e2b import Template

template = (
    Template()
    .from_base_image()
    .set_envs({
        "PYTHONPATH": "/app",
        "PIP_NO_CACHE_DIR": "1"
    })
    .pip_install([
        "numpy",
        "pandas", 
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "plotly"
    ])
    .copy("./requirements.txt", "/app/requirements.txt")
    .run_cmd("pip install -r /app/requirements.txt")
)

# Build template
template.build()
```

**`template_prod.py`** (Production Template - Async API)
```python
import asyncio
from e2b import AsyncTemplate

async def create_production_template():
    template = (
        AsyncTemplate()
        .from_base_image()
        .set_envs({
            "PYTHONPATH": "/app",
            "DEBIAN_FRONTEND": "noninteractive"
        })
        .run_cmd("apt-get update && apt-get install -y build-essential")
        .pip_install([
            "numpy",
            "pandas",
            "scikit-learn", 
            "matplotlib",
            "seaborn",
            "plotly"
        ])
    )
    
    # Build template asynchronously
    await template.build()
    return template

# Usage
asyncio.run(create_production_template())
```

#### Template Building & Deployment

```bash
# Install E2B CLI (v2)
pip install e2b  # Sudah included jika menggunakan Python SDK

# Initialize template (optional - bisa manual)
e2b template init my-template

# Build development template
python template_dev.py

# Build production template  
python template_prod.py

# List available templates
e2b template list
```

#### Using Templates in Code

```python
from e2b import Sandbox

# Use template by alias (sync)
sbx = Sandbox.create(template="my-template-dev")

# Use template by alias (async)
import asyncio
from e2b import AsyncSandbox

async def use_template():
    sbx = await AsyncSandbox.create(template="my-template-dev")
    result = await sbx.run_code("import pandas as pd; print('Data science ready!')")
    await sbx.kill()
```

#### Template Best Practices (E2B v2)

1. **SDK-Based Definition**: Define templates as Python code untuk better maintainability
2. **Sync vs Async**: Use sync API untuk simple templates, async untuk complex builds
3. **Environment Separation**: Separate dev/prod templates untuk optimal performance
4. **Package Management**: Use `.pip_install()` untuk Python packages, `.run_cmd()` untuk system commands
5. **Environment Variables**: Configure runtime behavior melalui `.set_envs()`
6. **File Management**: Use `.copy()` untuk include configuration files
7. **Base Image Selection**: Choose appropriate base images untuk target language/runtime

#### Migration from v1 to v2

**Old v1 Approach (Deprecated - Dockerfile):**
```dockerfile
# .e2b/Dockerfile
FROM e2bdev/code-interpreter:latest
RUN pip install numpy pandas
```

**New v2 Approach (Python SDK - Sync):**
```python
from e2b import Template

template = (
    Template()
    .from_base_image()
    .pip_install(["numpy", "pandas"])
)

template.build()
```

**New v2 Approach (Python SDK - Async):**
```python
import asyncio
from e2b import AsyncTemplate

async def create_template():
    template = (
        AsyncTemplate()
        .from_base_image()
        .pip_install(["numpy", "pandas"])
    )
    await template.build()

asyncio.run(create_template())
```

### Advanced Template Features (v2)

- **Environment Variables**: Configure runtime behavior dengan `.set_envs()`
- **Network Access**: Control internet access untuk security
- **Resource Limits**: Set CPU/memory limits per template
- **Startup Scripts**: Run initialization scripts saat sandbox creation
- **Volume Mounting**: Mount external storage untuk persistent data
- **Multi-Environment**: Separate dev/prod configurations
- **Build Optimization**: Incremental builds dan caching
- **Async Support**: Full async/await support untuk complex workflows

---

---

## Comprehensive Error Handling & Troubleshooting

### Error Types & Where to Find Them

| Error Type | Location | Properties | Example |
| ---------- | -------- | ---------- | ------- |
| **Runtime Errors** | `execution.logs.stderr` | Stack traces, exceptions | Division by zero, import errors |
| **Syntax/Compile Errors** | `execution.error` | `.name`, `.value`, `.traceback` | SyntaxError, IndentationError |
| **Sandbox Creation Failures** | Exception on `Sandbox.create()` | Connection issues, auth failures | Invalid API key, network timeout |
| **Template Errors** | Exception on template operations | Template not found, build failures | Invalid template name |
| **Timeout Errors** | `Sandbox.set_timeout()` | Execution exceeded time limit | Long-running code |

### Error Handling Patterns

#### Basic Error Handling
```python
from e2b_code_interpreter import Sandbox

def safe_execute(code: str):
    sandbox = None
    try:
        sandbox = Sandbox.create()
        execution = sandbox.run_code(code)

        # Check for execution errors
        if execution.error:
            return {
                "success": False,
                "error": {
                    "type": execution.error.name,
                    "message": execution.error.value,
                    "traceback": execution.error.traceback
                }
            }

        # Check for runtime errors in stderr
        if execution.logs.stderr:
            return {
                "success": False,
                "error": {
                    "type": "RuntimeError",
                    "message": ''.join(execution.logs.stderr)
                }
            }

        # Success case
        return {
            "success": True,
            "output": ''.join(execution.logs.stdout).strip()
        }

    except Exception as e:
        return {
            "success": False,
            "error": {
                "type": "SandboxError",
                "message": str(e)
            }
        }
    finally:
        if sandbox:
            sandbox.kill()
```

#### Advanced Error Recovery
```python
def execute_with_retry(code: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            result = safe_execute(code)
            if result["success"]:
                return result

            # Check if error is recoverable
            error_type = result["error"]["type"]
            if error_type in ["SandboxError", "ConnectionError"]:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

            return result

        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "success": False,
                    "error": {"type": "MaxRetriesExceeded", "message": str(e)}
                }

    return {"success": False, "error": {"type": "Unknown", "message": "All retries failed"}}
```

### Common Issues & Solutions

#### Import Errors
```python
# ❌ Wrong
from e2b_code_interpreter import CodeInterpreterSandbox

# ✅ Correct
from e2b import Sandbox as GeneralSandbox
from e2b_code_interpreter import Sandbox as CodeInterpreterSandbox
```

#### API Key Issues
```python
# Check API key
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('E2B_API_KEY')

if not api_key:
    raise ValueError("E2B_API_KEY not found in environment variables")

# Verify key format (should start with 'e2b_')
if not api_key.startswith('e2b_'):
    raise ValueError("Invalid E2B API key format")
```

#### Output Handling Mistakes
```python
execution = sandbox.run_code("print('hello')")

# ❌ Wrong - returns list
output = execution.logs.stdout

# ✅ Correct - join list into string
output = ''.join(execution.logs.stdout).strip()

# ✅ Alternative - handle multi-line output
lines = [line.strip() for line in execution.logs.stdout if line.strip()]
output = '\n'.join(lines)
```

#### Template Issues
```python
# Check available templates
import subprocess
result = subprocess.run(['e2b', 'templates', 'list'], capture_output=True, text=True)
print("Available templates:", result.stdout)

# Use correct template name
sbx = Sandbox.create(template="python")  # ✅
# sbx = Sandbox.create(template="py")    # ❌ (if 'py' doesn't exist)
```

#### Timeout Management
```python
# Set reasonable timeouts
sandbox = Sandbox.create()
sandbox.set_timeout(30)  # 30 seconds

# For long-running tasks
sandbox.set_timeout(300)  # 5 minutes

# Handle timeout errors
try:
    execution = sandbox.run_code(long_running_code)
except TimeoutError:
    print("Code execution timed out")
    # Implement fallback or notify user
```

### Debug Steps

1. **Verify Environment Setup**
   ```bash
   # Check Python version
   python --version

   # Check E2B installation
   python -c "import e2b, e2b_code_interpreter; print('E2B installed')"

   # Check API key
   echo $E2B_API_KEY
   ```

2. **Test Basic Connectivity**
   ```python
   # Minimal test
   from e2b_code_interpreter import Sandbox
   sbx = Sandbox.create()
   result = sbx.run_code("print('test')")
   print("Success:", result.logs.stdout)
   sbx.kill()
   ```

3. **Check Template Validity**
   ```bash
   e2b template list
   ```

4. **Monitor Resource Usage**
   ```python
   import psutil
   import os

   # Check system resources before sandbox creation
   print(f"CPU: {psutil.cpu_percent()}%")
   print(f"Memory: {psutil.virtual_memory().percent}%")
   ```

### Getting Help

1. **Official Documentation**: [e2b.dev/docs](https://e2b.dev/docs)
2. **GitHub Issues**: Search existing issues atau create new ones
3. **Discord Community**: Real-time help di [E2B Discord](https://discord.gg/e2b)
4. **Enterprise Support**: Priority support untuk paid plans

```python
from e2b import Sandbox
from openai import OpenAI

sbx = Sandbox.create(template="golang")
client = OpenAI(api_key="sk-...")

def fix_go_code(code):
    sbx.files.write("/app/main.go", code)
    result = sbx.run("go build main.go")

    if result.logs.stderr:
        feedback = result.logs.stderr
    elif result.error:
        feedback = result.error.traceback
    else:
        print("✅ Build success!")
        return code

    prompt = f"Fix this Go code:\n\n{code}\n\nCompiler error:\n{feedback}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a Go bug-fixing assistant."},
                  {"role": "user", "content": prompt}]
    )

    fixed_code = response.choices[0].message.content
    sbx.files.write("/app/main.go", fixed_code)
    return fixed_code
```

---

## Environment Setup

### API Key Management
```python
# .env file
E2B_API_KEY=your_api_key_here
```

```python
# Python code
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('E2B_API_KEY')
```

### Authentication & API Keys
E2B menggunakan API keys untuk mengautentikasi SDK calls ke cloud mereka.

```bash
export E2B_API_KEY="your_api_key_here"
```

- **Default mode** → runs di **E2B Cloud** (requires API key)
- **Experimental** → bisa **self-host** sandbox runtime locally (via open-source repo)
- **Enterprise** → **BYOC** (Bring Your Own Cloud) deployment untuk private runtime

**Free tier** menyediakan **$100 trial credit (one-time)** dengan 1-hour sandbox session limit.

### Dependencies
```bash
pip install python-dotenv e2b e2b-code-interpreter
```

---

## Use Cases untuk AI Agents

### 1. Code Execution Agent
AI agents yang bisa menjalankan kode Python yang di-generate user.

### 2. Data Analysis Assistant
Agents yang bisa memproses data, membuat visualisasi, dan menjalankan computations.

### 3. Educational Tools
Interactive coding tutors yang bisa execute dan validate code.

### 4. Research Assistants
Agents yang membantu prototyping algorithms dan running experiments.

---

---

## Best Practices & Security Guidelines

### 1. Resource Management
```python
# Always use try/finally for proper cleanup
try:
    sandbox = CodeInterpreterSandbox.create()
    # ... use sandbox ...
finally:
    sandbox.kill()  # Critical for cost control
```

**Why it matters**: Sandboxes consume resources even when idle. Proper cleanup prevents cost overruns and resource leaks.

### 2. Error Handling & Recovery
```python
def robust_execute(code: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            sandbox = CodeInterpreterSandbox.create()
            execution = sandbox.run_code(code)

            if execution.error:
                return {"success": False, "error": execution.error.traceback}
            if execution.logs.stderr:
                return {"success": False, "error": ''.join(execution.logs.stderr)}

            return {"success": True, "output": ''.join(execution.logs.stdout).strip()}

        except Exception as e:
            if attempt == max_retries - 1:
                return {"success": False, "error": str(e)}
            time.sleep(2 ** attempt)  # Exponential backoff
        finally:
            if 'sandbox' in locals():
                sandbox.kill()
```

### 3. Timeout Management
```python
# Set appropriate timeouts based on use case
sandbox = CodeInterpreterSandbox.create()
sandbox.set_timeout(30)  # 30 seconds for simple operations
# sandbox.set_timeout(300)  # 5 minutes for complex computations

# Handle timeout gracefully
try:
    execution = sandbox.run_code(potentially_long_code)
except TimeoutError:
    print("Operation timed out - consider optimizing code or increasing timeout")
```

### 4. Input Validation & Security
```python
import ast
import re

def validate_code_safety(code: str) -> bool:
    """Basic validation for potentially unsafe operations"""
    dangerous_patterns = [
        r'import\s+os\b',  # OS operations
        r'import\s+subprocess\b',  # System commands
        r'exec\(',  # Dynamic execution
        r'eval\(',  # Dynamic evaluation
        r'open\([^)]*w',  # File writing
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, code):
            return False

    # Check for syntax validity
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

# Usage
if validate_code_safety(user_code):
    result = sandbox.run_code(user_code)
else:
    print("Unsafe code detected")
```

### 5. Cost Optimization Strategies

#### Sandbox Reuse
```python
# Reuse sandbox for multiple related operations
sandbox = CodeInterpreterSandbox.create()

# Perform multiple operations in same sandbox
result1 = sandbox.run_code("x = 42")
result2 = sandbox.run_code("print(x * 2)")
result3 = sandbox.run_code("y = x + 10")

sandbox.kill()
```

#### Selective Execution
```python
def should_execute(code: str) -> bool:
    """Determine if code should be executed based on business logic"""
    # Skip empty or trivial code
    if not code.strip():
        return False

    # Skip comments-only code
    lines = [line.strip() for line in code.split('\n') if line.strip()]
    if all(line.startswith('#') for line in lines):
        return False

    return True
```

#### Resource Monitoring
```python
import time
from typing import Dict, Any

def execute_with_monitoring(code: str) -> Dict[str, Any]:
    start_time = time.time()
    sandbox = CodeInterpreterSandbox.create()

    try:
        execution = sandbox.run_code(code)
        duration = time.time() - start_time

        return {
            "success": not execution.error and not execution.logs.stderr,
            "duration": duration,
            "output": ''.join(execution.logs.stdout).strip() if execution.logs.stdout else "",
            "error": execution.error.traceback if execution.error else None,
            "cost_estimate": estimate_cost(duration)  # Implement based on your pricing
        }
    finally:
        sandbox.kill()
```

### 6. Security Best Practices

#### Sandbox Isolation Understanding
- **Complete Isolation**: Each sandbox is a separate micro-VM with no shared state
- **Network Controls**: By default, sandboxes have controlled internet access
- **Filesystem Sandboxing**: All file operations are contained within `/app` directory
- **Resource Limits**: CPU, memory, dan disk usage are automatically limited

#### Input Sanitization
```python
def sanitize_code_input(code: str) -> str:
    """Remove potentially harmful constructs"""
    # Remove shebang lines
    code = re.sub(r'^#!/.*\n?', '', code, flags=re.MULTILINE)

    # Limit code length
    if len(code) > 10000:  # 10KB limit
        raise ValueError("Code too long")

    # Remove null bytes and other control characters
    code = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', code)

    return code
```

#### Audit Logging
```python
import logging
import json
from datetime import datetime

def log_execution_attempt(code: str, user_id: str, result: Dict[str, Any]):
    """Log all execution attempts for security and debugging"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "code_length": len(code),
        "success": result.get("success", False),
        "duration": result.get("duration", 0),
        "error_type": type(result.get("error")).__name__ if result.get("error") else None,
        "has_output": bool(result.get("output")),
        # Don't log actual code or output for privacy
    }

    logging.info(f"E2B Execution: {json.dumps(log_entry)}")
```

### 7. Performance Optimization

#### Connection Pooling
```python
from typing import List
import threading

class SandboxPool:
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.sandboxes: List[CodeInterpreterSandbox] = []
        self.lock = threading.Lock()

    def get_sandbox(self) -> CodeInterpreterSandbox:
        with self.lock:
            if self.sandboxes:
                return self.sandboxes.pop()
            return CodeInterpreterSandbox.create()

    def return_sandbox(self, sandbox: CodeInterpreterSandbox):
        with self.lock:
            if len(self.sandboxes) < self.pool_size:
                self.sandboxes.append(sandbox)
            else:
                sandbox.kill()
```

#### Template Selection Strategy
```python
def choose_optimal_template(requirements: List[str]) -> str:
    """Select best template based on requirements"""
    template_matrix = {
        "data-science": ["numpy", "pandas", "matplotlib", "scikit-learn"],
        "web-dev": ["flask", "fastapi", "requests", "beautifulsoup"],
        "golang": ["go", "debugging tools"],
        "python-basic": []  # Minimal template for simple tasks
    }

    for template, capabilities in template_matrix.items():
        if all(req in capabilities for req in requirements):
            return template

    return "python-basic"  # Fallback
```

### 8. Production Readiness Checklist

- [ ] **Error Handling**: Comprehensive try/catch blocks with proper cleanup
- [ ] **Timeouts**: Appropriate timeout settings for all operations
- [ ] **Input Validation**: Code sanitization and safety checks
- [ ] **Resource Limits**: CPU/memory monitoring and limits
- [ ] **Logging**: Audit trails untuk security dan debugging
- [ ] **Cost Monitoring**: Usage tracking dan budget alerts
- [ ] **Health Checks**: Regular validation of sandbox connectivity
- [ ] **Graceful Degradation**: Fallback mechanisms when E2B is unavailable
- [ ] **Rate Limiting**: Protection against abuse
- [ ] **Monitoring**: Metrics collection untuk performance tracking

### Import Errors
```python
# Pastikan import yang benar
from e2b import Sandbox as GeneralSandbox
from e2b_code_interpreter import Sandbox as CodeInterpreterSandbox

# Bukan:
# from e2b_code_interpreter import CodeInterpreterSandbox  # ❌
```

### API Key Issues
```python
# Verify API key
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('E2B_API_KEY')
if not api_key:
    raise ValueError("E2B_API_KEY not found")
```

### Output Handling
```python
# execution.logs.stdout adalah list
execution = sandbox.run_code("print('hello')")
output = ''.join(execution.logs.stdout).strip()  # ✅

# Bukan:
# output = execution.logs.stdout  # ❌ (returns list)
```

---

## Integration dengan AI Frameworks

### LangChain + E2B
```python
from langchain.tools import Tool
from e2b_code_interpreter import Sandbox

def execute_code(code: str) -> str:
    sandbox = CodeInterpreterSandbox.create()
    try:
        execution = sandbox.run_code(code)
        return ''.join(execution.logs.stdout).strip()
    finally:
        sandbox.kill()

code_executor = Tool(
    name="CodeExecutor",
    description="Execute Python code in a sandbox",
    func=execute_code
)
```

### AutoGen + E2B
```python
from autogen import AssistantAgent
from e2b_code_interpreter import Sandbox

class CodeExecutionAgent(AssistantAgent):
    def execute_code(self, code):
        sandbox = CodeInterpreterSandbox.create()
        try:
            result = sandbox.run_code(code)
            return result.logs.stdout
        finally:
            sandbox.kill()
```

---

## Cost Optimization

### 1. Sandbox Reuse
```python
# Reuse sandbox untuk multiple operations
sandbox = CodeInterpreterSandbox.create()

# Multiple executions
result1 = sandbox.run_code("x = 1 + 1")
result2 = sandbox.run_code("print(x * 2)")

sandbox.kill()
```

### 2. Selective Execution
```python
# Hanya execute code yang necessary
def safe_execute(code):
    # Validate code sebelum execute
    if is_safe_code(code):
        return sandbox.run_code(code)
    else:
        return "Unsafe code detected"
```

### 3. Resource Monitoring
```python
# Monitor usage patterns
def execute_with_monitoring(code):
    start_time = time.time()
    result = sandbox.run_code(code)
    duration = time.time() - start_time

    # Log untuk cost analysis
    log_execution(code, duration, result.success)
    return result
```

---

---

## Referensi

### Official Documentation
* [E2B Documentation](https://e2b.dev/docs) - Official docs untuk semua features
* [E2B Dashboard](https://e2b.dev/dashboard) - Web dashboard untuk managing sandboxes
* [E2B Code Interpreter](https://github.com/e2b-dev/e2b-code-interpreter) - GitHub repo untuk code interpreter SDK
* [E2B Python SDK](https://github.com/e2b-dev/e2b) - GitHub repo untuk general sandbox SDK

### Technical Guides
* [Sandbox Lifecycle](https://e2b.dev/docs/sandbox) - Detail tentang lifecycle management
* [Code Interpreting & Streaming](https://e2b.dev/docs/code-interpreting/streaming) - Advanced streaming features
* [Template Quickstart](https://e2b.dev/docs/template/quickstart) - Getting started dengan custom templates
* [Authentication Guide](https://e2b.dev/docs/authentication) - API key management dan security

### Example Projects
* [Fragments Example Project](https://github.com/e2b-dev/fragments) - Real-world example dengan templates
* [E2B Examples Repository](https://github.com/e2b-dev/examples) - Collection of example implementations
* [AI Agent Examples](https://github.com/e2b-dev/ai-agents) - Examples untuk AI coding agents

### Integration Guides
* [LangChain Integration](https://e2b.dev/docs/integrations/langchain) - Using E2B dengan LangChain
* [AutoGen Integration](https://e2b.dev/docs/integrations/autogen) - Using E2B dengan Microsoft AutoGen
* [OpenAI Integration](https://e2b.dev/docs/integrations/openai) - Building AI agents dengan OpenAI

### Community Resources
* [E2B Discord](https://discord.gg/e2b) - Community support dan discussions
* [E2B Blog](https://e2b.dev/blog) - Technical articles dan updates
* [E2B YouTube](https://youtube.com/@e2b-dev) - Video tutorials dan demos

### Related Technologies
* [Firecracker](https://firecracker-microvm.github.io/) - MicroVM technology yang digunakan E2B
* [LangChain](https://python.langchain.com/) - Framework untuk AI agents
* [AutoGen](https://microsoft.github.io/autogen/) - Multi-agent framework dari Microsoft
* [Gradio](https://gradio.app/) - Framework untuk web interfaces (seperti yang digunakan di workspace ini)

---

## Advanced Topics

### Performance Optimization
1. **Connection Pooling**: Reuse sandbox connections untuk multiple requests
2. **Template Caching**: Pre-build templates untuk faster startup
3. **Resource Limits**: Configure CPU/memory limits berdasarkan use case
4. **Batch Operations**: Group multiple operations dalam satu sandbox session

### Enterprise Features
1. **BYOC (Bring Your Own Cloud)**: Deploy E2B runtime di private cloud
2. **Custom Templates**: Build organization-specific development environments
3. **Advanced Monitoring**: Detailed metrics dan logging capabilities
4. **SLA Guarantees**: Enterprise-grade reliability dan support

### Future Developments
E2B terus berkembang dengan features seperti:
- **Multi-language support expansion** (Rust, Java, C++, etc.)
- **GPU acceleration** untuk machine learning workloads
- **Persistent storage** untuk long-running applications
- **Real-time collaboration** features untuk team development

---

## Korelasikan dengan Files di Workspace

Notes ini berkorelasi dengan implementasi praktis E2B di workspace:

- **[e2b_sandbox_runner.ipynb](notebooks/e2b_sandbox_runner.ipynb)**: Notebook Jupyter interaktif untuk pembelajaran E2B dengan cells yang bisa dieksekusi satu per satu
- **[gradio_e2b_code_runner.py](scripts/gradio_e2b_code_runner.py)**: UI interaktif seperti Replit untuk coding dan running code di E2B sandbox
- **[gradio_code_repair_agent.py](scripts/gradio_code_repair_agent.py)**: AI agent yang menggunakan E2B sandbox untuk debugging dan memperbaiki kode secara iteratif

Implementasi ini mendemonstrasikan penggunaan E2B untuk:
- Code execution yang aman
- Filesystem operations
- Streaming output untuk real-time interaction
- Proper resource cleanup
- Multi-language support via templates
- AI coding agent patterns (reason-execute-reflect loop)
- Error handling dan debugging workflows

Notebook dan script bisa dijalankan untuk melihat implementasi praktis dari konsep-konsep yang dijelaskan di atas.

---

## Takeaways

### Core Understanding
* **E2B** = Secure compute layer untuk AI agents menjalankan kode dengan aman
* **Sandbox Isolation** = Complete micro-VM isolation menggunakan Firecracker technology
* **Multi-Language Support** = Template system untuk Python, Node.js, Go, Bash, dan custom runtimes
* **Real-Time Execution** = Streaming output untuk interactive AI agent experiences

### Technical Architecture
* **CodeInterpreterSandbox** = Specialized untuk Python code execution dengan streaming support
* **GeneralSandbox** = Full filesystem access dan multi-language command execution
* **Template System** = SDK-based custom environments dengan pre-installed packages
* **Resource Management** = Automatic cleanup, timeout handling, dan cost optimization

### AI Agent Patterns
* **Reason-Execute-Reflect Loop** = Best practice untuk iterative code improvement
* **Error Recovery** = Comprehensive error handling dengan automatic retry mechanisms
* **Input Validation** = Security-first approach dengan code sanitization
* **Audit Logging** = Complete traceability untuk debugging dan compliance

### Integration & Ecosystem
* **Framework Ready** = Native integration dengan LangChain, AutoGen, dan AI frameworks
* **Production Hardened** = Connection pooling, resource monitoring, dan graceful degradation
* **Enterprise Features** = BYOC deployment, advanced monitoring, dan SLA guarantees
* **Developer Experience** = Rich SDKs, comprehensive documentation, dan active community

### Best Practices Summary
* **Always use try/finally** untuk proper resource cleanup
* **Implement comprehensive error handling** dengan retry logic dan user feedback
* **Validate inputs** dan sanitize code sebelum execution
* **Monitor costs** dengan resource tracking dan usage optimization
* **Choose appropriate templates** berdasarkan use case requirements
* **Log everything** untuk debugging, security, dan compliance

### Future Outlook
E2B represents the future of AI-powered development tools, enabling AI agents to:
- **Safely execute code** without compromising system security
- **Access real computing resources** for complex computations
- **Maintain persistent state** across multi-step workflows
- **Scale to enterprise requirements** dengan private cloud deployment
- **Integrate seamlessly** dengan existing AI agent frameworks

The platform combines the security of sandboxed execution with the power of cloud computing, making it possible to build truly autonomous AI coding assistants that can reason about, execute, and improve code in real-time.</content>
<parameter name="filePath">/Users/zeihanaulia/Programming/research/agent/notes/introducing_e2b_sandbox.md