# Jesse MCP Server - Product Requirements Document

**Project Name**: `jesse-mcp`

## Executive Summary

Build an MCP (Model Context Protocol) server that exposes Jesse's algorithmic trading framework capabilities to LLM agents, enabling autonomous strategy development, backtesting, optimization, and iterative improvement workflows.

**Vision**: An LLM agent that can independently research, develop, test, and refine trading strategies—running backtests, analyzing results, modifying code, and iterating until performance benchmarks are met.

### Key Capabilities

- **Backtesting** - Single and batch backtest execution via research module
- **Optimization** - Hyperparameter tuning with Optuna + walk-forward validation
- **Monte Carlo Analysis** - Statistical robustness testing (trade-shuffle & candle-resample)
- **Pairs Trading** - Cointegration testing, spread analysis, multi-route strategies
- **Candle Pipelines** - Synthetic data generation for stress testing

---

## Problem Statement

Current algorithmic trading strategy development is:
1. **Manual and tedious** - Developers must manually run backtests, analyze results, tweak parameters, repeat
2. **Prone to overfitting** - Easy to over-optimize on historical data without proper validation
3. **Time-consuming** - Each iteration cycle takes significant human attention
4. **Knowledge-gated** - Requires expertise in both trading and programming

**Opportunity**: Jesse's research module provides a clean, stateless Python API perfect for LLM automation. Combined with MCP, we can create an autonomous strategy development pipeline.

---

## Goals & Success Metrics

### Primary Goals
1. Enable LLM agents to run Jesse backtests programmatically
2. Support autonomous strategy iteration based on performance benchmarks
3. Maintain built-in overfitting protection through walk-forward validation
4. Provide rich feedback for LLM decision-making

### Success Metrics
| Metric | Target |
|--------|--------|
| Backtest execution time | <30s for 1-year daily data |
| Strategy iteration cycle | <5 minutes per iteration |
| Overfitting detection | 100% of iterations include OOS testing |
| Agent autonomy | Complete 10+ iteration cycles without human intervention |

---

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LLM Agent (Claude, etc.)                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                              MCP Protocol
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Jesse MCP Server                                │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                            TOOLS                                    │ │
│  │                                                                     │ │
│  │  Backtesting          Optimization         Strategy Management      │ │
│  │  ────────────         ────────────         ───────────────────      │ │
│  │  • backtest           • optimize           • strategy_list          │ │
│  │  • backtest_batch     • walk_forward       • strategy_read          │ │
│  │                                            • strategy_write         │ │
│  │                                            • strategy_validate      │ │
│  │                                                                     │ │
│  │  Data Management      Analysis             Utilities                │ │
│  │  ───────────────      ────────             ─────────                │ │
│  │  • candles_import     • analyze_results    • get_indicators         │ │
│  │  • candles_available  • compare_runs       • get_config             │ │
│  │                                                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                          RESOURCES                                  │ │
│  │                                                                     │ │
│  │  • strategies://list          Available strategies                  │ │
│  │  • strategies://{name}        Strategy source code                  │ │
│  │  • candles://{exchange}/{symbol}  Available data ranges             │ │
│  │  • results://latest           Most recent backtest results          │ │
│  │  • indicators://list          Available technical indicators        │ │
│  │                                                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                           PROMPTS                                   │ │
│  │                                                                     │ │
│  │  • iterate_strategy     Autonomous improvement workflow             │ │
│  │  • analyze_performance  Deep-dive metrics analysis                  │ │
│  │  • debug_strategy       Troubleshoot failing strategies             │ │
│  │                                                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Jesse Research Module                             │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ backtest()  │  │get_candles()│  │store_candles│  │ Optimizer   │    │
│  │             │  │             │  │             │  │             │    │
│  │ Pure func,  │  │ Fetch from  │  │ Import CSV  │  │ Optuna+Ray  │    │
│  │ stateless   │  │ database    │  │ data        │  │ parallel    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Jesse Database                                   │
│                                                                          │
│  • Candle data (1m resolution)                                          │
│  • Strategy definitions                                                  │
│  • Optimization sessions                                                 │
│  • Historical results                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            server1                                       │
│                                                                          │
│  ┌─────────────────────┐    ┌─────────────────────┐                     │
│  │  jesse-mcp-server   │    │   jesse-ntfy        │                     │
│  │  (new container)    │◄──►│   (existing)        │                     │
│  │                     │    │                     │                     │
│  │  Port: 3100 (stdio) │    │  Port: 9000 (GUI)   │                     │
│  │                     │    │                     │                     │
│  └─────────────────────┘    └─────────────────────┘                     │
│            │                          │                                  │
│            └──────────┬───────────────┘                                  │
│                       ▼                                                  │
│              ┌─────────────────┐                                        │
│              │  Shared Volume  │                                        │
│              │                 │                                        │
│              │  /srv/containers/jesse/                                  │
│              │  ├── strategies/                                         │
│              │  ├── data/                                               │
│              │  └── storage/                                            │
│              │                 │                                        │
│              └─────────────────┘                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Tool Specifications

### 1. `backtest`

Run a single backtest with specified parameters.

**Parameters:**
```typescript
{
  // Required
  strategy: string | StrategyCode,  // Strategy name or inline code
  symbol: string,                    // e.g., "BTC-USDT"
  timeframe: string,                 // e.g., "1h", "4h", "1D"
  start_date: string,                // "YYYY-MM-DD"
  end_date: string,                  // "YYYY-MM-DD"
  
  // Optional
  exchange?: string,                 // Default: "Binance"
  starting_balance?: number,         // Default: 10000
  fee?: number,                      // Default: 0.001 (0.1%)
  leverage?: number,                 // Default: 1 (futures only)
  leverage_mode?: "cross" | "isolated",
  exchange_type?: "spot" | "futures",
  hyperparameters?: Record<string, any>,  // Override strategy params
  
  // Output options
  include_trades?: boolean,          // Return individual trades
  include_equity_curve?: boolean,    // Return equity curve data
  include_logs?: boolean,            // Return strategy logs
}
```

**Returns:**
```typescript
{
  success: boolean,
  metrics: {
    total_trades: number,
    win_rate: number,
    net_profit_percentage: number,
    sharpe_ratio: number,
    sortino_ratio: number,
    calmar_ratio: number,
    omega_ratio: number,
    max_drawdown: number,
    annual_return: number,
    expectancy: number,
    ratio_avg_win_loss: number,
    winning_streak: number,
    losing_streak: number,
    largest_winning_trade: number,
    largest_losing_trade: number,
    average_holding_period: number,
    longs_count: number,
    shorts_count: number,
    // ... full metrics set
  },
  trades?: Trade[],
  equity_curve?: number[],
  logs?: string[],
  execution_time_ms: number,
  warnings?: string[],
}
```

**Example Usage:**
```
Agent: Run a backtest for the EMA crossover strategy on BTC-USDT 
       from 2023-01-01 to 2023-12-31 using 4h timeframe

Tool Call: backtest({
  strategy: "EmaCrossover",
  symbol: "BTC-USDT",
  timeframe: "4h",
  start_date: "2023-01-01",
  end_date: "2023-12-31",
  starting_balance: 10000,
  exchange_type: "futures",
  leverage: 2
})
```

---

### 2. `backtest_batch`

Run multiple backtests in parallel for comparison.

**Parameters:**
```typescript
{
  runs: Array<{
    name: string,           // Identifier for this run
    strategy: string,
    symbol: string,
    timeframe: string,
    start_date: string,
    end_date: string,
    hyperparameters?: Record<string, any>,
  }>,
  
  // Shared config
  exchange?: string,
  starting_balance?: number,
  fee?: number,
  exchange_type?: "spot" | "futures",
  leverage?: number,
}
```

**Returns:**
```typescript
{
  results: Array<{
    name: string,
    metrics: Metrics,
    success: boolean,
    error?: string,
  }>,
  comparison: {
    best_sharpe: string,      // Run name
    best_return: string,
    lowest_drawdown: string,
    most_trades: string,
  },
  execution_time_ms: number,
}
```

---

### 3. `optimize`

Run hyperparameter optimization with walk-forward validation.

**Parameters:**
```typescript
{
  strategy: string,
  symbol: string,
  timeframe: string,
  
  // Training period (in-sample)
  training_start: string,
  training_end: string,
  
  // Testing period (out-of-sample)  
  testing_start: string,
  testing_end: string,
  
  // Optimization config
  objective?: "sharpe" | "calmar" | "sortino" | "omega" | "serenity",
  optimal_trades?: number,      // Target trade count (affects fitness)
  max_trials?: number,          // Default: 100
  cpu_cores?: number,           // Default: auto
  
  // Optional overrides
  exchange?: string,
  starting_balance?: number,
  leverage?: number,
}
```

**Returns:**
```typescript
{
  best_parameters: Record<string, any>,
  best_dna: string,              // Base64 encoded params
  
  training_metrics: Metrics,
  testing_metrics: Metrics,      // Out-of-sample validation
  
  fitness_score: number,
  trials_completed: number,
  
  top_candidates: Array<{
    rank: number,
    parameters: Record<string, any>,
    training_sharpe: number,
    testing_sharpe: number,
    fitness: number,
  }>,
  
  overfitting_warning: boolean,  // True if testing << training
  execution_time_ms: number,
}
```

---

### 4. `walk_forward`

Run walk-forward optimization with multiple periods.

**Parameters:**
```typescript
{
  strategy: string,
  symbol: string,
  timeframe: string,
  
  start_date: string,
  end_date: string,
  
  // Walk-forward config
  training_days: number,        // Size of training window
  testing_days: number,         // Size of testing window
  step_days?: number,           // How much to advance (default: testing_days)
  
  objective?: string,
  optimal_trades?: number,
}
```

**Returns:**
```typescript
{
  periods: Array<{
    training_start: string,
    training_end: string,
    testing_start: string,
    testing_end: string,
    best_parameters: Record<string, any>,
    training_metrics: Metrics,
    testing_metrics: Metrics,
  }>,
  
  aggregate_metrics: {
    avg_training_sharpe: number,
    avg_testing_sharpe: number,
    consistency_score: number,   // How stable across periods
    overfitting_score: number,   // Difference between train/test
  },
  
  recommended_parameters: Record<string, any>,  // Most robust
}
```

---

### 5. `strategy_list`

List available strategies.

**Parameters:**
```typescript
{
  include_test_strategies?: boolean,  // Default: false
}
```

**Returns:**
```typescript
{
  strategies: Array<{
    name: string,
    path: string,
    has_hyperparameters: boolean,
    hyperparameters?: Array<{
      name: string,
      type: "int" | "float" | "categorical",
      min?: number,
      max?: number,
      options?: string[],
      default: any,
    }>,
  }>,
}
```

---

### 6. `strategy_read`

Read strategy source code.

**Parameters:**
```typescript
{
  name: string,
}
```

**Returns:**
```typescript
{
  name: string,
  code: string,
  path: string,
  hyperparameters: HyperparameterDef[],
}
```

---

### 7. `strategy_write`

Create or update a strategy.

**Parameters:**
```typescript
{
  name: string,
  code: string,
  overwrite?: boolean,  // Default: false, error if exists
}
```

**Returns:**
```typescript
{
  success: boolean,
  path: string,
  validation: {
    syntax_valid: boolean,
    imports_valid: boolean,
    class_structure_valid: boolean,
    errors?: string[],
    warnings?: string[],
  },
}
```

---

### 8. `strategy_validate`

Validate strategy code without saving.

**Parameters:**
```typescript
{
  code: string,
}
```

**Returns:**
```typescript
{
  valid: boolean,
  errors: string[],
  warnings: string[],
  detected_indicators: string[],
  has_hyperparameters: boolean,
  hyperparameters?: HyperparameterDef[],
}
```

---

### 9. `candles_import`

**Download new candle data from exchange autonomously.**

Jesse's `research.import_candles()` function allows the MCP server to directly download candle data from exchange APIs. This means **the server can fetch new data ranges on its own** without human intervention.

**Supported Exchanges:**
- Binance
- Bitfinex
- Bybit
- Coinbase
- Gate
- Hyperliquid
- Apex

**Parameters:**
```typescript
{
  exchange: string,              // e.g., "Binance"
  symbol: string,                // e.g., "BTC-USDT"
  start_date: string,            // "YYYY-MM-DD" (oldest data to fetch)
  end_date?: string,             // "YYYY-MM-DD" (default: today)
}
```

**Returns:**
```typescript
{
  success: boolean,
  candles_imported: number,      // Total candles downloaded
  date_range: {
    start: string,
    end: string,
  },
  execution_time_ms: number,
  exchange_supported: boolean,   // Is exchange available?
  warnings?: string[],           // e.g., gaps in data
}
```

**Example Usage:**
```
Agent: Download BTC candle data for all of 2023 from Binance

Tool Call: candles_import({
  exchange: "Binance",
  symbol: "BTC-USDT",
  start_date: "2023-01-01",
  end_date: "2023-12-31"
})

Response: {
  success: true,
  candles_imported: 525600,  // 1 minute candles for a year
  date_range: {
    start: "2023-01-01T00:00:00Z",
    end: "2023-12-31T23:59:00Z"
  },
  execution_time_ms: 45000
}
```

**Key Capability:**
This tool enables **autonomous data acquisition**. The LLM agent can decide to download new data ranges as needed during the iteration process, without requiring manual intervention.

---

### 10. `candles_available`

Check available candle data.

**Parameters:**
```typescript
{
  exchange?: string,      // Filter by exchange
  symbol?: string,        // Filter by symbol
}
```

**Returns:**
```typescript
{
  data: Array<{
    exchange: string,
    symbol: string,
    first_candle: string,   // ISO date
    last_candle: string,
    total_candles: number,
    gaps?: Array<{start: string, end: string}>,
  }>,
}
```

---

### 11. `analyze_results`

Deep analysis of backtest results.

**Parameters:**
```typescript
{
  metrics: Metrics,
  trades?: Trade[],
  equity_curve?: number[],
  
  analysis_type?: "full" | "summary" | "risk" | "trades",
}
```

**Returns:**
```typescript
{
  summary: string,           // Human-readable summary
  
  risk_analysis: {
    var_95: number,          // Value at Risk
    cvar_95: number,         // Conditional VaR
    max_consecutive_losses: number,
    recovery_time_avg: number,
  },
  
  trade_analysis?: {
    best_days: string[],
    worst_days: string[],
    avg_trade_duration: string,
    profit_factor: number,
  },
  
  recommendations: string[], // Actionable suggestions
}
```

---

### 12. `get_indicators`

List available technical indicators.

**Parameters:**
```typescript
{
  category?: "trend" | "momentum" | "volatility" | "volume" | "all",
  search?: string,
}
```

**Returns:**
```typescript
{
  indicators: Array<{
    name: string,
    function: string,        // e.g., "ta.ema"
    parameters: Array<{
      name: string,
      type: string,
      default?: any,
      description: string,
    }>,
    returns: string,         // Return type description
    example: string,         // Usage example
  }>,
}
```

---

### 13. `monte_carlo_trades`

Statistical robustness test by shuffling trade order.

**Purpose**: Tests whether your strategy's performance is dependent on the specific sequence of trades, or if it's robust to different orderings. Answers: "Was I just lucky with trade timing?"

**Parameters:**
```typescript
{
  // Backtest config (same as backtest tool)
  strategy: string,
  symbol: string,
  timeframe: string,
  start_date: string,
  end_date: string,
  
  // Monte Carlo config
  num_scenarios?: number,      // Default: 1000
  cpu_cores?: number,          // Default: auto
  
  // Optional
  hyperparameters?: Record<string, any>,
  fast_mode?: boolean,         // Default: true
}
```

**Returns:**
```typescript
{
  original: {
    metrics: Metrics,
    equity_curve: EquityCurve,
  },
  
  scenarios: Array<{
    total_return: number,
    max_drawdown: number,
    sharpe_ratio: number,
    calmar_ratio: number,
  }>,
  
  confidence_analysis: {
    summary: {
      num_simulations: number,
      significant_metrics_5pct: number,
      significant_metrics_1pct: number,
    },
    metrics: {
      [metric_name]: {
        original: number,
        simulations: { mean, std, min, max },
        percentiles: { 5th, 25th, 50th, 75th, 95th },
        confidence_intervals: {
          "90%": { lower, upper },
          "95%": { lower, upper },
        },
        p_value: number,
        is_significant_5pct: boolean,
        is_significant_1pct: boolean,
      }
    },
    interpretation: {
      detailed: Array<{ metric, significance, rank, message }>,
      overall: string,
    }
  },
  
  num_scenarios: number,
}
```

**Example Output Interpretation:**
```
Monte Carlo Trades Summary (1000 simulations):

Metric          | Original | Worst 5% | Median  | Best 5%
----------------|----------|----------|---------|--------
Return (%)      | 34.2%    | 28.1%    | 33.8%   | 39.2%
Max Drawdown    | -18.7%   | -22.3%   | -18.9%  | -15.1%
Sharpe Ratio    | 1.45     | 1.21     | 1.43    | 1.67

Interpretation: Your original result is in the top 25% of simulations.
Trade order DID matter - consider if strategy is robust.
```

---

### 14. `monte_carlo_candles`

Statistical robustness test using synthetic market data.

**Purpose**: Tests how your strategy performs across different possible market paths. Uses candle pipelines to generate synthetic but statistically similar price data. Answers: "Would my strategy work in alternative market histories?"

**Parameters:**
```typescript
{
  // Backtest config
  strategy: string,
  symbol: string,
  timeframe: string,
  start_date: string,
  end_date: string,
  
  // Monte Carlo config  
  num_scenarios?: number,      // Default: 1000
  cpu_cores?: number,
  
  // Candle generation pipeline
  pipeline: "gaussian_noise" | "moving_block_bootstrap",
  pipeline_config?: {
    // For gaussian_noise:
    close_sigma?: number,      // Noise std dev for close prices
    high_sigma?: number,
    low_sigma?: number,
    
    // For moving_block_bootstrap:
    // (auto-configured based on batch_size)
  },
  
  batch_size?: number,         // Default: 1440 (1 day of 1m candles)
}
```

**Returns:**
```typescript
{
  original: {
    metrics: Metrics,
    equity_curve: EquityCurve,
  },
  
  scenarios: Array<{
    scenario_index: number,
    metrics: Metrics,
    equity_curve: EquityCurve,
  }>,
  
  confidence_analysis: {
    // Same structure as monte_carlo_trades
    // But includes more metrics: win_rate, total_trades, annual_return
  },
  
  num_scenarios: number,
}
```

**Candle Pipeline Options:**

| Pipeline | Description | Use Case |
|----------|-------------|----------|
| `gaussian_noise` | Adds random noise to OHLC prices | Test sensitivity to small price variations |
| `moving_block_bootstrap` | Resamples blocks of price changes | Preserve autocorrelation while varying paths |

---

### 15. `pairs_analysis`

Analyze potential pairs trading relationships.

**Purpose**: Test cointegration and calculate spread statistics for pairs trading strategies.

**Parameters:**
```typescript
{
  symbol1: string,             // e.g., "BTC-USDT"
  symbol2: string,             // e.g., "ETH-USDT"
  exchange: string,
  start_date: string,
  end_date: string,
  timeframe?: string,          // Default: "1h"
  
  // Analysis options
  lookback_period?: number,    // For rolling calculations
  cointegration_cutoff?: number,  // p-value threshold, default: 0.05
}
```

**Returns:**
```typescript
{
  cointegration: {
    is_cointegrated: boolean,
    p_value: number,
    confidence: string,        // "high" | "medium" | "low"
  },
  
  spread_analysis: {
    current_z_score: number,
    mean: number,
    std: number,
    half_life: number,         // Mean reversion speed (candles)
  },
  
  hedge_ratio: {
    alpha: number,
    beta: number,              // Units of symbol2 per unit of symbol1
  },
  
  correlation: {
    pearson: number,
    rolling_30d: number[],
  },
  
  recommendation: {
    tradeable: boolean,
    entry_threshold: number,   // Suggested z-score for entry
    exit_threshold: number,
    position_sizing: string,   // Suggested allocation ratio
  }
}
```

**Example Usage:**
```
Agent: Analyze BTC-ETH pair for potential pairs trading on Binance, 
       using 2023 data

Tool Call: pairs_analysis({
  symbol1: "BTC-USDT",
  symbol2: "ETH-USDT", 
  exchange: "Binance",
  start_date: "2023-01-01",
  end_date: "2023-12-31"
})

Result:
  Cointegration: YES (p=0.023)
  Current Z-Score: 1.8 (spread is extended)
  Beta (hedge ratio): 0.065 ETH per BTC
  Half-life: 12 days
  
  Recommendation: Tradeable pair
  - Enter when |z| > 2.0
  - Exit when |z| < 0.5
  - Allocate 60% to BTC leg, 40% to ETH leg
```

---

### 16. `create_pairs_strategy`

Generate a pairs trading strategy from analysis.

**Parameters:**
```typescript
{
  symbol1: string,
  symbol2: string,
  exchange: string,
  
  // Strategy parameters
  entry_z_score?: number,      // Default: 2.0
  exit_z_score?: number,       // Default: 0.5
  lookback_period?: number,    // Default: 100
  risk_per_trade?: number,     // Default: 2 (%)
  
  // Output
  strategy_name: string,
}
```

**Returns:**
```typescript
{
  success: boolean,
  strategies: {
    leader: {
      name: string,
      code: string,
      path: string,
    },
    follower: {
      name: string, 
      code: string,
      path: string,
    }
  },
  routes_config: {
    // Ready-to-use route configuration
    routes: Route[],
    data_routes: DataRoute[],
  },
  instructions: string,        // How to use the generated strategies
}
```

---

## Resource Specifications

### `strategies://list`
Returns list of all available strategies with metadata.

### `strategies://{name}`
Returns full strategy details including source code.

### `candles://{exchange}/{symbol}`
Returns available date ranges for specific symbol.

### `results://latest`
Returns the most recent backtest results.

### `indicators://list`
Returns all available Jesse indicators with documentation.

---

## Prompt Specifications

### `iterate_strategy`

An autonomous workflow prompt for strategy improvement.

**Arguments:**
```typescript
{
  strategy_name: string,
  symbol: string,
  timeframe: string,
  
  // Benchmarks to achieve
  targets: {
    min_sharpe?: number,
    max_drawdown?: number,
    min_trades?: number,
    min_win_rate?: number,
  },
  
  // Constraints
  max_iterations?: number,    // Default: 20
  training_period: string,    // e.g., "2022-01-01:2023-06-30"
  testing_period: string,     // e.g., "2023-07-01:2023-12-31"
}
```

**Workflow:**
```
1. Read current strategy code
2. Run baseline backtest
3. Analyze results vs. targets
4. If targets met → return success
5. If iteration limit reached → return best result
6. Generate hypothesis for improvement
7. Modify strategy code
8. Validate syntax
9. Run backtest with train/test split
10. Compare to previous best
11. If better → keep changes, else → revert
12. Go to step 3
```

---

### `analyze_performance`

Deep-dive analysis with actionable insights.

**Arguments:**
```typescript
{
  backtest_result: BacktestResult,
}
```

**Output:**
Structured analysis including:
- Executive summary
- Risk assessment
- Trade pattern analysis
- Specific improvement suggestions
- Comparison to benchmarks

---

### `debug_strategy`

Troubleshoot a failing or underperforming strategy.

**Arguments:**
```typescript
{
  strategy_name: string,
  error_message?: string,
  unexpected_behavior?: string,
}
```

**Output:**
- Root cause analysis
- Code fix suggestions
- Test cases to verify fix

---

## Autonomous Iteration Workflow

The core value proposition - an LLM that can independently improve strategies:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AUTONOMOUS ITERATION LOOP                            │
└─────────────────────────────────────────────────────────────────────────┘

User Input:
  "Optimize my EMA crossover strategy to achieve Sharpe > 2.0 
   with max drawdown < 15% on BTC-USDT 2023 data"

                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ITERATION 1                                                              │
│                                                                          │
│ 1. strategy_read("EmaCrossover")                                        │
│    → Gets current strategy code                                          │
│                                                                          │
│ 2. backtest({                                                           │
│      strategy: "EmaCrossover",                                          │
│      training: "2023-01-01:2023-09-30",                                 │
│      testing: "2023-10-01:2023-12-31"                                   │
│    })                                                                    │
│    → Sharpe: 1.2, MaxDD: 22%, Trades: 45                                │
│                                                                          │
│ 3. Analysis:                                                             │
│    - Sharpe below target (1.2 < 2.0)                                    │
│    - Drawdown too high (22% > 15%)                                      │
│    - Hypothesis: EMA periods too reactive, need smoothing               │
│                                                                          │
│ 4. strategy_write("EmaCrossover_v2", modified_code)                     │
│    → Added volatility filter, adjusted EMA periods                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ITERATION 2                                                              │
│                                                                          │
│ 1. backtest({strategy: "EmaCrossover_v2", ...})                         │
│    → Sharpe: 1.6, MaxDD: 18%, Trades: 38                                │
│                                                                          │
│ 2. Analysis:                                                             │
│    - Improvement! But still below targets                                │
│    - Hypothesis: Position sizing too aggressive                          │
│                                                                          │
│ 3. Modify: Reduce risk per trade from 3% to 2%                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ITERATION 3                                                              │
│                                                                          │
│ 1. backtest({strategy: "EmaCrossover_v3", ...})                         │
│    → Sharpe: 2.1, MaxDD: 14%, Trades: 38                                │
│                                                                          │
│ 2. Analysis:                                                             │
│    - ALL TARGETS MET!                                                    │
│    - Training Sharpe: 2.1, Testing Sharpe: 1.9 (good consistency)       │
│                                                                          │
│ 3. Return final strategy + comprehensive report                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
Output:
  - Final strategy code
  - Performance report (train vs test)
  - Changelog of modifications
  - Risk assessment
  - Deployment recommendations
```

---

## Safety & Guardrails

### Overfitting Protection

1. **Mandatory Out-of-Sample Testing**
   - Every backtest includes train/test split
   - Results always show both periods
   - Warnings when test << train performance

2. **Minimum Trade Thresholds**
   - Strategies with <10 trades flagged as statistically insignificant
   - Fitness score penalizes low trade counts

3. **Walk-Forward Validation**
   - Built-in tool for multi-period validation
   - Consistency score across periods

4. **Iteration Limits**
   - Hard cap on autonomous iterations (default: 50)
   - Diminishing returns detection

### Resource Limits

```python
LIMITS = {
    "max_backtest_duration_days": 365 * 3,  # 3 years
    "max_optimization_trials": 500,
    "max_concurrent_backtests": 4,
    "max_strategy_file_size_kb": 100,
    "iteration_timeout_seconds": 600,
}
```

### Code Safety

1. **Syntax Validation** - All strategy code validated before execution
2. **Import Whitelist** - Only approved imports allowed
3. **No File System Access** - Strategies cannot access arbitrary files
4. **Sandboxed Execution** - Backtests run in isolated environment

---

## Implementation Phases

### Phase 1: Core Foundation (Week 1)
- [ ] MCP server scaffold (Python)
- [ ] `backtest` tool implementation
- [ ] `strategy_read` / `strategy_write` tools
- [ ] Basic validation
- [ ] Integration with existing Jesse container

### Phase 2: Optimization (Week 2)
- [ ] `optimize` tool implementation
- [ ] `walk_forward` tool
- [ ] `backtest_batch` for comparisons
- [ ] Results caching

### Phase 3: Data Management (Week 2-3)
- [ ] `candles_import` tool
- [ ] `candles_available` tool
- [ ] Data gap detection
- [ ] Multi-exchange support

### Phase 4: Analysis & Intelligence (Week 3)
- [ ] `analyze_results` tool
- [ ] `get_indicators` tool
- [ ] Resources implementation
- [ ] Rich metrics formatting

### Phase 5: Monte Carlo & Statistical Analysis (Week 3-4)
- [ ] `monte_carlo_trades` tool
- [ ] `monte_carlo_candles` tool
- [ ] Candle pipeline integration (Gaussian, Bootstrap)
- [ ] Confidence interval calculations
- [ ] Chart generation

### Phase 6: Pairs Trading (Week 4)
- [ ] `pairs_analysis` tool
- [ ] `create_pairs_strategy` tool
- [ ] Cointegration testing
- [ ] Multi-route strategy generation

### Phase 7: Autonomous Workflows (Week 4-5)
- [ ] `iterate_strategy` prompt
- [ ] Iteration loop logic
- [ ] Benchmark tracking
- [ ] Convergence detection

### Phase 8: Polish & Documentation (Week 5)
- [ ] Error handling refinement
- [ ] Performance optimization
- [ ] Usage documentation
- [ ] Example workflows

---

## Configuration

### MCP Server Config

```json
{
  "name": "jesse-mcp",
  "version": "1.0.0",
  "description": "Jesse algorithmic trading framework MCP server",
  
  "jesse": {
    "project_path": "/srv/containers/jesse",
    "strategies_path": "/srv/containers/jesse/strategies",
    "database_url": "postgresql://...",
    "default_exchange": "Binance",
    "default_fee": 0.001
  },
  
  "limits": {
    "max_backtest_days": 1095,
    "max_optimization_trials": 500,
    "max_iterations": 50,
    "backtest_timeout_seconds": 300
  },
  
  "safety": {
    "require_oos_testing": true,
    "min_trades_warning": 10,
    "overfitting_threshold": 0.5
  }
}
```

### Integration with OpenCode

```json
{
  "mcpServers": {
    "jesse-mcp": {
      "command": "python",
      "args": ["/srv/containers/jesse-mcp/server.py"],
      "env": {
        "JESSE_PROJECT_PATH": "/srv/containers/jesse"
      }
    }
  }
}
```

---

## Example Conversations

### Example 1: Simple Backtest

```
User: Run a backtest for Test01 strategy on ETH-USDT, 1h timeframe, 
      for all of 2023

Agent: I'll run that backtest for you.

[Tool: backtest]
{
  strategy: "Test01",
  symbol: "ETH-USDT", 
  timeframe: "1h",
  start_date: "2023-01-01",
  end_date: "2023-12-31"
}

Results:
- Total Trades: 127
- Win Rate: 58.3%
- Net Profit: +34.2%
- Sharpe Ratio: 1.45
- Max Drawdown: -18.7%
- Calmar Ratio: 1.83

The strategy shows positive performance with reasonable risk metrics.
The Sharpe of 1.45 indicates decent risk-adjusted returns, though 
the 18.7% max drawdown might be concerning for conservative portfolios.
```

### Example 2: Autonomous Optimization

```
User: I want to create a momentum strategy for BTC that achieves 
      Sharpe > 2.5 with max drawdown under 12%. Use 2022-2023 data 
      for training and first half of 2024 for validation.

Agent: I'll develop this iteratively. Let me start by creating a 
       baseline momentum strategy and then improve it.

[Creates initial strategy with RSI + trend filter]
[Runs backtest: Sharpe 1.3, DD 24%]

The baseline is underperforming. Key issues:
- Drawdown too high (24% vs 12% target)
- Sharpe needs improvement (1.3 vs 2.5 target)

Iteration 2: Adding volatility filter and tighter stops...
[Runs backtest: Sharpe 1.8, DD 16%]

Better! Continuing optimization...

[... 5 more iterations ...]

Final Results after 7 iterations:

Training Period (2022-2023):
- Sharpe: 2.7 ✓
- Max DD: 11.2% ✓
- Trades: 89

Validation Period (2024 H1):  
- Sharpe: 2.3
- Max DD: 13.1%
- Trades: 34

The strategy meets targets on training data. Validation shows 
slight degradation but remains robust. The consistency between
train/test suggests low overfitting risk.

Shall I save this as a new strategy?
```

### Example 3: Monte Carlo Robustness Testing

```
User: I have a strategy that looks great on backtests but I'm worried 
      it might just be luck. Can you test if it's statistically robust?

Agent: I'll run both Monte Carlo analyses to test robustness.

[Tool: monte_carlo_trades]
Running 1000 trade-shuffle simulations...

Trade-Order Sensitivity Analysis:
┌─────────────────┬──────────┬──────────┬─────────┬─────────┐
│ Metric          │ Original │ Worst 5% │ Median  │ Best 5% │
├─────────────────┼──────────┼──────────┼─────────┼─────────┤
│ Return (%)      │ 34.2%    │ 28.1%    │ 33.8%   │ 39.2%   │
│ Max Drawdown    │ -18.7%   │ -22.3%   │ -18.9%  │ -15.1%  │
│ Sharpe Ratio    │ 1.45     │ 1.21     │ 1.43    │ 1.67    │
└─────────────────┴──────────┴──────────┴─────────┴─────────┘

Your original performance is at the 68th percentile - above median 
but not exceptional. The strategy is NOT overly dependent on trade 
order, which is good.

[Tool: monte_carlo_candles]  
Running 500 candle-resample simulations with moving block bootstrap...

Market-Path Robustness Analysis:
┌─────────────────┬──────────┬──────────┬─────────┬─────────┐
│ Metric          │ Original │ Worst 5% │ Median  │ Best 5% │
├─────────────────┼──────────┼──────────┼─────────┼─────────┤
│ Return (%)      │ 34.2%    │ 12.3%    │ 28.7%   │ 51.2%   │
│ Max Drawdown    │ -18.7%   │ -31.2%   │ -21.3%  │ -12.8%  │
│ Sharpe Ratio    │ 1.45     │ 0.72     │ 1.18    │ 1.89    │
│ Win Rate        │ 58.3%    │ 48.2%    │ 55.1%   │ 64.7%   │
└─────────────────┴──────────┴──────────┴─────────┴─────────┘

Wider variance here - your original is at the 71st percentile.
The strategy would have been profitable in 89% of simulated 
market paths.

Summary:
✓ Trade-order robust (not lucky sequencing)
✓ Market-path robust (works across different conditions)
⚠ Drawdown could reach -31% in adverse conditions (5th percentile)

Recommendation: Strategy is statistically sound. Consider adding 
a volatility filter to reduce worst-case drawdown scenarios.
```

### Example 4: Pairs Trading Setup

```
User: I want to set up a pairs trade between BTC and ETH. 
      Can you analyze the relationship and create a strategy?

Agent: I'll analyze the BTC-ETH relationship and generate a 
       pairs trading strategy.

[Tool: pairs_analysis]
{
  symbol1: "BTC-USDT",
  symbol2: "ETH-USDT",
  exchange: "Binance",
  start_date: "2023-01-01",
  end_date: "2023-12-31"
}

Pairs Analysis Results:

Cointegration Test:
  ✓ Cointegrated (p-value: 0.023)
  Confidence: HIGH

Spread Statistics:
  Current Z-Score: 1.82 (spread extended - BTC expensive vs ETH)
  Half-Life: 14.3 days (reasonable mean reversion speed)
  
Hedge Ratio:
  Beta: 0.0652 (for every 1 BTC, short 15.3 ETH)
  
Correlation:
  Pearson: 0.89
  30-day Rolling: [0.82, 0.91, 0.88, ...]

This pair is suitable for mean-reversion trading.

[Tool: create_pairs_strategy]
{
  symbol1: "BTC-USDT",
  symbol2: "ETH-USDT",
  entry_z_score: 2.0,
  exit_z_score: 0.5,
  strategy_name: "BtcEthPairs"
}

Created two strategies:
1. BtcEthPairs (leader) - handles cointegration checks & signals
2. BtcEthPairs_Follower - executes ETH leg based on leader signals

Routes configuration:
[
  {exchange: "Binance", strategy: "BtcEthPairs", symbol: "BTC-USDT", timeframe: "1h"},
  {exchange: "Binance", strategy: "BtcEthPairs_Follower", symbol: "ETH-USDT", timeframe: "1h"}
]

Shall I backtest this pairs strategy?
```

---

## Open Questions

1. **Database Access**: Should MCP server share Jesse's PostgreSQL or use separate storage?

2. **Real-time Data**: Should we support live data feeds for paper trading validation?

3. **Multi-Symbol Strategies**: How to handle strategies that trade multiple pairs?

4. **Notification Integration**: Should iteration progress notify via ntfy?

5. **Version Control**: Should strategy iterations be git-tracked automatically?

---

## Appendix A: Jesse Metrics Reference

| Metric | Formula | Good Value |
|--------|---------|------------|
| Sharpe Ratio | (Return - Rf) / StdDev | > 1.5 |
| Sortino Ratio | (Return - Rf) / DownsideStdDev | > 2.0 |
| Calmar Ratio | CAGR / MaxDrawdown | > 1.0 |
| Omega Ratio | Prob(gain) / Prob(loss) | > 1.5 |
| Win Rate | Wins / Total | > 50% |
| Profit Factor | GrossProfit / GrossLoss | > 1.5 |
| Expectancy | (WinRate × AvgWin) - (LossRate × AvgLoss) | > 0 |

---

## Appendix B: Indicator Categories

**Trend**: EMA, SMA, TEMA, KAMA, SuperTrend, Ichimoku, Alligator
**Momentum**: RSI, MACD, Stochastic, CCI, Williams %R, MFI
**Volatility**: ATR, Bollinger Bands, Keltner Channel, Donchian
**Volume**: OBV, VWAP, Volume Oscillator, Accumulation/Distribution

Full list: 200+ indicators available via `ta.*`

---

## Appendix C: Strategy Template

```python
from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils


class MyStrategy(Strategy):
    """
    Strategy description here.
    """
    
    def hyperparameters(self) -> list:
        return [
            {'name': 'ema_fast', 'type': int, 'min': 5, 'max': 50, 'default': 12},
            {'name': 'ema_slow', 'type': int, 'min': 20, 'max': 200, 'default': 26},
            {'name': 'risk_pct', 'type': float, 'min': 1, 'max': 5, 'default': 2},
        ]
    
    @property
    def fast_ema(self):
        return ta.ema(self.candles, self.hp['ema_fast'])
    
    @property
    def slow_ema(self):
        return ta.ema(self.candles, self.hp['ema_slow'])
    
    def should_long(self) -> bool:
        return self.fast_ema > self.slow_ema
    
    def should_short(self) -> bool:
        return self.fast_ema < self.slow_ema
    
    def go_long(self):
        entry = self.price
        stop = entry - ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(
            self.available_margin, 
            self.hp['risk_pct'], 
            entry, 
            stop, 
            fee_rate=self.fee_rate
        )
        self.buy = qty, entry
    
    def go_short(self):
        entry = self.price
        stop = entry + ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(
            self.available_margin,
            self.hp['risk_pct'],
            entry,
            stop,
            fee_rate=self.fee_rate
        )
        self.sell = qty, entry
    
    def on_open_position(self, order):
        if self.is_long:
            self.stop_loss = self.position.qty, self.price - ta.atr(self.candles) * 2
            self.take_profit = self.position.qty, self.price + ta.atr(self.candles) * 3
        elif self.is_short:
            self.stop_loss = self.position.qty, self.price + ta.atr(self.candles) * 2
            self.take_profit = self.position.qty, self.price - ta.atr(self.candles) * 3
    
    def should_cancel_entry(self) -> bool:
        return True
    
    def update_position(self):
        # Trailing stop logic here
        pass
```

---

## Appendix D: Monte Carlo Methods

### Trade-Shuffle Monte Carlo

**What it tests**: Whether your strategy's performance depends on the specific order of trades.

**How it works**:
1. Run original backtest, collect all trades
2. Shuffle trade order randomly (1000+ times)
3. Reconstruct equity curves from shuffled trades
4. Calculate metrics for each scenario
5. Compare original to distribution

**Interpretation**:
- If original is near median → Performance is robust to trade order
- If original is in top 5% → Might have been lucky with sequencing
- If original is in bottom 5% → Unlikely to be sustainable

### Candle-Resample Monte Carlo

**What it tests**: How your strategy performs across different possible market paths.

**How it works**:
1. Apply candle pipeline to generate synthetic data:
   - **Gaussian Noise**: Adds random perturbations to prices
   - **Moving Block Bootstrap**: Resamples blocks of price changes while preserving autocorrelation
2. Run backtest on each synthetic dataset
3. Collect metrics across all scenarios

**Candle Pipelines Available**:

| Pipeline | Parameters | Best For |
|----------|------------|----------|
| `GaussianNoiseCandlesPipeline` | `close_sigma`, `high_sigma`, `low_sigma` | Testing price sensitivity |
| `MovingBlockBootstrapCandlesPipeline` | `batch_size` (auto block size) | Realistic alternative histories |

**Example Pipeline Config**:
```python
# Gaussian noise: 0.1% std dev on close prices
pipeline_kwargs = {
    "batch_size": 1440,
    "close_sigma": 0.001,
    "high_sigma": 0.0005,
    "low_sigma": 0.0005,
}

# Moving block bootstrap: auto-configured
pipeline_kwargs = {
    "batch_size": 1440,  # Block size derived automatically
}
```

---

## Appendix E: Pairs Trading Utilities

### Cointegration Testing

Jesse provides `utils.are_cointegrated()` using the Engle-Granger two-step method:

```python
from jesse import utils

# Test if two price series are cointegrated
is_coint = utils.are_cointegrated(
    price_returns_1,  # np.ndarray of returns
    price_returns_2,
    cutoff=0.05       # p-value threshold
)
```

**Interpretation**:
- p < 0.05 → Series are cointegrated (mean-reverting spread)
- p >= 0.05 → No cointegration (spread may drift)

### Hedge Ratio Calculation

```python
from jesse import utils

alpha, beta = utils.calculate_alpha_beta(returns1, returns2)
# beta = hedge ratio (units of asset2 per unit of asset1)
```

### Z-Score for Spread

```python
from jesse import utils

spread = prices1 - beta * prices2
z_scores = utils.z_score(spread)
# z > 2: spread extended (short spread)
# z < -2: spread contracted (long spread)
```

### Pairs Strategy Architecture

Jesse supports multi-route strategies using `shared_vars`:

```python
# Leader strategy (symbol 1)
class PairsLeader(Strategy):
    def before(self):
        # Calculate spread z-score
        z = calculate_z_score(...)
        
        # Signal to follower via shared_vars
        if z > 2:
            self.shared_vars["signal"] = "short_spread"
        elif z < -2:
            self.shared_vars["signal"] = "long_spread"
        else:
            self.shared_vars["signal"] = "neutral"

# Follower strategy (symbol 2)
class PairsFollower(Strategy):
    def should_long(self):
        # Opposite of leader for spread trade
        return self.shared_vars.get("signal") == "short_spread"
    
    def should_short(self):
        return self.shared_vars.get("signal") == "long_spread"
```

---

## Appendix F: Utility Functions Reference

### Risk Management

| Function | Description |
|----------|-------------|
| `utils.risk_to_qty(capital, risk_pct, entry, stop, fee_rate)` | Position size from risk % |
| `utils.size_to_qty(size, price, precision, fee_rate)` | Convert $ size to quantity |
| `utils.qty_to_size(qty, price)` | Convert quantity to $ size |
| `utils.estimate_risk(entry, stop)` | Risk per share |
| `utils.limit_stop_loss(entry, stop, type, max_risk_pct)` | Constrain stop loss |
| `utils.kelly_criterion(win_rate, avg_win_loss_ratio)` | Optimal bet size |

### Statistical

| Function | Description |
|----------|-------------|
| `utils.z_score(series)` | Z-score normalization |
| `utils.are_cointegrated(r1, r2, cutoff)` | Cointegration test |
| `utils.calculate_alpha_beta(r1, r2)` | OLS regression |
| `utils.prices_to_returns(prices)` | Price → returns conversion |

### Helpers

| Function | Description |
|----------|-------------|
| `utils.crossed(s1, s2, direction, sequential)` | Cross detection |
| `utils.strictly_increasing(series, lookback)` | Trend detection |
| `utils.strictly_decreasing(series, lookback)` | Trend detection |
| `utils.streaks(series)` | Win/loss streak calculation |
| `utils.anchor_timeframe(tf)` | Get higher timeframe |

---

*Document Version: 1.1*
*Created: 2024-11-26*
*Updated: 2024-11-26 - Added Monte Carlo & Pairs Trading*
*Author: OpenCode + Human Collaboration*
