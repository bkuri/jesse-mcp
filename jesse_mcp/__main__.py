#!/usr/bin/env python3
"""
Jesse MCP Server - Entry point for running as module

Usage:
    python -m jesse_mcp
"""

import sys
from jesse_mcp.cli import main

if __name__ == "__main__":
    sys.exit(main())
