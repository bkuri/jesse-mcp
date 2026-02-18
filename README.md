# Jesse MCP Server

[![PyPI version](https://badge.fury.io/py/jesse-mcp.svg)](https://badge.fury.io/py/jesse-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An MCP (Model Context Protocol) server that exposes Jesse's algorithmic trading framework capabilities to LLM agents.

## Status: Feature Complete ✅

All planned features implemented and tested. 32 tools available (17 core + 15 agent).

## Installation

### PyPI

```bash
pip install jesse-mcp
```

### uvx (recommended for running directly)

```bash
uvx jesse-mcp
```

### Arch Linux (AUR)

```bash
yay -S jesse-mcp
# or
paru -S jesse-mcp
```

### From Source

```bash
git clone https://github.com/bkuri/jesse-mcp.git
cd jesse-mcp
pip install -e .
```

## Usage

```bash
# stdio transport (default, for MCP clients)
jesse-mcp

# HTTP transport (for remote access)
jesse-mcp --transport http --port 8100

# Show help
jesse-mcp --help
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JESSE_URL` | Jesse REST API URL | `http://localhost:9000` |
| `JESSE_PASSWORD` | Jesse UI password | (required) |
| `JESSE_API_TOKEN` | Pre-generated API token | (alternative to password) |

## Features

- **Backtesting** - Single and batch backtest execution via Jesse REST API
- **Optimization** - Hyperparameter tuning with walk-forward validation  
- **Monte Carlo Analysis** - Statistical robustness testing
- **Pairs Trading** - Cointegration testing and strategy generation
- **Strategy Management** - CRUD operations for trading strategies
- **Risk Analysis** - VaR, stress testing, comprehensive risk reports
- **Agent Tools** - 15 specialized tools for autonomous trading workflows

## Architecture

```
LLM Agent ←→ MCP Protocol ←→ jesse-mcp ←→ Jesse REST API (localhost:9000)
                                    ↓
                            Mock Fallbacks (when Jesse unavailable)
```

## Available Tools (32 Total)

### Core Tools (17)

#### Phase 1: Backtesting
| Tool | Description |
|------|-------------|
| `backtest` | Run single backtest with specified parameters |
| `strategy_list` | List available strategies |
| `strategy_read` | Read strategy source code |
| `strategy_validate` | Validate strategy code |

#### Phase 2: Data & Analysis
| Tool | Description |
|------|-------------|
| `candles_import` | Download candle data from exchanges |
| `backtest_batch` | Run concurrent multi-asset backtests |
| `analyze_results` | Extract insights from backtest results |
| `walk_forward` | Walk-forward analysis for overfitting detection |

#### Phase 3: Optimization
| Tool | Description |
|------|-------------|
| `optimize` | Optimize hyperparameters using Optuna |

#### Phase 4: Risk Analysis
| Tool | Description |
|------|-------------|
| `monte_carlo` | Monte Carlo simulations for risk analysis |
| `var_calculation` | Value at Risk (historical, parametric, Monte Carlo) |
| `stress_test` | Test under extreme market scenarios |
| `risk_report` | Comprehensive risk assessment |

#### Phase 5: Pairs Trading
| Tool | Description |
|------|-------------|
| `correlation_matrix` | Cross-asset correlation analysis |
| `pairs_backtest` | Backtest pairs trading strategies |
| `factor_analysis` | Decompose returns into systematic factors |
| `regime_detector` | Identify market regimes and transitions |

### Agent Tools (15)

Specialized tools for autonomous trading workflows:

| Tool | Description |
|------|-------------|
| `strategy_suggest_improvements` | AI-powered strategy enhancement suggestions |
| `strategy_compare_strategies` | Compare multiple strategies side-by-side |
| `strategy_optimize_pair_selection` | Optimize pairs trading selection |
| `strategy_analyze_optimization_impact` | Analyze impact of optimization changes |
| `risk_analyze_portfolio` | Portfolio-level risk analysis |
| `risk_stress_test` | Advanced stress testing |
| `risk_assess_leverage` | Leverage risk assessment |
| `risk_recommend_hedges` | Hedging recommendations |
| `risk_analyze_drawdown_recovery` | Drawdown recovery analysis |
| `backtest_comprehensive` | Full backtest with all metrics |
| `backtest_compare_timeframes` | Compare performance across timeframes |
| `backtest_optimize_parameters` | Quick parameter optimization |
| `backtest_monte_carlo` | Backtest with Monte Carlo analysis |
| `backtest_analyze_regimes` | Regime-aware backtest analysis |
| `backtest_validate_significance` | Statistical significance validation |

## Testing

```bash
# Install dev dependencies
pip install jesse-mcp[dev]

# Run all tests
pytest -v

# Run with coverage
pytest --cov=jesse_mcp
```

**Status:** 49 tests passing

## Local Development

### Prerequisites
- Python 3.10+
- Jesse 1.13.x running on localhost:9000
- PostgreSQL on localhost:5432
- Redis on localhost:6379

### Start Jesse Stack (Podman)
```bash
# Start infrastructure
podman run -d --name jesse-postgres --network host \
  -e POSTGRES_USER=jesse_user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=jesse_db \
  docker.io/library/postgres:14-alpine

podman run -d --name jesse-redis --network host \
  docker.io/library/redis:6-alpine redis-server --save "" --appendonly no

# Start Jesse
podman run -d --name jesse --network host \
  -v /path/to/jesse-bot:/home:z \
  docker.io/salehmir/jesse:latest bash -c "cd /home && jesse run"
```

### Start Dev MCP Server
```bash
./scripts/start-dev-server.sh   # Start on port 8100
./scripts/stop-dev-server.sh    # Stop server
```

### Add to OpenCode
Add to `~/.config/opencode/opencode.json`:
```json
{
  "mcp": {
    "jesse-mcp-dev": {
      "type": "remote",
      "url": "http://localhost:8100/mcp",
      "enabled": true
    }
  }
}
```

## Documentation

- [Using with LLMs](docs/USING_WITH_LLMS.md) - How to use with MCP-compatible LLMs
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md) - Production deployment guide
- [Jesse Setup](docs/JESSE_SETUP.md) - Jesse integration setup
- [Agent System](docs/AGENT_SYSTEM.md) - Agent architecture
- [AGENTS.md](AGENTS.md) - Development guidelines for AI agents

## API Reference

### Jesse REST Client

The `jesse_rest_client.py` module provides direct access to Jesse's REST API:

```python
from jesse_mcp.core.jesse_rest_client import get_jesse_rest_client

client = get_jesse_rest_client()

# Run backtest
result = client.backtest(
    strategy="OctopusStrategy",
    symbol="BTC-USDT", 
    timeframe="1h",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### Mock Implementations

When Jesse is unavailable, all tools gracefully fall back to mock implementations that return realistic synthetic data. This enables development and testing without a full Jesse installation.

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastmcp | >=0.3.0 | MCP server framework |
| numpy | >=1.24.0 | Numerical computations |
| pandas | >=2.0.0 | Data manipulation |
| scipy | >=1.10.0 | Statistical functions |
| scikit-learn | >=1.3.0 | ML utilities |
| optuna | >=3.0.0 | Hyperparameter optimization |

## Project Structure

```
jesse_mcp/
├── server.py            # FastMCP server with 17 core tools
├── optimizer.py         # Phase 3: Optimization tools
├── risk_analyzer.py     # Phase 4: Risk analysis tools
├── pairs_analyzer.py    # Phase 5: Pairs trading tools
├── agent_tools.py       # 15 agent-specific tools
├── core/
│   ├── integrations.py  # Jesse framework integration
│   ├── jesse_rest_client.py  # REST API client
│   └── mock.py          # Mock implementations
├── agents/
│   ├── base.py          # Base agent class
│   ├── backtester.py    # Backtesting specialist
│   └── risk_manager.py  # Risk management specialist
└── scripts/
    ├── start-dev-server.sh
    └── stop-dev-server.sh
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Publishing

This package uses GitHub Actions with PyPI trusted publishing. To release a new version:

1. Update version in `pyproject.toml` and `jesse_mcp/__init__.py`
2. Create a git tag: `git tag v1.x.x`
3. Push tag: `git push origin v1.x.x`
4. Create GitHub release - automatically publishes to PyPI
