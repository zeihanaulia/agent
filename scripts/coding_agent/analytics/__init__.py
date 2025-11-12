# Analytics package - framework detection and analysis
from .framework_detector import (
    detect_framework,
    detect_framework_from_filesystem,
    detect_framework_from_analysis,
    get_framework_name,
)

__all__ = [
    "detect_framework",
    "detect_framework_from_filesystem",
    "detect_framework_from_analysis",
    "get_framework_name",
]
