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
    from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE

    logger.info("✅ Jesse integration layer loaded")
except ImportError as e:
    logger.warning(f"Jesse integration layer not available: {e}")
    JESSE_AVAILABLE = False
    get_jesse_wrapper = None

# Import Phase 3 optimizer
try:
    from jesse_mcp.phase3.optimizer import get_optimizer

    OPTIMIZER_AVAILABLE = True
    logger.info("✅ Phase 3 optimizer loaded")
except ImportError as e:
    logger.warning(f"Phase 3 optimizer not available: {e}")

# Import Phase 4 risk analyzer
try:
    from jesse_mcp.phase4.risk_analyzer import get_risk_analyzer

    RISK_ANALYZER_AVAILABLE = True
    logger.info("✅ Phase 4 risk analyzer loaded")
except ImportError as e:
    logger.warning(f"Phase 4 risk analyzer not available: {e}")
    RISK_ANALYZER_AVAILABLE = False

# Import Phase 5 pairs analyzer
try:
    from jesse_mcp.phase5.pairs_analyzer import get_pairs_analyzer

    PAIRS_ANALYZER_AVAILABLE = True
    logger.info("✅ Phase 5 pairs analyzer loaded")
except ImportError as e:
    logger.warning(f"Phase 5 pairs analyzer not available: {e}")
    PAIRS_ANALYZER_AVAILABLE = False


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
            {
                "name": "walk_forward",
                "description": "Perform walk-forward analysis to detect overfitting",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "description": "Strategy name",
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
                        "in_sample_period": {
                            "type": "integer",
                            "description": "Days for optimization period (default: 365)",
                            "default": 365,
                        },
                        "out_sample_period": {
                            "type": "integer",
                            "description": "Days for validation period (default: 30)",
                            "default": 30,
                        },
                        "step_forward": {
                            "type": "integer",
                            "description": "Days to move window forward (default: 7)",
                            "default": 7,
                        },
                        "param_space": {
                            "type": "object",
                            "description": "Parameter space for optimization (optional)",
                        },
                        "metric": {
                            "type": "string",
                            "description": "Optimization metric (default: total_return)",
                            "default": "total_return",
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
                "name": "backtest_batch",
                "description": "Run multiple backtests concurrently for strategy comparison",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "description": "Strategy name",
                        },
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of trading symbols",
                        },
                        "timeframes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of timeframes",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)",
                        },
                        "hyperparameters": {
                            "type": "array",
                            "description": "List of parameter sets to test (optional)",
                        },
                        "concurrent_limit": {
                            "type": "integer",
                            "description": "Maximum concurrent backtests (default: 4)",
                            "default": 4,
                        },
                    },
                    "required": [
                        "strategy",
                        "symbols",
                        "timeframes",
                        "start_date",
                        "end_date",
                    ],
                },
            },
            {
                "name": "analyze_results",
                "description": "Extract deep insights from backtest results",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backtest_result": {
                            "type": "object",
                            "description": "Result from backtest() or backtest_batch()",
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["basic", "advanced", "deep"],
                            "description": "Depth of analysis (default: basic)",
                            "default": "basic",
                        },
                        "include_trade_analysis": {
                            "type": "boolean",
                            "description": "Include detailed trade analysis (default: true)",
                            "default": True,
                        },
                        "include_correlation": {
                            "type": "boolean",
                            "description": "Include correlation analysis (default: false)",
                            "default": False,
                        },
                        "include_monte_carlo": {
                            "type": "boolean",
                            "description": "Include Monte Carlo simulation (default: false)",
                            "default": False,
                        },
                    },
                    "required": ["backtest_result"],
                },
            },
            {
                "name": "monte_carlo",
                "description": "Generate Monte Carlo simulations for comprehensive risk analysis with bootstrap resampling",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backtest_result": {
                            "type": "object",
                            "description": "Result from backtest() or backtest_batch()",
                        },
                        "simulations": {
                            "type": "integer",
                            "description": "Number of Monte Carlo runs (default: 10000)",
                            "default": 10000,
                        },
                        "confidence_levels": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Confidence levels for intervals (default: [0.95, 0.99])",
                        },
                        "resample_method": {
                            "type": "string",
                            "enum": [
                                "bootstrap",
                                "block_bootstrap",
                                "stationary_bootstrap",
                            ],
                            "description": "Bootstrap method (default: bootstrap)",
                            "default": "bootstrap",
                        },
                        "block_size": {
                            "type": "integer",
                            "description": "Block size for block bootstrap (default: 20)",
                            "default": 20,
                        },
                        "include_drawdowns": {
                            "type": "boolean",
                            "description": "Include drawdown analysis (default: true)",
                            "default": True,
                        },
                        "include_returns": {
                            "type": "boolean",
                            "description": "Include return distribution analysis (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["backtest_result"],
                },
            },
            {
                "name": "var_calculation",
                "description": "Calculate Value at Risk using multiple methods (historical, parametric, Monte Carlo)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backtest_result": {
                            "type": "object",
                            "description": "Result from backtest() or backtest_batch()",
                        },
                        "confidence_levels": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Confidence levels (default: [0.90, 0.95])",
                        },
                        "time_horizons": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Time horizons in days (default: [1, 5, 10])",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["historical", "parametric", "monte_carlo", "all"],
                            "description": "VaR calculation method (default: all)",
                            "default": "all",
                        },
                        "monte_carlo_sims": {
                            "type": "integer",
                            "description": "Number of Monte Carlo simulations (default: 10000)",
                            "default": 10000,
                        },
                    },
                    "required": ["backtest_result"],
                },
            },
            {
                "name": "stress_test",
                "description": "Test strategy performance under extreme market scenarios and black swan events",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backtest_result": {
                            "type": "object",
                            "description": "Result from backtest() or backtest_batch()",
                        },
                        "scenarios": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Scenarios to test (default: all). Options: market_crash, volatility_spike, correlation_breakdown, flash_crash, black_swan",
                        },
                        "include_custom_scenarios": {
                            "type": "boolean",
                            "description": "Include custom market scenarios (default: false)",
                            "default": False,
                        },
                    },
                    "required": ["backtest_result"],
                },
            },
            {
                "name": "risk_report",
                "description": "Generate comprehensive risk assessment and recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backtest_result": {
                            "type": "object",
                            "description": "Result from backtest() or backtest_batch()",
                        },
                        "include_monte_carlo": {
                            "type": "boolean",
                            "description": "Include Monte Carlo analysis (default: true)",
                            "default": True,
                        },
                        "include_var_analysis": {
                            "type": "boolean",
                            "description": "Include VaR analysis (default: true)",
                            "default": True,
                        },
                        "include_stress_test": {
                            "type": "boolean",
                            "description": "Include stress testing (default: true)",
                            "default": True,
                        },
                        "monte_carlo_sims": {
                            "type": "integer",
                            "description": "Number of Monte Carlo simulations (default: 5000)",
                            "default": 5000,
                        },
                        "report_format": {
                            "type": "string",
                            "enum": ["summary", "detailed", "executive"],
                            "description": "Report format (default: summary)",
                            "default": "summary",
                        },
                    },
                    "required": ["backtest_result"],
                },
            },
            {
                "name": "correlation_matrix",
                "description": "Analyze cross-asset correlations and identify pairs trading opportunities",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backtest_results": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "List of backtest results from different symbols",
                        },
                        "lookback_period": {
                            "type": "integer",
                            "description": "Days to analyze (default: 60)",
                            "default": 60,
                        },
                        "correlation_threshold": {
                            "type": "number",
                            "description": "Minimum correlation for pair suggestions (default: 0.7)",
                            "default": 0.7,
                        },
                        "include_rolling": {
                            "type": "boolean",
                            "description": "Include rolling correlations (default: true)",
                            "default": True,
                        },
                        "rolling_window": {
                            "type": "integer",
                            "description": "Window size for rolling correlation (default: 20)",
                            "default": 20,
                        },
                        "include_heatmap": {
                            "type": "boolean",
                            "description": "Generate correlation heatmap (default: false)",
                            "default": False,
                        },
                    },
                    "required": ["backtest_results"],
                },
            },
            {
                "name": "pairs_backtest",
                "description": "Backtest pairs trading strategies (statistical arbitrage, mean reversion)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pair": {
                            "type": "object",
                            "description": "Dict with 'symbol1' and 'symbol2'",
                        },
                        "strategy": {
                            "type": "string",
                            "enum": [
                                "mean_reversion",
                                "momentum_divergence",
                                "cointegration",
                            ],
                            "description": "Pairs trading strategy (default: mean_reversion)",
                            "default": "mean_reversion",
                        },
                        "backtest_result_1": {
                            "type": "object",
                            "description": "Backtest result for first symbol",
                        },
                        "backtest_result_2": {
                            "type": "object",
                            "description": "Backtest result for second symbol",
                        },
                        "lookback_period": {
                            "type": "integer",
                            "description": "Historical period for calculations (default: 60)",
                            "default": 60,
                        },
                        "entry_threshold": {
                            "type": "number",
                            "description": "Entry signal threshold - std dev (default: 2.0)",
                            "default": 2.0,
                        },
                        "exit_threshold": {
                            "type": "number",
                            "description": "Exit signal threshold - std dev (default: 0.5)",
                            "default": 0.5,
                        },
                        "position_size": {
                            "type": "number",
                            "description": "Risk per trade (default: 0.02)",
                            "default": 0.02,
                        },
                        "max_holding_days": {
                            "type": "integer",
                            "description": "Maximum days to hold position (default: 20)",
                            "default": 20,
                        },
                    },
                    "required": ["pair", "backtest_result_1", "backtest_result_2"],
                },
            },
            {
                "name": "factor_analysis",
                "description": "Decompose returns into systematic factors (market, size, momentum, value)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backtest_result": {
                            "type": "object",
                            "description": "Strategy backtest result",
                        },
                        "factors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Factors to analyze (default: market, size, momentum, value)",
                        },
                        "factor_returns": {
                            "type": "object",
                            "description": "Dict mapping factors to historical returns",
                        },
                        "include_residuals": {
                            "type": "boolean",
                            "description": "Include unexplained returns (default: true)",
                            "default": True,
                        },
                        "analysis_period": {
                            "type": "integer",
                            "description": "Days to analyze (default: 252, annual)",
                            "default": 252,
                        },
                        "confidence_level": {
                            "type": "number",
                            "description": "Statistical confidence (default: 0.95)",
                            "default": 0.95,
                        },
                    },
                    "required": ["backtest_result"],
                },
            },
            {
                "name": "regime_detector",
                "description": "Identify market regimes and transitions (bull, bear, high/low volatility)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "backtest_results": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "List of backtest results",
                        },
                        "lookback_period": {
                            "type": "integer",
                            "description": "Days for regime analysis (default: 60)",
                            "default": 60,
                        },
                        "detection_method": {
                            "type": "string",
                            "enum": [
                                "hmm",
                                "volatility_based",
                                "correlation_based",
                            ],
                            "description": "Regime detection method (default: hmm)",
                            "default": "hmm",
                        },
                        "n_regimes": {
                            "type": "integer",
                            "description": "Number of market regimes (default: 3)",
                            "default": 3,
                        },
                        "include_transitions": {
                            "type": "boolean",
                            "description": "Include regime transition analysis (default: true)",
                            "default": True,
                        },
                        "include_forecast": {
                            "type": "boolean",
                            "description": "Forecast next regime probability (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["backtest_results"],
                },
            },
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""

        # Phase 3-5 tools can work with mock data (don't require Jesse)
        mock_capable_tools = [
            # Phase 3
            "optimize",
            "walk_forward",
            "backtest_batch",
            "analyze_results",
            # Phase 4
            "monte_carlo",
            "var_calculation",
            "stress_test",
            "risk_report",
            # Phase 5
            "correlation_matrix",
            "pairs_backtest",
            "factor_analysis",
            "regime_detector",
        ]

        if not JESSE_AVAILABLE and name not in mock_capable_tools:
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
            elif name == "monte_carlo":
                return await self.handle_monte_carlo(arguments)
            elif name == "var_calculation":
                return await self.handle_var_calculation(arguments)
            elif name == "stress_test":
                return await self.handle_stress_test(arguments)
            elif name == "risk_report":
                return await self.handle_risk_report(arguments)
            elif name == "correlation_matrix":
                return await self.handle_correlation_matrix(arguments)
            elif name == "pairs_backtest":
                return await self.handle_pairs_backtest(arguments)
            elif name == "factor_analysis":
                return await self.handle_factor_analysis(arguments)
            elif name == "regime_detector":
                return await self.handle_regime_detector(arguments)
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

    async def handle_walk_forward(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle walk-forward analysis tool call - PHASE 3 IMPLEMENTATION"""
        try:
            if not OPTIMIZER_AVAILABLE:
                return {"error": "Phase 3 optimizer not available"}

            optimizer = get_optimizer()

            result = await optimizer.walk_forward(
                strategy=args["strategy"],
                symbol=args["symbol"],
                timeframe=args["timeframe"],
                start_date=args["start_date"],
                end_date=args["end_date"],
                in_sample_period=args.get("in_sample_period", 365),
                out_sample_period=args.get("out_sample_period", 30),
                step_forward=args.get("step_forward", 7),
                param_space=args.get("param_space"),
                metric=args.get("metric", "total_return"),
            )

            return result

        except Exception as e:
            logger.error(f"Walk-forward analysis failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_backtest_batch(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch backtest tool call - PHASE 3 IMPLEMENTATION"""
        try:
            if not OPTIMIZER_AVAILABLE:
                return {"error": "Phase 3 optimizer not available"}

            optimizer = get_optimizer()

            result = await optimizer.backtest_batch(
                strategy=args["strategy"],
                symbols=args["symbols"],
                timeframes=args["timeframes"],
                start_date=args["start_date"],
                end_date=args["end_date"],
                hyperparameters=args.get("hyperparameters"),
                concurrent_limit=args.get("concurrent_limit", 4),
            )

            return result

        except Exception as e:
            logger.error(f"Batch backtest failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_monte_carlo(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Monte Carlo tool call - PHASE 4 IMPLEMENTATION"""
        try:
            if not RISK_ANALYZER_AVAILABLE:
                return {"error": "Phase 4 risk analyzer not available"}

            analyzer = get_risk_analyzer()

            result = await analyzer.monte_carlo(
                backtest_result=args["backtest_result"],
                simulations=args.get("simulations", 10000),
                confidence_levels=args.get("confidence_levels"),
                resample_method=args.get("resample_method", "bootstrap"),
                block_size=args.get("block_size", 20),
                include_drawdowns=args.get("include_drawdowns", True),
                include_returns=args.get("include_returns", True),
            )

            return result

        except Exception as e:
            logger.error(f"Monte Carlo analysis failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_var_calculation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle VaR calculation tool call - PHASE 4 IMPLEMENTATION"""
        try:
            if not RISK_ANALYZER_AVAILABLE:
                return {"error": "Phase 4 risk analyzer not available"}

            analyzer = get_risk_analyzer()

            result = await analyzer.var_calculation(
                backtest_result=args["backtest_result"],
                confidence_levels=args.get("confidence_levels"),
                time_horizons=args.get("time_horizons"),
                method=args.get("method", "historical"),
                monte_carlo_sims=args.get("monte_carlo_sims", 10000),
            )

            return result

        except Exception as e:
            logger.error(f"VaR calculation failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_stress_test(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stress test tool call - PHASE 4 IMPLEMENTATION"""
        try:
            if not RISK_ANALYZER_AVAILABLE:
                return {"error": "Phase 4 risk analyzer not available"}

            analyzer = get_risk_analyzer()

            result = await analyzer.stress_test(
                backtest_result=args["backtest_result"],
                scenarios=args.get("scenarios"),
                custom_scenarios=args.get("custom_scenarios"),
                shock_magnitude=args.get("shock_magnitude", -0.20),
                volatility_multiplier=args.get("volatility_multiplier", 3.0),
                correlation_shift=args.get("correlation_shift", 0.8),
                recovery_periods=args.get("recovery_periods"),
            )

            return result

        except Exception as e:
            logger.error(f"Stress test failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_risk_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle risk report tool call - PHASE 4 IMPLEMENTATION"""
        try:
            if not RISK_ANALYZER_AVAILABLE:
                return {"error": "Phase 4 risk analyzer not available"}

            analyzer = get_risk_analyzer()

            result = await analyzer.risk_report(
                backtest_result=args["backtest_result"],
                include_monte_carlo=args.get("include_monte_carlo", True),
                include_var_analysis=args.get("include_var_analysis", True),
                include_stress_test=args.get("include_stress_test", True),
                monte_carlo_sims=args.get("monte_carlo_sims", 5000),
                report_format=args.get("report_format", "summary"),
            )

            return result

        except Exception as e:
            logger.error(f"Risk report failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_correlation_matrix(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle correlation matrix tool call - PHASE 5 IMPLEMENTATION"""
        try:
            if not PAIRS_ANALYZER_AVAILABLE:
                return {"error": "Phase 5 pairs analyzer not available"}

            analyzer = get_pairs_analyzer()

            result = await analyzer.correlation_matrix(
                backtest_results=args.get("backtest_results", []),
                lookback_period=args.get("lookback_period", 60),
                correlation_threshold=args.get("correlation_threshold", 0.7),
                include_rolling=args.get("include_rolling", True),
                rolling_window=args.get("rolling_window", 20),
                include_heatmap=args.get("include_heatmap", False),
            )

            return result

        except Exception as e:
            logger.error(f"Correlation matrix failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_pairs_backtest(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pairs backtest tool call - PHASE 5 IMPLEMENTATION"""
        try:
            if not PAIRS_ANALYZER_AVAILABLE:
                return {"error": "Phase 5 pairs analyzer not available"}

            analyzer = get_pairs_analyzer()

            result = await analyzer.pairs_backtest(
                pair=args.get("pair", {}),
                strategy=args.get("strategy", "mean_reversion"),
                backtest_result_1=args.get("backtest_result_1"),
                backtest_result_2=args.get("backtest_result_2"),
                lookback_period=args.get("lookback_period", 60),
                entry_threshold=args.get("entry_threshold", 2.0),
                exit_threshold=args.get("exit_threshold", 0.5),
                position_size=args.get("position_size", 0.02),
                max_holding_days=args.get("max_holding_days", 20),
            )

            return result

        except Exception as e:
            logger.error(f"Pairs backtest failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_factor_analysis(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle factor analysis tool call - PHASE 5 IMPLEMENTATION"""
        try:
            if not PAIRS_ANALYZER_AVAILABLE:
                return {"error": "Phase 5 pairs analyzer not available"}

            analyzer = get_pairs_analyzer()

            result = await analyzer.factor_analysis(
                backtest_result=args.get("backtest_result", {}),
                factors=args.get("factors"),
                factor_returns=args.get("factor_returns"),
                include_residuals=args.get("include_residuals", True),
                analysis_period=args.get("analysis_period", 252),
                confidence_level=args.get("confidence_level", 0.95),
            )

            return result

        except Exception as e:
            logger.error(f"Factor analysis failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__}

    async def handle_regime_detector(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle regime detector tool call - PHASE 5 IMPLEMENTATION"""
        try:
            if not PAIRS_ANALYZER_AVAILABLE:
                return {"error": "Phase 5 pairs analyzer not available"}

            analyzer = get_pairs_analyzer()

            result = await analyzer.regime_detector(
                backtest_results=args.get("backtest_results", []),
                lookback_period=args.get("lookback_period", 60),
                detection_method=args.get("detection_method", "hmm"),
                n_regimes=args.get("n_regimes", 3),
                include_transitions=args.get("include_transitions", True),
                include_forecast=args.get("include_forecast", True),
            )

            return result

        except Exception as e:
            logger.error(f"Regime detector failed: {e}")
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
