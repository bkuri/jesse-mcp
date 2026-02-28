# Jesse MCP Server - Quick Reference Guide

## Tool Extraction Line Numbers

### Backtesting Tools (6 tools, ~180 lines)
| Tool | Lines | Status |
|------|-------|--------|
| jesse_status() | 126-147 | Health check |
| get_exchanges() | 150-188 | Exchange info |
| backtest() | 190-294 | Core execution |
| strategy_list() | 296-311 | List strategies |
| strategy_read() | 313-323 | Read code |
| strategy_validate() | 325-335 | Validate code |

**Extract to**: `jesse_mcp/tools/backtesting.py`
**Supporting function**: _initialize_dependencies() - keep in server.py

---

### Strategy Creation Tools (9 tools, ~320 lines)
| Tool | Lines | Status |
|------|-------|--------|
| _strategy_create_impl() | 340-453 | Internal helper |
| strategy_create() | 455-560 | Create strategy |
| strategy_create_status() | 562-607 | Poll async job |
| strategy_create_cancel() | 609-638 | Cancel job |
| strategy_refine() | 640-725 | Refine strategy |
| strategy_delete() | 727-770 | Delete strategy |
| jobs_list() | 772-808 | List jobs |
| strategy_metadata() | 810-858 | Get metadata |
| candles_import() | 860-881 | Import candles |
| rate_limit_status() | 883-904 | Rate limiter status |

**Extract to**: `jesse_mcp/tools/strategy_creation.py`
**Note**: These are interspersed in current server.py

---

### Optimization Tools (4 tools, ~130 lines)
| Tool | Lines | Status |
|------|-------|--------|
| optimize() | 909-958 | Async optimization |
| walk_forward() | 960-993 | Walk-forward analysis |
| backtest_batch() | 995-1022 | Batch backtest |
| analyze_results() | 1024-1061 | Analyze results |

**Extract to**: `jesse_mcp/tools/optimization.py`

---

### Risk Analysis Tools (4 tools, ~140 lines)
| Tool | Lines | Status |
|------|-------|--------|
| monte_carlo() | 1066-1093 | Monte Carlo sim |
| var_calculation() | 1095-1118 | VaR calculation |
| stress_test() | 1120-1139 | Stress testing |
| risk_report() | 1141-1166 | Risk report |

**Extract to**: `jesse_mcp/tools/risk_analysis.py`

---

### Pairs Trading Tools (4 tools, ~110 lines)
| Tool | Lines | Status |
|------|-------|--------|
| correlation_matrix() | 1171-1196 | Correlation analysis |
| pairs_backtest() | 1198-1229 | Pairs backtest |
| factor_analysis() | 1231-1256 | Factor analysis |
| regime_detector() | 1258-1283 | Regime detection |

**Extract to**: `jesse_mcp/tools/pairs_trading.py`

---

### Cache & Utilities Tools (3 tools, ~150 lines)
| Tool | Lines | Status |
|------|-------|--------|
| cache_stats() | 1288-1303 | Cache statistics |
| cache_clear() | 1305-1328 | Clear caches |
| backtest_benchmark() | 1330-1434 | Performance benchmark |

**Extract to**: `jesse_mcp/tools/cache_utilities.py`

---

### Live Trading Tools (9 tools, ~390 lines)
| Tool | Lines | Status |
|------|-------|--------|
| live_check_plugin() | 1439-1455 | Check plugin |
| live_start_paper_trading() | 1457-1548 | Start paper trading |
| live_start_live_trading() | 1550-1685 | Start live trading |
| live_cancel_session() | 1687-1707 | Cancel session |
| live_get_sessions() | 1709-1729 | Get sessions list |
| live_get_status() | 1731-1750 | Get session status |
| live_get_orders() | 1752-1771 | Get orders |
| live_get_equity_curve() | 1773-1798 | Get equity curve |
| live_get_logs() | 1800-1820 | Get logs |

**Extract to**: `jesse_mcp/tools/live_trading.py`

---

### Paper Trading Tools (8 tools, ~210 lines)
| Tool | Lines | Status |
|------|-------|--------|
| paper_start() | 1825-1888 | Start paper trading |
| paper_stop() | 1890-1917 | Stop paper trading |
| paper_status() | 1919-1938 | Get paper status |
| paper_get_trades() | 1940-1971 | Get trades |
| paper_get_equity() | 1973-2014 | Get equity curve |
| paper_get_metrics() | 2016-2043 | Get metrics |
| paper_list_sessions() | 2045-2061 | List sessions |
| paper_update_session() | 2063-2087 | Update session |

**Extract to**: `jesse_mcp/tools/paper_trading.py`

---

## Critical Sections to Preserve in server.py

| Section | Lines | Keep Reason |
|---------|-------|------------|
| Lazy initialization | 35-88 | Shared by all tools |
| FastMCP init | 91-120 | Server core |
| Health endpoint | 96-120 | HTTP monitoring |
| Main entry point | 2089-2133 | Server startup |
| Tool registration dispatcher | NEW | Coordinates all modules |

---

## Global Dependencies to Pass

```
Global Variables:
├── jesse (Optional[Any])
├── optimizer (Optional[Any])
├── risk_analyzer (Optional[Any])
├── pairs_analyzer (Optional[Any])
└── _initialized (bool)

Tool-to-Dependency Mapping:
├── backtesting.py      → jesse, mcp
├── optimization.py     → optimizer, mcp
├── risk_analysis.py    → risk_analyzer, mcp
├── pairs_trading.py    → pairs_analyzer, mcp
├── strategy_creation.py → jesse, mcp
├── live_trading.py     → jesse, mcp
├── paper_trading.py    → mcp
└── cache_utilities.py  → mcp
```

---

## Namespace Implementation Examples

### Current (Flat)
```python
@mcp.tool
def live_start_paper_trading(...): pass
```

### Proposed (Hierarchical)
```python
@mcp.tool(name="trading:live:paper:start")
def live_start_paper_trading(...): pass
```

### Tool Naming Convention
- `phase:category:action` format
- Colon-separated for hierarchical discovery
- Optional implementation (non-breaking)

---

## Migration Order (Recommended)

1. **Phase 1**: Extract low-dependency tools
   - cache_utilities.py (only uses mcp)
   - pairs_trading.py (only uses pairs_analyzer)
   - risk_analysis.py (only uses risk_analyzer)

2. **Phase 2**: Extract mid-dependency tools
   - optimization.py (uses optimizer, rest_client)
   - backtesting.py (uses jesse, rest_client, mock)

3. **Phase 3**: Extract high-dependency tools
   - strategy_creation.py (complex initialization)
   - live_trading.py (certification, config)
   - paper_trading.py (session management)

4. **Phase 4**: Refactor server.py and add namespaces

---

## Testing Checklist per Module

- [ ] All tools callable
- [ ] Error handling preserved
- [ ] Mock fallback working
- [ ] Logging operational
- [ ] Type hints correct
- [ ] Docstrings intact
- [ ] Integration with global state
- [ ] Async/sync methods work

---

## Files to Create

```
jesse_mcp/tools/
├── __init__.py (shared utilities, register_tools() dispatcher)
├── backtesting.py
├── optimization.py
├── risk_analysis.py
├── pairs_trading.py
├── strategy_creation.py
├── live_trading.py
├── paper_trading.py
└── cache_utilities.py
```

---

## Key Metrics

| Metric | Current | After |
|--------|---------|-------|
| server.py lines | 2,134 | 400 |
| Avg module lines | - | 150-180 |
| Tool groups | 1 | 8 |
| Testability | Low | High |
| Navigation | Difficult | Easy |

