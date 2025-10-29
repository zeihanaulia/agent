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

# Global sandbox used for preview runner (persist across runs until stopped)
PREVIEW_SANDBOX = None

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

        # Wait and stream startup logs in short chunks so we can detect readiness
        output += "⏳ Waiting for app to start (streaming logs)...\n"
        yield output

        # We'll stream `app.log` in short chunks and after each chunk check for readiness.
        # This allows the generator to "detach" the log streaming once the app is ready
        # while leaving the Java process running in the sandbox.
        run_output = []

        def on_stdout(data):
            # collect raw lines (without adding additional prefixes here)
            run_output.append(str(data).rstrip('\n'))

        def on_stderr(data):
            run_output.append("[ERR] " + str(data).rstrip('\n'))

        total_timeout = 20 * 60  # 20 minutes in seconds (user provided)
        chunk_seconds = 4
        elapsed = 0
        last_index = 0
        process_found = False
        port_listening = False
        port_status = "Port 8080 not listening"

        # Try to stream logs repeatedly in short chunks until readiness or timeout
        while elapsed < total_timeout:
            try:
                # tail -n 0 -f prints only new lines appended after the command starts.
                # Run in short chunks (sandbox enforces timeout) so we can poll readiness
                # without reprinting the whole file each iteration.
                sandbox.commands.run(
                    "cd /home/user/spring-boot && tail -n 0 -f app.log",
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                    timeout=chunk_seconds + 1,
                )
            except Exception:
                # expected when the remote command hits the timeout; continue
                pass

            # Stream any newly collected lines to the UI
            for line in run_output[last_index:]:
                output += line + "\n"
                yield output
            last_index = len(run_output)

            # Check any newly streamed lines for common readiness messages
            new_lines = run_output[last_index:]
            for l in new_lines:
                lower = l.lower()
                # common Spring Boot readiness messages
                if "started application" in lower or "tomcat started" in lower or "started" in lower and "seconds" in lower:
                    output += "✅ Detected application startup in logs\n"
                    yield output
                    port_listening = True
                    break

            # Check if Java process is running
            try:
                ps_check = sandbox.commands.run("ps aux | grep java | grep -v grep || true", timeout=5)
                java_processes = ps_check.stdout.strip()
            except Exception:
                java_processes = ""

            if java_processes:
                output += "✅ Java process found running\n"
                yield output
                process_found = True

                # Now check if port 8080 is listening
                try:
                    port_check = sandbox.commands.run(
                        "netstat -tlnp 2>/dev/null | grep :8080 || ss -tlnp | grep :8080 || echo 'Port 8080 not listening'",
                        timeout=5,
                    )
                    port_status = port_check.stdout.strip()
                except Exception:
                    port_status = "Port check command failed"

                # Some systems show LISTEN or listening; check for 'listen' substring for robustness
                if "8080" in port_status and "listen" in port_status.lower():
                    output += "✅ Port 8080 is now listening\n"
                    yield output
                    port_listening = True
                    break
                else:
                    output += "⏳ Port 8080 not ready yet, continuing to stream logs...\n"
                    yield output
            else:
                output += "⏳ No Java process yet, continuing to stream logs...\n"
                yield output

            elapsed += chunk_seconds

        if not process_found:
            output += "❌ Java process not found after streaming period\n"
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
                    output += "📡 E2B Hostname: " + sandbox.get_host(port=8080) + "\n"
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


def run_app_and_preview():
    """Generator to start the app in a persistent sandbox for manual preview.

    Differences from `start_app_and_test`:
    - Sandbox is kept alive after the function returns and stored in `PREVIEW_SANDBOX`.
    - Sandbox is only killed when the user clicks the Stop preview button (stop_preview).
    """
    global PREVIEW_SANDBOX

    output = "🚀 Starting Spring Boot preview sandbox...\n"
    # show a small loading placeholder immediately so the preview area appears
    loading_html = "<div style='padding:12px;font-style:italic;color:#666;'>Preview starting…</div>"
    # first yields return (logs, preview_html)
    yield (output, gr.update(value=loading_html, visible=True))

    # Load API key
    api_key = os.getenv('E2B_API_KEY')
    if not api_key:
        output += "❌ E2B_API_KEY not found in environment variables\n"
        yield (output, gr.update(value="", visible=False))
        return

    sandbox = PREVIEW_SANDBOX
    created_here = False
    try:
        if sandbox is None:
            output += "🔧 Creating preview sandbox...\n"
            yield (output, gr.update(value=loading_html, visible=True))
            sandbox = Sandbox.create(template="springboot-dev", api_key=api_key)
            created_here = True
            output += "✅ Preview sandbox created\n"
            yield (output, gr.update(value=loading_html, visible=True))
        else:
            output += "ℹ️ Reusing existing preview sandbox\n"
            yield (output, gr.update(value=loading_html, visible=True))

        # Recreate project and build
        output += "📁 Uploading project files...\n"
        yield (output, gr.update(value=loading_html, visible=True))
        sandbox.commands.run("mkdir -p /home/user/spring-boot/src/main/java/com/example/springboot")

        pom_content = load_file("pom.xml")
        app_content = load_file("src/main/java/com/example/springboot/Application.java")
        controller_content = load_file("src/main/java/com/example/springboot/HelloController.java")

        sandbox.files.write("/home/user/spring-boot/pom.xml", pom_content)
        sandbox.files.write("/home/user/spring-boot/src/main/java/com/example/springboot/Application.java", app_content)
        sandbox.files.write("/home/user/spring-boot/src/main/java/com/example/springboot/HelloController.java", controller_content)

        # Build quietly
        output += "🔨 Building application (preview)...\n"
        yield (output, gr.update(value=loading_html, visible=True))
        build_result = sandbox.commands.run("cd /home/user/spring-boot && mvn clean package -DskipTests -q")
        if build_result.exit_code != 0:
            output += "❌ Build failed, cannot start preview app\n"
            yield (output, gr.update(value="", visible=False))
            # keep sandbox for debugging
            PREVIEW_SANDBOX = sandbox
            return

        output += "✅ Build successful\n"
        yield (output, gr.update(value=loading_html, visible=True))

        # Start the app in background
        jar_name = "target/spring-boot-0.0.1-SNAPSHOT.jar"
        start_cmd = f"cd /home/user/spring-boot && nohup java -jar {jar_name} > app.log 2>&1 & echo $!"
        output += f"🏃 Starting app: {start_cmd}\n"
        yield (output, gr.update(value=loading_html, visible=True))

        try:
            start_result = sandbox.commands.run(start_cmd, timeout=10)
            pid = start_result.stdout.strip()
            output += f"✅ Start command issued, PID: {pid}\n"
            yield (output, gr.update(value=loading_html, visible=True))
        except Exception as e:
            output += f"⚠️ Start command may have timed out or failed: {e}\n"
            yield (output, gr.update(value=loading_html, visible=True))

        # Stream a short amount of logs so the user can see startup and the E2B host
        try:
            tail_result = sandbox.commands.run("cd /home/user/spring-boot && tail -n 20 app.log", timeout=10)
            output += f"Recent logs:\n{tail_result.stdout}\n"
            yield (output, gr.update(value=loading_html, visible=True))
        except Exception:
            pass

        # Show the E2B host so user can open in browser
        html_preview = ""

        try:
            host = sandbox.get_host(port=8080)
            output += "📡 E2B Hostname: " + host + "\n"
            # build public url (ensure protocol)
            public_url = host
            if not public_url.startswith("http://") and not public_url.startswith("https://"):
                public_url = f"http://{public_url}"

            # build iframe HTML preview — force white background so content is readable in dark mode
            html_preview = f"""\n<div style='border:1px solid #ddd;width:100%;height:600px;background:#ffffff;color:#000;'>\n  <iframe src=\"{public_url}\" width=\"100%\" height=\"100%\" frameborder=\"0\" style=\"background:#ffffff;color:#000;\"></iframe>\n</div>\n<p style='color:#000'><strong>External link:</strong> <a href=\"{public_url}\" target=\"_blank\">{public_url}</a></p>\n"""

            output += f"Preview available at: {public_url}\n"
            # yield logs plus an update to show preview HTML
            PREVIEW_SANDBOX = sandbox
            yield (output, gr.update(value=html_preview, visible=True))
        except Exception as e:
            output += f"⚠️ Could not get preview host: {e}\n"
            PREVIEW_SANDBOX = sandbox
            yield (output, gr.update(value="", visible=False))

    except Exception as e:
        output += f"❌ Preview error: {e}\n"
        # hide preview on error
        PREVIEW_SANDBOX = sandbox
        yield (output, gr.update(value="", visible=False))
    # intentionally DO NOT kill the sandbox here; user will stop it manually


def stop_preview():
    """Generator to stop the persistent preview sandbox started by run_app_and_preview."""
    global PREVIEW_SANDBOX
    output = "🛑 Stopping preview sandbox...\n"
    # second output clears the preview HTML
    preview_val = ""
    yield (output, preview_val)
    if PREVIEW_SANDBOX:
        try:
            PREVIEW_SANDBOX.kill()
            output += "✅ Preview sandbox terminated\n"
            PREVIEW_SANDBOX = None
            yield (output, gr.update(value="", visible=False))
        except Exception as e:
            output += f"❌ Failed to stop preview sandbox: {e}\n"
            yield (output, gr.update(value="", visible=False))
    else:
        output += "ℹ️ No preview sandbox to stop\n"
        yield (output, gr.update(value="", visible=False))


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
                # Place preview control buttons side-by-side
                with gr.Row():
                    run_prev_btn = gr.Button("Run App & Preview", variant="primary")
                    stop_prev_btn = gr.Button("Stop App", variant="stop")
                logs = gr.Textbox(label="Build/Startup Output (streaming)", lines=25, interactive=False, show_copy_button=True)
                gr.Markdown("**Build**: Runs `mvn clean package -DskipTests` in E2B sandbox\n**Start App & Test**: Builds, starts the app, and tests the endpoint")
        # After the two-column row, place a full-width preview area so iframe is large
        with gr.Row():
            preview_html = gr.HTML(value="", visible=False)

        # Wire up events while still inside the Blocks context (now preview_html is defined)
        file_dropdown.change(fn=update_code, inputs=file_dropdown, outputs=code_display)
        # Button triggers generator which streams text into logs textbox
        run_btn.click(fn=build_and_stream, inputs=None, outputs=logs)
        start_app_btn.click(fn=start_app_and_test, inputs=None, outputs=logs)
        # Preview controls (now also update the full-width preview_html area)
        run_prev_btn.click(fn=run_app_and_preview, inputs=None, outputs=[logs, preview_html])
        stop_prev_btn.click(fn=stop_preview, inputs=None, outputs=[logs, preview_html])

    return demo


if __name__ == "__main__":
    app = make_demo()
    app.launch()
