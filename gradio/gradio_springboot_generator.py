#!/usr/bin/env python3
"""
Gradio interface for the Spring Boot generator using E2B sandbox

Features:
- Shows that code is loaded from `dataset/springboot-demo` (pom.xml, Application.java, HelloController.java)
- Dropdown to select file and view its contents
- "Run Build" button to run `mvn clean package -DskipTests` in E2B sandbox
- Streaming build output shown in a logs panel (using E2B callbacks like original script)
- Option to start the Spring Boot app after build
- Test endpoint functionality

Uses E2B sandbox environment like the original springboot_generator.py
"""

import os
import time
import gradio as gr
from e2b import Sandbox

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If dotenv not available, try manual loading
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEMO_DIR = os.path.join(ROOT_DIR, "dataset", "springboot-demo")

DEFAULT_FILES = [
    "pom.xml",
    os.path.join("src", "main", "java", "com", "example", "springboot", "Application.java"),
    os.path.join("src", "main", "java", "com", "example", "springboot", "HelloController.java"),
]

def list_demo_files():
    files = []
    for rel in DEFAULT_FILES:
        path = os.path.join(DEMO_DIR, rel)
        if os.path.exists(path):
            files.append(rel)
    # add any other files at root of demo
    try:
        for entry in os.listdir(DEMO_DIR):
            if entry not in [os.path.basename(p) for p in DEFAULT_FILES] and os.path.isfile(os.path.join(DEMO_DIR, entry)):
                files.append(entry)
    except Exception:
        pass
    return files

def load_file(relpath: str) -> str:
    path = os.path.join(DEMO_DIR, relpath)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error loading {relpath}: {e}"

def detect_language(relpath: str):
    # Gradio Code component doesn't support Java or XML syntax highlighting
    return None

def update_code(relpath: str):
    content = load_file(relpath)
    lang = detect_language(relpath)
    return gr.update(value=content, language=lang)

def build_and_stream():
    """Generator that streams build output using E2B sandbox like the original script.

    Yields accumulated output to show complete streaming in textbox.
    """
    output = "🔧 Setting up E2B sandbox...\n"
    yield output

    # Load API key
    api_key = os.getenv('E2B_API_KEY')
    if not api_key:
        output += "❌ E2B_API_KEY not found in environment variables\n"
        output += "Please set your E2B API key: export E2B_API_KEY=your_key_here\n"
        yield output
        return

    sandbox = None
    try:
        output += "🚀 Creating Spring Boot sandbox...\n"
        yield output
        sandbox = Sandbox.create(template="springboot-dev", api_key=api_key)
        output += "✅ Sandbox created successfully!\n\n"
        yield output

        # Create project structure like original script
        output += "📁 Creating project structure...\n"
        yield output
        sandbox.commands.run("mkdir -p /home/user/spring-boot/src/main/java/com/example/springboot")
        sandbox.commands.run("mkdir -p /home/user/spring-boot/src/test/java/com/example/springboot")

        # Write files from demo
        pom_content = load_file("pom.xml")
        app_content = load_file("src/main/java/com/example/springboot/Application.java")
        controller_content = load_file("src/main/java/com/example/springboot/HelloController.java")

        sandbox.files.write("/home/user/spring-boot/pom.xml", pom_content)
        sandbox.files.write("/home/user/spring-boot/src/main/java/com/example/springboot/Application.java", app_content)
        sandbox.files.write("/home/user/spring-boot/src/main/java/com/example/springboot/HelloController.java", controller_content)
        output += "✅ Project files uploaded to sandbox\n\n"
        yield output

        # Verify environment
        output += "🔍 Verifying environment...\n"
        yield output
        java_result = sandbox.commands.run("java -version")
        output += f"Java: {java_result.stdout or java_result.stderr}\n"
        yield output
        maven_result = sandbox.commands.run("mvn -version")
        output += f"Maven: {maven_result.stdout or maven_result.stderr}\n"
        yield output
        output += "✅ Environment ready\n\n"
        yield output

        # Build with streaming callbacks like original
        output += "🔨 Starting Maven build...\n"
        yield output
        build_output = []

        def on_stdout(data):
            line = f"[BUILD] {data.strip()}\n"
            build_output.append(line)

        def on_stderr(data):
            line = f"[ERROR] {data.strip()}\n"
            build_output.append(line)

        try:
            build_result = sandbox.commands.run(
                "cd /home/user/spring-boot && mvn clean package -DskipTests",
                on_stdout=on_stdout,
                on_stderr=on_stderr,
                timeout=300
            )

            # Stream the collected output
            for line in build_output:
                output += line
                yield output
                time.sleep(0.05)  # Small delay to make streaming visible

            output += f"\n🏁 Build completed with exit code: {build_result.exit_code}\n"
            yield output

            if build_result.exit_code != 0:
                output += "❌ Build failed!\n"
                if build_result.stderr:
                    output += f"Error details: {build_result.stderr}\n"
                yield output
                return False
            else:
                output += "✅ Build successful!\n"
                yield output

                # Check JAR
                jar_check = sandbox.commands.run("cd /home/user/spring-boot && ls -la target/*.jar")
                output += f"JAR files: {jar_check.stdout}\n"
                yield output
                return True

        except Exception as e:
            output += f"❌ Build error: {e}\n"
            yield output
            return False

    except Exception as e:
        output += f"❌ Sandbox error: {e}\n"
        yield output
        return False

    finally:
        if sandbox:
            output += "\n🔄 Cleaning up sandbox...\n"
            yield output
            sandbox.kill()
            output += "✅ Sandbox terminated\n"
            yield output


def start_app_and_test():
    """Generator that starts the Spring Boot app in E2B sandbox and tests endpoints.

    Yields accumulated output to show complete streaming in textbox.
    """
    output = "🚀 Starting Spring Boot application...\n"
    yield output

    # Load API key
    api_key = os.getenv('E2B_API_KEY')
    if not api_key:
        output += "❌ E2B_API_KEY not found in environment variables\n"
        yield output
        return

    sandbox = None
    try:
        output += "🔧 Setting up sandbox for app startup...\n"
        yield output
        sandbox = Sandbox.create(template="springboot-dev", api_key=api_key)
        output += "✅ Sandbox ready\n"
        yield output

        # Recreate project and build first
        output += "📁 Setting up project...\n"
        yield output
        sandbox.commands.run("mkdir -p /home/user/spring-boot/src/main/java/com/example/springboot")

        pom_content = load_file("pom.xml")
        app_content = load_file("src/main/java/com/example/springboot/Application.java")
        controller_content = load_file("src/main/java/com/example/springboot/HelloController.java")

        sandbox.files.write("/home/user/spring-boot/pom.xml", pom_content)
        sandbox.files.write("/home/user/spring-boot/src/main/java/com/example/springboot/Application.java", app_content)
        sandbox.files.write("/home/user/spring-boot/src/main/java/com/example/springboot/HelloController.java", controller_content)

        # Quick build
        output += "🔨 Building application...\n"
        yield output
        build_result = sandbox.commands.run("cd /home/user/spring-boot && mvn clean package -DskipTests -q")
        if build_result.exit_code != 0:
            output += "❌ Build failed, cannot start app\n"
            yield output
            return

        output += "✅ Build successful\n"
        yield output

        # Start the app
        jar_name = "target/spring-boot-0.0.1-SNAPSHOT.jar"
        start_cmd = f"cd /home/user/spring-boot && nohup java -jar {jar_name} > app.log 2>&1 &"
        output += f"🏃 Starting app: {start_cmd}\n"
        yield output

        # Start the app - use short timeout since it should return immediately with &
        try:
            start_result = sandbox.commands.run(start_cmd, timeout=2)
            output += "✅ Start command issued successfully\n"
            yield output
        except Exception as e:
            output += f"⚠️  Start command may have timed out, but app might still be starting: {str(e)}\n"
            yield output
            # Continue anyway since the app should be starting in background

        # Wait and check startup
        output += "⏳ Waiting for app to start...\n"
        yield output
        import time

        # Check multiple times for Java process
        max_checks = 10
        process_found = False
        port_listening = False
        port_status = "Port 8080 not listening"

        for i in range(max_checks):
            output += f"Check {i+1}/{max_checks}...\n"
            yield output

            # Check if Java process is running
            ps_check = sandbox.commands.run("ps aux | grep java | grep -v grep", timeout=5)
            java_processes = ps_check.stdout.strip()
            if java_processes:
                output += "✅ Java process found running\n"
                process_found = True

                # Now check if port 8080 is listening
                port_check = sandbox.commands.run("netstat -tlnp 2>/dev/null | grep :8080 || ss -tlnp | grep :8080 || echo 'Port 8080 not listening'", timeout=5)
                port_status = port_check.stdout.strip()
                if "8080" in port_status and "listening" in port_status.lower():
                    output += "✅ Port 8080 is now listening\n"
                    port_listening = True
                    break
                else:
                    output += "⏳ Port 8080 not ready yet, waiting...\n"
                    time.sleep(2)
            else:
                output += "⏳ No Java process yet, waiting...\n"
                time.sleep(3)

        if not process_found:
            output += "❌ Java process not found after all checks\n"
            yield output
        elif not port_listening:
            output += f"⚠️  Java process found but port 8080 not listening (status: {port_status})\n"
            yield output

        # Test endpoint
        if port_listening:
            output += "🌐 Testing endpoint...\n"
            yield output

            # Check application logs first
            output += "📋 Checking application logs...\n"
            yield output
            log_check = sandbox.commands.run("cd /home/user/spring-boot && cat app.log 2>/dev/null | tail -10 || echo 'No logs yet'", timeout=5)
            output += f"Recent logs: {log_check.stdout}\n"
            yield output

            # First check if curl is available
            curl_check = sandbox.commands.run("which curl || echo 'curl not found'", timeout=5)
            if "curl not found" in curl_check.stdout:
                output += "❌ curl command not available in sandbox\n"
                yield output
            else:
                output += "✅ curl is available\n"
                yield output

                # Try curl with more verbose output
                try:
                    curl_result = sandbox.commands.run("curl -v -m 10 http://localhost:8080/ 2>&1 || echo 'CURL_FAILED'", timeout=15)
                    output += f"Curl output: {curl_result.stdout}\n"
                    yield output

                    if "Greetings from Spring Boot" in curl_result.stdout:
                        output += "✅ Endpoint working correctly!\n"
                        yield output
                    elif "CURL_FAILED" in curl_result.stdout:
                        output += "❌ Curl command failed completely\n"
                        yield output
                    else:
                        output += "⚠️  Unexpected curl response\n"
                        yield output
                except Exception as e:
                    output += f"❌ Curl exception: {e}\n"
                    yield output
        else:
            output += "⚠️  Port 8080 not ready yet\n"
            yield output

        output += "\n🎉 App startup and testing completed!\n"
        yield output

    except Exception as e:
        output += f"❌ Error: {e}\n"
        yield output

    finally:
        if sandbox:
            output += "\n🔄 Cleaning up...\n"
            yield output
            sandbox.kill()
            output += "✅ Sandbox terminated\n"
            yield output


def make_demo():
    files = list_demo_files()
    first = files[0] if files else "pom.xml"

    with gr.Blocks(title="Spring Boot Generator - Demo") as demo:
        gr.Markdown("## Spring Boot Demo — Gradio Interface")
        gr.Markdown(f"Code loaded from: `{DEMO_DIR}`")

        with gr.Row():
            with gr.Column(scale=1):
                file_dropdown = gr.Dropdown(label="Select file", choices=files, value=first)
                code_display = gr.Code(value=load_file(first), language=detect_language(first), label="File contents")
            with gr.Column(scale=1):
                run_btn = gr.Button("Run Build", variant="primary")
                start_app_btn = gr.Button("Start App & Test", variant="secondary")
                logs = gr.Textbox(label="Build/Startup Output (streaming)", lines=25, interactive=False, show_copy_button=True)
                gr.Markdown("**Build**: Runs `mvn clean package -DskipTests` in E2B sandbox\n**Start App & Test**: Builds, starts the app, and tests the endpoint")

        file_dropdown.change(fn=update_code, inputs=file_dropdown, outputs=code_display)
        # Button triggers generator which streams text into logs textbox
        run_btn.click(fn=build_and_stream, inputs=None, outputs=logs)
        start_app_btn.click(fn=start_app_and_test, inputs=None, outputs=logs)

    return demo


if __name__ == "__main__":
    app = make_demo()
    app.launch()
