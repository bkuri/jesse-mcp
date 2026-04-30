"""
Phase 4: Risk Analysis Tools

Monte Carlo simulation, Value at Risk, stress testing, and risk reporting.
"""

import logging
from typing import Any, Dict, List, Optional

from jesse_mcp.tools._utils import (
    async_call,
    get_client,
    require_risk_analyzer,
    tool_error_handler,
)

logger = logging.getLogger("jesse-mcp.risk")


def register_risk_tools(mcp):
    """Register risk analysis tools with the MCP server."""

    @mcp.tool
    @tool_error_handler
    async def monte_carlo(
        backtest_result: Dict[str, Any],
        simulations: int = 10000,
        confidence_levels: Optional[List[float]] = None,
        resample_method: str = "bootstrap",
        block_size: int = 20,
        include_drawdowns: bool = True,
        include_returns: bool = True,
    ) -> Dict[str, Any]:
        """Generate Monte Carlo simulations for comprehensive risk analysis"""
        ra = require_risk_analyzer()
        return await ra.monte_carlo(
            backtest_result=backtest_result,
            simulations=simulations,
            confidence_levels=confidence_levels or [],
            resample_method=resample_method,
            block_size=block_size,
            include_drawdowns=include_drawdowns,
            include_returns=include_returns,
        )

    @mcp.tool(name="native_monte_carlo")
    @tool_error_handler
    async def native_monte_carlo(
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        exchange: str = "Binance Spot",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "spot",
        run_trades: bool = True,
        run_candles: bool = False,
        num_scenarios: int = 500,
        cpu_cores: int = 1,
        fast_mode: bool = True,
        pipeline_type: str = "moving_block_bootstrap",
    ) -> Dict[str, Any]:
        """
        Run native Jesse Monte Carlo simulation with confidence analysis.

        Uses Jesse's built-in Monte Carlo engine which provides:
        - Confidence analysis with p-values and significance testing
        - Percentile distributions (5th, 25th, 50th, 75th, 95th)
        - Structured interpretation output
        - Two pipeline methods: moving_block_bootstrap (default) and gaussian_noise

        This is more rigorous than the basic monte_carlo tool as it uses
        Jesse's native research module with full statistical validation.

        Args:
            strategy: Strategy name
            symbol: Trading pair (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h", "4h")
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            run_trades: Shuffle trade order for robustness check
            run_candles: Resample candles for price data robustness
            num_scenarios: Number of simulation scenarios (default: 500)
            pipeline_type: 'moving_block_bootstrap' or 'gaussian_noise'
            fast_mode: Enable fast mode for speed (default: True)
        """
        client = get_client()
        return await async_call(
            client.native_monte_carlo,
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
            run_trades=run_trades,
            run_candles=run_candles,
            num_scenarios=num_scenarios,
            cpu_cores=cpu_cores,
            fast_mode=fast_mode,
            pipeline_type=pipeline_type,
        )

    @mcp.tool
    @tool_error_handler
    async def var_calculation(
        backtest_result: Dict[str, Any],
        confidence_levels: Optional[List[float]] = None,
        time_horizons: Optional[List[int]] = None,
        method: str = "all",
        monte_carlo_sims: int = 10000,
    ) -> Dict[str, Any]:
        """Calculate Value at Risk using multiple methods"""
        ra = require_risk_analyzer()
        return await ra.var_calculation(
            backtest_result=backtest_result,
            confidence_levels=confidence_levels or [],
            time_horizons=time_horizons or [],
            method=method,
            monte_carlo_sims=monte_carlo_sims,
        )

    @mcp.tool
    @tool_error_handler
    async def stress_test(
        backtest_result: Dict[str, Any],
        scenarios: Optional[List[str]] = None,
        include_custom_scenarios: bool = False,
    ) -> Dict[str, Any]:
        """Test strategy performance under extreme market scenarios"""
        ra = require_risk_analyzer()
        return await ra.stress_test(
            backtest_result=backtest_result,
            scenarios=scenarios,
            custom_scenarios=include_custom_scenarios,
        )

    @mcp.tool(name="risk_report")
    @tool_error_handler
    async def risk_report(
        backtest_result: Dict[str, Any],
        include_monte_carlo: bool = True,
        include_var_analysis: bool = True,
        include_stress_test: bool = True,
        monte_carlo_sims: int = 5000,
        report_format: str = "summary",
    ) -> Dict[str, Any]:
        """Generate comprehensive risk assessment and recommendations"""
        ra = require_risk_analyzer()
        return await ra.risk_report(
            backtest_result=backtest_result,
            include_monte_carlo=include_monte_carlo,
            include_var_analysis=include_var_analysis,
            include_stress_test=include_stress_test,
            monte_carlo_sims=monte_carlo_sims,
            report_format=report_format,
        )

    @mcp.tool
    @tool_error_handler
    def plot_significance_test(
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        hyperparameters: Optional[Dict[str, Any]] = None,
        n_bootstrap: int = 1000,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate bootstrap significance test histogram as PNG chart.

        Creates a histogram of the bootstrap sampling distribution with the
        observed mean annotated, saved as a PNG file. Requires local Jesse installation.

        Use alongside rule_significance_test() for visual analysis of whether
        a strategy's performance is statistically significant.

        Args:
            strategy: Strategy name to test
            symbol: Trading pair (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h", "4h")
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            exchange: Exchange name (default: Binance)
            n_bootstrap: Number of bootstrap samples (default: 1000)
            output_path: Optional custom path for the PNG file
        """
        from jesse_mcp.tools._utils import require_jesse

        return require_jesse().plot_significance_test(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
            hyperparameters=hyperparameters,
            n_bootstrap=n_bootstrap,
            output_path=output_path,
        )

    @mcp.tool
    @tool_error_handler
    def rule_significance_test(
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        hyperparameters: Optional[Dict[str, Any]] = None,
        n_bootstrap: int = 1000,
    ) -> Dict[str, Any]:
        """
        Run bootstrap-based statistical significance test for a trading rule.

        Evaluates whether a strategy's mean return is statistically distinguishable
        from random noise using bootstrap resampling. Requires local Jesse installation.

        Returns p-value, observed mean return, bootstrap distribution stats, and
        whether the result is statistically significant.

        Use this to validate that backtest results represent real alpha, not luck.

        Args:
            strategy: Strategy name to test
            symbol: Trading pair (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h", "4h")
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD
            exchange: Exchange name (default: Binance)
            n_bootstrap: Number of bootstrap samples (default: 1000)
        """
        from jesse_mcp.tools._utils import require_jesse

        return require_jesse().rule_significance_test(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
            hyperparameters=hyperparameters,
            n_bootstrap=n_bootstrap,
        )
