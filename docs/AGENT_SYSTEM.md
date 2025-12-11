# Jesse MCP Specialized Agent System

## Overview

The Jesse MCP Agent System extends the base MCP server with three specialized agents, each with deep domain expertise in trading strategy analysis and optimization.

```
┌─────────────────────────────────────────────────────────────┐
│                   Your LLM (Claude, ChatGPT)               │
└────────────────────────────┬────────────────────────────────┘
                             │
                    MCP Protocol (stdio/HTTP)
                             │
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (jesse-mcp)                  │
│                     17 Trading Tools                        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│              Specialized Agent Layer (Optional)             │
│                                                             │
│  1. Strategy Optimization Agent                            │
│     - Analyze strategy weaknesses                          │
│     - Suggest improvements                                 │
│     - Recommend parameter tuning                           │
│                                                             │
│  2. Risk Management Agent                                  │
│     - Portfolio risk analysis                              │
│     - Stress testing                                       │
│     - Hedging recommendations                              │
│                                                             │
│  3. Backtesting & Analysis Agent                           │
│     - Comprehensive backtest design                        │
│     - Cross-timeframe comparison                           │
│     - Monte Carlo simulation                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                    Jesse REST API                          │
│              (running on configured host/port)             │
└─────────────────────────────────────────────────────────────┘
```

## Three Specialized Agents

### 1. Strategy Optimization Agent

**Specialization**: Identifying and implementing strategy improvements

**Key Capabilities**:
- Analyze backtest results for performance weaknesses
- Compare multiple strategies to identify best practices
- Recommend specific, testable improvements
- Track optimization iterations and results
- Suggest parameter tuning with expected impact

**System Prompt Highlights**:
- Deep knowledge of performance metrics (Sharpe, profit factor, win rate)
- Understanding of entry/exit optimization
- Position sizing and risk adjustment recommendations
- Market regime change detection
- Sustainable improvement methodology

**Example Usage**:

```
User: "Help me improve my mean_reversion strategy on BTCUSDT"

Agent Steps:
1. Run backtest on BTCUSDT to get baseline metrics
2. Identify underperforming timeframes or market conditions
3. Analyze winning vs losing trades
4. Suggest 3-5 specific improvements with expected impact
5. Recommend testing methodology (A/B testing, walk-forward)
6. Provide metrics to track after implementing changes
```

**Typical Workflows**:
- Analyze top/bottom performing pairs → Suggest pair-specific tuning
- Compare different parameter settings → Recommend optimal values
- Backtest across timeframes → Suggest timeframe-specific adjustments
- Historical analysis → Recommend regime-aware strategies

### 2. Risk Management Agent

**Specialization**: Identifying and mitigating trading risks

**Key Capabilities**:
- Calculate portfolio-level risk metrics
- Analyze correlation and concentration risks
- Stress test under various market scenarios
- Design hedging strategies
- Assess leverage and drawdown risks

**System Prompt Highlights**:
- Correlation and diversification analysis
- VaR and expected shortfall calculations
- Drawdown recovery pattern analysis
- Stress test scenario design
- Position sizing relative to risk tolerance
- Practical, implementable risk controls

**Example Usage**:

```
User: "Analyze the risk of trading BTCUSDT and ETHUSDT together"

Agent Steps:
1. Analyze correlation between BTC and ETH pairs
2. Calculate portfolio concentration metrics
3. Identify concentration hotspots
4. Perform stress tests (market crash, liquidity crisis)
5. Suggest position sizing to manage risk
6. Recommend hedging if needed
7. Provide risk tolerance parameters
```

**Typical Workflows**:
- Portfolio analysis → Identify concentrated positions → Rebalance
- Stress testing → Identify weak points → Design hedges
- Leverage assessment → Calculate safe levels → Recommend sizing
- Drawdown analysis → Understand recovery patterns → Suggest improvements

### 3. Backtesting & Analysis Agent

**Specialization**: Comprehensive backtest design and analysis

**Key Capabilities**:
- Design effective backtest scenarios
- Compare multiple configurations and timeframes
- Extract actionable performance metrics
- Validate statistical significance
- Identify regime-dependent performance

**System Prompt Highlights**:
- Comprehensive backtest scenario design
- Cross-timeframe and market condition comparison
- Monte Carlo simulation for robustness
- Walk-forward testing to avoid overfitting
- Statistical significance validation
- Regime-dependent performance analysis
- Performance attribution and insight extraction

**Example Usage**:

```
User: "Thoroughly backtest my momentum strategy"

Agent Steps:
1. Design backtest across multiple timeframes (1h, 4h, 1d)
2. Run tests in different market conditions
3. Extract performance metrics with context
4. Perform Monte Carlo simulation
5. Validate statistical significance
6. Analyze regime-dependent performance
7. Identify stress scenarios and edge cases
8. Provide comprehensive analysis report
```

**Typical Workflows**:
- Single strategy test → Comprehensive metrics → Detailed analysis
- Parameter optimization → Test ranges → Find optimal values
- Timeframe comparison → Performance curves → Best timeframe recommendation
- Statistical validation → Confidence intervals → Risk assessment
- Monte Carlo → Robustness analysis → Expected outcome distribution

## Integration Patterns

### Pattern 1: Sequential Analysis Workflow
```
1. Backtesting Agent: Run comprehensive backtest
2. Strategy Optimization Agent: Identify improvements
3. Risk Management Agent: Validate risk profile
```

### Pattern 2: Iterative Improvement Loop
```
1. Strategy Optimization Agent: Suggest improvement
2. Backtesting Agent: Test the improvement
3. Strategy Optimization Agent: Analyze results
4. → Repeat until satisfied
```

### Pattern 3: Risk-First Design
```
1. Risk Management Agent: Define acceptable risk parameters
2. Backtesting Agent: Find strategies meeting risk profile
3. Strategy Optimization Agent: Optimize within risk constraints
```

## Implementation Guide

### Using Agents Programmatically

Each agent can be instantiated and used independently:

```python
from jesse_mcp.agents import (
    StrategyOptimizationAgent,
    RiskManagementAgent,
    BacktestingAgent
)

# Create agents
strategy_agent = StrategyOptimizationAgent(
    mcp_host="localhost",
    mcp_port=5000
)

risk_agent = RiskManagementAgent(
    mcp_host="localhost",
    mcp_port=5000
)

backtest_agent = BacktestingAgent(
    mcp_host="localhost",
    mcp_port=5000
)

# Use agents in conversation
improvement_request = strategy_agent.suggest_improvements(
    strategy_name="mean_reversion",
    pair="BTCUSDT"
)

risk_request = risk_agent.analyze_portfolio_risk(
    pairs=["BTCUSDT", "ETHUSDT", "BNBUSDT"]
)

backtest_request = backtest_agent.backtest_strategy(
    strategy_name="momentum",
    pair="BTCUSDT",
    start_date="2023-01-01",
    end_date="2024-01-01"
)
```

### Conversation History

Agents maintain conversation history for multi-turn interactions:

```python
# First analysis
prompt1 = agent.suggest_improvements("my_strategy", "BTCUSDT")
# Agent response: "The strategy has X weakness, Y strength, Z recommendation"

# Follow-up question
prompt2 = agent.analyze_optimization_impact("Increase period from 20 to 30")
# Agent response: "Based on the previous analysis, this change would..."

# View full conversation
conversation = agent.get_history()
# [
#   {"role": "user", "content": prompt1},
#   {"role": "assistant", "content": "..."},
#   {"role": "user", "content": prompt2},
#   {"role": "assistant", "content": "..."}
# ]
```

## Best Practices

### For Strategy Optimization
1. **Get baseline metrics first** - Run comprehensive backtest before optimization
2. **Focus on sustainable improvements** - Avoid overfitting to historical data
3. **Test changes incrementally** - Change one thing at a time
4. **Use walk-forward testing** - Validate improvements on out-of-sample data
5. **Track optimization history** - Keep record of what was tried and results

### For Risk Management
1. **Stress test thoroughly** - Test beyond historical scenarios
2. **Monitor concentration** - Keep position sizes manageable
3. **Plan for leverage carefully** - Understand liquidation risks
4. **Hedge systematically** - Use hedges for concentrated or correlated positions
5. **Review drawdown patterns** - Understand when and why losses occur

### For Backtesting
1. **Test across conditions** - Don't just test one timeframe or pair
2. **Validate significance** - Ensure results aren't due to luck
3. **Avoid overfitting** - Use walk-forward testing, not just in-sample optimization
4. **Extract insights** - Understand WHY a strategy works, not just THAT it works
5. **Plan live testing** - Have a strategy for small-scale live validation

## System Prompts in Detail

Each agent's system prompt encodes deep domain expertise. These prompts guide the agent's analysis, recommendations, and interaction style. The prompts emphasize:

- **Specificity** - Give concrete, testable recommendations
- **Context** - Explain metrics and why they matter
- **Practicality** - Focus on implementable suggestions
- **Rigor** - Validate conclusions with appropriate analysis
- **Transparency** - Explain reasoning and assumptions

## Future Enhancements

Potential extensions to the agent system:

1. **Custom Agent Creation** - Build agents for specialized strategies
2. **Agent Coordination** - Multi-agent workflows that delegate between agents
3. **Learning from Experience** - Track which recommendations work best
4. **Integration with Live Trading** - Monitor live performance vs backtest
5. **Anomaly Detection** - Alert on unexpected market behavior

## See Also

- [USING_WITH_LLMS.md](USING_WITH_LLMS.md) - Integration with LLM interfaces
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current project state
- [../../AGENTS.md](../../AGENTS.md) - Development guidelines
