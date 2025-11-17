import argparse
import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from planner.planner_agent import build_analyzer_agent
from answer.answer_agent import build_answer_agent

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--codebase-path", required=True)
parser.add_argument("--human-request", required=True)
args = parser.parse_args()

ROOT = args.codebase_path
REQUEST = args.human_request

model_name = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
is_gpt120_oss = "gpt-oss-120b" in model_name.lower()
is_qwen_coder_30b = "qwen3-coder-30b" in model_name.lower()
is_minimax = "minimax" in model_name.lower()

# Note: Some models don't follow strict chat protocol:
# - gpt-oss-120b: Non-standard tool calling format
# - qwen3-coder-30b: May produce inconsistent JSON output
# - minimax: Produces non-JSON/incomplete responses
# Recommended models: gpt-5-mini, azure/gpt-4 (stable output format)
# To use: Uncomment LITELLM_MODEL=gpt-5-mini in .env

# Adjust temperature for model stability
temp = 0.2
if is_gpt120_oss or is_qwen_coder_30b or is_minimax:
    temp = 0.1  # Lower temp for model stability

model = ChatOpenAI(
    model=model_name,
    base_url=os.getenv("LITELLM_API"),
    api_key=os.getenv("LITELLM_VIRTUAL_KEY"), # pyright: ignore[reportArgumentType]
    temperature=temp,
)


#########################
# 1. RUN PLANNER
#########################

print("📌 Running ANALYZER agent...")

analyzer = build_analyzer_agent(model)

analyzer_response = analyzer.invoke({
    "messages": [{"role": "user", "content": f"Analyze repo at {ROOT}. ROOT={ROOT}"}]
}, config={"recursion_limit": 200})

repo_map_text = analyzer_response["messages"][-1].content

# Handle different response formats based on model
if is_gpt120_oss or is_qwen_coder_30b or is_minimax:
    # These models may not follow strict XML format, try to extract JSON with fallback
    model_type = "GPT-OSS-120b" if is_gpt120_oss else ("Qwen-Coder-30b" if is_qwen_coder_30b else "Minimax")
    try:
        json_str = repo_map_text.replace("<repo_map>", "").replace("</repo_map>", "").strip()
        if not json_str or json_str.startswith("I couldn't") or json_str.startswith("I apologize") or json_str.startswith("<"):
            # Model returned an error message or markup instead of data
            print(f"⚠️  {model_type} returned non-JSON response. Using fallback...")
            repo_map = {
                "structure": f"Auto-generated (note: {model_type} model may have limited repo_map generation)",
                "languages": [],
                "file_tree": [],
                "all_files": [],
                "key_files": [],
                "entrypoints": [],
                "build_commands": ["mvn clean package"],
                "run_commands": ["mvn spring-boot:run"]
            }
        else:
            repo_map = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parsing failed with {model_type}: {str(e)[:50]}...")
        print(f"Raw response preview: {repo_map_text[:150]}...")
        # Fallback for non-standard model
        repo_map = {
            "structure": "Auto-generated from directory listing (model parsing failed)",
            "languages": [],
            "file_tree": [],
            "all_files": [],
            "key_files": [],
            "entrypoints": [],
            "build_commands": ["mvn clean package"],
            "run_commands": ["mvn spring-boot:run"]
        }
else:
    # Standard models (gpt-5-mini, gpt-4, etc.) follow strict XML format
    json_str = repo_map_text.replace("<repo_map>", "").replace("</repo_map>", "").strip()
    repo_map = json.loads(json_str)

os.makedirs("output", exist_ok=True)
json.dump(repo_map, open("output/repo_map.json", "w"), indent=2)

if is_qwen_coder_30b or is_gpt120_oss or is_minimax:
    print(f"✅ REPO_MAP generated (using {model_name}).")
else:
    print("✅ REPO_MAP generated.")

#########################
# 2. RUN ANSWER AGENT
#########################

print("🤖 Generating final answer...")
if is_qwen_coder_30b or is_gpt120_oss or is_minimax:
    print(f"   (Note: Using {model_name} for analysis)")

answer_agent = build_answer_agent(model)

answer = answer_agent.invoke({
    "messages": [
        {"role": "system", "content": f"Repository ROOT path: {ROOT}\n\nRepo Map:\n{json.dumps(repo_map)}"},
        {"role": "user", "content": REQUEST}
    ]
}, config={"recursion_limit": 200})

print("\n================= RESULT =================")
print(answer["messages"][-1].content)
print("==========================================\n")
