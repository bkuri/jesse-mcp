"""Specialized agents for Jesse trading platform.

These agents provide domain-specific intelligence on top of the MCP server,
using optimized system prompts and multi-turn conversation capabilities.
"""


# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy load agent classes."""
    if name == "BaseJesseAgent":
        from jesse_mcp.agents.base import BaseJesseAgent

        return BaseJesseAgent
    elif name == "StrategyOptimizationAgent":
        from jesse_mcp.agents.strategy_optimizer import StrategyOptimizationAgent

        return StrategyOptimizationAgent
    elif name == "RiskManagementAgent":
        from jesse_mcp.agents.risk_manager import RiskManagementAgent

        return RiskManagementAgent
    elif name == "BacktestingAgent":
        from jesse_mcp.agents.backtester import BacktestingAgent

        return BacktestingAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseJesseAgent",
    "StrategyOptimizationAgent",
    "RiskManagementAgent",
    "BacktestingAgent",
]
