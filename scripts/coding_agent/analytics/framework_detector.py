"""
FRAMEWORK DETECTOR - Unified Framework Detection
=================================================

Single source of truth for framework detection across all phases.
Consolidates detection logic from flow_analyze_context.py and elsewhere.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from framework_instructions import FrameworkType, FRAMEWORK_REGISTRY


def detect_framework_from_filesystem(codebase_path: str) -> Optional[FrameworkType]:
    """
    Detect framework from filesystem markers (pom.xml, go.mod, etc).
    
    Args:
        codebase_path: Root path of the codebase
        
    Returns:
        FrameworkType or None if not detected
    """
    codebase = Path(codebase_path)
    
    # Check each framework in registry
    for framework_type, instruction in FRAMEWORK_REGISTRY.items():
        if instruction.detect_from_path(str(codebase)):
            return framework_type
    
    return None


def detect_framework_from_analysis(analysis_result: Dict[str, Any]) -> Optional[FrameworkType]:
    """
    Detect framework from code analysis results.
    
    Looks at:
    - project_type (Java/Maven, Node.js, Python, Go, etc)
    - framework field (Spring Boot, Django, etc)
    - tech_stack list
    
    Args:
        analysis_result: Result from code analysis (Phase 1)
        
    Returns:
        FrameworkType or None
    """
    if not analysis_result:
        return None
    
    basic_info = analysis_result.get("basic_info", {})
    project_type = basic_info.get("project_type", "").lower()
    framework = basic_info.get("framework", "").lower()
    tech_stack = basic_info.get("tech_stack", [])
    tech_stack_str = " ".join(str(t).lower() for t in tech_stack)
    
    # Spring Boot
    if "spring" in framework or "maven" in project_type or "gradle" in project_type:
        return FrameworkType.SPRING_BOOT
    
    # Django (note: Django not in FrameworkType enum currently)
    if "django" in framework or "django" in tech_stack_str:
        return FrameworkType.LARAVEL  # Map to LARAVEL as placeholder
    
    # Golang
    if "go" in framework or "go" in project_type:
        return FrameworkType.GOLANG
    
    # Laravel
    if "laravel" in framework or "php" in tech_stack_str:
        return FrameworkType.LARAVEL
    
    # Rails
    if "rails" in framework or "ruby" in tech_stack_str:
        return FrameworkType.RAILS
    
    # ASP.NET Core
    if "aspnet" in framework or "csharp" in tech_stack_str:
        return FrameworkType.ASPNET
    
    # Next.js
    if "next" in framework or "nextjs" in tech_stack_str:
        return FrameworkType.NEXTJS
    
    return None


def detect_framework(
    codebase_path: str,
    analysis_result: Optional[Dict[str, Any]] = None
) -> Optional[FrameworkType]:
    """
    Unified framework detection using multiple strategies.
    
    Strategy:
    1. First try filesystem detection (most reliable)
    2. Fall back to analysis-based detection if available
    3. Return None if no framework detected
    
    Args:
        codebase_path: Root path of the codebase
        analysis_result: Optional result from code analysis (Phase 1)
        
    Returns:
        FrameworkType or None
    """
    # Try filesystem detection first
    fs_detected = detect_framework_from_filesystem(codebase_path)
    if fs_detected:
        return fs_detected
    
    # Try analysis-based detection if provided
    if analysis_result:
        analysis_detected = detect_framework_from_analysis(analysis_result)
        if analysis_detected:
            return analysis_detected
    
    return None


def get_framework_name(framework_type: Optional[FrameworkType]) -> str:
    """
    Get human-readable framework name.
    
    Args:
        framework_type: FrameworkType enum
        
    Returns:
        String name of framework
    """
    if not framework_type:
        return "Unknown"
    
    instruction = FRAMEWORK_REGISTRY.get(framework_type)
    if instruction:
        return instruction.framework_name
    
    return str(framework_type)
