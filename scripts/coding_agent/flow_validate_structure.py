"""
ENHANCED VALIDATE_STRUCTURE WITH FEEDBACK LOOP
===============================================

Phase 2A: Structure Validation with Iterative Refinement

This module implements:
1. Validate architecture against best practices
2. Provide detailed assessment and recommendations
3. Auto-create missing directories
4. Feedback loop: max 3 iterations to refine plan
5. Block advancement if not production-ready
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# ==============================================================================
# DATA MODELS
# ==============================================================================

@dataclass
class StructureViolation:
    """A structure violation or deviation from best practices"""
    violation_type: str  # "missing_layer", "wrong_location", "naming_issue", "architecture"
    severity: str  # "error", "warning", "info"
    location: str  # File path or directory
    message: str  # Human-readable message
    suggested_fix: str  # How to fix it


@dataclass
class RefactoringPlan:
    """Plan to refactor structure to meet best practices"""
    create_layers: List[str]  # Directories to create
    extract_classes: List[Dict]  # Classes to extract
    move_code: List[Dict]  # Code to move between files
    add_annotations: List[Dict]  # Annotations to add
    effort_level: str  # "low", "medium", "high"
    estimated_time: str  # "30 mins", "1 hour", "2 hours"


@dataclass
class StructureAssessment:
    """Complete structure assessment result"""
    framework: str
    is_production_ready: bool
    score: float  # 0-100
    summary: str
    violations: List[StructureViolation]
    refactoring_plan: Optional[RefactoringPlan]


@dataclass
class ValidationRound:
    """Result of one validation round"""
    round_number: int
    timestamp: str
    assessment: StructureAssessment
    changes_made: List[str]  # What was adjusted
    ready_to_proceed: bool


# ==============================================================================
# VALIDATOR CLASS
# ==============================================================================

class EnhancedStructureValidator:
    """
    Enhanced validator with feedback loop.
    
    Flow:
    1. Validate current plan against best practices
    2. If violations found:
       - Generate refinement suggestions
       - Adjust plan if needed
       - Create missing directories
       - Retry validation (max 3 rounds)
    3. When production-ready or max rounds reached:
       - Proceed to next phase
    """
    
    MAX_VALIDATION_ROUNDS = 3
    
    def __init__(self, codebase_path: str, framework: str):
        self.codebase_path = codebase_path
        self.framework = framework
        self.validation_history = []
        self.current_round = 0
    
    def validate_and_refine(
        self,
        feature_spec: Dict[str, Any],
        new_files_planning: Optional[Dict[str, Any]] = None
    ) -> Tuple[StructureAssessment, bool, List[Dict]]:
        """
        Validate structure and refine plan iteratively.
        
        Args:
            feature_spec: Feature specification with new files
            new_files_planning: Planning suggestions for new files
            
        Returns:
            (assessment, production_ready, refinement_history)
        """
        import os
        
        refinements = []
        
        # Round 0: Initial validation
        self.current_round = 0
        assessment = self._validate_structure(feature_spec, new_files_planning)
        self.validation_history.append(assessment)
        
        # Check if production-ready
        if assessment.is_production_ready:
            print(f"  ✅ Structure is production-ready (score: {assessment.score:.1f}/100)")
            return assessment, True, refinements
        
        print(f"  ⚠️  Structure needs refinement (score: {assessment.score:.1f}/100)")
        print(f"  📋 Found {len(assessment.violations)} issues")
        
        # Refinement loop: max 3 rounds
        while self.current_round < self.MAX_VALIDATION_ROUNDS - 1:
            self.current_round += 1
            print(f"\n  🔄 Refinement Round {self.current_round}/{self.MAX_VALIDATION_ROUNDS}:")
            
            # Generate refinement
            refinement = self._generate_refinement(
                assessment,
                feature_spec,
                new_files_planning
            )
            refinements.append(refinement)
            
            # Apply refinement
            changes = self._apply_refinement(refinement)
            print(f"    ✓ Applied {len(changes)} changes")
            for change in changes[:3]:
                print(f"      - {change}")
            if len(changes) > 3:
                print(f"      ... and {len(changes) - 3} more")
            
            # Re-validate
            assessment = self._validate_structure(feature_spec, new_files_planning)
            self.validation_history.append(assessment)
            
            print(f"    📊 New score: {assessment.score:.1f}/100")
            print(f"    📋 Remaining issues: {len(assessment.violations)}")
            
            # Check if production-ready now
            if assessment.is_production_ready:
                print(f"\n  ✅ Structure is now production-ready!")
                return assessment, True, refinements
        
        # Max rounds reached
        print(f"\n  ⏸️  Max refinement rounds reached ({self.MAX_VALIDATION_ROUNDS})")
        
        if assessment.score >= 75:  # Good enough threshold
            print(f"  ✅ Score is acceptable ({assessment.score:.1f}/100). Proceeding with warnings.")
            return assessment, True, refinements
        else:
            print(f"  ❌ Score is below threshold ({assessment.score:.1f}/100). Manual review needed.")
            return assessment, False, refinements
    
    def _validate_structure(
        self,
        feature_spec: Dict[str, Any],
        new_files_planning: Optional[Dict[str, Any]] = None
    ) -> StructureAssessment:
        """Perform comprehensive structure validation"""
        import os
        
        violations = []
        score = 100  # Start with perfect score
        
        # Get new files that will be created
        new_files = new_files_planning.get("suggested_files", []) if new_files_planning else []
        new_dirs = new_files_planning.get("directory_structure", {}) if new_files_planning else {}
        
        # ===== VALIDATION RULES BY FRAMEWORK =====
        
        if self.framework == "spring-boot" or "spring" in str(self.framework).lower():
            violations, score = self._validate_spring_boot(
                new_files, new_dirs, violations, score
            )
        elif self.framework == "django" or "django" in str(self.framework).lower():
            violations, score = self._validate_django(
                new_files, new_dirs, violations, score
            )
        elif self.framework == "nodejs" or "node" in str(self.framework).lower():
            violations, score = self._validate_nodejs(
                new_files, new_dirs, violations, score
            )
        
        # Score cannot go below 0
        score = max(0, score)
        
        # Determine if production-ready
        is_production_ready = (
            score >= 85 and  # Score threshold
            len([v for v in violations if v.severity == "error"]) == 0  # No errors
        )
        
        # Generate refactoring plan if needed
        refactoring_plan = None
        if not is_production_ready and violations:
            refactoring_plan = self._generate_refactoring_plan(violations, new_files_planning)
        
        # Build summary
        error_count = len([v for v in violations if v.severity == "error"])
        warning_count = len([v for v in violations if v.severity == "warning"])
        summary = f"{error_count} errors, {warning_count} warnings, {len([v for v in violations if v.severity == 'info'])} info"
        
        return StructureAssessment(
            framework=str(self.framework),
            is_production_ready=is_production_ready,
            score=score,
            summary=summary,
            violations=violations,
            refactoring_plan=refactoring_plan
        )
    
    def _validate_spring_boot(
        self,
        new_files: List[Any],
        new_dirs: Dict[str, str],
        violations: List[StructureViolation],
        score: float
    ) -> Tuple[List[StructureViolation], float]:
        """Spring Boot specific validation"""
        
        # Check for required layers
        required_layers = ["model", "service", "controller", "repository", "dto"]
        
        for layer in required_layers:
            layer_path = f"src/main/java/com/example/springboot/{layer}"
            if layer not in str(new_dirs):
                violations.append(StructureViolation(
                    violation_type="missing_layer",
                    severity="warning",
                    location=layer_path,
                    message=f"Missing {layer} layer",
                    suggested_fix=f"Create directory: {layer_path}"
                ))
                score -= 10
        
        # Check file naming conventions
        file_count = len(new_files)
        if file_count > 0:
            # Check if files follow naming conventions
            for file_obj in new_files:
                filename = getattr(file_obj, 'filename', str(file_obj))
                layer = getattr(file_obj, 'layer', 'unknown')
                
                # Validate naming for each layer
                if layer == "model" and not filename.endswith(".java"):
                    violations.append(StructureViolation(
                        violation_type="naming_issue",
                        severity="warning",
                        location=filename,
                        message=f"Model file should be .java",
                        suggested_fix=f"Ensure file is named: {filename}"
                    ))
                    score -= 5
                
                # Check if entity has @Entity annotation will be checked in synthesize
                if layer == "model":
                    violations.append(StructureViolation(
                        violation_type="info",
                        severity="info",
                        location=filename,
                        message=f"Model file needs @Entity, @Table annotations",
                        suggested_fix="Add JPA annotations during code generation"
                    ))
        else:
            violations.append(StructureViolation(
                violation_type="architecture",
                severity="error",
                location="feature_spec.new_files",
                message="No new files identified for feature",
                suggested_fix="Run feature analysis again to identify new files needed"
            ))
            score -= 20
        
        # Check SOLID principles mapping
        solid_mapped = all(
            getattr(f, 'solid_principles', []) 
            for f in new_files 
            if hasattr(f, 'filename')
        )
        if not solid_mapped:
            violations.append(StructureViolation(
                violation_type="info",
                severity="info",
                location="feature_spec.new_files",
                message="Not all files have SOLID principles mapped",
                suggested_fix="Map SOLID principles for each new file"
            ))
        
        return violations, score
    
    def _validate_django(
        self,
        new_files: List[Any],
        new_dirs: Dict[str, str],
        violations: List[StructureViolation],
        score: float
    ) -> Tuple[List[StructureViolation], float]:
        """Django specific validation"""
        
        # Check for required files in Django app
        required_files = ["models.py", "views.py", "urls.py", "serializers.py"]
        
        file_count = len(new_files)
        if file_count == 0:
            violations.append(StructureViolation(
                violation_type="missing_layer",
                severity="error",
                location="app",
                message="No new files identified for Django app",
                suggested_fix="Identify which Django files need to be created/modified"
            ))
            score -= 20
        
        return violations, score
    
    def _validate_nodejs(
        self,
        new_files: List[Any],
        new_dirs: Dict[str, str],
        violations: List[StructureViolation],
        score: float
    ) -> Tuple[List[StructureViolation], float]:
        """Node.js specific validation"""
        
        # Check for required layers
        required_dirs = ["routes", "controllers", "services", "middleware"]
        
        for dir_name in required_dirs:
            if dir_name not in str(new_dirs):
                violations.append(StructureViolation(
                    violation_type="missing_layer",
                    severity="warning",
                    location=dir_name,
                    message=f"Missing {dir_name} directory",
                    suggested_fix=f"Create directory: {dir_name}"
                ))
                score -= 10
        
        return violations, score
    
    def _generate_refinement(
        self,
        assessment: StructureAssessment,
        feature_spec: Dict[str, Any],
        new_files_planning: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate refinement suggestions based on violations"""
        
        refinement = {
            "round": self.current_round,
            "violations_to_address": [],
            "suggested_adjustments": [],
            "auto_fixes": []
        }
        
        # Address each violation
        for violation in assessment.violations:
            if violation.severity in ["error", "warning"]:
                refinement["violations_to_address"].append({
                    "type": violation.violation_type,
                    "message": violation.message,
                    "fix": violation.suggested_fix
                })
                
                # Auto-fix if possible
                if violation.violation_type == "missing_layer":
                    refinement["auto_fixes"].append({
                        "type": "create_directory",
                        "location": violation.location
                    })
        
        return refinement
    
    def _apply_refinement(self, refinement: Dict[str, Any]) -> List[str]:
        """Apply refinement changes to the project"""
        import os
        
        changes = []
        
        # Create missing directories
        for auto_fix in refinement.get("auto_fixes", []):
            if auto_fix["type"] == "create_directory":
                dir_path = os.path.join(self.codebase_path, auto_fix["location"])
                os.makedirs(dir_path, exist_ok=True)
                changes.append(f"Created directory: {auto_fix['location']}")
        
        return changes
    
    def _generate_refactoring_plan(
        self,
        violations: List[StructureViolation],
        new_files_planning: Optional[Dict[str, Any]] = None
    ) -> RefactoringPlan:
        """Generate a refactoring plan to address violations"""
        
        create_layers = []
        extract_classes = []
        move_code = []
        add_annotations = []
        
        # Extract suggestions from violations
        for violation in violations:
            if violation.violation_type == "missing_layer":
                create_layers.append(violation.location)
            elif violation.violation_type == "naming_issue":
                move_code.append({
                    "from": violation.location,
                    "reason": violation.message,
                    "suggested_fix": violation.suggested_fix
                })
            elif violation.violation_type == "architecture":
                add_annotations.append({
                    "file": violation.location,
                    "reason": violation.message,
                    "suggested_fix": violation.suggested_fix
                })
        
        # Determine effort level
        total_changes = len(create_layers) + len(extract_classes) + len(move_code)
        if total_changes == 0:
            effort_level = "low"
            estimated_time = "15 mins"
        elif total_changes <= 3:
            effort_level = "medium"
            estimated_time = "1 hour"
        else:
            effort_level = "high"
            estimated_time = "2 hours"
        
        return RefactoringPlan(
            create_layers=create_layers,
            extract_classes=extract_classes,
            move_code=move_code,
            add_annotations=add_annotations,
            effort_level=effort_level,
            estimated_time=estimated_time
        )


# ==============================================================================
# PHASE 2A: VALIDATE_STRUCTURE WITH FEEDBACK LOOP
# ==============================================================================

def validate_structure_with_feedback(
    state: Dict[str, Any],
    max_loops: int = 3
) -> Dict[str, Any]:
    """
    Enhanced validate_structure with iterative feedback loop.
    
    Flow:
    1. Validate plan from parse_intent
    2. If issues found:
       - Generate refinement suggestions
       - Auto-fix if possible
       - Create missing directories
       - Mark for feedback to parse_intent if major issues
    3. Allow max 3 validation rounds
    4. Proceed to next phase if good enough or max rounds reached
    
    Args:
        state: Workflow state with feature_spec
        max_loops: Max validation/refinement loops
        
    Returns:
        Updated state with structure assessment and validation results
    """
    print("🏗️ Phase 2A: Structure Validation & Refinement (with feedback loop)...")
    
    codebase_path = state.get("codebase_path")
    feature_spec = state.get("feature_spec")
    framework = state.get("framework")
    
    # Validation
    if not codebase_path:
        state["errors"].append("No codebase path provided")
        return state
    
    if not feature_spec:
        state["errors"].append("No feature spec available for validation")
        return state
    
    if not framework:
        print("  ⚠️  No framework detected, skipping framework-specific validation")
        framework = "generic"
    
    print(f"  🔍 Framework: {framework}")
    print(f"  📄 New files planned: {len(feature_spec.new_files) if hasattr(feature_spec, 'new_files') else 0}")
    
    try:
        # Create validator
        validator = EnhancedStructureValidator(codebase_path, framework)
        
        # Get new files planning if available
        new_files_planning = None
        if hasattr(feature_spec, 'new_files_planning'):
            nfp = feature_spec.new_files_planning
            new_files_planning = {
                "suggested_files": nfp.suggested_files if hasattr(nfp, 'suggested_files') else [],
                "directory_structure": nfp.directory_structure if hasattr(nfp, 'directory_structure') else {},
            }
        
        # Validate and refine (with feedback loop)
        assessment, production_ready, refinements = validator.validate_and_refine(
            feature_spec.__dict__ if hasattr(feature_spec, '__dict__') else feature_spec,
            new_files_planning
        )
        
        # Store results
        state["structure_assessment"] = {
            "framework": assessment.framework,
            "is_production_ready": assessment.is_production_ready,
            "score": assessment.score,
            "summary": assessment.summary,
            "violations": [
                {
                    "type": v.violation_type,
                    "severity": v.severity,
                    "location": v.location,
                    "message": v.message,
                    "suggested_fix": v.suggested_fix
                }
                for v in assessment.violations
            ],
            "refactoring_plan": None
        }
        
        if assessment.refactoring_plan:
            rp = assessment.refactoring_plan
            state["structure_assessment"]["refactoring_plan"] = {
                "create_layers": rp.create_layers,
                "extract_classes": rp.extract_classes,
                "move_code": rp.move_code,
                "add_annotations": rp.add_annotations,
                "effort_level": rp.effort_level,
                "estimated_time": rp.estimated_time
            }
        
        # Store validation history
        state["validation_history"] = [
            {
                "round": round_num + 1,
                "score": hist.score,
                "violations": len(hist.violations),
                "is_production_ready": hist.is_production_ready
            }
            for round_num, hist in enumerate(validator.validation_history)
        ]
        
        state["current_phase"] = "structure_validation_complete"
        
        # Print summary
        print(f"\n  📊 Validation Summary:")
        print(f"    Score: {assessment.score:.1f}/100")
        print(f"    Violations: {len(assessment.violations)}")
        print(f"    Production Ready: {'✅ Yes' if production_ready else '❌ No'}")
        print(f"    Rounds: {len(validator.validation_history)}/{max_loops}")
        
        # Violations summary
        error_count = len([v for v in assessment.violations if v.severity == "error"])
        warning_count = len([v for v in assessment.violations if v.severity == "warning"])
        info_count = len([v for v in assessment.violations if v.severity == "info"])
        
        if error_count > 0:
            print(f"\n  ❌ Errors ({error_count}):")
            for v in [v for v in assessment.violations if v.severity == "error"][:3]:
                print(f"     - {v.message}")
        
        if warning_count > 0:
            print(f"\n  ⚠️  Warnings ({warning_count}):")
            for v in [v for v in assessment.violations if v.severity == "warning"][:3]:
                print(f"     - {v.message}")
        
        if info_count > 0:
            print(f"\n  ℹ️  Info ({info_count}):")
            for v in [v for v in assessment.violations if v.severity == "info"][:2]:
                print(f"     - {v.message}")
        
        # Feedback suggestion
        if not production_ready and assessment.score < 70:
            print(f"\n  💡 Suggestion: Review plan with parse_intent to improve score")
            state["structure_feedback"] = {
                "action": "review_with_parse_intent",
                "reason": "Score below 70",
                "recommendations": [
                    v.suggested_fix for v in assessment.violations 
                    if v.severity == "error"
                ]
            }
        else:
            print(f"\n  ✅ Structure assessment complete. Proceeding to next phase.")
        
        return state
        
    except Exception as e:
        print(f"  ❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        state["errors"].append(f"Structure validation error: {str(e)}")
        state["structure_assessment"] = None
        return state


# ==============================================================================
# INTEGRATION: Update feature_by_request_agent_v3.py to use this
# ==============================================================================

"""
In feature_by_request_agent_v3.py, replace the validate_structure node with:

def validate_structure(state: AgentState) -> AgentState:
    '''Node: Structure Validation Phase with Feedback Loop'''
    from scripts.coding_agent.flow_validate_structure import validate_structure_with_feedback
    return validate_structure_with_feedback(state, max_loops=3)

This provides:
✅ Iterative validation and refinement
✅ Auto-fix for missing directories
✅ Production-readiness scoring
✅ Feedback loop back to parse_intent if needed
✅ Clear summary of issues and recommendations
"""
