# Phase 5: Pairs Trading & Advanced Analysis Tools

## Overview
Phase 5 implements 4 advanced pairs trading and correlation analysis tools. These tools enable sophisticated multi-asset strategies, factor analysis, and market regime detection.

**Target**: 16/16 tools complete (100% project completion)
**Current**: 13/16 tools (Phase 1-4 complete)

## Tools Specification

### 1. correlation_matrix()
**Purpose**: Analyze cross-asset correlations and co-movements to identify trading pairs

**Input Parameters**:
- `backtest_results`: List of backtest results from different symbols/strategies
- `lookback_period`: Days to analyze (default: 60)
- `correlation_threshold`: Minimum correlation for pair suggestions (default: 0.7)
- `include_rolling`: Include rolling correlations (default: true)
- `rolling_window`: Window size for rolling correlation (default: 20)
- `include_heatmap`: Generate correlation heatmap visualization (default: false)

**Output Format**:
```json
{
  "summary": {
    "symbols": ["BTC-USDT", "ETH-USDT", "SOL-USDT"],
    "correlation_matrix": [[1.0, 0.82, 0.65], ...],
    "average_correlation": 0.72,
    "correlation_strength": "Strong"
  },
  "pairs": [
    {
      "pair": "BTC-USDT / ETH-USDT",
      "correlation": 0.82,
      "cointegration_score": 0.85,
      "spread_mean": 0.0012,
      "spread_std": 0.0045,
      "trading_signal": "BUY_PAIR"
    }
  ],
  "rolling_correlations": [{"date": "2024-01-01", "correlations": {...}}],
  "heatmap": "base64_encoded_image",
  "analysis_stats": {
    "strongest_pair": "BTC-USDT / ETH-USDT (0.82)",
    "weakest_pair": "BTC-USDT / SOL-USDT (0.65)",
    "cointegrated_pairs": 3
  },
  "execution_time": 0.45,
  "use_mock": true
}
```

**Algorithm Details**:
- Pearson correlation for each pair
- Cointegration test (Johansen test) for pairs
- Rolling correlation analysis to detect regime changes
- Statistical summary generation
- Mock data: Generate synthetic correlated time series

---

### 2. pairs_backtest()
**Purpose**: Backtest pairs trading strategies (statistical arbitrage, mean reversion)

**Input Parameters**:
- `pair`: Dict with 'symbol1', 'symbol2' (e.g., {'symbol1': 'BTC-USDT', 'symbol2': 'ETH-USDT'})
- `strategy`: Pairs trading strategy ('mean_reversion', 'momentum_divergence', 'cointegration')
- `backtest_result_1`: Backtest result for first symbol
- `backtest_result_2`: Backtest result for second symbol
- `lookback_period`: Historical period for calculations (default: 60)
- `entry_threshold`: Entry signal threshold (default: 2.0 for std dev)
- `exit_threshold`: Exit signal threshold (default: 0.5 for std dev)
- `position_size`: Risk per trade (default: 0.02)
- `max_holding_days`: Maximum days to hold position (default: 20)

**Output Format**:
```json
{
  "pair": "BTC-USDT / ETH-USDT",
  "strategy": "mean_reversion",
  "total_return": 0.18,
  "sharpe_ratio": 1.45,
  "max_drawdown": 0.08,
  "win_rate": 0.58,
  "total_trades": 32,
  "avg_trade_return": 0.0056,
  "trades": [
    {
      "entry_date": "2024-01-05",
      "exit_date": "2024-01-12",
      "spread_entry": 2.3,
      "spread_exit": 0.8,
      "return": 0.0145,
      "holding_days": 7
    }
  ],
  "spread_analysis": {
    "mean": 0.0,
    "std": 1.5,
    "current": 1.2,
    "z_score": 0.8
  },
  "correlation_period": 0.82,
  "cointegration_status": "cointegrated",
  "execution_time": 0.32,
  "use_mock": true
}
```

**Algorithm Details**:
- Calculate spread (symbol1 price - beta * symbol2 price)
- Detect mean reversion when spread deviates beyond threshold
- Monitor cointegration (beta) changes
- Track position hedges (long symbol1, short symbol2)
- Risk management with position sizing and stop losses
- Mock data: Generate paired price series with correlation

---

### 3. factor_analysis()
**Purpose**: Decompose returns into systematic factors (market, size, momentum, value)

**Input Parameters**:
- `backtest_result`: Strategy backtest result
- `factors`: List of factors to analyze (default: ['market', 'size', 'momentum', 'value'])
- `factor_returns`: Dict mapping factors to their historical returns
- `include_residuals`: Include unexplained returns (default: true)
- `analysis_period`: Days to analyze (default: 252, annual)
- `confidence_level`: Statistical confidence (default: 0.95)

**Output Format**:
```json
{
  "strategy": "TestStrategy",
  "factor_attribution": {
    "market": {
      "beta": 1.2,
      "contribution": 0.085,
      "contribution_pct": 56.7,
      "t_statistic": 3.45,
      "p_value": 0.001,
      "significant": true
    },
    "size": {
      "beta": 0.3,
      "contribution": 0.018,
      "contribution_pct": 12.0,
      "t_statistic": 2.1,
      "p_value": 0.035,
      "significant": true
    },
    "momentum": {
      "beta": 0.45,
      "contribution": 0.032,
      "contribution_pct": 21.3,
      "t_statistic": 1.8,
      "p_value": 0.072,
      "significant": false
    },
    "value": {
      "beta": 0.15,
      "contribution": 0.008,
      "contribution_pct": 5.3,
      "t_statistic": 0.9,
      "p_value": 0.368,
      "significant": false
    },
    "residual": {
      "contribution": 0.017,
      "contribution_pct": 11.3,
      "alpha": 0.0015
    }
  },
  "model_statistics": {
    "r_squared": 0.85,
    "adjusted_r_squared": 0.83,
    "f_statistic": 42.5,
    "durbin_watson": 1.95,
    "model_significance": "Highly Significant"
  },
  "risk_metrics": {
    "systematic_risk": 0.125,
    "idiosyncratic_risk": 0.045,
    "total_risk": 0.15
  },
  "execution_time": 0.28,
  "use_mock": true
}
```

**Algorithm Details**:
- Multi-factor regression analysis (Fama-French style)
- Calculate factor betas and loadings
- Compute contribution of each factor to returns
- Statistical significance testing (t-tests, p-values)
- Risk decomposition (systematic vs idiosyncratic)
- Mock data: Generate synthetic factor returns and loadings

---

### 4. regime_detector()
**Purpose**: Identify market regimes (bull, bear, high volatility, low volatility) and transitions

**Input Parameters**:
- `backtest_results`: List of backtest results or returns history
- `lookback_period`: Days for regime analysis (default: 60)
- `detection_method`: 'hmm' (Hidden Markov Model), 'volatility_based', 'correlation_based' (default: 'hmm')
- `n_regimes`: Number of market regimes (default: 3)
- `include_transitions`: Include regime transition analysis (default: true)
- `include_forecast`: Forecast next regime probability (default: true)

**Output Format**:
```json
{
  "current_regime": {
    "regime": "Bullish High Volatility",
    "regime_id": 1,
    "probability": 0.92,
    "characteristics": {
      "expected_return": 0.0025,
      "volatility": 0.025,
      "correlation": 0.65,
      "sharpe_ratio": 0.85
    },
    "duration_days": 8,
    "confidence": "High"
  },
  "regimes": [
    {
      "id": 0,
      "name": "Bullish Low Volatility",
      "probability": 0.35,
      "characteristics": {
        "mean_return": 0.0015,
        "volatility": 0.008,
        "correlation": 0.4
      },
      "frequency": 45,
      "avg_duration_days": 12
    },
    {
      "id": 1,
      "name": "Bullish High Volatility",
      "probability": 0.40,
      "characteristics": {
        "mean_return": 0.0025,
        "volatility": 0.025,
        "correlation": 0.65
      },
      "frequency": 35,
      "avg_duration_days": 8
    },
    {
      "id": 2,
      "name": "Bearish",
      "probability": 0.25,
      "characteristics": {
        "mean_return": -0.0015,
        "volatility": 0.02,
        "correlation": 0.75
      },
      "frequency": 18,
      "avg_duration_days": 6
    }
  ],
  "transitions": [
    {
      "from_regime": 0,
      "to_regime": 1,
      "transition_probability": 0.15,
      "count": 8
    },
    {
      "from_regime": 1,
      "to_regime": 2,
      "transition_probability": 0.20,
      "count": 7
    }
  ],
  "forecast": {
    "next_regime_probabilities": {
      "Bullish Low Volatility": 0.25,
      "Bullish High Volatility": 0.60,
      "Bearish": 0.15
    },
    "most_likely_next": "Bullish High Volatility",
    "confidence": 0.60
  },
  "strategy_performance_by_regime": [
    {
      "regime": "Bullish Low Volatility",
      "return": 0.018,
      "sharpe": 1.2,
      "max_dd": 0.03,
      "win_rate": 0.62
    }
  ],
  "execution_time": 0.35,
  "use_mock": true
}
```

**Algorithm Details**:
- Hidden Markov Model (HMM) for regime detection
- Gaussian Mixture Model (GMM) alternative
- Volatility-based thresholds for regime identification
- Transition matrix calculation
- Regime-specific strategy performance metrics
- Mock data: Generate regime-switching synthetic price series

---

## Implementation Notes

### File Structure
```
phase5_pairs_analyzer.py    # Main implementation (1200+ lines)
├── Phase5PairsAnalyzer class
├── get_pairs_analyzer() factory function
├── correlation_matrix() async method
├── pairs_backtest() async method
├── factor_analysis() async method
└── regime_detector() async method

test_phase5.py               # Comprehensive test suite
├── Mock data generation
├── All 4 tools tested
└── Performance verification
```

### Key Libraries
- `numpy`: Numerical computations
- `scipy.stats`: Statistical tests (cointegration, correlation)
- `statsmodels`: Factor regression, HMM
- `pandas`: Data manipulation

### Testing Strategy
- Mock-first development (all tools work with mock data)
- Unit tests for each tool
- Integration tests with MCP server
- Performance benchmarking

### MCP Server Integration
- Import: `from phase5_pairs_analyzer import get_pairs_analyzer`
- Handler methods: `handle_correlation_matrix()`, `handle_pairs_backtest()`, etc.
- Tool definitions: Complete inputSchema for all 4 tools
- Flags: `PAIRS_ANALYZER_AVAILABLE`

---

## Success Criteria

✅ All 4 tools implemented and tested
✅ 100% test pass rate
✅ MCP server integration complete
✅ Mock data generation working
✅ Comprehensive error handling
✅ Performance < 1 second per tool call
✅ All 16 tools in production

---

## Next Steps (After Phase 5)

Phase 5 completes the project with all 16 trading analysis tools:
- **Phase 1** (4 tools): Backtesting fundamentals
- **Phase 2** (5 tools): Data import and analysis
- **Phase 3** (4 tools): Advanced optimization
- **Phase 4** (4 tools): Risk analysis
- **Phase 5** (4 tools): Pairs trading & regime analysis

Final deliverable: Comprehensive MCP server with 16 tools for quantitative trading research and strategy development.
