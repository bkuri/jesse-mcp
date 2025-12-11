#!/usr/bin/env python3
"""
Jesse MCP Server - CLI entry point

Usage:
    jesse-mcp                                   # Start with stdio transport
    jesse-mcp --transport http --port 8000     # Start with HTTP transport
    jesse-mcp --version                        # Show version
    jesse-mcp --help                           # Show help
"""

import sys


def main():
    """Main entry point for CLI"""
    try:
        from jesse_mcp.server import main as server_main

        server_main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
