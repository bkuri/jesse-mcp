# Jesse MCP Server Refactoring Analysis

## Executive Summary

The current `server.py` contains **47 MCP tools** organized into 8 sections/phases. This analysis provides a modular refactoring strategy using FastMCP's native tool naming support, enabling namespace-like organization without code duplication.

---

## 1. CURRENT STRUCTURE

### File Statistics
- **File**: `/home/bk/source/jesse-mcp/jesse_mcp/server.py`
- **Lines**: 2,134 total
- **Tools**: 47 tools across 8 sections
- **Global Variables**: 5 (jesse, optimizer, risk_analyzer, pairs_analyzer, _initialized)

### Current Sections & Tool Counts

| Section | Tools | Lines | Key Responsibility |
|---------|-------|-------|-------------------|
| PHASE 1: Backtesting | 6 | 126-904 | Strategy execution, exchange info, candles |
| PHASE 3: Optimization | 4 | 906-1061 | Parameter optimization, walk-forward, batch testing |
| PHASE 4: Risk Analysis | 4 | 1063-1166 | Monte Carlo, VaR, stress testing |
| PHASE 5: Pairs Trading | 4 | 1168-1283 | Correlation, pairs backtest, factor analysis, regime detection |
| Cache Management | 3 | 1285-1434 | Cache stats/clear, benchmark |
| Strategy Creation | 9 | 337-858 | Strategy CRUD, jobs, metadata (Ralph Wiggum Loop) |
| Live Trading (Phase 6) | 9 | 1436-1820 | Paper & live trading sessions |
| Paper Trading | 8 | 1822-2087 | Paper trading lifecycle |

### Tool Categories by Function

```
Backtesting Phase (6 tools)
├── Status/Health: jesse_status, get_exchanges
├── Core Execution: backtest
├── Strategy CRUD: strategy_list, strategy_read, strategy_validate

Optimization Phase (4 tools)
├── Optimization: optimize
├── Analysis: walk_forward, backtest_batch, analyze_results

Risk Analysis Phase (4 tools)
├── Simulation: monte_carlo
├── Valuation: var_calculation
├── Testing: stress_test
├── Reporting: risk_report

Pairs Trading Phase (4 tools)
├── Analysis: correlation_matrix, factor_analysis, regime_detector
├── Execution: pairs_backtest

Strategy Creation (9 tools)
├── Creation: strategy_create
├── Async Jobs: strategy_create_status, strategy_create_cancel
├── Refinement: strategy_refine
├── Management: strategy_delete, strategy_metadata
├── Utility: jobs_list, candles_import, rate_limit_status

Live Trading (9 tools)
├── Plugin: live_check_plugin
├── Session Management: live_start_paper_trading, live_start_live_trading, live_cancel_session
├── Data Retrieval: live_get_sessions, live_get_status, live_get_orders, live_get_equity_curve, live_get_logs

Paper Trading (8 tools)
├── Lifecycle: paper_start, paper_stop, paper_status
├── Analysis: paper_get_trades, paper_get_equity, paper_get_metrics
├── Management: paper_list_sessions, paper_update_session

Cache & Utilities (3 tools)
├── Caching: cache_stats, cache_clear
├── Benchmarking: backtest_benchmark
```

---

## 2. REFACTORING OPPORTUNITIES

### 2.1 Problems with Current Structure

1. **Monolithic File**: 2,134 lines makes navigation and maintenance difficult
2. **Mixed Concerns**: Strategy creation, live trading, and paper trading mixed in same file
3. **No Tool Prefixing**: Tools appear flat with naming conventions (e.g., `live_*`, `paper_*`) to simulate namespaces
4. **Initialization Logic**: Lazy initialization of 5 modules embedded in single file
5. **Hidden Dependencies**: Tool relationships and data flow not immediately visible
6. **Testing Complexity**: Hard to test individual tool groups in isolation

### 2.2 Proposed Modular Structure

```
jesse_mcp/
├── server.py (REFACTORED - 400 lines)
│   ├── Main initialization (_initialize_dependencies)
│   ├── Health endpoint
│   ├── Tool registration dispatchers
│   └── Main entry point
│
├── tools/
│   ├── __init__.py
│   ├── backtesting.py (6 tools, 180 lines)
│   │   └── jesse_status, get_exchanges, backtest, strategy_list, strategy_read, strategy_validate
│   │
│   ├── optimization.py (4 tools, 130 lines)
│   │   └── optimize, walk_forward, backtest_batch, analyze_results
│   │
│   ├── risk_analysis.py (4 tools, 140 lines)
│   │   └── monte_carlo, var_calculation, stress_test, risk_report
│   │
│   ├── pairs_trading.py (4 tools, 110 lines)
│   │   └── correlation_matrix, pairs_backtest, factor_analysis, regime_detector
│   │
│   ├── strategy_creation.py (9 tools, 320 lines)
│   │   └── strategy_create, strategy_create_status, strategy_create_cancel
│   │   └── strategy_refine, strategy_delete, strategy_metadata
│   │   └── jobs_list, candles_import, rate_limit_status
│   │
│   ├── live_trading.py (9 tools, 240 lines)
│   │   └── live_check_plugin
│   │   └── live_start_paper_trading, live_start_live_trading, live_cancel_session
│   │   └── live_get_sessions, live_get_status, live_get_orders, live_get_equity_curve, live_get_logs
│   │
│   ├── paper_trading.py (8 tools, 210 lines)
│   │   └── paper_start, paper_stop, paper_status
│   │   └── paper_get_trades, paper_get_equity, paper_get_metrics
│   │   └── paper_list_sessions, paper_update_session
│   │
│   └── cache_utilities.py (3 tools, 150 lines)
│       └── cache_stats, cache_clear, backtest_benchmark
```

---

## 3. NAMESPACE PATTERN FINDINGS

### 3.1 FastMCP Tool Naming Support

FastMCP's `@mcp.tool()` decorator supports custom naming via the `name` parameter:

```python
@mcp.tool(name="backtesting:status")  # Custom name with prefix
def jesse_status():
    """Tool description"""
    pass
```

### 3.2 Recommended Namespace Strategy

Use **colon-separated prefixes** to simulate namespaces:

```
backtesting:status          (jesse_status)
backtesting:exchanges       (get_exchanges)
backtesting:run             (backtest)
backtesting:strategies:list (strategy_list)
backtesting:strategies:read (strategy_read)

optimization:run            (optimize)
optimization:walk_forward   (walk_forward)
optimization:batch          (backtest_batch)
optimization:analyze        (analyze_results)

risk:monte_carlo            (monte_carlo)
risk:var                    (var_calculation)
risk:stress_test            (stress_test)
risk:report                 (risk_report)

pairs:correlation           (correlation_matrix)
pairs:backtest              (pairs_backtest)
pairs:factors               (factor_analysis)
pairs:regime                (regime_detector)

strategy:create             (strategy_create)
strategy:create:status      (strategy_create_status)
strategy:create:cancel      (strategy_create_cancel)
strategy:refine             (strategy_refine)
strategy:delete             (strategy_delete)
strategy:metadata           (strategy_metadata)

trading:live:status         (live_check_plugin)
trading:live:paper:start    (live_start_paper_trading)
trading:live:start          (live_start_live_trading)
trading:live:cancel         (live_cancel_session)
trading:live:sessions       (live_get_sessions)
trading:live:session:status (live_get_status)
trading:live:orders         (live_get_orders)
trading:live:equity         (live_get_equity_curve)
trading:live:logs           (live_get_logs)

trading:paper:start         (paper_start)
trading:paper:stop          (paper_stop)
trading:paper:status        (paper_status)
trading:paper:trades        (paper_get_trades)
trading:paper:equity        (paper_get_equity)
trading:paper:metrics       (paper_get_metrics)
trading:paper:sessions      (paper_list_sessions)
trading:paper:update        (paper_update_session)

cache:stats                 (cache_stats)
cache:clear                 (cache_clear)
cache:benchmark             (backtest_benchmark)
```

### 3.3 Namespace Patterns Found in Codebase

**Note**: No existing namespace implementation found in the codebase. Current patterns:
- **Simple prefixes**: `live_*`, `paper_*` (string-based naming convention)
- **No tool name customization** used currently in agent_tools.py

---

## 4. DEPENDENCIES & GLOBAL STATE

### 4.1 Global Variables in server.py

```python
jesse: Optional[Any] = None              # Line 39
optimizer: Optional[Any] = None          # Line 40
risk_analyzer: Optional[Any] = None      # Line 41
pairs_analyzer: Optional[Any] = None     # Line 42
_initialized: bool = False               # Line 43
```

### 4.2 Lazy Initialization Pattern

All modules use lazy initialization pattern (lines 46-88):

```python
def _initialize_dependencies():
    global jesse, optimizer, risk_analyzer, pairs_analyzer, _initialized
    
    # Initialize from jesse_mcp.core.integrations
    # Initialize from jesse_mcp.optimizer
    # Initialize from jesse_mcp.risk_analyzer
    # Initialize from jesse_mcp.pairs_analyzer
```

**Refactoring Strategy**: Preserve this pattern but centralize initialization in `server.py`, then pass globals to tool modules via dependency injection.

### 4.3 Critical Imports (Must Be Preserved)

```python
# Core dependencies
from fastmcp import FastMCP
from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE
from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client
from jesse_mcp.core.mock import get_mock_jesse_wrapper

# Optimizer modules (lazy-loaded)
from jesse_mcp.optimizer import get_optimizer
from jesse_mcp.risk_analyzer import get_risk_analyzer
from jesse_mcp.pairs_analyzer import get_pairs_analyzer

# Validation & Strategy tools
from jesse_mcp.core.strategy_validation.metadata import (...)
from jesse_mcp.core.strategy_validator import get_validator
from jesse_mcp.core.strategy_builder import get_strategy_builder
from jesse_mcp.core.job_manager import get_job_manager

# Live trading config
from jesse_mcp.core.live_config import (...)
```

### 4.4 Import Dependencies by Tool Group

| Module | Imports | Count |
|--------|---------|-------|
| backtesting.py | jesse_rest_client, mock, integrations | 3 |
| optimization.py | jesse_rest_client, optimizer | 2 |
| risk_analysis.py | risk_analyzer | 1 |
| pairs_trading.py | pairs_analyzer | 1 |
| strategy_creation.py | strategy_validator, strategy_builder, job_manager, integrations, metadata | 5 |
| live_trading.py | jesse_rest_client, integrations, live_config, certification | 4 |
| paper_trading.py | jesse_rest_client | 1 |
| cache_utilities.py | cache, rate_limiter | 2 |

---

## 5. TOOL EXTRACTION GUIDE

### 5.1 Backtesting Tools (Lines 126-904)

**Extract to**: `jesse_mcp/tools/backtesting.py`

```python
# Tools to extract:
- jesse_status()                          [Lines 126-147]
- get_exchanges()                         [Lines 150-188]
- backtest(...)                          [Lines 190-294]
- strategy_list(...)                     [Lines 296-311]
- strategy_read(name)                    [Lines 313-323]
- strategy_validate(code)                [Lines 325-335]
- candles_import(...)                    [Lines 860-881]    # Move here from strategy section

# Dependencies to pass:
- jesse (global)
- mcp (FastMCP instance)

# Imports needed:
- logging
- Optional, Dict, Any, List from typing
- get_jesse_rest_client
- get_mock_jesse_wrapper
```

**Line Mappings for Extraction**:
- Health check: 126-147
- Exchange info: 150-188
- Backtest execution: 190-294
- Strategy CRUD: 296-335
- Candles import: 860-881

### 5.2 Optimization Tools (Lines 906-1061)

**Extract to**: `jesse_mcp/tools/optimization.py`

```python
# Tools to extract:
- optimize(...)                          [Lines 909-958]
- walk_forward(...)                      [Lines 960-993]
- backtest_batch(...)                    [Lines 995-1022]
- analyze_results(...)                   [Lines 1024-1061]

# Dependencies to pass:
- optimizer (global)
- mcp (FastMCP instance)

# Imports needed:
- logging
- Dict, Any, List, Optional from typing
- get_jesse_rest_client
```

### 5.3 Risk Analysis Tools (Lines 1063-1166)

**Extract to**: `jesse_mcp/tools/risk_analysis.py`

```python
# Tools to extract:
- monte_carlo(...)                       [Lines 1066-1093]
- var_calculation(...)                   [Lines 1095-1118]
- stress_test(...)                       [Lines 1120-1139]
- risk_report(...)                       [Lines 1141-1166]

# Dependencies to pass:
- risk_analyzer (global)
- mcp (FastMCP instance)

# Imports needed:
- logging
- Dict, Any, List, Optional from typing
```

### 5.4 Pairs Trading Tools (Lines 1168-1283)

**Extract to**: `jesse_mcp/tools/pairs_trading.py`

```python
# Tools to extract:
- correlation_matrix(...)                [Lines 1171-1196]
- pairs_backtest(...)                    [Lines 1198-1229]
- factor_analysis(...)                   [Lines 1231-1256]
- regime_detector(...)                   [Lines 1258-1283]

# Dependencies to pass:
- pairs_analyzer (global)
- mcp (FastMCP instance)

# Imports needed:
- logging
- Dict, Any, List, Optional from typing
```

### 5.5 Strategy Creation Tools (Lines 337-858)

**Extract to**: `jesse_mcp/tools/strategy_creation.py`

```python
# Tools to extract:
- strategy_create(...)                   [Lines 455-560]
- strategy_create_status(...)            [Lines 562-607]
- strategy_create_cancel(...)            [Lines 609-638]
- strategy_refine(...)                   [Lines 640-725]
- strategy_delete(...)                   [Lines 727-770]
- strategy_metadata(...)                 [Lines 810-858]
- jobs_list(...)                         [Lines 772-808]
- rate_limit_status()                    [Lines 883-904]

# Supporting function to extract:
- _strategy_create_impl(...)             [Lines 340-453]

# Dependencies to pass:
- jesse (global)
- mcp (FastMCP instance)

# Imports needed:
- logging, threading, os
- Dict, Any, List, Optional from typing
- datetime, timedelta, timezone
- Multiple strategy validation & builder modules
```

### 5.6 Live Trading Tools (Lines 1436-1820)

**Extract to**: `jesse_mcp/tools/live_trading.py`

```python
# Tools to extract:
- live_check_plugin()                    [Lines 1439-1455]
- live_start_paper_trading(...)          [Lines 1457-1548]
- live_start_live_trading(...)           [Lines 1550-1685]
- live_cancel_session(...)               [Lines 1687-1707]
- live_get_sessions(...)                 [Lines 1709-1729]
- live_get_status(...)                   [Lines 1731-1750]
- live_get_orders(...)                   [Lines 1752-1771]
- live_get_equity_curve(...)             [Lines 1773-1798]
- live_get_logs(...)                     [Lines 1800-1820]

# Dependencies to pass:
- jesse (global)
- mcp (FastMCP instance)

# Imports needed:
- logging
- Dict, Any, Optional from typing
- datetime, timedelta, timezone
- Jesse REST client, live config, certification modules
```

### 5.7 Paper Trading Tools (Lines 1822-2087)

**Extract to**: `jesse_mcp/tools/paper_trading.py`

```python
# Tools to extract:
- paper_start(...)                       [Lines 1825-1888]
- paper_stop(...)                        [Lines 1890-1917]
- paper_status(...)                      [Lines 1919-1938]
- paper_get_trades(...)                  [Lines 1940-1971]
- paper_get_equity(...)                  [Lines 1973-2014]
- paper_get_metrics(...)                 [Lines 2016-2043]
- paper_list_sessions()                  [Lines 2045-2061]
- paper_update_session(...)              [Lines 2063-2087]

# Dependencies to pass:
- mcp (FastMCP instance)

# Imports needed:
- logging
- Dict, Any, Optional from typing
- datetime
- Jesse REST client
```

### 5.8 Cache & Utilities Tools (Lines 1285-1434)

**Extract to**: `jesse_mcp/tools/cache_utilities.py`

```python
# Tools to extract:
- cache_stats()                          [Lines 1288-1303]
- cache_clear(...)                       [Lines 1305-1328]
- backtest_benchmark(...)                [Lines 1330-1434]

# Dependencies to pass:
- mcp (FastMCP instance)

# Imports needed:
- logging, time
- Dict, Any, Optional from typing
- datetime, timedelta
- get_jesse_rest_client, cache modules, rate_limiter
```

---

## 6. REFACTORED SERVER.PY STRUCTURE

### New server.py (400 lines)

```python
#!/usr/bin/env python3
"""
Jesse MCP Server - FastMCP Implementation

Provides 47 tools for quantitative trading analysis organized into 7 modules:
1. Backtesting (6 tools)
2. Optimization (4 tools)
3. Risk Analysis (4 tools)
4. Pairs Trading (4 tools)
5. Strategy Creation (9 tools)
6. Live Trading (9 tools)
7. Paper Trading (8 tools)
8. Cache & Utilities (3 tools)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jesse-mcp")

# ==================== LAZY INITIALIZATION ====================
# These will be initialized when main() is called, not at import time

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

    # [Keep existing initialization code from current server.py lines 46-88]
    
    _initialized = True


# ==================== FASTMCP INITIALIZATION ====================

mcp = FastMCP("jesse-mcp", version="1.0.0")


@mcp.custom_route("/health", methods=["GET"])
async def health_endpoint(request: Request) -> JSONResponse:
    """HTTP health endpoint for monitoring Jesse MCP server status."""
    # [Keep existing health endpoint code from current server.py lines 96-120]


# ==================== TOOL REGISTRATION ====================

def register_all_tools():
    """Register all tool modules with FastMCP"""
    from jesse_mcp.tools import (
        backtesting,
        optimization,
        risk_analysis,
        pairs_trading,
        strategy_creation,
        live_trading,
        paper_trading,
        cache_utilities,
    )
    
    # Pass mcp instance and globals to each module
    backtesting.register_tools(mcp, jesse)
    optimization.register_tools(mcp, optimizer)
    risk_analysis.register_tools(mcp, risk_analyzer)
    pairs_trading.register_tools(mcp, pairs_analyzer)
    strategy_creation.register_tools(mcp, jesse)
    live_trading.register_tools(mcp, jesse)
    paper_trading.register_tools(mcp)
    cache_utilities.register_tools(mcp)
    
    logger.info("✅ All tool modules registered")


# ==================== MAIN ENTRY POINT ====================

def main():
    """Main entry point with transport options"""
    import argparse
    
    _initialize_dependencies()
    register_all_tools()
    
    # Register agent tools
    try:
        from jesse_mcp.agent_tools import register_agent_tools
        register_agent_tools(mcp)
        logger.info("✅ Agent tools registered")
    except Exception as e:
        logger.warning(f"⚠️  Agent tools registration failed: {e}")
    
    parser = argparse.ArgumentParser(description="Jesse MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    
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

---

## 7. MIGRATION CHECKLIST

- [ ] Create `jesse_mcp/tools/` directory
- [ ] Create `jesse_mcp/tools/__init__.py` with shared utilities
- [ ] Extract backtesting tools to `jesse_mcp/tools/backtesting.py`
- [ ] Extract optimization tools to `jesse_mcp/tools/optimization.py`
- [ ] Extract risk analysis tools to `jesse_mcp/tools/risk_analysis.py`
- [ ] Extract pairs trading tools to `jesse_mcp/tools/pairs_trading.py`
- [ ] Extract strategy creation tools to `jesse_mcp/tools/strategy_creation.py`
- [ ] Extract live trading tools to `jesse_mcp/tools/live_trading.py`
- [ ] Extract paper trading tools to `jesse_mcp/tools/paper_trading.py`
- [ ] Extract cache utilities to `jesse_mcp/tools/cache_utilities.py`
- [ ] Refactor server.py to use tool registration dispatchers
- [ ] Add custom tool naming using namespace prefixes (optional)
- [ ] Update imports in tests
- [ ] Run full test suite
- [ ] Update documentation

---

## 8. NAMESPACE IMPLEMENTATION PATTERN

### Before (Current)
```python
@mcp.tool
def live_start_paper_trading(...):
    pass

@mcp.tool
def live_get_sessions(...):
    pass
```

### After (With Namespace)
```python
# jesse_mcp/tools/live_trading.py

def register_tools(mcp: FastMCP, jesse: Optional[Any]):
    @mcp.tool(name="trading:live:paper:start")
    def live_start_paper_trading(...):
        pass
    
    @mcp.tool(name="trading:live:sessions")
    def live_get_sessions(...):
        pass
```

This gives LLM agents a cleaner, hierarchical tool structure:
- Clients see: `trading:live:paper:start` instead of `live_start_paper_trading`
- Better discovery and organization in tool lists
- Easier to find related tools (prefix-based grouping)

---

## 9. IMPLEMENTATION NOTES

### Non-Breaking Changes
- Tool functionality unchanged
- Same parameters and return types
- Backwards compatible if using function names (not renamed tools)

### Breaking Changes (If Implementing Namespaces)
- Tool names change from `live_start_paper_trading` to `trading:live:paper:start`
- Clients need to update tool invocation names
- Can be optional - keep old names and add namespaced versions

### Testing Strategy
1. Extract one module at a time
2. Run tool-specific tests after each extraction
3. Run full test suite after all extractions
4. Verify tool registration and invocation

### Code Review Checklist
- [ ] All 47 tools accounted for
- [ ] No imports lost during extraction
- [ ] Error handling preserved
- [ ] Logging maintained
- [ ] Type hints correct
- [ ] Docstrings preserved/updated
- [ ] Tests passing

