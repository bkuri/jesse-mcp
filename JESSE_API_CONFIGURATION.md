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
- **Description**: API password for Jesse authentication (NOT the LICENSE_API_TOKEN)
- **Default**: `jessesecurepassword2025` (see Jesse .env PASSWORD variable)
- **Required**: Yes
- **Important**: This is the `PASSWORD` value from Jesse's `.env` file, NOT the `LICENSE_API_TOKEN`
- **Authentication Flow**: 
  1. Client sends POST /auth/login with password from JESSE_API_TOKEN
  2. Jesse returns an auth_token
  3. Client uses auth_token in lowercase `authorization` header for all subsequent requests

## How to Configure in MetaMCP

1. Open MetaMCP panel: https://metamcp.kuri.casa
2. Navigate to "MCP Servers"
3. Find "jesse-mcp" in the list
4. Edit the environment variables:
   - Set `JESSE_URL=http://server2:8000`
   - Set `JESSE_API_TOKEN=<PASSWORD_from_jesse_.env_file>`
     - On server2, check: `cat /home/jesse/jesse-trading/.env | grep "^PASSWORD="`
     - Default: `jessesecurepassword2025`
5. Save and restart the container

**Note**: The token you provide is the PASSWORD, not the LICENSE_API_TOKEN. The client will automatically:
1. Login to Jesse using this password
2. Obtain a session token
3. Use the session token for all subsequent API calls

## Verifying Configuration

Once configured in MetaMCP, the jesse-mcp client will automatically:
1. Authenticate with Jesse using the PASSWORD
2. Obtain a session token
3. Use that token for all API operations

To manually test the authentication:

```bash
# Step 1: Login to get an auth token
AUTH_TOKEN=$(curl -s -X POST http://server2:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password": "jessesecurepassword2025"}' | jq -r '.auth_token')

# Step 2: Use the auth token in API calls (note lowercase 'authorization')
curl -s -X POST http://server2:8000/backtest \
  -H "authorization: $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...backtest_payload...}'
```

## Jesse API Authentication Details

Jesse uses a two-step authentication process:
1. **Login**: POST `/auth/login` with `{"password": "..."}` returns `{"auth_token": "..."}`
2. **API Calls**: Include token in lowercase `authorization:` header (no "Bearer" prefix)

Example:
```
authorization: c8f16e7c14bd480cd46982b58595c478ea099ec617fd813bd234133d9796b4a3
```

## Current Status

- Jesse service running on server2: ✅
- API endpoint accessible: ✅
- Authentication: ✅ (Working with correct PASSWORD)
- jesse-mcp REST client: ✅ (Automatically handles login and token management)

## Troubleshooting

If you see `"Invalid password"` errors:
1. Verify `JESSE_API_TOKEN` is set to the PASSWORD from Jesse's `.env` file
2. On server2, check: `sudo cat /home/jesse/jesse-trading/.env | grep "^PASSWORD="`
3. Update MetaMCP jesse-mcp environment variables with correct PASSWORD
4. Restart the jesse-mcp container

If you see connection errors:
1. Verify Jesse service is running: `ssh server2 "sudo systemctl status jesse.service"`
2. Verify network connectivity: `curl -s http://server2:8000/ | head -10`
3. Check firewall rules allow traffic on port 8000
