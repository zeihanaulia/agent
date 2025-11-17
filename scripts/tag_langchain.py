from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ToolCallLimitMiddleware
)
from langchain.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()

# LLM
model = ChatOpenAI(
    model=os.getenv("LITELLM_MODEL", "gpt-3.5-turbo"),
    base_url=os.getenv("LITELLM_API"),
    api_key=os.getenv("LITELLM_VIRTUAL_KEY"), # pyright: ignore[reportArgumentType]
    temperature=0.2,
)

##############################################
# ----------------- TOOLS -------------------
##############################################

@tool
def simple_tool(input_str: str) -> str:
    """Example tool."""
    return f"Tool executed with: {input_str}"

tools = [simple_tool]


##############################################
# ----------- TAG-BASED SYSTEM PROMPT -------
##############################################

system_prompt_plain = """
You are a helpful teaching assistant.

Your task:
Explain what the HTTP GET method is.

Rules:
- Answer with exactly 3 bullet points.
- No examples.
- No questions.
- Keep the answer short.

When finished, output:
Final Answer: Completed
"""

##############################################
# ----------- TAG-BASED SYSTEM PROMPT -------
##############################################

system_prompt_tag = """
<identity>
You are a structured teaching assistant.
</identity>

<task>
Explain what HTTP GET method is.
</task>

<rules>
- Respond in exactly 3 bullet points.
- No examples.
- Do not ask questions.
</rules>

<output_format>
<answer>
<!-- Fill this only -->
</answer>
</output_format>

When done, output EXACTLY:
Final Answer: Completed
"""



##############################################
# -------------- CREATE AGENT ---------------
##############################################

middleware = [
    ModelCallLimitMiddleware(run_limit=6, thread_limit=1, exit_behavior="end"),
    ToolCallLimitMiddleware(run_limit=3, thread_limit=1, exit_behavior="end")
]

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt_tag,
    middleware=middleware,
)

agent_2 = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt_plain,
    middleware=middleware,
)

##############################################
# ------------------- RUN -------------------
##############################################

def print_response(response, title, is_raw=False):
    """Format and print response in a readable way."""
    if is_raw:
        print(f"\n{'='*60}")
        print(f"RAW OUTPUT: {title}")
        print(f"{'='*60}")
        print(response)
    else:
        print(f"\n{'='*60}")
        print(f"HUMAN READABLE: {title}")
        print(f"{'='*60}")
        
        # Extract content from response
        if isinstance(response, dict) and "messages" in response:
            messages = response["messages"]
            if messages and hasattr(messages[-1], "content"):
                content = messages[-1].content
                # Clean up content
                content = content.replace("\\n", "\n").strip()
                print(content)
        else:
            print(response)


if __name__ == "__main__":
    response = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Start."
        }]
    })
    print_response(response, "TAG-BASED RESPONSE", is_raw=False)
    print_response(response, "TAG-BASED RESPONSE (RAW)", is_raw=True)

    response = agent_2.invoke({
        "messages": [{
            "role": "user",
            "content": "Start."
        }]
    })
    print_response(response, "NON TAG-BASED RESPONSE", is_raw=False)
    print_response(response, "NON TAG-BASED RESPONSE (RAW)", is_raw=True)
