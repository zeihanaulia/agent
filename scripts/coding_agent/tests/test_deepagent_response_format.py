#!/usr/bin/env python3
"""Test script to inspect DeepAgent response format"""

import os
import sys
import json
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import AzureChatOpenAI

# Setup
codebase_path = "/Users/zeihanaulia/Programming/research/agent/dataset/codes/springboot-demo"

# Create model
model = AzureChatOpenAI(
    azure_endpoint=os.getenv("LITELLM_API"),
    api_key=os.getenv("LITELLM_VIRTUAL_KEY"),
    model="gpt-4-mini",
    temperature=0.3
)

# Create backend
backend = FilesystemBackend(root_dir=codebase_path)

# Create agent
agent = create_deep_agent(
    system_prompt="You are a helpful code assistant. Read the OrderController.java file and make a simple change to add a comment.",
    model=model,
    backend=backend
)

# Simple test input
print("🧪 Testing DeepAgent response format...")
print(f"Codebase: {codebase_path}")

try:
    result = agent.invoke({"input": "Read dataset/codes/springboot-demo/src/main/java/com/example/springboot/controller/OrderController.java and tell me what you see."})
    
    print("\n" + "="*60)
    print("RESPONSE TYPE:", type(result))
    print("="*60)
    
    if isinstance(result, dict):
        print(f"\nKeys in response: {list(result.keys())}")
        
        # Check for messages
        if "messages" in result:
            print(f"\nNumber of messages: {len(result['messages'])}")
            for i, msg in enumerate(result['messages']):
                print(f"\n  Message {i}:")
                print(f"    Type: {type(msg).__name__}")
                if hasattr(msg, 'content'):
                    print(f"    Content length: {len(str(msg.content))}")
                    print(f"    Content preview: {str(msg.content)[:200]}")
                if hasattr(msg, 'tool_calls'):
                    print(f"    Tool calls: {msg.tool_calls}")
        
        # Check for tool_execution_log
        if "tool_execution_log" in result:
            print(f"\nTool execution log length: {len(result['tool_execution_log'])}")
            for i, log in enumerate(result['tool_execution_log'][:3]):
                print(f"  Log {i}: {log}")
                
    print("\n" + "="*60)
    print("Full response (JSON-serializable parts):")
    print("="*60)
    
    # Try to print what we can
    if isinstance(result, dict):
        try:
            safe_result = {}
            for k, v in result.items():
                if k == "messages":
                    safe_result[k] = f"<{len(v)} messages>"
                elif isinstance(v, (str, int, float, bool, type(None))):
                    safe_result[k] = v
                else:
                    safe_result[k] = f"<{type(v).__name__}>"
            print(json.dumps(safe_result, indent=2))
        except Exception as e:
            print(f"Error serializing: {e}")
            
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
