"""Base agent class for Jesse trading platform specialists."""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseJesseAgent:
    """Base class for specialized Jesse trading agents.

    Each agent provides domain expertise through optimized system prompts
    and multi-turn conversation capabilities with the MCP tools.
    """

    def __init__(self, mcp_host: str = "localhost", mcp_port: int = 5000):
        """Initialize the agent.

        Args:
            mcp_host: MCP server host
            mcp_port: MCP server port
        """
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port
        self.conversation_history: list[Dict[str, str]] = []
        self.agent_name = self.__class__.__name__

    @property
    def system_prompt(self) -> str:
        """Return the specialized system prompt for this agent.

        Should be overridden by subclasses to provide domain expertise.
        """
        return (
            f"You are a specialized {self.agent_name} for the Jesse trading platform. "
            "Your role is to provide expert analysis and recommendations for trading strategies."
        )

    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history.

        Args:
            role: Either 'user' or 'assistant'
            content: The message content
        """
        self.conversation_history.append({"role": role, "content": content})

    def get_history(self) -> list[Dict[str, str]]:
        """Get the full conversation history.

        Returns:
            List of conversation messages
        """
        return self.conversation_history.copy()

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []

    def format_context(self, data: Dict[str, Any]) -> str:
        """Format analysis data into readable context.

        Args:
            data: Dictionary of analysis results

        Returns:
            Formatted string representation
        """
        if not data:
            return "No data available."

        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"\n{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """String representation of the agent."""
        return (
            f"{self.__class__.__name__}(host={self.mcp_host}, "
            f"port={self.mcp_port}, history_size={len(self.conversation_history)})"
        )
