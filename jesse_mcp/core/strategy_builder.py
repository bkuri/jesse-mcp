"""
Strategy Builder and Refinement Framework

Provides strategy generation and iterative refinement capabilities for
autonomous trading strategy development.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from jesse_mcp.core.strategy_validator import StrategyValidator

logger = logging.getLogger("jesse-mcp.strategy_builder")

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

INDICATOR_KEYWORDS: Dict[str, List[str]] = {
    "trend": ["sma", "ema", "macd", "ichimoku", "supertrend", "parabolic_sar", "adx"],
    "momentum": ["rsi", "stoch", "cci", "momentum", "roc", "williams_r", "mfi"],
    "volatility": ["bollinger_bands", "atr", "keltner_channel", "donchian_channel"],
    "volume": ["obv", "volume_profile", "vwap", "cmf", "mfi"],
    "mean_reversion": ["rsi", "bollinger_bands", "zscore", "kalman_filter"],
    "breakout": ["donchian_channel", "bollinger_bands", "pivot_points", "support_resistance"],
    "scalping": ["ema", "vwap", "order_flow", "tick_volume"],
    "swing": ["sma", "ema", "macd", "rsi", "fibonacci"],
    "position": ["sma", "ema", "macd", "adx", "ichimoku"],
    "default": ["sma", "ema", "rsi", "macd"],
}

STRATEGY_TYPE_INDICATORS: Dict[str, List[str]] = {
    "trend_following": ["sma", "ema", "macd", "adx"],
    "mean_reversion": ["rsi", "bollinger_bands", "zscore"],
    "breakout": ["donchian_channel", "bollinger_bands", "atr"],
    "momentum": ["rsi", "stoch", "macd", "momentum"],
    "scalping": ["ema", "vwap", "rsi"],
    "swing": ["sma", "ema", "macd", "rsi"],
    "position": ["sma", "ema", "macd", "adx", "ichimoku"],
    "default": ["sma", "ema", "rsi"],
}


@dataclass
class StrategySpec:
    """
    Specification for a trading strategy.

    Attributes:
        name: Strategy name (used as class name)
        description: Human-readable description of the strategy
        strategy_type: Type classification (trend_following, mean_reversion, etc.)
        indicators: List of technical indicators to use
        risk_per_trade: Risk percentage per trade (0.01 = 1%)
        timeframe: Primary trading timeframe (1h, 4h, 1d, etc.)
        additional_params: Extra parameters for strategy customization
    """

    name: str
    description: str
    strategy_type: str
    indicators: List[str] = field(default_factory=list)
    risk_per_trade: float = 0.01
    timeframe: str = "1h"
    additional_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.indicators:
            self.indicators = infer_indicators(self.description, self.strategy_type)


def infer_indicators(description: str, strategy_type: str) -> List[str]:
    """
    Infer appropriate indicators from description and strategy type.

    Args:
        description: Natural language description of the strategy
        strategy_type: Strategy type classification

    Returns:
        List of indicator names to use
    """
    description_lower = description.lower()
    inferred: List[str] = []

    for keyword, indicators in INDICATOR_KEYWORDS.items():
        if keyword in description_lower:
            for indicator in indicators:
                if indicator not in inferred:
                    inferred.append(indicator)

    if strategy_type in STRATEGY_TYPE_INDICATORS:
        for indicator in STRATEGY_TYPE_INDICATORS[strategy_type]:
            if indicator not in inferred:
                inferred.append(indicator)

    if not inferred:
        inferred = STRATEGY_TYPE_INDICATORS.get("default", ["sma", "ema", "rsi"])

    logger.info(f"Inferred indicators for '{strategy_type}': {inferred}")
    return inferred


class StrategyBuilder:
    """
    Strategy generation and iterative refinement framework.

    This class handles:
    - Generating initial strategy code templates
    - Refining strategies based on validation errors
    - Refining strategies based on runtime errors
    - Running refinement loops until validation passes
    """

    def __init__(self, validator: "StrategyValidator") -> None:
        """
        Initialize the strategy builder.

        Args:
            validator: StrategyValidator instance for validation
        """
        self.validator = validator
        self._refinement_count = 0
        logger.info("✅ StrategyBuilder initialized")

    def generate_initial(self, spec: StrategySpec) -> str:
        """
        Generate initial strategy code template.

        This generates a placeholder template that should be filled in by an LLM.

        Args:
            spec: Strategy specification

        Returns:
            Strategy code template string
        """
        logger.info(f"Generating initial strategy: {spec.name}")

        indicators_init = self._generate_indicator_init(spec.indicators)
        hyperparameters = self._generate_hyperparameters(spec.indicators)

        code = f'''"""
{spec.description}

Strategy Type: {spec.strategy_type}
Indicators: {", ".join(spec.indicators)}
Timeframe: {spec.timeframe}
Risk per Trade: {spec.risk_per_trade * 100}%
"""

from jesse.strategies import Strategy
import jesse.indicators as ta


class {spec.name}(Strategy):
    """
    {spec.description}

    Auto-generated strategy template - requires LLM refinement.
    """

    def __init__(self):
        super().__init__()
        self.risk_per_trade = {spec.risk_per_trade}

    @property
    def hyperparameters(self):
        return {hyperparameters}

    def before(self):
        {indicators_init}

    def should_long(self) -> bool:
        return False

    def should_short(self) -> bool:
        return False

    def go_long(self):
        pass

    def go_short(self):
        pass

    def should_cancel_entry(self) -> bool:
        return True

    def on_close_position(self, order):
        pass

    def hyperparameters(self):
        return self.hyperparameters
'''
        logger.info(f"✅ Generated initial template for {spec.name} ({len(code)} bytes)")
        return code

    def _generate_indicator_init(self, indicators: List[str]) -> str:
        """Generate indicator initialization code."""
        if not indicators:
            return "pass"

        lines = []
        for indicator in indicators:
            if indicator == "sma":
                lines.append("self.sma_fast = ta.sma(self.candles, 20)")
                lines.append("self.sma_slow = ta.sma(self.candles, 50)")
            elif indicator == "ema":
                lines.append("self.ema_fast = ta.ema(self.candles, 12)")
                lines.append("self.ema_slow = ta.ema(self.candles, 26)")
            elif indicator == "rsi":
                lines.append("self.rsi = ta.rsi(self.candles, 14)")
            elif indicator == "macd":
                lines.append("self.macd = ta.macd(self.candles)")
            elif indicator == "bollinger_bands":
                lines.append("self.bb = ta.bollinger_bands(self.candles)")
            elif indicator == "atr":
                lines.append("self.atr = ta.atr(self.candles, 14)")
            elif indicator == "adx":
                lines.append("self.adx = ta.adx(self.candles, 14)")
            else:
                lines.append(f"# TODO: Initialize {indicator}")

        return "\n        ".join(lines)

    def _generate_hyperparameters(self, indicators: List[str]) -> str:
        """Generate hyperparameters list."""
        params = []

        if "sma" in indicators or "ema" in indicators:
            params.extend(
                [
                    "{'name': 'fast_period', 'type': int, 'default': 20, 'min': 5, 'max': 50}",
                    "{'name': 'slow_period', 'type': int, 'default': 50, 'min': 20, 'max': 200}",
                ]
            )

        if "rsi" in indicators:
            params.append("{'name': 'rsi_period', 'type': int, 'default': 14, 'min': 7, 'max': 28}")
            params.append(
                "{'name': 'rsi_overbought', 'type': int, 'default': 70, 'min': 60, 'max': 90}"
            )
            params.append(
                "{'name': 'rsi_oversold', 'type': int, 'default': 30, 'min': 10, 'max': 40}"
            )

        if "macd" in indicators:
            params.extend(
                [
                    "{'name': 'macd_fast', 'type': int, 'default': 12, 'min': 5, 'max': 26}",
                    "{'name': 'macd_slow', 'type': int, 'default': 26, 'min': 13, 'max': 52}",
                    "{'name': 'macd_signal', 'type': int, 'default': 9, 'min': 5, 'max': 20}",
                ]
            )

        if not params:
            params.append(
                "{'name': 'risk_per_trade', 'type': float, 'default': 0.01, 'min': 0.001, 'max': 0.05}"
            )

        return "[\n            " + ",\n            ".join(params) + "\n        ]"

    def refine_from_validation(self, code: str, result: Dict[str, Any]) -> str:
        """
        Refine strategy code based on validation errors using LLM.

        Args:
            code: Current strategy code
            result: Validation result containing errors

        Returns:
            Refined strategy code
        """
        self._refinement_count += 1
        logger.info(f"🔧 Refining strategy (iteration {self._refinement_count})")

        errors = result.get("errors", [])
        warnings = result.get("warnings", [])

        if not errors:
            logger.info("No errors to fix")
            return code

        error_summary = "\n".join(
            [f"- {e.get('level', 'unknown')}: {e.get('error', 'Unknown error')}" for e in errors]
        )
        logger.warning(f"Errors to fix:\n{error_summary}")

        if LLM_ENDPOINT and LLM_API_KEY:
            try:
                fixed_code = self._fix_with_llm(code, errors, warnings, result.get("spec", {}))
                if fixed_code:
                    logger.info("✅ LLM successfully fixed the code")
                    return fixed_code
            except Exception as e:
                logger.warning(f"LLM refinement failed: {e}, falling back to template-based fixes")

        fixed_code = self._fix_with_templates(code, errors, result)
        return fixed_code

    def _fix_with_llm(
        self, code: str, errors: List[Dict], warnings: List[Dict], spec: Dict
    ) -> Optional[str]:
        """Fix validation errors using LLM API."""
        import requests

        error_summary = "\n".join(
            [f"- {e.get('level', 'unknown')}: {e.get('error', 'Unknown error')}" for e in errors]
        )

        prompt = f"""You are a Jesse trading strategy expert. Fix the following Python strategy code that has validation errors.

STRATEGY NAME: {spec.get("name", "Unknown")}
STRATEGY DESCRIPTION: {spec.get("description", "")}

VALIDATION ERRORS:
{error_summary}

CURRENT CODE:
```{code}
```

Instructions:
1. Fix all validation errors
2. Keep the same strategy name and indicators
3. Implement proper trading logic (not just pass/return False)
4. Use Jesse framework conventions (self.candles, ta.* indicators, etc.)
5. Return ONLY the fixed Python code, no explanations

Fix the code:"""

        headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}

        payload = {
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
        }

        response = requests.post(
            f"{LLM_ENDPOINT}/chat/completions", headers=headers, json=payload, timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            fixed_code = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            code_match = re.search(r"```python\n?(.*?)```", fixed_code, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()

            if "class " in fixed_code and "def should_long" in fixed_code:
                return fixed_code.strip()

        return None

    def _fix_with_templates(self, code: str, errors: List[Dict], result: Dict[str, Any]) -> str:
        """Fix validation errors using template-based approach."""
        errors_by_level = {e.get("level"): e for e in errors}

        if "syntax" in errors_by_level:
            code = self._fix_syntax_errors(code, errors_by_level["syntax"])

        if "imports" in errors_by_level:
            code = self._fix_import_errors(code, errors_by_level["imports"])

        if "structure" in errors_by_level:
            code = self._fix_structure_errors(code, errors_by_level["structure"])

        if "methods" in errors_by_level:
            code = self._fix_method_errors(code, errors_by_level["methods"])

        return code

    def _fix_syntax_errors(self, code: str, error: Dict) -> str:
        """Fix syntax errors."""
        error_msg = error.get("error", "")
        line = error.get("line", 0)

        if "expected ':'" in error_msg.lower():
            lines = code.split("\n")
            for i, ln in enumerate(lines):
                if "def " in ln or "if " in ln or "for " in ln or "while " in ln:
                    if (
                        ln.strip()
                        and not ln.strip().endswith(":")
                        and "#" not in ln.split("def ")[0]
                    ):
                        lines[i] = ln.rstrip() + ":"
            code = "\n".join(lines)

        return code

    def _fix_import_errors(self, code: str, error: Dict) -> str:
        """Fix import errors."""
        if "from jesse.strategies import Strategy" not in code:
            lines = code.split("\n")
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.startswith("import ") or line.startswith("from "):
                    new_lines.insert(-1, "from jesse.strategies import Strategy")
                    break
                if line.strip() == "" and not any(l.strip().startswith("from ") for l in new_lines):
                    new_lines.insert(-1, "from jesse.strategies import Strategy")
                    break
            if "from jesse.strategies import Strategy" not in "\n".join(new_lines):
                new_lines.insert(0, "from jesse.strategies import Strategy")
            code = "\n".join(new_lines)
        return code

    def _fix_structure_errors(self, code: str, error: Dict) -> str:
        """Fix structure errors."""
        class_match = re.search(r"class\s+(\w+)\s*\([^)]*\):", code)
        if class_match:
            class_name = class_match.group(1)
            code = re.sub(
                r"class\s+" + class_name + r"\s*\([^)]*\):", f"class {class_name}(Strategy):", code
            )
        return code

    def _fix_method_errors(self, code: str, error: Dict) -> str:
        """Fix method errors."""
        fix_hint = error.get("fix_hint", "")
        if "should_long" in fix_hint and "def should_long" not in code:
            code = self._add_method(code, "should_long", "return False")
        if "should_short" in fix_hint and "def should_short" not in code:
            code = self._add_method(code, "should_short", "return False")
        if "go_long" in fix_hint and "def go_long" not in code:
            code = self._add_method(code, "go_long", "pass")
        if "go_short" in fix_hint and "def go_short" not in code:
            code = self._add_method(code, "go_short", "pass")
        return code

    def _add_method(self, code: str, method_name: str, body: str) -> str:
        """Add a method to the strategy class."""
        indent = "    "
        new_method = f"\n{indent}def {method_name}(self) -> bool:\n{indent}    {body}"

        class_match = re.search(r"class\s+\w+\s*\(Strategy\):", code)
        if class_match:
            insert_pos = class_match.end()
            code = code[:insert_pos] + new_method + code[insert_pos:]
        return code

    def _add_missing_methods(self, code: str, methods: List[str]) -> str:
        """Add placeholder implementations for missing methods."""
        method_templates = {
            "should_long": """
    def should_long(self) -> bool:
        return False""",
            "should_short": """
    def should_short(self) -> bool:
        return False""",
            "go_long": """
    def go_long(self):
        pass""",
            "go_short": """
    def go_short(self):
        pass""",
            "should_cancel_entry": """
    def should_cancel_entry(self) -> bool:
        return True""",
        }

        for method in methods:
            if method in method_templates and method not in code:
                insert_pos = code.rfind("class ")
                class_end = code.find(":", insert_pos)
                next_class_or_end = code.find("\nclass ", class_end)
                if next_class_or_end == -1:
                    next_class_or_end = len(code)

                code = (
                    code[:next_class_or_end] + method_templates[method] + code[next_class_or_end:]
                )
                logger.info(f"Added missing method: {method}")

        return code

    def refine_from_error(self, code: str, error: str) -> str:
        """
        Refine strategy code based on runtime error.

        This is a placeholder that should be implemented by an LLM agent.
        The actual refinement requires understanding the specific runtime error.

        Args:
            code: Current strategy code
            error: Runtime error message

        Returns:
            Refined strategy code
        """
        self._refinement_count += 1
        logger.warning(
            f"⚠️ refine_from_error called (iteration {self._refinement_count}) - "
            "LLM refinement required"
        )
        logger.error(f"Runtime error: {error}")

        common_fixes = {
            "NameError": self._fix_name_error,
            "AttributeError": self._fix_attribute_error,
            "TypeError": self._fix_type_error,
            "IndexError": self._fix_index_error,
        }

        for error_type, fix_func in common_fixes.items():
            if error_type in error:
                logger.info(f"Attempting to fix {error_type}")
                return fix_func(code, error)

        return code

    def _fix_name_error(self, code: str, error: str) -> str:
        """Attempt to fix NameError."""
        import re

        name_match = re.search(r"name '(\w+)' is not defined", error)
        if name_match:
            undefined_name = name_match.group(1)
            logger.info(f"Found undefined name: {undefined_name}")

        return code

    def _fix_attribute_error(self, code: str, error: str) -> str:
        """Attempt to fix AttributeError."""
        import re

        attr_match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error)
        if attr_match:
            obj_name = attr_match.group(1)
            attr_name = attr_match.group(2)
            logger.info(f"Found missing attribute: {obj_name}.{attr_name}")

        return code

    def _fix_type_error(self, code: str, error: str) -> str:
        """Attempt to fix TypeError."""
        logger.info("TypeError detected - manual review recommended")
        return code

    def _fix_index_error(self, code: str, error: str) -> str:
        """Attempt to fix IndexError."""
        logger.info("IndexError detected - check array/candle access")
        return code

    def refinement_loop(
        self,
        code: str,
        spec: StrategySpec,
        max_iter: int = 5,
        progress_callback: Optional[Callable[[float, str, int], None]] = None,
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Run iterative refinement loop until validation passes or max iterations.

        Args:
            code: Initial strategy code
            spec: Strategy specification
            max_iter: Maximum refinement iterations
            progress_callback: Optional callback(percent, step, iteration)

        Returns:
            Tuple of (final_code, validation_history, success)
        """
        logger.info(f"Starting refinement loop (max {max_iter} iterations)")

        history: List[Dict[str, Any]] = []
        current_code = code
        success = False

        for iteration in range(max_iter):
            step = f"Validation iteration {iteration + 1}/{max_iter}"
            if progress_callback:
                progress = (iteration + 1) / max_iter
                progress_callback(progress, step, iteration)

            logger.info(f"🔍 {step}")

            spec_dict = {
                "name": spec.name,
                "strategy_type": spec.strategy_type,
                "timeframe": spec.timeframe,
            }
            result = self.validator.full_validation(current_code, spec_dict)
            history.append(
                {
                    "iteration": iteration + 1,
                    "result": result,
                    "code_length": len(current_code),
                }
            )

            if result.get("passed", False):
                success = True
                logger.info(f"✅ Validation passed at iteration {iteration + 1}")
                break

            logger.warning(f"❌ Validation failed at iteration {iteration + 1}")

            errors = result.get("errors", [])
            if errors:
                logger.warning(f"Errors: {errors[:3]}...")

            result["spec"] = {
                "name": spec.name,
                "description": spec.description,
                "strategy_type": spec.strategy_type,
                "indicators": spec.indicators,
                "timeframe": spec.timeframe,
            }
            current_code = self.refine_from_validation(current_code, result)

        if not success:
            logger.error(f"❌ Refinement loop exhausted after {max_iter} iterations")

        return current_code, history, success


def get_strategy_builder(validator: Optional["StrategyValidator"] = None) -> StrategyBuilder:
    """
    Factory function to get StrategyBuilder instance.

    Args:
        validator: Optional StrategyValidator instance

    Returns:
        StrategyBuilder instance
    """
    if validator is None:
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()

    return StrategyBuilder(validator)
