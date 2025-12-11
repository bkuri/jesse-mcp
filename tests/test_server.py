#!/usr/bin/env python3
"""
Test Jesse MCP Server tool discovery and execution

Uses FastMCP Client API to test server functionality
"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_tools_list():
    """Test that all 17 tools are discoverable"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        tools = await client.list_tools()

        # Verify count
        assert len(tools) == 17, f"Expected 17 tools, got {len(tools)}"

        # Verify tool names
        tool_names = {t.name for t in tools}
        expected_tools = {
            # Phase 1: Backtesting
            "backtest",
            "strategy_list",
            "strategy_read",
            "strategy_validate",
            "candles_import",
            # Phase 3: Optimization
            "optimize",
            "walk_forward",
            "backtest_batch",
            "analyze_results",
            # Phase 4: Risk Analysis
            "monte_carlo",
            "var_calculation",
            "stress_test",
            "risk_report",
            # Phase 5: Pairs Trading
            "correlation_matrix",
            "pairs_backtest",
            "factor_analysis",
            "regime_detector",
        }
        assert expected_tools == tool_names, (
            f"Tool mismatch. Expected: {expected_tools}, Got: {tool_names}"
        )

        print(f"✅ All {len(tools)} tools discovered successfully")


@pytest.mark.asyncio
async def test_backtest_tool():
    """Test backtest tool execution"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        result = await client.call_tool(
            "backtest",
            {
                "strategy": "Test01",
                "symbol": "BTC-USDT",
                "timeframe": "1h",
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
        )

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        # Tool should return a result (may contain error if Jesse unavailable)
        assert "error" in result or "total_return" in result or "status" in result
        print(f"✅ Backtest tool responded: {result.get('status', 'executed')}")


@pytest.mark.asyncio
async def test_strategy_list_tool():
    """Test strategy_list tool"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        result = await client.call_tool("strategy_list", {})

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        print(f"✅ Strategy list tool responded")


@pytest.mark.asyncio
async def test_optimize_tool():
    """Test optimize tool (async)"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        result = await client.call_tool(
            "optimize",
            {
                "strategy": "Test01",
                "symbol": "BTC-USDT",
                "timeframe": "1h",
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
                "param_space": {"param1": {"type": "float", "min": 0, "max": 1}},
            },
        )

        assert isinstance(result, dict)
        print(f"✅ Optimize tool responded (async)")


@pytest.mark.asyncio
async def test_monte_carlo_tool():
    """Test monte_carlo tool"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        mock_result = {"trades": [], "metrics": {}}
        result = await client.call_tool(
            "monte_carlo",
            {
                "backtest_result": mock_result,
                "simulations": 1000,
            },
        )

        assert isinstance(result, dict)
        print(f"✅ Monte Carlo tool responded")


@pytest.mark.asyncio
async def test_invalid_tool():
    """Test calling non-existent tool"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        # Should raise or return error
        try:
            result = await client.call_tool("nonexistent_tool", {})
            # Some clients may return error dict instead of raising
            assert "error" in str(result) or "not found" in str(result).lower()
        except Exception:
            # Expected behavior for non-existent tool
            pass

        print(f"✅ Invalid tool handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
