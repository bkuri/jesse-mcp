# Jesse MCP Server

An MCP (Model Context Protocol) server that exposes Jesse's algorithmic trading framework capabilities to LLM agents.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
```

## Features

- **Backtesting** - Single and batch backtest execution
- **Optimization** - Hyperparameter tuning with walk-forward validation  
- **Monte Carlo Analysis** - Statistical robustness testing
- **Pairs Trading** - Cointegration testing and strategy generation
- **Strategy Management** - CRUD operations for trading strategies
- **Data Management** - Candle import and availability checking

## Documentation

See [PRD](jesse_mcp_server.md) for complete specifications.

## Architecture

```
LLM Agent ←→ MCP Protocol ←→ jesse-mcp ←→ Jesse Research Module
```

## Development

Based on the PRD, implementation phases:

- **Phase 1**: Core Foundation (backtest, strategy tools)
- **Phase 2**: Optimization (hyperparameter tuning)
- **Phase 3**: Data Management (candle operations)
- **Phase 4**: Analysis & Intelligence (metrics, indicators)
- **Phase 5**: Monte Carlo & Statistical Analysis
- **Phase 6**: Pairs Trading
- **Phase 7**: Autonomous Workflows
- **Phase 8**: Polish & Documentation

## License

MIT