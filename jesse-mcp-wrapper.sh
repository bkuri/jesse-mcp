#!/bin/bash
# Wrapper script to run jesse-mcp with proper PYTHONPATH and dependencies

# Add venv's site-packages to PYTHONPATH so dependencies are available
export PYTHONPATH="/mnt/jesse-mcp/.venv/lib/python3.13/site-packages:/mnt/jesse-mcp:/mnt/autocli:${PYTHONPATH}"

# Use venv's Python directly which has all dependencies installed
exec /mnt/jesse-mcp/.venv/bin/python3 -m jesse_mcp "$@"
