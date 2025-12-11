#!/usr/bin/env python3
"""
Test Phase 5 Pairs Trading & Advanced Analysis Tools
"""

import asyncio
import sys
import os
import pytest

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from jesse_mcp.pairs_analyzer import get_pairs_analyzer

    print("✅ Phase 5 pairs analyzer imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Phase 5 pairs analyzer: {e}")
    sys.exit(1)


@pytest.mark.asyncio
async def test_phase5_tools():
    """Test all Phase 5 tools"""
    print("🧪 Phase 5 Tools Test Suite")
    print("=" * 50)

    try:
        analyzer = get_pairs_analyzer(use_mock=True)
        print(f"✅ Pairs analyzer initialized (use_mock={analyzer.use_mock})")
    except Exception as e:
        print(f"❌ Failed to initialize pairs analyzer: {e}")
        return False

    # Mock backtest results for testing
    mock_backtest_result = {
        "strategy": "TestStrategy",
        "symbol": "BTC-USDT",
        "timeframe": "1h",
        "start_date": "2024-01-01",
        "end_date": "2024-02-01",
        "total_return": 0.15,
        "sharpe_ratio": 1.2,
        "max_drawdown": 0.1,
        "win_rate": 0.55,
        "total_trades": 50,
        "equity_curve": [
            {"date": "2024-01-01", "return": 0.01, "equity": 10010},
            {"date": "2024-01-02", "return": -0.02, "equity": 9980},
            {"date": "2024-01-03", "return": 0.03, "equity": 10010},
            {"date": "2024-01-04", "return": 0.01, "equity": 10040},
            {"date": "2024-01-05", "return": 0.02, "equity": 10060},
        ],
    }

    # Create multiple backtest results for correlation
    backtest_results = [
        {**mock_backtest_result, "symbol": "BTC-USDT"},
        {**mock_backtest_result, "symbol": "ETH-USDT", "total_return": 0.12},
        {**mock_backtest_result, "symbol": "SOL-USDT", "total_return": 0.18},
    ]

    tests = [
        ("Correlation Matrix", "correlation_matrix"),
        ("Pairs Backtest", "pairs_backtest"),
        ("Factor Analysis", "factor_analysis"),
        ("Regime Detector", "regime_detector"),
    ]

    results = []

    for test_name, method_name in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            method = getattr(analyzer, method_name)

            if test_name == "Correlation Matrix":
                result = await method(
                    backtest_results=backtest_results,
                    lookback_period=60,
                    correlation_threshold=0.7,
                    include_rolling=True,
                )
                success = "summary" in result and "pairs" in result and len(result["pairs"]) > 0

            elif test_name == "Pairs Backtest":
                result = await method(
                    pair={"symbol1": "BTC-USDT", "symbol2": "ETH-USDT"},
                    strategy="mean_reversion",
                    backtest_result_1=backtest_results[0],
                    backtest_result_2=backtest_results[1],
                    lookback_period=60,
                    entry_threshold=2.0,
                    exit_threshold=0.5,
                )
                success = (
                    "pair" in result and "total_trades" in result and result["total_trades"] > 0
                )

            elif test_name == "Factor Analysis":
                result = await method(
                    backtest_result=mock_backtest_result,
                    factors=["market", "size", "momentum", "value"],
                    include_residuals=True,
                )
                success = "factor_attribution" in result and len(result["factor_attribution"]) == 5

            elif test_name == "Regime Detector":
                result = await method(
                    backtest_results=backtest_results,
                    lookback_period=60,
                    detection_method="hmm",
                    n_regimes=3,
                    include_transitions=True,
                    include_forecast=True,
                )
                success = (
                    "current_regime" in result
                    and "regimes" in result
                    and len(result["regimes"]) == 3
                )

            else:
                success = False

            if success:
                print(f"   ✅ {test_name} completed successfully")
                if test_name == "Correlation Matrix":
                    print(f"      Assets analyzed: {len(result['summary']['symbols'])}")
                    print(f"      Correlated pairs: {len(result['pairs'])}")
                    print(
                        f"      Average correlation: {result['summary']['average_correlation']:.3f}"
                    )
                elif test_name == "Pairs Backtest":
                    print(f"      Total trades: {result['total_trades']}")
                    print(f"      Win rate: {result['win_rate']:.1%}")
                    print(f"      Sharpe ratio: {result['sharpe_ratio']:.2f}")
                elif test_name == "Factor Analysis":
                    print(
                        f"      Factors analyzed: {len([k for k in result['factor_attribution'].keys() if k != 'residual'])}"
                    )
                    print(f"      R-squared: {result['model_statistics']['r_squared']:.2%}")
                    print(
                        f"      Model significance: {result['model_statistics']['model_significance']}"
                    )
                elif test_name == "Regime Detector":
                    print(f"      Current regime: {result['current_regime']['regime']}")
                    print(f"      Regimes identified: {len(result['regimes'])}")
                    print(f"      Confidence: {result['current_regime']['confidence']}")
            else:
                print(f"   ❌ {test_name} failed")
                if "error" in result:
                    print(f"      Error: {result['error']}")

            results.append((test_name, success))

        except Exception as e:
            print(f"   ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Phase 5 tools working correctly!")
        return True
    else:
        print("⚠️  Some tests failed - check implementation")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_phase5_tools())
    sys.exit(0 if success else 1)
