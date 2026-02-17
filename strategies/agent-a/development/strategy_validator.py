"""
Strategy Validation and Testing Framework
Agent A Strategy Development Implementation
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
import json
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from enhanced_sma_strategy import EnhancedSMAStrategy


class StrategyValidator:
    """
    Comprehensive strategy validation framework for Agent A development
    """

    def __init__(self):
        self.validation_results = {}
        self.test_data = None
        self.strategy = None

    def generate_test_data(self, days: int = 252) -> np.ndarray:
        """
        Generate synthetic OHLCV data for testing

        Args:
            days: Number of days of test data to generate

        Returns:
            OHLCV numpy array
        """
        np.random.seed(42)  # For reproducible results

        # Generate price series with trend and volatility
        returns = np.random.normal(0.0005, 0.02, days * 24)  # Hourly data

        # Add some trend
        trend = np.linspace(0, 0.3, len(returns))
        returns += trend / len(returns)

        # Generate price series
        prices = 100 * np.exp(np.cumsum(returns))

        # Generate OHLC data
        data = []
        for i in range(len(prices)):
            high = prices[i] * (1 + abs(np.random.normal(0, 0.01)))
            low = prices[i] * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i] * (1 + np.random.normal(0, 0.005))
            close = prices[i]
            volume = np.random.normal(1000000, 200000)

            data.append([i, open_price, high, low, close, max(volume, 100000)])

        return np.array(data)

    def validate_strategy_parameters(
        self, strategy: EnhancedSMAStrategy
    ) -> Dict[str, Any]:
        """
        Validate strategy parameters

        Args:
            strategy: Strategy instance to validate

        Returns:
            Validation results
        """
        results = {
            "test_name": "parameter_validation",
            "timestamp": datetime.now().isoformat(),
            "passed": True,
            "errors": [],
            "warnings": [],
        }

        # Test parameter validation
        is_valid, error_msg = strategy.validate_parameters()
        if not is_valid:
            results["passed"] = False
            results["errors"].append(f"Parameter validation failed: {error_msg}")

        # Test edge cases
        test_configs = [
            {"sma_fast": 50, "sma_slow": 20},  # Invalid: fast > slow
            {"sma_fast": 300, "sma_slow": 400},  # Invalid: periods too large
            {"position_size": 0.15},  # Invalid: position size too large
            {"stop_loss_pct": -0.01},  # Invalid: negative stop loss
        ]

        for config in test_configs:
            test_strategy = EnhancedSMAStrategy(config)
            is_valid, error_msg = test_strategy.validate_parameters()
            if is_valid:  # Should be invalid
                results["passed"] = False
                results["errors"].append(f"Invalid config passed validation: {config}")

        return results

    def validate_indicator_calculation(
        self, strategy: EnhancedSMAStrategy
    ) -> Dict[str, Any]:
        """
        Validate technical indicator calculations

        Args:
            strategy: Strategy instance to validate

        Returns:
            Validation results
        """
        results = {
            "test_name": "indicator_calculation",
            "timestamp": datetime.now().isoformat(),
            "passed": True,
            "errors": [],
            "warnings": [],
        }

        # Generate test data
        test_data = self.generate_test_data(100)

        # Calculate indicators
        indicators = strategy.calculate_indicators(test_data)

        # Check required indicators
        required_indicators = ["sma_fast", "sma_slow"]
        for indicator in required_indicators:
            if indicator not in indicators:
                results["passed"] = False
                results["errors"].append(f"Missing required indicator: {indicator}")

        # Validate indicator values
        if "sma_fast" in indicators and "sma_slow" in indicators:
            sma_fast = indicators["sma_fast"]
            sma_slow = indicators["sma_slow"]

            # Check for NaN values in recent data
            if np.isnan(sma_fast[-10:]).any():
                results["errors"].append(
                    "NaN values found in recent SMA fast calculations"
                )

            if np.isnan(sma_slow[-10:]).any():
                results["errors"].append(
                    "NaN values found in recent SMA slow calculations"
                )

            # Check SMA relationship (fast should be more responsive)
            if len(sma_fast) > 50 and len(sma_slow) > 50:
                fast_volatility = np.std(sma_fast[-50:])
                slow_volatility = np.std(sma_slow[-50:])

                if fast_volatility <= slow_volatility:
                    results["warnings"].append(
                        "Fast SMA should be more volatile than slow SMA"
                    )

        return results

    def validate_signal_generation(
        self, strategy: EnhancedSMAStrategy
    ) -> Dict[str, Any]:
        """
        Validate signal generation logic

        Args:
            strategy: Strategy instance to validate

        Returns:
            Validation results
        """
        results = {
            "test_name": "signal_generation",
            "timestamp": datetime.now().isoformat(),
            "passed": True,
            "errors": [],
            "warnings": [],
            "signal_stats": {},
        }

        # Generate test data
        test_data = self.generate_test_data(200)

        # Generate signals over time
        signals = []
        for i in range(100, len(test_data)):
            candles = test_data[: i + 1]
            signal = strategy.generate_signals(candles)
            signals.append(signal)

        # Analyze signals
        signal_actions = [s["action"] for s in signals]
        signal_counts = {
            action: signal_actions.count(action) for action in set(signal_actions)
        }
        results["signal_stats"] = signal_counts

        # Validate signal structure
        for signal in signals:
            required_fields = ["action", "confidence", "reason"]
            for field in required_fields:
                if field not in signal:
                    results["passed"] = False
                    results["errors"].append(
                        f"Missing required field in signal: {field}"
                    )

            # Validate confidence range
            if "confidence" in signal:
                if not (0 <= signal["confidence"] <= 100):
                    results["passed"] = False
                    results["errors"].append(
                        f"Invalid confidence value: {signal['confidence']}"
                    )

            # Validate action values
            if "action" in signal:
                valid_actions = ["long", "short", "hold"]
                if signal["action"] not in valid_actions:
                    results["passed"] = False
                    results["errors"].append(f"Invalid action: {signal['action']}")

        # Check for reasonable signal distribution
        total_signals = len(signals)
        if total_signals > 0:
            hold_ratio = signal_counts.get("hold", 0) / total_signals
            if hold_ratio < 0.5:  # Too many trading signals
                results["warnings"].append(
                    f"High trading frequency: {1 - hold_ratio:.2%} non-hold signals"
                )

        return results

    def validate_risk_management(self, strategy: EnhancedSMAStrategy) -> Dict[str, Any]:
        """
        Validate risk management features

        Args:
            strategy: Strategy instance to validate

        Returns:
            Validation results
        """
        results = {
            "test_name": "risk_management",
            "timestamp": datetime.now().isoformat(),
            "passed": True,
            "errors": [],
            "warnings": [],
        }

        # Test risk constraint checking
        strategy.current_drawdown = 0.1  # 10% drawdown
        if not strategy._check_risk_constraints():
            results["errors"].append(
                "Risk constraints incorrectly blocked 10% drawdown"
            )

        strategy.current_drawdown = 0.2  # 20% drawdown (exceeds 15% limit)
        if strategy._check_risk_constraints():
            results["passed"] = False
            results["errors"].append(
                "Risk constraints failed to block excessive drawdown"
            )

        # Test trade execution with risk parameters
        test_signal = {"action": "long", "confidence": 80.0, "reason": "test"}
        test_price = 100.0

        trade = strategy.execute_trade(test_signal, test_price)

        if trade:
            # Validate stop loss and take profit
            expected_stop_loss = test_price * (1 - strategy.stop_loss_pct)
            expected_take_profit = test_price * (1 + strategy.take_profit_pct)

            if abs(trade["stop_loss"] - expected_stop_loss) > 0.01:
                results["errors"].append("Stop loss calculation incorrect")

            if abs(trade["take_profit"] - expected_take_profit) > 0.01:
                results["errors"].append("Take profit calculation incorrect")

        return results

    def validate_performance_tracking(
        self, strategy: EnhancedSMAStrategy
    ) -> Dict[str, Any]:
        """
        Validate performance tracking capabilities

        Args:
            strategy: Strategy instance to validate

        Returns:
            Validation results
        """
        results = {
            "test_name": "performance_tracking",
            "timestamp": datetime.now().isoformat(),
            "passed": True,
            "errors": [],
            "warnings": [],
        }

        # Test performance metrics calculation
        metrics = strategy.get_performance_metrics()

        # Validate metrics structure
        expected_metrics = [
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
            "current_drawdown",
            "max_drawdown",
        ]

        for metric in expected_metrics:
            if metric not in metrics:
                results["errors"].append(f"Missing performance metric: {metric}")

        # Test with some simulated trades
        strategy.trades = [
            {"pnl": 100, "action": "long"},
            {"pnl": -50, "action": "short"},
            {"pnl": 75, "action": "long"},
        ]

        updated_metrics = strategy.get_performance_metrics()

        if updated_metrics["total_trades"] != 3:
            results["errors"].append("Trade count incorrect")

        if updated_metrics["winning_trades"] != 2:
            results["errors"].append("Winning trades count incorrect")

        if abs(updated_metrics["win_rate"] - 0.667) > 0.01:
            results["errors"].append("Win rate calculation incorrect")

        return results

    def run_comprehensive_validation(
        self, strategy: EnhancedSMAStrategy
    ) -> Dict[str, Any]:
        """
        Run all validation tests

        Args:
            strategy: Strategy instance to validate

        Returns:
            Comprehensive validation results
        """
        validation_suite = [
            self.validate_strategy_parameters,
            self.validate_indicator_calculation,
            self.validate_signal_generation,
            self.validate_risk_management,
            self.validate_performance_tracking,
        ]

        all_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "strategy_config": strategy.config,
            "overall_passed": True,
            "test_results": [],
            "summary": {
                "total_tests": len(validation_suite),
                "passed_tests": 0,
                "failed_tests": 0,
                "total_errors": 0,
                "total_warnings": 0,
            },
        }

        for validation_func in validation_suite:
            try:
                result = validation_func(strategy)
                all_results["test_results"].append(result)

                if result["passed"]:
                    all_results["summary"]["passed_tests"] += 1
                else:
                    all_results["summary"]["failed_tests"] += 1
                    all_results["overall_passed"] = False

                all_results["summary"]["total_errors"] += len(result["errors"])
                all_results["summary"]["total_warnings"] += len(result["warnings"])

            except Exception as e:
                error_result = {
                    "test_name": validation_func.__name__,
                    "timestamp": datetime.now().isoformat(),
                    "passed": False,
                    "errors": [f"Test execution failed: {str(e)}"],
                    "warnings": [],
                }
                all_results["test_results"].append(error_result)
                all_results["summary"]["failed_tests"] += 1
                all_results["overall_passed"] = False
                all_results["summary"]["total_errors"] += 1

        return all_results

    def save_validation_report(self, results: Dict[str, Any], filepath: str):
        """Save validation report to file"""
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)


def main():
    """Main validation execution"""
    print("🔍 Agent A Strategy Validation Started")
    print("=" * 50)

    # Initialize validator
    validator = StrategyValidator()

    # Create strategy with default configuration
    strategy = EnhancedSMAStrategy()

    # Run comprehensive validation
    results = validator.run_comprehensive_validation(strategy)

    # Display results
    print(
        f"📊 Overall Result: {'✅ PASSED' if results['overall_passed'] else '❌ FAILED'}"
    )
    print(
        f"📈 Tests Passed: {results['summary']['passed_tests']}/{results['summary']['total_tests']}"
    )
    print(f"🚨 Total Errors: {results['summary']['total_errors']}")
    print(f"⚠️  Total Warnings: {results['summary']['total_warnings']}")

    print("\n📋 Detailed Results:")
    for test_result in results["test_results"]:
        status = "✅ PASSED" if test_result["passed"] else "❌ FAILED"
        print(f"  {test_result['test_name']}: {status}")

        if test_result["errors"]:
            for error in test_result["errors"]:
                print(f"    ❌ Error: {error}")

        if test_result["warnings"]:
            for warning in test_result["warnings"]:
                print(f"    ⚠️  Warning: {warning}")

    # Save validation report
    report_path = "/home/bk/source/jesse-mcp/strategies/agent-a/development/validation_report.json"
    validator.save_validation_report(results, report_path)
    print(f"\n💾 Validation report saved to: {report_path}")

    return results["overall_passed"]


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
