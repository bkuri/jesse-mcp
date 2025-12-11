# Agent Usage Examples and Patterns

This document provides real-world examples of how to use the three specialized agents to improve trading strategies.

## Quick Start

### Running an Agent in Python

```python
from jesse_mcp.agents import (
    StrategyOptimizationAgent,
    RiskManagementAgent,
    BacktestingAgent
)

# Create an agent
agent = StrategyOptimizationAgent(mcp_host="localhost", mcp_port=5000)

# Use the agent
request = agent.suggest_improvements(
    strategy_name="mean_reversion",
    pair="BTCUSDT"
)

# Access conversation history
history = agent.get_history()
```

## Pattern 1: Iterative Strategy Improvement

**Goal**: Improve a mean reversion strategy that's showing decent returns but inconsistent performance.

### Step 1: Backtest and Analyze
```python
backtest_agent = BacktestingAgent()

# Run comprehensive backtest
backtest_request = backtest_agent.backtest_strategy(
    strategy_name="mean_reversion",
    pair="BTCUSDT",
    start_date="2023-01-01",
    end_date="2024-01-01"
)
```

**Expected Response**:
```
Performance Summary:
- Total Return: 45%
- Sharpe Ratio: 1.2
- Win Rate: 52%
- Max Drawdown: 18%
- Profit Factor: 1.8

Key Findings:
- Strategy performs well in ranging markets (55% win rate)
- Struggles in trending markets (48% win rate)
- Best performance on 4h timeframe vs 1h
- Concentrated losses during high-volatility events

Recommendations:
1. Add trend filter to avoid entries during strong trends
2. Increase position size in ranging markets
3. Test strategy on 4h timeframe instead of 1h
```

### Step 2: Identify Improvements
```python
optimization_agent = StrategyOptimizationAgent()

# Ask for specific improvements
request = optimization_agent.suggest_improvements(
    strategy_name="mean_reversion",
    pair="BTCUSDT"
)
```

**Expected Response**:
```
Based on the backtest analysis, here are 3 specific improvements:

Improvement #1: Add ADX Filter
- Current: Enters on RSI reversal regardless of trend
- Proposed: Only enter when ADX < 25 (indicating range market)
- Expected Impact: Reduce whipsaws by 40%, improve Sharpe to 1.5
- Test Duration: 3 months

Improvement #2: Dynamic Position Sizing
- Current: Fixed position size of 2% risk
- Proposed: Use 3% risk in ranging markets, 1% in trending markets
- Expected Impact: Increase returns 15% while maintaining risk
- Implementation: Use Chop Index to detect market regime

Improvement #3: Multi-Timeframe Confirmation
- Current: Only looks at 1h candles
- Proposed: Confirm trades with 4h trend (only short when 4h in downtrend)
- Expected Impact: Improve win rate to 56%, reduce false signals
- Setup: Add get_candles() for 4h timeframe

Testing Plan:
1. Implement Improvement #1 (ADX Filter)
2. Backtest: Should see 40% fewer trades, 15% higher win rate
3. If successful, add Improvement #2
4. Final test with all 3 improvements combined
```

### Step 3: Implement and Validate
```python
# After implementing improvements, backtest again
backtest_request = backtest_agent.backtest_strategy(
    strategy_name="mean_reversion_v2",
    pair="BTCUSDT",
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# Compare results
optimization_request = optimization_agent.compare_strategies(
    strategy1="mean_reversion",
    strategy2="mean_reversion_v2"
)
```

**Expected Comparison**:
```
Strategy Comparison: mean_reversion vs mean_reversion_v2

Performance Metrics:
                    v1          v2        Change
Return:             45%         52%       +7% (15% improvement)
Sharpe:             1.2         1.5       +25%
Win Rate:           52%         55%       +3%
Max Drawdown:       18%         14%       -4% (better)
Profit Factor:      1.8         2.1       +17%
Trades:             145         98        -33% (fewer whipsaws)

Trade Distribution:
- Range Markets:    v1: 55% win | v2: 62% win (ADX filter working)
- Trend Markets:    v1: 48% win | v2: 58% win (trend filter helping)

Validation:
✓ All improvements showing expected impact
✓ Drawdown reduced as expected
✓ Sharpe ratio above 1.5 target
✓ Profitable in both market conditions

Recommendation: Deploy v2 with confidence. Monitor for 1 month in paper trading.
```

## Pattern 2: Risk Assessment Before Live Trading

**Goal**: Validate that a profitable strategy has acceptable risk before deploying real capital.

### Step 1: Portfolio Risk Analysis
```python
risk_agent = RiskManagementAgent()

# Analyze risk if trading multiple pairs
risk_request = risk_agent.analyze_portfolio_risk(
    pairs=["BTCUSDT", "ETHUSDT", "BNBUSDT"]
)
```

**Expected Response**:
```
Portfolio Risk Analysis:

Pair Correlations:
- BTC-ETH:   0.82 (high positive correlation)
- BTC-BNB:   0.75 (high positive correlation)
- ETH-BNB:   0.70 (moderate positive correlation)

Concentration Risk:
Current allocation (equal weight):
- BTC: 33.3% of portfolio
- ETH: 33.3% of portfolio
- BNB: 33.3% of portfolio

Risk Assessment: MODERATE-HIGH
- High correlation means diversification benefit is limited
- In a market-wide crash, all positions could lose together
- Single pair drawdown would impact 33% of account

Recommendations:
1. Reduce to 2 pairs maximum (BTC and non-BTC pair)
2. Or reduce position sizes: BTC 50%, ETH 30%, BNB 20%
3. Or use uncorrelated pairs (add commodity, forex alternative)

Suggested Allocation:
- BTCUSDT (high conviction): 50%
- ETHUSDT (medium conviction): 30%
- Alternative pair (low correlation): 20%

Expected portfolio benefit:
- Correlation with BTC reduced to 0.40
- Diversification benefit: +15% Sharpe ratio
- Max drawdown reduced from 22% to 18%
```

### Step 2: Stress Testing
```python
# Test extreme scenarios
stress_request = risk_agent.stress_test_portfolio(
    pairs=["BTCUSDT", "ETHUSDT"],
    scenario="market crash"
)
```

**Expected Response**:
```
Stress Test: -30% Market Crash Scenario

Starting Portfolio: $100,000

Scenario 1: Synchronized Crash
- Both BTC and ETH fall 30%
- Portfolio value: $70,000 (30% loss)
- Max drawdown: 30%
- Recovery time (assuming normal returns): ~45 days
- Margin impact: Available margin drops 60%

Scenario 2: Correlation Breakdown (Crash)
- BTC falls 40%, ETH falls only 15%
- Portfolio value: $77,500 (22.5% loss)
- Divergence reduces portfolio loss
- Still manageable without forced liquidation

Scenario 3: Flash Crash (Temporary)
- Both fall 20% intraday, recover to -5% by close
- Potential stop-loss triggers: YES
- Recommended action: Widen stops to 25% on all positions

Liquidation Risk Assessment: SAFE
✓ Even 40% drop doesn't trigger margin liquidation (need 50%+)
✓ Available margin stays positive in all scenarios
✓ Can add more positions during crashes (accumulate dips)

Risk Controls Recommended:
1. Set hard stop at 25% portfolio loss (close all positions)
2. Reduce position size if margin usage exceeds 30%
3. Use alerts at 15% drawdown to review and potentially hedge
4. Keep 20% cash reserve for opportunities
```

### Step 3: Leverage Assessment
```python
# If using leverage, assess the risks
leverage_request = risk_agent.assess_leverage_risk(
    strategy_name="mean_reversion",
    leverage=2.0
)
```

**Expected Response**:
```
Leverage Risk Assessment: 2x Leverage

Current Setup:
- Account: $100,000
- Effective capital: $200,000 (2x)
- Margin requirement: $100,000 (50% of effective)
- Available margin: $100,000

Liquidation Risk:
- Liquidation happens at: -50% (account value drops to $50,000)
- In 2x leverage, this means: -100% on leveraged portion
- Typical scenario: -20% drop = forced close at -40% loss

Scenario Analysis:
1. Normal day (-5% move): Portfolio at 95% → Available margin: $90,000 ✓
2. Bad day (-15% move): Portfolio at 85% → Available margin: $70,000 ⚠️
3. Worst case (-25% move): Portfolio at 75% → Liquidation risk 🔴

Safe Leverage Recommendation: 1.5x maximum
- Liquidation threshold moves to -67% (safer)
- Allows for 25% drawdown without concerns
- Keeps available margin above $30,000 in worst case
- Matches risk tolerance of 2% per trade

If insisting on 2x:
- Must implement strict 15% portfolio loss stop
- Reduce per-trade risk to 1% (from 2%)
- Keep 30% cash reserve (not leveraged)
- Expected return reduction: ~20%
```

## Pattern 3: Pair Selection Optimization

**Goal**: Find the best pairs to trade a particular strategy.

### Step 1: Analyze Pair Performance
```python
optimization_agent = StrategyOptimizationAgent()

# Test strategy across multiple pairs
pair_request = optimization_agent.optimize_pair_selection(
    strategy_name="momentum"
)
```

**Expected Response**:
```
Pair Performance Analysis for Momentum Strategy:

Performance Ranking (by Sharpe Ratio):
1. ETHUSDT:   Sharpe 1.8, Return 68%, Win Rate 58%
2. BTCUSDT:   Sharpe 1.5, Return 52%, Win Rate 55%
3. BNBUSDT:   Sharpe 1.2, Return 38%, Win Rate 51%
4. ADAUSDT:   Sharpe 0.8, Return 22%, Win Rate 49%
5. XRPUSDT:   Sharpe 0.4, Return 8%,  Win Rate 47%

Market Characteristics (Top Performers):
ETH and BTC both show:
- Strong trending periods (momentum strategy strength)
- Lower slippage on entries/exits
- Higher volume = better execution
- Volatility 15-25% (ideal for momentum)

Pairs to Avoid:
- XRPUSDT: Too choppy, low volatility
- ADAUSDT: Weak trends, many false breakouts

Volatility Considerations:
- High volatility (>25%): Good for large moves, bad for tight stops
- Low volatility (<10%): Tight stops needed, more whipsaws
- Optimal range: 15-20% (matches strategy ATR assumptions)

Recommended Trading Pairs:
1. Primary:  ETHUSDT (highest Sharpe, best trends)
2. Secondary: BTCUSDT (stable, large moves)
3. Diversifier: BNBUSDT (alt-coin, different regime)

Avoid:
- Pairs with volatility outside 12-25% range
- Pairs with <$1M daily volume
- Pairs with spreads >0.02% (execution cost)

Expected Portfolio Improvement:
- Focusing on top 2 pairs: +25% aggregate return
- Removing bottom 2 pairs: -50% drag eliminated
- Recommended allocation: ETH 50%, BTC 50%
- Expected Sharpe: 1.7 (vs 1.1 with all 5)
```

## Pattern 4: Full Workflow - From Idea to Live Trading

**Goal**: Take a new trading idea from concept through validation to live deployment.

### Phase 1: Backtest Design
```python
backtest_agent = BacktestingAgent()

# Design comprehensive test
request = backtest_agent.backtest_strategy(
    strategy_name="ichimoku_breakout",
    pair="BTCUSDT",
    start_date="2022-01-01",
    end_date="2024-01-01"
)
```

### Phase 2: Timeframe Analysis
```python
# Test across multiple timeframes
request = backtest_agent.compare_timeframes(
    strategy_name="ichimoku_breakout",
    pair="BTCUSDT"
)
```

### Phase 3: Parameter Optimization
```python
# Find optimal settings
request = backtest_agent.optimize_parameters(
    strategy_name="ichimoku_breakout",
    pair="BTCUSDT",
    param_name="cloud_lookback",
    param_range="15-50"
)
```

### Phase 4: Statistical Validation
```python
# Ensure results aren't just luck
request = backtest_agent.validate_statistical_significance(
    strategy_name="ichimoku_breakout",
    pair="BTCUSDT"
)
```

**Expected Response**:
```
Statistical Significance Validation:

Sample Size: 127 trades over 2 years
Minimum Required: 30 trades (✓ Sufficient)

Win Rate Analysis:
- Observed: 56%
- Random expectation: 50%
- Difference: 6% (statistically significant at 95%)

P-value: 0.042 (< 0.05, significant)
Confidence: The edge is real, not luck

Profit Factor Analysis:
- Observed: 2.1
- Random expectation: 1.0
- Z-score: 3.2 (highly significant)

Robustness Check:
- Walk-forward test: 53% win rate (vs 56% in-sample)
- Degradation: 3% (acceptable)
- Strategy is NOT severely overfitted

Risk Assessment:
- Max consecutive losses: 4
- Probability of 5+ in a row: <5%
- Drawdown recovery time: 8-12 days (acceptable)

Recommendation: SAFE TO TRADE LIVE
- Statistical edge is real and significant
- Not overfit to historical data
- Risk profile is acceptable
- Recommended: Start with 1x position size, scale to 2x after 1 month
```

### Phase 5: Risk Management Setup
```python
risk_agent = RiskManagementAgent()

# Verify risk profile
request = risk_agent.analyze_portfolio_risk(
    pairs=["BTCUSDT"]
)

# Stress test
request = risk_agent.stress_test_portfolio(
    pairs=["BTCUSDT"],
    scenario="flash crash"
)
```

### Phase 6: Live Deployment
```python
# Final checklist completed:
# ✓ Backtest shows positive edge
# ✓ Timeframe optimization done
# ✓ Parameter optimization complete
# ✓ Statistical significance confirmed
# ✓ Risk profile acceptable
# ✓ Stress tests passed
# Ready for paper trading → Live trading
```

## Best Practices by Agent

### Strategy Optimization Agent
- Always start with a baseline backtest
- Change ONE thing at a time
- Test improvements on OUT-OF-SAMPLE data
- Track what you've tried (avoid repeating)
- Focus on sustainable changes, not curve-fitting

### Risk Management Agent
- Always stress test before going live
- Understand your leverage limits
- Know your liquidation price
- Monitor correlation changes over time
- Have a stop-loss plan for portfolio loss

### Backtesting Agent
- Test across multiple timeframes
- Include different market conditions
- Validate statistical significance
- Use walk-forward testing
- Extract WHY it works, not just THAT it works

## Common Pitfalls to Avoid

1. **Over-optimization**: Testing too many parameters, curve-fitting to history
2. **Insufficient data**: Trading with <30 trades of backtest history
3. **Ignoring correlation**: Trading pairs that move together
4. **Leverage without testing**: Using 2x+ leverage without stress tests
5. **One-pair focus**: Concentrating all capital on a single trading pair
6. **Ignoring regime changes**: Not testing in different market conditions

## Integration with LLMs

All agents work seamlessly with LLM interfaces:

```python
# Example: Using Claude to orchestrate agents
from anthropic import Anthropic

client = Anthropic()

# Multi-turn conversation with agents
conversation = [
    {
        "role": "user",
        "content": """Analyze my momentum strategy on BTCUSDT. 
        I want to improve it and ensure it's safe to trade with 2x leverage."""
    }
]

# Agent system prompt guides the LLM to use all three agents
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=8000,
    system="""You have access to three specialized trading agents:
    1. StrategyOptimizationAgent - for strategy improvements
    2. RiskManagementAgent - for risk analysis
    3. BacktestingAgent - for comprehensive backtesting
    
    Use the appropriate agent(s) to help the user.""",
    messages=conversation
)
```

## See Also

- [AGENT_SYSTEM.md](AGENT_SYSTEM.md) - Complete agent architecture
- [USING_WITH_LLMS.md](USING_WITH_LLMS.md) - LLM integration guide
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Deployment guide
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current capabilities
