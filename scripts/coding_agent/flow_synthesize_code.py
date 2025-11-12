"""
PHASE 4: CODE SYNTHESIS - Multi-Step Expert Implementation
===========================================================

Responsible for:
- Planning implementation based on architecture analysis
- Multi-step code generation with structured prompts
- Generating code patches with validation
- Supporting layered architecture (controller, service, repository, etc.)
"""

import os
import sys
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from feature_by_request_agent_v3 import AgentState

# Import generation mode agent for tool whitelisting
from agents.agent_factory import create_code_synthesis_agent_generation_mode


def invoke_with_timeout(agent, input_data, timeout_seconds=30):
    """
    Invoke agent with timeout protection and proper tool execution loop.
    
    FIX: Use .stream() instead of .invoke() to ensure agent loop runs and tools execute.
    DeepAgent (LangGraph) requires streaming to actually execute tool calls.
    Single .invoke() call doesn't trigger tool execution loop.
    """
    import threading
    
    result_container = {"status": "pending", "data": None, "error": None, "all_chunks": []}
    
    def worker():
        try:
            # Use .stream() for proper agent loop with tool execution
            # This ensures agent runs until it completes all tool calls
            all_chunks = []
            for chunk in agent.stream(input_data, stream_mode="values"):
                all_chunks.append(chunk)
            
            # The final chunk contains the complete agent state with all results
            if all_chunks:
                result_container["all_chunks"] = all_chunks
                result_container["data"] = all_chunks[-1]  # Last chunk is final state
            else:
                result_container["data"] = {}
            
            result_container["status"] = "success"
        except Exception as e:
            import traceback
            result_container["status"] = "error"
            result_container["error"] = str(e)
            result_container["traceback"] = traceback.format_exc()
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if result_container["status"] == "pending":
        print(f"  ⚠️  Agent stream timeout after {timeout_seconds}s - switching to fast mode")
        return None
    
    if result_container["status"] == "error":
        error_msg = result_container["error"]
        tb = result_container.get("traceback", "")
        print(f"  ❌ Agent error: {error_msg}")
        if tb:
            print(f"     {tb[:200]}")
        raise Exception(error_msg)
    
    return result_container["data"]


def _extract_patch_from_call(call: Dict[str, Any], progress: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """Extract single patch from LangChain-style tool call"""
    if call.get("name") not in ["write_file", "edit_file"]:
        return None
    
    tool_args = call.get("args", {})
    tool_name = call.get("name")
    # IMPORTANT: LLM might use 'file_path' or 'path', check both
    file_path = tool_args.get("path") or tool_args.get("file") or tool_args.get("file_path")
    
    if tool_name == "write_file":
        content = tool_args.get("content", "")
        if file_path and content and len(content.strip()) > 0:
            if progress:
                loc = len(content.split('\n'))
                for file_task in progress.files_to_create:
                    if file_path in file_task.filepath or file_task.name in file_path:
                        from progress_tracker import TaskStatus
                        file_task.status = TaskStatus.COMPLETED
                        file_task.lines_of_code = loc
            return {"tool": tool_name, "args": tool_args, "description": "Generated file", "file": file_path}
        elif not file_path:
            print("    ⚠️  Skipped write_file with missing path")
        elif not content:
            print(f"    ⚠️  Skipped write_file with empty content: {file_path}")
    
    elif tool_name == "edit_file":
        old_string = tool_args.get("oldString", "")
        new_string = tool_args.get("newString", "")
        if file_path and old_string and new_string:
            return {"tool": tool_name, "args": tool_args, "description": "Modified file", "file": file_path}
        elif not file_path:
            print("    ⚠️  Skipped edit_file with missing path")
        elif not old_string or not new_string:
            print(f"    ⚠️  Skipped edit_file missing oldString/newString: {file_path}")
    
    return None


def extract_patches_from_result(
    result: Optional[Dict[str, Any]], 
    progress: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Extract tool calls (write_file, edit_file) from agent response
    
    Handles multiple result formats:
    - Format 0: Stream state with "files" dict (from .stream() output)
    - Format 1: LangChain style with "messages" key
    - Format 2: DeepAgent style with "tool_execution_log"
    - Format 3: Result with "response" field
    - Format 4: String response
    - Format 5: Generic dict with alternate field names
    - Format 6: Direct files dict from DeepAgent
    
    Args:
        result: Agent invoke result (various formats)
        progress: WorkProgress tracker to update file creation status
    
    Returns:
        List of validated patches with tool name and arguments
    """
    patches = []
    
    if not result:
        return patches
    
    # Format 0: Stream state with "files" dict (from .stream() output)
    # This is the NEW format from using .stream() instead of .invoke()
    if isinstance(result, dict) and "files" in result and isinstance(result.get("files"), dict):
        files_dict = result.get("files", {})
        if files_dict and any(len(str(v).strip()) > 0 for v in files_dict.values()):
            print("  ℹ️ Using format: stream-state with files (from .stream())")
            for file_path, content in files_dict.items():
                content_str = str(content) if content else ""
                if file_path and len(content_str.strip()) > 0:
                    patch = {
                        "tool": "write_file",
                        "args": {"path": file_path, "content": content_str},
                        "description": "Generated file",
                        "file": file_path
                    }
                    patches.append(patch)
                    if progress:
                        loc = len(content_str.split('\n'))
                        for file_task in progress.files_to_create:
                            if file_path in file_task.filepath or file_task.name in file_path:
                                from progress_tracker import TaskStatus
                                file_task.status = TaskStatus.COMPLETED
                                file_task.lines_of_code = loc
            if patches:
                return patches  # Return early if we found patches
    
    # Format 6: DeepAgent direct files dict
    if isinstance(result, dict) and "files" in result and isinstance(result.get("files"), dict):
        print("  ℹ️ Using format: direct-files (DeepAgent)")
        files_dict = result.get("files", {})
        for file_path, content in files_dict.items():
            if content and len(str(content).strip()) > 0:
                patch = {"tool": "write_file", "args": {"path": file_path, "content": content}, "description": "Generated file", "file": file_path}
                patches.append(patch)
        if patches:
            return patches  # Return early if we found patches in files format
    
    # Format 1: LangChain style with "messages" key (original format)
    if isinstance(result, dict) and "messages" in result:
        print("  ℹ️ Using format: messages-based (LangChain)")
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls"):
                for call in getattr(msg, "tool_calls", []):
                    patch = _extract_patch_from_call(call, progress)
                    if patch:
                        patches.append(patch)
    
    # Format 2: DeepAgent style with "tool_execution_log" key
    elif isinstance(result, dict) and "tool_execution_log" in result:
        print("  ℹ️ Using format: tool_execution_log (DeepAgent)")
        for log_entry in result.get("tool_execution_log", []):
            if isinstance(log_entry, dict) and log_entry.get("tool") in ["write_file", "edit_file"]:
                tool_name = log_entry.get("tool")
                file_path = log_entry.get("path") or log_entry.get("file")
                
                if tool_name == "write_file":
                    content = log_entry.get("content") or log_entry.get("output", "")
                    if file_path and content:
                        if progress:
                            loc = len(str(content).split('\n'))
                            for file_task in progress.files_to_create:
                                if file_path in file_task.filepath or file_task.name in file_path:
                                    from progress_tracker import TaskStatus
                                    file_task.status = TaskStatus.COMPLETED
                                    file_task.lines_of_code = loc
                        patches.append({
                            "tool": "write_file",
                            "args": {"path": file_path, "content": content},
                            "description": "Generated file",
                            "file": file_path
                        })
                
                elif tool_name == "edit_file":
                    old_string = log_entry.get("oldString") or log_entry.get("old", "")
                    new_string = log_entry.get("newString") or log_entry.get("new", "")
                    if file_path and old_string and new_string:
                        patches.append({
                            "tool": "edit_file",
                            "args": {"path": file_path, "oldString": old_string, "newString": new_string},
                            "description": "Modified file",
                            "file": file_path
                        })
    
    # Format 3: Result with "response" or "output" field
    elif isinstance(result, dict) and ("response" in result or "output" in result):
        print("  ℹ️ Using format: response/output field")
        response_text = result.get("response") or result.get("output", "")
        # Could parse response text for patterns, but for now just note it
        if response_text and len(str(response_text)) > 100:
            print(f"  ℹ️ Response received: {str(response_text)[:100]}...")
    
    # Format 4: String response (agent final message)
    elif isinstance(result, str):
        print("  ℹ️ Using format: string response")
        response_str = str(result)
        if len(response_str) > 100:
            response_preview = response_str[:100]
            print(f"  ℹ️ Response: {response_preview}...")
    
    # Format 5: Generic dict with common field names
    elif isinstance(result, dict):
        print("  ℹ️ Using format: generic dict (searching for tool results)")
        for key in ["output", "result", "data", "tool_calls", "patches"]:
            if key in result and isinstance(result[key], list):
                for item in result[key]:
                    if isinstance(item, dict) and item.get("tool") in ["write_file", "edit_file"]:
                        tool_name = item.get("tool")
                        file_path = item.get("path") or item.get("file")
                        
                        if tool_name == "write_file" and file_path:
                            content = item.get("content", "")
                            if content:
                                patches.append({
                                    "tool": "write_file",
                                    "args": {"path": file_path, "content": content},
                                    "description": "Generated file",
                                    "file": file_path
                                })
                        elif tool_name == "edit_file" and file_path:
                            old_string = item.get("oldString", "")
                            new_string = item.get("newString", "")
                            if old_string and new_string:
                                patches.append({
                                    "tool": "edit_file",
                                    "args": {"path": file_path, "oldString": old_string, "newString": new_string},
                                    "description": "Modified file",
                                    "file": file_path
                                })
    
    return patches


def log_agent_response(result: Optional[Dict[str, Any]]) -> None:
    """Log the agent's final response for debugging"""
    if result and isinstance(result, dict) and "messages" in result:
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                content_str = str(msg.content)[:300]
                print(f"  ℹ️ Agent response: {content_str}")
                break
    elif result is None:
        print("  ℹ️ No agent response (timeout occurred)")


def build_layer_guidance(refactoring_note: str) -> str:
    """Build layer-aware implementation guidance for Spring Boot projects"""
    if not refactoring_note:
        return ""
    
    return """
LAYERED ARCHITECTURE REQUIREMENTS:
Your task is to CREATE NEW FILES in the layer directories for separation of concerns:

📦 MODEL LAYER (src/main/java/com/example/springboot/model/):
   - ORDER ENTITY: Order.java - JPA entity with @Entity, @Table("orders")
   - Package: com.example.springboot.model
   - Fields: id (auto-generated), product_name, quantity, price, created_at
   - Use @Column annotations for mapping

📦 DTO LAYER (src/main/java/com/example/springboot/dto/):
   - OrderDTO.java - Data Transfer Object for responses
   - OrderRequest.java - Request DTO for creation/updates
   - Package: com.example.springboot.dto
   - Setters/getters, no business logic

📦 REPOSITORY LAYER (src/main/java/com/example/springboot/repository/):
   - OrderRepository.java - Interface extending JpaRepository
   - Package: com.example.springboot.repository
   - Methods: findById, findAll, save, delete (inherited from JpaRepository)
   - Mark with @Repository annotation

📦 SERVICE LAYER (src/main/java/com/example/springboot/service/):
   - OrderService.java - Business logic implementation
   - Package: com.example.springboot.service
   - Methods: createOrder(), getOrderById(), getAllOrders(), deleteOrder()
   - Use @Service annotation, @Autowired for OrderRepository dependency

📦 CONTROLLER LAYER (src/main/java/com/example/springboot/controller/):
   - OrderController.java - REST API endpoints
   - Package: com.example.springboot.controller
   - Endpoints: POST /api/orders, GET /api/orders/{id}, GET /api/orders, DELETE /api/orders/{id}
   - Use @RestController, @RequestMapping("/api/orders")

IMPORTANT:
- Use write_file to CREATE NEW FILES in the layer directories above
- Each file must have its correct package declaration
- Use proper Spring Boot annotations (@Entity, @Repository, @Service, @RestController)
- Follow existing code style from HelloController
- Files MUST be created in their respective layer directories, not the root package

DO NOT modify HelloController unless absolutely necessary.
CREATE the new layer files NOW.
"""


def build_analysis_prompt(spec_intent: str, files_to_modify: List[str], framework_prompt: str, refactoring_note: str, original_request: str = "") -> str:
    """Build the multi-step analysis prompt for agent planning"""
    architecture = ""  # Placeholder - will be populated from impact analysis
    
    return f"""
FEATURE REQUEST: {spec_intent}

FILES TO MODIFY: {', '.join(files_to_modify[:3])}

{framework_prompt}

{refactoring_note}

STEP 1: ANALYSIS & PLANNING

1. Use read_file to examine each file in FILES TO MODIFY
2. Understand the existing code structure, naming conventions, imports, and patterns
3. Identify classes, interfaces, methods, and their responsibilities
4. Use write_todos to create a detailed implementation plan with:
   - Task: Understand [file] - purpose and current implementation
   - Task: Identify patterns - what design patterns are used
   - Task: Plan changes to [file] - exactly what needs to change
   - Task: Implement [method/class] - with specific code requirements
   - Task: Create tests for [functionality]

ARCHITECTURE CONTEXT:
{architecture}

Be thorough in understanding before planning implementation.
"""


def build_implementation_prompt(spec_intent: str, files_to_modify: List[str], framework_prompt: str, layer_guidance: str, spec: Optional[Any] = None, impact: Optional[Dict[str, Any]] = None, original_request: str = "") -> str:
    """Build the code implementation prompt for agent execution with full context"""
    
    # Build explicit file creation guide (NEW - HIGH PRIORITY)
    file_creation_guide = ""
    if spec and hasattr(spec, 'new_files'):
        new_files = getattr(spec, 'new_files', [])
        if new_files:
            file_creation_guide = "\n🎯 EXPLICIT FILES TO CREATE (PRIORITY ORDER):\n"
            base_package = "src/main/java/com/example/springboot"
            
            # Map file names to layers
            file_mappings = {
                'DTO': ('dto', 'Data Transfer Objects - plain classes with getters/setters'),
                'Entity': ('model', 'JPA domain entities with @Entity annotation'),
                'Repository': ('repository', 'Data access layer extending JpaRepository'),
                'Service': ('service', 'Business logic layer with @Service annotation'),
                'Controller': ('controller', 'REST API endpoints with @RestController'),
                'Request': ('dto', 'Request DTO for POST/PUT operations'),
                'Response': ('dto', 'Response DTO for GET operations'),
                'Exception': ('exception', 'Custom exception classes'),
            }
            
            file_creation_guide += "   START HERE - Create files in this exact order:\n"
            for i, file_name in enumerate(new_files[:7], 1):
                # Determine layer based on file name
                layer = "TBD"
                description = "Model/DTO/Service class"
                
                for key, (layer_name, desc) in file_mappings.items():
                    if key in file_name:
                        layer = layer_name
                        description = desc
                        break
                
                file_path = f"{base_package}/{layer}/{file_name}"
                file_creation_guide += f"   {i}. {file_name}\n"
                file_creation_guide += f"      Location: {file_path}\n"
                file_creation_guide += f"      Type: {description}\n"
    
    # Build new files planning section
    new_files_section = ""
    if spec and hasattr(spec, 'new_files_planning') and spec.new_files_planning:
        planning = spec.new_files_planning
        new_files_section = "\n📋 NEW FILES PLANNING (With Framework Conventions):\n"
        
        if hasattr(planning, 'creation_order') and planning.creation_order:
            new_files_section += "   Execution Order: " + " → ".join(planning.creation_order[:5]) + "\n"
        
        if hasattr(planning, 'best_practices') and planning.best_practices:
            new_files_section += "   Best Practices:\n"
            for bp in planning.best_practices[:3]:
                new_files_section += f"      - {bp}\n"
    
    # Build design patterns section
    patterns_section = ""
    if impact and impact.get('patterns_to_follow'):
        patterns = impact.get('patterns_to_follow', [])
        if patterns:
            patterns_section = "\n🔄 DESIGN PATTERNS TO FOLLOW:\n"
            for pattern in patterns[:5]:
                patterns_section += f"   - {pattern}\n"
    
    # Build testing strategy section
    testing_section = ""
    if impact and impact.get('testing_approach'):
        testing_approach = impact.get('testing_approach', '')
        if testing_approach:
            testing_section = f"\n✅ TESTING STRATEGY:\n   {testing_approach}\n"
    
    # Build constraints section
    constraints_section = ""
    if impact and impact.get('constraints'):
        constraints = impact.get('constraints', [])
        if constraints:
            constraints_section = "\n⚠️  CONSTRAINTS & BEST PRACTICES:\n"
            for constraint in constraints[:5]:
                constraints_section += f"   - {constraint}\n"
    
    # Build todo execution guide
    todos_section = ""
    if spec and hasattr(spec, 'todo_list') and spec.todo_list:
        todo_list = spec.todo_list
        todos_section = "\n📝 GENERATION PHASE EXECUTION CHECKLIST:\n"
        if hasattr(todo_list, 'todos'):
            gen_todos = [t for t in todo_list.todos if getattr(t, 'phase', '') == 'generation']
            for t in gen_todos[:5]:
                title = getattr(t, 'title', 'Task')
                todos_section += f"   [ ] {title}\n"
    
    # Include original request if provided
    original_request_section = f"\n🎯 ORIGINAL USER REQUEST:\n{original_request}\n" if original_request else ""
    
    # Build new files list for emphasis in reordered prompt
    new_files_explicit = ""
    new_files_count = 10
    if spec and hasattr(spec, 'new_files_planning') and spec.new_files_planning:
        planning = spec.new_files_planning
        new_files_explicit = "\n⭐ EXACT FILES TO CREATE - DO NOT DEVIATE:\n"
        for i, suggestion in enumerate(planning.suggested_files[:10], 1):
            filename = getattr(suggestion, 'filename', 'unknown')
            filepath = getattr(suggestion, 'relative_path', 'unknown')
            new_files_explicit += f"   {i}. {filename}\n      Path: {filepath}/{filename}\n"
        new_files_count = len(planning.suggested_files)
    
    # REORDERED: Spec-focused prompt with constraints BEFORE framework details
    return f"""
🔴 CRITICAL GENERATION TASK - READ FIRST:
==========================================

{original_request_section}

YOUR ONLY JOB: Create these {new_files_count} NEW delivery files:
{new_files_explicit}

⛔ MANDATORY CONSTRAINTS (STRICTLY ENFORCE):
=============================================
❌ DO NOT: read or analyze existing code (HelloController, GreetingService, etc.)
❌ DO NOT: edit or modify ANY existing files
❌ DO NOT: call edit_file, read_file, ls, or write_todos
❌ DO NOT: create Greeting, Greeting*, or non-delivery classes

✅ MUST: Use ONLY write_file() for each file
✅ MUST: Include complete Java code in each write_file call
✅ MUST: Stop after creating all files - no analysis needed

---

FRAMEWORK CONTEXT (For code style reference only):
{framework_prompt}

---

NEW FILES PLANNING:
{new_files_section}

DESIGN PATTERNS TO FOLLOW:
{patterns_section}

CONSTRAINTS & BEST PRACTICES:
{constraints_section}

---

NOW: Execute write_file() calls for all {new_files_count} files listed above.
"""


def flow_synthesize_code(
    state: "AgentState",
    create_code_synthesis_agent,
    get_instruction,
    analysis_model
) -> "AgentState":
    """
    Phase 4: Code Synthesis - Multi-step expert code generation
    
    Args:
        state: Current workflow state
        create_code_synthesis_agent: Factory to create synthesis agent
        get_instruction: Function to get framework instructions
        analysis_model: LLM model instance
    
    Returns:
        Updated state with code_patches
    """
    from progress_tracker import WorkProgress, FileTask, TaskStatus
    
    print("⚙️ Phase 4: Expert code generation with testability and SOLID principles...")
    
    codebase_path = state["codebase_path"]
    spec = state.get("feature_spec")
    impact = state.get("impact_analysis", {})
    structure_assessment = state.get("structure_assessment")
    framework_type = state.get("framework")
    original_feature_request = state.get("feature_request", "")  # ✓ GET ORIGINAL REQUEST

    if not spec or impact is None:
        state["errors"].append("Missing feature spec or impact analysis")
        return state

    # Initialize progress tracker - use original feature request
    feature_display = original_feature_request if original_feature_request else spec.intent_summary
    progress = WorkProgress(
        feature_name=feature_display[:50],
        feature_request=feature_display[:100],
        framework=framework_type or "Unknown"
    )
    
    # Extract files from new_files_planning if available
    if hasattr(spec, 'new_files_planning') and spec.new_files_planning:
        planning = spec.new_files_planning
        suggested_files = getattr(planning, 'suggested_files', [])
        base_package = "src/main/java/com/example/springboot"
        
        for file_spec in suggested_files[:10]:  # Track first 10 files
            file_name = getattr(file_spec, 'name', 'Unknown.java') if hasattr(file_spec, 'name') else str(file_spec)
            file_type = getattr(file_spec, 'type', 'class') if hasattr(file_spec, 'type') else 'class'
            layer = getattr(file_spec, 'layer', 'model') if hasattr(file_spec, 'layer') else 'model'
            
            filepath = f"{base_package}/{layer}/{file_name}"
            file_task = FileTask(
                name=file_name,
                filepath=filepath,
                file_type=file_type,
                layer=layer,
                status=TaskStatus.PENDING
            )
            progress.add_file_task(file_task)

    # Log what data is being consumed
    print("  📊 Data Consumption Summary:")
    print(f"    ✅ spec.intent_summary: {spec.intent_summary[:50]}...")
    print(f"    ✅ spec.affected_files: {len(spec.affected_files)} file(s)")
    print(f"    ✅ impact.files_to_modify: {len(impact.get('files_to_modify', []))} file(s)")
    print(f"    ✅ impact.patterns_to_follow: {len(impact.get('patterns_to_follow', []))} pattern(s)")
    print(f"    ✅ impact.testing_approach: {'Available' if impact.get('testing_approach') else 'N/A'}")
    print(f"    ✅ impact.constraints: {len(impact.get('constraints', []))} constraint(s)")
    
    todo_list = getattr(spec, 'todo_list', None)
    if todo_list:
        total_tasks = getattr(todo_list, 'total_tasks', 0)
        print(f"    ✅ spec.todo_list: {total_tasks} task(s)")
    else:
        print("    ⚠️  spec.todo_list: Not available")
    
    new_files_planning = getattr(spec, 'new_files_planning', None)
    if new_files_planning:
        new_files_count = len(getattr(new_files_planning, 'suggested_files', []))
        print(f"    ✅ spec.new_files_planning: {new_files_count} file(s) planned")
        
        # Display progress tracker
        print()
        progress.display_progress()
    else:
        print("    ⚠️  spec.new_files_planning: Not available")
    
    print()

    # Build refactoring note and layer guidance
    refactoring_note = ""
    if structure_assessment and not state.get("dry_run"):
        violations = structure_assessment.get("violations", [])
        refactoring_plan = structure_assessment.get("refactoring_plan")
        
        if violations or refactoring_plan:
            print("  🔧 Creating missing directory layers...")
            
            # Determine base package path for Java project
            base_package_path = "src/main/java/com/example/springboot"
            
            # Extract directories to create from violations and plan
            dirs_to_create = []
            
            # From violations: extract layer names
            for v in violations:
                if v.get("type") == "missing_layer":
                    import re
                    match = re.search(r"'(\w+)/'", v.get("message", ""))
                    if match:
                        layer_name = match.group(1)
                        layer_path = os.path.join(codebase_path, base_package_path, layer_name)
                        if layer_path not in dirs_to_create:
                            dirs_to_create.append(layer_path)
            
            # From refactoring plan: use layer names
            if refactoring_plan:
                for layer_name in refactoring_plan.get("create_layers", []):
                    layer_basename = os.path.basename(layer_name.rstrip("/"))
                    layer_path = os.path.join(codebase_path, base_package_path, layer_basename)
                    if layer_path not in dirs_to_create:
                        dirs_to_create.append(layer_path)
            
            # Create directories
            for dir_path in dirs_to_create:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"    ✓ Created: {os.path.relpath(dir_path, codebase_path)}")
                except Exception as e:
                    print(f"    ❌ Failed to create {os.path.basename(dir_path)}: {e}")
                    state["errors"].append(f"Failed to create directory: {str(e)}")
            
            # Build refactoring instruction for LLM
            if violations:
                refactoring_note = f"""
STRUCTURE REFACTORING REQUIRED:
Current compliance score: {structure_assessment.get("score", 0)}/100
Violations found: {len(violations)}

REFACTORING STRATEGY:
{refactoring_plan.get("effort_level", "medium") if refactoring_plan else "medium"} effort required

Create files in proper layers:
- controller/ directory: HTTP handlers (already created)
- service/ directory: Business logic (already created)
- repository/ directory: Data access layer (already created)
- dto/ directory: Data transfer objects (already created)
- model/ directory: Domain entities (already created)

Generate code that SEPARATES concerns into these layers.
"""
                print(f"  📝 Refactoring strategy: {len(violations)} violations to address")

    # Use files from impact analysis
    files_to_modify = impact.get("files_to_modify", spec.affected_files)
    
    # Build list of layer directories for middleware scope
    layer_dirs_to_allow = []
    if structure_assessment and not state.get("dry_run"):
        base_package_path = "src/main/java/com/example/springboot"
        layer_dirs_to_allow = [
            os.path.join(base_package_path, layer)
            for layer in ["controller", "service", "repository", "dto", "model"]
        ]
    
    # Combine files_to_modify with layer directories for middleware
    files_for_middleware = list(files_to_modify) + layer_dirs_to_allow

    # Create synthesis agent with GENERATION MODE (tool whitelist: write_file only)
    # This ensures agent focuses on creating NEW files, not modifying existing ones
    agent = create_code_synthesis_agent_generation_mode(
        codebase_path, 
        analysis_model,
        files_to_modify=files_for_middleware,
        feature_request=spec.intent_summary
    )

    # Build framework-aware prompt
    framework_prompt = ""
    if framework_type:
        try:
            framework_instruction = get_instruction(framework_type)
            if framework_instruction:
                system_prompt_text = framework_instruction.get_system_prompt()
                layer_mapping_text = "\n".join(
                    f"- {k}: {v}" for k, v in framework_instruction.get_layer_mapping().items()
                )
                file_patterns_text = "\n".join(
                    f"- {k}: {v}" for k, v in framework_instruction.get_file_patterns().items()
                )
                framework_prompt = f"""
FRAMEWORK-SPECIFIC GUIDELINES:
{system_prompt_text}

FRAMEWORK LAYER MAPPING:
{layer_mapping_text}

FILE NAMING PATTERNS:
{file_patterns_text}

"""
                print(f"  🏗️  Using {framework_type} best practices for code generation")
        except Exception:
            pass

    # Step 1: Analysis and planning
    print("  📋 Step 1: Agent analyzing code patterns and planning implementation...")
    analysis_prompt = build_analysis_prompt(
        spec.intent_summary,
        files_to_modify,
        framework_prompt,
        refactoring_note,
        original_request=original_feature_request  # ✓ PASS ORIGINAL REQUEST
    )
    
    _analysis_result = invoke_with_timeout(agent, {"input": analysis_prompt}, timeout_seconds=1800)

    # Step 2: Implementation
    print("  🛠️  Step 2: Agent implementing changes...")
    layer_guidance = build_layer_guidance(refactoring_note)
    implementation_prompt = build_implementation_prompt(
        spec.intent_summary,
        files_to_modify,
        framework_prompt,
        layer_guidance,
        spec=spec,
        impact=impact,
        original_request=original_feature_request  # ✓ PASS ORIGINAL REQUEST
    )
    
    result2 = invoke_with_timeout(agent, {"input": implementation_prompt}, timeout_seconds=600)

    # DEBUG: Log result structure with detailed info
    if result2:
        print(f"  📊 Result type: {type(result2).__name__}, keys: {list(result2.keys()) if isinstance(result2, dict) else 'N/A'}")
        
        # Check for different result formats
        if isinstance(result2, dict):
            # Check for files dict (new stream format)
            if "files" in result2:
                files_dict = result2.get("files", {})
                non_empty_files = {k: v for k, v in files_dict.items() if v and len(str(v).strip()) > 0}
                print(f"  📁 Files dict: {len(files_dict)} total, {len(non_empty_files)} non-empty")
                for file_path in list(non_empty_files.keys())[:3]:
                    content_str = str(non_empty_files[file_path])
                    print(f"     ✓ {file_path}: {len(content_str)} bytes")
            
            # Check for messages with tool calls
            if "messages" in result2:
                messages = result2.get("messages", [])
                print(f"  💬 Messages: {len(messages)} total")
                tool_call_count = 0
                for msg in messages:
                    if hasattr(msg, "tool_calls"):
                        tool_calls = getattr(msg, "tool_calls", [])
                        tool_call_count += len(tool_calls)
                        for call in tool_calls:
                            print(f"     ✓ Tool call: {call.get('name', 'unknown')}")
                if tool_call_count > 0:
                    print(f"  🔧 Total tool calls detected: {tool_call_count}")
            
            # Check for other potential result keys
            for key in ["todos", "tool_execution_log", "output", "response"]:
                if key in result2 and result2[key]:
                    value = result2[key]
                    if isinstance(value, list):
                        print(f"  📋 {key}: {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"  📋 {key}: {len(value)} keys")
                    else:
                        print(f"  📋 {key}: present")

    # Extract patches from result with progress tracking
    patches = extract_patches_from_result(result2, progress)
    log_agent_response(result2)

    if patches:
        print(f"  ✓ Generated {len(patches)} code change(s)")
        for p in patches:
            file_path = p.get('file', 'unknown')
            print(f"    - {p['tool']}: {file_path}")
        
        # Display final progress
        progress.display_progress()
        print()
        progress.display_finished_summary()
    else:
        print("  ℹ️ No code patches generated")
        print()
        progress.display_progress()

    state["code_patches"] = patches
    state["current_phase"] = "code_synthesis_complete"
    
    return state


# ==============================================================================
# MAIN FUNCTION FOR TESTING
# ==============================================================================

if __name__ == "__main__":
    import argparse
    import os
    import sys
    from pathlib import Path
    
    # Add the scripts directory to Python path to import other modules
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    
    # Import required modules
    try:
        from models.llm_setup import setup_model
        from agents.agent_factory import create_code_synthesis_agent, create_impact_analysis_agent
        from flow_parse_intent import flow_parse_intent
        from flow_analyze_impact import flow_analyze_impact
        from flow_analyze_context import AiderStyleRepoAnalyzer
        from framework_instructions import detect_framework, get_instruction
        from feature_by_request_agent_v3 import AgentState
        from typing import cast
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the correct directory and virtual environment is activated")
        sys.exit(1)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Test Flow Synthesize Code with Real LLM")
    parser.add_argument("--codebase-path", "-p", required=True, help="Path to codebase")
    parser.add_argument("--feature-request-spec", help="Path to markdown file containing feature request specification")
    parser.add_argument("--feature-request", "-f", help="Feature request text")
    parser.add_argument("--model", default=None, help="LLM model to use")
    parser.add_argument("--temperature", type=float, default=None)
    
    args = parser.parse_args()
    
    # Validate paths
    codebase_path = os.path.abspath(args.codebase_path)
    if not os.path.isdir(codebase_path):
        print(f"❌ Not a directory: {codebase_path}")
        sys.exit(1)
    
    # Setup model
    try:
        model_name, temperature, analysis_model = setup_model(
            model_override=args.model,
            temperature_override=args.temperature
        )
    except Exception as e:
        print(f"❌ Failed to setup model: {e}")
        sys.exit(1)
    
    # Load feature request
    feature_request_text = args.feature_request
    if args.feature_request_spec:
        try:
            with open(args.feature_request_spec, 'r', encoding='utf-8') as f:
                full_content = f.read().strip()
            
            # Check if there's a "## 🎯 Feature Request" section
            if "## 🎯 Feature Request" in full_content:
                sections = full_content.split("## 🎯 Feature Request")
                if len(sections) > 1:
                    feature_section = sections[1].split("---")[0].strip()
                    feature_request_text = feature_section.replace("## 🎯 Feature Request", "").strip()
                    print("✓ Loaded feature request from '## 🎯 Feature Request' section")
                else:
                    feature_request_text = full_content
            else:
                feature_request_text = full_content
                print(f"✓ Loaded entire feature request spec from: {args.feature_request_spec}")
                
        except Exception as e:
            print(f"❌ Failed to read feature request spec: {e}")
            sys.exit(1)
    
    if not feature_request_text:
        print("❌ No feature request provided")
        sys.exit(1)
    
    print("🤖 FLOW SYNTHESIZE CODE - REAL LLM TEST")
    print("=" * 50)
    print(f"📁 Codebase: {codebase_path}")
    print(f"🛠️  Model: {model_name}")
    print(f"🌡️  Temperature: {temperature}")
    print(f"🎯 Feature: {feature_request_text[:100]}{'...' if len(feature_request_text) > 100 else ''}")
    print("=" * 50)
    
    try:
        # PREDEFINED STATE - Skip phases 1-3 for faster testing
        print("🔍 Using predefined state (skipping phases 1-3)...")
        
        # Import required classes for predefined data
        from pydantic import BaseModel
        from typing import List, Optional
        
        class TodoItem(BaseModel):
            id: int
            title: str
            description: str
            phase: str
            status: str
            priority: str
            depends_on: List[int]
            files_affected: List[str]
            estimated_effort: str
            notes: str = ""

        class TodoList(BaseModel):
            feature_name: str
            feature_request: str
            framework: Optional[str]
            total_tasks: int
            completed_tasks: int
            in_progress_tasks: int
            pending_tasks: int
            todos: List[TodoItem]
            created_at: str
            updated_at: str

        class FilePlacementSuggestion(BaseModel):
            file_type: str
            relative_path: str
            filename: str
            purpose: str
            solid_principles: List[str]
            example_class_name: str
            layer: str

        class NewFilesPlanningSuggestion(BaseModel):
            suggested_files: List[FilePlacementSuggestion]
            directory_structure: Dict[str, str]
            best_practices: List[str]
            framework_conventions: List[str]
            creation_order: List[str]

        class FeatureSpec(BaseModel):
            feature_name: str
            intent_summary: str
            affected_files: List[str]
            new_files: List[str]
            modifications: List[Dict[str, Any]]
            notes: str
            todo_list: Optional[TodoList]
            new_files_planning: Optional[NewFilesPlanningSuggestion]

        # Predefined context and data
        context_summary = """
PROJECT ANALYSIS:
- Type: Spring Boot Application
- Framework: Spring Boot
- Tech Stack: Java, Spring Boot, Maven, PostgreSQL
- Total Source Files: 5
"""
        
        feature_spec = FeatureSpec(
            feature_name="Real-time Delivery Routing System",
            intent_summary="Build a real-time delivery routing and optimization system for a fleet of couriers delivering packages",
            affected_files=["src/main/java/com/example/demo/HelloController.java"],
            new_files=[
                "src/main/java/com/example/delivery/domain/entity/Delivery.java",
                "src/main/java/com/example/delivery/domain/repository/DeliveryRepository.java",
                "src/main/java/com/example/delivery/adapters/persistence/JpaDeliveryRepository.java",
                "src/main/java/com/example/delivery/application/dto/DeliveryDTO.java",
                "src/main/java/com/example/delivery/domain/entity/Courier.java",
                "src/main/java/com/example/delivery/domain/repository/CourierRepository.java",
                "src/main/java/com/example/delivery/application/dto/CourierPositionDTO.java",
                "src/main/java/com/example/delivery/domain/entity/Route.java",
                "src/main/java/com/example/delivery/domain/service/RouteOptimizer.java",
                "src/main/java/com/example/delivery/adapters/optimization/GraphHopperRouteOptimizer.java"
            ],
            modifications=[],
            notes="Hexagonal architecture with domain-driven design",
            todo_list=TodoList(
                feature_name="Real-time Delivery Routing System",
                feature_request="Build a real-time delivery routing and optimization system",
                framework="Spring Boot",
                total_tasks=30,
                completed_tasks=3,
                in_progress_tasks=0,
                pending_tasks=27,
                todos=[
                    TodoItem(id=1, title="Analyze existing codebase", description="Scan codebase structure", phase="analysis", status="completed", priority="high", depends_on=[], files_affected=[], estimated_effort="medium"),
                    TodoItem(id=2, title="Create Delivery entity", description="JPA entity for delivery", phase="generation", status="pending", priority="high", depends_on=[1], files_affected=["src/main/java/com/example/delivery/domain/entity/Delivery.java"], estimated_effort="medium"),
                    TodoItem(id=3, title="Create DeliveryRepository", description="Repository interface", phase="generation", status="pending", priority="high", depends_on=[2], files_affected=["src/main/java/com/example/delivery/domain/repository/DeliveryRepository.java"], estimated_effort="small"),
                    TodoItem(id=4, title="Create JpaDeliveryRepository", description="JPA implementation", phase="generation", status="pending", priority="high", depends_on=[3], files_affected=["src/main/java/com/example/delivery/adapters/persistence/JpaDeliveryRepository.java"], estimated_effort="medium"),
                    TodoItem(id=5, title="Create DeliveryDTO", description="DTO for API", phase="generation", status="pending", priority="high", depends_on=[4], files_affected=["src/main/java/com/example/delivery/application/dto/DeliveryDTO.java"], estimated_effort="small"),
                    TodoItem(id=6, title="Create Courier entity", description="JPA entity for courier", phase="generation", status="pending", priority="medium", depends_on=[1], files_affected=["src/main/java/com/example/delivery/domain/entity/Courier.java"], estimated_effort="medium"),
                    TodoItem(id=7, title="Create CourierRepository", description="Repository interface", phase="generation", status="pending", priority="medium", depends_on=[6], files_affected=["src/main/java/com/example/delivery/domain/repository/CourierRepository.java"], estimated_effort="small"),
                    TodoItem(id=8, title="Create CourierPositionDTO", description="DTO for position", phase="generation", status="pending", priority="medium", depends_on=[7], files_affected=["src/main/java/com/example/delivery/application/dto/CourierPositionDTO.java"], estimated_effort="small"),
                    TodoItem(id=9, title="Create Route entity", description="Entity for routes", phase="generation", status="pending", priority="medium", depends_on=[1], files_affected=["src/main/java/com/example/delivery/domain/entity/Route.java"], estimated_effort="medium"),
                    TodoItem(id=10, title="Create RouteOptimizer service", description="Business logic service", phase="generation", status="pending", priority="high", depends_on=[9], files_affected=["src/main/java/com/example/delivery/domain/service/RouteOptimizer.java"], estimated_effort="large"),
                ],
                created_at="2025-01-12T10:00:00Z",
                updated_at="2025-01-12T10:00:00Z"
            ),
            new_files_planning=NewFilesPlanningSuggestion(
                suggested_files=[
                    FilePlacementSuggestion(
                        file_type="entity",
                        relative_path="src/main/java/com/example/delivery/domain/entity",
                        filename="Delivery.java",
                        purpose="Aggregate root representing a package delivery",
                        solid_principles=["SRP: models only delivery state and domain logic", "OCP: behaviors delegated to strategy interfaces"],
                        example_class_name="Delivery",
                        layer="entity"
                    ),
                    FilePlacementSuggestion(
                        file_type="repository_port",
                        relative_path="src/main/java/com/example/delivery/domain/repository",
                        filename="DeliveryRepository.java",
                        purpose="Domain-level repository interface",
                        solid_principles=["DIP: higher layer depends on this interface, not implementation"],
                        example_class_name="Delivery",
                        layer="repository_port"
                    ),
                    FilePlacementSuggestion(
                        file_type="jpa_impl",
                        relative_path="src/main/java/com/example/delivery/adapters/persistence",
                        filename="JpaDeliveryRepository.java",
                        purpose="Spring Data JpaRepository implementation",
                        solid_principles=["SRP: persistence responsibility only"],
                        example_class_name="Delivery",
                        layer="jpa_impl"
                    ),
                    FilePlacementSuggestion(
                        file_type="dto",
                        relative_path="src/main/java/com/example/delivery/application/dto",
                        filename="DeliveryDTO.java",
                        purpose="DTO for REST API and messaging",
                        solid_principles=["ISP: small DTOs for specific API surfaces"],
                        example_class_name="Delivery",
                        layer="dto"
                    ),
                    FilePlacementSuggestion(
                        file_type="entity",
                        relative_path="src/main/java/com/example/delivery/domain/entity",
                        filename="Courier.java",
                        purpose="Represents courier profile and status",
                        solid_principles=["SRP: courier state only"],
                        example_class_name="Courier",
                        layer="entity"
                    ),
                    FilePlacementSuggestion(
                        file_type="repository_port",
                        relative_path="src/main/java/com/example/delivery/domain/repository",
                        filename="CourierRepository.java",
                        purpose="Domain-level repository interface",
                        solid_principles=["DIP: higher layer depends on this interface, not implementation"],
                        example_class_name="Courier",
                        layer="repository_port"
                    ),
                    FilePlacementSuggestion(
                        file_type="dto",
                        relative_path="src/main/java/com/example/delivery/application/dto",
                        filename="CourierPositionDTO.java",
                        purpose="DTO for courier position updates",
                        solid_principles=["ISP: small DTOs for specific API surfaces"],
                        example_class_name="CourierPositionDTO",
                        layer="dto"
                    ),
                    FilePlacementSuggestion(
                        file_type="entity",
                        relative_path="src/main/java/com/example/delivery/domain/entity",
                        filename="Route.java",
                        purpose="Represents optimized delivery route",
                        solid_principles=["SRP: route state only"],
                        example_class_name="Route",
                        layer="entity"
                    ),
                    FilePlacementSuggestion(
                        file_type="service_port",
                        relative_path="src/main/java/com/example/delivery/domain/service",
                        filename="RouteOptimizer.java",
                        purpose="Domain service interface for route optimization",
                        solid_principles=["DIP: higher layer depends on this interface, not implementation"],
                        example_class_name="RouteOptimizer",
                        layer="service_port"
                    ),
                    FilePlacementSuggestion(
                        file_type="service_impl",
                        relative_path="src/main/java/com/example/delivery/adapters/optimization",
                        filename="GraphHopperRouteOptimizer.java",
                        purpose="GraphHopper implementation of route optimization",
                        solid_principles=["SRP: optimization responsibility only"],
                        example_class_name="GraphHopperRouteOptimizer",
                        layer="service_impl"
                    )
                ],
                directory_structure={
                    "domain": "Business logic and domain entities",
                    "application": "Application services and DTOs",
                    "adapters": "Infrastructure implementations"
                },
                best_practices=[
                    "Use hexagonal architecture",
                    "Apply SOLID principles",
                    "Separate domain from infrastructure"
                ],
                framework_conventions=[
                    "Spring Boot naming conventions",
                    "JPA entity annotations",
                    "REST controller patterns"
                ],
                creation_order=[
                    "entity",
                    "repository_port",
                    "jpa_impl",
                    "dto",
                    "service_port",
                    "service_impl",
                    "controller"
                ]
            )
        )
        
        impact_analysis = {
            "files_to_modify": ["src/main/java/com/example/demo/HelloController.java"],
            "patterns_to_follow": [
                "Hexagonal Architecture",
                "Domain-Driven Design",
                "SOLID Principles",
                "Repository Pattern",
                "DTO Pattern"
            ],
            "testing_approach": "Unit tests with JUnit and Mockito, Integration tests with TestContainers",
            "constraints": [
                "Use Spring Boot 3.x with Jakarta EE (jakarta.persistence.*)",
                "PostgreSQL with PostGIS for spatial data",
                "RESTful API design",
                "Hexagonal architecture",
                "SOLID principles compliance",
                "Use jakarta.persistence.* imports NOT javax.persistence.*"
            ]
        }
        
        print("  ✓ Predefined state loaded")
        
        # PHASE 4: Code synthesis (the main test)
        print("⚙️ Phase 4: Expert code generation with real LLM...")
        
        synthesis_state = {
            "codebase_path": codebase_path,
            "feature_request": feature_request_text,
            "context_analysis": context_summary,
            "full_analysis": {},  # Empty for predefined
            "feature_spec": feature_spec,
            "impact_analysis": impact_analysis,
            "structure_assessment": {
                "score": 100.0,
                "violations": [],
                "production_ready": True,
                "refactoring_plan": None
            },
            "framework": "Spring Boot",
            "errors": [],
            "dry_run": False,
            "current_phase": "impact_analysis_complete"
        }
        
        # Run the actual synthesis flow
        final_state = flow_synthesize_code(
            cast(AgentState, synthesis_state),
            create_code_synthesis_agent,
            get_instruction,
            analysis_model
        )
        
        # Report results
        print("\n" + "=" * 50)
        print("🎉 SYNTHESIS COMPLETE")
        print("=" * 50)
        
        code_patches = final_state.get('code_patches', [])
        print(f"🔧 Code Patches Generated: {len(code_patches) if code_patches else 0}")
        
        if code_patches:
            print("\n📄 Generated Files:")
            for i, patch in enumerate(code_patches, 1):
                file_path = patch.get('file', 'unknown')
                tool = patch.get('tool', 'unknown')
                print(f"  {i}. {tool}: {file_path}")
                
                # Show content preview for write_file patches
                if tool == 'write_file' and 'content' in patch.get('args', {}):
                    content = patch['args']['content']
                    lines = content.split('\n')
                    print(f"     � {len(lines)} lines, {len(content)} chars")
                    if len(lines) <= 10:
                        print(f"     Content: {content[:200]}{'...' if len(content) > 200 else ''}")
                    else:
                        print(f"     Preview: {lines[0][:100]}...")
        else:
            print("ℹ️ No code patches were generated")
        
        errors = final_state.get('errors', [])
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors:
                print(f"  - {error}")
        
        print(f"\n📊 Final Phase: {final_state.get('current_phase', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
