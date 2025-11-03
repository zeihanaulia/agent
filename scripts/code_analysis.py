"""
DEEP CODE ANALYSIS AGENT - Educational Implementation
======================================================

PURPOSE:
    This script demonstrates how to build an AI-powered code analysis agent
    that can explore and understand any codebase. It uses DeepAgents framework
    with built-in FilesystemBackend to interact with the filesystem and analyze
    code structure, technology stack, architecture, and functionality.

KEY CONCEPTS:
    1. FilesystemBackend - LangChain's built-in filesystem abstraction following BackendProtocol
    2. create_deep_agent - Creating agents with filesystem middleware via backend
    3. Built-in tools - ls, read_file, write_file, edit_file, glob, grep (auto-provided)
    4. Agent Invocation - Running the agent with a specific task
    5. Message Processing - Understanding AI agent communication flow
    6. Result Extraction - Parsing agent responses for display

WORKFLOW:
    Step 1: Load environment & configure LLM (ChatOpenAI)
    Step 2: Configure FilesystemBackend with root_dir for secure filesystem access
    Step 3: Create analysis prompt that guides the agent
    Step 4: Instantiate DeepAgent with backend and prompt
    Step 5: Invoke agent with codebase path
    Step 6: Parse messages and display final analysis

BEST PRACTICES:
    - Use FilesystemBackend for real filesystem access with security
    - Leverage built-in tools (ls, read_file, glob, grep) - no custom tools needed
    - Set absolute root_dir to sandbox agent filesystem access
    - Agent automatically gets 6 filesystem tools via backend
"""

import argparse
import os
import sys
import time

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

# Load environment variables from .env file
# Contains: LITELLM_MODEL, LITELLM_VIRTUAL_KEY, LITELLM_API
# Optional: LANGSMITH_API_KEY, LANGSMITH_PROJECT for observability
load_dotenv()

# ==============================================================================
# STEP 1: CONFIGURE THE AI MODEL
# ==============================================================================
# We need to set up the language model that will power our agent.
# This model will use the built-in tools from FilesystemBackend to analyze code.

# Get configuration from environment or use defaults
model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
api_key = os.getenv("LITELLM_VIRTUAL_KEY")
api_base = os.getenv("LITELLM_API")

# Validate that required environment variables are set
if not api_key or not api_base:
    raise ValueError(
        "Missing required environment variables:\n"
        "  LITELLM_VIRTUAL_KEY: LLM API key\n"
        "  LITELLM_API: LLM API base URL\n"
        "Please set these in your .env file or environment."
    )

# Determine if this is a reasoning model (models with "thinking" capabilities)
# Some models like GPT-5-mini ONLY support temperature=1.0
# Some models like gpt-oss-120b require specific temperature values
is_reasoning_model = any(
    keyword in model_name.lower()
    for keyword in ["gpt-5", "5-mini", "oss", "120b", "thinking", "reasoning"]
)

# Set temperature based on model type
# - Reasoning models: temperature=1.0 (required, more creative, explores more options)
# - Other models: temperature=0.7 (balanced, good for analysis)
# NOTE: azure/gpt-5-mini only supports temperature=1.0, not 0.1
if is_reasoning_model:
    temperature = 1.0
else:
    temperature = 0.7  # Changed from 0.1 to 0.7 for broader model compatibility

# Initialize the ChatOpenAI model with our configuration
# Use SecretStr for API key to satisfy type requirements
analysis_model = ChatOpenAI(
    api_key=SecretStr(api_key),
    model=model_name,
    base_url=api_base,
    temperature=temperature,
)


# ==============================================================================
# STEP 2: CONFIGURE FILESYSTEM BACKEND
# ==============================================================================
# LangChain's FilesystemBackend provides built-in filesystem tools following
# the BackendProtocol. This is a best practice alternative to custom tools.
#
# Built-in tools provided automatically:
#   - ls: List files with metadata (size, modified_at, is_dir)
#   - read_file: Read file contents with offset/limit support for large files
#   - write_file: Create new files with content validation
#   - edit_file: Perform exact string replacements in files
#   - glob: Advanced pattern matching with recursive support
#   - grep: Fast text search with ripgrep integration
#
# Benefits of using built-in backend:
#   ✓ No custom tool definition needed (@tool decorators eliminated)
#   ✓ Built-in security features (path validation, symlink protection)
#   ✓ Automatic large content handling (eviction to filesystem)
#   ✓ LangGraph state integration via BackendProtocol
#   ✓ Multiple backend support (FilesystemBackend, StateBackend, StoreBackend, etc.)

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

# Validate that codebase path exists and is accessible
if not os.path.exists(codebase_path):
    raise ValueError(
        f"Codebase path does not exist: {codebase_path}\n"
        f"Please provide a valid path using --codebase-path or CODEBASE_PATH env var"
    )

if not os.path.isdir(codebase_path):
    raise ValueError(
        f"Codebase path is not a directory: {codebase_path}\n"
        f"Please provide a directory path"
    )

# Convert to absolute path for consistency
codebase_path = os.path.abspath(codebase_path)

# ==============================================================================
# STEP 4: CREATE THE ANALYSIS PROMPT (Agent's Instructions)
# ==============================================================================
# This is the system prompt that tells the agent WHAT to do and HOW to do it.
# The agent uses built-in filesystem tools via FilesystemBackend and this prompt
# to guide its analysis.

analysis_prompt = f"""\
You are an expert code analysis agent. Your primary goal is to analyze the codebase and provide a comprehensive understanding of the project.

CODEBASE PATH: {codebase_path}

CONTEXT:
- You have access to the full codebase via built-in filesystem tools
- The workspace structure may be truncated, use tools to collect more context if needed
- Focus on gathering relevant context without going overboard

YOUR TASK:
1. **Gather Context**: Use ls and glob to explore the directory structure
2. **Identify Project Purpose**: Read README files, package.json, requirements.txt, pom.xml, or build.gradle to understand the project
3. **Analyze Code Content**: Read key source files to understand functionality
4. **Examine Architecture**: Map the project structure (folders, packages, layers)
5. **Summarize**: Provide a comprehensive overview with:
   - Project purpose and goals
   - Technology stack and dependencies
   - Architecture and main components
   - Key functionalities

BUILT-IN FILESYSTEM TOOLS (automatically available):
- ls(path): List files and directories with metadata (size, modified_at, is_dir)
- read_file(path, offset, limit): Read file contents with line numbers and pagination
- write_file(path, content): Create new files
- edit_file(path, old_string, new_string): Perform exact string replacements
- glob(pattern): Find files matching patterns (supports **/*.py recursive patterns)
- grep(pattern, path, glob): Fast text search with context

ANALYSIS WORKFLOW:
1. First, use ls or glob to understand the project layout
2. Read key configuration files (README.md, package.json, requirements.txt, setup.py, etc.)
3. Find and read main source files to understand the core functionality
4. Analyze the architecture based on your findings
5. Provide your comprehensive analysis with concrete examples from the code

TOOL USE BEST PRACTICES:
- Use glob() for pattern matching: glob("**/*.py"), glob("*.json"), glob("src/**/*.java")
- Use read_file() with offset/limit for pagination on large files
- Use grep() to search for specific patterns across files
- Combine tools in one response when possible to reduce turns

START EXPLORATION:
Begin by exploring the codebase structure and key files to build your understanding.
"""

# ==============================================================================
# STEP 5: INSTANTIATE DEEP AGENT WITH FILESYSTEM BACKEND
# ==============================================================================
# Create the deep agent with FilesystemBackend for real filesystem access.
# The backend provides all 6 filesystem tools (ls, read_file, write_file, etc.)
# without needing custom tool definitions.

# Configure FilesystemBackend with the codebase path
# This ensures the agent can only access files under root_dir (security feature)
try:
    backend = FilesystemBackend(root_dir=codebase_path)
except Exception as e:
    raise RuntimeError(
        f"Failed to initialize FilesystemBackend with root_dir={codebase_path}\n"
        f"Error: {str(e)}"
    ) from e

# Create the deep agent with backend
# Note: DeepAgents will automatically provide 6 built-in filesystem tools
try:
    agent = create_deep_agent(
        system_prompt=analysis_prompt,
        model=analysis_model,
        backend=backend,  # Pass backend instead of tools
    )
except Exception as e:
    raise RuntimeError(
        f"Failed to create deep agent with FilesystemBackend\n"
        f"Error: {str(e)}"
    ) from e

# ==============================================================================
# STEP 6: DISPLAY STARTUP INFORMATION AND RUN THE AGENT
# ==============================================================================
# Print verbose output to show the user what's happening

print("=" * 80)
print("🤖 DEEP CODE ANALYSIS AGENT (VERBOSE MODE)")
print("=" * 80)
print(f"📁 Target Codebase: {codebase_path}")
print(f"🛠️  Model: {model_name}")
print("💾 Backend: FilesystemBackend (LangChain Built-in)")
print(f"🌡️  Temperature: {temperature}")
print("=" * 80)
print("🔍 Starting analysis... This may take a few moments.")
print()

print(f"[{time.strftime('%H:%M:%S')}] 📋 Agent initialized with FilesystemBackend")
print(f"[{time.strftime('%H:%M:%S')}] 🔍 Starting codebase analysis...")

start_time = time.time()

# Invoke the agent with the analysis task
# The agent will:
# 1. Use the tools to explore the codebase
# 2. Make decisions about what to read/analyze
# 3. Generate a comprehensive analysis
# 4. Return all messages in the conversation history

try:
    result = agent.invoke(
        {
            "input": f"Please analyze the codebase at {codebase_path}",
        },
        # Add timeout to prevent infinite loops (in seconds)
        # Note: This requires LangGraph version that supports timeout
    )
except TimeoutError as e:
    print(f"❌ Agent analysis timed out: {str(e)}")
    print("The agent took too long to complete the analysis.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during agent execution: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

analysis_time = time.time() - start_time
print(f"[{time.strftime('%H:%M:%S')}] ✅ Analysis completed in {analysis_time:.2f} seconds")

# ==============================================================================
# STEP 7: EXTRACT AND DISPLAY RESULTS
# ==============================================================================
# Process the agent's messages to extract and display the final analysis

# Validate result structure
if not result or not isinstance(result, dict):
    print("❌ Error: Agent returned invalid result structure")
    sys.exit(1)

# Count tool calls made during the analysis
tool_call_counter = 0
if "messages" in result:
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_call_counter += len(msg.tool_calls)
else:
    print("⚠️  Warning: No messages found in result")

print("\n📈 Analysis Summary:")
print(f"   • Tool calls made: {tool_call_counter}")
print(f"   • Analysis time: {analysis_time:.2f} seconds")
if tool_call_counter > 0:
    print(f"   • Average time per tool call: {analysis_time/tool_call_counter:.2f} seconds")
else:
    print("   • No tool calls made (agent may have failed or been blocked)")

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
        print("❌ No detailed analysis result found.")
        if tool_call_counter == 0:
            print("\nPossible reasons:")
            print("  1. Agent failed to initialize properly")
            print("  2. Model API key or credentials are invalid")
            print("  3. Backend failed to provide filesystem tools")
            print("  4. Agent got stuck in infinite loop (check LangSmith trace)")
else:
    print("❌ Error: No messages in result")

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
