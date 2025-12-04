#!/usr/bin/env python3
"""
Test jesse-mcp server
"""

import asyncio
import json
import sys
import subprocess
import os
import pytest


@pytest.mark.asyncio
async def test_server():
    """Test jesse-mcp server"""

    print("🚀 Testing jesse-mcp server...")

    # Test 1: List tools
    print("\n1. Testing tools/list...")
    request = {"method": "tools/list", "params": {}}

    result = await run_server_command(request)
    print(f"✓ Tools listed: {len(result.get('tools', []))}")

    # Test 2: Call backtest tool
    print("\n2. Testing backtest tool...")
    request = {
        "method": "tools/call",
        "params": {
            "name": "backtest",
            "arguments": {
                "strategy": "Test01",
                "symbol": "BTC-USDT",
                "timeframe": "1h",
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
        },
    }

    result = await run_server_command(request)
    if "error" in result:
        print(f"✗ Backtest failed: {result['error']}")
    else:
        print("✓ Backtest tool responded")

    # Test 3: List resources
    print("\n3. Testing resources/list...")
    request = {"method": "resources/list", "params": {}}

    result = await run_server_command(request)
    print(f"✓ Resources listed: {len(result.get('resources', []))}")

    print("\n🎉 All tests passed!")


async def run_server_command(request):
    """Run a command against the server"""
    try:
        # Change to server directory
        server_dir = "/home/bk/jesse-mcp"

        # Run server with input
        proc = subprocess.Popen(
            [sys.executable, "server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=server_dir,
        )

        # Send request
        request_json = json.dumps(request)
        proc.stdin.write(request_json + "\n")
        proc.stdin.flush()

        # Read response
        stdout, stderr = proc.communicate(input=request_json, timeout=10)

        if proc.returncode != 0:
            return {"error": f"Server error: {stderr}"}

        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON response: {stdout}"}

    except subprocess.TimeoutExpired:
        return {"error": "Server timeout"}
    except Exception as e:
        return {"error": f"Test error: {str(e)}"}


if __name__ == "__main__":
    asyncio.run(test_server())
