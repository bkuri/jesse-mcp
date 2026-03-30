# Jesse-MCP Integration Issues via MCProxy

Empirical observations from integrating `jesse-mcp` with `mcproxy` (MCP gateway).

> **Last updated**: 2026-03-29
> **Status**: All issues resolved

## Environment

| Component | Host | Address |
|-----------|------|---------|
| mcproxy | server2 (192.168.50.71) | port 12010 |
| jesse (REST API) | server2 | port 9100 |
| jesse-mcp | server2 | via mcproxy stdio |
| callers | workstation / agents | over LAN |

## Summary

All issues identified below have been resolved in the codebase. Tool names now match function names (no more decorator name confusion), and `candles_import` sends correct API payloads.

## Issue 1: Wrong Tool Names (FIXED)

### Symptom
```
RuntimeError: No response from server 'jesse'
```

### Root Cause
Callers used `backtesting_run` (the `@mcp.tool(name=...)` decorator value) but FastMCP registers tools by their **function name**, not the decorator name.

### Fix Applied
Removed all `name=` overrides from `@mcp.tool` decorators. Tools are now registered by their function names.

### Tool Name Mapping (historical)

| Old Decorator Name | Function Name (current) |
|-------------------|------------------------|
| `backtesting_status` | `jesse_status` |
| `backtesting_exchanges` | `get_exchanges` |
| `backtesting_run` | `backtest` |
| `backtesting_list_strategies` | `strategy_list` |
| `backtesting_read_strategy` | `strategy_read` |
| `backtesting_validate` | `strategy_validate` |
| `backtesting_import_candles` | `candles_import` |
| `optimization_run` | `optimize` |
| `optimization_walk_forward` | `walk_forward` |
| `optimization_batch` | `backtest_batch` |
| `optimization_analyze` | `analyze_results` |
| `risk_monte_carlo` | `monte_carlo` |
| `risk_var` | `var_calculation` |
| `risk_stress_test` | `stress_test` |
| `benchmark_run` | `backtest_benchmark` |
| `trading_live_check` | `live_check_plugin` |
| `trading_live_paper` | `live_start_paper_trading` |
| `trading_live_real` | `live_start_live_trading` |
| `trading_live_cancel` | `live_cancel_session` |
| `trading_live_sessions` | `live_get_sessions` |
| `trading_live_status` | `live_get_status` |
| `trading_live_orders` | `live_get_orders` |
| `trading_live_equity` | `live_get_equity_curve` |
| `trading_live_logs` | `live_get_logs` |
| `trading_paper_start` | `paper_start` |
| `trading_paper_stop` | `paper_stop` |
| `trading_paper_status` | `paper_status` |
| `trading_paper_trades` | `paper_get_trades` |
| `trading_paper_equity_history` | `paper_get_equity` |
| `trading_paper_metrics` | `paper_get_metrics` |
| `trading_paper_list` | `paper_list_sessions` |
| `trading_paper_update` | `paper_update_session` |
| `pairs_correlation` | `correlation_matrix` |
| `pairs_factors` | `factor_analysis` |
| `pairs_regimes` | `regime_detector` |

## Issue 2: Wrong Parameter Names (FIXED)

### Symptom
Pydantic validation errors returned as strings.

### Root Cause
The tool accepts `end_date`, not `finish_date`. Some parameters like `fast_mode` are internal and not exposed in the MCP tool schema.

### Correct Parameters
```python
api.call_tool("jesse", "backtest", {
    "strategy": "SMACrossover",
    "symbol": "BTC-USDT",
    "timeframe": "1h",
    "start_date": "2026-03-20",
    "end_date": "2026-03-25",
    "exchange": "Binance Spot",
    "exchange_type": "spot",
})
```

## Issue 3: MCProxy Sandbox Caching (MCProxy-side)

### Symptom
Sandbox returns previous result when same code is sent again (0.0s response with stale data).

### Root Cause
MCProxy's sandbox pool reuses subprocess processes. Identical code patterns may return cached results from a previous execution.

### Workaround
Add `import time; time.sleep(2)` at the start of code to force a fresh sandbox process:
```python
import time; time.sleep(2)
result = api.call_tool("jesse", "backtest", {...})
```

### Note
This is a mcproxy issue, not a jesse-mcp issue. Tracked in mcproxy repo.

## Issue 4: Backtest Result Caching (Jesse-MCP-side)

### Symptom
Second backtest call with different parameters returns first call's results.

### Root Cause
Jesse-mcp has built-in backtest result caching (`cached_backtest()` in `jesse_rest_client.py`).

### Note
This is intentional behavior with a 1-hour TTL. Not a bug.

## Issue 5: candles_import 422 Error (FIXED)

### Symptom
`candles_import()` returned HTTP 422 from Jesse API.

### Root Cause
Three bugs in `JesseRESTClient.import_candles()`:
1. **Missing `id` field** — Jesse API requires a UUID for the async import job
2. **Missing `timeframe` field** — API needs candle granularity (e.g. `"1h"`)
3. **Wrong field name** — Client sent `end_date` but API expects `finish_date`
4. **No polling** — Client returned the POST response instead of polling for completion

### Fix Applied
- Added `timeframe` parameter to the MCP tool and client method
- Added UUID `id` to the API payload
- Changed `end_date` to `finish_date` in the API payload
- Added polling loop (up to 120s) matching the pattern in `candles.py`

## Verified Working (2026-03-29)

All tools tested successfully through mcproxy:

| Tool | Status | Notes |
|------|--------|-------|
| `jesse_status()` | Works | Returns health check |
| `strategy_list()` | Works | Lists 149 strategies |
| `get_exchanges()` | Works | Returns 13 exchanges |
| `backtest()` | Works | 5-day: ~2s, 6-month: varies |
| `cache_stats()` | Works | Returns cache info |
| `analyze_results()` | Works | With sanitized dict input |
| `monte_carlo()` | Works | With sanitized dict input |
| `candles_import()` | Works | Now sends correct payload |

### Example Working Call
```python
import time
time.sleep(2)  # Force fresh sandbox
result = api.call_tool("jesse", "backtest", {
    "strategy": "SMACrossover",
    "symbol": "BTC-USDT",
    "timeframe": "1h",
    "start_date": "2025-09-01",
    "end_date": "2026-03-25",
    "exchange": "Binance Spot",
    "exchange_type": "spot",
})
```

## Recommendations for Callers

1. **Use function names** when calling jesse-mcp tools (no namespace prefixes)
2. **Use `end_date`, not `finish_date`** for the backtest tool
3. **Don't pass `fast_mode`** - it's an internal parameter not exposed via MCP
4. **Add `import time; time.sleep(2)`** to force fresh sandbox processes (mcproxy workaround)
5. **Sanitize dicts before passing to analysis tools** - only primitive types (str, int, float, bool, list, dict)
