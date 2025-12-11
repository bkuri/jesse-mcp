#!/bin/bash
# Wrapper script to run jesse-mcp with proper PYTHONPATH
# Uses container's Python but loads dependencies from venv

# Add venv's site-packages to PYTHONPATH so dependencies are available
export PYTHONPATH="/mnt/jesse-mcp/.venv/lib/python3.13/site-packages:/mnt/jesse-mcp:/mnt/autocli:${PYTHONPATH}"

# Use system Python but with venv's site-packages in path
exec python3 -m jesse_mcp "$@"
