# Jesse MCP Development Guidelines

## Project Overview

Jesse MCP is a Model Context Protocol (MCP) server exposing Jesse's algorithmic trading framework capabilities to LLM agents. It provides 17 tools across 5 phases: backtesting, optimization, risk analysis, pairs trading, and data management.

## Agent Persona

When working on trading strategy tasks, adopt the persona defined in **jessegpt.md**:
- Strategy Optimization Expert
- Risk Management Expert  
- Backtesting & Analysis Expert

Apply the communication style and output format from that document for all trading-related work.

## Build/Lint/Test Commands

```bash
# Install dependencies (runtime)
pip install -r requirements.txt

# Install dependencies (development)
pip install -r requirements-dev.txt

# Install package in editable mode
pip install -e .

# Run all tests
pytest

# Run all tests with verbose output
pytest -v

# Run single test file
pytest tests/test_server.py

# Run single test function
pytest tests/test_server.py::test_tools_list

# Run single test class method
pytest tests/test_optimizer.py::test_optimize

# Run tests matching a pattern
pytest -k "monte_carlo"

# Run tests with print output visible
pytest -v -s tests/test_optimizer.py

# Lint code with flake8
flake8 jesse_mcp/

# Format code with black
black jesse_mcp/

# Type checking with mypy
mypy jesse_mcp/

# Run the MCP server (stdio transport)
python -m jesse_mcp

# Run the MCP server (HTTP transport)
python -m jesse_mcp --transport http --port 8000
```

## Code Style Guidelines

### Imports & Formatting
- Use `black` for code formatting (88 character line length)
- Import order: stdlib → third-party → local imports (separate with blank lines)
- Use absolute imports from package root: `from jesse_mcp.core.integrations import ...`
- Maximum line length: 100 (flake8), 88 (black default)
- Use double quotes for strings

### Import Pattern Example
```python
import asyncio
import logging
from typing import Dict, List, Any, Optional

import numpy as np

from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE
```

### Type Annotations
- Use `typing` module for all function signatures
- Use `Optional[T]` for nullable returns
- Use `Dict[str, Any]` for flexible JSON-like structures
- Use `List[T]` for typed lists
- Use `Union[T1, T2]` for multiple types

```python
async def optimize(
    self,
    strategy: str,
    symbol: str,
    param_space: Dict[str, Dict[str, Any]],
    metric: str = "total_return",
) -> Dict[str, Any]:
```

### Naming Conventions
- Classes: `PascalCase` (e.g., `Phase3Optimizer`, `JesseWrapper`)
- Functions/variables: `snake_case` (e.g., `get_optimizer`, `backtest_result`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `JESSE_AVAILABLE`, `OPTUNA_AVAILABLE`)
- Private members: prefix with underscore (`_internal_method`, `_calculate_convergence`)
- Module-level singletons: `_optimizer_instance`, `_initialized`

### Error Handling
- Use try/except blocks for optional imports with fallback behavior
- Log warnings with `logger.warning()` when dependencies unavailable
- Return `{"error": str(e), "error_type": type(e).__name__}` for tool errors
- Never let exceptions bubble up from MCP tool handlers
- Use custom exception classes for domain errors (e.g., `JesseIntegrationError`)

```python
try:
    from jesse_mcp.core.integrations import get_jesse_wrapper, JESSE_AVAILABLE
except ImportError:
    JESSE_AVAILABLE = False
    get_jesse_wrapper = None
```

### Logging
- Use module-level logger: `logger = logging.getLogger("jesse-mcp.phase3")`
- Log levels: `logger.info()` for operations, `logger.warning()` for fallbacks, `logger.error()` for failures
- Use emoji prefixes in logs: ✅ success, ❌ failure, ⚠️ warning, 🔬 analysis

### Documentation
- Use triple-quote docstrings for classes and public methods
- Include Args, Returns, and Raises sections in docstrings
- Document parameter format in docstrings (e.g., "Format: YYYY-MM-DD")

```python
def backtest(
    self,
    strategy: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """
    Run a backtest using Jesse's research module

    Args:
        strategy: Strategy name (must exist in strategies directory)
        start_date: Start date "YYYY-MM-DD"
        end_date: End date "YYYY-MM-DD"

    Returns:
        Dict with backtest results and metrics

    Raises:
        JesseIntegrationError: If Jesse framework is unavailable
    """
```

## Testing Guidelines

### Test Structure
- Test files: `test_*.py` in `tests/` directory
- Use `pytest` with `pytest-asyncio` for async tests
- Mark async tests with `@pytest.mark.asyncio`
- Use descriptive test names: `test_optimize_with_mock_data`

### Test Patterns
```python
import pytest

@pytest.mark.asyncio
async def test_tool_execution():
    """Test description for debugging"""
    try:
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
    except ImportError:
        pytest.skip("FastMCP not installed")

    transport = StdioTransport(command="python", args=["-m", "jesse_mcp"])
    async with Client(transport) as client:
        result = await client.call_tool("backtest", {...})
        assert isinstance(result, dict)
```

### Test Assertions
- Use descriptive assert messages
- Use `pytest.skip()` for optional dependencies
- Print debug info with `print()` statements (visible with `pytest -s`)

## Jesse 1.13.x REST API Reference

### Authentication Flow

Jesse 1.13.x uses password-based authentication with JWT tokens:

```bash
# Step 1: Login to get session token
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your-jesse-password"}'

# Response: {"token": "session-uuid-here"}

# Step 2: Use token in subsequent requests
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer session-uuid-here" \
  -d @backtest-payload.json
```

### Backtest API Payload Structure

Required fields for backtest endpoint:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "exchange": "Binance",
  "routes": [
    {
      "strategy": "MyStrategy",
      "symbol": "BTC-USDT",
      "timeframe": "1h"
    }
  ],
  "config": {
    "warm_up_candles": 240,
    "logging": {
      "output_type": "json"
    },
    "exchanges": {
      "Binance": {
        "balance": 10000,
        "fee_rate": 0.001
      }
    },
    "reporting": {
      "tradingview": false
    }
  },
  "start_date": "2023-01-01",
  "finish_date": "2024-01-01"
}
```

### Optimization API Payload Structure

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "exchange": "Binance",
  "routes": [
    {
      "strategy": "MyStrategy",
      "symbol": "BTC-USDT",
      "timeframe": "1h"
    }
  ],
  "config": {
    "warm_up_candles": 240,
    "logging": {"output_type": "json"},
    "exchanges": {
      "Binance": {"balance": 10000, "fee_rate": 0.001}
    }
  },
  "start_date": "2023-01-01",
  "finish_date": "2024-01-01",
  "optimize": {
    "strategy_name": "MyStrategy",
    "dna": "default-dna-string",
    "parameters": {
      "rsi_period": [10, 20],
      "tp_rate": [0.01, 0.05]
    }
  }
}
```

### Common Gotchas

1. **`warm_up_candles` placement** - MUST be in `config` object, not at root level:
   ```json
   // ✅ Correct
   {"config": {"warm_up_candles": 240}}

   // ❌ Wrong - will be ignored
   {"warm_up_candles": 240}
   ```

2. **`exchanges` dict requires `balance` field** - Missing balance causes errors:
   ```json
   // ✅ Correct
   "exchanges": {"Binance": {"balance": 10000, "fee_rate": 0.001}}

   // ❌ Wrong - missing balance
   "exchanges": {"Binance": {"fee_rate": 0.001}}
   ```

3. **ID must be valid UUID format** - String must match UUID regex:
   ```python
   import uuid
   backtest_id = str(uuid.uuid4())  # Always use uuid module
   ```

4. **Route timeframe format** - Use hyphen format for pairs:
   ```json
   // ✅ Correct
   {"symbol": "BTC-USDT", "timeframe": "1h"}

   // ❌ Wrong
   {"symbol": "BTCUSDT", "timeframe": "1H"}
   ```

5. **Date format** - Use `YYYY-MM-DD` string format:
   ```json
   // ✅ Correct
   {"start_date": "2023-01-01", "finish_date": "2024-01-01"}

   // ❌ Wrong
   {"start_date": "2023/01/01"}
   ```

6. **Strategy class name** - Must match class name exactly (case-sensitive):
   ```json
   // If class is `MyStrategy`
   {"strategy": "MyStrategy"}  // ✅
   {"strategy": "mystrategy"}  // ❌
   ```

### API Endpoint Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | POST | Authenticate, returns session token |
| `/backtest` | POST | Run single backtest |
| `/backtest/{id}` | GET | Get backtest result/status |
| `/optimize` | POST | Run optimization |
| `/optimize/{id}` | GET | Get optimization result/status |
| `/candles/import` | POST | Import historical candles from exchange |
| `/candles/cancel-import` | POST | Cancel running import process |
| `/candles/existing` | POST | List existing candles with date ranges |
| `/candles/get` | POST | Get candles for exchange/symbol/timeframe |
| `/candles/delete` | POST | Delete candles for exchange/symbol |
| `/candles/clear-cache` | POST | Clear candles database cache |
| `/exchange/supported-symbols` | POST | Get available symbols for exchange |

## Architecture Patterns

### Lazy Initialization
Server module uses lazy initialization to allow testing without Jesse:
```python
jesse = None
_initialized = False

def _initialize_dependencies():
    global jesse, _initialized
    if _initialized:
        return
    # ... initialization logic
    _initialized = True
```

### Singleton Pattern
Use module-level singletons with getter functions:
```python
_optimizer_instance = None

def get_optimizer(use_mock=None) -> Phase3Optimizer:
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = Phase3Optimizer(use_mock=use_mock)
    return _optimizer_instance
```

### MCP Tool Registration
Register tools using FastMCP decorators:
```python
mcp = FastMCP("jesse-mcp", version="1.0.0")

@mcp.tool
def backtest(strategy: str, ...) -> dict:
    """Tool description shown to LLM agents"""
    try:
        # implementation
        return result
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return {"error": str(e), "error_type": type(e).__name__}
```

### Mock Pattern
Tools gracefully fall back to mock implementations:
```python
if not JESSE_AVAILABLE:
    logger.warning("Jesse not available, using mock")
    return self._mock_backtest(...)
```

## Project Structure

```
jesse_mcp/
├── __init__.py          # Package exports
├── __main__.py          # Entry point for python -m
├── server.py            # FastMCP server with 17 tools
├── cli.py               # Command-line interface
├── optimizer.py         # Phase 3: Optimization tools
├── risk_analyzer.py     # Phase 4: Risk analysis tools
├── pairs_analyzer.py    # Phase 5: Pairs trading tools
├── agent_tools.py       # Agent-specific tool extensions
├── core/
│   ├── __init__.py
│   ├── integrations.py  # Jesse framework integration
│   ├── jesse_rest_client.py  # REST API client
│   └── mock.py          # Mock implementations
├── agents/
│   ├── __init__.py
│   ├── base.py          # Base agent class
│   ├── backtester.py    # Backtesting specialist
│   └── risk_manager.py  # Risk management specialist
└── config/
    └── __init__.py      # Configuration management

tests/
├── __init__.py
├── test_server.py       # MCP server tests
├── test_optimizer.py    # Optimization tests
├── test_risk_analyzer.py
└── test_pairs_analyzer.py
```

## Common Development Workflow

For MCP server development workflow, including automatic synchronization to MetaMCP, see: **../MCP_DEVELOPMENT.md**

This includes:
- Git hook + rsync setup for automatic sync
- MetaMCP integration and container restart
- Troubleshooting and maintenance guidelines
- Complete development cycle instructions

## Key Dependencies

- `fastmcp>=0.3.0` - MCP server framework
- `numpy>=1.24.0` - Numerical computations
- `pandas>=2.0.0` - Data manipulation
- `scipy>=1.10.0` - Statistical functions
- `scikit-learn>=1.3.0` - Machine learning utilities
- `optuna>=3.0.0` (optional) - Hyperparameter optimization
- `pydantic>=2.0.0` - Data validation

## Python Version

Requires Python >= 3.10 (uses modern type hint syntax)

## Live Trading (Phase 6)

Jesse MCP now supports live trading via the `jesse-live` plugin. This enables autonomous trading with safety mechanisms.

### Prerequisites

1. **jesse-live plugin** - Must be installed in Jesse container:
   ```bash
   # In Jesse container
   jesse install-live --no-strict
   ```

2. **Exchange API Keys** - Must be configured in Jesse UI before use

3. **LICENSE_API_TOKEN** - Required in Jesse .env file

### MCP Tools

| Tool | Purpose | Mode |
|------|---------|------|
| `live_check_plugin` | Check if jesse-live is available | Safe |
| `live_start_paper_trading` | Start simulated trading | Safe |
| `live_start_live_trading` | Start real money trading | ⚠️ Risky |
| `live_cancel_session` | Stop running session | Safe |
| `live_get_sessions` | List trading sessions | Safe |
| `live_get_status` | Get session status | Safe |
| `live_get_orders` | Get session orders | Safe |
| `live_get_equity_curve` | Get P&L data | Safe |
| `live_get_logs` | Get session logs | Safe |

### Safety Mechanisms

1. **Confirmation Required** - Live trading requires confirmation phrase: `"I UNDERSTAND THE RISKS"`
2. **Agent Permission Levels**:
   - `paper_only` - Can only start paper trading
   - `confirm_required` - Can start live with confirmation
   - `full_autonomous` - Can trade live without confirmation
3. **Risk Limits** (configurable):
   - Max position size: 10% of portfolio
   - Max daily loss: 5%
   - Max drawdown: 15%
4. **Auto-Stop** - Sessions stop automatically on max loss

### Example Usage

```python
# Paper trading (safe)
result = await client.call_tool("live_start_paper_trading", {
    "strategy": "SMACrossover",
    "symbol": "BTC-USDT",
    "timeframe": "1h",
    "exchange": "Binance",
    "exchange_api_key_id": "your-key-id"
})

# Live trading (requires confirmation)
result = await client.call_tool("live_start_live_trading", {
    "strategy": "SMACrossover",
    "symbol": "BTC-USDT",
    "timeframe": "1h",
    "exchange": "Binance",
    "exchange_api_key_id": "your-key-id",
    "confirmation": "I UNDERSTAND THE RISKS",
    "permission": "confirm_required"
})
```

### TradingAgent Class

For programmatic autonomous trading:

```python
from jesse_mcp.agents.live_trader import TradingAgent, get_trading_agent
from jesse_mcp.core.live_config import AgentPermission

# Create agent with paper-only permission
agent = get_trading_agent("paper_only")

# Execute full workflow: backtest → paper trade
result = await agent.execute_strategy_workflow(
    strategy="SMACrossover",
    symbol="BTC-USDT",
    timeframe="1h",
    start_date="2023-01-01",
    end_date="2024-01-01",
    exchange_api_key_id="your-key-id",
)

# Monitor session
async for update in agent.monitor_session(session_id, interval_seconds=60):
    print(f"Status: {update['status']}, Alerts: {update.get('alerts', [])}")
```

### Environment Variables

```bash
JESSE_DEFAULT_PERMISSION=paper_only    # Default agent permission
JESSE_MAX_POSITION_SIZE=0.1            # Max 10% position
JESSE_MAX_DAILY_LOSS=0.05              # Max 5% daily loss
JESSE_MAX_DRAWDOWN=0.15                # Max 15% drawdown
JESSE_REQUIRE_CONFIRMATION=true        # Require confirmation phrase
JESSE_AUTO_STOP_ON_LOSS=true           # Auto-stop on max loss
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
