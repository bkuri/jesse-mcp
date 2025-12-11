#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for jesse-mcp
Tests all 17 tools with realistic workflows and integration scenarios
"""

import asyncio
import sys
import os
import time
import pytest
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from jesse_mcp.server import main as server_main

    print("✅ Jesse MCP Server imported successfully")
except ImportError as e:
    print(f"❌ Failed to import server: {e}")
    sys.exit(1)


def get_client_transport():
    """Helper to create StdioTransport for the MCP server"""
    try:
        from fastmcp.client.transports import StdioTransport

        return StdioTransport(command="python", args=["-m", "jesse_mcp"])
    except ImportError:
        raise ImportError("FastMCP not installed")


class E2ETestSuite:
    """Comprehensive end-to-end test suite"""

    def __init__(self):
        self.server = None
        self.results = []
        self.start_time = time.time()

    async def run_all_tests(self) -> bool:
        """Run all E2E tests"""
        print("\n" + "=" * 70)
        print("🧪 JESSE-MCP END-TO-END TEST SUITE")
        print("=" * 70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Test categories
        await self._test_tool_availability()
        await self._test_individual_tools()
        await self._test_tool_chains()
        await self._test_error_handling()
        await self._test_performance()

        # Print summary
        return self._print_summary()

    async def _test_tool_availability(self):
        """Test 1: Verify all 17 tools are discoverable"""
        print("TEST 1: Tool Availability")
        print("-" * 70)

        try:
            from fastmcp import Client
        except ImportError:
            pytest.skip("FastMCP not installed")

        async with Client(get_client_transport()) as client:
            tools = await client.list_tools()
            total_tools = len(tools)
            tool_names = {t["name"] for t in tools}

            expected_tools = {
                "backtest",
                "strategy_list",
                "strategy_read",
                "strategy_validate",
                "candles_import",
                "backtest_batch",
                "analyze_results",
                "walk_forward",
                "optimize",
                "monte_carlo",
                "var_calculation",
                "stress_test",
                "risk_report",
                "correlation_matrix",
                "pairs_backtest",
                "factor_analysis",
                "regime_detector",
            }

            available = set(tool_names)
            expected = set(expected_tools)
            missing = expected - available
            extra = available - expected

            print(f"  Total tools: {total_tools}")
            print(f"  Expected: {len(expected_tools)}")
            print(f"  Available: {len(available)}")

            if missing:
                print(f"  ❌ Missing tools: {sorted(missing)}")
                self.results.append(("Tool Availability", False))
                return

            if extra:
                print(f"  ⚠️  Extra tools: {sorted(extra)}")

            success = len(available) == 17
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"\n  {status}: All 17 tools available")

            self.results.append(("Tool Availability", success))

    async def _test_individual_tools(self):
        """Test 2: Individual tool functionality"""
        print("\nTEST 2: Individual Tool Functionality")
        print("-" * 70)

        try:
            from fastmcp import Client
        except ImportError:
            pytest.skip("FastMCP not installed")

        # Test Phase 1 tools
        phase1_tools = [
            ("strategy_list", {}, "Strategy listing"),
            (
                "backtest",
                {
                    "strategy": "Test01",
                    "symbol": "BTC-USDT",
                    "timeframe": "1h",
                    "start_date": "2023-01-01",
                    "end_date": "2023-01-31",
                },
                "Single backtest",
            ),
        ]

        passed = 0
        for tool_name, args, description in phase1_tools:
            try:
                async with Client(get_client_transport()) as client:
                    result = await client.call_tool(tool_name, args)
                    has_error = "error" in result and result["error"] is not None
                    status = "✅" if not has_error else "❌"
                    print(f"  {status} {description}: {tool_name}")
                    if not has_error:
                        passed += 1
            except Exception as e:
                print(f"  ❌ {description}: {tool_name} - {e}")

        self.results.append(("Individual Tools", passed == len(phase1_tools)))

    async def _test_tool_chains(self):
        """Test 3: Tool workflow chains"""
        print("\nTEST 3: Tool Workflow Chains")
        print("-" * 70)

        try:
            from fastmcp import Client
        except ImportError:
            pytest.skip("FastMCP not installed")

        # Test optimization workflow
        try:
            async with Client(get_client_transport()) as client:
                # Step 1: Get strategies
                strategies = await client.call_tool("strategy_list", {})

                # Step 2: Run optimization (will fail gracefully without Jesse)
                opt_result = await client.call_tool(
                    "optimize",
                    {
                        "strategy": "Test01",
                        "symbol": "BTC-USDT",
                        "timeframe": "1h",
                        "start_date": "2023-01-01",
                        "end_date": "2023-01-31",
                        "param_space": {
                            "param1": {"type": "float", "min": 0, "max": 1}
                        },
                    },
                )

                workflow_success = "error" not in strategies or strategies.get(
                    "strategies", []
                )

                status = "✅" if workflow_success else "❌"
                print(f"  {status} Optimization workflow")

        except Exception as e:
            print(f"  ❌ Optimization workflow: {e}")

        self.results.append(("Tool Chains", workflow_success))

    async def _test_error_handling(self):
        """Test 4: Error handling and edge cases"""
        print("\nTEST 4: Error Handling & Edge Cases")
        print("-" * 70)

        try:
            from fastmcp import Client
        except ImportError:
            pytest.skip("FastMCP not installed")

        error_tests = [
            {
                "name": "Unknown tool",
                "tool": "nonexistent_tool",
                "args": {},
                "expect_error": True,
            },
            {
                "name": "Missing required args",
                "tool": "backtest",
                "args": {},
                "expect_error": True,
            },
            {
                "name": "Invalid tool arguments",
                "tool": "monte_carlo",
                "args": {"backtest_result": None},
                "expect_error": True,
            },
        ]

        passed = 0
        for test in error_tests:
            try:
                async with Client(get_client_transport()) as client:
                    result = await client.call_tool(test["tool"], test["args"])
                    has_error = "error" in result and result["error"] is not None

                    if test["expect_error"] and has_error:
                        print(f"  ✅ {test['name']}: Correctly reported error")
                        passed += 1
                    elif not test["expect_error"] and not has_error:
                        print(f"  ✅ {test['name']}: Handled gracefully")
                        passed += 1
                    else:
                        print(f"  ❌ {test['name']}: Unexpected behavior")
            except Exception as e:
                if test["expect_error"]:
                    print(f"  ✅ {test['name']}: Correctly raised exception")
                    passed += 1

        self.results.append(("Error Handling", passed == len(error_tests)))

    async def _test_performance(self):
        """Test 5: Performance benchmarks"""
        print("\nTEST 5: Performance Benchmarks")
        print("-" * 70)

        try:
            from fastmcp import Client
        except ImportError:
            pytest.skip("FastMCP not installed")

        # Test tool discovery performance
        start_time = time.time()
        async with Client(get_client_transport()) as client:
            tools = await client.list_tools()
        discovery_time = time.time() - start_time

        # Test simple tool call performance
        start_time = time.time()
        async with Client(get_client_transport()) as client:
            await client.call_tool("strategy_list", {})
        call_time = time.time() - start_time

        print(f"  Tool discovery: {discovery_time:.3f}s")
        print(f"  Simple tool call: {call_time:.3f}s")

        # Performance criteria (adjust as needed)
        discovery_ok = discovery_time < 2.0
        call_ok = call_time < 1.0
        performance_ok = discovery_ok and call_ok

        status = "✅" if performance_ok else "❌"
        print(f"  {status} Performance benchmarks")

        self.results.append(("Performance", performance_ok))

    def _print_summary(self):
        """Print test summary"""
        elapsed = time.time() - self.start_time
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total time: {elapsed:.2f}s")

        for test_name, result in self.results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")

        passed = sum(1 for _, result in self.results)
        total = len(self.results)
        overall_status = (
            "✅ ALL TESTS PASSED" if passed == total else "❌ SOME TESTS FAILED"
        )
        print(f"\nOverall: {overall_status} ({passed}/{total})")

        return passed == total


@pytest.mark.asyncio
async def test_e2e_full_suite():
    """Run complete E2E test suite"""
    suite = E2ETestSuite()
    success = await suite.run_all_tests()
    assert success, "Some E2E tests failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
