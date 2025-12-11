#!/bin/bash
# Wrapper script to run jesse-mcp with proper venv activation
# This ensures all dependencies (including fastmcp) are available

# Check if running in MetaMCP container
if [ -d "/mnt/jesse-mcp/.venv" ]; then
    # Use venv from mounted volume
    source /mnt/jesse-mcp/.venv/bin/activate
    exec python3 -m jesse_mcp "$@"
elif [ -d ".venv" ]; then
    # Use local venv
    source .venv/bin/activate
    exec python3 -m jesse_mcp "$@"
else
    # Fall back to system python
    exec python3 -m jesse_mcp "$@"
fi
