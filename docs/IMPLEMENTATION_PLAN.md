# Jesse MCP Server Refactoring: Implementation Plan

**Objective**: Transform the MCP server from local direct imports to HTTP-based remote communication with Jesse.

**Status**: Planning Phase ✓ | Implementation Pending

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Phase-by-Phase Breakdown](#phase-by-phase-breakdown)
4. [Dependencies and Build Order](#dependencies-and-build-order)
5. [Testing Strategy](#testing-strategy)
6. [Deployment and Rollout](#deployment-and-rollout)
7. [Risk Management](#risk-management)
8. [Appendix](#appendix)

---

## Executive Summary

### Current State Issues
- ❌ Hardcoded filesystem paths to Jesse (`/srv/containers/jesse`, `/mnt/nfs/server1/containers/jesse`)
- ❌ Direct Python imports - requires Jesse to be installed locally
- ❌ Not containerization-friendly
- ❌ Cannot run with remote Jesse instances
- ❌ No configuration system - all defaults hardcoded

### Target State
- ✅ Environment variable configuration (`JESSE_URL`, `JESSE_API_TOKEN`)
- ✅ HTTP-based communication with Jesse API
- ✅ Deployment-agnostic (works with Jesse anywhere)
- ✅ Docker/container-friendly
- ✅ Scales horizontally (multiple MCP servers → single Jesse)
- ✅ Clean separation of concerns

### Timeline Estimate
- **Total Duration**: 3-4 weeks
- **Phase 1**: 2-3 days (Config layer)
- **Phase 2**: 3-4 days (HTTP client)
- **Phase 3**: 2-3 days (Integration refactor)
- **Phase 4**: 1-2 days (Server startup)
- **Phase 5**: 1 day (CLI enhancement)
- **Phase 6**: 3-4 days (Testing)
- **Phase 7**: 2-3 days (Documentation)
- **Phase 8**: 2-3 days (Integration testing + fixes)

### Success Criteria
1. MCP server connects to remote Jesse via environment variables
2. All existing MCP tools work identically to before
3. Docker deployment works with env vars only
4. Clear error messages for configuration/connection issues
5. All tests pass (unit + integration)
6. No local filesystem assumptions
7. Backward compatible with current tool definitions

---

## Architecture Overview

### Environment Variables

```bash
# REQUIRED
JESSE_URL="http://localhost:5000"
JESSE_API_TOKEN="<sha256_hash_of_password>"

# OPTIONAL
JESSE_LOG_LEVEL="INFO"              # DEBUG, INFO, WARNING, ERROR
JESSE_JSON_INDENT="2"               # 0-4 for JSON formatting
JESSE_CONNECT_TIMEOUT="30"          # seconds
JESSE_REQUEST_TIMEOUT="300"         # seconds (for long operations)
```

### Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    MCP Client (Claude)                        │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ MCP Protocol (stdin/stdout)
             │
┌────────────▼─────────────────────────────────────────────────┐
│                  jesse-mcp Server (NEW)                       │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │            JesseMCPServer (unchanged)                  │  │
│  │  - Handles MCP protocol                              │  │
│  │  - Routes tool calls                                 │  │
│  │  - Returns results                                   │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │ uses                                 │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │        JesseWrapper (REFACTORED)                     │  │
│  │  - Keeps existing interface                         │  │
│  │  - Now uses HTTP client internally                  │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │ uses                                 │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │     JesseHTTPClient (NEW)                            │  │
│  │  - HTTP requests to Jesse API                       │  │
│  │  - Authentication handling                         │  │
│  │  - Polling for async operations                    │  │
│  │  - Error handling & retries                        │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │ uses                                 │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │     JesseConfig (NEW)                                │  │
│  │  - Loads env vars                                   │  │
│  │  - Validates configuration                         │  │
│  │  - Provides defaults                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                                │
└────────────┬─────────────────────────────────────────────────┘
             │ HTTP + Auth Header
             │
┌────────────▼─────────────────────────────────────────────────┐
│               Jesse API Server (EXISTING)                     │
│          (Accessed via JESSE_URL from env var)               │
└──────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

#### 1. Async Operations Handling
Jesse API returns 202 (Accepted) for long-running operations. Options:

| Option | Pros | Cons |
|--------|------|------|
| **Block & Poll** ✓ CHOSEN | Simple, predictable for LLM | May timeout on very long ops |
| Async/Job ID | Non-blocking | Requires UI changes, complex state management |
| WebSocket | Real-time updates | Complex, requires persistent connection |

**Decision**: Block & poll with configurable timeout. Simple and predictable for LLM integration.

#### 2. Authentication
Jesse uses SHA256 hash of password as token.

```python
# Option 1: Store hash directly (secure)
JESSE_API_TOKEN="<sha256_hash>"  # Use as-is in Authorization header

# Option 2: Store password and compute hash (more user-friendly)
JESSE_PASSWORD="<password>"      # Compute hash internally
```

**Decision**: Option 1 - Token stored directly. Allows users to generate hash themselves.

#### 3. Error Handling Strategy

| Status | Handling |
|--------|----------|
| 401 Unauthorized | Clear message: "Invalid JESSE_API_TOKEN" |
| 404 Not Found | "Jesse API endpoint not found - version mismatch?" |
| 500 Server Error | "Jesse server error - check Jesse logs" |
| Connection refused | "Cannot connect to JESSE_URL - is Jesse running?" |
| Timeout | "Operation took too long - increase JESSE_REQUEST_TIMEOUT" |

#### 4. Polling Strategy
- Use session IDs from async endpoint responses
- Poll `/backtest/sessions`, `/optimization/sessions`, etc.
- Exponential backoff: 0.1s → 0.2s → 0.5s → 1s → 5s (max)
- Respect `JESSE_REQUEST_TIMEOUT` for total operation time

---

## Phase-by-Phase Breakdown

### Phase 1: Configuration Layer (2-3 days)

**Objective**: Create environment variable loading and validation system.

**Files to Create**:
- `jesse_mcp/core/config.py` (NEW)

**Files to Modify**:
- `pyproject.toml` (add pydantic if not already present)
- `requirements.txt` (add pydantic if not already present)

#### Implementation Steps

##### Step 1.1: Create config.py

```python
# jesse_mcp/core/config.py
from typing import Optional
from pydantic import BaseSettings, AnyHttpUrl, validator
import logging

logger = logging.getLogger("jesse-mcp.config")

class JesseConfig(BaseSettings):
    """Configuration for Jesse MCP Server from environment variables."""
    
    # Required fields
    url: AnyHttpUrl  # JESSE_URL - e.g., http://localhost:5000
    api_token: str   # JESSE_API_TOKEN - SHA256 hash
    
    # Optional fields with defaults
    log_level: str = "INFO"              # JESSE_LOG_LEVEL
    json_indent: int = 2                 # JESSE_JSON_INDENT
    connect_timeout: int = 30            # JESSE_CONNECT_TIMEOUT (seconds)
    request_timeout: int = 300           # JESSE_REQUEST_TIMEOUT (seconds)
    
    class Config:
        env_prefix = "JESSE_"
        env_file = ".env"
        case_sensitive = False
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @validator("json_indent")
    def validate_json_indent(cls, v):
        if not 0 <= v <= 4:
            raise ValueError("json_indent must be between 0 and 4")
        return v
    
    @validator("api_token")
    def validate_api_token(cls, v):
        if not v or len(v) != 64:  # SHA256 produces 64 hex chars
            logger.warning(
                "api_token should be a SHA256 hash (64 hex characters). "
                "Got length: {}".format(len(v))
            )
        return v
    
    def __repr__(self):
        """Safe representation that doesn't expose token."""
        return (
            f"JesseConfig(url={self.url}, "
            f"api_token=***hidden***, "
            f"log_level={self.log_level}, "
            f"json_indent={self.json_indent})"
        )


def load_config() -> JesseConfig:
    """
    Load and validate configuration from environment variables.
    
    Raises:
        ValueError: If required env vars are missing or invalid
    
    Returns:
        JesseConfig instance
    """
    try:
        config = JesseConfig()
        logger.info(f"✅ Configuration loaded: {config}")
        return config
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error loading config: {e}")
        raise
```

**Success Criteria**:
- [ ] Config loads from environment variables
- [ ] Validates required fields (url, api_token)
- [ ] Validates optional fields (log_level, timeouts)
- [ ] Raises clear error if required fields missing
- [ ] Masks token in string representation
- [ ] Unit tests pass (see Phase 6)

**Testing Approach**:
- Test with valid env vars
- Test with missing required vars
- Test with invalid values (wrong log_level, etc.)
- Test configuration masking

**Rollback Strategy**:
- If config loading fails, server won't start (that's OK)
- Can restore by setting correct env vars

---

### Phase 2: HTTP Client (3-4 days)

**Objective**: Create HTTP wrapper for all Jesse API communication.

**Files to Create**:
- `jesse_mcp/core/http_client.py` (NEW)
- `jesse_mcp/core/errors.py` (NEW - for custom exceptions)

**Files to Modify**:
- `pyproject.toml` (add aiohttp)
- `requirements.txt` (add aiohttp)

#### Implementation Steps

##### Step 2.1: Create error classes

```python
# jesse_mcp/core/errors.py
class JesseIntegrationError(Exception):
    """Base exception for Jesse integration errors."""
    pass

class JesseConnectionError(JesseIntegrationError):
    """Raised when cannot connect to Jesse API."""
    pass

class JesseAuthenticationError(JesseIntegrationError):
    """Raised when authentication fails."""
    pass

class JesseTimeoutError(JesseIntegrationError):
    """Raised when operation times out."""
    pass

class JesseAPIError(JesseIntegrationError):
    """Raised when Jesse API returns error."""
    pass
```

##### Step 2.2: Create HTTP client

```python
# jesse_mcp/core/http_client.py
import aiohttp
import asyncio
import logging
import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from jesse_mcp.core.config import JesseConfig
from jesse_mcp.core.errors import (
    JesseConnectionError,
    JesseAuthenticationError,
    JesseTimeoutError,
    JesseAPIError,
)

logger = logging.getLogger("jesse-mcp.http_client")


class JesseHTTPClient:
    """HTTP client for communicating with Jesse API."""
    
    def __init__(self, config: JesseConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = str(config.url).rstrip("/")
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def connect(self):
        """Create HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.connect_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info(f"✅ HTTP session created for {self.base_url}")
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("✅ HTTP session closed")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        return {
            "Authorization": self.config.api_token,
            "Content-Type": "application/json",
        }
    
    async def health_check(self) -> bool:
        """
        Check if Jesse API is reachable and authentication works.
        
        Returns:
            True if healthy, False otherwise
        
        Raises:
            JesseConnectionError: If cannot connect
            JesseAuthenticationError: If auth fails
        """
        try:
            await self.connect()
            
            async with self.session.get(
                f"{self.base_url}/",
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=self.config.connect_timeout),
            ) as resp:
                if resp.status == 401:
                    raise JesseAuthenticationError(
                        "Invalid JESSE_API_TOKEN. Check your authentication."
                    )
                elif resp.status == 200:
                    logger.info("✅ Jesse API health check passed")
                    return True
                else:
                    logger.warning(f"⚠️ Jesse API health check returned {resp.status}")
                    return resp.status < 400
        
        except aiohttp.ClientConnectorError as e:
            raise JesseConnectionError(
                f"Cannot connect to Jesse at {self.base_url}. "
                f"Is Jesse running? Error: {e}"
            )
        except asyncio.TimeoutError:
            raise JesseConnectionError(
                f"Connection to Jesse at {self.base_url} timed out. "
                f"Check JESSE_CONNECT_TIMEOUT."
            )
    
    async def backtest(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        hyperparameters: Optional[Dict[str, Any]] = None,
        include_trades: bool = False,
        include_equity_curve: bool = False,
        include_logs: bool = False,
    ) -> Dict[str, Any]:
        """
        Run backtest and wait for completion (blocking).
        
        Returns:
            Backtest results matching current JesseWrapper interface
        """
        await self.connect()
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Prepare request
        request_data = {
            "id": session_id,
            "exchange": exchange,
            "routes": [{
                "exchange": exchange,
                "strategy": strategy,
                "symbol": symbol,
                "timeframe": timeframe,
            }],
            "data_routes": [],
            "config": {
                "starting_balance": starting_balance,
                "fee": fee,
                "type": exchange_type,
                "futures_leverage": leverage,
                "futures_leverage_mode": "cross",
                "exchange": exchange,
                "warm_up_candles": 240,
            },
            "start_date": start_date,
            "finish_date": end_date,
            "debug_mode": False,
            "export_csv": include_trades,
            "export_json": include_equity_curve,
            "export_chart": False,
            "export_tradingview": False,
            "fast_mode": True,
            "benchmark": False,
        }
        
        if hyperparameters:
            request_data["hyperparameters"] = hyperparameters
        
        try:
            # Start backtest
            logger.info(f"Starting backtest {session_id}: {strategy} on {symbol}")
            async with self.session.post(
                f"{self.base_url}/backtest",
                json=request_data,
                headers=self._get_headers(),
            ) as resp:
                if resp.status == 401:
                    raise JesseAuthenticationError("Invalid JESSE_API_TOKEN")
                elif resp.status == 202:
                    logger.info(f"✅ Backtest accepted: {session_id}")
                elif resp.status != 200:
                    raise JesseAPIError(
                        f"Backtest start failed: {resp.status} "
                        f"- {await resp.text()}"
                    )
            
            # Poll for results
            result = await self._poll_backtest_results(session_id)
            return result
        
        except asyncio.TimeoutError:
            raise JesseTimeoutError(
                f"Backtest timed out after {self.config.request_timeout}s. "
                f"Increase JESSE_REQUEST_TIMEOUT."
            )
    
    async def _poll_backtest_results(
        self, session_id: str
    ) -> Dict[str, Any]:
        """
        Poll for backtest results until completion.
        
        Uses exponential backoff: 0.1s → 0.2s → 0.5s → 1s → 5s (max)
        """
        start_time = datetime.now()
        timeout = timedelta(seconds=self.config.request_timeout)
        
        poll_interval = 0.1
        max_poll_interval = 5.0
        
        while True:
            elapsed = datetime.now() - start_time
            if elapsed > timeout:
                raise JesseTimeoutError(
                    f"Backtest polling timed out after {elapsed.total_seconds()}s"
                )
            
            try:
                # Query session status
                async with self.session.get(
                    f"{self.base_url}/backtest/sessions?id={session_id}",
                    headers=self._get_headers(),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"⚠️ Session query failed: {resp.status}")
                        await asyncio.sleep(poll_interval)
                        poll_interval = min(poll_interval * 2, max_poll_interval)
                        continue
                    
                    data = await resp.json()
                    # Parse response - adjust based on actual Jesse API
                    # This is a placeholder; adjust based on actual response format
                    if self._is_backtest_complete(data):
                        logger.info(f"✅ Backtest complete: {session_id}")
                        return data
                    
                    logger.debug(f"Backtest still running: {session_id}")
                    await asyncio.sleep(poll_interval)
                    poll_interval = min(poll_interval * 2, max_poll_interval)
            
            except Exception as e:
                logger.warning(f"⚠️ Error polling backtest: {e}")
                await asyncio.sleep(poll_interval)
                poll_interval = min(poll_interval * 2, max_poll_interval)
    
    def _is_backtest_complete(self, response: Dict) -> bool:
        """
        Check if backtest response indicates completion.
        
        Adjust based on actual Jesse API response format.
        """
        # This is a placeholder - adjust based on actual API
        if isinstance(response, dict):
            status = response.get("status")
            return status in ["completed", "finished", "done"]
        return False
    
    async def list_strategies(self) -> Dict[str, Any]:
        """List available strategies."""
        await self.connect()
        
        try:
            async with self.session.get(
                f"{self.base_url}/strategies",
                headers=self._get_headers(),
            ) as resp:
                if resp.status == 401:
                    raise JesseAuthenticationError("Invalid JESSE_API_TOKEN")
                elif resp.status != 200:
                    raise JesseAPIError(f"Failed to list strategies: {resp.status}")
                
                return await resp.json()
        except Exception as e:
            logger.error(f"Error listing strategies: {e}")
            raise
    
    async def read_strategy(self, name: str) -> Dict[str, Any]:
        """Read strategy source code."""
        await self.connect()
        
        try:
            async with self.session.get(
                f"{self.base_url}/strategies/{name}",
                headers=self._get_headers(),
            ) as resp:
                if resp.status == 401:
                    raise JesseAuthenticationError("Invalid JESSE_API_TOKEN")
                elif resp.status == 404:
                    raise JesseAPIError(f"Strategy not found: {name}")
                elif resp.status != 200:
                    raise JesseAPIError(f"Failed to read strategy: {resp.status}")
                
                return await resp.json()
        except Exception as e:
            logger.error(f"Error reading strategy: {e}")
            raise
    
    async def import_candles(
        self,
        exchange: str,
        symbol: str,
        start_date: str,
    ) -> Dict[str, Any]:
        """Import candles and wait for completion."""
        await self.connect()
        
        session_id = str(uuid.uuid4())
        
        request_data = {
            "id": session_id,
            "exchange": exchange,
            "symbol": symbol,
            "start_date": start_date,
        }
        
        try:
            # Start import
            logger.info(f"Starting candles import: {exchange} {symbol}")
            async with self.session.post(
                f"{self.base_url}/candles/import",
                json=request_data,
                headers=self._get_headers(),
            ) as resp:
                if resp.status == 401:
                    raise JesseAuthenticationError("Invalid JESSE_API_TOKEN")
                elif resp.status == 202:
                    logger.info(f"✅ Import accepted: {session_id}")
                elif resp.status != 200:
                    raise JesseAPIError(f"Import failed: {resp.status}")
            
            # Poll for results
            result = await self._poll_import_results(session_id)
            return result
        
        except asyncio.TimeoutError:
            raise JesseTimeoutError(f"Candles import timed out after {self.config.request_timeout}s")
```

**Success Criteria**:
- [ ] HTTP client connects to Jesse API
- [ ] Authentication works (token in headers)
- [ ] Health check validates connection
- [ ] Backtest request is sent correctly
- [ ] Polling logic works (exponential backoff)
- [ ] Errors are caught and wrapped appropriately
- [ ] Timeout handling works
- [ ] All methods return data matching current JesseWrapper interface

**Testing Approach**:
- Mock aiohttp.ClientSession
- Test each endpoint with mocked responses
- Test error scenarios (401, 404, 500)
- Test polling timeout
- Test connection failure

**Rollback Strategy**:
- Keep old `core/integrations.py` until Phase 3 is complete
- HTTP client is isolated, doesn't affect other code

---

### Phase 3: Integration Layer Refactor (2-3 days)

**Objective**: Update JesseWrapper to use HTTP client instead of direct imports.

**Files to Modify**:
- `jesse_mcp/core/integrations.py` (REFACTOR)

**Files to Delete** (when complete):
- Old import paths and filesystem logic

#### Implementation Steps

##### Step 3.1: Refactor JesseWrapper

```python
# jesse_mcp/core/integrations.py (REFACTORED)
import logging
from typing import Dict, Any, Optional

from jesse_mcp.core.config import JesseConfig, load_config
from jesse_mcp.core.http_client import JesseHTTPClient
from jesse_mcp.core.errors import JesseIntegrationError

logger = logging.getLogger("jesse-mcp.integration")

# Global config and client (initialized at startup)
_config: Optional[JesseConfig] = None
_client: Optional[JesseHTTPClient] = None
JESSE_AVAILABLE = False


async def initialize_jesse_client():
    """
    Initialize Jesse HTTP client from environment configuration.
    
    Should be called at server startup.
    
    Raises:
        ValueError: If configuration is invalid
        JesseConnectionError: If cannot connect to Jesse API
    """
    global _config, _client, JESSE_AVAILABLE
    
    try:
        # Load and validate configuration
        _config = load_config()
        logger.info(f"✅ Configuration loaded: {_config}")
        
        # Create and test HTTP client
        _client = JesseHTTPClient(_config)
        await _client.connect()
        
        # Verify connection
        if await _client.health_check():
            JESSE_AVAILABLE = True
            logger.info("✅ Jesse API is available and authenticated")
        else:
            JESSE_AVAILABLE = False
            logger.error("❌ Jesse API health check failed")
            raise JesseIntegrationError("Jesse API health check failed")
    
    except Exception as e:
        JESSE_AVAILABLE = False
        logger.error(f"❌ Failed to initialize Jesse client: {e}")
        raise


class JesseWrapper:
    """
    Wrapper around Jesse HTTP API for MCP operations.
    
    Provides clean abstractions for:
    - Running backtests
    - Managing strategies
    - Downloading candle data
    - Analyzing results
    
    Uses HTTP client internally for all communication.
    """
    
    def __init__(self):
        if not JESSE_AVAILABLE or _client is None:
            raise JesseIntegrationError("Jesse API not available")
        self.client = _client
        logger.info("✅ JesseWrapper initialized")
    
    def backtest(
        self,
        strategy: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        exchange: str = "Binance",
        starting_balance: float = 10000,
        fee: float = 0.001,
        leverage: float = 1,
        exchange_type: str = "futures",
        hyperparameters: Optional[Dict[str, Any]] = None,
        include_trades: bool = False,
        include_equity_curve: bool = False,
        include_logs: bool = False,
    ) -> Dict[str, Any]:
        """
        Run a backtest using Jesse's HTTP API.
        
        NOTE: This method is synchronous but calls async client internally.
        In a real async environment, this should be awaited.
        
        Returns:
            Dict with backtest results and metrics
        """
        import asyncio
        
        try:
            # Run async client in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, use run_coroutine_threadsafe
                # For now, we'll require this to be called from non-async context
                raise RuntimeError("backtest() must be called from sync context")
            
            result = loop.run_until_complete(
                self.client.backtest(
                    strategy=strategy,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                    exchange=exchange,
                    starting_balance=starting_balance,
                    fee=fee,
                    leverage=leverage,
                    exchange_type=exchange_type,
                    hyperparameters=hyperparameters,
                    include_trades=include_trades,
                    include_equity_curve=include_equity_curve,
                    include_logs=include_logs,
                )
            )
            return result
        
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {"error": str(e), "error_type": type(e).__name__, "success": False}
    
    def list_strategies(self) -> Dict[str, Any]:
        """List all available strategies."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError("list_strategies() must be called from sync context")
            
            result = loop.run_until_complete(self.client.list_strategies())
            return result
        
        except Exception as e:
            logger.error(f"Failed to list strategies: {e}")
            return {"error": str(e), "strategies": []}
    
    def read_strategy(self, name: str) -> Dict[str, Any]:
        """Read strategy source code."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError("read_strategy() must be called from sync context")
            
            result = loop.run_until_complete(self.client.read_strategy(name))
            return result
        
        except Exception as e:
            logger.error(f"Failed to read strategy: {e}")
            return {"error": str(e), "name": name}
    
    def validate_strategy(self, code: str) -> Dict[str, Any]:
        """Validate strategy code without saving (local validation only)."""
        try:
            # Try to compile the code
            try:
                compile(code, "<string>", "exec")
                syntax_valid = True
                syntax_error = None
            except SyntaxError as e:
                syntax_valid = False
                syntax_error = str(e)
            
            # Check for required methods
            required_methods = ["should_long", "go_long", "should_short", "go_short"]
            missing_methods = [m for m in required_methods if f"def {m}(" not in code]
            
            # Check imports
            imports_valid = "from jesse.strategies import Strategy" in code
            
            result = {
                "valid": syntax_valid and imports_valid and len(missing_methods) == 0,
                "syntax_valid": syntax_valid,
                "syntax_error": syntax_error,
                "imports_valid": imports_valid,
                "has_required_methods": len(missing_methods) == 0,
                "missing_methods": missing_methods,
                "has_hyperparameters": "def hyperparameters(" in code,
            }
            
            logger.info(
                f"Strategy validation: {'✅ Valid' if result['valid'] else '❌ Invalid'}"
            )
            return result
        
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"error": str(e), "valid": False}
    
    def import_candles(
        self,
        exchange: str,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Import candle data from exchange."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                raise RuntimeError("import_candles() must be called from sync context")
            
            result = loop.run_until_complete(
                self.client.import_candles(
                    exchange=exchange,
                    symbol=symbol,
                    start_date=start_date,
                )
            )
            return {
                "success": True,
                "exchange": exchange,
                "symbol": symbol,
                "start_date": start_date,
                "result": result,
            }
        
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "exchange": exchange,
                "symbol": symbol,
            }


def get_jesse_wrapper() -> JesseWrapper:
    """
    Factory function to get JesseWrapper instance.
    
    Returns:
        JesseWrapper instance
    
    Raises:
        JesseIntegrationError if Jesse is not available
    """
    if not JESSE_AVAILABLE:
        raise JesseIntegrationError("Jesse API not available")
    
    return JesseWrapper()
```

**Success Criteria**:
- [ ] JesseWrapper maintains same interface as before
- [ ] All methods work via HTTP client
- [ ] Error handling preserved
- [ ] Sync/async bridging works
- [ ] No direct Jesse imports remain
- [ ] No filesystem path logic remains

**Testing Approach**:
- Mock HTTP client responses
- Test that wrapper methods call correct HTTP endpoints
- Test error propagation
- Test sync/async bridging

**Rollback Strategy**:
- Keep old direct-import version in git history
- If HTTP client has issues, can revert Phase 2-3

---

### Phase 4: Server Startup Enhancements (1-2 days)

**Objective**: Update server initialization to load config and validate Jesse connection.

**Files to Modify**:
- `jesse_mcp/server.py` (ADD initialization logic)
- `jesse_mcp/__main__.py` (minimal changes)
- `jesse_mcp/cli.py` (minimal changes)

#### Implementation Steps

##### Step 4.1: Update server.py main()

```python
# jesse_mcp/server.py - Update main() function

async def main():
    """Main server entry point with configuration and health checks."""
    import logging
    from jesse_mcp.core.config import load_config
    from jesse_mcp.core.integrations import initialize_jesse_client, JESSE_AVAILABLE
    
    logger.info("Starting jesse-mcp server v1.0.0")
    
    # Step 1: Load configuration
    try:
        config = load_config()
        logger.info(f"✅ Configuration loaded")
    except Exception as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Please check your environment variables:")
        logger.error("  - JESSE_URL (required)")
        logger.error("  - JESSE_API_TOKEN (required)")
        sys.exit(1)
    
    # Step 2: Initialize Jesse client
    try:
        await initialize_jesse_client()
        logger.info("✅ Jesse API connection established")
    except Exception as e:
        logger.error(f"❌ Jesse connection failed: {e}")
        logger.error(f"Trying to connect to: {config.url}")
        logger.error("Is Jesse running? Check JESSE_URL and JESSE_API_TOKEN")
        sys.exit(1)
    
    # Step 3: Run MCP server normally
    logger.info("✅ MCP server ready to accept connections")
    
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                response = await handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            
            except json.JSONDecodeError:
                error_response = {"error": "Invalid JSON request"}
                print(json.dumps(error_response))
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Cleanup
        from jesse_mcp.core.http_client import _client
        if _client:
            await _client.close()
```

**Success Criteria**:
- [ ] Server loads config on startup
- [ ] Server validates Jesse connection before starting
- [ ] Clear error messages if connection fails
- [ ] Server exits with proper error code if config invalid
- [ ] MCP protocol handling unchanged

---

### Phase 5: CLI Enhancement (1 day)

**Objective**: Add helpful CLI commands for configuration and debugging.

**Files to Modify**:
- `jesse_mcp/cli.py`

#### Implementation Steps

##### Step 5.1: Add CLI commands

```python
# jesse_mcp/cli.py (ENHANCED)

import argparse
import sys
import asyncio
from jesse_mcp.core.config import load_config, JesseConfig
from jesse_mcp.core.http_client import JesseHTTPClient


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Jesse MCP Server - Quantitative Trading Analysis"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="jesse-mcp 1.0.0"
    )
    
    parser.add_argument(
        "--config",
        action="store_true",
        help="Show current configuration (token masked)"
    )
    
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test connection to Jesse API"
    )
    
    args = parser.parse_args()
    
    # Handle --config
    if args.config:
        try:
            config = load_config()
            print("✅ Configuration loaded successfully:")
            print(f"  JESSE_URL: {config.url}")
            print(f"  JESSE_API_TOKEN: ***hidden***")
            print(f"  JESSE_LOG_LEVEL: {config.log_level}")
            print(f"  JESSE_JSON_INDENT: {config.json_indent}")
            print(f"  JESSE_CONNECT_TIMEOUT: {config.connect_timeout}s")
            print(f"  JESSE_REQUEST_TIMEOUT: {config.request_timeout}s")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            sys.exit(1)
        return
    
    # Handle --test-connection
    if args.test_connection:
        try:
            config = load_config()
            client = JesseHTTPClient(config)
            
            print(f"Testing connection to: {config.url}")
            is_healthy = asyncio.run(client.health_check())
            
            if is_healthy:
                print("✅ Jesse API is reachable and authenticated")
            else:
                print("❌ Jesse API health check failed")
                sys.exit(1)
        
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            sys.exit(1)
        finally:
            asyncio.run(client.close())
        return
    
    # Default: start server
    from jesse_mcp.server import main as server_main
    asyncio.run(server_main())


if __name__ == "__main__":
    sys.exit(main())
```

**Success Criteria**:
- [ ] `jesse-mcp --config` shows configuration
- [ ] `jesse-mcp --test-connection` tests Jesse API
- [ ] Default behavior starts server
- [ ] Token is masked in config output

---

### Phase 6: Testing (3-4 days)

**Objective**: Create comprehensive unit and integration tests.

**Files to Create**:
- `tests/test_config.py` (NEW)
- `tests/test_http_client.py` (NEW)
- `tests/test_integrations.py` (NEW - updated from old tests)
- `tests/conftest.py` (pytest fixtures)

**Files to Modify**:
- `tests/test_server.py` (update to use new config)

#### Testing Categories

##### 6.1: Configuration Tests

```python
# tests/test_config.py
import os
import pytest
from jesse_mcp.core.config import JesseConfig, load_config
from pydantic import ValidationError


def test_config_requires_jesse_url():
    """Test that JESSE_URL is required."""
    # Clear env vars
    for key in ["JESSE_URL", "JESSE_API_TOKEN"]:
        os.environ.pop(key, None)
    
    with pytest.raises(ValidationError):
        load_config()


def test_config_requires_jesse_api_token():
    """Test that JESSE_API_TOKEN is required."""
    os.environ["JESSE_URL"] = "http://localhost:5000"
    os.environ.pop("JESSE_API_TOKEN", None)
    
    with pytest.raises(ValidationError):
        load_config()


def test_config_loads_valid_env_vars():
    """Test loading valid configuration."""
    os.environ["JESSE_URL"] = "http://localhost:5000"
    os.environ["JESSE_API_TOKEN"] = "a" * 64  # Valid SHA256 length
    
    config = load_config()
    assert str(config.url) == "http://localhost:5000/"
    assert config.api_token == "a" * 64


def test_config_uses_defaults():
    """Test that optional vars use defaults."""
    os.environ["JESSE_URL"] = "http://localhost:5000"
    os.environ["JESSE_API_TOKEN"] = "a" * 64
    os.environ.pop("JESSE_LOG_LEVEL", None)
    
    config = load_config()
    assert config.log_level == "INFO"
    assert config.json_indent == 2


def test_config_masks_token_in_repr():
    """Test that token is masked in string representation."""
    os.environ["JESSE_URL"] = "http://localhost:5000"
    os.environ["JESSE_API_TOKEN"] = "secret" * 10  # 60 chars
    
    config = load_config()
    config_str = repr(config)
    
    assert "***hidden***" in config_str
    assert "secret" not in config_str
```

##### 6.2: HTTP Client Tests

```python
# tests/test_http_client.py
import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from jesse_mcp.core.http_client import JesseHTTPClient
from jesse_mcp.core.config import JesseConfig
from jesse_mcp.core.errors import (
    JesseConnectionError,
    JesseAuthenticationError,
    JesseTimeoutError,
)


@pytest.fixture
def config():
    """Create test configuration."""
    return JesseConfig(
        url="http://localhost:5000",
        api_token="a" * 64,
    )


@pytest.fixture
async def client(config):
    """Create test HTTP client."""
    client = JesseHTTPClient(config)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_health_check_success(client):
    """Test successful health check."""
    with patch.object(client, "session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        result = await client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_auth_failure(client):
    """Test health check with auth failure."""
    with patch.object(client, "session") as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(JesseAuthenticationError):
            await client.health_check()


@pytest.mark.asyncio
async def test_health_check_connection_error(client):
    """Test health check with connection error."""
    with patch.object(client, "session") as mock_session:
        mock_session.get.side_effect = aiohttp.ClientConnectorError(
            connection_key=None,
            os_error=OSError("Connection refused")
        )
        
        with pytest.raises(JesseConnectionError):
            await client.health_check()


# More tests for each method...
```

##### 6.3: Integration Tests

```python
# tests/test_integrations.py
import pytest
from unittest.mock import patch, AsyncMock
from jesse_mcp.core.integrations import (
    JesseWrapper,
    initialize_jesse_client,
    JESSE_AVAILABLE,
)


@pytest.mark.asyncio
async def test_initialize_jesse_client_success():
    """Test successful initialization."""
    with patch("jesse_mcp.core.integrations.load_config") as mock_config, \
         patch("jesse_mcp.core.integrations.JesseHTTPClient") as mock_client:
        
        # Mock config
        mock_config.return_value.url = "http://localhost:5000"
        
        # Mock HTTP client
        mock_client_instance = AsyncMock()
        mock_client_instance.health_check = AsyncMock(return_value=True)
        mock_client.return_value = mock_client_instance
        
        await initialize_jesse_client()
        # Assert that JESSE_AVAILABLE is True


def test_jesse_wrapper_preserves_interface():
    """Test that JesseWrapper maintains backward compatibility."""
    # Create wrapper with mocked client
    with patch("jesse_mcp.core.integrations.JESSE_AVAILABLE", True):
        with patch("jesse_mcp.core.integrations._client"):
            wrapper = JesseWrapper()
            
            # Check that all expected methods exist
            assert hasattr(wrapper, "backtest")
            assert hasattr(wrapper, "list_strategies")
            assert hasattr(wrapper, "read_strategy")
            assert hasattr(wrapper, "validate_strategy")
            assert hasattr(wrapper, "import_candles")
```

**Success Criteria**:
- [ ] All configuration tests pass
- [ ] All HTTP client tests pass
- [ ] All integration tests pass
- [ ] Test coverage > 80%
- [ ] Mocking strategy works without live Jesse
- [ ] Error scenarios covered

---

### Phase 7: Documentation (2-3 days)

**Objective**: Update/create documentation for deployment and usage.

**Files to Create/Modify**:
- `DEPLOYMENT.md` (NEW)
- `README.md` (UPDATE)
- `.env.example` (UPDATE)

#### 7.1: Update README

```markdown
# Jesse MCP Server

An MCP (Model Context Protocol) server that exposes Jesse's algorithmic trading framework capabilities to LLM agents.

## Quick Start

### Prerequisites
- Jesse API running and accessible (see [Deployment](#deployment))
- Python 3.10+

### Environment Variables

Required:
```bash
export JESSE_URL="http://localhost:5000"
export JESSE_API_TOKEN="<sha256_hash_of_jesse_password>"
```

Optional:
```bash
export JESSE_LOG_LEVEL="INFO"              # DEBUG, INFO, WARNING, ERROR
export JESSE_JSON_INDENT="2"               # 0-4 for JSON formatting
export JESSE_CONNECT_TIMEOUT="30"          # seconds
export JESSE_REQUEST_TIMEOUT="300"         # seconds
```

### Installation

```bash
pip install -e .
```

### Running the Server

```bash
# Start server
jesse-mcp

# Show configuration (token masked)
jesse-mcp --config

# Test connection to Jesse API
jesse-mcp --test-connection
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Running Jesse API
- Generating authentication token
- Docker deployment
- Troubleshooting
```

#### 7.2: Create DEPLOYMENT.md

```markdown
# Deployment Guide

## Jesse API Setup

### Step 1: Install Jesse

```bash
pip install jesse
```

### Step 2: Create Jesse Project

```bash
jesse create-project myproject
cd myproject
```

### Step 3: Start Jesse API

```bash
jesse server
```

The Jesse API will start on `http://localhost:5000` by default.

### Step 4: Generate Authentication Token

The JESSE_API_TOKEN is a SHA256 hash of your Jesse password. Generate it:

```python
from hashlib import sha256
password = "your_jesse_password"
token = sha256(password.encode()).hexdigest()
print(token)
```

## MCP Server Setup

### Local Machine

```bash
# Clone repo
git clone <repo>
cd jesse-mcp

# Set environment variables
export JESSE_URL="http://localhost:5000"
export JESSE_API_TOKEN="<token_from_above>"

# Install
pip install -e .

# Test connection
jesse-mcp --test-connection

# Start server
jesse-mcp
```

### Docker

Create `.env`:
```env
JESSE_URL=http://jesse:5000
JESSE_API_TOKEN=<token>
```

Build:
```bash
docker build -t jesse-mcp .
```

Run:
```bash
docker run -e JESSE_URL=http://jesse:5000 \
           -e JESSE_API_TOKEN=<token> \
           jesse-mcp
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  jesse:
    image: jesse:latest
    ports:
      - "5000:5000"
    environment:
      PASSWORD: "jesse_password"
  
  jesse-mcp:
    build: .
    environment:
      JESSE_URL: http://jesse:5000
      JESSE_API_TOKEN: <token>
```

Run:
```bash
docker-compose up
```

## Troubleshooting

### Connection Failed
```
Error: Cannot connect to Jesse at http://localhost:5000
```

**Checks**:
1. Is Jesse running? `curl http://localhost:5000/`
2. Is URL correct? Check `JESSE_URL` env var
3. Firewall? Check if port 5000 is accessible
4. Docker? If using Docker, use service name not localhost

### Authentication Failed
```
Error: Invalid JESSE_API_TOKEN
```

**Checks**:
1. Generate token again: `echo -n "password" | sha256sum`
2. Is it the SHA256 hash? Should be 64 hex characters
3. Is it the right password? Check Jesse configuration

### Operation Timeout
```
Error: Operation took too long - increase JESSE_REQUEST_TIMEOUT
```

**Fixes**:
1. Increase timeout: `export JESSE_REQUEST_TIMEOUT="600"`
2. Check Jesse logs for errors
3. Check system resources (CPU, memory)
```

**Success Criteria**:
- [ ] README updated with env var info
- [ ] DEPLOYMENT.md created with complete setup guide
- [ ] `.env.example` includes all env vars
- [ ] Docker examples work
- [ ] Troubleshooting section covers common issues

---

### Phase 8: Integration Testing & Fixes (2-3 days)

**Objective**: End-to-end testing with real Jesse instance and final fixes.

#### Implementation Steps

##### Step 8.1: E2E Test with Real Jesse

```bash
# Start Jesse
jesse create-project test_project
cd test_project
jesse server &

# Get auth token
TOKEN=$(python3 -c "from hashlib import sha256; print(sha256(b'password').hexdigest())")

# Set env vars
export JESSE_URL="http://localhost:5000"
export JESSE_API_TOKEN="$TOKEN"

# Run MCP server
jesse-mcp

# In another terminal, test with curl
curl -X GET http://localhost:5000/ \
  -H "Authorization: $TOKEN"
```

##### Step 8.2: Run Full Test Suite

```bash
# Unit tests
pytest tests/test_config.py -v
pytest tests/test_http_client.py -v
pytest tests/test_integrations.py -v

# Integration tests
pytest tests/test_e2e.py -v

# Coverage report
pytest --cov=jesse_mcp tests/
```

##### Step 8.3: Fix Any Issues

- Adjust polling intervals if too slow/fast
- Fix any response format mismatches
- Handle edge cases discovered in testing

**Success Criteria**:
- [ ] All tests pass
- [ ] E2E flow works end-to-end
- [ ] No warnings in logs
- [ ] Error handling works correctly
- [ ] Performance acceptable

---

## Dependencies and Build Order

### Dependency Graph

```
Phase 1: Config Layer
    ↓
Phase 2: HTTP Client (depends on Config)
    ↓
Phase 3: Integration Refactor (depends on HTTP Client)
    ↓
Phase 4: Server Startup (depends on Integration)
    ↓
Phase 5: CLI Enhancement (depends on Config)
    ↓
Phase 6: Testing (tests Phases 1-5)
    ↓
Phase 7: Documentation
    ↓
Phase 8: E2E Testing & Fixes
```

### Parallel Opportunities

- Phase 5 (CLI) can start once Phase 1 is done
- Phase 7 (Documentation) can start anytime (reference design docs)
- Phase 6 (Testing) can start as soon as each phase is complete

### Build Order

**Week 1**:
- Day 1-2: Phase 1 (Config)
- Day 2-3: Phase 2 (HTTP Client)
- Day 3-4: Phase 3 (Integration)
- Day 4-5: Phase 4 (Server) + Phase 5 (CLI) in parallel

**Week 2**:
- Day 1-3: Phase 6 (Testing)
- Day 3-4: Phase 7 (Documentation)
- Day 4-5: Phase 8 (E2E Testing & Fixes)

---

## Testing Strategy

### Unit Testing

**Config Tests** (`test_config.py`):
- Valid configuration loading
- Required field validation
- Default value handling
- Token masking

**HTTP Client Tests** (`test_http_client.py`):
- Request formatting
- Authentication headers
- Response parsing
- Error handling
- Timeout handling
- Polling logic

**Integration Tests** (`test_integrations.py`):
- Wrapper interface preservation
- Method delegation to HTTP client
- Error propagation
- Initialization flow

### Integration Testing

**E2E Tests** (`test_e2e.py`):
- Full backtest flow
- Strategy listing
- Candles import
- Real Jesse API (if available)

### Manual Testing Checklist

- [ ] Start Jesse API
- [ ] Set environment variables
- [ ] Run `jesse-mcp --config` (verify masking)
- [ ] Run `jesse-mcp --test-connection` (verify connection)
- [ ] Start MCP server
- [ ] Test with Claude (run actual tools)
- [ ] Verify backtest works
- [ ] Verify error handling

### CI/CD Considerations

- Run unit tests on every PR
- Run integration tests before merge
- Run E2E tests on deployment
- Generate coverage reports
- Check for regressions

---

## Deployment and Rollout

### Feature Flags

If needed, use feature flags to gradually roll out:

```python
# jesse_mcp/core/config.py
USE_HTTP_CLIENT = os.getenv("USE_HTTP_CLIENT", "true").lower() == "true"

if USE_HTTP_CLIENT:
    # Use new HTTP client
    client = JesseHTTPClient(config)
else:
    # Fall back to old direct imports
    client = OldJesseWrapper()
```

### Backward Compatibility

✅ **Maintained**:
- All MCP tool signatures unchanged
- Response format identical
- Error types preserved

**Changes** (not breaking):
- Requires Jesse running separately (better architecture)
- Requires environment variables (more flexible)
- Requires network connection (expected with HTTP)

### Migration Path

1. **Phase 1-2**: Develop and test new code
2. **Phase 3-4**: Deploy to staging with real Jesse instance
3. **Phase 5-6**: Run full test suite
4. **Phase 7**: Deploy to production with feature flag
5. **Phase 8**: Monitor for issues, gradually increase rollout

### Rollback Procedures

If issues discovered:

1. **Immediate**: Set `USE_HTTP_CLIENT=false` env var
2. **Short-term**: Use previous version from git
3. **Long-term**: Fix issues and re-deploy

---

## Risk Management

### Identified Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Network latency makes ops slow | High | Configurable timeouts, monitor latency |
| Jesse API changes break MCP | High | Vendor API responses, version checks |
| Auth token exposed in logs | Medium | Mask token, security review |
| Jesse instance crashes mid-op | Medium | Graceful error handling, clear messages |
| Polling timeout too aggressive | Medium | Configurable with sane defaults |
| Config validation too strict | Low | Provide helpful error messages |

### Testing Checklist for Risks

- [ ] Test with slow network (increase timeouts)
- [ ] Test with Jesse unavailable (clear error)
- [ ] Test with wrong token (auth failure)
- [ ] Test with long-running backtest (polling works)
- [ ] Test with timeout exceeded (graceful failure)
- [ ] Scan logs for exposed tokens (use pytest)

---

## Success Criteria - Final Checklist

- [ ] **Configuration**: All env vars load and validate correctly
- [ ] **HTTP Client**: All Jesse API endpoints callable
- [ ] **Integration**: JesseWrapper interface unchanged
- [ ] **Server**: Starts with config validation
- [ ] **CLI**: All commands work as documented
- [ ] **Testing**: >80% code coverage
- [ ] **Documentation**: Complete setup guides
- [ ] **E2E**: Full workflow tested
- [ ] **Error Handling**: All scenarios produce helpful messages
- [ ] **Deployment**: Works in Docker and on bare metal

---

## Appendix

### A. Code Examples

#### Example 1: Running a Backtest

```python
from jesse_mcp.core.config import load_config
from jesse_mcp.core.http_client import JesseHTTPClient
import asyncio

async def run_backtest():
    config = load_config()
    async with JesseHTTPClient(config) as client:
        result = await client.backtest(
            strategy="MyStrategy",
            symbol="BTC-USDT",
            timeframe="1h",
            start_date="2023-01-01",
            end_date="2023-12-31",
        )
        print(result)

asyncio.run(run_backtest())
```

#### Example 2: Health Check

```python
from jesse_mcp.core.config import load_config
from jesse_mcp.core.http_client import JesseHTTPClient
import asyncio

async def check_health():
    config = load_config()
    client = JesseHTTPClient(config)
    is_healthy = await client.health_check()
    print("Jesse API is healthy:", is_healthy)

asyncio.run(check_health())
```

### B. Environment Configuration Template

```bash
# .env.template

# REQUIRED: Jesse API connection
JESSE_URL="http://localhost:5000"
JESSE_API_TOKEN="<sha256_hash_of_password>"

# OPTIONAL: Logging and formatting
JESSE_LOG_LEVEL="INFO"              # DEBUG, INFO, WARNING, ERROR
JESSE_JSON_INDENT="2"               # 0-4

# OPTIONAL: Timeout configurations
JESSE_CONNECT_TIMEOUT="30"          # Connection timeout in seconds
JESSE_REQUEST_TIMEOUT="300"         # Long operation timeout in seconds

# OPTIONAL: Feature flags
USE_HTTP_CLIENT="true"              # Use HTTP client (false = legacy)
```

### C. Docker Deployment Example

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY jesse_mcp ./jesse_mcp
COPY setup.py .

# Install application
RUN pip install -e .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD jesse-mcp --test-connection

# Run server
CMD ["jesse-mcp"]
```

### D. Troubleshooting Guide

**Q: "Cannot connect to Jesse at http://localhost:5000"**

A: Check:
1. Jesse is running: `curl http://localhost:5000/`
2. URL is correct: `echo $JESSE_URL`
3. Firewall allows port 5000
4. If using Docker, use service name not localhost

**Q: "Invalid JESSE_API_TOKEN"**

A: Regenerate token:
```bash
python3 -c "from hashlib import sha256; print(sha256(b'your_password').hexdigest())"
export JESSE_API_TOKEN="<result>"
```

**Q: "Operation took too long"**

A: Increase timeout:
```bash
export JESSE_REQUEST_TIMEOUT="600"
```

**Q: MCP server won't start**

A: Check logs:
```bash
jesse-mcp --config        # Show configuration
jesse-mcp --test-connection  # Test Jesse connection
```

---

## Document History

| Date | Author | Phase | Status |
|------|--------|-------|--------|
| 2024-12-04 | Research Team | Planning | ✓ Complete |
| TBD | Dev Team | Phase 1-8 | ⏳ Pending |

---

**Next Steps**: Proceed to Phase 1 implementation when ready.
