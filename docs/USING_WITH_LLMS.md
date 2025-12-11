# Using Jesse-MCP with LLM Chat Interfaces

The jesse-mcp MCP server provides a transparent, language-agnostic interface to Jesse's trading capabilities. **Any LLM chat interface that supports MCP** can use these tools to help improve trading strategies.

---

## Architecture

```
┌────────────────────────────────────┐
│    LLM Chat Interface              │
│  (Claude, ChatGPT, etc.)           │
└────────────────┬────────────────────┘
                 │
                 │ MCP Protocol
                 │ (stdio/http)
                 ↓
┌────────────────────────────────────┐
│    jesse-mcp Server                │
│  (17 trading analysis tools)       │
└────────────────┬────────────────────┘
                 │
                 │ REST API
                 ↓
┌────────────────────────────────────┐
│    Jesse (server2:8000)            │
│  (Trading framework)               │
└────────────────────────────────────┘
```

**Key Point**: The MCP server is just a transparent layer. The LLM does the intelligent orchestration - deciding which tools to call, analyzing results, and having a conversation with the user about strategy improvements.

---

## Typical Conversational Workflows

### Example 1: Analyze Existing Strategy

**User**: "I have an EMA strategy that's not performing well. Can you analyze it?"

**LLM Orchestration**:
1. Calls `strategy_list()` → See available strategies
2. Calls `strategy_read("EMA_crossover")` → Get the code
3. Calls `backtest("EMA_crossover", ...)` → Run a test
4. Calls `analyze_results()` → Understand performance
5. Responds: "Your EMA strategy has a Sharpe of 1.2, which is okay but could be improved. Let me test some enhancements..."

---

### Example 2: A/B Test Strategy Variants

**User**: "Can you test if adding a volatility filter improves my EMA strategy?"

**LLM Orchestration**:
1. `strategy_read("EMA_crossover")` → Get current code
2. (Understands what changes are needed - volatility filter)
3. `backtest("EMA_crossover", ...)` → Baseline
4. `backtest("EMA_with_vol_filter", ...)` → New variant
5. `analyze_results()` on both → Compare
6. Responds: "The volatility filter improved your Sharpe from 1.2 to 1.45 (+20.8%). Here's what changed and why it helped..."

---

### Example 3: Iterative Optimization

**User**: "Can you try to improve my strategy to reach a Sharpe of 2.0?"

**LLM Orchestration**:
1. `backtest()` → Get baseline
2. `optimize(param_space={...}, metric="sharpe_ratio")` → Find best parameters
3. `backtest()` → Test optimized version
4. Evaluate: Did it reach goal? If not...
5. `optimize()` again with different param space
6. Responds: "Iteration 1: Sharpe 1.35. Iteration 2: Sharpe 1.68. Iteration 3: Sharpe 1.92 (96% toward goal). Want me to try one more round?"

---

### Example 4: Risk Assessment

**User**: "How risky is my strategy? Could it handle a market crash?"

**LLM Orchestration**:
1. `backtest()` → Get results
2. `monte_carlo()` → Simulate various outcomes
3. `var_calculation()` → Value at Risk
4. `stress_test()` → Test extreme scenarios
5. `risk_report()` → Comprehensive assessment
6. Responds: "Your strategy has a 95% confidence VaR of 5.2%. Under stress tests (20% drop, etc.), it remains profitable. Risk level: Moderate."

---

## Available Tools (17 Total)

### Phase 1: Backtesting & Strategy (6 tools)
- **backtest**: Run a single backtest
- **strategy_list**: List available strategies
- **strategy_read**: Read strategy source code
- **strategy_validate**: Validate strategy code
- **candles_import**: Download market data
- **analyze_results**: Extract insights from backtest

### Phase 3: Optimization (4 tools)
- **optimize**: Auto-optimize hyperparameters
- **walk_forward**: Detect overfitting
- **backtest_batch**: Run multiple tests concurrently
- (Note: optimize is the main one for iterative improvement)

### Phase 4: Risk Analysis (4 tools)
- **monte_carlo**: Bootstrap resampling simulation
- **var_calculation**: Value at Risk calculation
- **stress_test**: Black swan scenario testing
- **risk_report**: Comprehensive risk assessment

### Phase 5: Pairs Trading & Advanced Analysis (4 tools)
- **correlation_matrix**: Find correlated assets
- **pairs_backtest**: Test pairs trading strategies
- **factor_analysis**: Decompose returns into factors
- **regime_detector**: Identify market regimes

---

## Common Tool Sequences

### For Strategy Improvement
```
strategy_list()
  ↓
strategy_read(name)
  ↓
backtest(strategy, symbol, timeframe, dates)
  ↓
analyze_results(backtest_result)
  ↓
optimize(strategy, param_space, metric="sharpe_ratio")
  ↓
backtest(strategy, ...)  // with optimized params
  ↓
Repeat as needed for iterative improvement
```

### For Risk Assessment
```
backtest(strategy, ...)
  ↓
monte_carlo(backtest_result)
  ↓
var_calculation(backtest_result)
  ↓
stress_test(backtest_result)
  ↓
risk_report(backtest_result)
```

### For A/B Testing Variants
```
backtest(strategy_1, ...)
  ↓
backtest(strategy_2, ...)
  ↓
analyze_results(result_1)
  ↓
analyze_results(result_2)
  ↓
Compare metrics and recommend
```

---

## Tool Parameter Guide

### Backtest Parameters
- `strategy`: Strategy name (from `strategy_list()`)
- `symbol`: Trading pair (e.g., "BTC-USDT")
- `timeframe`: "1h", "4h", "1d", etc.
- `start_date`: "YYYY-MM-DD"
- `end_date`: "YYYY-MM-DD"

### Optimize Parameters
- `param_space`: Dict of parameters to optimize
  ```python
  {
    "ema_fast": [5, 30],      # range
    "ema_slow": [20, 100],
    "threshold": [0.01, 0.1]
  }
  ```
- `metric`: "total_return", "sharpe_ratio", "max_drawdown", etc.
- `n_trials`: Number of iterations (default: 100)

---

## Expected Tool Outputs

### Backtest Result
```json
{
  "total_return": 0.45,
  "sharpe_ratio": 1.5,
  "max_drawdown": 0.12,
  "win_rate": 0.62,
  "total_trades": 42,
  "profit_factor": 1.8,
  "metrics": { ... }
}
```

### Risk Report Result
```json
{
  "var_95": 0.042,
  "cvar_95": 0.065,
  "stress_test_results": { ... },
  "recommendation": "Acceptable risk level",
  "insights": [ ... ]
}
```

---

## Integration Points

### With Claude (or any MCP-compatible LLM)
The LLM can:
- Call tools sequentially or in parallel
- Interpret results conversationally
- Suggest next steps based on outcomes
- Handle errors gracefully
- Maintain context across multiple turns

### No Specialized Code Needed
- Just provide `JESSE_URL` and `JESSE_API_TOKEN` environment variables
- The MCP server handles all communication with Jesse
- The LLM handles all orchestration logic

---

## Example: Full Strategy Improvement Conversation

```
User: "My EMA strategy makes money but has high drawdowns. 
       Can you improve it while keeping Sharpe above 1.5?"

LLM:
1. strategy_list() → Find "EMA_crossover"
2. strategy_read("EMA_crossover") → Understand current logic
3. backtest("EMA_crossover", BTC-USDT, 1h, 2024-01-01, 2024-12-31) 
   → Result: Sharpe 1.3, Max DD 0.25
4. Propose: "Your main issue is large drawdowns (25%). 
   Let me optimize parameters to reduce them."
5. optimize(strategy="EMA_crossover", 
            param_space={...}, 
            metric="sharpe_ratio")
   → Suggests: fast=10, slow=30
6. backtest(...) with new params 
   → Result: Sharpe 1.6, Max DD 0.15 ✓
7. monte_carlo() → Validate stability
8. risk_report() → Comprehensive assessment
9. Response: "✅ Improved! New Sharpe: 1.6 (+23%), 
   Drawdown: 15% (-40%). The new parameters are: ..."
```

---

## Why This Matters

### Transparent Layer
- The MCP server is NOT an agent itself
- It's just a protocol bridge
- The LLM (Claude, etc.) does all the intelligent orchestration

### Language Independent  
- Any LLM that supports MCP can use these tools
- No need for custom integrations
- No need for separate AI/agent framework

### Scalable
- Multiple users can talk to their favorite LLM
- All using the same jesse-mcp server
- All benefiting from the same 17 tools

### User-Friendly
- Users talk naturally to their LLM
- "Can you improve my strategy?"
- "What's the risk of my backtest?"
- The LLM figures out which tools to call

---

## Next Steps

1. **Start the jesse-mcp server**: It runs as MCP protocol
2. **Connect your LLM**: Configure it to use jesse-mcp MCP server
3. **Have conversations**: Natural language about your strategies
4. **Let the LLM orchestrate**: It calls tools as needed
5. **Get intelligent responses**: Based on real trading analysis

The power isn't in any single tool - it's in the transparent layer that lets any LLM orchestrate them intelligently.
