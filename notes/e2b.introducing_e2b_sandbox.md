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

... (content truncated, identical to original)
