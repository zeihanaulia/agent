"""
DEEP CODE ANALYSIS AGENT - Educational Implementation
======================================================

PURPOSE:
    This script demonstrates how to build an AI-powered code analysis agent
    that can explore and understand any codebase. It uses DeepAgents framework
    with custom tools to interact with the filesystem and analyze code structure,
    technology stack, architecture, and functionality.

KEY CONCEPTS:
    1. Tool Definition (@tool decorator) - How AI agents interact with external systems
    2. Agent Invocation - Running the agent with a specific task
    3. Message Processing - Understanding AI agent communication flow
    4. Result Extraction - Parsing agent responses for display

WORKFLOW:
    Step 1: Load environment & configure LLM (ChatOpenAI)
    Step 2: Define custom tools for filesystem access (list_directory, read_file, etc.)
    Step 3: Create analysis prompt that guides the agent
    Step 4: Instantiate DeepAgent with tools and prompt
    Step 5: Invoke agent with codebase path
    Step 6: Parse messages and display final analysis
"""

import argparse
import os
import sys
import time
from pathlib import Path

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
# Contains: LITELLM_MODEL, LITELLM_VIRTUAL_KEY, LITELLM_API
load_dotenv()

# ==============================================================================
# STEP 1: CONFIGURE THE AI MODEL
# ==============================================================================
# We need to set up the language model that will power our agent.
# This model will use the tools we define to understand and analyze code.

# Get configuration from environment or use defaults
model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
api_key = os.getenv("LITELLM_VIRTUAL_KEY")
api_base = os.getenv("LITELLM_API")

# Determine if this is a reasoning model (models with "thinking" capabilities)
# Reasoning models like GPT-5-mini work better with higher temperature (more creativity)
is_reasoning_model = any(
    keyword in model_name.lower()
    for keyword in ["gpt-5", "5-mini", "oss", "120b", "thinking", "reasoning"]
)

# Set temperature based on model type
# - Reasoning models: temperature=1.0 (more creative, explores more options)
# - Other models: temperature=0.1 (more focused, deterministic)
if is_reasoning_model:
    temperature = 1.0
else:
    temperature = 0.1

# Initialize the ChatOpenAI model with our configuration
# This model will be used by the agent to make decisions and analyze code
analysis_model = ChatOpenAI(
    api_key=lambda: api_key,  # pyright: ignore[reportArgumentType]
    model=model_name,
    base_url=api_base,
    temperature=temperature,
)


# ==============================================================================
# STEP 2: DEFINE CUSTOM TOOLS FOR FILESYSTEM ACCESS
# ==============================================================================
# AI agents need tools to interact with the external world. We define custom tools
# that allow the agent to:
# - List files in directories
# - Read file contents
# - Find files by pattern
# - Understand directory structure
#
# Each tool is decorated with @tool which tells DeepAgents to make it available
# to the AI agent. The docstring of each function becomes the tool's description.


@tool
def list_directory(path: str) -> str:
    """
    List all files and directories in a given path.
    
    PURPOSE:
        This tool allows the agent to see what files and folders exist in a directory.
        This is the first step in understanding a codebase structure.
    
    ARGUMENTS:
        path (str): The filesystem path to list. Can be absolute or relative.
                   Examples: "/Users/username/project", "src", "./config"
    
    RETURN VALUE (str):
        A formatted string listing all items in the directory with their type:
        - "[DIR]  folder_name/" for directories
        - "[FILE] file_name" for files
        Items are sorted alphabetically for easier reading.
        
        Returns error message if:
        - Path doesn't exist
        - Permission denied
        - Other filesystem errors
    
    WHY THIS TOOL:
        The agent needs to explore directories to understand project organization.
        Example: seeing [DIR] src/ tells agent where source code is located.
    """
    try:
        items = []
        p = Path(path)
        if not p.exists():
            return f"Path does not exist: {path}"

        for item in sorted(p.iterdir()):
            if item.is_dir():
                items.append(f"[DIR]  {item.name}/")
            else:
                items.append(f"[FILE] {item.name}")

        return "\n".join(items) if items else "Empty directory"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@tool
def read_file(file_path: str, max_lines: int = 100) -> str:
    """
    Read contents of a file (limited to max_lines to avoid overwhelming the agent).
    
    PURPOSE:
        This tool allows the agent to read and understand file contents.
        Used to read configuration files (pom.xml, package.json, etc.) and source code.
    
    ARGUMENTS:
        file_path (str): Full path to the file to read.
                        Examples: "src/main/java/Application.java", "pom.xml"
        
        max_lines (int): Maximum number of lines to return (default 100).
                        PURPOSE: Prevents flooding agent with huge file contents.
                        EXAMPLE: If file has 1000 lines, only first 100 are returned
                        with a message indicating more lines exist.
    
    RETURN VALUE (str):
        The file contents as a string, with each line as-is from the file.
        If file exceeds max_lines, includes a message like:
        "... (file has 1000 lines total, showing first 100)"
        
        Returns error message if:
        - File doesn't exist
        - Cannot read file (permission issues)
        - File encoding issues
    
    WHY THIS TOOL:
        The agent needs to read actual code and config files to understand:
        - Project dependencies (pom.xml, package.json)
        - Project structure and entry points
        - Technology stack and frameworks used
    """
    try:
        p = Path(file_path)
        if not p.exists():
            return f"File does not exist: {file_path}"

        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Return first max_lines
        content = "".join(lines[:max_lines])
        if len(lines) > max_lines:
            content += (
                f"\n... (file has {len(lines)} lines total, showing first {max_lines})"
            )

        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def find_files_by_pattern(directory: str, pattern: str) -> str:
    """
    Find files matching a pattern (e.g., '*.java', '*.md', '*.py').
    
    PURPOSE:
        This tool helps the agent quickly locate all files of a specific type.
        Without this, the agent would need to manually explore every folder.
    
    ARGUMENTS:
        directory (str): Starting directory to search in. Search is recursive
                        (includes all subdirectories).
                        Examples: "src", "/project/root", "."
        
        pattern (str): Glob pattern to match filenames.
                      Examples:
                      - "*.java" finds all Java files
                      - "*.json" finds all JSON files
                      - "README*" finds README files
                      - "test_*.py" finds Python test files
    
    RETURN VALUE (str):
        A list of relative file paths matching the pattern, one per line.
        Maximum 50 results returned (to avoid overwhelming agent).
        
        Returns error message if:
        - Directory doesn't exist
        - No files match the pattern
        - Permission issues
    
    WHY THIS TOOL:
        The agent uses this to:
        - Find all Java files in "src" directory
        - Find configuration files like "pom.xml", "package.json"
        - Find README or documentation files
        - Locate test files
    """
    try:
        p = Path(directory)
        if not p.exists():
            return f"Directory does not exist: {directory}"

        matches = list(p.rglob(pattern))
        if not matches:
            return f"No files matching pattern '{pattern}' found in {directory}"

        return "\n".join([str(m.relative_to(p)) for m in sorted(matches)[:50]])
    except Exception as e:
        return f"Error finding files: {str(e)}"


@tool
def get_directory_structure(path: str, max_depth: int = 3) -> str:
    """
    Get tree structure of directories (like 'tree' command in Unix).
    
    PURPOSE:
        This tool provides a visual representation of the directory structure.
        Helps agent understand the overall organization of the codebase at a glance.
    
    ARGUMENTS:
        path (str): Root directory to start tree from.
                   Examples: "/project", ".", "src"
        
        max_depth (int): How many levels deep to show (default 3).
                        PURPOSE: Prevents overwhelming agent with deeply nested structures.
                        EXAMPLE: max_depth=3 means show root/level1/level2/level3 only
    
    RETURN VALUE (str):
        A tree-like representation using box-drawing characters:
        - "├── " for items (not last in folder)
        - "└── " for last item in folder
        - "│   " for continuation lines
        - "[DIR]" suffix (/) for directories
        - No suffix for files
        
        Example output:
        ```
        project/
        ├── src/
        │   ├── main/
        │   │   └── java/
        │   └── test/
        ├── pom.xml
        └── README.md
        ```
    
    WHY THIS TOOL:
        The agent uses this to:
        - Get a quick overview of project structure
        - Understand standard layouts (Maven, Gradle, Node.js patterns)
        - Identify where source code, tests, and configs are located
    """
    try:
        p = Path(path)
        if not p.exists():
            return f"Path does not exist: {path}"

        def build_tree(directory: Path, prefix: str = "", depth: int = 0) -> list:
            if depth > max_depth:
                return []

            items = []
            try:
                children = sorted(
                    directory.iterdir(), key=lambda x: (not x.is_dir(), x.name)
                )
                for i, child in enumerate(children[:20]):  # Limit to 20 items per dir
                    is_last = i == len(children) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = "    " if is_last else "│   "

                    if child.is_dir():
                        items.append(f"{prefix}{current_prefix}{child.name}/")
                        items.extend(build_tree(child, prefix + next_prefix, depth + 1))
                    else:
                        items.append(f"{prefix}{current_prefix}{child.name}")
            except PermissionError:
                pass

            return items

        tree = [p.name + "/"] + build_tree(p)
        return "\n".join(tree)
    except Exception as e:
        return f"Error building tree: {str(e)}"


# Register all tools so the agent can use them
# Register all tools so the agent can use them
tools = [list_directory, read_file, find_files_by_pattern, get_directory_structure]

# ==============================================================================
# STEP 3: SETUP ARGUMENT PARSING AND CODEBASE PATH
# ==============================================================================
# We allow users to specify which codebase to analyze via command-line argument
# or environment variable, with a sensible default.

default_codebase_path = "/Users/zeihanaulia/Programming/research/agent/outputs/internal-developer-platform-project/active"

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "--codebase-path",
    "-p",
    dest="codebase_path",
    default=os.getenv("CODEBASE_PATH", default_codebase_path),
)
args, _ = parser.parse_known_args()
codebase_path = args.codebase_path

# If running interactively and user didn't supply a custom path, prompt once
if codebase_path == default_codebase_path and sys.stdin.isatty():
    user_input = input(f"Codebase path [{default_codebase_path}]: ").strip()
    if user_input:
        codebase_path = user_input

# ==============================================================================
# STEP 4: CREATE THE ANALYSIS PROMPT (Agent's Instructions)
# ==============================================================================
# This is the system prompt that tells the agent WHAT to do and HOW to do it.
# The agent uses our tools and this prompt to guide its analysis.

analysis_prompt = f"""\
You are an expert code analysis agent. Your primary goal is to analyze the codebase and provide a comprehensive understanding of the project.

CODEBASE PATH: {codebase_path}

CONTEXT:
- You have access to the full codebase and can use tools to explore it
- The workspace structure may be truncated, use tools to collect more context if needed
- Focus on gathering relevant context without going overboard

YOUR TASK:
1. **Gather Context**: Use tools to explore the directory structure and list files
2. **Identify Project Purpose**: Read README files, package.json, requirements.txt, pom.xml, or build.gradle to understand the project
3. **Analyze Code Content**: Read key source files to understand functionality
4. **Examine Architecture**: Map the project structure (folders, packages, layers)
5. **Summarize**: Provide a comprehensive overview with:
   - Project purpose and goals
   - Technology stack and dependencies
   - Architecture and main components
   - Key functionalities

TOOL USE INSTRUCTIONS:
- You can call multiple tools in one response when running multiple tools can answer the question
- Use tools to collect context instead of making assumptions
- Call tools repeatedly to gather as much context as needed until you have completed the task fully
- Prefer calling tools in parallel when possible
- Follow the tool schema carefully and include all required fields
- If a tool exists to do a task, use the tool instead of manual actions

AVAILABLE TOOLS:
- list_directory(path): List files and directories in a given path
- read_file(file_path, max_lines): Read contents of a file (limited to max_lines, default 100)
- find_files_by_pattern(directory, pattern): Find files matching a pattern (e.g., '*.py', '*.md', '*.json')
- get_directory_structure(path, max_depth): Get tree structure of directories (default max_depth=3)

ANALYSIS WORKFLOW:
1. First, check the directory structure to understand the project layout
2. Read key configuration files (README.md, package.json, requirements.txt, setup.py, etc.)
3. Find and read main source files to understand the core functionality
4. Analyze the architecture based on your findings
5. Provide your comprehensive analysis with concrete examples from the code

START EXPLORATION:
Begin by exploring the codebase structure and key files to build your understanding.
"""

agent = create_deep_agent(
    system_prompt=analysis_prompt,
    model=analysis_model,
    tools=tools,  # Add tools to agent
)

# ==============================================================================
# STEP 5: DISPLAY STARTUP INFORMATION AND RUN THE AGENT
# ==============================================================================
# Print verbose output to show the user what's happening

print("=" * 80)
print("🤖 DEEP CODE ANALYSIS AGENT (VERBOSE MODE)")
print("=" * 80)
print(f"📁 Target Codebase: {codebase_path}")
print(f"🛠️  Model: {model_name}")
print("💾 Backend: Custom Tools")
print(f"🌡️  Temperature: {temperature}")
print("=" * 80)
print("🔍 Starting analysis... This may take a few moments.")
print()

print(f"[{time.strftime('%H:%M:%S')}] 📋 Agent initialized with custom tools")
print(f"[{time.strftime('%H:%M:%S')}] 🔍 Starting codebase analysis...")

start_time = time.time()

# Invoke the agent with the analysis task
# The agent will:
# 1. Use the tools to explore the codebase
# 2. Make decisions about what to read/analyze
# 3. Generate a comprehensive analysis
# 4. Return all messages in the conversation history
result = agent.invoke(
    {
        "input": f"Please analyze the codebase at {codebase_path}"
    }
)

analysis_time = time.time() - start_time
print(f"[{time.strftime('%H:%M:%S')}] ✅ Analysis completed in {analysis_time:.2f} seconds")

# ==============================================================================
# STEP 6: EXTRACT AND DISPLAY RESULTS
# ==============================================================================
# Process the agent's messages to extract and display the final analysis

# Count tool calls made during the analysis
tool_call_counter = 0
if "messages" in result:
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_call_counter += len(msg.tool_calls)

print("\n📈 Analysis Summary:")
print(f"   • Tool calls made: {tool_call_counter}")
print(f"   • Analysis time: {analysis_time:.2f} seconds")
print(f"   • Average time per tool call: {analysis_time/tool_call_counter:.2f} seconds" if tool_call_counter > 0 else "   • No tool calls made")

print("\n" + "=" * 80)
print("📊 FINAL ANALYSIS RESULT:")
print("=" * 80)

# Extract and print only the final result
# The agent's last substantial AI message contains the comprehensive analysis
if "messages" in result:
    final_messages = []
    for msg in result["messages"]:
        msg_type = type(msg).__name__
        content = getattr(msg, "content", None)
        has_content = content is not None and str(content).strip()
        has_tool_calls = hasattr(msg, "tool_calls") and msg.tool_calls

        # We want AI messages that contain analysis (no tool calls)
        if has_content and not has_tool_calls and msg_type == "AIMessage":
            final_messages.append(str(content))

    # Show the last substantial AI message (usually the final analysis)
    if final_messages:
        print("FINAL RESULT:")
        print(final_messages[-1])
    else:
        print("No detailed analysis result found.")

# ==============================================================================
# OPTIONAL: DISPLAY DETAILED MESSAGE TRACE (for learning/debugging)
# ==============================================================================
# Uncomment this section to see all messages exchanged between agent and tools
# This helps understand HOW the agent worked to arrive at the conclusion

if "messages" in result:
    for i, msg in enumerate(result["messages"]):
        msg_type = type(msg).__name__

        if hasattr(msg, "content") and msg.content:
            print(f"\n[{msg_type}]")
            print(msg.content)

        elif hasattr(msg, "tool_calls") and msg.tool_calls:
            print("\n[Tool Calls]")
            for call in msg.tool_calls:
                tool_name = call.get("name", "Unknown")
                args = call.get("args", {})
                print(
                    f"  → {tool_name}({', '.join(f'{k}={v}' for k, v in args.items())})"
                )

        elif hasattr(msg, "name") and msg.name:
            print(f"\n[Tool Response: {msg.name}]")
            content = getattr(msg, "content", "No content")
            # Truncate long outputs for readability
            if len(str(content)) > 500:
                print(str(content)[:500] + "\n... (truncated)")
            else:
                print(content)

print("\n" + "=" * 80)
print("Analysis complete!")
print("=" * 80)
