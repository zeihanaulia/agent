#!/usr/bin/env python3
"""
Debug LLM Response Parsing - Check what LLM actually returns
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent / "scripts" / "coding_agent"))

from flow_analyze_context import AiderStyleRepoAnalyzer

def test_llm_response():
    print("=" * 80)
    print("🔍 DEBUG: LLM RESPONSE PARSING")
    print("=" * 80)
    print()
    
    codebase_path = "dataset/codes/springboot-demo"
    analyzer = AiderStyleRepoAnalyzer(codebase_path, max_tokens=4096)
    
    # Get analysis
    print("📂 Analyzing codebase...")
    analysis_result = analyzer.analyze_codebase()
    
    structure = analysis_result.get("structure", {})
    discovered_packages = structure.get("java_packages", [])
    
    print(f"✅ Discovered packages: {discovered_packages}")
    print()
    
    # Call reasoning directly
    print("🧠 Calling LLM reasoning...")
    print()
    
    response = analyzer.main_model.generate_reasoning(
        prompt="""
Return a JSON with this exact structure:
{
  "placements": [
    {"type": "entity", "package": "com.example.springboot", "directory": "src/main/java/com/example/springboot"},
    {"type": "controller", "package": "com.example.springboot", "directory": "src/main/java/com/example/springboot"}
  ]
}
""",
        max_tokens=300
    )
    
    print("📄 LLM Raw Response:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    print()
    
    # Try parsing
    print("🔧 Attempting JSON parse...")
    try:
        import json
        json_start = response.find('{')
        if json_start >= 0:
            json_str = response[json_start:]
            parsed = json.loads(json_str)
            print("✅ Successfully parsed JSON:")
            print(json.dumps(parsed, indent=2))
        else:
            print("❌ No JSON found in response")
    except Exception as e:
        print(f"❌ JSON parse failed: {e}")
    
    print()

if __name__ == "__main__":
    test_llm_response()
