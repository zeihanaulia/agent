import os
import argparse
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware
)
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()


###############################################################
# ---------------------- CLI ARGUMENTS ------------------------
###############################################################

parser = argparse.ArgumentParser(description="Analyze a codebase project.")
parser.add_argument("--codebase-path", type=str, required=True)
parser.add_argument("--human-request", type=str, required=True)
args = parser.parse_args()

ROOT_DIR = args.codebase_path


###############################################################
# -------------------------- TOOLS ----------------------------
###############################################################

@tool
def list_files(input_str: str) -> str:
    """List all files in the project (max depth 5)."""
    result = []
    for root, dirs, files in os.walk(ROOT_DIR):
        depth = root.replace(ROOT_DIR, "").count(os.sep)
        if depth <= 5:
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, ROOT_DIR)
                result.append(rel)
    return "\n".join(result)


@tool
def read_file(path: str) -> str:
    """Read a file inside the project safely."""
    full_path = os.path.join(ROOT_DIR, path)
    if not os.path.isfile(full_path):
        return f"ERROR: {path} does not exist."

    try:
        with open(full_path, "r", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"ERROR reading {path}: {str(e)}"


@tool
def detect_language(input_str: str) -> str:
    """Detect programming languages in the codebase."""
    languages = set()

    for root, dirs, files in os.walk(ROOT_DIR):
        for filename in files:
            ext = filename.split(".")[-1].lower()
            if ext == "java":
                languages.add("Java")
            elif ext == "py":
                languages.add("Python")
            elif ext in ("js", "jsx", "ts", "tsx"):
                languages.add("JavaScript/TypeScript")
            elif ext == "go":
                languages.add("Go")
            elif ext == "rb":
                languages.add("Ruby")
            elif ext in ("php",):
                languages.add("PHP")
            elif ext in ("cs",):
                languages.add("C#")

    if not languages:
        return "Unable to detect language."

    return ", ".join(sorted(languages))


tools = [list_files, read_file, detect_language]


###############################################################
# ------------------ SYSTEM PROMPT (TAG-BASED) ----------------
###############################################################

SYSTEM_PROMPT = """
<identity>
You are a professional codebase analysis agent.
You NEVER guess — you MUST inspect files using tools.
Your job is to deeply understand what the project does based on real file contents.
</identity>

<role>
Context-Gathering & Codebase Analysis Assistant (Read-Only)
</role>

<primary_objective>
Your sole objective is to gather and synthesize context about the repository:
- What the project is and does
- Which tech stack it uses
- How the codebase is structured
You must achieve this ONLY through the tools you have access to.
</primary_objective>

<tools>
You have access to the following tools:

- list_files:
  - Lists files in the repository (recursively).
  - Use this first to understand the overall structure.
  - Use it again later if you need to refine your view of a specific subfolder.

- read_file:
  - Reads the contents of a file.
  - Use this on key files (README, config, entrypoints, etc).
  - Use it whenever you need ground truth instead of guessing.

- detect_language:
  - Analyzes files to determine the main technologies / languages used.
  - Use this after you have a basic sense of the structure so you can cross-check your understanding.
</tools>

<workflow>
1. ALWAYS start with list_files to get an overview of the repository structure.
2. From the file list, identify important project files and folders, such as:
   - README*, docs/, or similar documentation files
   - pom.xml / build.gradle (Java / Spring)
   - requirements.txt / pyproject.toml (Python)
   - package.json (JavaScript / TypeScript)
   - composer.json (PHP)
   - Gemfile (Ruby)
   - go.mod / go.sum (Go)
   - Cargo.toml (Rust)
   - src/, app/, backend/, frontend/, or other main source folders
3. Call read_file on the most important files you identified to understand:
   - What the project claims to do (README / docs)
   - How it is built and run (build / dependency files)
   - Where the main entrypoints live (e.g. main files, server / app files)
4. Call detect_language to confirm the tech stack and check it against what you inferred from the files.
5. If something is still unclear, use additional read_file calls on the most relevant files or directories.
6. Once you have enough real context from tool results, prepare your final explanation.
</workflow>

<rules>
- You MUST use tools before producing any final explanation.
- Never answer based on assumptions; always back your understanding with at least:
  - One list_files call, and
  - Several read_file calls on key files, and
  - A detect_language call (unless it is clearly redundant).
- Prefer a few well-chosen read_file calls over reading everything blindly.
- You may call tools in parallel if multiple independent inspections are useful.
- Never output raw tool results directly; always summarize and interpret them.
- Your final answer must be grounded in actual file contents and tool results.
</rules>

<thinking_instructions>
You may think step-by-step internally to decide:
- which tools to call
- which files are most informative
- what each file tells you about the project
- how to reconcile and summarize the information

However, this internal analysis MUST NOT be shown to the user.
Only the final <answer> section should be visible to the user.
</thinking_instructions>

<output_format>
Your final response to the user must include ONLY the following section:

<answer>
Explain in a clear, human-friendly way:
- what the project is / does
- what tech stack is used (languages, frameworks, build tools)
- what structure the project has (key folders, key files, entrypoints)
Base this strictly on the files you inspected and tool results.
</answer>
</output_format>

<stop_condition>
After you finish your inspection and produce the <answer> section,
you MUST STOP. Do NOT call more tools and do NOT produce any other sections.
</stop_condition>
"""

###############################################################
# -------------------------- AGENT ----------------------------
###############################################################

middleware = [
    ModelCallLimitMiddleware(
        run_limit=50, 
        exit_behavior="end"),
    ToolCallLimitMiddleware(
        run_limit=100, 
        exit_behavior="end"
    )
]

llm = ChatOpenAI(
    model=os.getenv("LITELLM_MODEL", "gpt-4o-mini"),
    base_url=os.getenv("LITELLM_API"),
    api_key=os.getenv("LITELLM_VIRTUAL_KEY"), # pyright: ignore[reportArgumentType]
    temperature=0.2,
)

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    middleware=middleware,
)


###############################################################
# ------------------------- EXECUTION -------------------------
###############################################################

if __name__ == "__main__":
    print(f"\n📁 Analyzing project at: {ROOT_DIR}")
    print(f"🧠 Human request: {args.human_request}\n")

    response = agent.invoke({
        "messages": [{
            "role": "user",
            "content": args.human_request
        }]
    }, config={"recursion_limit": 100})

    final = response["messages"][-1].content

    print("\n================= RESULT =================")
    print(final)
    print("==========================================\n")
