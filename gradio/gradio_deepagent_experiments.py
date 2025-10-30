# gradio_deepagent_experiments.py
import gradio as gr
import io
import sys
import os
from contextlib import redirect_stdout
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from dotenv import load_dotenv
from pydantic import SecretStr
import pprint
sys.path.append('scripts')
from debug_formatter import DebugFormatter
from deepagents import create_deep_agent, CompiledSubAgent

# Load environment
load_dotenv()
litellm_key = os.getenv("LITELLM_VIRTUAL_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
key = litellm_key or openai_key
if not key:
    raise SystemExit("Missing API key")

base_url = os.getenv("LITELLM_API") if litellm_key else None
model = ChatOpenAI(
    base_url=base_url,
    api_key=SecretStr(key),
    model=os.getenv("LITELLM_MODEL", "gpt-4o-mini"),
)

# Define tools
@tool
def search_web(query: str) -> str:
    """Search helper: perform a web search for the given query and return results as text."""
    print(f"🔍 SUBAGENT: Using search_web tool with query: '{query}'")
    result = f"Mock Search results for: {query}"
    print(f"🔍 SUBAGENT: Search completed, returning result")
    return result

@tool
def list_directory(path: str = ".") -> str:
    """List directory contents for the given path and return a human-readable summary."""
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
    """Read and return the contents of a file at `file_path` as a string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"📖 FILESYSTEM: Read file {file_path} ({len(content)} chars)")
        return f"Content of {file_path}:\n\n{content}"
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

@tool
def write_file_content(file_path: str, content: str) -> str:
    """Write `content` to `file_path` (virtual/project filesystem) and report status."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✏️ FILESYSTEM: Wrote {len(content)} chars to {file_path}")
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing to file {file_path}: {e}"

@tool
def edit_file_content(file_path: str, old_string: str, new_string: str) -> str:
    """Replace the first occurrence of `old_string` with `new_string` in `file_path`."""
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
    """Write `content` to the real filesystem at `path`, creating parent directories as needed."""
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

# Experiment functions
def run_basic_agent(user_query):
    f = io.StringIO()
    with redirect_stdout(f):
        print("\n" + "="*80)
        print("🚀 BASIC AGENT (create_agent) - Simple Tool Calling")
        print("="*80 + "\n")

        agent = create_agent(model, tools=[search_web])
        result = agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })
        for message in result['messages']:
            if hasattr(message, 'type'):
                msg_type = message.type
            else:
                msg_type = type(message).__name__

            if msg_type == 'human':
                print(f"\n👤 USER: {message.content}")
            elif msg_type == 'ai':
                print(f"\n🤖 AI [{msg_type.upper()}]:")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print("   🛠️  TOOL CALLS:")
                    for i, call in enumerate(message.tool_calls, 1):
                        tool_name = call['name']
                        tool_args = call['args']
                        print(f"      {i}. {tool_name.upper()}({tool_args})")
                elif hasattr(message, 'content') and message.content:
                    print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
            elif msg_type == 'tool':
                tool_name = getattr(message, 'name', 'unknown_tool')
                print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
                print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

            # yield incremental output so Gradio can stream updates
            yield f.getvalue()

    # final yield to ensure caller gets the complete output
    yield f.getvalue()

def run_planning_agent(user_query):
    f = io.StringIO()
    with redirect_stdout(f):
        print("\n" + "="*80)
        print("🚀 DEEP AGENT (create_deep_agent) - Planning")
        print("="*80 + "\n")

        planning_agent = create_deep_agent(
            model=model,
            tools=[search_web],
            system_prompt="""You're a planning agent that breaks down complex tasks into steps.
            For research tasks requiring web search, delegate to your 'researcher' subagent using the task() tool.
            This ensures specialized tools are used effectively.""",
            debug=True
        )

        result = planning_agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })

        for message in result['messages']:
            if hasattr(message, 'type'):
                msg_type = message.type
            else:
                msg_type = type(message).__name__

            if msg_type == 'human':
                print(f"\n👤 USER: {message.content}")
            elif msg_type == 'ai':
                print(f"\n🤖 AI [{msg_type.upper()}]:")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print("   🛠️  TOOL CALLS:")
                    for i, call in enumerate(message.tool_calls, 1):
                        tool_name = call['name']
                        tool_args = call['args']
                        print(f"      {i}. {tool_name.upper()}({tool_args})")
                elif hasattr(message, 'content') and message.content:
                    print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
            elif msg_type == 'tool':
                tool_name = getattr(message, 'name', 'unknown_tool')
                print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
                print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

            # stream incremental output
            yield f.getvalue()

    yield f.getvalue()

def run_subagent_experiment(user_query):
    f = io.StringIO()
    with redirect_stdout(f):
        print("\n" + "="*80)
        print("🚀 DEEP AGENT (create_deep_agent) - Deep Agent Subagent")
        print("="*80 + "\n")

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

        researcher_subagent = CompiledSubAgent(
            name="researcher",
            description="Specialized agent for web research with search tools",
            runnable=researcher_graph
        )

        planning_agent = create_deep_agent(
            model=model,
            tools=[search_web],
            subagents=[researcher_subagent],
            system_prompt="""You're a research assistant that gathers information on topics using web search. 
            Break down complex tasks into steps.
            
            IMPORTANT: For research tasks requiring web search, delegate to your 'researcher' subagent using the task() tool.
            This ensures specialized tools are used effectively.""",
            debug=True
        )

        result = planning_agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })

        for message in result['messages']:
            if hasattr(message, 'type'):
                msg_type = message.type
            else:
                msg_type = type(message).__name__

            if msg_type == 'human':
                print(f"\n👤 USER: {message.content}")
            elif msg_type == 'ai':
                print(f"\n🤖 AI [{msg_type.upper()}]:")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print("   🛠️  TOOL CALLS:")
                    for i, call in enumerate(message.tool_calls, 1):
                        tool_name = call['name']
                        tool_args = call['args']
                        print(f"      {i}. {tool_name.upper()}({tool_args})")
                elif hasattr(message, 'content') and message.content:
                    print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
            elif msg_type == 'tool':
                tool_name = getattr(message, 'name', 'unknown_tool')
                print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
                print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

            yield f.getvalue()

    yield f.getvalue()

def run_filesystem_experiment(user_query):
    f = io.StringIO()
    with redirect_stdout(f):
        print("\n" + "="*80)
        print("🗂️  DEEP AGENT (create_deep_agent) - Filesystem Operations")
        print("="*80 + "\n")

        filesystem_agent = create_deep_agent(
            model=model,
            tools=[],
            system_prompt="""You are a file management planning assistant.
            You have access to built-in filesystem tools for exploring and managing files.
            
            Your capabilities include:
            - Planning complex file operations and data management tasks
            - Breaking down file-related tasks into organized steps
            - Using filesystem tools to explore project structures
            - Creating summaries and documentation files
            - Organizing and restructuring file hierarchies
            
            Demonstrate your planning and organizational capabilities for file management tasks.""",
            debug=True
        )

        result = filesystem_agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })

        for message in result['messages']:
            if hasattr(message, 'type'):
                msg_type = message.type
            else:
                msg_type = type(message).__name__

            if msg_type == 'human':
                print(f"\n👤 USER: {message.content}")
            elif msg_type == 'ai':
                print(f"\n🤖 AI [{msg_type.upper()}]:")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print("   🛠️  TOOL CALLS:")
                    for i, call in enumerate(message.tool_calls, 1):
                        tool_name = call['name']
                        tool_args = call['args']
                        print(f"      {i}. {tool_name.upper()}({tool_args})")
                elif hasattr(message, 'content') and message.content:
                    print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
            elif msg_type == 'tool':
                tool_name = getattr(message, 'name', 'unknown_tool')
                print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
                print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

            # stream after each message
            yield f.getvalue()

        # Inspect filesystem data
        print(f"\n🔍 FILESYSTEM DATA INSPECTION:")
        print(f"Result keys: {list(result.keys())}")
        if 'files' in result:
            print(f"\n📁 FILES DATA FOUND:")
            files_data = result['files']
            print(f"Files data type: {type(files_data)}")
            if isinstance(files_data, dict):
                print(f"Files keys: {list(files_data.keys())}")
                pprint.pprint(files_data, width=120, depth=3)
        if 'todos' in result:
            print(f"\n📝 TODOS DATA FOUND:")
            todos_data = result['todos']
            print(f"Todos data type: {type(todos_data)}")
            if isinstance(todos_data, list):
                print(f"Number of todos: {len(todos_data)}")
                for i, todo in enumerate(todos_data[:3]):
                    print(f"  Todo {i+1}: {todo}")

    yield f.getvalue()

def run_real_filesystem_experiment(user_query):
    f = io.StringIO()
    with redirect_stdout(f):
        print("\n" + "="*80)
        print("💾 DEEP AGENT (create_deep_agent) - Real Filesystem Operations")
        print("="*80 + "\n")

        real_filesystem_agent = create_deep_agent(
            model=model,
            tools=[write_real_file],
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

        result = real_filesystem_agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })

        for message in result['messages']:
            if hasattr(message, 'type'):
                msg_type = message.type
            else:
                msg_type = type(message).__name__

            if msg_type == 'human':
                print(f"\n👤 USER: {message.content}")
            elif msg_type == 'ai':
                print(f"\n🤖 AI [{msg_type.upper()}]:")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print("   🛠️  TOOL CALLS:")
                    for i, call in enumerate(message.tool_calls, 1):
                        tool_name = call['name']
                        tool_args = call['args']
                        print(f"      {i}. {tool_name.upper()}({tool_args})")
                elif hasattr(message, 'content') and message.content:
                    print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
            elif msg_type == 'tool':
                tool_name = getattr(message, 'name', 'unknown_tool')
                print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
                print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

            yield f.getvalue()

        # Check if file was created
        print(f"\n🔍 VERIFYING REAL FILE CREATION:")
        readme_path = "/Users/zeihanaulia/Programming/research/agent/README.md"
        if os.path.exists(readme_path):
            print(f"✅ README.md successfully created at: {readme_path}")
            with open(readme_path, 'r') as rf:
                content = rf.read()
            print(f"📄 File size: {len(content)} characters")
            print(f"📄 First 200 chars: {content[:200]}...")
        else:
            print(f"❌ README.md not found at: {readme_path}")

    yield f.getvalue()

def run_parallel_subagents_experiment(user_query):
    f = io.StringIO()
    with redirect_stdout(f):
        print("\n" + "="*80)
        print("🚀 DEEP AGENT - MULTIPLE PARALLEL SUBAGENTS")
        print("="*80 + "\n")

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
            tools=[],
            system_prompt="""
You are a content writer specializing in creating engaging, well-structured articles.
Focus on clarity, readability, and compelling narratives.
Always structure your writing with clear headings and sections.
"""
        )

        reviewer_graph = create_agent(
            model=model,
            tools=[],
            system_prompt="""
You are a content reviewer specializing in quality assurance and improvement.
Check for accuracy, clarity, grammar, and overall quality.
Provide constructive feedback and suggest improvements.
"""
        )

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

        parallel_team_agent = create_deep_agent(
            model=model,
            tools=[search_web],
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

        result = parallel_team_agent.invoke({
            "messages": [{"role": "user", "content": user_query}]
        })

        print("\n📋 PARALLEL SUBAGENT EXECUTION ANALYSIS:")
        print("-" * 60)

        subagent_calls = []
        for message in result['messages']:
            if hasattr(message, 'type'):
                msg_type = message.type
            else:
                msg_type = type(message).__name__

            if msg_type == 'human':
                print(f"\n👤 USER: {message.content}")
            elif msg_type == 'ai':
                print(f"\n🤖 MAIN AGENT [{msg_type.upper()}]:")
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    print("   🛠️  TOOL CALLS:")
                    for i, call in enumerate(message.tool_calls, 1):
                        tool_name = call['name']
                        tool_args = call['args']
                        print(f"      {i}. {tool_name.upper()}({tool_args})")
                        if tool_name == 'task':
                            subagent_calls.append(call)
                elif hasattr(message, 'content') and message.content:
                    print(f"   💬 {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
            elif msg_type == 'tool':
                tool_name = getattr(message, 'name', 'unknown_tool')
                print(f"\n🔧 TOOL RESULT [{msg_type.upper()}] - {tool_name}:")
                print(f"   📄 {message.content[:300]}{'...' if len(message.content) > 300 else ''}")

            # stream incremental progress
            yield f.getvalue()

        print(f"\n🔍 PARALLEL EXECUTION ANALYSIS:")
        print(f"   📊 Total Subagent Calls: {len(subagent_calls)}")
        print(f"   🤖 Subagents Used: researcher, writer, reviewer")
        print(f"\n⏱️  EXECUTION PATTERN:")
        print(f"   1. Main agent delegates to researcher (gathers data)")
        print(f"   2. Main agent delegates to writer (creates content)")
        print(f"   3. Main agent delegates to reviewer (quality check)")
        print(f"   4. Main agent synthesizes all results")
        print(f"\n💡 Key Learning: Multiple subagents can work simultaneously!")
        print(f"   - Parallel execution increases efficiency")
        print(f"   - Specialization improves quality")
        print(f"   - Main agent coordinates the workflow")

    yield f.getvalue()

# Gradio Interface
with gr.Blocks(title="Deep Agents Experiments") as demo:
    gr.Markdown("# Deep Agents Experiments\n\nExplore different AI agent architectures and capabilities through interactive experiments.")

    with gr.Tabs():
        with gr.TabItem("Basic Agent"):
            gr.Markdown("""
            ## Experiment 1: Basic Agent with Tool Calling
            
            This experiment demonstrates a simple LangChain agent with basic tool calling capabilities.
            The agent can use the `search_web` tool to perform web searches.
            
            **Learning Objectives:**
            - Understand basic agent setup
            - See how tools are called and results processed
            - Observe agent reasoning and response generation
            """)
            query1 = gr.Textbox(label="Enter your query", value="Research the history of artificial intelligence and summarize the key milestones.")
            output1 = gr.Textbox(label="Experiment Output", lines=20, interactive=False)
            btn1 = gr.Button("Run Basic Agent Experiment")
            btn1.click(run_basic_agent, inputs=query1, outputs=output1)

        with gr.TabItem("Planning Agent"):
            gr.Markdown("""
            ## Experiment 2: Deep Agent with Planning
            
            This experiment shows a deep agent that can break down complex tasks into steps and delegate to subagents.
            The agent uses planning capabilities to organize research tasks.
            
            **Learning Objectives:**
            - See how agents plan complex tasks
            - Understand subagent delegation
            - Observe task decomposition
            """)
            query2 = gr.Textbox(label="Enter your query", value="Plan my birthday party with a 90s theme. Research popular 90s music, fashion, and food.")
            output2 = gr.Textbox(label="Experiment Output", lines=20, interactive=False)
            btn2 = gr.Button("Run Planning Agent Experiment")
            btn2.click(run_planning_agent, inputs=query2, outputs=output2)

        with gr.TabItem("Subagent Research"):
            gr.Markdown("""
            ## Experiment 3: Deep Agent with Specialized Subagent
            
            This experiment demonstrates a deep agent with a specialized 'researcher' subagent.
            The main agent delegates research tasks to the specialized subagent.
            
            **Learning Objectives:**
            - Understand specialized subagents
            - See delegation patterns
            - Observe how subagents use specific tools
            """)
            query3 = gr.Textbox(label="Enter your query", value="Research the history of artificial intelligence and summarize the key milestones.")
            output3 = gr.Textbox(label="Experiment Output", lines=20, interactive=False)
            btn3 = gr.Button("Run Subagent Research Experiment")
            btn3.click(run_subagent_experiment, inputs=query3, outputs=output3)

        with gr.TabItem("Filesystem Operations"):
            gr.Markdown("""
            ## Experiment 4: Filesystem Operations
            
            This experiment shows how deep agents can perform filesystem operations using built-in tools.
            The agent can explore project structures and manage files.
            
            **Learning Objectives:**
            - See filesystem tool usage
            - Understand virtual filesystem concepts
            - Observe file management planning
            """)
            query4 = gr.Textbox(label="Enter your query", value="Create a project summary file. First explore the project structure, then create a summary file called 'project_summary.txt' with key information about this project.")
            output4 = gr.Textbox(label="Experiment Output", lines=20, interactive=False)
            btn4 = gr.Button("Run Filesystem Experiment")
            btn4.click(run_filesystem_experiment, inputs=query4, outputs=output4)

        with gr.TabItem("Real Filesystem"):
            gr.Markdown("""
            ## Experiment 5: Real Filesystem Operations
            
            This experiment demonstrates writing to the actual filesystem.
            The agent can create real files on disk.
            
            **Learning Objectives:**
            - Understand real vs virtual filesystem
            - See file persistence
            - Observe disk operations
            """)
            query5 = gr.Textbox(label="Enter your query", value="Create a comprehensive README.md file for this project. Include project description, setup instructions, and feature overview. Save it to the actual filesystem.")
            output5 = gr.Textbox(label="Experiment Output", lines=20, interactive=False)
            btn5 = gr.Button("Run Real Filesystem Experiment")
            btn5.click(run_real_filesystem_experiment, inputs=query5, outputs=output5)

        with gr.TabItem("Parallel Subagents"):
            gr.Markdown("""
            ## Experiment 6: Multiple Parallel Subagents
            
            This experiment shows coordination of multiple specialized subagents working in parallel.
            The main agent manages a team of researcher, writer, and reviewer subagents.
            
            **Learning Objectives:**
            - Understand parallel agent coordination
            - See team-based workflows
            - Observe specialization benefits
            """)
            query6 = gr.Textbox(label="Enter your query", value="""Create a comprehensive guide about 'The Future of Artificial Intelligence in 2025'.
            
            Delegate to your team of subagents:
            1. Have the researcher gather current trends and predictions about AI in 2025
            2. Have the writer create an engaging article based on the research
            3. Have the reviewer check the article for accuracy and quality
            
            Coordinate their work to produce a final polished article.""")
            output6 = gr.Textbox(label="Experiment Output", lines=20, interactive=False)
            btn6 = gr.Button("Run Parallel Subagents Experiment")
            btn6.click(run_parallel_subagents_experiment, inputs=query6, outputs=output6)

if __name__ == "__main__":
    demo.launch()