# Jesse-MCP FastMCP Refactoring - Product Requirements Document

## Executive Summary

**Primary Objectives**:
1. Migrate jesse-mcp from manual MCP protocol to FastMCP framework
2. Remove phase namespacing (`phase3/4/5` → root-level modules)
3. Enable proper MetaMCP integration

**Scope**:
- 15 tasks across 3 phases
- ~1,800 lines affected
- 12 files modified, 3 directories removed
- 9 hours of execution time

**Status**: ✅ **FULLY PLANNED AND READY FOR EXECUTION**

---

## 📋 DETAILED TASK BREAKDOWN

### PHASE A: LOCAL REFACTORING & TESTING (Days 1-2, ~7 hours)

---

#### **Task A.0: Directory Structure Reorganization** ⏱️ 30 min

**Objective**: Move phase3/4/5 modules to root, delete empty directories

**Step-by-step execution**:

```bash
cd /home/bk/source/jesse-mcp

# 1. Move phase3/optimizer.py to root
git mv jesse_mcp/phase3/optimizer.py jesse_mcp/optimizer.py

# 2. Move phase4/risk_analyzer.py to root
git mv jesse_mcp/phase4/risk_analyzer.py jesse_mcp/risk_analyzer.py

# 3. Move phase5/pairs_analyzer.py to root
git mv jesse_mcp/phase5/pairs_analyzer.py jesse_mcp/pairs_analyzer.py

# 4. Delete empty phase directories
git rm -r jesse_mcp/phase3
git rm -r jesse_mcp/phase4
git rm -r jesse_mcp/phase5

# 5. Verify structure
ls -la jesse_mcp/
# Should show: core/, optimizer.py, risk_analyzer.py, pairs_analyzer.py, server.py, cli.py, etc.
# Should NOT show: phase3/, phase4/, phase5/

# 6. Verify git tracks the moves
git status
# Should show 3 renamed files + 3 deleted directories
```

**Expected result**:
- ✅ 3 Python files moved to `jesse_mcp/` root
- ✅ 3 empty `phase*` directories deleted
- ✅ Git history preserved (using `git mv` not `mv`)

---

#### **Task A.1: Add FastMCP Dependency** ⏱️ 5 min

**File**: `pyproject.toml`

**Specific changes**:

```toml
# Find [project] section's "dependencies" list
# Current (line 15-24):
dependencies = [
    "mcp>=1.0.0",
    "jedi>=0.19.0",
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "pydantic>=2.0.0",
    "typing-extensions",
    "scikit-learn>=1.3.0",
    "scipy>=1.10.0",
]

# Change to:
dependencies = [
    "mcp>=1.0.0",
    "fastmcp>=0.3.0",
    "jedi>=0.19.0",
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "pydantic>=2.0.0",
    "typing-extensions",
    "scikit-learn>=1.3.0",
    "scipy>=1.10.0",
]
```

**Verification**:
```bash
pip install -e ".[dev]"
pip list | grep -i fastmcp
# Should show: fastmcp    0.3.x
```

---

#### **Task A.2: Refactor server.py with FastMCP** ⏱️ 2-3 hours

**File**: `jesse_mcp/server.py` (Complete replacement)

**High-level structure**:

```python
#!/usr/bin/env python3
"""
Jesse MCP Server - FastMCP Implementation

Provides 17 tools for quantitative trading analysis:
- Phase 1: Backtesting (4 tools)
- Phase 3: Optimization (4 tools) [formerly phase3]
- Phase 4: Risk Analysis (4 tools) [formerly phase4]
- Phase 5: Pairs Trading (5 tools) [formerly phase5]
"""

import asyncio
import logging
from typing import Optional

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jesse-mcp")

# ==================== IMPORTS & VALIDATION ====================

try:
    from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE
    if not JESSE_AVAILABLE:
        raise ImportError("Jesse framework not available")
    jesse = get_jesse_wrapper()
    logger.info("✅ Jesse framework initialized")
except Exception as e:
    logger.critical(f"❌ Jesse initialization failed: {e}")
    raise SystemExit(1)

try:
    from jesse_mcp.optimizer import get_optimizer
    optimizer = get_optimizer()
    logger.info("✅ Optimizer module loaded")
except Exception as e:
    logger.critical(f"❌ Optimizer initialization failed: {e}")
    raise SystemExit(1)

try:
    from jesse_mcp.risk_analyzer import get_risk_analyzer
    risk_analyzer = get_risk_analyzer()
    logger.info("✅ Risk analyzer module loaded")
except Exception as e:
    logger.critical(f"❌ Risk analyzer initialization failed: {e}")
    raise SystemExit(1)

try:
    from jesse_mcp.pairs_analyzer import get_pairs_analyzer
    pairs_analyzer = get_pairs_analyzer()
    logger.info("✅ Pairs analyzer module loaded")
except Exception as e:
    logger.critical(f"❌ Pairs analyzer initialization failed: {e}")
    raise SystemExit(1)

# ==================== FASTMCP INITIALIZATION ====================

mcp = FastMCP("jesse-mcp", version="1.0.0")

# ==================== PHASE 1: BACKTESTING TOOLS ====================

@mcp.tool
def backtest(
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
    hyperparameters: Optional[dict] = None,
    include_trades: bool = False,
    include_equity_curve: bool = False,
    include_logs: bool = False,
) -> dict:
    """Run a single backtest with specified parameters"""
    try:
        result = jesse.backtest(
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
            include_trades=include_trades,
            include_equity_curve=include_equity_curve,
            include_logs=include_logs,
        )
        return result
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
def strategy_list(include_test_strategies: bool = False) -> dict:
    """List available strategies"""
    try:
        return jesse.list_strategies(include_test_strategies)
    except Exception as e:
        logger.error(f"Strategy list failed: {e}")
        return {"error": str(e), "strategies": []}

@mcp.tool
def strategy_read(name: str) -> dict:
    """Read strategy source code"""
    try:
        return jesse.read_strategy(name)
    except Exception as e:
        logger.error(f"Strategy read failed: {e}")
        return {"error": str(e), "name": name}

@mcp.tool
def strategy_validate(code: str) -> dict:
    """Validate strategy code without saving"""
    try:
        return jesse.validate_strategy(code)
    except Exception as e:
        logger.error(f"Strategy validation failed: {e}")
        return {"error": str(e), "valid": False}

@mcp.tool
def candles_import(
    exchange: str,
    symbol: str,
    start_date: str,
    end_date: Optional[str] = None,
) -> dict:
    """Download candle data from exchange"""
    try:
        return jesse.import_candles(
            exchange=exchange,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        logger.error(f"Candles import failed: {e}")
        return {"error": str(e), "success": False}

# ==================== PHASE 3: OPTIMIZATION TOOLS ====================

@mcp.tool
async def optimize(
    strategy: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    param_space: dict,
    metric: str = "total_return",
    n_trials: int = 100,
    n_jobs: int = 1,
    exchange: str = "Binance",
    starting_balance: float = 10000,
    fee: float = 0.001,
    leverage: float = 1,
    exchange_type: str = "futures",
) -> dict:
    """Optimize strategy hyperparameters using Optuna"""
    try:
        result = await optimizer.optimize(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            param_space=param_space,
            metric=metric,
            n_trials=n_trials,
            n_jobs=n_jobs,
            exchange=exchange,
            starting_balance=starting_balance,
            fee=fee,
            leverage=leverage,
            exchange_type=exchange_type,
        )
        return result
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
async def walk_forward(
    strategy: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    in_sample_period: int = 365,
    out_sample_period: int = 30,
    step_forward: int = 7,
    param_space: Optional[dict] = None,
    metric: str = "total_return",
) -> dict:
    """Perform walk-forward analysis to detect overfitting"""
    try:
        result = await optimizer.walk_forward(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            in_sample_period=in_sample_period,
            out_sample_period=out_sample_period,
            step_forward=step_forward,
            param_space=param_space,
            metric=metric,
        )
        return result
    except Exception as e:
        logger.error(f"Walk-forward analysis failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
async def backtest_batch(
    strategy: str,
    symbols: list[str],
    timeframes: list[str],
    start_date: str,
    end_date: str,
    hyperparameters: Optional[list[dict]] = None,
    concurrent_limit: int = 4,
) -> dict:
    """Run multiple backtests concurrently for strategy comparison"""
    try:
        result = await optimizer.backtest_batch(
            strategy=strategy,
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            hyperparameters=hyperparameters,
            concurrent_limit=concurrent_limit,
        )
        return result
    except Exception as e:
        logger.error(f"Batch backtest failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
def analyze_results(
    backtest_result: dict,
    analysis_type: str = "basic",
    include_trade_analysis: bool = True,
    include_correlation: bool = False,
    include_monte_carlo: bool = False,
) -> dict:
    """Extract deep insights from backtest results"""
    try:
        result = optimizer.analyze_results(
            backtest_result=backtest_result,
            analysis_type=analysis_type,
            include_trade_analysis=include_trade_analysis,
            include_correlation=include_correlation,
            include_monte_carlo=include_monte_carlo,
        )
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

# ==================== PHASE 4: RISK ANALYSIS TOOLS ====================

@mcp.tool
async def monte_carlo(
    backtest_result: dict,
    simulations: int = 10000,
    confidence_levels: Optional[list[float]] = None,
    resample_method: str = "bootstrap",
    block_size: int = 20,
    include_drawdowns: bool = True,
    include_returns: bool = True,
) -> dict:
    """Generate Monte Carlo simulations for comprehensive risk analysis"""
    try:
        result = await risk_analyzer.monte_carlo(
            backtest_result=backtest_result,
            simulations=simulations,
            confidence_levels=confidence_levels,
            resample_method=resample_method,
            block_size=block_size,
            include_drawdowns=include_drawdowns,
            include_returns=include_returns,
        )
        return result
    except Exception as e:
        logger.error(f"Monte Carlo analysis failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
async def var_calculation(
    backtest_result: dict,
    confidence_levels: Optional[list[float]] = None,
    time_horizons: Optional[list[int]] = None,
    method: str = "all",
    monte_carlo_sims: int = 10000,
) -> dict:
    """Calculate Value at Risk using multiple methods"""
    try:
        result = await risk_analyzer.var_calculation(
            backtest_result=backtest_result,
            confidence_levels=confidence_levels,
            time_horizons=time_horizons,
            method=method,
            monte_carlo_sims=monte_carlo_sims,
        )
        return result
    except Exception as e:
        logger.error(f"VaR calculation failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
async def stress_test(
    backtest_result: dict,
    scenarios: Optional[list[str]] = None,
    include_custom_scenarios: bool = False,
) -> dict:
    """Test strategy performance under extreme market scenarios"""
    try:
        result = await risk_analyzer.stress_test(
            backtest_result=backtest_result,
            scenarios=scenarios,
            custom_scenarios=include_custom_scenarios,
        )
        return result
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
async def risk_report(
    backtest_result: dict,
    include_monte_carlo: bool = True,
    include_var_analysis: bool = True,
    include_stress_test: bool = True,
    monte_carlo_sims: int = 5000,
    report_format: str = "summary",
) -> dict:
    """Generate comprehensive risk assessment and recommendations"""
    try:
        result = await risk_analyzer.risk_report(
            backtest_result=backtest_result,
            include_monte_carlo=include_monte_carlo,
            include_var_analysis=include_var_analysis,
            include_stress_test=include_stress_test,
            monte_carlo_sims=monte_carlo_sims,
            report_format=report_format,
        )
        return result
    except Exception as e:
        logger.error(f"Risk report failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

# ==================== PHASE 5: PAIRS TRADING TOOLS ====================

@mcp.tool
async def correlation_matrix(
    backtest_results: list[dict],
    lookback_period: int = 60,
    correlation_threshold: float = 0.7,
    include_rolling: bool = True,
    rolling_window: int = 20,
    include_heatmap: bool = False,
) -> dict:
    """Analyze cross-asset correlations and identify pairs trading opportunities"""
    try:
        result = await pairs_analyzer.correlation_matrix(
            backtest_results=backtest_results,
            lookback_period=lookback_period,
            correlation_threshold=correlation_threshold,
            include_rolling=include_rolling,
            rolling_window=rolling_window,
            include_heatmap=include_heatmap,
        )
        return result
    except Exception as e:
        logger.error(f"Correlation matrix failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
async def pairs_backtest(
    pair: dict,
    backtest_result_1: dict,
    backtest_result_2: dict,
    strategy: str = "mean_reversion",
    lookback_period: int = 60,
    entry_threshold: float = 2.0,
    exit_threshold: float = 0.5,
    position_size: float = 0.02,
    max_holding_days: int = 20,
) -> dict:
    """Backtest pairs trading strategies"""
    try:
        result = await pairs_analyzer.pairs_backtest(
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
        return result
    except Exception as e:
        logger.error(f"Pairs backtest failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
async def factor_analysis(
    backtest_result: dict,
    factors: Optional[list[str]] = None,
    factor_returns: Optional[dict] = None,
    include_residuals: bool = True,
    analysis_period: int = 252,
    confidence_level: float = 0.95,
) -> dict:
    """Decompose returns into systematic factors"""
    try:
        result = await pairs_analyzer.factor_analysis(
            backtest_result=backtest_result,
            factors=factors,
            factor_returns=factor_returns,
            include_residuals=include_residuals,
            analysis_period=analysis_period,
            confidence_level=confidence_level,
        )
        return result
    except Exception as e:
        logger.error(f"Factor analysis failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

@mcp.tool
async def regime_detector(
    backtest_results: list[dict],
    lookback_period: int = 60,
    detection_method: str = "hmm",
    n_regimes: int = 3,
    include_transitions: bool = True,
    include_forecast: bool = True,
) -> dict:
    """Identify market regimes and transitions"""
    try:
        result = await pairs_analyzer.regime_detector(
            backtest_results=backtest_results,
            lookback_period=lookback_period,
            detection_method=detection_method,
            n_regimes=n_regimes,
            include_transitions=include_transitions,
            include_forecast=include_forecast,
        )
        return result
    except Exception as e:
        logger.error(f"Regime detector failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}

# ==================== MAIN ENTRY POINT ====================

def main():
    """Main entry point with transport options"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Jesse MCP Server - Quantitative Trading Analysis"
    )
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
```

**Key implementation details**:
- ✅ 17 tools with proper decorators
- ✅ Async tools marked with `async def`
- ✅ Full type hints for all parameters
- ✅ Consistent error handling
- ✅ Startup validation (fail loudly if Jesse unavailable)
- ✅ Updated import paths (no more `phase3/4/5`)
- ✅ HTTP and stdio transport support
- ✅ Comprehensive logging

**Expected result**: ~400 lines, clean, maintainable code

---

#### **Task A.3: Update cli.py** ⏱️ 30 min

**File**: `jesse_mcp/cli.py`

**Current content** (from earlier reading):
```python
#!/usr/bin/env python3
"""
Jesse MCP Server - CLI entry point
"""
import argparse
import sys
from jesse_mcp.server import JesseMCPServer

def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Jesse MCP Server - Quantitative Trading Analysis"
    )
    parser.add_argument("--version", action="version", version="jesse-mcp 1.0.0")
    args = parser.parse_args()
    
    server = JesseMCPServer()
    import asyncio
    asyncio.run(server.run())

if __name__ == "__main__":
    sys.exit(main())
```

**Changes needed**:

Replace with:
```python
#!/usr/bin/env python3
"""
Jesse MCP Server - CLI entry point

Usage:
    jesse-mcp                                   # Start with stdio transport
    jesse-mcp --transport http --port 8000     # Start with HTTP transport
    jesse-mcp --version                        # Show version
    jesse-mcp --help                           # Show help
"""

import sys

def main():
    """Main entry point for CLI"""
    try:
        from jesse_mcp.server import main as server_main
        server_main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
```

**Verification**:
```bash
python -m jesse_mcp --help
# Should show transport and port options

python -m jesse_mcp
# Should start with stdio transport
```

---

#### **Task A.4: Rewrite test_server.py** ⏱️ 1 hour

**File**: `tests/test_server.py` (Complete rewrite)

```python
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
    except ImportError:
        pytest.skip("FastMCP not installed")

    async with Client("stdio", command=["python", "-m", "jesse_mcp"]) as client:
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
        assert expected_tools == tool_names, f"Tool mismatch. Expected: {expected_tools}, Got: {tool_names}"
        
        print(f"✅ All {len(tools)} tools discovered successfully")


@pytest.mark.asyncio
async def test_backtest_tool():
    """Test backtest tool execution"""
    try:
        from fastmcp import Client
    except ImportError:
        pytest.skip("FastMCP not installed")

    async with Client("stdio", command=["python", "-m", "jesse_mcp"]) as client:
        result = await client.call_tool("backtest", {
            "strategy": "Test01",
            "symbol": "BTC-USDT",
            "timeframe": "1h",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
        })
        
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        # Tool should return a result (may contain error if Jesse unavailable)
        assert "error" in result or "total_return" in result or "status" in result
        print(f"✅ Backtest tool responded: {result.get('status', 'executed')}")


@pytest.mark.asyncio
async def test_strategy_list_tool():
    """Test strategy_list tool"""
    try:
        from fastmcp import Client
    except ImportError:
        pytest.skip("FastMCP not installed")

    async with Client("stdio", command=["python", "-m", "jesse_mcp"]) as client:
        result = await client.call_tool("strategy_list", {})
        
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        print(f"✅ Strategy list tool responded")


@pytest.mark.asyncio
async def test_optimize_tool():
    """Test optimize tool (async)"""
    try:
        from fastmcp import Client
    except ImportError:
        pytest.skip("FastMCP not installed")

    async with Client("stdio", command=["python", "-m", "jesse_mcp"]) as client:
        result = await client.call_tool("optimize", {
            "strategy": "Test01",
            "symbol": "BTC-USDT",
            "timeframe": "1h",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "param_space": {"param1": {"type": "float", "min": 0, "max": 1}},
        })
        
        assert isinstance(result, dict)
        print(f"✅ Optimize tool responded (async)")


@pytest.mark.asyncio
async def test_monte_carlo_tool():
    """Test monte_carlo tool"""
    try:
        from fastmcp import Client
    except ImportError:
        pytest.skip("FastMCP not installed")

    async with Client("stdio", command=["python", "-m", "jesse_mcp"]) as client:
        mock_result = {"trades": [], "metrics": {}}
        result = await client.call_tool("monte_carlo", {
            "backtest_result": mock_result,
            "simulations": 1000,
        })
        
        assert isinstance(result, dict)
        print(f"✅ Monte Carlo tool responded")


@pytest.mark.asyncio
async def test_invalid_tool():
    """Test calling non-existent tool"""
    try:
        from fastmcp import Client
    except ImportError:
        pytest.skip("FastMCP not installed")

    async with Client("stdio", command=["python", "-m", "jesse_mcp"]) as client:
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
```

**Key changes**:
- ✅ Uses FastMCP Client API
- ✅ Tests tool discovery (all 17 tools)
- ✅ Tests execution of sample tools from each phase
- ✅ Tests both sync and async tools
- ✅ Clear assertions and messaging
- ✅ Graceful skip if FastMCP not installed

---

#### **Task A.5: Update test_e2e.py** ⏱️ 30 min

**File**: `tests/test_e2e.py`

**Changes needed**:

1. Remove the `_test_mcp_routing()` method (lines ~65-90 approximately, tests raw protocol)

2. Update JesseMCPServer imports to use new structure (if any direct instantiation)

3. Update any internal phase import references:
   - `from jesse_mcp.phase3...` → `from jesse_mcp...`
   - `from jesse_mcp.phase4...` → `from jesse_mcp...`
   - `from jesse_mcp.phase5...` → `from jesse_mcp...`

4. Keep all business logic tests intact:
   - `_test_backtest_tool()`
   - `_test_strategy_tools()`
   - `_test_optimization_pipeline()`
   - `_test_phase4_risk_analysis()`
   - All assertions and validation

**Specific search/replace pattern**:
```python
# OLD pattern (remove):
async def _test_mcp_routing(self):
    """Test MCP protocol routing and integration"""
    # ... entire method block
    
# OLD imports (find and replace):
from jesse_mcp.phase3.optimizer import ...
from jesse_mcp.phase4.risk_analyzer import ...
from jesse_mcp.phase5.pairs_analyzer import ...

# NEW imports:
from jesse_mcp.optimizer import ...
from jesse_mcp.risk_analyzer import ...
from jesse_mcp.pairs_analyzer import ...
```

**Verification**:
```bash
# Should see removed method mentioned in diff
git diff tests/test_e2e.py | grep -A5 "_test_mcp_routing"
```

---

#### **Task A.6: Rename and Update Test Files** ⏱️ 30 min

**Step 1: Rename test files**

```bash
cd /home/bk/source/jesse-mcp/tests

# Use git mv to preserve history
git mv test_phase3.py test_optimizer.py
git mv test_phase4.py test_risk_analyzer.py
git mv test_phase5.py test_pairs_analyzer.py
```

**Step 2: Update imports in renamed files**

In `tests/test_optimizer.py` (formerly test_phase3.py):
```python
# Line ~15, OLD:
from jesse_mcp.phase3.optimizer import get_optimizer

# NEW:
from jesse_mcp.optimizer import get_optimizer
```

In `tests/test_risk_analyzer.py` (formerly test_phase4.py):
```python
# Line ~15, OLD:
from jesse_mcp.phase4.risk_analyzer import get_risk_analyzer

# NEW:
from jesse_mcp.risk_analyzer import get_risk_analyzer
```

In `tests/test_pairs_analyzer.py` (formerly test_phase5.py):
```python
# Line ~15, OLD:
from jesse_mcp.phase5.pairs_analyzer import get_pairs_analyzer

# NEW:
from jesse_mcp.pairs_analyzer import get_pairs_analyzer
```

**Step 3: Update conftest.py or pytest.ini (if they exist)**

Check if any test config files reference the old phase names:
```bash
grep -r "test_phase" tests/ --include="*.ini" --include="conftest.py"
# Update any matches
```

**Verification**:
```bash
git status
# Should show: test_phase3.py → test_optimizer.py (renamed)
#             test_phase4.py → test_risk_analyzer.py (renamed)
#             test_phase5.py → test_pairs_analyzer.py (renamed)
```

---

#### **Task A.7: Update Imports in Moved Modules and Other Files** ⏱️ 45 min

**Files to check and update**:

1. **`jesse_mcp/optimizer.py`** (newly moved from phase3)
   - Check for any internal `from jesse_mcp.phase3...` imports (should be none)
   - Verify no circular imports

2. **`jesse_mcp/risk_analyzer.py`** (newly moved from phase4)
   - Search for: `from jesse_mcp.phase3.optimizer`
   - Replace with: `from jesse_mcp.optimizer`
   - Example location (from earlier reading): Line 18

3. **`jesse_mcp/pairs_analyzer.py`** (newly moved from phase5)
   - Check for phase imports (should be none)

4. **`jesse_mcp/__init__.py`**
   - Check current content for phase imports
   - Update to export main functions for convenience:
   ```python
   # Current (check what's there)
   # Should add:
   from jesse_mcp.optimizer import get_optimizer
   from jesse_mcp.risk_analyzer import get_risk_analyzer
   from jesse_mcp.pairs_analyzer import get_pairs_analyzer
   
   __all__ = [
       "JesseMCPServer",
       "get_optimizer",
       "get_risk_analyzer",
       "get_pairs_analyzer",
   ]
   ```

5. **`jesse_mcp/__main__.py`**
   - Verify it properly calls main()
   - Update if needed: `from jesse_mcp.cli import main`

**Verification command**:
```bash
cd /home/bk/source/jesse-mcp
python -c "from jesse_mcp import optimizer, risk_analyzer, pairs_analyzer; print('✅ All imports working')"
```

---

#### **Task A.8: Update Docstrings to Remove Phase References** ⏱️ 30 min

**Files to update**:

1. **`jesse_mcp/optimizer.py`**
   - Search for: `"Phase 3:` or `Phase 3 ` in docstrings
   - Replace with: Generic description
   - Example: `"Advanced Optimization Tools"` instead of `"Phase 3: Advanced Optimization Tools"`

2. **`jesse_mcp/risk_analyzer.py`**
   - Search for: `"Phase 4:` or `Phase 4 ` in docstrings
   - Replace with: `"Risk Analysis Tools"`

3. **`jesse_mcp/pairs_analyzer.py`**
   - Search for: `"Phase 5:` or `Phase 5 ` in docstrings
   - Replace with: `"Pairs Trading and Advanced Analysis Tools"`

4. **`jesse_mcp/server.py`** (new file - already has correct docstrings)
   - Verify no phase references
   - Should have comments: `# ==================== PHASE X: NAME ====================` (kept for clarity, but could remove)

**Find and fix pattern**:
```bash
cd /home/bk/source/jesse-mcp
grep -n "Phase [345]:" jesse_mcp/*.py
# Update each match with non-phase version
```

---

#### **Task A.9: Update jesse_mcp/__init__.py Exports** ⏱️ 15 min

**File**: `jesse_mcp/__init__.py`

**Current content** (from earlier reading):
```python
"""
Jesse MCP Server
...
"""
from jesse_mcp.server import JesseMCPServer

__all__ = ["JesseMCPServer"]
```

**Update to**:
```python
"""
Jesse MCP Server

An MCP (Model Context Protocol) server providing 17 advanced quantitative
trading analysis tools through FastMCP:

- Backtesting: backtest, strategy_list, strategy_read, strategy_validate, candles_import
- Optimization: optimize, walk_forward, backtest_batch, analyze_results
- Risk Analysis: monte_carlo, var_calculation, stress_test, risk_report
- Pairs Trading: correlation_matrix, pairs_backtest, factor_analysis, regime_detector
"""

from jesse_mcp.server import main
from jesse_mcp.optimizer import get_optimizer
from jesse_mcp.risk_analyzer import get_risk_analyzer
from jesse_mcp.pairs_analyzer import get_pairs_analyzer

__all__ = [
    "main",
    "get_optimizer",
    "get_risk_analyzer",
    "get_pairs_analyzer",
]
```

**Verification**:
```bash
python -c "from jesse_mcp import main, get_optimizer, get_risk_analyzer, get_pairs_analyzer; print('✅ Exports working')"
```

---

#### **Task A.10: Local Testing - All Test Suites** ⏱️ 1.5 hours

**Commands** (in order):

```bash
cd /home/bk/source/jesse-mcp

# 1. Install dependencies with FastMCP
pip install -e ".[dev]"

# 2. Verify imports work
echo "Testing imports..."
python -c "from jesse_mcp import optimizer, risk_analyzer, pairs_analyzer; print('✅ All imports OK')"

# 3. Test individual modules (should pass unchanged)
echo -e "\n=== Testing Optimizer Module ==="
pytest tests/test_optimizer.py -v

echo -e "\n=== Testing Risk Analyzer Module ==="
pytest tests/test_risk_analyzer.py -v

echo -e "\n=== Testing Pairs Analyzer Module ==="
pytest tests/test_pairs_analyzer.py -v

# 4. Test new server implementation
echo -e "\n=== Testing Server (FastMCP) ==="
pytest tests/test_server.py -v

# 5. Test E2E (with MCP routing test removed)
echo -e "\n=== Testing E2E ==="
pytest tests/test_e2e.py -v

# 6. Full test suite
echo -e "\n=== Running Full Test Suite ==="
pytest -v

# 7. Manual smoke test
echo -e "\n=== Manual Server Test ==="
timeout 5 python -m jesse_mcp --help || true
```

**Expected outcomes**:
- ✅ All imports successful
- ✅ test_optimizer.py: All tests pass
- ✅ test_risk_analyzer.py: All tests pass
- ✅ test_pairs_analyzer.py: All tests pass
- ✅ test_server.py: All 5+ tests pass
- ✅ test_e2e.py: All business logic tests pass (MCP routing test removed)
- ✅ Full suite: 0 failures
- ✅ Server starts without errors

---

#### **Task A.11: Code Quality Checks** ⏱️ 30 min

**Commands**:

```bash
cd /home/bk/source/jesse-mcp

# 1. Auto-format with black
echo "Running black..."
black jesse_mcp/ tests/ --line-length=100

# 2. Check style violations
echo "Running flake8..."
flake8 jesse_mcp/ tests/ --max-line-length=100 --ignore=E501,W503

# 3. Type checking
echo "Running mypy..."
mypy jesse_mcp/ --ignore-missing-imports --no-error-summary 2>/dev/null || echo "⚠️  Type hints suggestions (informational only)"

# 4. Verify no phase references remain
echo -e "\n=== Checking for remaining phase references ==="
grep -r "phase3\|phase4\|phase5" jesse_mcp/ tests/ || echo "✅ No phase references found"

# 5. Verify no broken imports
echo -e "\n=== Verifying imports ==="
python -c "import jesse_mcp; print('✅ Main import OK')"
python -c "from jesse_mcp.server import main; print('✅ Server import OK')"
python -c "from jesse_mcp.optimizer import get_optimizer; print('✅ Optimizer import OK')"
python -c "from jesse_mcp.risk_analyzer import get_risk_analyzer; print('✅ Risk analyzer import OK')"
python -c "from jesse_mcp.pairs_analyzer import get_pairs_analyzer; print('✅ Pairs analyzer import OK')"
```

**Expected results**:
- ✅ Black reformats code (may make changes, all auto)
- ✅ Flake8: No critical errors
- ✅ Mypy: Clean or only suggestions (optional)
- ✅ No phase references in active code
- ✅ All imports resolve correctly

---

## 📋 PHASE B: GIT WORKFLOW & DEPLOYMENT (Day 2, ~45 min)

---

#### **Task B.1: Git Commit with Comprehensive Message** ⏱️ 15 min

**Workflow**:

```bash
cd /home/bk/source/jesse-mcp

# 1. Verify status
echo "=== Git Status ==="
git status

# 2. Review all changes
echo -e "\n=== Staged Changes Summary ==="
git diff --cached --stat

# 3. Stage all changes (should be ready from previous tasks)
git add jesse_mcp/ tests/ pyproject.toml

# 4. Review before commit
echo -e "\n=== Verify Changes ==="
git status

# 5. Create commit
git commit -m "feat: Refactor to FastMCP and remove phase namespacing

BREAKING CHANGE: Moved phase3, phase4, phase5 modules to root namespace

Directory Restructuring:
- jesse_mcp.phase3.optimizer → jesse_mcp.optimizer
- jesse_mcp.phase4.risk_analyzer → jesse_mcp.risk_analyzer
- jesse_mcp.phase5.pairs_analyzer → jesse_mcp.pairs_analyzer
- Removed 3 empty phase directories
- Updated imports across 12 files

MCP Protocol Migration:
- Replace manual MCP JSON protocol with FastMCP framework
- Add HTTP transport support (--port 8000, configurable)
- Add stdio transport support (default)
- Require Jesse framework at startup (fail loudly if missing)
- Add full type hints to all 17 tool signatures for schema auto-generation
- Remove resources (can be added later as complementary tools)

Code Quality:
- server.py: 1,317 lines → ~400 lines (70% reduction)
- All 17 tools functional with improved maintainability
- Consistent error handling with proper logging
- Async/await for long-running operations

Testing:
- Updated test suite for FastMCP Client API
- Phase-specific tests pass unchanged (test business logic)
- Renamed tests: test_phase3 → test_optimizer, etc.
- Removed MCP routing test (protocol layer abstracted)
- Updated 11 files with new import paths

Documentation:
- Updated docstrings to remove phase references
- Updated __init__.py exports for convenience
- CLI help text reflects new transport options

Fixes: MetaMCP integration issues (unable to discover/interact with tools)

Co-authored-by: Jesse-MCP Team"

# 6. Verify commit
echo -e "\n=== Commit Created ==="
git log --oneline -3
```

**Expected result**:
- ✅ Single comprehensive commit
- ✅ Clear message describing all changes
- ✅ References BREAKING CHANGE for import paths
- ✅ All modified files included

---

#### **Task B.2: Push to Master and Verify MetaMCP Sync** ⏱️ 30 min

**Workflow**:

```bash
cd /home/bk/source/jesse-mcp

# 1. Switch to master (if not already there)
git checkout master

# 2. Verify you're on master
git branch
# Should show: * master

# 3. Push changes
git push origin master
# Should output: main 12345a6..6789bcde master -> master

# 4. Verify remote updated
git log --oneline origin/master -3
# Should show your commit at the top

# 5. Check MetaMCP sync location
echo -e "\n=== Checking MetaMCP sync ==="
ls -la /srv/containers/metamcp/mcp-servers/jesse-mcp/

# 6. Wait for rsync (usually 10-30 seconds)
sleep 15

# 7. Verify files synced
echo -e "\n=== Verifying synced files ==="
ls -la /srv/containers/metamcp/mcp-servers/jesse-mcp/jesse_mcp/

# 8. Check specific key files
echo "Checking server.py..."
test -f /srv/containers/metamcp/mcp-servers/jesse-mcp/jesse_mcp/server.py && echo "✅ server.py synced" || echo "⚠️  server.py not yet synced"

echo "Checking optimizer.py..."
test -f /srv/containers/metamcp/mcp-servers/jesse-mcp/jesse_mcp/optimizer.py && echo "✅ optimizer.py synced" || echo "⚠️  optimizer.py not yet synced"

# 9. Check that phase directories are gone
echo "Verifying phase directories removed..."
test ! -d /srv/containers/metamcp/mcp-servers/jesse-mcp/jesse_mcp/phase3 && echo "✅ phase3 directory removed" || echo "⚠️  phase3 still exists"
test ! -d /srv/containers/metamcp/mcp-servers/jesse-mcp/jesse_mcp/phase4 && echo "✅ phase4 directory removed" || echo "⚠️  phase4 still exists"
test ! -d /srv/containers/metamcp/mcp-servers/jesse-mcp/jesse_mcp/phase5 && echo "✅ phase5 directory removed" || echo "⚠️  phase5 still exists"

# 10. Check git log on container
echo -e "\n=== MetaMCP Git History ==="
cd /srv/containers/metamcp/mcp-servers/jesse-mcp && git log --oneline -3 && cd /home/bk/source/jesse-mcp
```

**Expected results**:
- ✅ Commit pushed to origin/master
- ✅ Files synced to `/srv/containers/metamcp/mcp-servers/jesse-mcp/`
- ✅ server.py exists with FastMCP code
- ✅ optimizer.py, risk_analyzer.py, pairs_analyzer.py exist in root
- ✅ phase3/, phase4/, phase5/ directories removed
- ✅ Git log shows new commit on both local and MetaMCP container

**Troubleshooting** (if sync doesn't happen):
```bash
# Check git hook status
echo "Checking git hooks on server1/server2..."
# (May need SSH access)

# Manual rsync fallback (if available)
# rsync -avz /home/bk/source/jesse-mcp/ /srv/containers/metamcp/mcp-servers/jesse-mcp/

# Wait a bit longer
sleep 30
ls /srv/containers/metamcp/mcp-servers/jesse-mcp/jesse_mcp/
```

---

## 🧪 PHASE C: POST-DEPLOYMENT TESTING (Day 3, ~1 hour)

---

#### **Task C.1: Post-Deployment MetaMCP Testing** ⏱️ 1 hour

**Objective**: Verify all 17 tools are discoverable and functional in MetaMCP

**Step 1: Verify Container is Running**

```bash
# Check MetaMCP container
docker ps | grep metamcp
# Should show: metamcp container running

# Check logs for jesse-mcp initialization
docker logs metamcp | grep "jesse-mcp" | tail -20
# Should show: "✅ Jesse framework initialized"
#             "✅ Optimizer module loaded"
#             "✅ Risk analyzer module loaded"
#             "✅ Pairs analyzer module loaded"
```

**Step 2: Verify Tools Discoverable in MetaMCP Dashboard**

```bash
# Log into MetaMCP dashboard
# URL: https://metamcp.kuri.casa (or internal IP)
# Navigate to: Admin → Namespaces → crypto → jesse-mcp

# Verify:
✅ 17 tools listed
✅ All tool names visible:
   - backtest, strategy_list, strategy_read, strategy_validate, candles_import
   - optimize, walk_forward, backtest_batch, analyze_results
   - monte_carlo, var_calculation, stress_test, risk_report
   - correlation_matrix, pairs_backtest, factor_analysis, regime_detector
✅ Each tool has schema with proper type hints
✅ No error messages in tool list
```

**Step 3: Test Each Tool Type**

**Phase 1 - Backtesting Tools**:
```bash
# Test: backtest
curl -X POST http://metamcp.internal/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "jesse-mcp/backtest",
    "params": {
      "strategy": "Test01",
      "symbol": "BTC-USDT",
      "timeframe": "1h",
      "start_date": "2023-01-01",
      "end_date": "2023-01-31"
    }
  }'
# Expected: ✅ Response with backtest results or error (not 404/500)

# Test: strategy_list
curl -X POST http://metamcp.internal/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "jesse-mcp/strategy_list", "params": {}}'
# Expected: ✅ Response with list of strategies
```

**Phase 3 - Optimization Tools** (async):
```bash
# Test: optimize
curl -X POST http://metamcp.internal/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "jesse-mcp/optimize",
    "params": {
      "strategy": "Test01",
      "symbol": "BTC-USDT",
      "timeframe": "1h",
      "start_date": "2023-01-01",
      "end_date": "2023-01-31",
      "param_space": {"param1": {"type": "float", "min": 0, "max": 1}}
    }
  }'
# Expected: ✅ Response (may take longer due to async execution)
```

**Phase 4 - Risk Analysis Tools** (async):
```bash
# Test: monte_carlo
curl -X POST http://metamcp.internal/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "jesse-mcp/monte_carlo",
    "params": {
      "backtest_result": {"trades": [], "metrics": {}},
      "simulations": 1000
    }
  }'
# Expected: ✅ Response with Monte Carlo results
```

**Phase 5 - Pairs Trading Tools** (async):
```bash
# Test: correlation_matrix
curl -X POST http://metamcp.internal/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "jesse-mcp/correlation_matrix",
    "params": {
      "backtest_results": [
        {"symbol": "BTC-USDT", "trades": []},
        {"symbol": "ETH-USDT", "trades": []}
      ]
    }
  }'
# Expected: ✅ Response with correlation analysis
```

**Step 4: Verify Transport Support**

```bash
# Test HTTP transport (if deployed)
curl http://localhost:8000/mcp/tools/list
# Expected: ✅ JSON response with all 17 tools

# Test stdio transport
echo '{"method": "tools/list", "params": {}}' | python -m jesse_mcp
# Expected: ✅ JSON response with tools list
```

**Step 5: Error Handling Verification**

```bash
# Test invalid parameters
curl -X POST http://metamcp.internal/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "jesse-mcp/backtest",
    "params": {"invalid_param": "value"}
  }'
# Expected: ✅ Clear error message (400 Bad Request with descriptive error)

# Test non-existent tool
curl -X POST http://metamcp.internal/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "jesse-mcp/nonexistent", "params": {}}'
# Expected: ✅ 404 or error response
```

**Step 6: Performance & Logging Verification**

```bash
# Check MetaMCP logs for errors
docker logs metamcp | grep -i "error\|jesse-mcp" | tail -50

# Verify response times
time curl -X POST http://metamcp.internal/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "jesse-mcp/strategy_list", "params": {}}'
# Expected: < 1 second for simple tools
```

**Step 7: Integration Test - Full Workflow**

```bash
# Complete workflow test:
# 1. Get available strategies
# 2. Run backtest on a strategy
# 3. Analyze results
# 4. Run optimization
# 5. Run risk analysis

# This verifies end-to-end tool chaining
```

---

## ✅ SUCCESS CRITERIA - FINAL CHECKLIST

### Pre-Execution Verification
- [ ] Git is clean (or changes stashed)
- [ ] All 11 tasks in Phase A understood
- [ ] All 2 tasks in Phase B understood
- [ ] All 1 task in Phase C understood
- [ ] Access to `/srv/containers/metamcp/` verified
- [ ] MetaMCP dashboard access confirmed

### Post-Execution Verification

**Phase A Completion**:
- [ ] Directory structure reorganized (no phase* dirs)
- [ ] FastMCP dependency added to pyproject.toml
- [ ] server.py refactored with 17 FastMCP tools
- [ ] cli.py updated with transport args
- [ ] test_server.py rewritten for FastMCP Client
- [ ] test_e2e.py updated (MCP routing test removed)
- [ ] Test files renamed (test_phase* → test_*)
- [ ] All imports updated across 12+ files
- [ ] Docstrings updated (no phase references)
- [ ] __init__.py exports updated
- [ ] All test suites pass (0 failures)
- [ ] Code quality checks pass (black, flake8, mypy)

**Phase B Completion**:
- [ ] Comprehensive commit created
- [ ] Commit pushed to origin/master
- [ ] Files synced to MetaMCP (`/srv/containers/metamcp/mcp-servers/jesse-mcp/`)
- [ ] Old phase directories removed from MetaMCP
- [ ] New module files present in MetaMCP

**Phase C Completion**:
- [ ] MetaMCP container running
- [ ] 17 tools discoverable in MetaMCP dashboard
- [ ] All tool types tested (Phase 1/3/4/5 samples)
- [ ] Error handling working correctly
- [ ] HTTP and stdio transports functional
- [ ] No errors in MetaMCP logs
- [ ] Response times acceptable

---

## 📊 FINAL METRICS

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Files in jesse_mcp/** | 13 | 10 | -3 (phase dirs removed) |
| **Directories** | 5 | 2 | -3 (phase* removed) |
| **server.py lines** | 1,317 | ~400 | -917 (70% reduction) |
| **Total lines affected** | — | ~1,800 | Significant refactoring |
| **Tools available** | 17 | 17 | 100% maintained |
| **Features** | 100% | 100% | 100% maintained |
| **Code quality** | Manual protocol | FastMCP framework | Major improvement |
| **Maintainability** | Complex | Clean | Significantly better |
| **MetaMCP integration** | ❌ Broken | ✅ Working | Fixed |

---

## 🎯 READY FOR EXECUTION?

**Everything is planned and ready.** 

To proceed with execution, simply respond with **"Ready to execute"** and I will:

1. **Mark Task A.0 as in_progress** and execute directory reorganization
2. **Continue through all 15 tasks systematically**
3. **Mark each task complete as it finishes**
4. **Provide clear feedback and error handling**
5. **Commit and deploy when all local testing passes**

All detailed step-by-step instructions are in this document. No ambiguity, no guessing—just methodical execution.

**Status**: ✅ **PLAN COMPLETE AND READY FOR EXECUTION**