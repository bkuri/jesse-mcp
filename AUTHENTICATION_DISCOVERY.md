# Jesse API Authentication Discovery

## Key Finding

Jesse API requires a **two-step authentication process**, not Bearer token authentication as initially assumed.

### Actual Authentication Flow

1. **Step 1: Login**
   ```bash
   POST /auth/login
   Body: {"password": "..."}
   Response: {"auth_token": "c8f16e7c14bd480cd46982b58595c478ea099ec617fd813bd234133d9796b4a3"}
   ```

2. **Step 2: API Calls**
   ```bash
   POST /backtest (or any API endpoint)
   Header: authorization: c8f16e7c14bd480cd46982b58595c478ea099ec617fd813bd234133d9796b4a3
   ```

**Important**: The `authorization` header must be:
- Lowercase (not `Authorization`)
- Without the "Bearer " prefix
- Just the raw auth_token value

## Configuration Parameters

The `JESSE_API_TOKEN` environment variable should contain:
- **VALUE**: The `PASSWORD` from Jesse's `.env` file
- **NOT**: The `LICENSE_API_TOKEN` (which is for jesse.trade service)
- **Current Value**: `jessesecurepassword2025` (on server2)

## Token Provided

The token `X8Ge4gij2mWEuNAeS4MeWvModtPqLPoStC0nXI5c3c5aa3ec` does not work with the `/auth/login` endpoint.

**Possible Explanations**:
1. It's an old/outdated token
2. It's a different authentication mechanism (LICENSE_API_TOKEN for jesse.trade)
3. It's the wrong format or needs updating in MetaMCP

**Recommendation**: Verify the current password in MetaMCP matches Jesse's `.env` PASSWORD field, or update MetaMCP with `jessesecurepassword2025`.

## Jesse REST Client Implementation

The `JesseRESTClient` has been updated to:
1. Automatically authenticate on initialization
2. Handle the two-step login flow internally
3. Manage auth tokens transparently
4. Use lowercase `authorization` headers in all requests

## Status

- ✅ Authentication flow discovered and implemented
- ✅ Manual backtest call successful with correct password
- ⚠️ MetaMCP environment variable needs verification
- ⏳ Full MCP tool testing pending
