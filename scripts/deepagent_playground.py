# %pip install langchain langchain-openai dotenv pydantic

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool

from dotenv import load_dotenv
import os
import sys
from pydantic import SecretStr
import pprint
from debug_formatter import DebugFormatter

@tool
def search_web(query: str) -> str:
    """Search the web for the given query and return a summary of the results."""
    # Implementation of web search
    print(f"🔍 SUBAGENT: Using search_web tool with query: '{query}'")
    result = f"Mock Search results for: {query}"
    print(f"🔍 SUBAGENT: Search completed, returning result")
    return result

@tool
def list_directory(path: str = ".") -> str:
    """List files and directories in the specified path."""
    import os
    try:
        items = os.listdir(path)
        result = f"Contents of {path}:\n"
        for item in sorted(items):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                result += f"📁 {item}/\n"
            else:
                size = os.path.getsize(item_path)
                result += f"📄 {item} ({size} bytes)\n"
        print(f"📂 FILESYSTEM: Listed directory {path}")
        return result
    except Exception as e:
        return f"Error listing directory {path}: {e}"

@tool
def read_file_content(file_path: str) -> str:
    """Read the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"📖 FILESYSTEM: Read file {file_path} ({len(content)} chars)")
        return f"Content of {file_path}:\n\n{content}"
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

@tool
def write_file_content(file_path: str, content: str) -> str:
    """Write content to a new file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✏️ FILESYSTEM: Wrote {len(content)} chars to {file_path}")
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to file {file_path}: {e}"

@tool
def edit_file_content(file_path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing old_string with new_string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_string not in content:
            return f"Error: '{old_string}' not found in {file_path}"

        new_content = content.replace(old_string, new_string, 1)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"🔧 FILESYSTEM: Edited {file_path}, replaced '{old_string}' with '{new_string}'")
        return f"Successfully edited {file_path}"
    except Exception as e:
        return f"Error editing file {file_path}: {e}"

@tool
def write_real_file(path: str, content: str) -> str:
    """Write content to a real file on disk (not virtual filesystem)."""
    import os
    try:
        full_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 REAL FILESYSTEM: Wrote {len(content)} chars to {full_path}")
        return f"✅ File written to {full_path}"
    except Exception as e:
        return f"Error writing to real file {path}: {e}"

# load .env from root
load_dotenv()

# prefer LiteLLM key, fallback to OpenAI key
litellm_key = os.getenv("LITELLM_VIRTUAL_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

key = litellm_key or openai_key
if not key:
    raise SystemExit(
        "Missing API key: set LITELLM_VIRTUAL_KEY (for LiteLLM local proxy) or OPENAI_API_KEY in your environment or ../.env.\n"
        "Example (zsh): export OPENAI_API_KEY=your_key_here\n"
        "If you intended to use a local LiteLLM instance, set LITELLM_VIRTUAL_KEY and ensure the base URL is available."
    )

# If using LiteLLM provide the local base_url, otherwise leave base_url unset for OpenAI
base_url = os.getenv("LITELLM_API") if litellm_key else None

try:
    model = ChatOpenAI(
        base_url=base_url,
        api_key=SecretStr(key),  # pydantic SecretStr wrapper
        model=os.getenv("LITELLM_MODEL", "gpt-4o-mini"),
    )
except Exception as e:
    # give a clearer message for common environment misconfiguration
    raise SystemExit(
        f"Failed to initialize ChatOpenAI client: {e}\n"
        "Check that your API key is valid and that environment variables are set (OPENAI_API_KEY or LITELLM_VIRTUAL_KEY)."
    )


print("\n" + "="*80)
print("🚀 BASIC AGENT (create_agent) - Simple Tool Calling")
print("="*80 + "\n")

agent = create_agent(
    model, 
    tools=[search_web]
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user", 
                "content": "Research the history of artificial intelligence and summarize the key milestones."
            }
        ]
    }
)

for message in result['messages']:
    if hasattr(message, 'type'):
        msg_type = message.type
    else:
        msg_type = type(message).__name__

    # Human message
    if msg_type == 'human':
        print(f"\n👤 USER: {message.content}")

    # AI message
    elif msg_type == 'ai':
        print(f"\n🤖 AI [{msg_type.upper()}]:")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"   🛠️  TOOL CALLS:")
            for i, call in enumerate(message.tool_calls, 1):
                tool_name = call['name']
                tool_args = call['args']
                print(f"      {i}. {tool_name.upper()}({tool_args})")
        elif hasattr(message, 'content') and message.content:
            print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")

    # Tool message
    elif msg_type == 'tool':
        tool_name = getattr(message, 'name', 'unknown_tool')
        print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
        print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")







# Implementation deepagents subagent experiment
from deepagents import create_deep_agent, CompiledSubAgent
from langchain_core.tools import tool
from langchain.agents import create_agent



print("\n" + "="*80)
experiment = "(create_deep_agent) - Planning"
print(f"🚀 DEEP AGENT {experiment}")
print("="*80 + "\n")

# Replace stdout with our formatter
debug_formatter = DebugFormatter()
debug_formatter.set_experiment(experiment)
sys.stdout = debug_formatter

planning_agent = create_deep_agent(
    model=model,  # Pass the pre-configured ChatOpenAI model instance
    tools=[search_web],
    system_prompt="""You're a planning agent that breaks down complex tasks into steps.
    For research tasks requiring web search, delegate to your 'researcher' subagent using the task() tool.
    This ensures specialized tools are used effectively.""",

    debug=True  # Enable debug mode to see internal subagent activity
)

result = planning_agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "Plan my birthday party with a 90s theme. Research popular 90s music, fashion, and food."
        }
    ]
})

# Process final result messages (human-readable summary)
for message in result['messages']:
    if hasattr(message, 'type'):
        msg_type = message.type
    else:
        msg_type = type(message).__name__

    # Human message
    if msg_type == 'human':
        print(f"\n👤 USER: {message.content}")

    # AI message
    elif msg_type == 'ai':
        print(f"\n🤖 AI [{msg_type.upper()}]:")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"   🛠️  TOOL CALLS:")
            for i, call in enumerate(message.tool_calls, 1):
                tool_name = call['name']
                tool_args = call['args']
                print(f"      {i}. {tool_name.upper()}({tool_args})")
        elif hasattr(message, 'content') and message.content:
            print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")

    # Tool message
    elif msg_type == 'tool':
        tool_name = getattr(message, 'name', 'unknown_tool')
        print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
        print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")



print("\n" + "="*80)
experiment = "(create_deep_agent) - Deep Agent Subagent"
print(f"🚀 DEEP AGENT {experiment}")
print("="*80 + "\n")

# Replace stdout with our formatter
debug_formatter.set_experiment(experiment)


# Create a custom agent graph for the researcher subagent
researcher_graph = create_agent(
    model=model,
    tools=[search_web],
    system_prompt="""
You are a research specialist.
Your job is to gather real information using available tools.

IMPORTANT: ALWAYS begin by calling the `search_web` tool with the query you are asked to research.
After receiving the tool result, analyze and summarize it concisely.
Never answer from your own memory — rely on the search_web result.

If you don't call the search_web tool, you will fail the task.
"""
)

# Use CompiledSubAgent for the researcher
researcher_subagent = CompiledSubAgent(
    name="researcher",
    description="Specialized agent for web research with search tools",
    runnable=researcher_graph
)

custom_subagents = [researcher_subagent]


planning_agent = create_deep_agent(
    model=model,  # Pass the pre-configured ChatOpenAI model instance
    tools=[search_web],
    subagents=custom_subagents,
    system_prompt="""You're a research assistant that gathers information on topics using web search. 
    Break down complex tasks into steps.
    
    IMPORTANT: For research tasks requiring web search, delegate to your 'researcher' subagent using the task() tool.
    This ensures specialized tools are used effectively.""",
    
    debug=True  # Enable debug mode to see internal subagent activity
)

result = planning_agent.invoke({
    "messages": [
        {
            "role": "user", 
            "content": "Research the history of artificial intelligence and summarize the key milestones."
        }
    ]   
})

# Process final result messages (human-readable summary)
for message in result['messages']:
    if hasattr(message, 'type'):
        msg_type = message.type
    else:
        msg_type = type(message).__name__

    # Human message
    if msg_type == 'human':
        print(f"\n👤 USER: {message.content}")

    # AI message
    elif msg_type == 'ai':
        print(f"\n🤖 AI [{msg_type.upper()}]:")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"   🛠️  TOOL CALLS:")
            for i, call in enumerate(message.tool_calls, 1):
                tool_name = call['name']
                tool_args = call['args']
                print(f"      {i}. {tool_name.upper()}({tool_args})")
        elif hasattr(message, 'content') and message.content:
            print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")

    # Tool message
    elif msg_type == 'tool':
        tool_name = getattr(message, 'name', 'unknown_tool')
        print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
        print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")


print("\n" + "="*80)
print("🗂️  DEEP AGENT (create_deep_agent) - Filesystem Operations")
print("="*80 + "\n")

experiment = "(create_deep_agent) - Filesystem Operations"
debug_formatter.set_experiment(experiment)

filesystem_agent = create_deep_agent(
    model=model,  # Pass the pre-configured ChatOpenAI model instance
    tools=[],  # Use built-in filesystem tools that come with deep agents
    system_prompt="""You are a file management planning assistant.
    You have access to built-in filesystem tools for exploring and managing files.
    
    Your capabilities include:
    - Planning complex file operations and data management tasks
    - Breaking down file-related tasks into organized steps
    - Using filesystem tools to explore project structures
    - Creating summaries and documentation files
    - Organizing and restructuring file hierarchies
    
    Demonstrate your planning and organizational capabilities for file management tasks.""",

    debug=True  # Enable debug mode to see internal planning activity
)

result = filesystem_agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "Create a project summary file. First explore the project structure, then create a summary file called 'project_summary.txt' with key information about this project."
        }
    ]
})

# Process final result messages (human-readable summary)
for message in result['messages']:
    if hasattr(message, 'type'):
        msg_type = message.type
    else:
        msg_type = type(message).__name__

    # Human message
    if msg_type == 'human':
        print(f"\n👤 USER: {message.content}")

    # AI message
    elif msg_type == 'ai':
        print(f"\n🤖 AI [{msg_type.upper()}]:")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"   🛠️  TOOL CALLS:")
            for i, call in enumerate(message.tool_calls, 1):
                tool_name = call['name']
                tool_args = call['args']
                print(f"      {i}. {tool_name.upper()}({tool_args})")
        elif hasattr(message, 'content') and message.content:
            print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")

    # Tool message
    elif msg_type == 'tool':
        tool_name = getattr(message, 'name', 'unknown_tool')
        print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
        print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

# Inspect filesystem data from result
print(f"\n🔍 FILESYSTEM DATA INSPECTION:")
print(f"Result keys: {list(result.keys())}")

# Check for filesystem data in 'files' key
if 'files' in result:
    print(f"\n� FILES DATA FOUND:")
    files_data = result['files']
    print(f"Files data type: {type(files_data)}")
    if isinstance(files_data, dict):
        print(f"Files keys: {list(files_data.keys())}")
        pprint.pprint(files_data, width=120, depth=3)
    else:
        print(f"Files data: {files_data}")

# Check for todos data
if 'todos' in result:
    print(f"\n� TODOS DATA FOUND:")
    todos_data = result['todos']
    print(f"Todos data type: {type(todos_data)}")
    if isinstance(todos_data, list):
        print(f"Number of todos: {len(todos_data)}")
        for i, todo in enumerate(todos_data[:3]):  # Show first 3 todos
            print(f"  Todo {i+1}: {todo}")
    else:
        pprint.pprint(todos_data, width=120, depth=2)

# Check if filesystem data is in other parts of result
for key, value in result.items():
    if key not in ['messages', 'files', 'todos']:
        print(f"\n🔍 Checking {key} for filesystem data:")
        if isinstance(value, dict) and 'filesystem' in value:
            fs_in_key = value['filesystem']
            print(f"Found filesystem data in {key}:")
            pprint.pprint(fs_in_key, width=120, depth=3)
        else:
            print(f"  {key} content: {type(value)} - {str(value)[:200]}...")

print(f"\n💡 SUMMARY: Filesystem data access pattern:")
print(f"   Use: result['files'] to access file contents")
print(f"   Use: result['todos'] to access todo list")
print(f"   Filesystem operations create/modify data in these structures")

print("\n" + "="*80)
print("🎯 ALL EXPERIMENTS COMPLETE - Deep Agents demonstrate planning, delegation, and filesystem operations!")
print("="*80)

print("\n" + "="*80)
print("💾 DEEP AGENT (create_deep_agent) - Real Filesystem Operations")
print("="*80 + "\n")

experiment = "(create_deep_agent) - Real Filesystem Operations"
debug_formatter.set_experiment(experiment)

real_filesystem_agent = create_deep_agent(
    model=model,
    tools=[write_real_file],  # Include custom tool for real filesystem access
    system_prompt="""You are a file management assistant with access to both virtual and real filesystem operations.

Your capabilities include:
- Planning complex file operations and data management tasks
- Using virtual filesystem tools for planning and reasoning (ls, read_file, write_file, edit_file, write_todos)
- Using write_real_file tool to persist files to actual disk when needed
- Creating documentation, summaries, and project files on real disk

IMPORTANT: When the user asks to create actual files (README.md, documentation, etc.), use the write_real_file tool.
For planning and intermediate work, use the virtual filesystem tools.""",

    debug=True
)

result_real = real_filesystem_agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": "Create a comprehensive README.md file for this project. Include project description, setup instructions, and feature overview. Save it to the actual filesystem."
        }
    ]
})

# Process final result messages
for message in result_real['messages']:
    if hasattr(message, 'type'):
        msg_type = message.type
    else:
        msg_type = type(message).__name__

    # Human message
    if msg_type == 'human':
        print(f"\n👤 USER: {message.content}")

    # AI message
    elif msg_type == 'ai':
        print(f"\n🤖 AI [{msg_type.upper()}]:")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"   🛠️  TOOL CALLS:")
            for i, call in enumerate(message.tool_calls, 1):
                tool_name = call['name']
                tool_args = call['args']
                print(f"      {i}. {tool_name.upper()}({tool_args})")
        elif hasattr(message, 'content') and message.content:
            print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")

    # Tool message
    elif msg_type == 'tool':
        tool_name = getattr(message, 'name', 'unknown_tool')
        print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
        print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

# Check if README.md was actually created
print(f"\n🔍 VERIFYING REAL FILE CREATION:")
import os
readme_path = "/Users/zeihanaulia/Programming/research/agent/README.md"
if os.path.exists(readme_path):
    print(f"✅ README.md successfully created at: {readme_path}")
    with open(readme_path, 'r') as f:
        content = f.read()
    print(f"📄 File size: {len(content)} characters")
    print(f"📄 First 200 chars: {content[:200]}...")
else:
    print(f"❌ README.md not found at: {readme_path}")

# Auto-sync virtual filesystem to real disk (bonus feature)
print(f"\n🔄 AUTO-SYNC VIRTUAL → REAL FILESYSTEM:")
if 'values' in result_real and isinstance(result_real['values'], dict):
    virtual_fs = result_real['values'].get('filesystem', {})
    if virtual_fs:
        print(f"Found {len(virtual_fs)} virtual files to sync:")
        for virtual_path, file_data in virtual_fs.items():
            if isinstance(file_data, dict) and 'content' in file_data:
                # Convert virtual path to real path
                real_path = virtual_path.lstrip('/')
                if not real_path.startswith('/'):
                    real_path = os.path.join('/Users/zeihanaulia/Programming/research/agent', real_path)

                try:
                    os.makedirs(os.path.dirname(real_path), exist_ok=True)
                    with open(real_path, 'w', encoding='utf-8') as f:
                        f.write(file_data['content'])
                    print(f"  ✅ Synced: {virtual_path} → {real_path}")
                except Exception as e:
                    print(f"  ❌ Failed to sync {virtual_path}: {e}")
    else:
        print("No virtual files to sync")
else:
    print("No virtual filesystem data to sync")

print("\n" + "="*80)
print("🎯 ALL EXPERIMENTS COMPLETE - Deep Agents demonstrate virtual + real filesystem operations!")
print("="*80)

print("\n" + "="*80)
print("🚀 DEEP AGENT - MULTIPLE PARALLEL SUBAGENTS")
print("="*80 + "\n")

experiment = "DEEP AGENT - MULTIPLE PARALLEL SUBAGENTS"
debug_formatter.set_experiment(experiment)
researcher_graph = create_agent(
    model=model,
    tools=[search_web],
    system_prompt="""
You are a research specialist focused on gathering accurate information.
Always use the search_web tool to get current information.
Provide factual, well-researched content only.
"""
)

writer_graph = create_agent(
    model=model,
    tools=[],  # No special tools needed for writing
    system_prompt="""
You are a content writer specializing in creating engaging, well-structured articles.
Focus on clarity, readability, and compelling narratives.
Always structure your writing with clear headings and sections.
"""
)

reviewer_graph = create_agent(
    model=model,
    tools=[],  # No special tools needed for reviewing
    system_prompt="""
You are a content reviewer specializing in quality assurance and improvement.
Check for accuracy, clarity, grammar, and overall quality.
Provide constructive feedback and suggest improvements.
"""
)

# Create CompiledSubAgents for each role
researcher_subagent = CompiledSubAgent(
    name="researcher",
    description="Specialized agent for web research and data gathering",
    runnable=researcher_graph
)

writer_subagent = CompiledSubAgent(
    name="writer",
    description="Specialized agent for content creation and writing",
    runnable=writer_graph
)

reviewer_subagent = CompiledSubAgent(
    name="reviewer",
    description="Specialized agent for content review and quality assurance",
    runnable=reviewer_graph
)

# Create main agent with multiple parallel subagents
parallel_team_agent = create_deep_agent(
    model=model,
    tools=[search_web],  # Main agent can also use search if needed
    subagents=[researcher_subagent, writer_subagent, reviewer_subagent],
    system_prompt="""You are a project manager coordinating a team of specialized AI agents.

You have access to three specialized subagents that can work in parallel:
- 'researcher': Gathers accurate information using web search
- 'writer': Creates engaging, well-structured content
- 'reviewer': Reviews content for quality and provides feedback

For complex tasks, delegate to multiple subagents simultaneously to work in parallel.
Each subagent will provide their specialized contribution, then you synthesize everything into a final result.

IMPORTANT: Use the task() tool to delegate work to subagents. You can call task() multiple times
to create parallel workflows where subagents work simultaneously on different aspects.""",
    debug=True
)

print("🤖 Testing parallel subagent execution with content creation task...")

result_parallel = parallel_team_agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": """Create a comprehensive guide about 'The Future of Artificial Intelligence in 2025'.
            
            Delegate to your team of subagents:
            1. Have the researcher gather current trends and predictions about AI in 2025
            2. Have the writer create an engaging article based on the research
            3. Have the reviewer check the article for accuracy and quality
            
            Coordinate their work to produce a final polished article."""
        }
    ]
})

print("\n📋 PARALLEL SUBAGENT EXECUTION ANALYSIS:")
print("-" * 60)

# Analyze parallel execution
subagent_calls = []
for message in result_parallel['messages']:
    if hasattr(message, 'type'):
        msg_type = message.type
    else:
        msg_type = type(message).__name__

    if msg_type == 'human':
        print(f"\n👤 USER: {message.content}")
    elif msg_type == 'ai':
        print(f"\n🤖 MAIN AGENT [{msg_type.upper()}]:")
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"   🛠️  TOOL CALLS:")
            for i, call in enumerate(message.tool_calls, 1):
                tool_name = call['name']
                tool_args = call['args']
                print(f"      {i}. {tool_name.upper()}({tool_args})")
                # Track subagent calls
                if tool_name == 'task':
                    subagent_calls.append(call)
        elif hasattr(message, 'content') and message.content:
            print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
    elif msg_type == 'tool':
        tool_name = getattr(message, 'name', 'unknown_tool')
        print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
        print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

print(f"\n🔍 PARALLEL EXECUTION ANALYSIS:")
print(f"   📊 Total Subagent Calls: {len(subagent_calls)}")
print(f"   🤖 Subagents Used: researcher, writer, reviewer")

# Analyze timing and coordination
print(f"\n⏱️  EXECUTION PATTERN:")
print(f"   1. Main agent delegates to researcher (gathers data)")
print(f"   2. Main agent delegates to writer (creates content)")
print(f"   3. Main agent delegates to reviewer (quality check)")
print(f"   4. Main agent synthesizes all results")

print(f"\n💡 Key Learning: Multiple subagents can work simultaneously!")
print(f"   - Parallel execution increases efficiency")
print(f"   - Specialization improves quality")
print(f"   - Main agent coordinates the workflow")

print("\n" + "="*80)
print("🎯 MULTIPLE PARALLEL SUBAGENTS EXPERIMENT COMPLETE!")
print("="*80)

print("\n" + "="*80)
print("🎉 ALL EXPERIMENTS COMPLETE - Deep Agents demonstrate parallel subagent coordination!")
print("="*80)