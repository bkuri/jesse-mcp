"""
Multi-level Strategy Validation Module

Provides comprehensive validation for Jesse trading strategies across multiple levels:
syntax, imports, structure, methods, and indicators.
"""

import ast
import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger("jesse-mcp.validator")


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


KNOWN_INDICATORS = {
    "acosc",
    "ad",
    "adosc",
    "adx",
    "adxr",
    "alligator",
    "alma",
    "ao",
    "apo",
    "aroon",
    "aroonosc",
    "atr",
    "avgprice",
    "bandpass",
    "beta",
    "bollinger_bands",
    "bollinger_bands_width",
    "bop",
    "cc",
    "cci",
    "cfo",
    "cg",
    "chande",
    "chop",
    "cksp",
    "cmo",
    "correl",
    "correlation_cycle",
    "cvi",
    "cwma",
    "damiani_volatmeter",
    "dec_osc",
    "decycler",
    "dema",
    "devstop",
    "di",
    "dm",
    "donchian",
    "dpo",
    "dti",
    "dx",
    "edcf",
    "efi",
    "ema",
    "emd",
    "emv",
    "epma",
    "er",
    "eri",
    "fisher",
    "fosc",
    "frama",
    "fwma",
    "gatorosc",
    "gauss",
    "heikin_ashi_candles",
    "high_pass",
    "high_pass_2_pole",
    "hma",
    "hurst_exponent",
    "hwma",
    "ichimoku_cloud",
    "ichimoku_cloud_seq",
    "ift_rsi",
    "itrend",
    "jma",
    "jsa",
    "kama",
    "kaufmanstop",
    "kdj",
    "keltner",
    "kst",
    "kurtosis",
    "kvo",
    "linearreg",
    "linearreg_angle",
    "linearreg_intercept",
    "linearreg_slope",
    "lrsi",
    "ma",
    "maaq",
    "mab",
    "macd",
    "mama",
    "marketfi",
    "mass",
    "mcginley_dynamic",
    "mean_ad",
    "median_ad",
    "medprice",
    "mfi",
    "midpoint",
    "midprice",
    "minmax",
    "mom",
    "mwdx",
    "msw",
    "natr",
    "nma",
    "nvi",
    "obv",
    "pfe",
    "pivot",
    "pma",
    "ppo",
    "pvi",
    "pwma",
    "qstick",
    "reflex",
    "roc",
    "rocp",
    "rocr",
    "rocr100",
    "roofing",
    "rsi",
    "rsmk",
    "rsx",
    "rvi",
    "safezonestop",
    "sar",
    "sinwma",
    "skew",
    "sma",
    "smma",
    "sqwma",
    "srsi",
    "srwma",
    "stc",
    "stiffness",
    "stdev",
    "stoch",
    "stochf",
    "supersmoother",
    "supersmoother_3_pole",
    "supertrend",
    "support_resistance_with_breaks",
    "swma",
    "t3",
    "tema",
    "trange",
    "trendflex",
    "trima",
    "trix",
    "tsf",
    "tsi",
    "ttm_squeeze",
    "ttm_trend",
    "typprice",
    "ui",
    "ultosc",
    "var",
    "vi",
    "vidya",
    "vlma",
    "vosc",
    "voss",
    "vpci",
    "vpwma",
    "vpt",
    "vwap",
    "vwma",
    "vwmacd",
    "wad",
    "waddah_attar_explosion",
    "wclprice",
    "wilders",
    "willr",
    "wma",
    "wt",
    "zlema",
    "zscore",
}

REQUIRED_METHODS = [
    "should_long",
    "go_long",
    "should_short",
    "go_short",
]


class StrategyValidator:
    """
    Multi-level validator for Jesse trading strategies.

    Validates strategies through progressive levels:
    1. Syntax - Python syntax validity
    2. Imports - Required Jesse imports present
    3. Structure - Class inherits from Strategy
    4. Methods - Required strategy methods defined
    5. Indicators - Known Jesse indicators used
    6. Dry Run - Placeholder for backtest validation
    """

    def __init__(self):
        self.known_indicators = KNOWN_INDICATORS
        self.required_methods = REQUIRED_METHODS

    def validate_syntax(self, code: str) -> ValidationResult:
        """
        Validate Python syntax using compile().

        Args:
            code: Strategy source code

        Returns:
            ValidationResult with syntax validation status
        """
        try:
            compile(code, "<strategy>", "exec")
            logger.info("✅ Syntax validation passed")
            return ValidationResult(
                passed=True,
                level=ValidationLevel.SYNTAX.value,
            )
        except SyntaxError as e:
            logger.warning(f"❌ Syntax error at line {e.lineno}: {e.msg}")
            fix_hint = self._generate_syntax_fix_hint(e)
            return ValidationResult(
                passed=False,
                level=ValidationLevel.SYNTAX.value,
                error=e.msg,
                line=e.lineno,
                fix_hint=fix_hint,
            )
        except Exception as e:
            logger.error(f"❌ Unexpected syntax validation error: {e}")
            return ValidationResult(
                passed=False,
                level=ValidationLevel.SYNTAX.value,
                error=str(e),
                fix_hint="Check code for unexpected errors",
            )

    def _generate_syntax_fix_hint(self, error: SyntaxError) -> str:
        hints = {
            "invalid syntax": "Check for missing colons, parentheses, or operators",
            "unexpected EOF while parsing": "Check for unclosed brackets or quotes",
            "unterminated string literal": "Close the string with matching quotes",
            "expected ':'": "Add colon after if/for/while/def/class statement",
            "invalid character": "Remove or replace invalid characters",
            "indentation": "Fix indentation to use consistent spaces or tabs",
        }
        msg_lower = error.msg.lower() if error.msg else ""
        for key, hint in hints.items():
            if key in msg_lower:
                return hint
        return "Review syntax around the error location"

    def validate_imports(self, code: str) -> ValidationResult:
        """
        Validate required Jesse imports are present.

        Args:
            code: Strategy source code

        Returns:
            ValidationResult with import validation status
        """
        missing_imports = []
        warnings = []

        has_strategy_import = "from jesse.strategies import Strategy" in code
        has_ta_import = "import jesse.indicators" in code

        if not has_strategy_import:
            missing_imports.append("from jesse.strategies import Strategy")

        if not has_ta_import:
            warnings.append("Consider adding 'import jesse.indicators as ta' for indicator access")

        if missing_imports:
            error = f"Missing required imports: {', '.join(missing_imports)}"
            fix_hint = f"Add at top of file:\n{chr(10).join(missing_imports)}"
            logger.warning(f"❌ Import validation failed: {error}")
            return ValidationResult(
                passed=False,
                level=ValidationLevel.IMPORTS.value,
                error=error,
                fix_hint=fix_hint,
                warnings=warnings,
            )

        logger.info("✅ Import validation passed")
        return ValidationResult(
            passed=True,
            level=ValidationLevel.IMPORTS.value,
            warnings=warnings,
        )

    def validate_structure(self, code: str) -> ValidationResult:
        """
        Validate class structure inherits from Strategy.

        Args:
            code: Strategy source code

        Returns:
            ValidationResult with structure validation status
        """
        try:
            tree = ast.parse(code)

            strategy_classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = None
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr

                        if base_name == "Strategy":
                            strategy_classes.append(node.name)

            if not strategy_classes:
                pattern = r"class\s+(\w+)\s*\([^)]*\):"
                matches = re.findall(pattern, code)
                if matches:
                    error = f"Class '{matches[0]}' does not inherit from Strategy"
                    fix_hint = f"Change class definition to: class {matches[0]}(Strategy):"
                else:
                    error = "No strategy class found"
                    fix_hint = "Create a class that inherits from Strategy"
                logger.warning(f"❌ Structure validation failed: {error}")
                return ValidationResult(
                    passed=False,
                    level=ValidationLevel.STRUCTURE.value,
                    error=error,
                    fix_hint=fix_hint,
                )

            logger.info(f"✅ Structure validation passed (found: {', '.join(strategy_classes)})")
            return ValidationResult(
                passed=True,
                level=ValidationLevel.STRUCTURE.value,
            )

        except SyntaxError as e:
            return ValidationResult(
                passed=False,
                level=ValidationLevel.STRUCTURE.value,
                error=f"Cannot parse code: {e.msg}",
                line=e.lineno,
                fix_hint="Fix syntax errors before validating structure",
            )

    def validate_methods(self, code: str) -> ValidationResult:
        """
        Validate required strategy methods are defined.

        Args:
            code: Strategy source code

        Returns:
            ValidationResult with method validation status
        """
        missing_methods = []

        for method in self.required_methods:
            pattern = rf"def\s+{method}\s*\([^)]*\)\s*(->\s*[^:]+)?\s*:"
            if not re.search(pattern, code):
                missing_methods.append(method)

        if missing_methods:
            error = f"Missing required methods: {', '.join(missing_methods)}"
            fix_hint = "Add the following methods to your strategy class:\n"
            for method in missing_methods:
                if method.startswith("should"):
                    fix_hint += f"\n    def {method}(self) -> bool:\n        return False\n"
                else:
                    fix_hint += f"\n    def {method}(self):\n        pass\n"
            logger.warning(f"❌ Method validation failed: {error}")
            return ValidationResult(
                passed=False,
                level=ValidationLevel.METHODS.value,
                error=error,
                fix_hint=fix_hint,
            )

        logger.info("✅ Method validation passed")
        return ValidationResult(
            passed=True,
            level=ValidationLevel.METHODS.value,
        )

    def validate_indicators(self, code: str) -> ValidationResult:
        """
        Validate indicator usage and warn on unknown ta.* calls.

        Args:
            code: Strategy source code

        Returns:
            ValidationResult with indicator validation status and warnings
        """
        warnings = []
        unknown_indicators = []

        ta_pattern = r"ta\.(\w+)\s*\("
        ta_calls = re.findall(ta_pattern, code)

        for indicator in ta_calls:
            if indicator not in self.known_indicators:
                unknown_indicators.append(indicator)

        if unknown_indicators:
            unique_unknown = list(set(unknown_indicators))
            for indicator in unique_unknown:
                warnings.append(f"Unknown indicator: ta.{indicator}()")

        if warnings:
            logger.warning(f"⚠️ Indicator validation warnings: {len(warnings)}")
            return ValidationResult(
                passed=True,
                level=ValidationLevel.INDICATORS.value,
                warnings=warnings,
            )

        logger.info("✅ Indicator validation passed")
        return ValidationResult(
            passed=True,
            level=ValidationLevel.INDICATORS.value,
        )

    def dry_run_backtest(self, code: str, spec: Dict[str, Any]) -> ValidationResult:
        """
        Run a quick dry-run backtest to catch runtime errors.

        Args:
            code: Strategy source code
            spec: Backtest specification (symbol, timeframe, date range, etc.)

        Returns:
            ValidationResult with dry-run status and metrics
        """
        try:
            import os
            import uuid

            from jesse_mcp.core.integrations import (
                JESSE_AVAILABLE,
                JESSE_RESEARCH_AVAILABLE,
                JESSE_PATH,
            )
        except Exception as e:
            logger.warning(f"Cannot import for dry-run: {e}")
            return ValidationResult(
                passed=True,
                level=ValidationLevel.DRY_RUN.value,
                warnings=["Import error - skipping dry-run"],
            )

        if not JESSE_AVAILABLE:
            logger.warning("Jesse not available for dry-run backtest")
            return ValidationResult(
                passed=True,
                level=ValidationLevel.DRY_RUN.value,
                warnings=["Jesse not available - skipping dry-run"],
            )

        if not JESSE_RESEARCH_AVAILABLE:
            logger.warning("Jesse research module not available for dry-run backtest")
            return ValidationResult(
                passed=True,
                level=ValidationLevel.DRY_RUN.value,
                warnings=["Jesse research module not available - skipping dry-run"],
            )

        strategy_name = spec.get("name", f"DryRun_{uuid.uuid4().hex[:8]}")
        symbol = spec.get("symbol", "BTC-USDT")
        timeframe = spec.get("timeframe", "1h")
        exchange = spec.get("exchange", "Binance")

        temp_strategy_dir = None
        try:
            if not JESSE_PATH:
                return ValidationResult(
                    passed=False,
                    level=ValidationLevel.DRY_RUN.value,
                    error="No Jesse path available for dry-run",
                )

            strategies_path = os.path.join(JESSE_PATH, "strategies")
            temp_strategy_dir = os.path.join(strategies_path, f"_temp_{strategy_name}")
            os.makedirs(temp_strategy_dir, exist_ok=True)

            strategy_file = os.path.join(temp_strategy_dir, "__init__.py")
            with open(strategy_file, "w") as f:
                f.write(code)

            import jesse.helpers as jh
            from jesse import research

            start_date = "2024-01-01"
            end_date = "2024-01-05"
            start_ts = jh.arrow_to_timestamp(start_date)
            end_ts = jh.arrow_to_timestamp(end_date)

            candles, warmup = research.get_candles(
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
                start_date_timestamp=start_ts,
                finish_date_timestamp=end_ts,
                warmup_candles_num=240,
            )

            if candles is None or len(candles) == 0:
                return ValidationResult(
                    passed=False,
                    level=ValidationLevel.DRY_RUN.value,
                    error=f"No candle data available for {symbol}",
                )

            config = {
                "starting_balance": 10000,
                "fee": 0.001,
                "type": "futures",
                "futures_leverage": 1,
                "futures_leverage_mode": "cross",
                "exchange": exchange,
                "warm_up_candles": 240,
            }

            routes = [
                {
                    "exchange": exchange,
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            ]

            result = research.backtest(
                config=config,
                routes=routes,
                data_routes=[],
                candles={
                    f"{exchange}-{symbol}": {
                        "exchange": exchange,
                        "symbol": symbol,
                        "candles": candles,
                    }
                },
                generate_equity_curve=False,
                generate_trades=True,
                generate_logs=False,
                hyperparameters=None,
                fast_mode=True,
            )

            if "error" in result:
                return ValidationResult(
                    passed=False,
                    level=ValidationLevel.DRY_RUN.value,
                    error=f"Backtest error: {result.get('error', 'Unknown error')}",
                )

            metrics = result.get("metrics", {})
            total_trades = metrics.get("total_trades", 0)
            win_rate = metrics.get("win_rate", 0)
            total_return = metrics.get("total_return", 0)

            logger.info(
                f"✅ Dry-run complete: {total_trades} trades, {win_rate:.1%} win rate, {total_return:.2f}% return"
            )

            return ValidationResult(
                passed=True,
                level=ValidationLevel.DRY_RUN.value,
                warnings=[
                    f"Dry-run: {total_trades} trades, {win_rate:.1%} win rate, {total_return:.2f}% return"
                ],
                metrics={
                    "total_trades": total_trades,
                    "win_rate": win_rate,
                    "total_return": total_return,
                },
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Dry-run backtest failed: {error_msg}")
            return ValidationResult(
                passed=False,
                level=ValidationLevel.DRY_RUN.value,
                error=f"Runtime error: {error_msg}",
            )

        finally:
            if temp_strategy_dir and os.path.exists(temp_strategy_dir):
                import shutil

                try:
                    shutil.rmtree(temp_strategy_dir)
                    logger.info(f"Cleaned up temp strategy: {temp_strategy_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp strategy: {e}")

    def full_validation(self, code: str, spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run all validation levels and return combined results.

        Args:
            code: Strategy source code
            spec: Optional backtest specification for dry-run validation

        Returns:
            Dict with combined validation results from all levels
        """
        results = {
            "passed": True,
            "levels": {},
            "errors": [],
            "warnings": [],
            "fix_hints": [],
        }

        validation_steps = [
            (ValidationLevel.SYNTAX.value, self.validate_syntax),
            (ValidationLevel.IMPORTS.value, self.validate_imports),
            (ValidationLevel.STRUCTURE.value, self.validate_structure),
            (ValidationLevel.METHODS.value, self.validate_methods),
            (ValidationLevel.INDICATORS.value, self.validate_indicators),
        ]

        for level_name, validator_func in validation_steps:
            result = validator_func(code)
            results["levels"][level_name] = result.to_dict()

            if not result.passed:
                results["passed"] = False
                results["errors"].append(
                    {
                        "level": level_name,
                        "error": result.error,
                        "line": result.line,
                    }
                )
                if result.fix_hint:
                    results["fix_hints"].append({"level": level_name, "hint": result.fix_hint})

            if result.warnings:
                for warning in result.warnings:
                    results["warnings"].append({"level": level_name, "warning": warning})

        if spec and results["passed"]:
            dry_run_result = self.dry_run_backtest(code, spec)
            results["levels"][ValidationLevel.DRY_RUN.value] = dry_run_result.to_dict()
            if dry_run_result.warnings:
                for warning in dry_run_result.warnings:
                    results["warnings"].append(
                        {"level": ValidationLevel.DRY_RUN.value, "warning": warning}
                    )

        logger.info(
            f"Full validation complete: {'✅ PASSED' if results['passed'] else '❌ FAILED'}"
        )
        return results


_validator_instance: Optional[StrategyValidator] = None


def get_validator() -> StrategyValidator:
    """
    Factory function to get StrategyValidator singleton.

    Returns:
        StrategyValidator instance
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = StrategyValidator()
    return _validator_instance
