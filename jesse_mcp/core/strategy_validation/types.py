"""
Strategy Validation Types and Enums
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class ValidationLevel(Enum):
    SYNTAX = "syntax"
    IMPORTS = "imports"
    STRUCTURE = "structure"
    METHODS = "methods"
    INDICATORS = "indicators"
    DRY_RUN = "dry_run"


@dataclass
class ValidationResult:
    passed: bool
    level: str
    error: Optional[str] = None
    line: Optional[int] = None
    fix_hint: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "passed": self.passed,
            "level": self.level,
            "error": self.error,
            "line": self.line,
            "fix_hint": self.fix_hint,
        }
        if self.warnings:
            result["warnings"] = self.warnings
        if self.metrics:
            result["metrics"] = self.metrics
        return result
