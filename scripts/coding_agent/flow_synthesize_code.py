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
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from feature_by_request_agent_v3 import AgentState


def invoke_with_timeout(agent, input_data, timeout_seconds=30):
    """Invoke agent with timeout protection"""
    import threading
    
    result_container = {"status": "pending", "data": None, "error": None}
    
    def worker():
        try:
            result_container["data"] = agent.invoke(input_data)
            result_container["status"] = "success"
        except Exception as e:
            result_container["status"] = "error"
            result_container["error"] = str(e)
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if result_container["status"] == "pending":
        print(f"  ⚠️  Agent invoke timeout after {timeout_seconds}s - switching to fast mode")
        return None
    
    if result_container["status"] == "error":
        raise Exception(result_container["error"])
    
    return result_container["data"]


def _extract_patch_from_call(call: Dict[str, Any], progress: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """Extract single patch from LangChain-style tool call"""
    if call.get("name") not in ["write_file", "edit_file"]:
        return None
    
    tool_args = call.get("args", {})
    tool_name = call.get("name")
    file_path = tool_args.get("path") or tool_args.get("file")
    
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


def build_analysis_prompt(spec_intent: str, files_to_modify: List[str], framework_prompt: str, refactoring_note: str) -> str:
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


def build_implementation_prompt(spec_intent: str, files_to_modify: List[str], framework_prompt: str, layer_guidance: str, spec: Optional[Any] = None, impact: Optional[Dict[str, Any]] = None) -> str:
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
    
    return f"""
FEATURE: {spec_intent}
FILES: {', '.join(files_to_modify[:3])}

{framework_prompt}

{layer_guidance}{file_creation_guide}{new_files_section}{patterns_section}{testing_section}{constraints_section}{todos_section}

STEP 2: IMPLEMENTATION - GENERATE CODE NOW

🚀 YOUR TASK: Create the files listed above using write_file() ONLY.

CRITICAL REQUIREMENTS:
✅ Use ONLY write_file() tool for creating files
✅ DO NOT use edit_file, ls, read_file, write_todos, or grep
✅ Every write_file() call MUST have BOTH path and content parameters
✅ DO NOT make calls with empty parameters
✅ Create ONE file per write_file() call
✅ Stop after creating all files - DO NOT analyze or loop

TEMPLATE - USE THIS EXACT FORMAT FOR EACH FILE:

write_file(
    path="src/main/java/com/example/springboot/[LAYER]/[FileName].java",
    content="[Complete valid Java code]"
)

PRIORITY FILES TO CREATE (IN THIS ORDER):
{file_creation_guide}{new_files_section}

NOW CREATE ALL FILES. START IMMEDIATELY WITH write_file CALLS ONLY.
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

    if not spec or not impact:
        state["errors"].append("Missing feature spec or impact analysis")
        return state

    # Initialize progress tracker
    feature_request = spec.intent_summary if spec else "Feature Development"
    progress = WorkProgress(
        feature_name=spec.intent_summary[:50] if spec else "Feature",
        feature_request=feature_request[:100],
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

    # Create synthesis agent
    agent = create_code_synthesis_agent(
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
        refactoring_note
    )
    
    _analysis_result = invoke_with_timeout(agent, {"input": analysis_prompt}, timeout_seconds=180)

    # Step 2: Implementation
    print("  🛠️  Step 2: Agent implementing changes...")
    layer_guidance = build_layer_guidance(refactoring_note)
    implementation_prompt = build_implementation_prompt(
        spec.intent_summary,
        files_to_modify,
        framework_prompt,
        layer_guidance,
        spec=spec,
        impact=impact
    )
    
    result2 = invoke_with_timeout(agent, {"input": implementation_prompt}, timeout_seconds=240)

    # DEBUG: Log result structure
    if result2:
        print(f"  📊 Result type: {type(result2).__name__}, keys: {list(result2.keys()) if isinstance(result2, dict) else 'N/A'}")
        
        # DEBUG: If there's a 'files' key, show what's in it
        if isinstance(result2, dict) and "files" in result2:
            files_dict = result2.get("files", {})
            print(f"  📁 Files dict size: {len(files_dict)}")
            for file_path in list(files_dict.keys())[:3]:
                content_preview = str(files_dict[file_path])[:100] if files_dict[file_path] else "(empty)"
                print(f"     - {file_path}: {content_preview}...")

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
