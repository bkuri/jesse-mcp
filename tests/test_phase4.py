#!/usr/bin/env python3
"""
Test Phase 4 Risk Analysis Tools
"""

import asyncio
import sys
import os
import pytest

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from jesse_mcp.phase4.risk_analyzer import get_risk_analyzer

    print("✅ Phase 4 risk analyzer imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Phase 4 risk analyzer: {e}")
    sys.exit(1)


@pytest.mark.asyncio
async def test_phase4_tools():
    """Test all Phase 4 tools"""
    print("🧪 Phase 4 Tools Test Suite")
    print("=" * 50)

    try:
        analyzer = get_risk_analyzer(use_mock=True)
        print(f"✅ Risk analyzer initialized (use_mock={analyzer.use_mock})")
    except Exception as e:
        print(f"❌ Failed to initialize risk analyzer: {e}")
        return False

    # Create mock backtest result for testing
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

    tests = [
        ("Monte Carlo", "monte_carlo"),
        ("VaR Calculation", "var_calculation"),
        ("Stress Test", "stress_test"),
        ("Risk Report", "risk_report"),
    ]

    results = []

    for test_name, method_name in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            method = getattr(analyzer, method_name)

            if test_name == "Monte Carlo":
                result = await method(
                    backtest_result=mock_backtest_result,
                    simulations=1000,  # Small for testing
                    confidence_levels=[0.95, 0.99],
                )
                success = "simulations" in result and result["simulations"] == 1000

            elif test_name == "VaR Calculation":
                result = await method(
                    backtest_result=mock_backtest_result,
                    confidence_levels=[0.90, 0.95],
                    time_horizons=[1, 5, 10],
                )
                success = "var_results" in result and len(result["var_results"]) == 6

            elif test_name == "Stress Test":
                result = await method(
                    backtest_result=mock_backtest_result,
                    scenarios=["market_crash", "volatility_spike"],
                )
                success = (
                    "stress_results" in result and len(result["stress_results"]) == 2
                )

            elif test_name == "Risk Report":
                result = await method(
                    backtest_result=mock_backtest_result,
                    include_monte_carlo=False,  # Skip for speed
                    include_var_analysis=False,  # Skip for speed
                    include_stress_test=False,  # Skip for speed
                    report_format="summary",
                )
                success = "report_type" in result and "risk" in result

            else:
                success = False

            if success:
                print(f"   ✅ {test_name} completed successfully")
                if test_name == "Monte Carlo":
                    print(f"      Simulations: {result.get('simulations', 0)}")
                    print(
                        f"      Probability of profit: {result.get('probability_of_profit', 0):.2%}"
                    )
                elif test_name == "VaR Calculation":
                    print(
                        f"      VaR calculations: {len(result.get('var_results', {}))}"
                    )
                elif test_name == "Stress Test":
                    print(
                        f"      Scenarios tested: {len(result.get('stress_results', {}))}"
                    )
                elif test_name == "Risk Report":
                    risk = result.get("risk", {})
                    print(f"      Risk level: {risk.get('level', 'Unknown')}")
                    print(f"      Risk rating: {risk.get('rating', 'N/A')}")
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
        print("🎉 All Phase 4 tools working correctly!")
        return True
    else:
        print("⚠️  Some tests failed - check implementation")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_phase4_tools())
    sys.exit(0 if success else 1)
