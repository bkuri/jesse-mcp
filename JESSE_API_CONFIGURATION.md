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

### 2. Authentication (Choose ONE of the following)

#### Option A: `JESSE_PASSWORD` (Recommended for simple setups)
- **Description**: Your Jesse UI login password
- **How to use**: 
  1. Set `JESSE_PASSWORD=<your_jesse_ui_password>`
  2. Don't set `JESSE_API_TOKEN`
- **Authentication Flow**: 
  1. Client sends POST /auth/login with password
  2. Jesse returns an auth_token
  3. Client uses auth_token for all API calls
- **Advantage**: Simple, uses your existing Jesse login credentials

#### Option B: `JESSE_API_TOKEN` (For programmatic access)
- **Description**: Pre-generated API token from Jesse UI
- **How to generate**: In Jesse UI → Settings/Admin → API Tokens → Generate New Token
- **How to use**:
  1. Set `JESSE_API_TOKEN=<generated_token>`
  2. Don't set `JESSE_PASSWORD`
- **Authentication Flow**: Token is used directly in API calls
- **Advantage**: No need to store/transmit UI password, token can be revoked separately

## How to Configure in MetaMCP

1. Open MetaMCP panel: https://metamcp.kuri.casa
2. Navigate to "MCP Servers"
3. Find "jesse-mcp" in the list
4. Edit the environment variables:
   - Set `JESSE_URL=http://server2:8000`
   - Choose authentication method:
     - **Method A (Simple)**: Set `JESSE_PASSWORD=<your_jesse_ui_password>`
     - **Method B (Token)**: Set `JESSE_API_TOKEN=<generated_token_from_jesse_ui>`
5. Save and restart the container

**Example Configuration (Method A - Password)**:
```
JESSE_URL=http://server2:8000
JESSE_PASSWORD=jessesecurepassword2025
```

**Example Configuration (Method B - API Token)**:
```
JESSE_URL=http://server2:8000
JESSE_API_TOKEN=abc123xyz789...
```

The client will automatically:
1. Authenticate using your chosen method
2. Obtain/use an auth token
3. Use the auth token for all subsequent API calls

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

### "Invalid password" errors
**If using JESSE_PASSWORD**:
1. Verify the password is correct (same as Jesse UI login password)
2. Check that the password doesn't have special characters that need escaping
3. Restart the jesse-mcp container after changing the password

**If using JESSE_API_TOKEN**:
1. Verify the token is correctly generated in Jesse UI (Settings → API Tokens)
2. Check that the full token is copied (may be very long)
3. Verify the token hasn't been revoked
4. Regenerate a new token if issues persist

### "No JESSE_PASSWORD or JESSE_API_TOKEN provided" warnings
1. Ensure at least ONE of JESSE_PASSWORD or JESSE_API_TOKEN is set in MetaMCP
2. Check MetaMCP environment variables are saved correctly
3. Restart the jesse-mcp container

### Connection errors
1. Verify Jesse service is running: `ssh server2 "sudo systemctl status jesse.service"`
2. Verify network connectivity: `curl -s http://server2:8000/ | head -10`
3. Check firewall rules allow traffic on port 8000
4. Verify `JESSE_URL` is set correctly in MetaMCP

### How to generate a new API token
1. Go to Jesse UI: http://server2:8000
2. Login with your credentials
3. Navigate to: Settings/Admin → API Tokens
4. Click "Generate New Token"
5. Copy the full token value
6. Set `JESSE_API_TOKEN=<copied_token>` in MetaMCP jesse-mcp environment
7. Restart the container
