# E2B Sandbox Documentation Index

## 📋 Overview
Dokumentasi lengkap untuk integrasi E2B (Execute Code in Browser) sebagai compute layer untuk AI agents. E2B menyediakan sandbox terisolasi untuk menjalankan kode Python secara aman.

## 🎯 Learning Path

### Level 1: Introduction (30 min)
1. **[Introducing E2B](e2b.introducing_e2b_sandbox.md)** - Pengenalan E2B sebagai compute layer untuk AI agents
2. **[Experiment Template Build](e2b.experiment-template-build.md)** - Membuat template Spring Boot dan alur build

### Level 2: Implementation (45 min)
1. **[Spring Boot + E2B + Gradio](e2b.springboot_gradio_sandbox_preview_experiment.md)** - Live preview & streaming build logs
2. **[Quick Start Guide](e2b.springboot-quick-start.md)** - Panduan cepat setup Spring Boot dengan E2B

### Level 3: Advanced Integration (60 min)
1. **[Setup Successful](e2b.springboot-setup-successful.md)** - Dokumentasi setup yang berhasil
2. **[Template README](e2b.springboot-template-readme.md)** - Dokumentasi template Spring Boot

### Level 4: Testing & Results (30 min)
1. **[Test Results](e2b.test-results-final.md)** - Hasil testing akhir
2. **[Implementation Summary](e2b.implementation-summary.md)** - Ringkasan implementasi

## 📁 File Structure

### Core Documentation
- `e2b.introducing_e2b_sandbox.md` - Introduction to E2B concepts
- `e2b.experiment-template-build.md` - Template building experiments
- `e2b.springboot_gradio_sandbox_preview_experiment.md` - Gradio integration

### Setup & Configuration
- `e2b.springboot-quick-start.md` - Quick start guide
- `e2b.springboot-setup-successful.md` - Successful setup documentation
- `e2b.springboot-template-readme.md` - Template documentation

### Testing & Results
- `e2b.test-results-final.md` - Final test results
- `e2b.implementation-summary.md` - Implementation summary

## 🚀 Quick Start

### Basic E2B Usage
```python
from e2b_code_interpreter import Sandbox

# Create sandbox
sandbox = Sandbox.create()

# Run code
execution = sandbox.run_code("print('Hello from E2B!')")
print(execution.logs.stdout)

# Cleanup
sandbox.kill()
```

### With Streaming
```python
def on_stdout(message):
    print(f"Streaming: {message}")

execution = sandbox.run_code("print('Hello')", on_stdout=on_stdout)
```

### Filesystem Operations
```python
from e2b import Sandbox as GeneralSandbox

sandbox = GeneralSandbox.create()
sandbox.files.write("/file.txt", "content")
content = sandbox.files.read("/file.txt")
```

## 🔧 Key Components

### E2B Libraries
- **e2b** - General sandbox untuk filesystem operations
- **e2b-code-interpreter** - Specialized untuk code execution dengan streaming

### Sandbox Types
- **Code Interpreter Sandbox** - Untuk eksekusi kode Python
- **General Sandbox** - Untuk operasi filesystem umum
- **Custom Templates** - Sandbox dengan environment khusus

### Features
- **Isolated Execution** - Kode berjalan di environment terpisah
- **Streaming Output** - Real-time output monitoring
- **Filesystem Access** - Read/write files dalam sandbox
- **Resource Management** - CPU/RAM quotas per sandbox

## 📊 Integration Examples

### With AI Agents
```python
# Reason-Execute-Reflect Loop
def run_and_reflect(code: str):
    result = sandbox.run_code(code)
    if result.error:
        feedback = f"Error: {result.error.traceback}"
    else:
        feedback = f"Output: {result.logs.stdout}"
    return feedback
```

### With Gradio
```python
import gradio as gr
from e2b_code_interpreter import Sandbox

def execute_code(code):
    sandbox = Sandbox.create()
    result = sandbox.run_code(code)
    sandbox.kill()
    return result.logs.stdout[0] if result.logs.stdout else "No output"

gr.Interface(fn=execute_code, inputs="textbox", outputs="text").launch()
```

## 📚 References

- **E2B Documentation**: https://e2b.dev/docs
- **Code Interpreter**: https://e2b.dev/docs/code-interpreter
- **Sandbox API**: https://e2b.dev/docs/sandbox

## 🎯 Next Steps

1. **Start Learning**: Read `e2b.introducing_e2b_sandbox.md`
2. **Try Basic Example**: Run simple code execution
3. **Explore Integration**: Check Gradio examples
4. **Build Templates**: Learn custom sandbox templates

---

**Last Updated**: November 4, 2025  
**Status**: ✅ Documentation Organized  
**Learning Path**: 4 levels, ~3 hours total