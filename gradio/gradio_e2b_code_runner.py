import os
import gradio as gr
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox as CodeInterpreterSandbox
from e2b import Sandbox as GeneralSandbox

# Load environment variables
load_dotenv()
e2b_api_key = os.getenv('E2B_API_KEY')

# Global persistent sandbox for filesystem operations
persistent_sandbox = None

def get_persistent_sandbox():
    """Get or create a persistent sandbox for filesystem operations"""
    global persistent_sandbox
    if persistent_sandbox is None and e2b_api_key:
        try:
            persistent_sandbox = GeneralSandbox.create()
            print("Persistent sandbox created for filesystem operations")
        except Exception as e:
            print(f"Failed to create persistent sandbox: {e}")
            return None
    return persistent_sandbox

def run_code_in_sandbox(code: str):
    """
    Run code in E2B sandbox and return output
    """
    if not e2b_api_key:
        return "❌ Error: E2B_API_KEY not found. Please set your API key in .env file."

    try:
        # Use code interpreter sandbox for code execution
        sandbox = CodeInterpreterSandbox.create()

        # Run the code
        execution = sandbox.run_code(code)

        # Get output
        final_output = "".join(execution.logs.stdout).strip() if execution.logs.stdout else ""

        # Add any errors
        if execution.logs.stderr:
            error_output = "".join(execution.logs.stderr).strip()
            final_output += f"\n\n❌ Errors:\n{error_output}"

        # Clean up
        sandbox.kill()

        return final_output if final_output else "✅ Code executed successfully (no output)"

    except Exception as e:
        return f"❌ Execution error: {str(e)}"

def create_file_in_sandbox(filename: str, content: str):
    """
    Create a file in the persistent sandbox filesystem
    """
    if not e2b_api_key:
        return "❌ Error: E2B_API_KEY not found."

    try:
        sandbox = get_persistent_sandbox()
        if sandbox is None:
            return "❌ Failed to create sandbox."

        sandbox.files.write(filename, content)
        return f"✅ File '{filename}' created successfully in persistent sandbox!"
    except Exception as e:
        return f"❌ Error creating file: {str(e)}"

def read_file_from_sandbox(filename: str):
    """
    Read a file from the persistent sandbox filesystem
    """
    if not e2b_api_key:
        return "❌ Error: E2B_API_KEY not found."

    try:
        sandbox = get_persistent_sandbox()
        if sandbox is None:
            return "❌ No persistent sandbox available."

        content = sandbox.files.read(filename)
        return content
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"

def list_files_in_sandbox(directory: str = "/home/user"):
    """
    List files in the persistent sandbox directory
    """
    if not e2b_api_key:
        return "❌ Error: E2B_API_KEY not found."

    try:
        sandbox = get_persistent_sandbox()
        if sandbox is None:
            return "❌ No persistent sandbox available."

        files = sandbox.files.list(directory)
        file_list = [f"{f.name} (file)" for f in files]
        return "\n".join(file_list) if file_list else "Directory is empty"
    except Exception as e:
        return f"❌ Error listing files: {str(e)}"

def reset_persistent_sandbox():
    """
    Reset/clear the persistent sandbox
    """
    global persistent_sandbox
    if persistent_sandbox:
        try:
            persistent_sandbox.kill()
        except Exception:
            pass
        persistent_sandbox = None
    return "✅ Persistent sandbox reset. All files cleared."

# Predefined code examples
code_examples = {
    "Hello World": 'print("Hello, World from E2B Sandbox!")',
    "Basic Math": """x = 10
y = 20
print(f"Sum: {x + y}")
print(f"Product: {x * y}")
print(f"Square of 5: {5**2}")""",
    "Loop Example": """for i in range(5):
    print(f"Iteration {i + 1}: {i**2}")""",
    "Function Example": """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print("Factorial of 5:", factorial(5))
print("Factorial of 10:", factorial(10))""",
    "Data Analysis": """import numpy as np

# Create sample data
data = np.random.normal(0, 1, 1000)

print("Mean:", np.mean(data))
print("Std:", np.std(data))
print("Min:", np.min(data))
print("Max:", np.max(data))""",
    "Plot Example": """import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)
plt.title('Sine Wave')
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.savefig('/tmp/sine_wave.png')
print("Plot saved as sine_wave.png")"""
}

# Gradio Interface
with gr.Blocks(title="E2B Code Runner - Like Replit") as demo:
    gr.Markdown("""
    # 🏃‍♂️ E2B Code Runner
    **Run Python code in secure sandbox environment - Just like Replit!**

    Write your Python code below and click **Run Code** to execute it in an isolated E2B sandbox.
    The sandbox provides a clean Python environment with popular libraries pre-installed.
    """)

    with gr.Tabs():
        # Main Code Editor Tab
        with gr.TabItem("💻 Code Editor"):
            with gr.Row():
                with gr.Column(scale=2):
                    code_input = gr.Code(
                        label="Python Code",
                        language="python",
                        lines=20,
                        value=code_examples["Hello World"]
                    )

                    with gr.Row():
                        run_btn = gr.Button("🚀 Run Code", variant="primary", size="lg")
                        clear_btn = gr.Button("🗑️ Clear", size="sm")

                    example_dropdown = gr.Dropdown(
                        label="📚 Load Example",
                        choices=list(code_examples.keys()),
                        value="Hello World",
                        interactive=True
                    )

                with gr.Column(scale=1):
                    output_display = gr.Textbox(
                        label="📤 Output",
                        lines=20,
                        interactive=False,
                        placeholder="Code output will appear here...",
                        show_copy_button=True
                    )

        # Filesystem Tab
        with gr.TabItem("📁 Filesystem"):
            gr.Markdown("""
            ### Manage files in your persistent sandbox environment
            
            **Note:** Files are stored in a persistent sandbox that stays active across operations.
            Use "Reset Sandbox" to clear all files and start fresh.
            """)

            with gr.Row():
                with gr.Column():
                    filename_input = gr.Textbox(
                        label="Filename",
                        placeholder="e.g., hello.py, data.txt",
                        value="hello.py"
                    )
                    file_content_input = gr.Textbox(
                        label="File Content",
                        lines=10,
                        placeholder="Write file content here...",
                        value='print("Hello from file!")'
                    )
                    with gr.Row():
                        create_file_btn = gr.Button("📝 Create File", variant="secondary")
                        reset_btn = gr.Button("🔄 Reset Sandbox", variant="stop")

                with gr.Column():
                    read_filename_input = gr.Textbox(
                        label="Filename to Read",
                        placeholder="e.g., hello.py",
                        value="hello.py"
                    )
                    read_file_btn = gr.Button("📖 Read File", variant="secondary")

                    list_dir_input = gr.Textbox(
                        label="Directory to List",
                        placeholder="/home/user",
                        value="/home/user"
                    )
                    list_files_btn = gr.Button("📋 List Files", variant="secondary")

            file_output = gr.Textbox(
                label="📤 File Operations Output",
                lines=15,
                interactive=False,
                placeholder="File operation results will appear here...",
                show_copy_button=True
            )

    # Event handlers
    def load_example(example_name):
        return code_examples.get(example_name, "")

    def clear_code():
        return ""

    # Code execution
    run_btn.click(
        fn=run_code_in_sandbox,
        inputs=[code_input],
        outputs=[output_display]
    )

    clear_btn.click(
        fn=clear_code,
        outputs=[code_input]
    )

    example_dropdown.change(
        fn=load_example,
        inputs=[example_dropdown],
        outputs=[code_input]
    )

    # File operations
    create_file_btn.click(
        fn=create_file_in_sandbox,
        inputs=[filename_input, file_content_input],
        outputs=[file_output]
    )

    read_file_btn.click(
        fn=read_file_from_sandbox,
        inputs=[read_filename_input],
        outputs=[file_output]
    )

    list_files_btn.click(
        fn=list_files_in_sandbox,
        inputs=[list_dir_input],
        outputs=[file_output]
    )

    reset_btn.click(
        fn=reset_persistent_sandbox,
        outputs=[file_output]
    )

    # Footer
    gr.Markdown("""
    ---
    **🔒 Security Note:** All code runs in isolated E2B sandboxes. Your local system remains safe.

    **📚 Libraries Available:** numpy, pandas, matplotlib, requests, and many more!

    **⚡ Powered by:** [E2B](https://e2b.dev) - Secure cloud environments for AI agents.
    """)

if __name__ == "__main__":
    demo.launch()