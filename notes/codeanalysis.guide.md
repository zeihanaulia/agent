# Code Analysis Agent - Educational Guide

## 📚 File Structure & Learning Path

This restructured `code_analysis.py` is designed as an **educational resource** to learn how AI agents work with tools. Here's how to read and understand it:

---

## 📖 Reading Guide (Step by Step)

### **SECTION 1: Module Header & Imports (Lines 1-50)**
```
PURPOSE: Understanding what this script does and why
```
- **What to learn**: Module docstring explains the purpose, key concepts, and workflow
- **Key concepts introduced**: 
  - Tool Definition (@tool decorator)
  - Agent Invocation
  - Message Processing
  - Result Extraction

### **SECTION 2: Model Configuration (Lines 51-95)**
```
PURPOSE: Setting up the AI model that powers the agent
```
- **What to learn**: How to configure LLM parameters
- **Key decisions**:
  - Model selection from environment
  - Temperature tuning (reasoning models use higher temp)
  - API configuration

**Questions to ask yourself:**
- Why does temperature matter?
- What's the difference between reasoning and non-reasoning models?

---

### **SECTION 3: Tool Definitions (Lines 96-375)**
```
PURPOSE: Defining what the agent CAN DO
```

This is the **most important section** for learning. Each tool has:

#### Tool Structure:
```python
@tool
def function_name(arg1: type1, arg2: type2 = default) -> return_type:
    """
    PURPOSE: What does this tool accomplish?
    
    ARGUMENTS:
        arg1 (type1): What is this argument for? Examples?
        arg2 (type2): Why do we need this? Default value & why?
    
    RETURN VALUE (type):
        What format is returned? When does it succeed? Error cases?
    
    WHY THIS TOOL:
        Why does the agent need this capability?
    """
    # Implementation
```

#### The Four Tools Explained:

1. **`list_directory(path: str) -> str`**
   - **Why**: Agent needs to see what files exist
   - **Learning point**: Simple filesystem operation, basic error handling
   - **Use case**: Initial codebase exploration

2. **`read_file(file_path: str, max_lines: int = 100) -> str`**
   - **Why**: Agent needs to read file contents
   - **Learning point**: Pagination concept (max_lines parameter)
   - **Use case**: Reading config files, source code

3. **`find_files_by_pattern(directory: str, pattern: str) -> str`**
   - **Why**: Agent needs to find specific file types
   - **Learning point**: Pattern matching with glob
   - **Use case**: Finding all "*.java" or "*.py" files

4. **`get_directory_structure(path: str, max_depth: int = 3) -> str`**
   - **Why**: Agent needs visual understanding of structure
   - **Learning point**: Recursive tree building
   - **Use case**: Understanding project layout

**Key Learning Concept**: Each tool returns a **string** because:
- The AI model can only understand text
- Tools translate filesystem operations into text descriptions
- This text is sent back to the model for interpretation

---

### **SECTION 4: Argument Parsing (Lines 376-396)**
```
PURPOSE: Getting input from the user
```
- **What to learn**: Command-line argument handling
- **How it works**:
  1. Check for `--codebase-path` argument
  2. Fall back to `CODEBASE_PATH` environment variable
  3. Use default path if neither provided
  4. Allow interactive override if running in terminal

---

### **SECTION 5: Analysis Prompt (The Agent's Instructions) (Lines 397-442)**
```
PURPOSE: Telling the agent WHAT to do and HOW to do it
```

This is the **system prompt** - it's critical for agent behavior:

**Components**:
- **Task Definition**: What is the agent's goal?
- **Available Tools**: Which tools can the agent use?
- **Instructions**: HOW to use the tools effectively?
- **Workflow**: What's the recommended order of operations?

**Key Learning Point**: 
- A good system prompt is more important than the model itself
- The prompt guides the agent's reasoning

---

### **SECTION 6: Agent Creation & Invocation (Lines 443-494)**
```
PURPOSE: Running the analysis
```

**What happens here**:
1. **Create DeepAgent**: Combine model + tools + prompt
2. **Print status**: Show user what's happening
3. **Invoke agent**: Start the analysis loop
4. **Time it**: Measure how long the analysis takes

**Key Learning Concept**: Agent Invocation Loop
```
1. Agent reads prompt and input
2. Agent decides which tools to call
3. Tools execute and return results
4. Agent reads results and decides next step
5. Repeat until agent decides it has the answer
```

---

### **SECTION 7: Result Processing (Lines 495-527)**
```
PURPOSE: Extracting and displaying the analysis
```

**What to learn**: Message processing in AI systems

The agent returns a **messages list** containing:
- **HumanMessage**: The input from the user
- **AIMessage**: The agent's thinking/decisions
- **ToolMessage**: Results from tool calls

**Processing logic**:
1. Count tool calls made
2. Find final analysis (last AIMessage without tool calls)
3. Display the result

---

### **SECTION 8: Optional Debug Output (Lines 528-559)**
```
PURPOSE: Understanding what the agent did (learning tool)
```

Uncomment this section to see:
- All tool calls made
- Tool arguments used
- Tool responses received

This helps you understand **HOW** the agent arrived at its conclusion.

---

## 🎯 Learning Exercises

### Exercise 1: Understand Tool Flow
**Question**: What happens if a tool returns an error?
**Answer**: Look at `read_file()` - it catches exceptions and returns error strings

### Exercise 2: Modify a Tool
**Task**: Add a `count_lines(file_path)` tool that returns number of lines in a file
**Learning**: Understand how tools extend agent capabilities

### Exercise 3: Change the Prompt
**Task**: Modify the system prompt to focus on security analysis instead
**Learning**: See how prompt changes affect agent behavior

### Exercise 4: Add Error Handling
**Task**: Add timeout handling for the agent invocation
**Learning**: Production-ready error handling

---

## 🔍 Key Concepts to Master

### 1. **The @tool Decorator**
```python
@tool
def my_tool(arg: str) -> str:
    """Docstring becomes tool description"""
    return result
```
- Converts Python function into an agent-callable tool
- Docstring is **critical** - it's how the agent understands the tool

### 2. **Agent Decision Making**
The agent uses **reasoning** to decide:
- Which tools to call?
- In what order?
- With what arguments?

This is based on the system prompt and agent's "understanding" of the goal.

### 3. **Message Flow**
```
User Input
    ↓
Agent Reasoning
    ↓
Tool Selection
    ↓
Tool Execution
    ↓
Result Processing
    ↓
Agent Reasoning (repeat or conclude)
    ↓
Final Response
```

### 4. **Limitations to Understand**
- Agent can only work with text input/output
- Agent can't read binary files
- Agent's reasoning is limited by context window
- Agent may hallucinate or make mistakes

---

## 📝 How to Run This Script

### Basic Usage:
```bash
# Use default codebase
python scripts/code_analysis.py

# Specify custom codebase
python scripts/code_analysis.py --codebase-path /path/to/project

# Via environment variable
export CODEBASE_PATH=/path/to/project
python scripts/code_analysis.py
```

### Understanding the Output:
```
🤖 DEEP CODE ANALYSIS AGENT (VERBOSE MODE)  ← Shows configuration
📁 Target Codebase: ...                      ← Which codebase?
🛠️  Model: ...                               ← Which AI model?

[HH:MM:SS] 📋 Agent initialized             ← Agent ready
[HH:MM:SS] 🔍 Starting analysis...          ← Beginning
[HH:MM:SS] ✅ Analysis completed in X.XX s   ← Finished

📈 Analysis Summary:
   • Tool calls made: N                      ← How many tools used?
   • Analysis time: X.XX seconds             ← Total time
   • Average time per tool: Y.YY seconds     ← Performance

📊 FINAL ANALYSIS RESULT:
FINAL RESULT:
[Comprehensive analysis output]             ← The answer
```

---

## 🚀 Next Steps for Learning

1. **Understand each tool** - Read the docstring and implementation
2. **Trace through an execution** - Uncomment debug output and see what happens
3. **Modify a tool** - Add new functionality
4. **Create a new tool** - Add a `search_in_files()` tool
5. **Change the prompt** - See how different instructions affect results
6. **Handle errors** - Add timeout and exception handling

---

## 📚 Resources for Further Learning

- **DeepAgents Documentation**: How agents and tools work
- **LangChain Tools**: More advanced tool patterns
- **Prompt Engineering**: How to write better system prompts
- **AI/ML Fundamentals**: Understanding model behavior

---

## 💡 Key Takeaways

1. **Tools are the bridge** between AI models and external systems
2. **Prompts guide behavior** more than model selection
3. **Message flow is key** to understanding agent decisions
4. **Error handling matters** in production systems
5. **Verbose output helps debugging** and learning

Good luck with your learning! 🎓
