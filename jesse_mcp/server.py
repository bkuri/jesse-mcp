#!/usr/bin/env python3
"""
Jesse MCP Server - FastMCP Implementation

Provides 51 tools for quantitative trading analysis:
- Phase 1: Backtesting (5 tools)
- Phase 3: Optimization (4 tools)
- Phase 4: Risk Analysis (4 tools)
- Phase 5: Pairs Trading (5 tools)
- Phase 6: Live Trading (12 tools)
- Strategy Creation (6 tools) - Ralph Wiggum Loop with progress tracking
- Community (5 tools) - jesse.trade community strategy browsing & comparison

Tools are registered from modular files in jesse_mcp/tools/:
- backtesting.py, strategy.py, optimization.py, risk.py, pairs.py, live.py
"""

import logging
import importlib.metadata
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jesse-mcp")

# ==================== LAZY INITIALIZATION ====================

jesse: Optional[Any] = None
optimizer: Optional[Any] = None
risk_analyzer: Optional[Any] = None
pairs_analyzer: Optional[Any] = None
_initialized: bool = False


def _initialize_dependencies():
    """Initialize Jesse and analyzer modules - called from main()"""
    global jesse, optimizer, risk_analyzer, pairs_analyzer, _initialized

    if _initialized:
        return

    init_configs = [
        (
            "jesse_mcp.core.integrations",
            "get_jesse_wrapper",
            "JESSE_AVAILABLE",
            "Jesse framework",
            "jesse",
        ),
        (
            "jesse_mcp.optimizer",
            "get_optimizer",
            None,
            "Optimizer module",
            "optimizer",
        ),
        (
            "jesse_mcp.risk_analyzer",
            "get_risk_analyzer",
            None,
            "Risk analyzer module",
            "risk_analyzer",
        ),
        (
            "jesse_mcp.pairs_analyzer",
            "get_pairs_analyzer",
            None,
            "Pairs analyzer module",
            "pairs_analyzer",
        ),
    ]

    for (
        module_path,
        getter_name,
        availability_check,
        display_name,
        var_name,
    ) in init_configs:
        try:
            module = __import__(module_path, fromlist=[getter_name])
            getter = getattr(module, getter_name)

            if availability_check:
                available = getattr(module, availability_check, False)
                if available:
                    instance = getter()
                    globals()[var_name] = instance
                    logger.info(f"✅ {display_name} initialized")
                else:
                    logger.warning(f"⚠️ {display_name} not available - running in mock mode")
            else:
                instance = getter()
                globals()[var_name] = instance
                logger.info(f"✅ {display_name} loaded")
        except Exception as e:
            logger.warning(f"⚠️ {display_name} initialization failed: {e}")

    from jesse_mcp.tools._utils import initialize

    initialize(jesse, optimizer, risk_analyzer, pairs_analyzer)

    _initialized = True


# ==================== FASTMCP INITIALIZATION ====================

mcp = FastMCP("jesse-mcp", version="1.0.0")


@mcp.custom_route("/health", methods=["GET"])
async def health_endpoint(request: Request) -> JSONResponse:
    """
    HTTP health endpoint for monitoring Jesse MCP server status.

    Returns MCP server status, Jesse connection status, and timestamp.
    """
    from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

    jesse_status: Dict[str, Any] = {"connected": False, "error": None}
    try:
        client = get_jesse_rest_client()
        jesse_status = client.health_check()
    except Exception as e:
        jesse_status["error"] = str(e)

    return JSONResponse(
        {
            "status": "healthy",
            "mcp_server": "jesse-mcp",
            "version": importlib.metadata.version("jesse-mcp"),
            "jesse": jesse_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


def _register_all_tools():
    """Register all MCP tools from modular tool files."""
    from jesse_mcp.tools.backtesting import register_backtesting_tools
    from jesse_mcp.tools.strategy import register_strategy_tools
    from jesse_mcp.tools.optimization import register_optimization_tools
    from jesse_mcp.tools.risk import register_risk_tools
    from jesse_mcp.tools.pairs import register_pairs_tools
    from jesse_mcp.tools.live import register_live_tools
    from jesse_mcp.tools.jesse_trade import register_jesse_trade_tools

    register_backtesting_tools(mcp)
    logger.info("✅ Backtesting tools registered")

    register_strategy_tools(mcp)
    logger.info("✅ Strategy tools registered")

    register_optimization_tools(mcp)
    logger.info("✅ Optimization tools registered")

    register_risk_tools(mcp)
    logger.info("✅ Risk tools registered")

    register_pairs_tools(mcp)
    logger.info("✅ Pairs tools registered")

    register_live_tools(mcp)
    logger.info("✅ Live trading tools registered")

    register_jesse_trade_tools(mcp)
    logger.info("✅ jesse.trade community tools registered")


# ==================== MAIN ENTRY POINT ====================


def main():
    """Main entry point with transport options"""
    import argparse

    _initialize_dependencies()
    _register_all_tools()

    try:
        from jesse_mcp.agent_tools import register_agent_tools

        register_agent_tools(mcp)
        logger.info("✅ Agent tools registered")
    except Exception as e:
        logger.warning(f"⚠️  Agent tools registration failed: {e}")

    parser = argparse.ArgumentParser(description="Jesse MCP Server - Quantitative Trading Analysis")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)",
    )

    args = parser.parse_args()

    if args.transport == "http":
        logger.info(f"Starting Jesse MCP Server on http://0.0.0.0:{args.port}")
        mcp.run(transport="http", host="0.0.0.0", port=args.port)
    else:
        logger.info("Starting Jesse MCP Server (stdio transport)")
        mcp.run()


if __name__ == "__main__":
    main()
