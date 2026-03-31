"""
Phase 5: Pairs Trading Tools

Provides cross-asset analysis for the Jesse MCP server:
- Correlation matrix analysis
- Pairs trading backtesting
- Factor analysis decomposition
- Market regime detection
"""

from typing import Any, Dict, List, Optional

from jesse_mcp.tools._utils import require_pairs_analyzer, tool_error_handler


def register_pairs_tools(mcp):
    """Register pairs trading tools with the MCP server."""

    @mcp.tool
    @tool_error_handler
    async def correlation_matrix(
        backtest_results: List[Dict[str, Any]],
        lookback_period: int = 60,
        correlation_threshold: float = 0.7,
        include_rolling: bool = True,
        rolling_window: int = 20,
        include_heatmap: bool = False,
    ) -> Dict[str, Any]:
        """Analyze cross-asset correlations and identify pairs trading opportunities"""
        pa = require_pairs_analyzer()
        return await pa.correlation_matrix(
            backtest_results=backtest_results,
            lookback_period=lookback_period,
            correlation_threshold=correlation_threshold,
            include_rolling=include_rolling,
            rolling_window=rolling_window,
            include_heatmap=include_heatmap,
        )

    @mcp.tool(name="pairs_backtest")
    @tool_error_handler
    async def pairs_backtest(
        pair: Dict[str, Any],
        backtest_result_1: Dict[str, Any],
        backtest_result_2: Dict[str, Any],
        strategy: str = "mean_reversion",
        lookback_period: int = 60,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        position_size: float = 0.02,
        max_holding_days: int = 20,
    ) -> Dict[str, Any]:
        """Backtest pairs trading strategies"""
        pa = require_pairs_analyzer()
        return await pa.pairs_backtest(
            pair=pair,
            strategy=strategy,
            backtest_result_1=backtest_result_1,
            backtest_result_2=backtest_result_2,
            lookback_period=lookback_period,
            entry_threshold=entry_threshold,
            exit_threshold=exit_threshold,
            position_size=position_size,
            max_holding_days=max_holding_days,
        )

    @mcp.tool
    @tool_error_handler
    async def factor_analysis(
        backtest_result: Dict[str, Any],
        factors: Optional[List[str]] = None,
        factor_returns: Optional[Dict[str, List[float]]] = None,
        include_residuals: bool = True,
        analysis_period: int = 252,
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """Decompose returns into systematic factors"""
        pa = require_pairs_analyzer()
        return await pa.factor_analysis(
            backtest_result=backtest_result,
            factors=factors or [],
            factor_returns=factor_returns or {},
            include_residuals=include_residuals,
            analysis_period=analysis_period,
            confidence_level=confidence_level,
        )

    @mcp.tool
    @tool_error_handler
    async def regime_detector(
        backtest_results: List[Dict[str, Any]],
        lookback_period: int = 60,
        detection_method: str = "hmm",
        n_regimes: int = 3,
        include_transitions: bool = True,
        include_forecast: bool = True,
    ) -> Dict[str, Any]:
        """Identify market regimes and transitions"""
        pa = require_pairs_analyzer()
        return await pa.regime_detector(
            backtest_results=backtest_results,
            lookback_period=lookback_period,
            detection_method=detection_method,
            n_regimes=n_regimes,
            include_transitions=include_transitions,
            include_forecast=include_forecast,
        )
