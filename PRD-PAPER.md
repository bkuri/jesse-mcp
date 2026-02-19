# PRD: Paper Trading MCP Tools for jesse-mcp

## Overview

**Goal**: Extend jesse-mcp with paper trading MCP tools that wrap Jesse's native paper trading capabilities.

**Timeline**: Phase 1 of E2E testing strategy

**Status**: Planning

---

## Background

MaxiTrader needs paper trading capabilities to validate safety scoring thresholds with real market data. This PRD defines the MCP tools required to support:

1. Starting/stopping paper trading sessions
2. Real-time metrics collection (equity, P&L, drawdown)
3. Trade execution tracking
4. Integration with MaxiTrader's safety monitoring system

---

## Tool Specifications

### 1. `paper_start`

Start a new paper trading session.

**Input Schema**:
```json
{
    "strategy": {
        "type": "string",
        "description": "Strategy name (e.g., 'SMACrossover', 'DayTrader')",
        "required": true
    },
    "symbol": {
        "type": "string",
        "description": "Trading pair (e.g., 'BTC-USDT')",
        "required": true
    },
    "timeframe": {
        "type": "string",
        "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
        "default": "1h",
        "required": false
    },
    "exchange": {
        "type": "string",
        "default": "Binance",
        "required": false
    },
    "starting_balance": {
        "type": "number",
        "default": 10000,
        "required": false
    },
    "leverage": {
        "type": "number",
        "default": 1,
        "required": false
    },
    "session_id": {
        "type": "string",
        "description": "Optional custom session ID (auto-generated if not provided)",
        "required": false
    },
    "fee": {
        "type": "number",
        "default": 0.001,
        "description": "Trading fee rate",
        "required": false
    }
}
```

**Returns**:
```json
{
    "session_id": "paper_abc123",
    "status": "running",
    "strategy": "SMACrossover",
    "symbol": "BTC-USDT",
    "timeframe": "1h",
    "exchange": "Binance",
    "starting_balance": 10000,
    "started_at": "2026-02-19T00:00:00Z"
}
```

**Maps to**: `jesse run-paper {exchange} {symbol} --strategy {strategy} --timeframe {timeframe}`

---

### 2. `paper_stop`

Stop a paper trading session and return final metrics.

**Input Schema**:
```json
{
    "session_id": {
        "type": "string",
        "required": true
    }
}
```

**Returns**:
```json
{
    "session_id": "paper_abc123",
    "status": "stopped",
    "stopped_at": "2026-02-19T12:00:00Z",
    "duration_hours": 12.0,
    "final_metrics": {
        "total_return": 0.0523,
        "sharpe_ratio": 1.45,
        "max_drawdown": 0.0821,
        "win_rate": 0.58,
        "total_trades": 23,
        "final_equity": 10523.00
    }
}
```

---

### 3. `paper_status`

Get current status of a paper trading session.

**Input Schema**:
```json
{
    "session_id": {
        "type": "string",
        "required": true
    }
}
```

**Returns**:
```json
{
    "session_id": "paper_abc123",
    "status": "running",
    "strategy": "SMACrossover",
    "symbol": "BTC-USDT",
    "current_equity": 10234.56,
    "unrealized_pnl": 34.56,
    "positions": [
        {
            "side": "long",
            "size": 0.05,
            "entry_price": 95000.00,
            "current_price": 96000.00,
            "unrealized_pnl": 50.00
        }
    ],
    "open_orders": [],
    "metrics": {
        "total_return": 0.0234,
        "sharpe_ratio": 1.23,
        "max_drawdown": 0.0421,
        "win_rate": 0.55,
        "total_trades": 11
    }
}
```

---

### 4. `paper_get_trades`

Get trades executed in a paper trading session.

**Input Schema**:
```json
{
    "session_id": {
        "type": "string",
        "required": true
    },
    "limit": {
        "type": "integer",
        "default": 100,
        "required": false
    },
    "offset": {
        "type": "integer",
        "default": 0,
        "required": false
    }
}
```

**Returns**:
```json
{
    "session_id": "paper_abc123",
    "total_trades": 23,
    "trades": [
        {
            "trade_id": "t001",
            "entry_time": "2026-02-19T01:00:00Z",
            "exit_time": "2026-02-19T02:30:00Z",
            "side": "long",
            "entry_price": 94500.00,
            "exit_price": 95200.00,
            "size": 0.1,
            "pnl": 70.00,
            "pnl_pct": 0.0074,
            "fees": 9.45
        }
    ]
}
```

---

### 5. `paper_get_equity`

Get equity curve data for a paper trading session.

**Input Schema**:
```json
{
    "session_id": {
        "type": "string",
        "required": true
    },
    "resolution": {
        "type": "string",
        "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
        "default": "1h",
        "description": "Resolution of equity curve data",
        "required": false
    }
}
```

**Returns**:
```json
{
    "session_id": "paper_abc123",
    "resolution": "1h",
    "equity_curve": [
        {
            "timestamp": "2026-02-19T00:00:00Z",
            "equity": 10000.00,
            "drawdown": 0.0,
            "unrealized_pnl": 0.0
        },
        {
            "timestamp": "2026-02-19T01:00:00Z",
            "equity": 10050.00,
            "drawdown": 0.0,
            "unrealized_pnl": 50.00
        }
    ]
}
```

---

### 6. `paper_get_metrics`

Get calculated performance metrics for a paper trading session.

**Input Schema**:
```json
{
    "session_id": {
        "type": "string",
        "required": true
    }
}
```

**Returns**:
```json
{
    "session_id": "paper_abc123",
    "metrics": {
        "total_return": 0.0523,
        "sharpe_ratio": 1.45,
        "sortino_ratio": 1.82,
        "max_drawdown": 0.0821,
        "win_rate": 0.58,
        "total_trades": 23,
        "profit_factor": 1.67,
        "avg_trade": 22.74,
        "avg_winning_trade": 85.50,
        "avg_losing_trade": -42.30,
        "var_95": 0.0234,
        "volatility": 0.15,
        "current_equity": 10523.00,
        "unrealized_pnl": 23.00
    }
}
```

---

### 7. `paper_list_sessions`

List all active paper trading sessions.

**Input Schema**:
```json
{}
```

**Returns**:
```json
{
    "sessions": [
        {
            "session_id": "paper_abc123",
            "strategy": "SMACrossover",
            "symbol": "BTC-USDT",
            "status": "running",
            "started_at": "2026-02-19T00:00:00Z",
            "duration_hours": 12.0
        }
    ],
    "total": 1
}
```

---

### 8. `paper_update_session`

Update session parameters (limited to safe modifications).

**Input Schema**:
```json
{
    "session_id": {
        "type": "string",
        "required": true
    },
    "updates": {
        "type": "object",
        "properties": {
            "leverage": {"type": "number"},
            "notes": {"type": "string"}
        },
        "required": false
    }
}
```

**Returns**:
```json
{
    "session_id": "paper_abc123",
    "status": "updated",
    "updated_fields": ["leverage"]
}
```

---

## Technical Implementation

### Architecture

```
jesse-mcp/
├── src/
│   ├── tools/
│   │   ├── paper_trading.py      # Paper trading tool implementations
│   │   ├── __init__.py
│   │   └── ...
│   ├── session_manager.py         # Session lifecycle management
│   └── server.py                  # Register new tools
└── tests/
    └── test_paper_tools.py        # Unit tests
```

### Session Manager

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import subprocess
import uuid
import asyncio

@dataclass
class PaperSession:
    id: str
    strategy: str
    symbol: str
    timeframe: str
    exchange: str
    starting_balance: float
    leverage: float
    fee: float
    started_at: datetime
    process: Optional[subprocess.Popen] = None
    status: str = "starting"
    jesse_session_id: Optional[str] = None

class PaperSessionManager:
    _sessions: Dict[str, PaperSession] = {}
    _jesse_base_path: str = "/srv/containers/jesse"
    
    async def start_session(
        self,
        strategy: str,
        symbol: str,
        timeframe: str = "1h",
        exchange: str = "Binance",
        starting_balance: float = 10000,
        leverage: float = 1.0,
        fee: float = 0.001,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        session_id = session_id or f"paper_{uuid.uuid4().hex[:8]}"
        
        session = PaperSession(
            id=session_id,
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            exchange=exchange,
            starting_balance=starting_balance,
            leverage=leverage,
            fee=fee,
            started_at=datetime.utcnow(),
            status="starting"
        )
        
        # Start Jesse paper trading process
        cmd = [
            "jesse", "run-paper",
            exchange, symbol,
            "--strategy", strategy,
            "--timeframe", timeframe,
            "--starting-balance", str(starting_balance),
            "--leverage", str(leverage),
            "--fee", str(fee),
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._jesse_base_path
        )
        
        session.process = process
        session.status = "running"
        self._sessions[session_id] = session
        
        return {
            "session_id": session_id,
            "status": "running",
            "strategy": strategy,
            "symbol": symbol,
            "timeframe": timeframe,
            "exchange": exchange,
            "starting_balance": starting_balance,
            "started_at": session.started_at.isoformat()
        }
    
    async def stop_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self._sessions[session_id]
        
        if session.process:
            session.process.terminate()
            try:
                session.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                session.process.kill()
        
        metrics = await self._calculate_final_metrics(session)
        session.status = "stopped"
        
        return {
            "session_id": session_id,
            "status": "stopped",
            "stopped_at": datetime.utcnow().isoformat(),
            "final_metrics": metrics
        }
    
    async def get_status(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self._sessions[session_id]
        
        is_running = session.process and session.process.poll() is None
        session.status = "running" if is_running else "stopped"
        
        metrics = await self._calculate_metrics(session)
        positions = await self._get_positions(session)
        orders = await self._get_open_orders(session)
        
        return {
            "session_id": session_id,
            "status": session.status,
            "strategy": session.strategy,
            "symbol": session.symbol,
            "current_equity": metrics.get("current_equity"),
            "unrealized_pnl": metrics.get("unrealized_pnl"),
            "positions": positions,
            "open_orders": orders,
            "metrics": metrics
        }
    
    async def get_trades(
        self, 
        session_id: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> Dict[str, Any]:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self._sessions[session_id]
        trades = await self._query_trades(session, limit, offset)
        
        return {
            "session_id": session_id,
            "total_trades": await self._count_trades(session),
            "trades": trades
        }
    
    async def get_equity(
        self, 
        session_id: str, 
        resolution: str = "1h"
    ) -> Dict[str, Any]:
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self._sessions[session_id]
        equity_curve = await self._query_equity(session, resolution)
        
        return {
            "session_id": session_id,
            "resolution": resolution,
            "equity_curve": equity_curve
        }
    
    def list_sessions(self) -> Dict[str, Any]:
        sessions = []
        for session in self._sessions.values():
            is_running = session.process and session.process.poll() is None
            sessions.append({
                "session_id": session.id,
                "strategy": session.strategy,
                "symbol": session.symbol,
                "status": "running" if is_running else "stopped",
                "started_at": session.started_at.isoformat(),
                "duration_hours": (datetime.utcnow() - session.started_at).total_seconds() / 3600
            })
        
        return {"sessions": sessions, "total": len(sessions)}
    
    async def _calculate_metrics(self, session: PaperSession) -> Dict[str, Any]:
        # Query Jesse's database for metrics
        # Implementation depends on Jesse's internal structures
        pass
    
    async def _calculate_final_metrics(self, session: PaperSession) -> Dict[str, Any]:
        # Calculate final metrics when session stops
        pass
    
    async def _get_positions(self, session: PaperSession) -> List[Dict[str, Any]]:
        # Query current positions from Jesse
        pass
    
    async def _get_open_orders(self, session: PaperSession) -> List[Dict[str, Any]]:
        # Query open orders from Jesse
        pass
    
    async def _query_trades(
        self, 
        session: PaperSession, 
        limit: int, 
        offset: int
    ) -> List[Dict[str, Any]]:
        # Query completed trades from Jesse's database
        pass
    
    async def _count_trades(self, session: PaperSession) -> int:
        # Count total trades for session
        pass
    
    async def _query_equity(
        self, 
        session: PaperSession, 
        resolution: str
    ) -> List[Dict[str, Any]]:
        # Query equity curve from Jesse's daily_balance table
        pass
```

### Tool Registration

```python
# In server.py

from .tools.paper_trading import (
    paper_start,
    paper_stop,
    paper_status,
    paper_get_trades,
    paper_get_equity,
    paper_get_metrics,
    paper_list_sessions,
    paper_update_session,
)

PAPER_TRADING_TOOLS = [
    {
        "name": "paper_start",
        "description": "Start a paper trading session for a strategy",
        "inputSchema": {...},
        "handler": paper_start
    },
    # ... other tools
]
```

---

## Integration with Jesse

### Database Tables

Paper trading sessions should use Jesse's existing tables:

- `candles` - Price data
- `trades` - Completed trades
- `orders` - Open/pending orders
- `positions` - Current positions
- `daily_balance` - Equity curve snapshots

### Session Isolation

Each paper session should be isolated by:
1. Unique session ID stored in a `session_id` column
2. Separate database file per session (optional)
3. Or filtering by session_id in queries

---

## Testing

### Unit Tests

```python
# tests/test_paper_tools.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_paper_start():
    """Test starting a paper trading session."""
    manager = PaperSessionManager()
    
    with patch.object(manager, '_start_jesse_process'):
        result = await manager.start_session(
            strategy="SMACrossover",
            symbol="BTC-USDT",
            timeframe="1h"
        )
    
    assert result["status"] == "running"
    assert result["strategy"] == "SMACrossover"
    assert result["symbol"] == "BTC-USDT"

@pytest.mark.asyncio
async def test_paper_stop():
    """Test stopping a paper trading session."""
    manager = PaperSessionManager()
    
    # Start session first
    with patch.object(manager, '_start_jesse_process'):
        start_result = await manager.start_session(
            strategy="SMACrossover",
            symbol="BTC-USDT"
        )
    
    # Stop session
    stop_result = await manager.stop_session(start_result["session_id"])
    
    assert stop_result["status"] == "stopped"

@pytest.mark.asyncio
async def test_paper_status():
    """Test getting session status."""
    pass

@pytest.mark.asyncio
async def test_paper_get_trades():
    """Test retrieving trades."""
    pass

@pytest.mark.asyncio
async def test_paper_get_equity():
    """Test retrieving equity curve."""
    pass
```

---

## Deployment Checklist

- [x] Implement `PaperSessionManager` class (via REST client wrapper)
- [x] Implement all 8 MCP tools
- [x] Add `get_closed_trades()` to REST client for trades endpoint
- [ ] Add session_id column to Jesse tables (if needed)
- [ ] Write unit tests for paper_* tools
- [ ] Test with actual Jesse paper trading
- [ ] Deploy to jesse-mcp server
- [ ] Update MCP tool registry
- [ ] Document in jesse-mcp README

---

## References

- Jesse Documentation: https://docs.jesse.trade
- Jesse Paper Trading: `jesse run-paper --help`
- MaxiTrader E2E Strategy: `/home/bk/source/maxitrader/AGENTS.md`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-19 | Initial PRD |
