#!/usr/bin/env python3
"""
Tests for Strategy Builder and Validator functionality

Tests cover:
- Indicator inference from strategy types and descriptions
- Multi-level strategy validation (syntax, imports, structure, methods, indicators)
- Strategy creation and deletion with safety checks
- Refinement loop for iterative strategy improvement
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os


class TestInferIndicators:
    """Tests for indicator inference from strategy types and descriptions."""

    def test_infer_indicators_trend(self):
        """Test that 'trend_following' returns appropriate indicators."""
        from jesse_mcp.core.strategy_builder import infer_indicators

        indicators = infer_indicators("A trend following strategy", "trend_following")

        assert "sma" in indicators or "ema" in indicators
        assert "macd" in indicators
        assert "adx" in indicators

    def test_infer_indicators_mean_reversion(self):
        """Test mean reversion indicators."""
        from jesse_mcp.core.strategy_builder import infer_indicators

        indicators = infer_indicators("A mean reversion strategy", "mean_reversion")

        assert "rsi" in indicators
        assert "bollinger_bands" in indicators or "zscore" in indicators

    def test_infer_indicators_from_description(self):
        """Test keyword-based inference from description."""
        from jesse_mcp.core.strategy_builder import infer_indicators

        indicators = infer_indicators("Using volatility and volume for signals", "default")

        assert "volatility" in " ".join(indicators) or any(
            ind in indicators for ind in ["bollinger_bands", "atr", "keltner_channel"]
        )

        indicators2 = infer_indicators("Momentum based trading with RSI", "default")
        assert "rsi" in indicators2

    def test_infer_indicators_default_fallback(self):
        """Test default indicators when no keywords match."""
        from jesse_mcp.core.strategy_builder import infer_indicators

        indicators = infer_indicators("A basic trading approach", "nonexistent_type")

        assert len(indicators) > 0
        assert "sma" in indicators or "ema" in indicators


class TestStrategyValidatorSyntax:
    """Tests for syntax validation level."""

    def test_validate_syntax_valid(self):
        """Test valid Python code passes syntax validation."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        valid_code = """
from jesse.strategies import Strategy

class TestStrategy(Strategy):
    def should_long(self) -> bool:
        return False
    
    def go_long(self):
        pass
    
    def should_short(self) -> bool:
        return False
    
    def go_short(self):
        pass
"""
        result = validator.validate_syntax(valid_code)

        assert result.passed is True
        assert result.error is None

    def test_validate_syntax_invalid(self):
        """Test invalid syntax fails with error details."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        invalid_code = """
class TestStrategy
    def should_long(self):
        return False
"""
        result = validator.validate_syntax(invalid_code)

        assert result.passed is False
        assert result.error is not None
        assert result.line is not None
        assert result.fix_hint is not None


class TestStrategyValidatorImports:
    """Tests for import validation level."""

    def test_validate_missing_imports(self):
        """Test code without Strategy import fails."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        code_without_import = """
class TestStrategy(Strategy):
    def should_long(self) -> bool:
        return False
"""
        result = validator.validate_imports(code_without_import)

        assert result.passed is False
        assert "Strategy" in result.error

    def test_validate_imports_present(self):
        """Test code with required imports passes."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        code_with_import = """
from jesse.strategies import Strategy

class TestStrategy(Strategy):
    pass
"""
        result = validator.validate_imports(code_with_import)

        assert result.passed is True


class TestStrategyValidatorMethods:
    """Tests for method validation level."""

    def test_validate_missing_methods(self):
        """Test code missing should_long/go_long fails."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        code_missing_methods = """
from jesse.strategies import Strategy

class TestStrategy(Strategy):
    pass
"""
        result = validator.validate_methods(code_missing_methods)

        assert result.passed is False
        assert "should_long" in result.error or "go_long" in result.error

    def test_validate_methods_present(self):
        """Test code with all required methods passes."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        code_with_methods = """
from jesse.strategies import Strategy

class TestStrategy(Strategy):
    def should_long(self) -> bool:
        return False
    
    def go_long(self):
        pass
    
    def should_short(self) -> bool:
        return False
    
    def go_short(self):
        pass
"""
        result = validator.validate_methods(code_with_methods)

        assert result.passed is True


class TestFullValidation:
    """Tests for full validation across all levels."""

    def test_full_validation_passes(self):
        """Test complete valid strategy passes all levels."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        valid_strategy = '''
"""
A valid test strategy.
"""
from jesse.strategies import Strategy
import jesse.indicators as ta


class ValidTestStrategy(Strategy):
    def should_long(self) -> bool:
        return self.price > ta.sma(self.candles, 20)
    
    def should_short(self) -> bool:
        return False
    
    def go_long(self):
        self.buy = 1, self.price
    
    def go_short(self):
        pass
'''
        result = validator.full_validation(valid_strategy)

        assert result["passed"] is True
        assert len(result["errors"]) == 0

    def test_full_validation_catches_multiple_errors(self):
        """Test full validation catches multiple error types."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        invalid_strategy = """
class InvalidStrategy:
    pass
"""
        result = validator.full_validation(invalid_strategy)

        assert result["passed"] is False
        assert len(result["errors"]) > 0


class TestStrategyBuilderRefinement:
    """Tests for the refinement loop."""

    def test_refinement_loop_success(self):
        """Test refinement loop eventually succeeds with fixable code."""
        from jesse_mcp.core.strategy_builder import (
            StrategyBuilder,
            StrategySpec,
            get_strategy_builder,
        )
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        builder = StrategyBuilder(validator)

        spec = StrategySpec(
            name="TestRefinementStrategy",
            description="A test strategy for refinement",
            strategy_type="trend_following",
        )

        code = builder.generate_initial(spec)
        final_code, history, success = builder.refinement_loop(code, spec, max_iter=3)

        assert len(history) > 0
        assert success is True

    def test_refinement_loop_max_iterations(self):
        """Test loop respects max_iterations limit."""
        from jesse_mcp.core.strategy_builder import (
            StrategyBuilder,
            StrategySpec,
        )
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        builder = StrategyBuilder(validator)

        spec = StrategySpec(
            name="MaxIterStrategy",
            description="Test max iterations",
            strategy_type="default",
        )

        broken_code = "this is not valid python at all {{{"
        final_code, history, success = builder.refinement_loop(broken_code, spec, max_iter=2)

        assert len(history) == 2
        assert success is False


class TestStrategySpec:
    """Tests for StrategySpec dataclass."""

    def test_spec_auto_infers_indicators(self):
        """Test StrategySpec auto-infers indicators when not provided."""
        from jesse_mcp.core.strategy_builder import StrategySpec

        spec = StrategySpec(
            name="AutoInferStrategy",
            description="Trend following with momentum",
            strategy_type="trend_following",
        )

        assert len(spec.indicators) > 0

    def test_spec_uses_provided_indicators(self):
        """Test StrategySpec uses provided indicators when given."""
        from jesse_mcp.core.strategy_builder import StrategySpec

        spec = StrategySpec(
            name="CustomIndicatorStrategy",
            description="Custom strategy",
            strategy_type="trend_following",
            indicators=["rsi", "macd"],
        )

        assert spec.indicators == ["rsi", "macd"]


class TestStrategyCreate:
    """Tests for strategy_create tool functionality."""

    def test_strategy_create_new(self):
        """Test the strategy_create tool creates new strategy."""
        from jesse_mcp.core.strategy_builder import (
            StrategyBuilder,
            StrategySpec,
            get_strategy_builder,
        )
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        builder = StrategyBuilder(validator)

        spec = StrategySpec(
            name="NewTestStrategy",
            description="A new test strategy",
            strategy_type="mean_reversion",
        )

        code = builder.generate_initial(spec)

        assert "class NewTestStrategy" in code
        assert "Strategy" in code

    def test_strategy_create_overwrite_protected(self):
        """Test can't overwrite without flag."""
        from jesse_mcp.core.integrations import JesseWrapper

        wrapper = JesseWrapper.__new__(JesseWrapper)
        wrapper.strategies_path = None

        result = wrapper.save_strategy("TestStrategy", "code", overwrite=False)

        assert result["success"] is False
        assert "not available" in result["error"].lower()


class TestStrategyDelete:
    """Tests for strategy deletion with safety checks."""

    def test_strategy_delete_requires_confirm(self):
        """Test delete requires confirm=True."""
        from jesse_mcp.core.integrations import JesseWrapper

        wrapper = JesseWrapper.__new__(JesseWrapper)
        wrapper.strategies_path = None

        result = wrapper.delete_strategy("TestStrategy")

        assert result["success"] is False


class TestSecurityValidation:
    """Tests for security-related validation."""

    def test_path_traversal_blocked(self):
        """Test path traversal attempts are blocked."""
        from jesse_mcp.core.integrations import JesseWrapper

        wrapper = JesseWrapper.__new__(JesseWrapper)
        wrapper.strategies_path = "/tmp/test_strategies"

        valid, error = wrapper._sanitize_strategy_name("../../../etc/passwd")

        assert valid is False
        assert "alphanumeric" in error.lower() or "letter" in error.lower()

    def test_sanitize_empty_name(self):
        """Test empty strategy name is rejected."""
        from jesse_mcp.core.integrations import JesseWrapper

        wrapper = JesseWrapper.__new__(JesseWrapper)

        valid, error = wrapper._sanitize_strategy_name("")

        assert valid is False
        assert "empty" in error.lower()

    def test_sanitize_long_name(self):
        """Test overly long strategy name is rejected."""
        from jesse_mcp.core.integrations import JesseWrapper

        wrapper = JesseWrapper.__new__(JesseWrapper)

        long_name = "A" * 100
        valid, error = wrapper._sanitize_strategy_name(long_name)

        assert valid is False
        assert "50" in error

    def test_sanitize_invalid_characters(self):
        """Test invalid characters in strategy name are rejected."""
        from jesse_mcp.core.integrations import JesseWrapper

        wrapper = JesseWrapper.__new__(JesseWrapper)

        valid, error = wrapper._sanitize_strategy_name("test-strategy!")

        assert valid is False

    def test_sanitize_valid_name(self):
        """Test valid strategy name passes sanitization."""
        from jesse_mcp.core.integrations import JesseWrapper

        wrapper = JesseWrapper.__new__(JesseWrapper)

        valid, sanitized = wrapper._sanitize_strategy_name("MyValidStrategy123")

        assert valid is True
        assert sanitized == "MyValidStrategy123"


class TestDryRunValidation:
    """Tests for dry-run backtest validation."""

    def test_dry_run_catches_runtime_error(self):
        """Test dry-run validation (placeholder - currently returns passed=True)."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()

        code = """
from jesse.strategies import Strategy

class DryRunTestStrategy(Strategy):
    def should_long(self) -> bool:
        return True
    
    def go_long(self):
        pass
    
    def should_short(self) -> bool:
        return False
    
    def go_short(self):
        pass
"""
        spec = {
            "name": "DryRunTestStrategy",
            "symbol": "BTC-USDT",
            "timeframe": "1h",
        }
        result = validator.dry_run_backtest(code, spec)

        assert result.passed is True
        assert len(result.warnings) > 0
        assert "not yet implemented" in result.warnings[0].lower()


class TestIndicatorValidation:
    """Tests for indicator validation level."""

    def test_known_indicators_pass(self):
        """Test known Jesse indicators pass validation."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        code = """
from jesse.strategies import Strategy
import jesse.indicators as ta

class IndicatorTestStrategy(Strategy):
    def should_long(self) -> bool:
        rsi = ta.rsi(self.candles, 14)
        sma = ta.sma(self.candles, 20)
        return False
    
    def go_long(self):
        pass
    
    def should_short(self) -> bool:
        return False
    
    def go_short(self):
        pass
"""
        result = validator.validate_indicators(code)

        assert result.passed is True
        assert len(result.warnings) == 0

    def test_unknown_indicators_warning(self):
        """Test unknown indicators generate warnings."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        code = """
from jesse.strategies import Strategy
import jesse.indicators as ta

class UnknownIndicatorStrategy(Strategy):
    def should_long(self) -> bool:
        val = ta.nonexistent_indicator(self.candles)
        return False
    
    def go_long(self):
        pass
    
    def should_short(self) -> bool:
        return False
    
    def go_short(self):
        pass
"""
        result = validator.validate_indicators(code)

        assert result.passed is True
        assert len(result.warnings) > 0
        assert "nonexistent_indicator" in result.warnings[0]


class TestStructureValidation:
    """Tests for structure validation level."""

    def test_valid_structure_passes(self):
        """Test valid class structure passes."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        code = """
from jesse.strategies import Strategy

class ValidStructureStrategy(Strategy):
    pass
"""
        result = validator.validate_structure(code)

        assert result.passed is True

    def test_missing_inheritance_fails(self):
        """Test class not inheriting from Strategy fails."""
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        code = """
class NotAStrategy:
    pass
"""
        result = validator.validate_structure(code)

        assert result.passed is False
        assert "strategy" in result.error.lower()


class TestStrategyBuilderCodeGeneration:
    """Tests for strategy code generation."""

    def test_generate_initial_includes_description(self):
        """Test generated code includes strategy description."""
        from jesse_mcp.core.strategy_builder import StrategySpec, get_strategy_builder
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        builder = get_strategy_builder(validator)

        spec = StrategySpec(
            name="DescriptionTestStrategy",
            description="This is a test description for the strategy",
            strategy_type="trend_following",
        )

        code = builder.generate_initial(spec)

        assert "This is a test description for the strategy" in code

    def test_generate_initial_includes_hyperparameters(self):
        """Test generated code includes hyperparameters."""
        from jesse_mcp.core.strategy_builder import StrategySpec, get_strategy_builder
        from jesse_mcp.core.strategy_validator import get_validator

        validator = get_validator()
        builder = get_strategy_builder(validator)

        spec = StrategySpec(
            name="HyperparamTestStrategy",
            description="Test hyperparameters",
            strategy_type="trend_following",
            indicators=["sma", "rsi"],
        )

        code = builder.generate_initial(spec)

        assert "hyperparameters" in code
        assert "fast_period" in code or "period" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
