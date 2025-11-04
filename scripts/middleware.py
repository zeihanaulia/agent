"""
MIDDLEWARE & GUARDRAILS - Custom LangChain Agent Middleware
============================================================

Three composable middleware components untuk Phase 4 agent:
1. IntentReminderMiddleware - Inject feature_request ke setiap model call
2. FileScopeGuardrail - Validate file edits stay within allowed scope
3. ToolCallValidationMiddleware - Block unauthorized file operations at tool level

Based on LangChain AgentMiddleware API:
https://docs.langchain.com/oss/python/langchain/middleware
"""

import os
import re
from typing import Any, Callable, List, Optional, Set
from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.agents.middleware import hook_config
from langgraph.runtime import Runtime
from langchain_core.messages import ToolMessage, AIMessage, SystemMessage


class IntentReminderMiddleware(AgentMiddleware):
    """
    Middleware: Inject user feature_request at the beginning of every model call.

    Purpose: Prevent agent from deviating from user intent (e.g., creating random files).

    Hook: before_model
    Timing: Runs BEFORE each LLM call, injecting a system message with:
      - Primary objective (feature request)
      - Allowed files to modify
      - Constraints (no new files, no refactoring, etc.)
    """

    def __init__(self, feature_request: str, affected_files: List[str]):
        """
        Args:
            feature_request: User's feature request description
            affected_files: List of file paths that are allowed to be modified
        """
        super().__init__()
        self.feature_request = feature_request
        self.affected_files = affected_files

    def before_model(self, state: AgentState, runtime: Runtime) -> Optional[dict[str, Any]]:
        """
        Inject reminder before model call.

        Returns:
            dict with modified messages, or None if no changes
        """
        messages = state.get("messages", [])

        # Check if reminder already exists (avoid duplicates on multiple invocations)
        has_reminder = any(
            "🎯 PRIMARY OBJECTIVE" in str(getattr(m, "content", ""))
            for m in messages
        )

        if has_reminder:
            return None  # Already injected, skip

        # Create reminder message with clear constraints
        files_list = "\n".join(f"  • {f}" for f in self.affected_files) if self.affected_files else "  (None specified)"

        reminder_content = f"""🎯 PRIMARY OBJECTIVE (CRITICAL - Do NOT deviate):
Implement this EXACT feature: "{self.feature_request}"

📁 ALLOWED FILES TO MODIFY:
{files_list}

⚠️ STRICT CONSTRAINTS:
1. DO NOT create new files (unless explicitly mentioned in feature request)
2. DO NOT create unrelated classes/services (e.g., GreetingService.java, RandomClass.py)
3. DO NOT refactor code outside feature scope
4. DO NOT modify files not in the allowed list above
5. DO NOT add new dependencies
6. Only use existing libraries in pom.xml/package.json/requirements.txt

🔍 FOCUS AREAS:
• Understand the existing patterns in allowed files
• Follow the same coding style and conventions
• Ensure implementation is testable and production-ready
• Keep changes minimal and focused

If you cannot implement the feature within these constraints, STOP and explain why."""

        reminder = SystemMessage(content=reminder_content)

        # Prepend reminder to messages
        new_messages = [reminder] + messages

        return {"messages": new_messages}


class FileScopeGuardrail(AgentMiddleware):
    """
    Middleware: Validate that model output only mentions allowed files.

    Purpose: Prevent agent from planning edits to files outside the scope.

    Hook: after_model
    Timing: Runs AFTER model responds, inspecting content for file paths.
            If unauthorized files detected, interrupts execution and returns error.

    Configuration:
    - soft_mode: If True, logs violations but doesn't block (warnings only)
    - verbose: If True, prints detailed guardrail logs for debugging
    """

    def __init__(self, allowed_files: List[str], soft_mode: bool = False, verbose: bool = False):
        """
        Args:
            allowed_files: List of file paths agent is allowed to modify
            soft_mode: If True, warn but don't block (useful for debugging)
            verbose: If True, print detailed logs
        """
        super().__init__()
        self.allowed_files = set(allowed_files)
        self.soft_mode = soft_mode
        self.verbose = verbose

    def _normalize_path(self, path: str) -> str:
        """Normalize a path for comparison (lowercase, forward slashes)."""
        return os.path.normpath(path).replace("\\", "/").lower()

    def _is_allowed(self, file_mention: str) -> bool:
        """
        Check if a mentioned file is in the allowed list.
        
        Supports:
        - Exact matches: "/path/to/HelloController.java"
        - Suffix matches: "HelloController.java", "springboot/HelloController.java"
        - Relative paths: "src/main/java/..." or just "HelloController.java"
        """
        normalized_mention = self._normalize_path(file_mention)

        for allowed in self.allowed_files:
            normalized_allowed = self._normalize_path(allowed)
            
            # Exact match
            if normalized_mention == normalized_allowed:
                return True
            
            # Check if mention is a suffix of allowed path
            # e.g., "HelloController.java" matches "/path/to/HelloController.java"
            if normalized_allowed.endswith(normalized_mention) or normalized_allowed.endswith("/" + normalized_mention):
                return True
            
            # Check if mention is a partial path match
            # e.g., "springboot/HelloController.java" matches "/path/to/springboot/HelloController.java"
            if "/" + normalized_mention in "/" + normalized_allowed:
                return True
            
            # Check basename match (for simple mentions like "HelloController.java")
            mention_basename = os.path.basename(normalized_mention)
            allowed_basename = os.path.basename(normalized_allowed)
            if mention_basename == allowed_basename and mention_basename:
                return True

        return False

    @hook_config(can_jump_to=["end"])
    def after_model(self, state: AgentState, runtime: Runtime) -> Optional[dict[str, Any]]:
        """
        Validate file mentions in model output.

        Returns:
            dict with blocking message if violations (hard mode), or None
        """
        messages = state.get("messages", [])
        if not messages:
            return None

        # Get last message from model
        last_msg = messages[-1]
        content = str(getattr(last_msg, "content", ""))

        # Skip if this is already a tool message
        if getattr(last_msg, "type", None) == "tool" or isinstance(last_msg, ToolMessage):
            return None

        # Extract file paths using regex patterns
        # Match: src/Main.java, controllers/UserController.java, ./file.py, etc.
        file_patterns = (
            r'(?:src/|\.?/)?[\w\-./]*\.(?:java|py|ts|tsx|js|go|rb|kt|scala|rs)',
            r'[\w\-./]*(?:pom|gradle|package|requirements|setup|\.env|\.yml|\.yaml)',
        )

        mentioned_files = set()
        for pattern in file_patterns:
            mentions = re.findall(pattern, content)
            mentioned_files.update(mentions)

        # Check for violations (only those not in allowed list)
        violations = {f for f in mentioned_files if not self._is_allowed(f)}

        if violations:
            violation_list = "\n".join(f"  ❌ {f}" for f in sorted(violations))
            allowed_list = "\n".join(f"  ✓ {f}" for f in sorted(self.allowed_files)[:10])

            log_msg = (
                f"\n🚫 GUARDRAIL ALERT — {len(violations)} file(s) outside scope detected:\n"
                f"{violation_list}\n"
                f"\nAllowed files (showing first 10):\n{allowed_list}"
            )

            if self.verbose:
                print(log_msg)

            if self.soft_mode:
                # Warning mode: don't block, just log
                print("⚠️  SOFT MODE: Violations detected but execution continues")
                return None
            else:
                # Hard mode: block execution
                block_msg = AIMessage(
                    content=f"""🛑 GUARDRAIL VIOLATION - EXECUTION BLOCKED

You attempted to modify files OUTSIDE the allowed scope:
{violation_list}

Allowed files (first 10):
{allowed_list}

Please ONLY modify files from the allowed list above.
If you need to modify additional files, request approval from the user."""
                )

                print("🛑 HARD MODE: Blocking execution")
                return {
                    "messages": messages + [block_msg],
                    "jump_to": "end"  # Stop agent execution
                }

        if self.verbose:
            print(f"✅ Guardrail check passed: {len(mentioned_files)} file(s) mentioned, all allowed")

        return None


class ToolCallValidationMiddleware(AgentMiddleware):
    """
    Middleware: Validate file operations at the tool call level.

    Purpose: Prevent write_file/edit_file tool calls to unauthorized paths.

    Hook: wrap_tool_call
    Timing: Runs AROUND each tool call, before execution.
            Intercepts file-modifying tools and validates paths.

    Configuration:
    - soft_mode: If True, logs violations but allows tool to execute
    - verbose: If True, prints detailed validation logs
    
    FIX for guardrail blocking issue:
    - Now accepts both individual files AND allowed directories
    - Allows new files to be created within allowed directories
    - Properly validates write_file calls for files that don't exist yet
    """

    def __init__(self, allowed_files: List[str], codebase_root: str, allowed_dirs: Optional[List[str]] = None, 
                 soft_mode: bool = False, verbose: bool = False):
        """
        Args:
            allowed_files: List of relative/absolute file paths allowed
            codebase_root: Absolute path to codebase root directory
            allowed_dirs: List of directories where new files can be created (NEW FIX)
            soft_mode: If True, log violations but don't block
            verbose: If True, print detailed logs
        """
        super().__init__()
        self.allowed_files = set(allowed_files) if allowed_files else set()
        self.allowed_dirs = set(allowed_dirs) if allowed_dirs else set()  # NEW FIX
        self.codebase_root = os.path.abspath(codebase_root)
        self.soft_mode = soft_mode
        self.verbose = verbose

        # Pre-compute absolute paths for efficiency
        self.allowed_abs_paths = self._normalize_paths(list(self.allowed_files))
        self.allowed_abs_dirs = self._normalize_paths(list(self.allowed_dirs))  # NEW FIX

    def _normalize_paths(self, paths: List[str]) -> Set[str]:
        """Normalize relative paths to absolute paths."""
        abs_paths = set()
        for path in paths:
            abs_path = os.path.abspath(os.path.join(self.codebase_root, path))
            abs_paths.add(abs_path)
        return abs_paths

    def _is_allowed(self, abs_path: str) -> bool:
        """
        Check if a path is allowed.

        Supports:
        - Exact matches on individual files
        - Files within allowed directories (NEW FIX for new file creation)
        - Sibling files in same directory as allowed file (NEW FIX)
        """
        abs_path = os.path.abspath(abs_path)

        # Direct match on individual files
        if abs_path in self.allowed_abs_paths:
            return True

        # NEW FIX: Check if path is within an allowed directory
        for allowed_dir in self.allowed_abs_dirs:
            if os.path.isdir(allowed_dir):
                # Allow files directly in directory or subdirectories
                if abs_path.startswith(allowed_dir + os.sep) or os.path.dirname(abs_path) == allowed_dir:
                    return True

        # Check if path is within an allowed directory (legacy check)
        for allowed in self.allowed_abs_paths:
            if os.path.isdir(allowed) and abs_path.startswith(allowed + os.sep):
                return True

        # Check if sibling in an allowed directory
        parent_dir = os.path.dirname(abs_path)
        for allowed in self.allowed_abs_paths:
            allowed_dir = os.path.dirname(allowed)
            if parent_dir == allowed_dir:
                return True

        return False

    def wrap_tool_call(
        self,
        request: Any,
        handler: Callable
    ) -> ToolMessage:
        """
        Intercept and validate tool calls.

        Returns:
            ToolMessage with result or error
        """
        try:
            # FIX: Better extraction of tool call information from request
            tool_call = None
            tool_name = ""
            args = {}
            
            # Try different ways to extract tool call based on LangChain structure
            if hasattr(request, 'tool_call'):
                tool_call = request.tool_call
            elif hasattr(request, 'tool_calls') and request.tool_calls:
                tool_call = request.tool_calls[0]
            
            if tool_call:
                # Extract tool name
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get("name", "") or tool_call.get("function", {}).get("name", "")
                    # Extract arguments
                    args = tool_call.get("arguments", {}) or tool_call.get("function", {}).get("arguments", {})
                else:
                    # If tool_call is an object
                    tool_name = getattr(tool_call, "name", "") or getattr(tool_call, "function", {}).get("name", "")
                    args = getattr(tool_call, "arguments", {}) or getattr(tool_call, "function", {}).get("arguments", {})

            # Parse arguments if they're JSON string
            if isinstance(args, str):
                import json
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            # Only validate file-modifying tools
            if tool_name not in ["write_file", "edit_file", "create_file"]:
                # For other tools, pass through without validation
                return handler(request)

            # Extract file path - try multiple possible keys
            file_path = ""
            if isinstance(args, dict):
                file_path = args.get("path") or args.get("filePath") or args.get("file_path") or ""

            # FIX: Skip validation if file_path is empty (agent made mistake)
            if not file_path or not file_path.strip():
                if self.verbose:
                    print(f"⚠️  Tool validation skipped: {tool_name} has empty file path")
                # Allow execution - agent needs to fix their tool call
                return handler(request)

            # Normalize to absolute path
            abs_path = os.path.abspath(os.path.join(self.codebase_root, file_path))

            # Check against allowed paths
            if not self._is_allowed(abs_path):
                error_msg = (
                    f"❌ BLOCKED: File '{file_path}' is NOT in the allowed list.\n"
                    f"Tool: {tool_name}\n"
                    f"Absolute path: {abs_path}\n"
                    f"\n"
                    f"Allowed files:\n"
                    + "\n".join(f"  • {f}" for f in sorted(self.allowed_files)[:5])
                    + "\n\nAllowed directories:\n"
                    + "\n".join(f"  • {d}" for d in sorted(self.allowed_dirs)[:5])
                )

                if self.verbose:
                    print(error_msg)

                if self.soft_mode:
                    # Warning mode: log but allow execution
                    print("⚠️  SOFT MODE: Tool call allowed despite violation")
                    return handler(request)
                else:
                    # Hard mode: block execution
                    print("🛑 HARD MODE: Blocking tool call")
                    tool_id = tool_call.get("id", "unknown") if isinstance(tool_call, dict) else getattr(tool_call, "id", "unknown")
                    return ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_id
                    )

            # Path is allowed, execute normally
            if self.verbose:
                print(f"✅ Tool validation passed: {tool_name}({file_path})")

            return handler(request)

        except Exception as e:
            # If anything goes wrong, safe-fail with error message
            tool_call_id = "unknown"
            if hasattr(request, 'tool_call'):
                tool_call_id = getattr(request.tool_call, "id", "unknown") if not isinstance(request.tool_call, dict) else request.tool_call.get("id", "unknown")
            elif hasattr(request, 'tool_calls') and request.tool_calls:
                tc = request.tool_calls[0]
                tool_call_id = getattr(tc, "id", "unknown") if not isinstance(tc, dict) else tc.get("id", "unknown")

            error_msg = f"❌ Tool validation error: {str(e)}"
            if self.verbose:
                print(error_msg)
                import traceback
                traceback.print_exc()
            return ToolMessage(
                content=error_msg,
                tool_call_id=tool_call_id
            )


class TraceLoggingMiddleware(AgentMiddleware):
    """
    Middleware: Simple trace logger for model and tool activity.

    Purpose: Log every tool call and model call for debugging and monitoring.

    Hook: before_model, wrap_tool_call
    Timing: Logs before model calls and around tool calls
    """

    def before_model(self, state: AgentState, runtime: Runtime) -> Optional[dict[str, Any]]:
        """Log before model calls."""
        messages = state.get("messages", [])
        print(f"🧩 [MODEL] About to call model with {len(messages)} messages")
        return None

    def wrap_tool_call(
        self,
        request: Any,
        handler: Callable
    ) -> ToolMessage:
        """Log tool calls."""
        # Extract tool call information
        tool_call = getattr(request, 'tool_call', {})
        if hasattr(request, 'tool_calls') and request.tool_calls:
            tool_call = request.tool_calls[0]

        tool_name = tool_call.get("name", "") or tool_call.get("function", {}).get("name", "")
        args = tool_call.get("arguments", {}) or tool_call.get("function", {}).get("arguments", {})

        print(f"🛠️ [TOOL] {tool_name}({args})")

        # Execute the tool
        result = handler(request)

        print(f"✅ [TOOL] {tool_name} completed")
        return result


class ComplianceMiddleware(AgentMiddleware):
    """
    Optional: Additional middleware for compliance checks.

    Can be extended for:
    - Dependency version validation
    - Code quality checks
    - Security scanning
    - Test coverage requirements
    """

    def __init__(self, config: Optional[dict] = None):
        super().__init__()
        self.config = config or {}

    def after_model(self, state: AgentState, runtime: Runtime) -> Optional[dict[str, Any]]:
        """
        Optional compliance validation.

        Stub for future enhancement.
        """
        # TODO: Implement compliance checks
        return None


# Utility functions for middleware composition

def _normalize_file_paths(
    affected_files: List[str],
    codebase_root: str,
    expand_scope: bool = True
) -> tuple[List[str], List[str]]:
    """
    Normalize and expand file paths for guardrail scope.
    
    FIX for guardrail blocking issue:
    - Return BOTH individual files AND their parent directories
    - Allows new files to be created within allowed directories
    - Previously only returned files, which blocked new file creation

    Args:
        affected_files: Relative or absolute file paths from Phase 3 analysis
        codebase_root: Absolute path to codebase root
        expand_scope: If True, auto-include sibling files in same directories

    Returns:
        Tuple of (normalized_files, allowed_directories)
        - normalized_files: List of individual file paths
        - allowed_directories: List of directory paths where new files are allowed
    """
    normalized_files = set()
    allowed_directories = set()  # NEW: Track directories for new file creation

    for f in affected_files:
        if not f or f == "TBD - to be determined by impact analysis":
            continue

        # Normalize to absolute path
        if os.path.isabs(f):
            abs_path = os.path.abspath(f)
        else:
            abs_path = os.path.abspath(os.path.join(codebase_root, f))

        if os.path.exists(abs_path):
            normalized_files.add(abs_path)
            
            # FIX: Also extract parent directory to allow sibling files
            parent_dir = os.path.dirname(abs_path)
            if os.path.isdir(parent_dir):
                allowed_directories.add(parent_dir)

            # Optional: expand scope to include sibling files in same directories
            if expand_scope:
                dir_name = os.path.basename(parent_dir).lower()
                # Always expand scope if it's a code directory
                if any(x in dir_name for x in ["controller", "service", "model", "api", "handler", "component", "java", "src"]):
                    try:
                        for sibling in os.listdir(parent_dir):
                            if sibling.startswith('.'):
                                continue
                            sibling_path = os.path.join(parent_dir, sibling)
                            # Include other code files in same directory
                            if sibling.endswith((".java", ".py", ".ts", ".tsx", ".js", ".go", ".rb", ".kt")):
                                normalized_files.add(sibling_path)
                    except (PermissionError, OSError):
                        pass  # Skip if can't list directory
        else:
            # FIX: Even if file doesn't exist, extract its parent directory
            # This allows new files to be created in the same directory
            parent_dir = os.path.dirname(abs_path)
            if os.path.isdir(parent_dir):
                allowed_directories.add(parent_dir)

    return sorted(normalized_files), sorted(allowed_directories)


def create_phase4_middleware(
    feature_request: str,
    affected_files: List[str],
    codebase_root: str,
    enable_guardrail: bool = True,
    expand_scope: bool = True
) -> List[AgentMiddleware]:
    """
    Factory function to create all Phase 4 middleware.

    Args:
        feature_request: User's feature description
        affected_files: List of files allowed to modify (from Phase 3)
        codebase_root: Path to codebase root
        enable_guardrail: If False, disable file scope guardrail (debug mode)
        expand_scope: If True, auto-include sibling files in same directories

    Returns:
        List of middleware instances for Phase 4 agent

    Implementation Notes:
    - Normalizes all file paths to absolute, deduplicated set
    - FIX: Now extracts both files AND directories for proper validation
    - Optionally expands scope to sibling files (e.g., all files in a controller directory)
    - Can be disabled entirely for debugging via enable_guardrail=False
    - Logs guardrail scope for transparency
    """
    # Fallback: ensure we have at least some scope
    if not affected_files or all(f == "TBD - to be determined by impact analysis" for f in affected_files):
        affected_files = [os.path.join(codebase_root, "src")]  # Fallback to src/ directory

    # FIX: _normalize_file_paths now returns tuple of (files, directories)
    normalized_files, allowed_directories = _normalize_file_paths(affected_files, codebase_root, expand_scope=expand_scope)

    # Log guardrail scope for debugging
    print("✅ Guardrail Scope Configuration:")
    print(f"  📄 Allowed files: {len(normalized_files)} file(s)")
    for f in normalized_files[:3]:
        print(f"    • {f}")
    if len(normalized_files) > 3:
        print(f"    ... and {len(normalized_files) - 3} more")
    
    print(f"  📁 Allowed directories: {len(allowed_directories)} dir(s)")
    for d in allowed_directories[:3]:
        print(f"    • {d}")
    if len(allowed_directories) > 3:
        print(f"    ... and {len(allowed_directories) - 3} more")

    # Base middleware (always applied)
    middleware = [
        TraceLoggingMiddleware(),
        IntentReminderMiddleware(feature_request, normalized_files),
    ]

    # Conditional: add guardrails only if enabled
    if enable_guardrail:
        middleware.extend([
            FileScopeGuardrail(normalized_files, soft_mode=False, verbose=True),  # Enable verbose for debugging
            # FIX: Pass both files and directories to ToolCallValidationMiddleware
            ToolCallValidationMiddleware(normalized_files, codebase_root, allowed_dirs=allowed_directories, 
                                        soft_mode=False, verbose=True),  # Enable verbose for debugging
        ])
        print("🛡️  Guardrails: ENABLED (with directory scope support)")
    else:
        print("⚠️  Guardrails: DISABLED (debug mode)")

    return middleware


def log_middleware_config(
    feature_request: str,
    affected_files: List[str]
) -> None:
    """Debug helper: Log middleware configuration."""
    print("🔧 Middleware Configuration:")
    print(f"  Feature: {feature_request[:60]}...")
    print(f"  Allowed files: {len(affected_files)} file(s)")
    for f in affected_files[:3]:
        print(f"    • {f}")
    if len(affected_files) > 3:
        print(f"    ... and {len(affected_files) - 3} more")
