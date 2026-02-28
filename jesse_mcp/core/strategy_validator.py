"""
Strategy Validator - Main entry point for validation.
"""

import logging
from typing import Dict, Optional

from jesse_mcp.core.strategy_validation import (
    ValidationResult,
    ValidationLevel,
    StaticValidator,
    DryRunValidator,
)

logger = logging.getLogger("jesse-mcp.validator")

_static_validator = StaticValidator()


def _get_rest_client():
    from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

    return get_jesse_rest_client()


_dry_run_validator = DryRunValidator(_get_rest_client)


class StrategyValidator:
    """Main validator that combines static and dynamic validation."""

    def validate_syntax(self, code: str) -> ValidationResult:
        return _static_validator.validate_syntax(code)

    def validate_imports(self, code: str) -> ValidationResult:
        return _static_validator.validate_imports(code)

    def validate_structure(self, code: str) -> ValidationResult:
        return _static_validator.validate_structure(code)

    def validate_methods(self, code: str) -> ValidationResult:
        return _static_validator.validate_methods(code)

    def validate_indicators(self, code: str) -> ValidationResult:
        return _static_validator.validate_indicators(code)

    def dry_run_backtest(self, code: str, spec: Dict) -> ValidationResult:
        return _dry_run_validator.run_dry_run(code, spec)

    def full_validation(self, code: str, spec: Optional[Dict] = None) -> Dict:
        """Run all validations and return combined results."""
        results = _static_validator.full_static_validation(code)

        if spec and results["passed"]:
            dry_run_result = self.dry_run_backtest(code, spec)
            results["levels"][ValidationLevel.DRY_RUN.value] = dry_run_result.to_dict()
            if dry_run_result.warnings:
                for warning in dry_run_result.warnings:
                    results["warnings"].append({ValidationLevel.DRY_RUN.value: warning})

        logger.info(f"Validation: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")
        return results


_validator_instance = None


def get_validator() -> StrategyValidator:
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = StrategyValidator()
    return _validator_instance
