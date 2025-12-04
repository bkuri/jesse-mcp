#!/usr/bin/env python3
"""
Jesse MCP Server - CLI entry point

Usage:
    jesse-mcp                    # Start the server
    jesse-mcp --help             # Show help
    jesse-mcp --version          # Show version
"""

import argparse
import sys
from jesse_mcp.server import JesseMCPServer


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Jesse MCP Server - Quantitative Trading Analysis"
    )
    parser.add_argument("--version", action="version", version="jesse-mcp 1.0.0")

    args = parser.parse_args()

    # Create and run server
    server = JesseMCPServer()

    # Run the async server
    import asyncio

    asyncio.run(server.run())


if __name__ == "__main__":
    sys.exit(main())
