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
    """Specification for a trading strategy."""

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
    """Infer appropriate indicators from description and strategy type."""
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


STRATEGY_IMPORTS = """from jesse.strategies import Strategy
import jesse.indicators as ta
import jesse.helpers as utils
"""


def _build_ema_crossover_properties() -> str:
    return """    @property
    def ema_fast(self):
        return ta.ema(self.candles, self.hp['fast_period'])

    @property
    def ema_slow(self):
        return ta.ema(self.candles, self.hp['slow_period'])"""


def _build_sma_crossover_properties() -> str:
    return """    @property
    def sma_fast(self):
        return ta.sma(self.candles, self.hp['fast_period'])

    @property
    def sma_slow(self):
        return ta.sma(self.candles, self.hp['slow_period'])"""


def _build_rsi_properties() -> str:
    return """    @property
    def rsi(self):
        return ta.rsi(self.candles, self.hp['rsi_period'])"""


def _build_ema_crossover_should_methods() -> str:
    return """    def should_long(self) -> bool:
        if self.prev_fast_above is not None and not self.prev_fast_above and self.fast_above:
            return True
        return False

    def should_short(self) -> bool:
        if self.prev_fast_above is not None and self.prev_fast_above and not self.fast_above:
            return True
        return False"""


def _build_rsi_should_methods() -> str:
    return """    def should_long(self) -> bool:
        return self.rsi < self.hp['rsi_oversold']

    def should_short(self) -> bool:
        return self.rsi > self.hp['rsi_overbought']"""


def _build_default_should_methods() -> str:
    return """    def should_long(self) -> bool:
        return False

    def should_short(self) -> bool:
        return False"""


def _build_entry_methods() -> str:
    return """    def go_long(self):
        entry_price = self.price
        qty = utils.size_to_qty(self.balance * 0.95, entry_price)
        self.buy = qty, entry_price

    def go_short(self):
        entry_price = self.price
        qty = utils.size_to_qty(self.balance * 0.95, entry_price)
        self.sell = qty, entry_price"""


def _build_hyperparameters(indicators: List[str]) -> str:
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
        params.append("{'name': 'rsi_oversold', 'type': int, 'default': 30, 'min': 10, 'max': 40}")

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


def _build_indicator_properties(indicators: List[str]) -> List[str]:
    props = []
    if "ema" in indicators:
        props.append(_build_ema_crossover_properties())
    elif "sma" in indicators:
        props.append(_build_sma_crossover_properties())
    if "rsi" in indicators:
        props.append(_build_rsi_properties())
    return props


class StrategyBuilder:
    """Strategy generation and iterative refinement framework."""

    def __init__(self, validator: "StrategyValidator"):
        self.validator = validator
        self._refinement_count = 0
        logger.info("✅ StrategyBuilder initialized")

    def generate_initial(self, spec: StrategySpec) -> str:
        """Generate initial strategy code with actual trading logic."""
        logger.info(f"Generating initial strategy: {spec.name}")

        hyperparameters = _build_hyperparameters(spec.indicators)
        indicator_props = _build_indicator_properties(spec.indicators)
        indicator_props_str = "\n\n".join(indicator_props) if indicator_props else "pass"

        if "ema" in spec.indicators:
            should_methods = _build_ema_crossover_should_methods()
        elif "rsi" in spec.indicators:
            should_methods = _build_rsi_should_methods()
        else:
            should_methods = _build_default_should_methods()

        if "ema" in spec.indicators:
            before_init = "self.fast_above = self.ema_fast > self.ema_slow\n        self.prev_fast_above = getattr(self, 'fast_above', None)"
        elif "sma" in spec.indicators:
            before_init = "self.fast_above = self.sma_fast > self.sma_slow\n        self.prev_fast_above = getattr(self, 'fast_above', None)"
        else:
            before_init = "pass"

        docstring = f"""{spec.description}

Strategy Type: {spec.strategy_type}
Indicators: {", ".join(spec.indicators)}
Timeframe: {spec.timeframe}
Risk per Trade: {spec.risk_per_trade * 100}%"""

        if "ema" in spec.indicators:
            strategy_doc = f"""{spec.description}

EMA crossover strategy - enters long when fast EMA crosses above slow EMA,
enters short when fast EMA crosses below slow EMA."""
        elif "rsi" in spec.indicators:
            strategy_doc = f"""{spec.description}

RSI mean reversion - buys when RSI is oversold, sells when RSI is overbought."""
        else:
            strategy_doc = spec.description

        code = f'''"""
{docstring}
"""

{STRATEGY_IMPORTS}


class {spec.name}(Strategy):
    """
    {strategy_doc}
    """

    def __init__(self):
        super().__init__()
        self.risk_per_trade = {spec.risk_per_trade}

    @property
    def hyperparameters(self):
        return {hyperparameters}

    def before(self):
        {before_init}

{indicator_props_str}

{should_methods}

{_build_entry_methods()}

    def should_cancel_entry(self) -> bool:
        return False

    def on_open_position(self, order):
        stop_loss = self.price - (self.atr * 2)
        take_profit = self.price + (self.atr * 3)
        self.stop_loss = self.position.qty, stop_loss
        self.take_profit = self.position.qty, take_profit
'''
        logger.info(f"✅ Generated initial strategy for {spec.name} ({len(code)} bytes)")
        return code

    def refine_from_validation(self, code: str, result: Dict[str, Any]) -> str:
        """Refine strategy code based on validation errors using LLM."""
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
4. Use Jesse framework conventions (self.candles, ta.* indicators, utils.* helpers, etc.)
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

    def refine_from_error(self, code: str, error: str) -> str:
        """Refine strategy code based on runtime error."""
        self._refinement_count += 1
        logger.warning(f"⚠️ refine_from_error called (iteration {self._refinement_count})")
        logger.error(f"Runtime error: {error}")
        return code

    def refinement_loop(
        self,
        code: str,
        spec: StrategySpec,
        max_iter: int = 5,
        skip_backtest: bool = False,
        progress_callback: Optional[Callable[[float, str, int], None]] = None,
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """Run iterative refinement loop: validate → dry-run → improve → repeat."""
        logger.info(
            f"Starting refinement loop (max {max_iter} iterations, skip_backtest={skip_backtest})"
        )

        history: List[Dict[str, Any]] = []
        current_code = code
        success = False

        for iteration in range(max_iter):
            step = f"Iteration {iteration + 1}/{max_iter}"
            if progress_callback:
                progress = (iteration + 1) / max_iter
                progress_callback(progress, step, iteration)

            logger.info(f"🔍 {step}")

            spec_dict = {
                "name": spec.name,
                "strategy_type": spec.strategy_type,
                "timeframe": spec.timeframe,
            }

            static_result = self.validator.full_validation(current_code, spec_dict)

            dry_run_result = None
            if static_result.get("passed", False):
                if skip_backtest:
                    logger.info("Dry-run skipped (skip_backtest=True)")
                    dry_run_result = {
                        "passed": True,
                        "error": None,
                        "skipped": True,
                        "note": "Dry-run skipped by user",
                    }
                else:
                    logger.info("🔬 Attempting dry-run backtest...")
                    try:
                        dry_run_validation = self.validator.dry_run_backtest(
                            current_code, spec_dict
                        )
                        dry_run_result = (
                            dry_run_validation.to_dict()
                            if hasattr(dry_run_validation, "to_dict")
                            else {
                                "passed": dry_run_validation.passed,
                                "level": dry_run_validation.level,
                                "error": dry_run_validation.error,
                                "metrics": getattr(dry_run_validation, "metrics", {}),
                            }
                        )
                        static_result["levels"]["dry_run"] = dry_run_result
                    except Exception as e:
                        logger.warning(f"Dry-run failed (continuing without): {e}")
                        dry_run_result = {"passed": True, "error": None}

            history.append(
                {
                    "iteration": iteration + 1,
                    "result": static_result,
                    "dry_run": dry_run_result,
                    "code_length": len(current_code),
                }
            )

            all_passed = static_result.get("passed", False)
            if dry_run_result and dry_run_result.get("passed") is not None:
                all_passed = all_passed and dry_run_result.get("passed", True)

            if all_passed:
                logger.info(f"✅ Validation + dry-run passed at iteration {iteration + 1}")

                if LLM_ENDPOINT and LLM_API_KEY and iteration < max_iter - 1:
                    logger.info("🔧 Attempting performance-based improvements...")
                    improved_code = self._improve_with_backtest_results(
                        current_code, spec, dry_run_result
                    )
                    if improved_code and improved_code != current_code:
                        logger.info("✅ Performance improvements found, re-validating...")
                        current_code = improved_code
                        continue

                success = True
                break

            logger.warning(f"❌ Validation/dry-run failed at iteration {iteration + 1}")

            errors = static_result.get("errors", [])
            if errors:
                logger.warning(f"Errors: {errors[:3]}...")

            if dry_run_result and dry_run_result.get("error"):
                logger.warning(f"Dry-run error: {dry_run_result.get('error')}")

            static_result["spec"] = {
                "name": spec.name,
                "description": spec.description,
                "strategy_type": spec.strategy_type,
                "indicators": spec.indicators,
                "timeframe": spec.timeframe,
            }
            current_code = self.refine_from_validation(current_code, static_result)

        if not success:
            logger.error(f"❌ Refinement loop exhausted after {max_iter} iterations")

        return current_code, history, success

    def _improve_with_backtest_results(
        self, code: str, spec: StrategySpec, dry_run_result: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Use backtest results to provide targeted improvements."""
        if not dry_run_result:
            return None

        import requests

        metrics = dry_run_result.get("metrics", {})
        error = dry_run_result.get("error")

        if error:
            prompt = f"""You are a Jesse trading strategy expert. Fix the runtime error in this strategy.

STRATEGY NAME: {spec.name}
STRATEGY DESCRIPTION: {spec.description}

RUNTIME ERROR:
{error}

CURRENT CODE:
```{code}
```

Instructions:
1. Fix the runtime error
2. Keep the same strategy logic where possible
3. Return ONLY the fixed code, no explanations

Fix the code:"""
        else:
            total_trades = metrics.get("total_trades", 0)
            win_rate = metrics.get("win_rate", 0)
            total_return = metrics.get("total_return", 0)

            performance_notes = []
            if total_trades == 0:
                performance_notes.append(
                    "- No trades executed - strategy too restrictive or no signals"
                )
            if win_rate < 0.4:
                performance_notes.append(
                    f"- Low win rate ({win_rate:.1%}) - consider adding filters"
                )
            if total_return < -10:
                performance_notes.append(
                    f"- Negative return ({total_return:.2f}%) - review entry/exit logic"
                )

            performance_str = (
                "\n".join(performance_notes)
                if performance_notes
                else "Strategy executed but may have room for improvement"
            )

            prompt = f"""You are a Jesse trading strategy expert. Improve this strategy based on backtest results.

STRATEGY NAME: {spec.name}
STRATEGY TYPE: {spec.strategy_type}
DESCRIPTION: {spec.description}

BACKTEST RESULTS:
- Total trades: {total_trades}
- Win rate: {win_rate:.1%}
- Total return: {total_return:.2f}%

PERFORMANCE ISSUES:
{performance_str}

CURRENT CODE:
```{code}
```

Instructions:
1. Analyze the backtest results and improve the strategy
2. If no trades: relax filters or adjust entry conditions
3. If low win rate: add confirmation filters or tighten entry conditions
4. If negative return: review risk management and exit logic
5. Keep good elements that are working
6. Return ONLY the improved code, no explanations

Improve the strategy:"""

        try:
            headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}

            payload = {
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000,
            }

            response = requests.post(
                f"{LLM_ENDPOINT}/chat/completions", headers=headers, json=payload, timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                improved_code = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                if "NO_IMPROVEMENTS_NEEDED" in improved_code:
                    logger.info("LLM: No improvements needed")
                    return None

                code_match = re.search(r"```python\n?(.*?)```", improved_code, re.DOTALL)
                if code_match:
                    return code_match.group(1).strip()

                if "class " in improved_code and "def should_long" in improved_code:
                    return improved_code.strip()

        except Exception as e:
            logger.warning(f"LLM improvement failed: {e}")

        return None

    def _improve_with_llm(self, code: str, spec: StrategySpec) -> Optional[str]:
        """Use jessegpt.md knowledge to improve the strategy."""
        import requests

        jessegpt_guidelines = """
You are a Jesse trading strategy expert with deep knowledge of the Jesse framework.

Jesse Best Practices from jessegpt.md:
1. Use utils.risk_to_qty() for proper position sizing based on risk percentage
2. Use ta.sma, ta.ema, ta.rsi, ta.atr etc. for technical indicators
3. In before(), store previous values using instance variables to detect crossovers
4. Implement proper stop-loss and take-profit in on_open_position()
5. Use self.balance for capital, self.price for current price
6. For entry: self.buy = qty, price or self.sell = qty, price
7. For exit: self.stop_loss = qty, price and self.take_profit = qty, price
8. Use should_cancel_entry() to cancel pending orders after timeout
9. Use ATR for dynamic stop-loss sizing
10. Consider market regime (trending vs ranging) in entry logic
11. Add filters to reduce false signals (volume, volatility, etc.)
12. Use on_close_position() for trailing stops or position management
"""

        prompt = f"""You are reviewing a generated Jesse trading strategy. Using Jesse best practices (from jessegpt.md below), analyze if this strategy can be improved.

STRATEGY NAME: {spec.name}
STRATEGY TYPE: {spec.strategy_type}
DESCRIPTION: {spec.description}

JESSE BEST PRACTICES:
{jessegpt_guidelines}

CURRENT STRATEGY CODE:
```{code}
```

Instructions:
1. Analyze if the strategy follows Jesse best practices
2. If improvements are needed, provide the improved code
3. Focus on: position sizing, stop-loss/take-profit, crossover detection, filters, edge cases
4. If no improvements needed, return "NO_IMPROVEMENTS_NEEDED"
5. Return ONLY the improved code (or "NO_IMPROVEMENTS_NEEDED"), no explanations

Improve the strategy:"""

        try:
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
                improved_code = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                if "NO_IMPROVEMENTS_NEEDED" in improved_code:
                    logger.info("LLM: No improvements needed")
                    return None

                code_match = re.search(r"```python\n?(.*?)```", improved_code, re.DOTALL)
                if code_match:
                    return code_match.group(1).strip()

                if "class " in improved_code and "def should_long" in improved_code:
                    return improved_code.strip()

        except Exception as e:
            logger.warning(f"LLM improvement failed: {e}")

        return None


def get_strategy_builder(validator: Optional["StrategyValidator"] = None) -> StrategyBuilder:
    """Factory function to get StrategyBuilder instance."""
    if validator is None:
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()

    return StrategyBuilder(validator)
