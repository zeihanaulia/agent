#!/usr/bin/env python3
"""
Debug LLM Setup - Test model initialization and LLM calls
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=" * 80)
print("🔧 DEBUG: LLM SETUP TEST")
print("=" * 80)
print()

# Check environment variables
print("📋 ENVIRONMENT VARIABLES:")
print(f"  LITELLM_API: {os.getenv('LITELLM_API', 'NOT SET')}")
print(f"  LITELLM_MODEL: {os.getenv('LITELLM_MODEL', 'NOT SET')}")
print(f"  LITELLM_VIRTUAL_KEY: {os.getenv('LITELLM_VIRTUAL_KEY', 'NOT SET')[:20]}...")
print()

# Test 1: Import litellm
print("✅ Test 1: Import litellm")
try:
    import litellm
    print("   ✓ LiteLLM imported successfully")
except ImportError as e:
    print(f"   ❌ FAILED: {e}")
    exit(1)
print()

# Test 2: Direct litellm.completion call
print("✅ Test 2: Direct litellm.completion() call")
try:
    model = os.getenv('LITELLM_MODEL', 'gpt-5-mini')
    api_key = os.getenv('LITELLM_VIRTUAL_KEY')
    api_base = os.getenv('LITELLM_API')
    
    print(f"   Model: {model}")
    print(f"   API Base: {api_base}")
    print()
    
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": "Say 'Hello World'"}],
        max_tokens=50,
        temperature=1.0,
        api_key=api_key,
        api_base=api_base
    )
    
    print(f"   ✓ Response received:")
    if hasattr(response, 'choices') and response.choices:
        content = response.choices[0].message.content
        print(f"     {content}")
    else:
        print(f"     {response}")
        
except Exception as e:
    print(f"   ❌ FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 3: Using ChatOpenAI from langchain
print("✅ Test 3: ChatOpenAI from langchain_openai")
try:
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr
    
    model_name = os.getenv('LITELLM_MODEL', 'gpt-5-mini')
    api_key = os.getenv('LITELLM_VIRTUAL_KEY')
    api_base = os.getenv('LITELLM_API')
    
    model = ChatOpenAI(
        api_key=SecretStr(api_key),
        model=model_name,
        base_url=api_base,
        temperature=1.0,
    )
    
    print(f"   ✓ ChatOpenAI initialized successfully")
    print(f"     Model: {model.model_name}")
    print()
    
    # Try invoking
    print("   Testing invocation...")
    result = model.invoke([{"role": "user", "content": "Say 'Test OK'"}])
    print(f"   ✓ Response: {result.content}")
    
except Exception as e:
    print(f"   ❌ FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 80)
print("✅ LLM DEBUG TEST COMPLETE")
print("=" * 80)
