"""
GRADIO CODE ANALYSIS WITH REPOSITORY CLONING
==============================================

PURPOSE:
    Web UI for Deep Code Analysis Agent with GitHub/GitLab repository cloning.
    Users can input a repository URL, clone it to the workspace, and analyze
    the codebase using the AI-powered code analysis agent.

FEATURES:
    1. Repository URL input (GitHub, GitLab, Gitea, etc.)
    2. Automatic clone to /dataset/codes/<repo_name>
    3. Codebase path selection from cloned repos
    4. AI-powered code analysis with FilesystemBackend
    5. Real-time progress updates and results display

WORKFLOW:
    1. User enters repository URL
    2. System validates URL and extracts repo name
    3. Clone repository to workspace (if not exists)
    4. User selects codebase path or auto-detect
    5. Run analysis agent and stream results
    6. Display comprehensive analysis in Gradio UI

REQUIREMENTS:
    - gradio
    - deepagents
    - langchain-openai
    - python-dotenv
    - gitpython (for git operations)
    - pydantic
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

import gradio as gr
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Import DeepAgents components
try:
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend
except ImportError:
    raise ImportError(
        "deepagents is not installed. Please run:\n"
        "  pip install deepagents langchain-openai python-dotenv"
    )

# Load environment variables
load_dotenv()

# ==============================================================================
# CONFIGURATION
# ==============================================================================

WORKSPACE_ROOT = Path("/Users/zeihanaulia/Programming/research/agent/dataset/codes")
DEFAULT_MODEL = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("LITELLM_VIRTUAL_KEY")
API_BASE = os.getenv("LITELLM_API")

# Ensure workspace exists
WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================


def extract_repo_name(repo_url: str) -> str:
    """Extract repository name from URL.
    
    Examples:
        https://github.com/user/my-repo.git -> my-repo
        https://github.com/user/my-repo -> my-repo
        git@github.com:user/my-repo.git -> my-repo
    """
    # Remove .git suffix if present
    repo_url = repo_url.rstrip("/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    
    # Extract from URL
    if "://" in repo_url:
        # HTTPS URL: https://github.com/user/repo
        path_part = urlparse(repo_url).path
    else:
        # SSH URL: git@github.com:user/repo
        path_part = repo_url.split(":")[-1]
    
    # Get last component of path
    repo_name = path_part.rstrip("/").split("/")[-1]
    return repo_name or "repo"


def validate_git_url(url: str) -> Tuple[bool, str]:
    """Validate if URL is a valid Git repository URL."""
    url = url.strip()
    
    if not url:
        return False, "❌ Repository URL is empty"
    
    # Check for common Git URL patterns
    valid_patterns = [
        "github.com",
        "gitlab.com",
        "gitea",
        "git@",
        ".git",
        "://",
    ]
    
    if not any(pattern in url for pattern in valid_patterns):
        return False, "❌ Invalid Git URL. Expected GitHub, GitLab, or Gitea URL"
    
    return True, "✅ URL format valid"


def clone_repository(repo_url: str) -> Tuple[bool, str, Optional[str]]:
    """Clone repository to workspace.
    
    Returns:
        (success, message, local_path)
    """
    # Validate URL
    is_valid, msg = validate_git_url(repo_url)
    if not is_valid:
        return False, msg, None
    
    # Extract repo name
    repo_name = extract_repo_name(repo_url)
    local_path = WORKSPACE_ROOT / repo_name
    
    # Check if already cloned
    if local_path.exists():
        return True, f"✅ Repository already cloned at: {local_path}", str(local_path)
    
    # Clone repository
    try:
        print(f"🔄 Cloning {repo_url}...")
        result = subprocess.run(
            ["git", "clone", repo_url, str(local_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            return False, f"❌ Failed to clone repository:\n{error_msg}", None
        
        return True, f"✅ Successfully cloned to: {local_path}", str(local_path)
    
    except subprocess.TimeoutExpired:
        return False, "❌ Clone operation timed out (>5 minutes)", None
    except Exception as e:
        return False, f"❌ Error cloning repository:\n{str(e)}", None


def list_available_codebases() -> list:
    """List all available cloned repositories in workspace.
    
    Includes:
    - Git repositories (with .git directory)
    - Local codebases (any subdirectory with source files)
    - Excludes: __pycache__, .DS_Store, etc.
    """
    if not WORKSPACE_ROOT.exists():
        return []
    
    codebases = []
    exclude_patterns = {".DS_Store", "__pycache__", ".pytest_cache", ".git"}
    
    for item in WORKSPACE_ROOT.iterdir():
        # Skip hidden files and common ignore patterns
        if item.name.startswith(".") or item.name in exclude_patterns:
            continue
        
        # Include any directory (git repos or local codebases)
        if item.is_dir():
            codebases.append(str(item))
    
    return sorted(codebases)


def validate_environment() -> Tuple[bool, str]:
    """Validate that required environment variables are set."""
    if not API_KEY:
        return False, "❌ Missing LITELLM_VIRTUAL_KEY environment variable"
    if not API_BASE:
        return False, "❌ Missing LITELLM_API environment variable"
    
    return True, "✅ Environment configured"


# ==============================================================================
# ANALYSIS ENGINE
# ==============================================================================


def run_code_analysis(codebase_path: str, progress=None, mode: str = "Detailed (Full)") -> Tuple[bool, str]:
    """Run code analysis on specified codebase.
    
    Args:
        codebase_path: Path to codebase to analyze
        progress: Gradio progress callback
        mode: Analysis mode - "Fast (Summary)" or "Detailed (Full)"
    
    Returns:
        (success, analysis_result_or_error_message)
    """
    # Validate environment
    is_valid, msg = validate_environment()
    if not is_valid:
        return False, msg
    
    # Validate path
    codebase_path = str(codebase_path).strip()
    if not codebase_path:
        return False, "❌ Codebase path is empty"
    
    if not os.path.exists(codebase_path):
        return False, f"❌ Codebase path does not exist: {codebase_path}"
    
    if not os.path.isdir(codebase_path):
        return False, f"❌ Codebase path is not a directory: {codebase_path}"
    
    codebase_path = os.path.abspath(codebase_path)
    
    # Update progress
    if progress:
        progress(0.1, desc="🧠 Configuring AI model...")
    
    try:
        # Configure AI model
        is_reasoning_model = any(
            keyword in DEFAULT_MODEL.lower()
            for keyword in ["gpt-5", "5-mini", "oss", "120b", "thinking", "reasoning"]
        )
        temperature = 1.0 if is_reasoning_model else 0.7
        
        # Validate API credentials before creating model
        if not API_KEY or not API_BASE:
            return False, "❌ Missing API credentials (LITELLM_VIRTUAL_KEY or LITELLM_API)"
        
        analysis_model = ChatOpenAI(
            api_key=SecretStr(API_KEY),
            model=DEFAULT_MODEL,
            base_url=API_BASE,
            temperature=temperature,
        )
        
        # Update progress
        if progress:
            progress(0.2, desc="💾 Initializing filesystem backend...")
        
        # Configure backend
        backend = FilesystemBackend(root_dir=codebase_path)
        
        # Create analysis prompt based on mode
        if mode == "Fast (Summary)":
            analysis_prompt = f"""\
You are a code analysis agent. Quickly analyze the codebase and provide a BRIEF summary (max 500 words).

CODEBASE PATH: {codebase_path}

QUICK ANALYSIS (5-10 minutes work):
1. Use ls to see main directory structure
2. Find and skim key files: README, package.json, pom.xml, requirements.txt, main.go
3. Identify 2-3 main source files and read them briefly
4. Provide SHORT summary:
   - Project name and purpose (1-2 lines)
   - Tech stack (1 line)
   - Main components (3-5 bullets)

KEEP IT SHORT AND FAST.
"""
        else:
            # Detailed mode
            analysis_prompt = f"""\
You are an expert code analysis agent. Your primary goal is to analyze the codebase and provide a comprehensive understanding of the project.

CODEBASE PATH: {codebase_path}

YOUR TASK:
1. **Gather Context**: Use ls and glob to explore the directory structure
2. **Identify Project Purpose**: Read README files, package.json, requirements.txt, pom.xml, build.gradle to understand the project
3. **Analyze Code Content**: Read key source files to understand functionality
4. **Examine Architecture**: Map the project structure (folders, packages, layers)
5. **Summarize**: Provide a comprehensive overview with:
   - Project purpose and goals
   - Technology stack and dependencies
   - Architecture and main components
   - Key functionalities

BUILT-IN TOOLS (automatically available):
- ls(path): List files and directories with metadata
- read_file(path, offset, limit): Read file contents with pagination
- write_file(path, content): Create new files
- edit_file(path, old_string, new_string): Perform exact string replacements
- glob(pattern): Find files matching patterns
- grep(pattern, path, glob): Fast text search

WORKFLOW:
1. Use ls or glob to understand the project layout
2. Read key configuration files (README.md, package.json, requirements.txt, etc.)
3. Find and read main source files to understand core functionality
4. Analyze the architecture
5. Provide comprehensive analysis with concrete examples

START EXPLORATION:
Begin analyzing the codebase now.
"""
        
        # Update progress
        if progress:
            progress(0.3, desc="🤖 Creating analysis agent...")
        
        # Create agent
        agent = create_deep_agent(
            system_prompt=analysis_prompt,
            model=analysis_model,
            backend=backend,
        )
        
        # Update progress
        if progress:
            progress(0.5, desc="🔍 Running analysis... (this may take a minute)")
        
        # Run analysis with timeout
        start_time = time.time()
        try:
            result = agent.invoke(
                {
                    "input": f"Please analyze the codebase at {codebase_path}",
                },
                timeout=120  # 2 minute timeout max
            )
        except TimeoutError:
            return False, "⏱️ Analysis timed out (120s). Try a smaller codebase or check network."
        except Exception as e:
            return False, f"❌ Analysis failed: {str(e)}"
        
        analysis_time = time.time() - start_time
        
        # Update progress
        if progress:
            progress(0.8, desc="📊 Extracting results...")
        
        # Extract final analysis
        if not result or not isinstance(result, dict):
            return False, "❌ Agent returned invalid result structure"
        
        # Count tool calls
        tool_call_counter = 0
        if "messages" in result:
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_call_counter += len(msg.tool_calls)
        
        # Extract final AI message
        final_analysis = None
        if "messages" in result:
            for msg in result["messages"]:
                msg_type = type(msg).__name__
                content = getattr(msg, "content", None)
                has_content = content is not None and str(content).strip()
                has_tool_calls = hasattr(msg, "tool_calls") and msg.tool_calls
                
                if has_content and not has_tool_calls and msg_type == "AIMessage":
                    final_analysis = str(content)
        
        if not final_analysis:
            return False, "❌ No analysis result found"
        
        # Format output
        output = f"""
📊 **ANALYSIS SUMMARY**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 **Codebase Path**: {codebase_path}
🤖 **Model**: {DEFAULT_MODEL}
🌡️ **Temperature**: {temperature}
⏱️ **Analysis Time**: {analysis_time:.2f} seconds
🔧 **Tool Calls**: {tool_call_counter}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **DETAILED ANALYSIS**:

{final_analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Analysis completed successfully!
"""
        
        if progress:
            progress(1.0, desc="✅ Complete!")
        
        return True, output
    
    except Exception as e:
        error_msg = f"❌ Analysis failed:\n{str(e)}"
        import traceback
        traceback.print_exc()
        return False, error_msg


# ==============================================================================
# GRADIO INTERFACE
# ==============================================================================


def create_gradio_interface():
    """Create the Gradio web interface."""
    
    with gr.Blocks(title="🤖 Code Analysis Agent") as app:
        gr.Markdown(
            """
# 🤖 Deep Code Analysis Agent
### AI-Powered Repository Analysis with Git Integration
            """
        )
        
        # Info section
        with gr.Accordion("ℹ️ How to use", open=False):
            gr.Markdown(
                """
1. **Enter Repository URL**: Paste GitHub/GitLab repository URL
2. **Clone Repository**: System clones repo to workspace automatically
3. **Select Codebase**: Choose cloned repository or enter custom path
4. **Run Analysis**: Click to analyze with AI agent
5. **View Results**: See comprehensive code analysis

**Supported URLs**:
- HTTPS: `https://github.com/user/repo.git`
- SSH: `git@github.com:user/repo.git`
- GitHub: `https://github.com/user/repo`
- GitLab: `https://gitlab.com/user/repo`
                """
            )
        
        # Main interface
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📚 Step 1: Clone Repository")
                repo_url_input = gr.Textbox(
                    label="Repository URL",
                    placeholder="https://github.com/user/repo.git",
                    lines=1,
                )
                
                with gr.Row():
                    clone_btn = gr.Button("🔄 Clone Repository", scale=1)
                    refresh_btn = gr.Button("🔃 Refresh List", scale=1)
                
                # Analysis mode selector
                gr.Markdown("### ⚡ Analysis Mode")
                analysis_mode = gr.Radio(
                    choices=["Fast (Summary)", "Detailed (Full)"],
                    value="Detailed (Full)",
                    label="Analysis Depth",
                )
                
                clone_status = gr.Textbox(
                    label="Clone Status",
                    interactive=False,
                    lines=2,
                )
                
                gr.Markdown("### 🎯 Step 2: Select Codebase")
                codebase_dropdown = gr.Dropdown(
                    choices=list_available_codebases(),
                    label="Available Codebases",
                    interactive=True,
                )
                
                manual_path = gr.Textbox(
                    label="Or enter custom path",
                    placeholder="/path/to/codebase",
                    lines=1,
                )
                
                gr.Markdown("### ▶️ Step 3: Run Analysis")
                analyze_btn = gr.Button("🚀 Run Analysis", variant="primary", scale=1)
            
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Analysis Results")
                analysis_output = gr.Textbox(
                    label="Analysis Output",
                    lines=20,
                    max_lines=50,
                    interactive=False,
                )
        
        # Event handlers
        def clone_repo_handler(repo_url: str):
            """Handle clone button click."""
            if not repo_url.strip():
                return "❌ Please enter a repository URL"
            
            success, message, local_path = clone_repository(repo_url)
            
            # Refresh codebase list
            updated_choices = list_available_codebases()
            
            return message, gr.Dropdown(choices=updated_choices, value=local_path)
        
        def refresh_list_handler():
            """Handle refresh button click."""
            updated_choices = list_available_codebases()
            return gr.Dropdown(choices=updated_choices)
        
        def get_codebase_path(dropdown_choice: str, manual_input: str) -> str:
            """Get codebase path from either dropdown or manual input."""
            if manual_input and manual_input.strip():
                return manual_input.strip()
            return dropdown_choice or ""
        
        def analyze_handler(dropdown_choice: str, manual_input: str, selected_mode: str):
            """Handle analyze button click."""
            codebase_path = get_codebase_path(dropdown_choice, manual_input)
            
            if not codebase_path:
                return "❌ Please select or enter a codebase path"
            
            success, result = run_code_analysis(codebase_path, mode=selected_mode)
            return result
        
        # Connect events
        clone_btn.click(
            clone_repo_handler,
            inputs=[repo_url_input],
            outputs=[clone_status, codebase_dropdown],
        )
        
        refresh_btn.click(
            refresh_list_handler,
            outputs=[codebase_dropdown],
        )
        
        analyze_btn.click(
            analyze_handler,
            inputs=[codebase_dropdown, manual_path, analysis_mode],
            outputs=[analysis_output],
        )
        
        # Initialize dropdown on load
        app.load(
            lambda: gr.Dropdown(choices=list_available_codebases()),
            outputs=[codebase_dropdown],
        )
    
    return app


# ==============================================================================
# MAIN
# ==============================================================================


if __name__ == "__main__":
    # Validate environment
    is_valid, msg = validate_environment()
    if not is_valid:
        print(msg)
        print("\nPlease set required environment variables in .env:")
        print("  LITELLM_VIRTUAL_KEY=<your-api-key>")
        print("  LITELLM_API=<api-base-url>")
        sys.exit(1)
    
    print("✅ Environment validated")
    print(f"📁 Workspace: {WORKSPACE_ROOT}")
    print(f"🤖 Model: {DEFAULT_MODEL}")
    
    # Create and launch interface
    app = create_gradio_interface()
    
    print("\n🚀 Starting Gradio server...")
    print("📱 Open http://localhost:7860 in your browser")
    
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        share=False,
    )
