import os, json
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

# ========== CONFIG ==========
PRD_TITLE = "school-registration"   # ubah sesuai nama PRD lo
PRD_PATH  = f"dataset/prds/prd-{PRD_TITLE}.md"
OUTPUT_DIR = "outputs"
OUTPUT_FILE = f"{OUTPUT_DIR}/plan-{PRD_TITLE}.json"

console = Console()

# ========== HELPERS ==========
def read_prd(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ PRD file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@tool
def write_plan_json(filename: str, plan_json: str) -> str:
    """Save the generated plan JSON file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(plan_json)
    return f"✅ Plan saved to {path}"

# ========== VISUAL RENDERING ==========
def render_plan_progress(plan):
    total = len(plan)
    completed = sum(1 for p in plan if p.get("status", "").lower() == "done")

    console.rule(f"[bold green]🧠 TODOS ({completed}/{total})")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("No", width=4)
    table.add_column("Task", style="cyan", width=60)
    table.add_column("Status", justify="center", style="bold green")

    for i, item in enumerate(plan, 1):
        status = item.get("status", "pending")
        mark = "✅" if status == "done" else "🕓" if status == "in_progress" else "⬜"
        table.add_row(str(i), item.get("content", ""), f"{mark} {status}")

    console.print(table)
    console.print()

    if completed < total:
        console.print(f"[yellow]⚙️  {total - completed} tasks remaining...[/yellow]\n")
    else:
        console.print("[bold green]🎉 All tasks completed![/bold green]\n")

# ========== MAIN ==========
def main():
    # --- 1. Load PRD ---
    prd_text = read_prd(PRD_PATH)
    console.print(f"📘 Loaded PRD from [cyan]{PRD_PATH}[/cyan]\n")

    # --- 2. Init LLM ---
    model = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY") or os.getenv("LITELLM_VIRTUAL_KEY"),
        model=os.getenv("LITELLM_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("LITELLM_API"),
        temperature=0.1,
    )

    # --- 3. Create planning agent ---
    planner = create_deep_agent(
        model=model,
        tools=[write_plan_json],
        system_prompt="""You are a senior AI project planner.
You read Product Requirement Documents (PRDs) and break them into actionable TODO steps.
Each TODO must include:
- content: concise action description
- reasoning: why it matters
- expected_output: artifact or deliverable name
- status: pending (default)
Use write_todos to record your plan and write_plan_json to export it as JSON.
""",
        debug=False
    )

    # --- 4. Invoke agent ---
    console.print("[cyan]🤖 Generating plan... please wait[/cyan]")
    result = planner.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"Analyze this PRD and create a structured implementation plan:\n\n{prd_text}"
            }
        ]
    })

    # --- 5. Extract plan & visualize ---
    plan = result.get("values", {}).get("todos", [])
    if not plan:
        console.print("[red]❌ No plan returned by agent. Check debug logs or model output.[/red]")
        return

    render_plan_progress(plan)

    # --- 6. Save plan JSON ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    console.print(f"[green]✅ Plan saved to {OUTPUT_FILE}[/green]\n")

if __name__ == "__main__":
    main()
