"""
Static validators for strategy code (syntax, imports, structure, methods, indicators).
"""

import ast
import re
import logging
from typing import Dict, List, Optional, Any

from jesse_mcp.core.strategy_validation.types import ValidationResult, ValidationLevel

logger = logging.getLogger("jesse-mcp.validator")


KNOWN_INDICATORS = {
    "sma",
    "ema",
    "wma",
    "hma",
    "vwma",
    "tema",
    "rsi",
    "macd",
    "atr",
    "adx",
    "stoch",
    "cci",
    "bollinger_bands",
    "bollinger_bands_width",
    "donchian_channel",
    "obv",
    "vwap",
    "mfi",
    "volume_profile",
    "supertrend",
    "ichimoku",
    "parabolic_sar",
    "zscore",
    "kalman_filter",
    "keltner_channel",
    "pivot_points",
}


class StaticValidator:
    """Static validation of strategy code (no execution)."""

    def validate_syntax(self, code: str) -> ValidationResult:
        """Validate Python syntax."""
        try:
            compile(code, "<string>", "exec")
            return ValidationResult(passed=True, level=ValidationLevel.SYNTAX.value)
        except SyntaxError as e:
            logger.warning(f"Syntax error: {e}")
            return ValidationResult(
                passed=False,
                level=ValidationLevel.SYNTAX.value,
                error=str(e),
                line=e.lineno,
            )

    def validate_imports(self, code: str) -> ValidationResult:
        """Validate required imports."""
        has_strategy_import = "from jesse.strategies import Strategy" in code
        has_ta_import = (
            "import jesse.indicators as ta" in code or "from jesse import indicators as ta" in code
        )

        if has_strategy_import and has_ta_import:
            return ValidationResult(passed=True, level=ValidationLevel.IMPORTS.value)

        missing = []
        if not has_strategy_import:
            missing.append("from jesse.strategies import Strategy")
        if not has_ta_import:
            missing.append("import jesse.indicators as ta")

        return ValidationResult(
            passed=False,
            level=ValidationLevel.IMPORTS.value,
            error=f"Missing imports: {', '.join(missing)}",
        )

    def validate_structure(self, code: str) -> ValidationResult:
        """Validate class structure (inherits from Strategy)."""
        class_match = re.search(r"class\s+(\w+)\s*\(([^)]*)\)\s*:", code)
        if not class_match:
            return ValidationResult(
                passed=False,
                level=ValidationLevel.STRUCTURE.value,
                error="No class definition found",
            )

        class_name = class_match.group(1)
        inherits = class_match.group(2)

        if "Strategy" in inherits:
            return ValidationResult(passed=True, level=ValidationLevel.STRUCTURE.value)

        return ValidationResult(
            passed=False,
            level=ValidationLevel.STRUCTURE.value,
            error=f"Class {class_name} must inherit from Strategy, not {inherits}",
            fix_hint="class " + class_name + "(Strategy):",
        )

    def validate_methods(self, code: str) -> ValidationResult:
        """Validate required methods exist."""
        required_methods = ["should_long", "go_long", "should_short", "go_short"]
        missing = []

        for method in required_methods:
            if f"def {method}(" not in code:
                missing.append(method)

        if not missing:
            return ValidationResult(passed=True, level=ValidationLevel.METHODS.value)

        return ValidationResult(
            passed=False,
            level=ValidationLevel.METHODS.value,
            error=f"Missing required methods: {', '.join(missing)}",
            fix_hint=",".join(missing),
        )

    def validate_indicators(self, code: str) -> ValidationResult:
        """Validate indicator usage."""
        ta_matches = re.findall(r"ta\.(\w+)\(", code)
        warnings = []

        for indicator in ta_matches:
            if indicator not in KNOWN_INDICATORS:
                warnings.append(f"Unknown indicator: ta.{indicator}")

        if warnings:
            logger.warning(f"Indicator warnings: {warnings}")

        return ValidationResult(
            passed=True,
            level=ValidationLevel.INDICATORS.value,
            warnings=warnings,
        )

    def full_static_validation(self, code: str) -> Dict[str, Any]:
        """Run all static validations."""
        results = {
            "passed": True,
            "levels": {},
            "errors": [],
            "warnings": [],
            "fix_hints": [],
        }

        validators = [
            (ValidationLevel.SYNTAX.value, self.validate_syntax),
            (ValidationLevel.IMPORTS.value, self.validate_imports),
            (ValidationLevel.STRUCTURE.value, self.validate_structure),
            (ValidationLevel.METHODS.value, self.validate_methods),
            (ValidationLevel.INDICATORS.value, self.validate_indicators),
        ]

        for level_name, validator in validators:
            result = validator(code)
            results["levels"][level_name] = result.to_dict()

            if not result.passed:
                results["passed"] = False
                results["errors"].append(
                    {"level": level_name, "error": result.error, "line": result.line}
                )
                if result.fix_hint:
                    results["fix_hints"].append({"level": level_name, "hint": result.fix_hint})

            if result.warnings:
                for warning in result.warnings:
                    results["warnings"].append({"level": level_name, "warning": warning})

        return results
