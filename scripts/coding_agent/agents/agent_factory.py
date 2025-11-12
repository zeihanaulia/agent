"""
AGENT FACTORY - Centralized Agent Creation
===========================================

Consolidates all agent creation functions from feature_by_request_agent_v3.py.
Single source of truth for agent instantiation and configuration.

Agents in pipeline:
1. Phase 3: Impact Analysis Agent - Architect analyzing codebase patterns
2. Phase 4: Code Synthesis Agent - Engineer generating production-ready code
3. Phase 5: Execution Agent - Specialist applying code changes
"""

import os
import sys
from typing import List, Optional, Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

# Add parent directory to path for imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)


# ==============================================================================
# FIX 2.2: VALIDATING FILESYSTEM BACKEND
# ==============================================================================
# FIX 2.2: USE STANDARD FILESYSTEM BACKEND
# ==============================================================================
# Note: DeepAgent handles FilesystemBackend internally with validation.
# We just provide the backend instance for agent creation.
# FIX 2.3: HELPER FUNCTION TO SCAN CODEBASE FILES
# ==============================================================================

def _scan_codebase_files(codebase_path: str, max_files: int = 40) -> List[str]:
    """
    Scan codebase and return list of relevant files.
    
    Args:
        codebase_path: Root path to scan
        max_files: Maximum number of files to include in context
        
    Returns:
        List of absolute file paths
    """
    relevant_files = []
    extensions = {'.java', '.xml', '.properties', '.sql', '.yml', '.yaml', '.json'}
    
    try:
        for root, dirs, files in os.walk(codebase_path):
            # Skip hidden directories and common exclusions
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['target', '__pycache__', 'node_modules']]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    full_path = os.path.join(root, file)
                    relevant_files.append(full_path)
                    if len(relevant_files) >= max_files:
                        return sorted(relevant_files)
    except Exception as e:
        print(f"  ⚠️  Error scanning codebase: {e}")
    
    return sorted(relevant_files)


def create_impact_analysis_agent(
    codebase_path: str,
    analysis_model: Any
) -> Any:
    """
    Phase 3: Impact Analysis - Expert architect analyzing codebase patterns
    
    Args:
        codebase_path: Root path of the codebase
        analysis_model: LLM model instance for analysis
        
    Returns:
        DeepAgent instance configured for impact analysis
    """
    if not analysis_model:
        raise ValueError(
            "Model not configured. Please ensure LITELLM_API and LITELLM_VIRTUAL_KEY are set in .env"
        )
    
    backend = FilesystemBackend(root_dir=codebase_path)
    prompt = f"""\
You are an expert software architect analyzing codebase impact.

CODEBASE: {codebase_path}

Your task:
1. Use ls and read_file to understand project structure and patterns
2. Identify the architecture (MVC, layered, microservices, modular, etc)
3. Find key frameworks, libraries, and patterns in use
4. Determine naming conventions and code organization
5. Identify design patterns already implemented
6. List all files that need changes and why
7. Note any constraints or best practices to follow

Be specific: List exact file paths, patterns, and current code style.
Provide actionable insights for implementation.
"""
    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model,
        backend=backend
    )


def create_code_synthesis_agent(
    codebase_path: str,
    analysis_model: Any,
    files_to_modify: Optional[List[str]] = None,
    feature_request: Optional[str] = None
) -> Any:
    """
    Phase 4: Code Synthesis - Expert engineer generating testable, production-ready code
    
    IMPLEMENTS: Fix 2.1, 2.2, 2.3
    - Fix 2.1: FilesystemMiddleware with custom system_prompt for absolute path guidance
    - Fix 2.2: ValidatingFilesystemBackend to catch empty paths before processing
    - Fix 2.3: Pre-loaded file list in context to prevent path hallucinations
    
    Args:
        codebase_path: Root path of the codebase
        analysis_model: LLM model instance for code generation
        files_to_modify: List of files that will be modified
        feature_request: Original feature request for intent reminder
        
    Returns:
        DeepAgent instance configured for code synthesis with all fixes applied
    """
    if not analysis_model:
        raise ValueError(
            "Model not configured. Please ensure LITELLM_API and LITELLM_VIRTUAL_KEY are set in .env"
        )
    
    # FIX 2.2: Use standard FilesystemBackend 
    # DeepAgent handles validation internally
    backend = FilesystemBackend(root_dir=codebase_path)
    
    # FIX 2.3: Scan codebase and get actual files
    # Pre-loading file list prevents LLM from hallucinating paths
    available_files = _scan_codebase_files(codebase_path, max_files=40)
    files_context = "AVAILABLE FILES IN CODEBASE:\n"
    if available_files:
        for f in available_files:
            files_context += f"  - {f}\n"
    else:
        files_context += "  (No files found in scan)\n"
    
    # Main Phase 4 system prompt
    prompt = f"""\
You are an expert software engineer implementing a feature with production-quality standards.

CODEBASE: {codebase_path}

Your task:
1. Read existing code files to understand patterns, naming conventions, imports
2. Plan implementation using write_todos with specific file changes
3. Follow SOLID principles:
   - Single Responsibility: Each class/function has one purpose
   - Open/Closed: Open for extension, closed for modification
   - Liskov Substitution: Proper inheritance and interface design
   - Interface Segregation: Small, focused interfaces
   - Dependency Inversion: Depend on abstractions, not concrete implementations
4. Use appropriate design patterns (Factory, Strategy, Decorator, etc)
5. Write testable code: dependency injection, pure functions, isolated concerns
6. Use edit_file and write_file tools to implement changes
7. Follow existing code style exactly (naming, formatting, structure)
8. DO NOT add new dependencies - use only what's already in pom.xml/package.json
9. Ensure code compiles/runs immediately without config changes

Generate production-grade code that fellow engineers would be proud to review.

REQUIRED WORKFLOW - MANDATORY:
=============================
Step 1: For EACH file you will modify, FIRST call read_file with its FULL ABSOLUTE PATH
Step 2: THEN call edit_file with:
  - file_path: same ABSOLUTE PATH as read_file
  - search_string: exact text from the file you just read
  - replace_string: full replacement including all context
Step 3: For NEW files, call write_file with:
  - file_path: ABSOLUTE PATH 
  - content: COMPLETE file (all imports, class definition, methods, etc)

CRITICAL PARAMETERS - MUST NEVER BE EMPTY:
==========================================
- file_path: MUST be /full/path/to/file.java (absolute, never relative or empty)
- search_string: MUST be exact text from read_file result (copy-paste, never empty)
- replace_string: MUST NOT be empty (always provide full replacement)
- content: MUST NOT be empty (complete file content)

AVAILABLE FILES TO MODIFY:
{files_context}

⚠️  NEVER try to edit/write files not in the list above
⚠️  NEVER use empty paths - if you don't have absolute path, use read_file FIRST
⚠️  NEVER describe changes - ONLY use write_file and edit_file tools
"""
    
    # DeepAgent creates its own FilesystemMiddleware internally
    # The system_prompt we provide covers tool guidance
    
    # DeepAgent accepts system_prompt, model, and backend directly
    # It handles FilesystemMiddleware internally
    agent_kwargs = {
        "system_prompt": prompt,
        "model": analysis_model,
        "backend": backend
    }
    
    # Create the agent with base configuration
    return create_deep_agent(**agent_kwargs)


def create_execution_agent(
    codebase_path: str,
    analysis_model: Any,
    dry_run: bool = False
) -> Any:
    """
    Phase 5: Execution & Verification - Apply and verify code changes
    
    Args:
        codebase_path: Root path of the codebase
        analysis_model: LLM model instance
        dry_run: If True, don't apply changes (report only)
        
    Returns:
        DeepAgent instance configured for execution
    """
    if not analysis_model:
        raise ValueError(
            "Model not configured. Please ensure LITELLM_API and LITELLM_VIRTUAL_KEY are set in .env"
        )
    
    backend = FilesystemBackend(root_dir=codebase_path)
    mode = "DRY RUN" if dry_run else "APPLY CHANGES"
    prompt = f"""\
You are an execution specialist applying code changes.

CODEBASE PATH: {codebase_path}
MODE: {mode}

Tasks:
1. Apply code patches using filesystem tools
2. Verify syntactic correctness
3. Check implementation matches specification
4. Report success/failure with detailed feedback
"""
    return create_deep_agent(
        system_prompt=prompt,
        model=analysis_model,
        backend=backend
    )
