"""
Jesse MCP Server

An MCP (Model Context Protocol) server providing 17 advanced quantitative
trading analysis tools organized across 5 phases.

Phases:
- Phase 1: Backtesting Fundamentals (4 tools)
- Phase 2: Data & Analysis (5 tools)
- Phase 3: Advanced Optimization (4 tools)
- Phase 4: Risk Analysis (4 tools)
- Phase 5: Pairs Trading & Regime Analysis (4 tools)
"""

__version__ = "1.0.0"
__author__ = "Jesse Team"
__all__ = ["JesseMCPServer"]

from jesse_mcp.server import JesseMCPServer
