#!/bin/bash
# Stop jesse-mcp development server
# Usage: ./scripts/stop-dev-server.sh

PORT=${JESSE_MCP_PORT:-8100}

echo "Stopping jesse-mcp dev server on port $PORT..."
pkill -f "jesse_mcp.*--transport http.*--port $PORT" 2>/dev/null && \
    echo "✅ Server stopped" || \
    echo "⚠️  No server found on port $PORT"
