#!/bin/bash
# Start jesse-mcp development server for opencode integration
# Usage: ./scripts/start-dev-server.sh

set -e

# Configuration
PORT=${JESSE_MCP_PORT:-8100}
JESSE_URL=${JESSE_URL:-http://server2:9100}
JESSE_PASSWORD=${JESSE_PASSWORD:-test}
LOG_FILE=/tmp/jesse-mcp-dev.log

# Kill existing server if running
pkill -f "jesse_mcp.*--transport http.*--port $PORT" 2>/dev/null || true
sleep 1

# Start server
echo "Starting jesse-mcp dev server on port $PORT..."
cd /home/bk/source/jesse-mcp
JESSE_URL=$JESSE_URL JESSE_PASSWORD=$JESSE_PASSWORD \
    nohup python -m jesse_mcp --transport http --port $PORT > "$LOG_FILE" 2>&1 &

sleep 2

# Verify server started
if curl -s http://localhost:$PORT/mcp -H "Accept: application/json, text/event-stream" 2>/dev/null | grep -q "session"; then
    echo "✅ jesse-mcp dev server running on http://localhost:$PORT/mcp"
    echo "   Logs: $LOG_FILE"
    echo "   PID: $(pgrep -f 'jesse_mcp.*http.*$PORT')"
else
    echo "❌ Server failed to start. Check logs: $LOG_FILE"
    exit 1
fi
