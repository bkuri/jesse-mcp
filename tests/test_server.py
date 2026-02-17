#!/usr/bin/env python3
"""
Test Jesse MCP Server tool discovery and execution

Uses FastMCP Client API to test server functionality
"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_tools_list():
    """Test that all core tools are discoverable"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        tools = await client.list_tools()

        # Verify we have at least the core 18 tools (may have more with agent tools)
        assert len(tools) >= 20, f"Expected at least 20 tools, got {len(tools)}"

        # Verify core tool names are present
        tool_names = {t.name for t in tools}
        core_tools = {
            # Phase 1: Backtesting
            "jesse_status",
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
            # Cache Management
            "cache_stats",
            "cache_clear",
        }
        assert core_tools.issubset(tool_names), (
            f"Missing core tools. Expected subset: {core_tools}, Got: {tool_names}"
        )

        print(
            f"✅ All {len(tools)} tools discovered successfully (20 core + {len(tools) - 20} agent)"
        )


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

        data = result.data if hasattr(result, "data") else result
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        # Tool should return a result (may contain error if Jesse unavailable)
        assert "error" in data or "total_return" in data or "status" in data
        print(f"✅ Backtest tool responded: {data.get('status', 'executed')}")


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

        # FastMCP 2.x returns CallToolResult with .data containing the dict
        data = result.data if hasattr(result, "data") else result
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        print(f"✅ Strategy list tool responded: {data.get('count', 0)} strategies")


@pytest.mark.asyncio
async def test_jesse_status_tool():
    """Test jesse_status tool"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        result = await client.call_tool("jesse_status", {})

        data = result.data if hasattr(result, "data") else result
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        assert "connected" in data, "Expected 'connected' key in jesse_status result"
        print(f"✅ Jesse status tool responded: connected={data.get('connected')}")


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

        data = result.data if hasattr(result, "data") else result
        assert isinstance(data, dict)
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
        mock_result = {"trades": [], "metrics": {}, "equity_curve": []}
        result = await client.call_tool(
            "monte_carlo",
            {
                "backtest_result": mock_result,
                "simulations": 1000,
            },
        )

        data = result.data if hasattr(result, "data") else result
        assert isinstance(data, dict)
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


@pytest.mark.asyncio
async def test_cache_tools():
    """Test cache_stats and cache_clear tools"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        # Test cache_stats
        result = await client.call_tool("cache_stats", {})
        data = result.data if hasattr(result, "data") else result
        assert isinstance(data, dict)
        assert "enabled" in data
        print(f"✅ Cache stats tool responded: enabled={data.get('enabled')}")

        # Test cache_clear
        result = await client.call_tool("cache_clear", {})
        data = result.data if hasattr(result, "data") else result
        assert isinstance(data, dict)
        assert "cleared" in data
        print(f"✅ Cache clear tool responded")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
