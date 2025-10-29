import os
import re
import ast
import textwrap
import gradio as gr
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from e2b_code_interpreter import Sandbox
from typing import TypedDict

# === Load environment ===
load_dotenv()
api_key_env = os.environ.get("LITELLM_VIRTUAL_KEY")
if not api_key_env:
    raise RuntimeError("LITELLM_VIRTUAL_KEY not set in environment")

# === Initialize LLM ===
llm = ChatOpenAI(
    api_key=api_key_env, # pyright: ignore[reportArgumentType]
    model=os.getenv("LITELLM_MODEL", "gpt-4o-mini"),
    base_url=os.getenv("LITELLM_API"),
    temperature=0,
)

# === Create persistent E2B sandbox ===
sbx = Sandbox.create(template="code-interpreter-v1")
sbx.set_timeout(600)

# === Define LangGraph State ===
class AgentState(TypedDict):
    problem_desc: str
    current_code: str
    validator_code: str
    stdout_output: str
    stderr_output: str
    iteration: int
    done: bool
    logs: list[str]

# === Utility ===
def strip_code_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:python)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    text = ''.join(c for c in text if ord(c) < 128)
    return text

def run_code_in_sandbox(code: str):
    sbx.files.write("test_script.py", code)
    sbx.commands.run("pkill -9 python || true")
    exec_result = sbx.commands.run("python test_script.py")
    stdout_output = "".join(exec_result.stdout).replace("\r", "").replace("\n\n", "\n")
    stderr_output = "".join(exec_result.stderr)
    return stdout_output, stderr_output, exec_result

def extract_main_function_name(code: str) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = None

    if tree:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "Solution":
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef) and not sub.name.startswith("__"):
                        return sub.name
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef):
                        return sub.name
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node.name
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef) and not sub.name.startswith("__"):
                        return sub.name
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef):
                        return sub.name

    pattern = re.compile(r"^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE)
    match = pattern.search(code)
    if match:
        return match.group(1)

    class_pattern = re.compile(
        r"class\s+\w+\s*\(.*\):\s*(?:#.*\n|\s)*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        re.MULTILINE,
    )
    match = class_pattern.search(code)
    if match:
        return match.group(1)
    return "solution"

def build_test_runner(user_code: str, validator_code: str):
    user_code = textwrap.dedent(user_code)
    func_name = extract_main_function_name(user_code)
    return f"""
import sys
import inspect
{user_code}

{validator_code}

def _resolve_callable():
    if '{func_name}' in globals():
        return {func_name}
    SolutionCls = Solution
    try:
        solver = SolutionCls()
    except TypeError:
        solver = SolutionCls.__new__(SolutionCls)
        init = getattr(SolutionCls, "__init__", None)
        if callable(init):
            try:
                init(solver)
            except TypeError:
                pass
    return getattr(solver, '{func_name}')

_target_callable = _resolve_callable()
_signature = inspect.signature(_target_callable)
_has_varargs = any(
    param.kind == inspect.Parameter.VAR_POSITIONAL
    for param in _signature.parameters.values()
)

def _coerce_to_tuple(data):
    if isinstance(data, tuple):
        return data
    if isinstance(data, list):
        return tuple(data)
    return (data,)

def _trim_args(args):
    if _has_varargs:
        return args
    try:
        _signature.bind(*args)
        return args
    except TypeError:
        pass
    for length in range(len(args) - 1, -2, -1):
        candidate = args[:length] if length >= 0 else tuple()
        try:
            _signature.bind(*candidate)
            return candidate
        except TypeError:
            continue
    return args

def run_tests():
    for idx, inputs in enumerate(test_inputs, 1):
        try:
            raw_inputs = inputs
            original_args = _coerce_to_tuple(raw_inputs)
            call_args = _trim_args(original_args)
            try:
                result = _target_callable(*call_args)
            except TypeError as call_err:
                if call_args != original_args:
                    result = _target_callable(*original_args)
                    call_args = original_args
                else:
                    raise call_err

            if call_args == original_args:
                inputs_for_validate = raw_inputs
                if len(call_args) == 1 and not isinstance(raw_inputs, tuple):
                    inputs_for_validate = call_args[0]
            else:
                if len(call_args) == 1 and len(original_args) > len(call_args):
                    inputs_for_validate = call_args[0]
                elif len(call_args) == 1:
                    inputs_for_validate = call_args[0]
                elif len(call_args) == 0:
                    inputs_for_validate = tuple()
                else:
                    inputs_for_validate = call_args

            try:
                ok = validate(inputs_for_validate, result)
            except TypeError:
                ok = validate(raw_inputs, result)
            print(f"Case {{idx}}: {{'✅ PASSED' if ok else '❌ FAILED'}}")
            print("  Input:", inputs_for_validate)
            print("  Output:", result)
            print()
        except Exception as e:
            print(f"Case {{idx}}: ❌ ERROR: {{e}}")
    sys.stdout.flush()

if __name__ == "__main__":
    run_tests()
"""

def validator_uses_solution(validator_code: str, func_name: str) -> bool:
    func_call_pattern = r"\b" + re.escape(func_name) + r"\s*\("
    if re.search(func_call_pattern, validator_code):
        return True
    if "Solution(" in validator_code or "Solution()." in validator_code:
        return True
    if "class Solution" in validator_code:
        return True
    return False

def validator_is_placeholder(validator_code: str) -> bool:
    lowered = validator_code.lower()
    if "placeholder" in lowered or "todo" in lowered:
        return True
    if re.search(r"def\s+validate[^\n]*\n\s+pass\b", validator_code):
        return True
    return False

def validator_uses_output(validator_code: str) -> bool:
    body_match = re.split(r"def\s+validate[^\n]*:\n", validator_code, maxsplit=1)
    body = body_match[1] if len(body_match) > 1 else ""
    return "output" in body

def _extract_test_inputs(validator_code: str):
    namespace: dict[str, object] = {}
    try:
        exec(compile(validator_code, "<validator>", "exec"), {}, namespace)
    except Exception:
        return None
    test_inputs = namespace.get("test_inputs")
    if isinstance(test_inputs, (list, tuple)):
        return list(test_inputs)
    return None

def _build_validator_from_examples(test_inputs):
    if not test_inputs:
        return None
    cases = []
    for entry in test_inputs:
        if not isinstance(entry, (list, tuple)):
            return None
        entry_list = list(entry)
        if len(entry_list) < 2:
            return None
        expected = entry_list[-1]
        inputs_tuple = tuple(entry_list[:-1])
        if not inputs_tuple:
            return None
        cases.append((inputs_tuple, expected))
    if not cases:
        return None

    raw_cases_lines = ",\n".join(
        f"    ({repr(inputs_tuple)}, {repr(expected)})"
        for inputs_tuple, expected in cases
    )

    helper_template = textwrap.dedent(
        """
        _RAW_CASES = [
        {raw_cases}
        ]

        def _build_linked_list(values):
            if 'ListNode' not in globals():
                return values
            if values is None:
                return None
            if isinstance(values, list):
                if not values:
                    return None
                dummy = ListNode(0)
                current = dummy
                for item in values:
                    node = ListNode(item)
                    current.next = node
                    current = node
                return dummy.next
            return values

        def _prepare_argument(value):
            if 'ListNode' in globals() and isinstance(value, list):
                if not value:
                    return _build_linked_list(value)
                if all(isinstance(item, list) or item is None for item in value):
                    return [_prepare_argument(item) for item in value]
                if all(isinstance(item, (int, float)) or item is None for item in value):
                    return _build_linked_list(value)
            return value

        def _prepare_cases():
            prepared = []
            for inputs, expected in _RAW_CASES:
                prepared_inputs = tuple(_prepare_argument(arg) for arg in inputs)
                prepared.append((prepared_inputs, expected))
            return prepared

        _CASES = _prepare_cases()

        def _normalize(value):
            if value is None:
                if 'ListNode' in globals():
                    return []
                return None
            if isinstance(value, list):
                return [_normalize(v) for v in value]
            if isinstance(value, tuple):
                return tuple(_normalize(v) for v in value)
            if isinstance(value, dict):
                return {k: _normalize(v) for k, v in value.items()}
            if hasattr(value, "val") and hasattr(value, "next"):
                seen = set()
                current = value
                result = []
                while current and id(current) not in seen:
                    seen.add(id(current))
                    result.append(_normalize(getattr(current, "val", None)))
                    current = getattr(current, "next", None)
                return result
            return value

        def validate(inputs, output):
            for sample_inputs, expected in _CASES:
                if inputs == sample_inputs:
                    return _normalize(output) == _normalize(expected)
            return False

        test_inputs = [case[0] for case in _CASES]
        """
    )

    helper_code = helper_template.replace("{raw_cases}", raw_cases_lines).strip()
    return helper_code

# === LangGraph nodes ===
def generate_validator(state: AgentState) -> AgentState:
    func_name = extract_main_function_name(state["current_code"])
    validator_prompt = f"""
You are a property-based testing generator for Python code.

Problem:
{state['problem_desc']}

Important:
- The user code defines a main function or class method to test.
- The main callable to test is the first top-level function or method found in the user's code below.
- Use exactly that name when calling it inside your test cases.
- Absolutely DO NOT call the implementation under test (no `{func_name}(... )`, `Solution().{func_name}`, or variants) while validating.
- Compute the expected behaviour yourself using Python logic, not by delegating back to the provided code.
- Prefer deterministic and complete checks (for example, rely on Python's standard library such as `re.fullmatch` for regex problems, or write a straightforward brute-force/verification routine).
- Avoid placeholder logic or heuristics that only work for a subset of cases.
- Include edge cases such as empty inputs, multiple consecutive '*' segments in the pattern, and duplicate or tie scenarios where applicable.
- In `validate`, compare the expected result with the `output` argument (e.g., `return expected == output`). Never return the expected value by itself.
- If you cannot derive the logic, return placeholder tests that still follow the rules above (but do not call the solution).

User code:
{state['current_code']}

Requirements:
1. Generate a function named `validate(inputs, output)` that returns True if the output satisfies the problem definition.
2. Generate a small list of 3–5 `test_inputs` tuples, each being the arguments to pass to the function (do not include expected outputs in the tuples).
   Example: `test_inputs = [ (arg1, arg2), (arg3, ) ]` where the tuples match the function's signature.
3. Output runnable Python code (no markdown) defining both `validate` and `test_inputs`.
"""

    prompt = validator_prompt
    for attempt in range(5):
        response = llm.invoke([
            SystemMessage(content="You are a Python validator generator."),
            HumanMessage(content=prompt)
        ])
        validator_code = strip_code_fence(str(response.content))
        print("\n📄 Validator attempt:\n", validator_code)
        issues = []
        if validator_uses_solution(validator_code, func_name):
            issues.append("referenced the implementation under test")
        placeholder = validator_is_placeholder(validator_code)
        if placeholder:
            samples = _extract_test_inputs(validator_code)
            salvaged = _build_validator_from_examples(samples)
            if salvaged:
                print("\n♻️ Rebuilt validator from provided examples.")
                validator_code = salvaged
                placeholder = False
            else:
                issues.append("did not implement real validation logic")
        if "class Solution" in validator_code:
            issues.append("reintroduced a Solution class in validator")
        if issues:
            prompt = validator_prompt + f"""

The previous attempt {', '.join(issues)}. Regenerate the validator implementing the correct behaviour without those mistakes.
"""
            continue
        if not validator_uses_output(validator_code):
            wrapper = textwrap.dedent("""
            _original_validate = validate
            def validate(inputs, output):
                expected = _original_validate(inputs, output)
                return expected == output
            """)
            validator_code = validator_code.rstrip() + "\n\n" + wrapper.strip()
        validator_code += "\nimport sys; sys.stdout.flush()"
        state["validator_code"] = validator_code
        break
    else:
        raise RuntimeError("Failed to generate a valid validator without referencing the solution.")

    return state

def run_tests(state: AgentState) -> AgentState:
    combined_code = build_test_runner(state["current_code"], state["validator_code"])
    stdout_output, stderr_output, execution = run_code_in_sandbox(combined_code)

    failed = "❌" in stdout_output
    exit_code = getattr(execution, "exit_code", getattr(execution, "returncode", None))

    if not failed and (not exit_code or exit_code == 0):
        state["done"] = True
    else:
        state["done"] = False

    state["stdout_output"] = stdout_output
    state["stderr_output"] = stderr_output
    iter_mark = state["iteration"]
    logs = state.get("logs", [])
    logs.append(f"Iteration {iter_mark}:\n{stdout_output or '<empty>'}")
    state["logs"] = logs
    return state

def fix_code(state: AgentState) -> AgentState:
    if state["done"]:
        return state

    fix_prompt = f"""
You are an AI code repair agent.

Problem:
{state['problem_desc']}

Your current code:
{state['current_code']}

Validation rules and test inputs:
{state['validator_code']}

Execution result:
{state['stdout_output']}

Instructions:
- Find why your implementation violates the validator logic.
- Rewrite the entire function correctly.
- Output only runnable Python code (no markdown, no explanation).
"""
    fix_response = llm.invoke([
        SystemMessage(content="You are a senior debugging agent."),
        HumanMessage(content=fix_prompt)
    ])
    fixed_code = strip_code_fence(str(fix_response.content))
    if fixed_code.strip() == state["current_code"].strip():
        state["done"] = True
    else:
        state["current_code"] = fixed_code
        state["iteration"] += 1

    return state

# === Graph definition ===
def route_after_fix(state: AgentState):
    if state["done"]:
        return END
    else:
        return "RunTests"

graph = StateGraph(AgentState)
graph.add_node("GenerateValidator", generate_validator)
graph.add_node("RunTests", run_tests)
graph.add_node("FixCode", fix_code)

graph.set_entry_point("GenerateValidator")
graph.add_edge("GenerateValidator", "RunTests")
graph.add_edge("RunTests", "FixCode")
graph.add_conditional_edges("FixCode", route_after_fix)

app = graph.compile()

# === Gradio Interface ===
def run_agent(problem_desc, initial_code):
    init_state = AgentState(
        problem_desc=problem_desc,
        current_code=initial_code,
        validator_code="",
        stdout_output="",
        stderr_output="",
        iteration=1,
        done=False,
        logs=[]
    )

    final_state = app.invoke(init_state)
    log_text = "\n\n".join(final_state.get("logs", []))
    return final_state["current_code"], log_text

with gr.Blocks() as demo:
    gr.Markdown("# Code Repair Agent")
    gr.Markdown("Input a problem description and initial buggy code. The agent will iteratively fix the code using LLM and sandbox testing.")

    with gr.Row():
        problem_input = gr.Textbox(
            label="Problem Description", 
            lines=5, 
            placeholder="Describe the coding problem...",
            value="""Given an input string s and a pattern p, implement regular expression matching with support for '.' and '*' where:

'.' Matches any single character.​​​​
'*' Matches zero or more of the preceding element.
The matching should cover the entire input string (not partial)."""
        )
        code_input = gr.Textbox(
            label="Initial Code", 
            lines=10, 
            placeholder="Paste your initial Python code here...",
            value="""class Solution(object):
    def isMatch(self, s, p):
        return True"""
        )

    run_btn = gr.Button("Run Agent")

    code_output = gr.Textbox(label="Fixed Code", lines=15, interactive=False)
    log_output = gr.Textbox(label="Iteration Logs", lines=15, interactive=False)

    run_btn.click(fn=run_agent, inputs=[problem_input, code_input], outputs=[code_output, log_output])

if __name__ == "__main__":
    demo.launch()
