"""
PHASE 5: EXECUTION - Apply Generated Code Changes
=================================================

Responsible for:
- Applying code patches to files
- Human-in-the-loop approval (optional)
- Dry-run mode support
- Verification and error handling
"""

import os
from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from feature_by_request_agent_v3 import AgentState


def validate_patch(patch: Dict[str, Any]) -> bool:
    """Validate that a patch has all required fields"""
    tool_name = patch.get("tool")
    args = patch.get("args", {})
    
    if tool_name == "write_file":
        file_path = args.get("path") or args.get("file")
        content = args.get("content", "")
        return bool(file_path and content and len(content.strip()) > 0)
    
    elif tool_name == "edit_file":
        file_path = args.get("path") or args.get("file")
        old_string = args.get("oldString", "")
        new_string = args.get("newString", "")
        return bool(file_path and old_string and new_string)
    
    return False


def apply_write_file(file_path: str, content: str) -> tuple[bool, str]:
    """
    Apply a write_file patch
    
    Returns:
        (success, message) tuple
    """
    try:
        # Ensure parent directories exist
        parent_dir = os.path.dirname(file_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        # Write the file
        with open(file_path, "w") as f:
            f.write(content)
        
        return True, f"✓ Created: {file_path}"
    
    except Exception as e:
        return False, f"❌ Failed to create {file_path}: {str(e)}"


def apply_edit_file(file_path: str, old_string: str, new_string: str) -> tuple[bool, str]:
    """
    Apply an edit_file patch
    
    Returns:
        (success, message) tuple
    """
    try:
        if not os.path.isfile(file_path):
            return False, f"⚠️  Edit target missing: {file_path}"
        
        # Read file
        with open(file_path, "r") as f:
            current_content = f.read()
        
        # Check if old string exists
        if old_string not in current_content:
            return False, f"⚠️  Old string not found in: {file_path}"
        
        # Apply changes
        new_content = current_content.replace(old_string, new_string, 1)
        
        with open(file_path, "w") as f:
            f.write(new_content)
        
        return True, f"✓ Modified: {file_path}"
    
    except Exception as e:
        return False, f"❌ Error modifying {file_path}: {str(e)}"


def apply_patches_dry_run(patches: List[Dict[str, Any]]) -> List[str]:
    """Show what would be done without actually applying patches"""
    applied = []
    for patch in patches:
        file_path = patch.get("file", "unknown")
        tool_name = patch.get("tool")
        print(f"    [DRY] {tool_name}: {file_path}")
        applied.append(file_path)
    return applied


def apply_patches_execute(patches: List[Dict[str, Any]]) -> tuple[List[str], List[str], List[str]]:
    """
    Actually apply patches to files
    
    Returns:
        (patches_applied, files_created, errors) tuples
    """
    patches_applied = []
    files_created = []
    errors = []
    
    for patch in patches:
        # Validate patch
        if not validate_patch(patch):
            file_path = patch.get("file", "unknown")
            errors.append(f"Invalid patch for {file_path}")
            continue
        
        tool_name = patch.get("tool")
        args = patch.get("args", {})
        file_path = args.get("path") or args.get("file")
        
        if tool_name == "write_file":
            content = args.get("content", "")
            success, message = apply_write_file(file_path, content)
            print(f"    {message}")
            
            if success:
                patches_applied.append(file_path)
                files_created.append(file_path)
            else:
                errors.append(message)
        
        elif tool_name == "edit_file":
            old_string = args.get("oldString", "")
            new_string = args.get("newString", "")
            success, message = apply_edit_file(file_path, old_string, new_string)
            print(f"    {message}")
            
            if success:
                patches_applied.append(file_path)
            else:
                errors.append(message)
    
    return patches_applied, files_created, errors


def flow_execute_changes(state: "AgentState", enable_human_loop: bool = False) -> "AgentState":
    """
    Phase 5: Execute code changes with optional human approval
    
    Args:
        state: Current workflow state
        enable_human_loop: Whether to require human approval before applying changes
    
    Returns:
        Updated state with execution_results
    """
    print("🚀 Phase 5: Execution & Verification...")

    patches = state.get("code_patches", [])
    dry_run = state.get("dry_run", False)

    # Human-in-the-loop: Require approval for actual code changes
    if not dry_run and enable_human_loop and patches:
        print("  ⚠️  Human approval required for code changes")
        state["human_approval_required"] = True

        # In a real implementation, you would interrupt here
        # For now, we'll proceed automatically
        # Uncomment below to enable actual interrupt:
        # from langgraph.types import interrupt
        # user_decision = interrupt({
        #     "message": f"About to apply {len(patches)} code changes. Approve?",
        #     "patches": patches,
        #     "options": ["approve", "reject", "edit"]
        # })

    if not patches:
        print("  ℹ️ No patches to apply")
        state["execution_results"] = {
            "patches_applied": [],
            "verification_status": "no_patches"
        }
        state["current_phase"] = "execution_complete"
        return state

    mode = "DRY RUN" if dry_run else "EXECUTE"
    print(f"  ℹ️ {mode}: Applying {len(patches)} patch(es)...")

    # Apply patches
    if dry_run:
        patches_applied = apply_patches_dry_run(patches)
        results = {
            "patches_applied": patches_applied,
            "verification_status": "dry_run_completed",
            "errors": [],
            "files_created": []
        }
    else:
        patches_applied, files_created, errors = apply_patches_execute(patches)
        results = {
            "patches_applied": patches_applied,
            "verification_status": "completed",
            "errors": errors,
            "files_created": files_created
        }

    state["execution_results"] = results
    state["current_phase"] = "execution_complete"
    
    return state
