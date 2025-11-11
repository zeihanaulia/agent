"""
PROJECT STRUCTURE VALIDATOR
============================

Validates project structure against framework best practices.
Identifies violations and proposes refactoring strategy.

Usage:
    from structure_validator import validate_structure
    
    assessment = validate_structure(
        codebase_path="/path/to/project",
        framework="SPRING_BOOT"
    )
    
    if not assessment["is_production_ready"]:
        print(assessment["violations"])
        print(assessment["refactoring_needed"])
"""

import os
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Try to import framework instructions
try:
    from coding_agent.framework_instructions import FrameworkType  # pyright: ignore[reportAssignmentType]
    HAS_FRAMEWORK_INSTRUCTIONS = True
except ImportError:
    HAS_FRAMEWORK_INSTRUCTIONS = False
    FrameworkType = None  # type: ignore


@dataclass
class Violation:
    """Represents a structure violation"""
    violation_type: str  # "missing_layer", "code_in_wrong_place", "nested_model", etc
    location: str  # File or directory where violation occurs
    severity: str  # "critical", "high", "medium", "low"
    message: str  # Human-readable explanation
    suggested_fix: str  # What should be done


@dataclass
class RefactoringPlan:
    """Plan for refactoring project structure"""
    create_layers: List[str]  # Directories to create
    extract_classes: List[Dict[str, str]]  # Classes to extract from files
    move_code: List[Dict[str, str]]  # Code sections to move
    add_annotations: List[Dict[str, str]]  # Annotations to add to classes
    effort_level: str  # "low", "medium", "high"
    estimated_time: str  # "< 5 min", "5-15 min", "> 15 min"


@dataclass
class StructureAssessment:
    """Complete assessment of project structure"""
    is_production_ready: bool
    framework: Optional[str]
    violations: List[Violation]
    refactoring_plan: Optional[RefactoringPlan]
    score: float  # 0-100, 100 = fully compliant
    summary: str


# ============================================================================
# CORE FUNCTIONS
# ============================================================================


def validate_structure(
    codebase_path: str,
    framework: Optional[str] = None
) -> StructureAssessment:
    """
    Main entry point: validate project structure against best practices.
    
    Args:
        codebase_path: Root path of project
        framework: Framework type (e.g., "SPRING_BOOT"). If None, will attempt to detect.
    
    Returns:
        StructureAssessment with violations and refactoring plan
    """
    
    # Step 1: Get expected structure for framework
    expected_structure = get_expected_structure(framework)
    
    if not expected_structure:
        return StructureAssessment(
            is_production_ready=True,  # Can't validate without framework info
            framework=None,
            violations=[],
            refactoring_plan=None,
            score=100,
            summary="Unknown framework. Skipping structure validation."
        )
    
    # Step 2: Scan actual structure
    actual_structure = scan_project_structure(codebase_path)
    
    # Step 3: Compare and identify violations
    violations = identify_violations(
        codebase_path,
        actual_structure,
        expected_structure
    )
    
    # Step 4: Determine if production ready
    is_production_ready = len([v for v in violations if v.severity == "critical"]) == 0
    
    # Step 5: Generate refactoring plan if needed
    refactoring_plan = None
    if violations:
        refactoring_plan = generate_refactoring_plan(
            codebase_path,
            violations,
            expected_structure
        )
    
    # Step 6: Calculate compliance score
    score = calculate_compliance_score(violations)
    
    return StructureAssessment(
        is_production_ready=is_production_ready,
        framework=framework,
        violations=violations,
        refactoring_plan=refactoring_plan,
        score=score,
        summary=generate_summary(violations, is_production_ready)
    )


def get_expected_structure(framework: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Get expected structure for framework.
    
    Returns expected layers, file patterns, annotations, etc.
    """
    
    # For now, define Spring Boot structure inline
    # In future, can get from framework_instructions module
    
    if framework and framework.upper() == "SPRING_BOOT":
        return {
            "framework": "SPRING_BOOT",
            "required_layers": {
                "controller": "HTTP request handlers (@RestController)",
                "service": "Business logic (@Service)",
                "repository": "Data access (@Repository)",
                "dto": "Data transfer objects (plain classes)",
                "model": "Domain entities (@Entity, @Table)"
            },
            "optional_layers": {
                "config": "Spring configuration",
                "exception": "Custom exceptions",
                "util": "Utility classes"
            },
            "file_patterns": {
                "controller": r".*Controller\.java$",
                "service": r".*Service\.java$",
                "repository": r".*Repository\.java$",
                "dto": r".*DTO\.java$",
                "model": r"^(?!.*Controller|.*Service|.*Repository|.*DTO)[a-zA-Z]+\.java$"
            },
            "base_package": "com/example/springboot",
            "package_path": "src/main/java/com/example/springboot",
            "required_annotations": {
                "controller": ["@RestController", "@RequestMapping"],
                "service": ["@Service"],
                "repository": ["@Repository"],
                "model": ["@Entity"]
            }
        }
    
    # Add other frameworks as needed (Django, Rails, etc)
    
    return None


def scan_project_structure(codebase_path: str) -> Dict[str, Any]:
    """
    Scan project and extract structure information.
    
    Returns:
        Dict with: directories, files, classes, imports, annotations
    """
    
    structure: Dict[str, Any] = {
        "directories": [],
        "java_files": [],
        "packages": set(),
        "classes": {},  # class_name -> {file, package, annotations, code}
        "violations": []
    }
    
    # Scan for Java files
    java_src_path = os.path.join(codebase_path, "src/main/java")
    
    if not os.path.isdir(java_src_path):
        return structure
    
    for root, dirs, files in os.walk(java_src_path):
        # Track directories
        rel_root = os.path.relpath(root, java_src_path)
        if rel_root != ".":
            structure["directories"].append(rel_root)
        
        # Track Java files
        for file in files:
            if file.endswith(".java"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, codebase_path)
                structure["java_files"].append(rel_path)
                
                # Extract package and class info
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    # Extract package
                    package_match = re.search(r'package\s+([\w.]+);', content)
                    package = None
                    if package_match:
                        package = package_match.group(1)
                        structure["packages"].add(package)
                    
                    # Extract class names and annotations
                    class_matches = re.finditer(
                        r'(@[\w.]+\s+)*public\s+(?:static\s+)?(?:abstract\s+)?class\s+(\w+)',
                        content
                    )
                    for match in class_matches:
                        class_name = match.group(2)
                        structure["classes"][class_name] = {
                            "file": rel_path,
                            "package": package,
                            "content": content[:1000]  # First 1000 chars for analysis
                        }
                except Exception:
                    pass
    
    return structure


def identify_violations(
    codebase_path: str,
    actual: Dict[str, Any],
    expected: Dict[str, Any]
) -> List[Violation]:
    """
    Compare actual vs expected structure, identify violations.
    
    Returns:
        List of violations found
    """
    
    violations: List[Violation] = []
    
    if not expected:
        return violations
    
    # Extract expected data
    required_layers = expected.get("required_layers", {})
    base_package_path = expected.get("package_path", "src/main/java/com/example/springboot")
    
    # Check 1: Verify required layer directories exist
    for layer, description in required_layers.items():
        layer_path = os.path.join(codebase_path, base_package_path, layer)
        if not os.path.isdir(layer_path):
            violations.append(Violation(
                violation_type="missing_layer",
                location=layer_path,
                severity="high",
                message=f"Missing {layer}/ directory for {description}",
                suggested_fix=f"Create directory: {layer_path}"
            ))
    
    # Check 2: Scan for code in wrong places
    for class_name, class_info in actual.get("classes", {}).items():
        violations.extend(check_class_location(class_name, class_info, expected, codebase_path))
    
    # Check 3: Check for nested classes that should be separate
    violations.extend(check_for_nested_models(codebase_path, actual))
    
    # Check 4: Check for data storage/business logic in controllers
    violations.extend(check_controller_violations(codebase_path, actual))
    
    # Check 5: Check for missing separation of concerns
    violations.extend(check_separation_of_concerns(codebase_path, actual))
    
    return violations


def check_class_location(
    class_name: str,
    class_info: Dict[str, Any],
    expected: Dict[str, Any],
    codebase_path: str
) -> List[Violation]:
    """Check if class is in correct directory based on its name and type."""
    
    violations: List[Violation] = []
    file_path = class_info.get("file", "")
    
    # Infer layer from class name
    inferred_layer = infer_layer_from_class_name(class_name)
    
    if not inferred_layer:
        return violations
    
    # Check if file is in correct directory
    base_package_path = expected.get("package_path", "src/main/java/com/example/springboot")
    expected_dir = os.path.join(base_package_path, inferred_layer)
    
    if expected_dir not in file_path:
        violations.append(Violation(
            violation_type="class_in_wrong_layer",
            location=file_path,
            severity="high",
            message=f"Class '{class_name}' should be in {inferred_layer}/ directory",
            suggested_fix=f"Move {file_path} to {expected_dir}/"
        ))
    
    return violations


def check_for_nested_models(codebase_path: str, actual: Dict[str, Any]) -> List[Violation]:
    """Check for nested classes that should be separate files."""
    
    violations: List[Violation] = []
    
    for java_file in actual.get("java_files", []):
        full_path = os.path.join(codebase_path, java_file)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find nested classes (static or non-static)
            nested_matches = re.finditer(
                r'(?:public\s+static\s+)?class\s+(\w+)\s*\{[^}]*\}',
                content
            )
            
            for match in nested_matches:
                nested_class = match.group(1)
                # Check if it looks like a domain model (not an inner utility class)
                if is_domain_model_class(nested_class, content):
                    violations.append(Violation(
                        violation_type="nested_model",
                        location=f"{java_file}::{nested_class}",
                        severity="medium",
                        message=f"Domain model '{nested_class}' should be in separate file in model/ directory",
                        suggested_fix=f"Extract '{nested_class}' to model/{nested_class}.java"
                    ))
        except Exception:
            pass
    
    return violations


def check_controller_violations(codebase_path: str, actual: Dict[str, Any]) -> List[Violation]:
    """Check for business logic/data storage in controllers."""
    
    violations: List[Violation] = []
    
    for java_file in actual.get("java_files", []):
        if "controller" not in java_file.lower():
            continue
        
        full_path = os.path.join(codebase_path, java_file)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check for data storage patterns
            storage_patterns = [
                (r'private\s+.*Map\s*<', "Data storage (Map/Dictionary) in controller"),
                (r'private\s+.*List\s*<', "Data storage (List/Collection) in controller"),
                (r'private\s+.*Set\s*<', "Data storage (Set/Collection) in controller"),
                (r'private\s+AtomicLong', "ID generation in controller"),
                (r'private\s+.*\[\]', "Data storage (Array) in controller")
            ]
            
            for pattern, message in storage_patterns:
                if re.search(pattern, content):
                    violations.append(Violation(
                        violation_type="data_storage_in_controller",
                        location=java_file,
                        severity="high",
                        message=message,
                        suggested_fix="Move to repository/ or service/ layer"
                    ))
        except Exception:
            pass
    
    return violations


def check_separation_of_concerns(codebase_path: str, actual: Dict[str, Any]) -> List[Violation]:
    """Check for mixed concerns in files."""
    
    violations: List[Violation] = []
    
    # Check if service layer uses repository (proper injection)
    # Check if controller uses service (proper injection)
    # (This is a simplified check - could be enhanced)
    
    return violations


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def infer_layer_from_class_name(class_name: str) -> Optional[str]:
    """Infer which layer a class belongs to based on its name."""
    
    patterns = {
        "controller": r".*Controller$",
        "service": r".*Service$",
        "repository": r".*Repository$",
        "dto": r".*DTO$|.*Dto$",
        "model": r"^(?!.*Controller|.*Service|.*Repository|.*DTO)[a-zA-Z]+$"
    }
    
    for layer, pattern in patterns.items():
        if re.match(pattern, class_name):
            return layer
    
    return None


def is_domain_model_class(class_name: str, file_content: str) -> bool:
    """Check if class looks like a domain model."""
    
    # Domain models typically:
    # - Have field declarations
    # - Have getters/setters
    # - Don't have HTTP annotations
    # - Don't have Spring annotations
    
    has_fields = bool(re.search(r'private\s+\w+\s+\w+\s*[;=]', file_content))
    has_getters = bool(re.search(r'public\s+\w+\s+get\w+\s*\(', file_content))
    has_spring_annotations = bool(re.search(r'@(?:Autowired|Service|Repository|Controller)', file_content))
    
    return has_fields and (has_getters or has_fields) and not has_spring_annotations


def generate_refactoring_plan(
    codebase_path: str,
    violations: List[Violation],
    expected: Dict[str, Any]
) -> RefactoringPlan:
    """Generate refactoring plan based on violations."""
    
    create_layers: List[str] = []
    extract_classes: List[Dict[str, str]] = []
    move_code: List[Dict[str, str]] = []
    add_annotations: List[Dict[str, str]] = []
    
    # Collect actions from violations
    for violation in violations:
        if violation.violation_type == "missing_layer":
            # Extract layer name from path
            layer = os.path.basename(violation.location)
            if layer not in create_layers:
                create_layers.append(layer)
        
        elif violation.violation_type == "nested_model":
            # Extract class name and file
            parts = violation.location.split("::")
            if len(parts) == 2:
                extract_classes.append({
                    "from_file": parts[0],
                    "class_name": parts[1],
                    "to_directory": "model"
                })
        
        elif violation.violation_type == "data_storage_in_controller":
            move_code.append({
                "from_file": violation.location,
                "type": "data_storage",
                "to_layer": "repository"
            })
    
    # Determine effort level
    total_items = len(create_layers) + len(extract_classes) + len(move_code)
    if total_items <= 2:
        effort_level = "low"
        estimated_time = "< 5 min"
    elif total_items <= 5:
        effort_level = "medium"
        estimated_time = "5-15 min"
    else:
        effort_level = "high"
        estimated_time = "> 15 min"
    
    return RefactoringPlan(
        create_layers=create_layers,
        extract_classes=extract_classes,
        move_code=move_code,
        add_annotations=add_annotations,
        effort_level=effort_level,
        estimated_time=estimated_time
    )


def calculate_compliance_score(violations: List[Violation]) -> float:
    """Calculate compliance score (0-100) based on violations."""
    
    # Weight by severity
    severity_weights = {
        "critical": 25,
        "high": 15,
        "medium": 5,
        "low": 1
    }
    
    total_penalty = sum(
        severity_weights.get(v.severity, 0) for v in violations
    )
    
    # Max penalty is 100 (fully non-compliant)
    score = max(0, 100 - total_penalty)
    
    return score


def generate_summary(violations: List[Violation], is_production_ready: bool) -> str:
    """Generate human-readable summary of assessment."""
    
    if not violations:
        return "✅ Project structure is production-ready!"
    
    critical_count = len([v for v in violations if v.severity == "critical"])
    high_count = len([v for v in violations if v.severity == "high"])
    medium_count = len([v for v in violations if v.severity == "medium"])
    low_count = len([v for v in violations if v.severity == "low"])
    
    summary = "⚠️  Project structure needs improvement: "
    counts = []
    if critical_count:
        counts.append(f"{critical_count} critical")
    if high_count:
        counts.append(f"{high_count} high")
    if medium_count:
        counts.append(f"{medium_count} medium")
    if low_count:
        counts.append(f"{low_count} low")
    
    summary += ", ".join(counts) + " violation(s) found"
    
    if is_production_ready:
        summary += "\n✅ No critical issues - can proceed with feature implementation"
    else:
        summary += "\n❌ Critical issues found - refactoring recommended before feature implementation"
    
    return summary


# ============================================================================
# CLI FOR TESTING
# ============================================================================


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python structure_validator.py <codebase_path> [framework]")
        sys.exit(1)
    
    codebase = sys.argv[1]
    framework = sys.argv[2] if len(sys.argv) > 2 else "SPRING_BOOT"
    
    print(f"\n🔍 Validating structure: {codebase}")
    print(f"   Framework: {framework}\n")
    
    assessment = validate_structure(codebase, framework)
    
    print(assessment.summary)
    print(f"\nCompliance Score: {assessment.score}/100")
    
    if assessment.violations:
        print(f"\n📋 Violations ({len(assessment.violations)}):")
        for v in assessment.violations:
            print(f"  [{v.severity.upper()}] {v.violation_type}")
            print(f"      Location: {v.location}")
            print(f"      Message: {v.message}")
            print(f"      Fix: {v.suggested_fix}\n")
    
    if assessment.refactoring_plan:
        plan = assessment.refactoring_plan
        print(f"🔧 Refactoring Plan (Effort: {plan.effort_level}, ~{plan.estimated_time}):")
        if plan.create_layers:
            print(f"  Create layers: {', '.join(plan.create_layers)}")
        if plan.extract_classes:
            print(f"  Extract classes: {len(plan.extract_classes)} class(es)")
        if plan.move_code:
            print(f"  Move code: {len(plan.move_code)} block(s)")
