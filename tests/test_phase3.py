#!/usr/bin/env python3
"""
Test Phase 3 optimize() tool with mock data
"""

import asyncio
import json
import sys
import os
import pytest

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jesse_mcp.phase3.optimizer import get_optimizer


@pytest.mark.asyncio
async def test_optimize():
    """Test the optimize function with mock data"""
    print("🚀 Testing Phase 3 optimize() tool with mock data...")

    try:
        # Get optimizer (should use mock by default)
        optimizer = get_optimizer()
        print(f"✅ Optimizer initialized (use_mock={optimizer.use_mock})")

        # Define parameter space for optimization
        param_space = {
            "fast_period": {"type": "int", "min": 5, "max": 20, "step": 1},
            "slow_period": {"type": "int", "min": 20, "max": 50, "step": 1},
            "signal_period": {"type": "int", "min": 5, "max": 15, "step": 1},
        }

        print(f"📊 Parameter space: {json.dumps(param_space, indent=2)}")

        # Run optimization
        print("🔬 Starting optimization (20 trials for testing)...")
        result = await optimizer.optimize(
            strategy="SimpleMovingAverage",
            symbol="BTC-USDT",
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-03-01",
            param_space=param_space,
            metric="total_return",
            n_trials=20,  # Small number for testing
            n_jobs=1,
        )

        # Display results
        print("\n📈 Optimization Results:")
        print(f"  Strategy: {result['strategy']}")
        print(f"  Symbol: {result['symbol']}")
        print(f"  Timeframe: {result['timeframe']}")
        print(f"  Best Value: {result['best_value']:.4f}")
        print(f"  Best Parameters: {json.dumps(result['best_parameters'], indent=4)}")
        print(f"  Trials: {result['n_trials']}")
        print(f"  Successful Trials: {result['n_successful_trials']}")
        print(f"  Execution Time: {result['execution_time']}s")
        print(f"  Use Mock: {result['use_mock']}")

        # Show convergence data
        if result["convergence"]:
            print(f"\n📊 Convergence (first 5 trials):")
            for i, point in enumerate(result["convergence"][:5]):
                print(
                    f"  Trial {point['trial']}: {point['current_value']:.4f} (best: {point['best_value']:.4f})"
                )

        # Show final backtest results
        if "final_backtest" in result:
            final = result["final_backtest"]
            print(f"\n🎯 Final Backtest with Best Parameters:")
            print(f"  Total Return: {final.get('total_return', 0):.2%}")
            print(f"  Sharpe Ratio: {final.get('sharpe_ratio', 0):.2f}")
            print(f"  Max Drawdown: {final.get('max_drawdown', 0):.2%}")
            print(f"  Win Rate: {final.get('win_rate', 0):.2%}")
            print(f"  Total Trades: {final.get('total_trades', 0)}")

        print("\n✅ Optimization test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Optimization test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_walk_forward():
    """Test walk-forward analysis"""
    print("\n🔄 Testing walk_forward() tool...")

    try:
        optimizer = get_optimizer()

        # Simple parameter space for walk-forward
        param_space = {"period": {"type": "int", "min": 10, "max": 30, "step": 1}}

        result = await optimizer.walk_forward(
            strategy="SimpleMovingAverage",
            symbol="BTC-USDT",
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-06-01",
            in_sample_period=30,  # 30 days optimization
            out_sample_period=10,  # 10 days validation
            step_forward=15,  # Move forward 15 days
            param_space=param_space,
            metric="total_return",
        )

        print(f"  Periods Analyzed: {len(result['periods'])}")
        print(f"  Execution Time: {result['execution_time']}s")

        if result["overall"]:
            overall = result["overall"]
            print(
                f"  Positive Periods: {overall['positive_periods']}/{overall['total_periods']}"
            )
            print(f"  Average Degradation: {overall['average_degradation']:.2%}")
            print(f"  Overfitting Indicator: {overall['overfitting_indicator']}")

        print("✅ Walk-forward test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Walk-forward test failed: {e}")
        return False


@pytest.mark.asyncio
async def test_analyze_results():
    """Test results analysis"""
    print("\n📊 Testing analyze_results() tool...")

    try:
        optimizer = get_optimizer()

        # First run a simple backtest to get results
        backtest_result = optimizer.wrapper.backtest(
            strategy_name="SimpleMovingAverage",
            symbol="BTC-USDT",
            timeframe="1h",
            start_date="2024-01-01",
            end_date="2024-02-01",
        )

        # Analyze the results
        analysis = optimizer.analyze_results(
            backtest_result,
            analysis_type="basic",
            include_trade_analysis=True,
            include_monte_carlo=True,
        )

        print(f"  Analysis Type: {analysis['analysis_type']}")
        print(f"  Execution Time: {analysis['execution_time']}s")

        if "basic" in analysis:
            basic = analysis["basic"]
            print(f"  Performance Rating: {basic['performance_rating']}")
            print(f"  Total Return: {basic['total_return']:.2%}")
            print(f"  Sharpe Ratio: {basic['sharpe_ratio']:.2f}")

        if "trade_analysis" in analysis:
            trade = analysis["trade_analysis"]
            print(f"  Win Rate: {trade['win_rate']:.2%}")
            print(f"  Profit Factor: {trade['profit_factor']:.2f}")

        if "monte_carlo" in analysis:
            mc = analysis["monte_carlo"]
            print(f"  Monte Carlo Simulations: {mc['simulations']}")
            print(f"  Probability of Profit: {mc['probability_of_profit']:.2%}")

        print("✅ Results analysis test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Results analysis test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Phase 3 Tools Test Suite")
    print("=" * 50)

    tests = [
        ("Optimization", test_optimize),
        ("Walk-Forward", test_walk_forward),
        ("Results Analysis", test_analyze_results),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n🔍 Running {name} Test...")
        success = await test_func()
        results.append((name, success))

    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    passed = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {name}: {status}")
        if success:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All Phase 3 tools working correctly!")
        return 0
    else:
        print("⚠️  Some tests failed - check implementation")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
