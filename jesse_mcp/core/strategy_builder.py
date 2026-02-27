"""
Strategy Builder and Refinement Framework

Provides strategy generation and iterative refinement capabilities for
autonomous trading strategy development.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from jesse_mcp.core.strategy_validator import StrategyValidator

logger = logging.getLogger("jesse-mcp.strategy_builder")

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
        Refine strategy code based on validation errors.

        This is a placeholder that should be implemented by an LLM agent.
        The actual refinement logic requires understanding the specific errors.

        Args:
            code: Current strategy code
            result: Validation result containing errors

        Returns:
            Refined strategy code
        """
        self._refinement_count += 1
        logger.warning(
            f"⚠️ refine_from_validation called (iteration {self._refinement_count}) - "
            "LLM refinement required"
        )

        errors = result.get("errors", [])
        missing_methods = result.get("missing_methods", [])

        if missing_methods:
            logger.info(f"Missing methods detected: {missing_methods}")
            code = self._add_missing_methods(code, missing_methods)

        if result.get("syntax_error"):
            logger.error(f"Syntax error: {result['syntax_error']}")

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
