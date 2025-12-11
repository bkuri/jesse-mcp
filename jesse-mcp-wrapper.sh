#!/bin/bash
# Wrapper script to run jesse-mcp with proper PYTHONPATH
# Avoids issues with venv's bundled Python executable

# Ensure PYTHONPATH includes jesse-mcp directory
export PYTHONPATH="/mnt/jesse-mcp:/mnt/autocli:${PYTHONPATH}"

# Use system Python directly (avoids venv Python executable issues)
exec /usr/bin/python3 -m jesse_mcp "$@"
