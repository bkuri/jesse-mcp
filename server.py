#!/usr/bin/env python3
"""
Jesse MCP Server - Phase 1 Implementation

An MCP server that exposes Jesse's algorithmic trading framework capabilities to LLM agents.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jesse-mcp")

# Import Jesse integration layer
try:
    from jesse_integration import get_jesse_wrapper, JESSE_AVAILABLE

    logger.info("✅ Jesse integration layer loaded")
except ImportError as e:
    logger.warning(f"Jesse integration layer not available: {e}")
    JESSE_AVAILABLE = False
    get_jesse_wrapper = None

# Import Phase 3 optimizer
try:
    from phase3_optimizer import get_optimizer

    OPTIMIZER_AVAILABLE = True
    logger.info("✅ Phase 3 optimizer loaded")
except ImportError as e:
    logger.warning(f"Phase 3 optimizer not available: {e}")
    OPTIMIZER_AVAILABLE = False


class JesseMCPServer:
    """Jesse MCP Server implementation"""

    def __init__(self):
        self.name = "jesse-mcp"
        self.version = "1.0.0"

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        return [
            {
                "name": "backtest",
                "description": "Run a single backtest with specified parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "description": "Strategy name or inline code",
                        },
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTC-USDT)",
                        },
                        "timeframe": {
                            "type": "string",
                            "description": "Timeframe (e.g., 1h, 4h, 1D)",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)",
                        },
                        "exchange": {
                            "type": "string",
                            "description": "Exchange (default: Binance)",
                        },
                        "starting_balance": {
                            "type": "number",
                            "description": "Starting balance (default: 10000)",
                        },
                        "fee": {
                            "type": "number",
                            "description": "Trading fee (default: 0.001)",
                        },
                        "leverage": {
                            "type": "number",
                            "description": "Leverage for futures (default: 1)",
                        },
                        "exchange_type": {
                            "type": "string",
                            "enum": ["spot", "futures"],
                            "description": "Exchange type",
                        },
                        "hyperparameters": {
                            "type": "object",
                            "description": "Override strategy hyperparameters",
                        },
                        "include_trades": {
                            "type": "boolean",
                            "description": "Return individual trades",
                        },
                        "include_equity_curve": {
                            "type": "boolean",
                            "description": "Return equity curve data",
                        },
                        "include_logs": {
                            "type": "boolean",
                            "description": "Return strategy logs",
                        },
                    },
                    "required": [
                        "strategy",
                        "symbol",
                        "timeframe",
                        "start_date",
                        "end_date",
                    ],
                },
            },
            {
                "name": "strategy_list",
                "description": "List available strategies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_test_strategies": {
                            "type": "boolean",
                            "description": "Include test strategies",
                        }
                    },
                },
            },
            {
                "name": "strategy_read",
                "description": "Read strategy source code",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Strategy name"}
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "strategy_validate",
                "description": "Validate strategy code without saving",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Strategy code to validate",
                        }
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "candles_import",
                "description": "Download candle data from exchange",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "exchange": {
                            "type": "string",
                            "description": "Exchange (Binance, Bitfinex, Bybit, Coinbase, Gate, Hyperliquid, Apex)",
                        },
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTC-USDT)",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD, default: today)",
                        },
                    },
                    "required": ["exchange", "symbol", "start_date"],
                },
            },
            {
                "name": "optimize",
                "description": "Optimize strategy hyperparameters using Optuna",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "description": "Strategy name to optimize",
                        },
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol (e.g., BTC-USDT)",
                        },
                        "timeframe": {
                            "type": "string",
                            "description": "Timeframe (e.g., 1h, 4h, 1D)",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)",
                        },
                        "param_space": {
                            "type": "object",
                            "description": "Parameter space to optimize. Format: {'param_name': {'type': 'float', 'min': 0, 'max': 1}}",
                        },
                        "metric": {
                            "type": "string",
                            "description": "Optimization metric (total_return, sharpe_ratio, etc.)",
                            "default": "total_return",
                        },
                        "n_trials": {
                            "type": "integer",
                            "description": "Number of optimization trials",
                            "default": 100,
                        },
                        "n_jobs": {
                            "type": "integer",
                            "description": "Number of parallel jobs",
                            "default": 1,
                        },
                    },
                    "required": [
                        "strategy",
                        "symbol",
                        "timeframe",
                        "start_date",
                        "end_date",
                        "param_space",
                    ],
                },
            },
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""

        if not JESSE_AVAILABLE:
            return {
                "error": "Jesse framework not available",
                "message": "Please ensure Jesse is installed and accessible.",
            }

        try:
            if name == "backtest":
                return await self.handle_backtest(arguments)
            elif name == "strategy_list":
                return await self.handle_strategy_list(arguments)
            elif name == "strategy_read":
                return await self.handle_strategy_read(arguments)
            elif name == "strategy_validate":
                return await self.handle_strategy_validate(arguments)
            elif name == "candles_import":
                return await self.handle_candles_import(arguments)
            elif name == "optimize":
                return await self.handle_optimize(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}

    async def handle_backtest(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle backtest tool call - REAL IMPLEMENTATION"""
        try:
            if not JESSE_AVAILABLE or get_jesse_wrapper is None:
                return {"error": "Jesse not available"}

            wrapper = get_jesse_wrapper()

            result = wrapper.backtest(
                strategy=args["strategy"],
                symbol=args["symbol"],
                timeframe=args["timeframe"],
                start_date=args["start_date"],
                end_date=args["end_date"],
                exchange=args.get("exchange", "Binance"),
                starting_balance=args.get("starting_balance", 10000),
                fee=args.get("fee", 0.001),
                leverage=args.get("leverage", 1),
                exchange_type=args.get("exchange_type", "futures"),
                hyperparameters=args.get("hyperparameters"),
                include_trades=args.get("include_trades", False),
                include_equity_curve=args.get("include_equity_curve", False),
                include_logs=args.get("include_logs", False),
            )

            return result

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_strategy_list(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle strategy list tool call - REAL IMPLEMENTATION"""
        try:
            if not JESSE_AVAILABLE or get_jesse_wrapper is None:
                return {"error": "Jesse not available"}

            wrapper = get_jesse_wrapper()
            result = wrapper.list_strategies()

            return result

        except Exception as e:
            logger.error(f"Strategy list failed: {e}")
            return {"error": str(e), "strategies": []}

    async def handle_strategy_read(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle strategy read tool call - REAL IMPLEMENTATION"""
        try:
            if not JESSE_AVAILABLE or get_jesse_wrapper is None:
                return {"error": "Jesse not available"}

            wrapper = get_jesse_wrapper()
            result = wrapper.read_strategy(args["name"])

            return result

        except Exception as e:
            logger.error(f"Strategy read failed: {e}")
            return {"error": str(e), "name": args.get("name")}

    async def handle_strategy_validate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle strategy validate tool call - REAL IMPLEMENTATION"""
        try:
            if not JESSE_AVAILABLE or get_jesse_wrapper is None:
                return {"error": "Jesse not available"}

            wrapper = get_jesse_wrapper()
            result = wrapper.validate_strategy(args["code"])

            return result

        except Exception as e:
            logger.error(f"Strategy validation failed: {e}")
            return {"error": str(e), "valid": False}

    async def handle_candles_import(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle candles import tool call - REAL IMPLEMENTATION"""
        try:
            if not JESSE_AVAILABLE or get_jesse_wrapper is None:
                return {"error": "Jesse not available"}

            wrapper = get_jesse_wrapper()
            result = wrapper.import_candles(
                exchange=args["exchange"],
                symbol=args["symbol"],
                start_date=args["start_date"],
                end_date=args.get("end_date"),
            )

            return result

        except Exception as e:
            logger.error(f"Candles import failed: {e}")
            return {"error": str(e), "success": False}

    async def handle_optimize(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle optimize tool call - PHASE 3 IMPLEMENTATION"""
        try:
            if not OPTIMIZER_AVAILABLE:
                return {"error": "Phase 3 optimizer not available"}

            optimizer = get_optimizer()

            result = await optimizer.optimize(
                strategy=args["strategy"],
                symbol=args["symbol"],
                timeframe=args["timeframe"],
                start_date=args["start_date"],
                end_date=args["end_date"],
                param_space=args["param_space"],
                metric=args.get("metric", "total_return"),
                n_trials=args.get("n_trials", 100),
                n_jobs=args.get("n_jobs", 1),
                exchange=args.get("exchange", "Binance"),
                starting_balance=args.get("starting_balance", 10000),
                fee=args.get("fee", 0.001),
                leverage=args.get("leverage", 1),
                exchange_type=args.get("exchange_type", "futures"),
            )

            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        return [
            {
                "uri": "strategies://list",
                "name": "Strategy List",
                "description": "List of all available strategies with metadata",
                "mimeType": "application/json",
            },
            {
                "uri": "indicators://list",
                "name": "Indicators List",
                "description": "All available Jesse indicators with documentation",
                "mimeType": "application/json",
            },
        ]

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read resource content - REAL IMPLEMENTATION"""
        try:
            if uri == "strategies://list":
                if not JESSE_AVAILABLE or get_jesse_wrapper is None:
                    return {"error": "Jesse not available"}

                wrapper = get_jesse_wrapper()
                return wrapper.list_strategies()

            elif uri == "indicators://list":
                return {
                    "message": "Indicators list - Phase 2 (200+ indicators available)",
                    "status": "Implementation coming in Phase 4",
                    "note": "Jesse provides 200+ indicators via ta.* namespace",
                }
            else:
                return {"error": f"Unknown resource: {uri}"}

        except Exception as e:
            logger.error(f"Resource read failed for {uri}: {e}")
            return {"error": str(e)}


# Simple MCP protocol implementation
async def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP request"""
    server = JesseMCPServer()

    method = request.get("method")
    params = request.get("params", {})

    if method == "tools/list":
        return {"tools": await server.list_tools()}
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        return await server.call_tool(name, arguments)
    elif method == "resources/list":
        return {"resources": await server.list_resources()}
    elif method == "resources/read":
        uri = params.get("uri")
        return await server.read_resource(uri)
    else:
        return {"error": f"Unknown method: {method}"}


async def main():
    """Main server entry point"""
    logger.info("Starting jesse-mcp server v1.0.0")

    if not JESSE_AVAILABLE:
        logger.error(
            "Jesse framework not available. Please ensure Jesse is installed and accessible."
        )
        # Continue anyway for testing

    # Simple stdio communication
    try:
        while True:
            # Read request from stdin
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line.strip())
                response = await handle_request(request)

                # Send response to stdout
                print(json.dumps(response))
                sys.stdout.flush()

            except json.JSONDecodeError:
                error_response = {"error": "Invalid JSON request"}
                print(json.dumps(error_response))
                sys.stdout.flush()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
