"""
Jesse MCP Server

An MCP (Model Context Protocol) server providing 17 advanced quantitative
trading analysis tools:
- Optimization tools for strategy parameter tuning
- Risk analysis tools for portfolio and trade risk assessment
- Pairs trading tools for statistical arbitrage and regime analysis
- Backtesting and data analysis tools
"""

__version__ = "1.0.0"
__author__ = "Jesse Team"
__all__ = ["main"]

from jesse_mcp.server import main
