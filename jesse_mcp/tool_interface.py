"""
Tool Interface for OpenCode Orchestration

Provides a clean Python interface to call MCP tools directly.
Designed for use by OpenCode/LLM orchestration without requiring
the full FastMCP server infrastructure.

This is the bridge between OpenCode's conversational abilities
and Jesse's trading capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("jesse-mcp.tool_interface")


@dataclass
class ToolResult:
    """Result from a tool call"""

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MCPToolInterface:
    """
    Clean interface to all 17 MCP tools.

    Used by OpenCode to orchestrate strategy improvement conversations.
    """

    def __init__(self):
        """Initialize tool interface"""
        self.tools_cache = {}
        self._initialize_tools()
        logger.info("✅ MCP Tool Interface initialized with 17 tools")

    def _initialize_tools(self):
        """Initialize all 17 tools"""
        self.tools_cache = {
            # Phase 1: Backtesting (6)
            "backtest": self._call_tool_wrapper("backtest"),
            "strategy_list": self._call_tool_wrapper("strategy_list"),
            "strategy_read": self._call_tool_wrapper("strategy_read"),
            "strategy_validate": self._call_tool_wrapper("strategy_validate"),
            "candles_import": self._call_tool_wrapper("candles_import"),
            "analyze_results": self._call_tool_wrapper("analyze_results"),
            # Phase 3: Optimization (4)
            "optimize": self._call_tool_wrapper("optimize"),
            "walk_forward": self._call_tool_wrapper("walk_forward"),
            "backtest_batch": self._call_tool_wrapper("backtest_batch"),
            # Phase 4: Risk Analysis (4)
            "monte_carlo": self._call_tool_wrapper("monte_carlo"),
            "var_calculation": self._call_tool_wrapper("var_calculation"),
            "stress_test": self._call_tool_wrapper("stress_test"),
            "risk_report": self._call_tool_wrapper("risk_report"),
            # Phase 5: Pairs Trading (4)
            "correlation_matrix": self._call_tool_wrapper("correlation_matrix"),
            "pairs_backtest": self._call_tool_wrapper("pairs_backtest"),
            "factor_analysis": self._call_tool_wrapper("factor_analysis"),
            "regime_detector": self._call_tool_wrapper("regime_detector"),
        }

    def _call_tool_wrapper(self, tool_name: str):
        """Wrapper to import and call actual MCP tool"""

        async def tool_func(**kwargs) -> ToolResult:
            try:
                # Import the actual tool from server.py
                from jesse_mcp import server

                # Get the tool function
                tool = getattr(server, tool_name, None)
                if not tool:
                    return ToolResult(
                        success=False, error=f"Tool '{tool_name}' not found"
                    )

                # Call the tool
                if asyncio.iscoroutinefunction(tool):
                    result = await tool(**kwargs)
                else:
                    result = tool(**kwargs)

                return ToolResult(success=True, data=result)

            except Exception as e:
                logger.error(f"❌ Tool error ({tool_name}): {e}")
                return ToolResult(success=False, error=str(e))

        return tool_func

    # ==================== Phase 1: Backtesting Tools ====================

    async def backtest(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        **kwargs,
    ) -> ToolResult:
        """Run a single backtest"""
        return await self.tools_cache["backtest"](
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )

    async def strategy_list(self) -> ToolResult:
        """List available strategies"""
        return await self.tools_cache["strategy_list"]()

    async def strategy_read(self, name: str) -> ToolResult:
        """Read strategy source code"""
        return await self.tools_cache["strategy_read"](name=name)

    async def strategy_validate(self, code: str) -> ToolResult:
        """Validate strategy code"""
        return await self.tools_cache["strategy_validate"](code=code)

    async def candles_import(
        self,
        exchange: str,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
    ) -> ToolResult:
        """Download candle data"""
        return await self.tools_cache["candles_import"](
            exchange=exchange, symbol=symbol, start_date=start_date, end_date=end_date
        )

    async def analyze_results(
        self, backtest_result: Dict[str, Any], analysis_type: str = "basic"
    ) -> ToolResult:
        """Analyze backtest results"""
        return await self.tools_cache["analyze_results"](
            backtest_result=backtest_result, analysis_type=analysis_type
        )

    # ==================== Phase 3: Optimization Tools ====================

    async def optimize(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        param_space: Dict[str, Any],
        **kwargs,
    ) -> ToolResult:
        """Optimize strategy hyperparameters"""
        return await self.tools_cache["optimize"](
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            param_space=param_space,
            **kwargs,
        )

    async def walk_forward(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        **kwargs,
    ) -> ToolResult:
        """Perform walk-forward analysis"""
        return await self.tools_cache["walk_forward"](
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )

    async def backtest_batch(
        self,
        strategy: str,
        symbols: List[str],
        timeframes: List[str],
        start_date: str,
        end_date: str,
        **kwargs,
    ) -> ToolResult:
        """Run multiple backtests concurrently"""
        return await self.tools_cache["backtest_batch"](
            strategy=strategy,
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            **kwargs,
        )

    # ==================== Phase 4: Risk Analysis Tools ====================

    async def monte_carlo(
        self, backtest_result: Dict[str, Any], simulations: int = 10000, **kwargs
    ) -> ToolResult:
        """Run Monte Carlo simulation"""
        return await self.tools_cache["monte_carlo"](
            backtest_result=backtest_result, simulations=simulations, **kwargs
        )

    async def var_calculation(
        self,
        backtest_result: Dict[str, Any],
        confidence_levels: Optional[List[float]] = None,
        **kwargs,
    ) -> ToolResult:
        """Calculate Value at Risk"""
        return await self.tools_cache["var_calculation"](
            backtest_result=backtest_result,
            confidence_levels=confidence_levels,
            **kwargs,
        )

    async def stress_test(
        self,
        backtest_result: Dict[str, Any],
        scenarios: Optional[List[str]] = None,
        **kwargs,
    ) -> ToolResult:
        """Run stress test with market scenarios"""
        return await self.tools_cache["stress_test"](
            backtest_result=backtest_result, scenarios=scenarios, **kwargs
        )

    async def risk_report(
        self, backtest_result: Dict[str, Any], **kwargs
    ) -> ToolResult:
        """Generate comprehensive risk report"""
        return await self.tools_cache["risk_report"](
            backtest_result=backtest_result, **kwargs
        )

    # ==================== Phase 5: Pairs Trading Tools ====================

    async def correlation_matrix(
        self, backtest_results: List[Dict[str, Any]], **kwargs
    ) -> ToolResult:
        """Analyze cross-asset correlations"""
        return await self.tools_cache["correlation_matrix"](
            backtest_results=backtest_results, **kwargs
        )

    async def pairs_backtest(
        self,
        pair: Dict[str, str],
        backtest_result_1: Dict[str, Any],
        backtest_result_2: Dict[str, Any],
        **kwargs,
    ) -> ToolResult:
        """Backtest pairs trading strategy"""
        return await self.tools_cache["pairs_backtest"](
            pair=pair,
            backtest_result_1=backtest_result_1,
            backtest_result_2=backtest_result_2,
            **kwargs,
        )

    async def factor_analysis(
        self, backtest_result: Dict[str, Any], **kwargs
    ) -> ToolResult:
        """Decompose returns into systematic factors"""
        return await self.tools_cache["factor_analysis"](
            backtest_result=backtest_result, **kwargs
        )

    async def regime_detector(
        self, backtest_results: List[Dict[str, Any]], **kwargs
    ) -> ToolResult:
        """Identify market regimes and transitions"""
        return await self.tools_cache["regime_detector"](
            backtest_results=backtest_results, **kwargs
        )

    # ==================== Helper Methods ====================

    def get_available_tools(self) -> List[str]:
        """Get list of all available tools"""
        return sorted(list(self.tools_cache.keys()))

    def get_tool_count(self) -> int:
        """Get total number of tools"""
        return len(self.tools_cache)

    async def compare_strategies(
        self,
        strategy_1: str,
        strategy_2: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        Helper: Run A/B comparison of two strategies

        This orchestrates multiple tools to compare two strategies:
        1. Run backtest on both
        2. Analyze results for both
        3. Compare metrics
        4. Generate recommendation
        """
        logger.info(f"🔄 Comparing {strategy_1} vs {strategy_2}...")

        # Run both backtests
        result_1 = await self.backtest(
            strategy=strategy_1,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )

        result_2 = await self.backtest(
            strategy=strategy_2,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
        )

        if not (result_1.success and result_2.success):
            return {"success": False, "error": "Failed to run backtests"}

        # Analyze both
        analysis_1 = await self.analyze_results(result_1.data)
        analysis_2 = await self.analyze_results(result_2.data)

        # Extract key metrics
        metrics_1 = self._extract_metrics(result_1.data)
        metrics_2 = self._extract_metrics(result_2.data)

        # Compare
        return {
            "success": True,
            "strategy_1": {
                "name": strategy_1,
                "metrics": metrics_1,
                "analysis": analysis_1.data if analysis_1.success else None,
            },
            "strategy_2": {
                "name": strategy_2,
                "metrics": metrics_2,
                "analysis": analysis_2.data if analysis_2.success else None,
            },
            "winner": strategy_1
            if metrics_1.get("sharpe_ratio", 0) > metrics_2.get("sharpe_ratio", 0)
            else strategy_2,
            "improvements": self._calculate_improvements(metrics_1, metrics_2),
        }

    def _extract_metrics(self, backtest_result: Dict[str, Any]) -> Dict[str, float]:
        """Extract key metrics from backtest result"""
        return {
            "total_return": backtest_result.get("total_return", 0),
            "sharpe_ratio": backtest_result.get("sharpe_ratio", 0),
            "max_drawdown": backtest_result.get("max_drawdown", 0),
            "win_rate": backtest_result.get("win_rate", 0),
            "total_trades": backtest_result.get("total_trades", 0),
        }

    def _calculate_improvements(
        self, metrics_1: Dict[str, float], metrics_2: Dict[str, float]
    ) -> Dict[str, str]:
        """Calculate improvements from strategy_1 to strategy_2"""
        improvements = {}

        for key in ["total_return", "sharpe_ratio", "win_rate"]:
            if key in metrics_1 and key in metrics_2 and metrics_1[key] > 0:
                pct_change = ((metrics_2[key] - metrics_1[key]) / metrics_1[key]) * 100
                improvements[key] = f"{pct_change:+.1f}%"

        return improvements


# Global instance for easy access
_tool_interface = None


def get_tool_interface() -> MCPToolInterface:
    """Get or create global tool interface instance"""
    global _tool_interface
    if _tool_interface is None:
        _tool_interface = MCPToolInterface()
    return _tool_interface
