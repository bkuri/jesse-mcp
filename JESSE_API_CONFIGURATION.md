# Jesse MCP API Configuration Guide

## Overview

The jesse-mcp server connects to the Jesse trading platform via its REST API running on **server2**. Configuration is done through the MetaMCP web panel, not through files.

## Required Environment Variables

Configure these in the MetaMCP MCP Servers panel for jesse-mcp:

### 1. `JESSE_URL`
- **Description**: Base URL of the Jesse API
- **Default**: `http://server2:8000`
- **Example**: `http://server2:8000`
- **Required**: Yes

### 2. `JESSE_API_TOKEN`
- **Description**: API authentication token/password for Jesse
- **Value**: The password configured in Jesse API
- **Required**: Yes
- **Note**: This is used as the Bearer token in the `Authorization: Bearer` header

## How to Configure in MetaMCP

1. Open MetaMCP panel: https://metamcp.kuri.casa
2. Navigate to "MCP Servers"
3. Find "jesse-mcp" in the list
4. Edit the environment variables:
   - Add `JESSE_URL=http://server2:8000`
   - Add `JESSE_API_TOKEN=<actual_token_from_jesse>`
5. Save and restart the container

## Verifying Configuration

Once configured, test the connection:

```bash
# Check if environment variables are set
env | grep JESSE_

# Test the Jesse API directly
curl -H "Authorization: Bearer <JESSE_API_TOKEN>" http://server2:8000/

# Test backtest endpoint
curl -X POST http://server2:8000/backtest \
  -H "Authorization: Bearer <JESSE_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{...backtest_payload...}'
```

## Jesse API Authentication

Jesse requires Bearer token authentication. The token is passed as:
```
Authorization: Bearer <JESSE_API_TOKEN>
```

## Current Status

- Jesse service running on server2: ✅
- API endpoint accessible: ✅
- Authentication: ⚠️ (Requires correct token from MetaMCP configuration)

## Troubleshooting

If you see `401 Unauthorized` errors:
1. Verify `JESSE_API_TOKEN` is correctly set in MetaMCP
2. Check that the token matches the password configured in Jesse
3. Verify `JESSE_URL` points to server2 and port 8000 is accessible

If you see `Invalid password` errors:
1. The token value is incorrect
2. Contact the system administrator for the correct token value
3. Check Jesse service logs on server2 for authentication issues
