# The Badass Jesse MCP Conversational Pipeline

## Executive Summary

A conversational CI/CD pipeline that enables LLM agents to have multi-turn conversations with users about trading strategies, iteratively improving them toward specified goals (e.g., Sharpe ratio 2.0).

**Vision**: User describes a strategy improvement idea → System reads code → Creates variants → Tests them → Validates security → Compares results → Auto-iterates toward goals → Generates intelligent reports.

---

## Architecture Overview

### System Flow

```
User Input (Natural Language)
    ↓
Conversational Orchestrator (Multi-turn state management)
    ↓
┌─────────────────────────────────────────────────┐
│  Tool Execution Layer (MCP Tools + New Tools)   │
├─────────────────────────────────────────────────┤
│  • strategy_read() - Get current code           │
│  • strategy_make() - Create variant [NEW]       │
│  • strategy_write() - Modify code [NEW]         │
│  • strategy_validate() - Validate code          │
│  • backtest() - Single backtest                 │
│  • compare_backtest() - A/B test [NEW]          │
│  • analyze_results() - Extract metrics          │
│  • iterate_strategy() - Auto-improve [NEW]      │
│  • risk_report() - Risk analysis                │
│  • generate_report() - Final summary [NEW]      │
└─────────────────────────────────────────────────┘
    ↓
LLM (Claude) with Tool Calling
    ↓
Conversational Response to User
```

### State Management

```python
ConversationState {
  session_id: str                    # Unique conversation ID
  base_strategy: str                 # Original strategy name
  current_variant: dict              # {name, code, results}
  iteration_history: list            # All variants tested
  goal: dict                          # {metric: "sharpe", target: 2.0}
  backtests: dict                     # {variant_name: result}
  comparisons: dict                   # {pair: comparison_result}
  conversation_turn: int              # Turn counter for context
}
```

---

## New MCP Tools Specification

### 1. strategy_make()

**Purpose**: Create a new strategy variant from an existing strategy

**Input Parameters**:
- `base_strategy`: str - Name of base strategy (e.g., "EMA_crossover")
- `variant_name`: str - Name for new variant (e.g., "EMA_with_volatility_filter")
- `description`: str - What's being changed (e.g., "Adding volatility filter to entry signals")
- `modifications`: dict - Specific code changes to make

**Output Format**:
```json
{
  "success": true,
  "variant_name": "EMA_with_volatility_filter",
  "base_strategy": "EMA_crossover",
  "code_path": "/path/to/variant/code.py",
  "code_preview": "First 100 lines of created code",
  "modification_count": 5,
  "ready_for_test": true
}
```

**Algorithm**:
1. Read base strategy code via `strategy_read()`
2. Parse strategy structure (imports, class def, indicators, logic)
3. Apply modifications intelligently (comment old logic, add new logic)
4. Create new file with variant name
5. Return code preview for validation

---

### 2. strategy_write()

**Purpose**: Intelligently modify strategy code based on natural language description

**Input Parameters**:
- `strategy_name`: str - Strategy to modify
- `modification_request`: str - Natural language description (e.g., "Add RSI overbought/oversold filter")
- `parameters`: dict - Optional parameter specifications
- `safety_check`: bool - Whether to validate before writing

**Output Format**:
```json
{
  "success": true,
  "strategy_name": "EMA_crossover_modified",
  "changes": [
    {
      "type": "added",
      "location": "entry_signal()",
      "code": "rsi = talib.RSI(self.candles[-50:])",
      "description": "Added RSI calculation"
    }
  ],
  "code_preview": "Modified code snippet",
  "validation_result": {
    "valid": true,
    "issues": []
  }
}
```

**Algorithm**:
1. Read current strategy code
2. Use Claude to understand modification request
3. Generate code modifications with context
4. Syntax validation
5. Optional security checks via validation agent
6. Write modified code

---

### 3. compare_backtest()

**Purpose**: Run A/B comparison tests between two strategy versions

**Input Parameters**:
- `strategy_1`: str - First strategy name
- `strategy_2`: str - Second strategy name
- `symbol`: str - Trading pair (e.g., "BTC-USDT")
- `timeframe`: str - Timeframe (e.g., "1h")
- `start_date`: str - Backtest start date
- `end_date`: str - Backtest end date
- `metrics_to_compare`: list - Which metrics to focus on (default: all)

**Output Format**:
```json
{
  "comparison": {
    "strategy_1": {
      "name": "EMA_crossover",
      "return": 0.45,
      "sharpe": 1.2,
      "max_dd": 0.15,
      "win_rate": 0.58
    },
    "strategy_2": {
      "name": "EMA_with_volatility",
      "return": 0.52,
      "sharpe": 1.6,
      "max_dd": 0.12,
      "win_rate": 0.62
    },
    "winner": "strategy_2",
    "improvements": {
      "return": "+15.6%",
      "sharpe": "+33.3%",
      "max_dd": "-20.0%",
      "win_rate": "+6.9%"
    },
    "statistical_significance": {
      "sharpe_ttest": {
        "t_statistic": 2.45,
        "p_value": 0.014,
        "significant": true
      }
    }
  },
  "recommendation": "Strategy 2 shows statistically significant improvement. Consider adopting it."
}
```

**Algorithm**:
1. Run backtest on both strategies (parallel)
2. Extract key metrics from both
3. Calculate percentage improvements
4. Run t-tests for statistical significance
5. Generate winner recommendation with confidence

---

### 4. iterate_strategy()

**Purpose**: Automatically improve strategy toward a goal (e.g., Sharpe 2.0)

**Input Parameters**:
- `base_strategy`: str - Strategy to improve
- `goal`: dict - Goal specification (e.g., {"metric": "sharpe", "target": 2.0})
- `max_iterations`: int - Maximum iterations (default: 5)
- `iteration_strategy`: str - "random_params" | "genetic" | "bayesian" (default: "bayesian")
- `symbol`: str - Trading pair for backtests
- `timeframe`: str - Timeframe
- `date_range`: dict - {start_date, end_date}

**Output Format**:
```json
{
  "base_strategy": "EMA_crossover",
  "goal": {"metric": "sharpe", "target": 2.0},
  "iterations": [
    {
      "iteration": 1,
      "variant": "EMA_crossover_iter1",
      "modifications": "Optimized EMA periods: fast=8, slow=24",
      "metrics": {"return": 0.48, "sharpe": 1.35, "max_dd": 0.14},
      "improvement": "+12.5%",
      "converging": true
    },
    {
      "iteration": 2,
      "variant": "EMA_crossover_iter2",
      "modifications": "Added volume confirmation filter",
      "metrics": {"return": 0.54, "sharpe": 1.68, "max_dd": 0.11},
      "improvement": "+24.4%",
      "converging": true
    },
    {
      "iteration": 3,
      "variant": "EMA_crossover_iter3",
      "modifications": "Enhanced stop loss logic",
      "metrics": {"return": 0.56, "sharpe": 1.92, "max_dd": 0.09},
      "improvement": "+42.4%",
      "converging": true
    }
  ],
  "best_variant": "EMA_crossover_iter3",
  "best_metrics": {"return": 0.56, "sharpe": 1.92, "max_dd": 0.09},
  "goal_achieved": false,
  "goal_progress": "96% toward Sharpe 2.0",
  "recommendation": "Iteration 3 achieves 1.92 Sharpe. One more iteration might reach the goal."
}
```

**Algorithm**:
1. Run initial backtest on base strategy
2. For each iteration:
   - Use selected algorithm (Bayesian optimization recommended) to suggest changes
   - Create variant with modifications
   - Run backtest
   - Compare to previous best
   - Update goal progress
   - Decide if converging or should continue
3. Return all iterations with recommendations

---

### 5. generate_report()

**Purpose**: Create intelligent final report with recommendations

**Input Parameters**:
- `comparison_results`: dict - Results from compare_backtest()
- `iteration_results`: dict - Results from iterate_strategy()
- `risk_analysis`: dict - Results from risk_report()
- `report_format`: str - "summary" | "detailed" | "executive"
- `include_visualizations`: bool

**Output Format**:
```json
{
  "report": {
    "executive_summary": "Strategy improvements achieved 42% gain in Sharpe ratio...",
    "key_findings": [
      "Original Sharpe: 1.2 → Optimized: 1.92 (+60%)",
      "Risk (max drawdown) improved from 15% to 9%",
      "Win rate increased from 58% to 72%"
    ],
    "recommendation": {
      "action": "ADOPT_OPTIMIZED_VERSION",
      "confidence": 0.92,
      "rationale": "Consistent improvements across all key metrics with strong statistical significance"
    },
    "risk_assessment": {
      "var_95": 0.045,
      "cvar_95": 0.068,
      "stress_test_result": "Remains profitable in all tested scenarios"
    },
    "next_steps": [
      "Deploy optimized strategy with position sizing constraints",
      "Monitor live performance vs. backtest for first 30 days",
      "Re-optimize monthly with new market data"
    ]
  },
  "metadata": {
    "generated_at": "2025-12-11T10:30:00Z",
    "session_id": "conv_abc123",
    "strategies_tested": 5,
    "total_backtests": 8
  }
}
```

---

## Conversational Orchestrator

### Multi-Turn Conversation Manager

```python
class ConversationOrchestrator:
    """Manages multi-turn strategy improvement conversations"""
    
    async def start_conversation(self, user_message: str) -> str:
        """Start new conversation about strategy improvements"""
        
    async def continue_conversation(self, 
                                   session_id: str, 
                                   user_message: str) -> str:
        """Continue existing conversation"""
        
    async def get_conversation_state(self, session_id: str) -> ConversationState:
        """Get current state of conversation"""
        
    async def suggest_next_step(self, session_id: str) -> str:
        """AI suggests what to do next based on progress"""
        
    async def handle_tool_call(self, 
                              session_id: str, 
                              tool_name: str, 
                              parameters: dict) -> dict:
        """Execute tool and update conversation state"""
```

### Conversation Flow Example

```
User: "I have an EMA strategy. Can you test if adding a volatility filter improves it?"

System:
1. Create ConversationState with "EMA_crossover" as base
2. Call strategy_read("EMA_crossover")
3. Call strategy_make("EMA_crossover", "EMA_with_volatility_filter", "Add vol filter")
4. Call compare_backtest("EMA_crossover", "EMA_with_volatility_filter", ...)
5. Respond: "Great! The volatility filter improved Sharpe from 1.2 to 1.45 (+20.8%). 
             Would you like me to iterate on this to try reaching Sharpe 2.0?"

User: "Yes, go for it. Try to reach Sharpe 2.0 in the next 3 iterations."

System:
1. Update goal: {metric: "sharpe", target: 2.0}
2. Call iterate_strategy("EMA_with_volatility_filter", max_iterations=3, ...)
3. Return iteration results
4. Call generate_report(...)
5. Respond: "Excellent progress! Iteration 3 achieved Sharpe 1.92 (96% of goal). 
             The strategy now has better risk management too (max DD: 9%). 
             I recommend deploying this version. Here's the full report..."
```

---

## Strategy Validation Agent

### Security & Sanity Checks

```python
class StrategyValidator:
    """Validates strategy code for safety and viability"""
    
    async def validate_code(self, code: str) -> ValidationResult:
        """Check code for:
        - No infinite loops
        - Proper position sizing
        - Valid indicators
        - No data leakage
        - Proper error handling
        """
        
    async def check_parameter_ranges(self, parameters: dict) -> bool:
        """Verify parameters are within reasonable ranges"""
        
    async def assess_complexity(self, code: str) -> str:
        """Rate code complexity: simple | moderate | complex"""
```

---

## Integration with MCP Server

### New Tools Added to server.py

```python
@mcp.tool
async def strategy_make(
    base_strategy: str,
    variant_name: str,
    description: str,
    modifications: dict
) -> dict:
    """Create new strategy variant from existing strategy"""

@mcp.tool
async def strategy_write(
    strategy_name: str,
    modification_request: str,
    parameters: Optional[dict] = None,
    safety_check: bool = True
) -> dict:
    """Intelligently modify strategy code"""

@mcp.tool
async def compare_backtest(
    strategy_1: str,
    strategy_2: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    metrics_to_compare: Optional[list] = None
) -> dict:
    """Run A/B comparison tests"""

@mcp.tool
async def iterate_strategy(
    base_strategy: str,
    goal: dict,
    max_iterations: int = 5,
    iteration_strategy: str = "bayesian",
    symbol: str = "BTC-USDT",
    timeframe: str = "1h",
    date_range: dict = None
) -> dict:
    """Auto-improve strategy toward goal"""

@mcp.tool
async def generate_report(
    comparison_results: dict,
    iteration_results: dict,
    risk_analysis: dict,
    report_format: str = "summary",
    include_visualizations: bool = False
) -> dict:
    """Generate intelligent final report"""
```

---

## Implementation Phases

### Phase 1: Core Tool Implementation
- Implement strategy_make()
- Implement strategy_write()
- Basic code generation without LLM dependency

### Phase 2: Comparison & Testing
- Implement compare_backtest()
- Add statistical significance testing
- Report generation

### Phase 3: Iteration & Optimization
- Implement iterate_strategy()
- Add Bayesian optimization
- Goal tracking and convergence detection

### Phase 4: Conversation Layer
- Build ConversationOrchestrator
- Multi-turn state management
- Integration with Claude API

### Phase 5: Validation & Safety
- Implement StrategyValidator
- Security checks
- Code quality assessment

### Phase 6: Integration & Testing
- Add all tools to MCP server
- End-to-end conversational tests
- Performance optimization

---

## Success Criteria

✅ User can have natural multi-turn conversations about strategy improvements
✅ All 5 new tools work correctly with mock data
✅ Conversational state persists across turns
✅ Strategy validation prevents unsafe code
✅ Reports are intelligent and actionable
✅ End-to-end conversational flow works (read → make → test → iterate → report)
✅ Performance: Each tool <2 seconds, conversation response <5 seconds

---

## Example Conversation

```
User: "I've been trading with my EMA strategy but it's underperforming. 
       The Sharpe is only 1.2. Can you help me improve it?"