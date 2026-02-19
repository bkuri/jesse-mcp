"""
Jesse MCP Server

An MCP (Model Context Protocol) server providing 26+ quantitative trading tools:
- Phase 1: Backtesting and strategy validation
- Phase 3: Optimization tools for strategy parameter tuning
- Phase 4: Risk analysis tools for portfolio and trade risk assessment
- Phase 5: Pairs trading tools for statistical arbitrage and regime analysis
- Phase 6: Live trading with paper/live mode support and safety mechanisms
"""

__version__ = "1.1.0"
__author__ = "Bernardo Kuri"
__all__ = ["main"]

from jesse_mcp.server import main
