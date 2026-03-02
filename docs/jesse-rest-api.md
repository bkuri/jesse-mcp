# Jesse 1.13.x REST API Reference

## Authentication

Jesse 1.13.x uses password-based authentication with JWT tokens:

```bash
# Login to get session token
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"password": "your-jesse-password"}'
# Response: {"token": "session-uuid-here"}

# Use token in subsequent requests
curl -X POST http://localhost:8000/backtest \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer session-uuid-here" \
  -d @backtest-payload.json
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | POST | Authenticate, returns session token |
| `/backtest` | POST | Run single backtest |
| `/backtest/{id}` | GET | Get backtest result/status |
| `/optimize` | POST | Run optimization |
| `/optimize/{id}` | GET | Get optimization result/status |
| `/candles/import` | POST | Import historical candles from exchange |
| `/candles/cancel-import` | POST | Cancel running import process |
| `/candles/existing` | POST | List existing candles with date ranges |
| `/candles/get` | POST | Get candles for exchange/symbol/timeframe |
| `/candles/delete` | POST | Delete candles for exchange/symbol |
| `/candles/clear-cache` | POST | Clear candles database cache |
| `/exchange/supported-symbols` | POST | Get available symbols for exchange |

## Backtest Payload

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "exchange": "Binance",
  "routes": [
    {
      "strategy": "MyStrategy",
      "symbol": "BTC-USDT",
      "timeframe": "1h"
    }
  ],
  "config": {
    "warm_up_candles": 240,
    "logging": {
      "output_type": "json"
    },
    "exchanges": {
      "Binance": {
        "balance": 10000,
        "fee_rate": 0.001
      }
    },
    "reporting": {
      "tradingview": false
    }
  },
  "start_date": "2023-01-01",
  "finish_date": "2024-01-01"
}
```

## Optimization Payload

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "exchange": "Binance",
  "routes": [
    {
      "strategy": "MyStrategy",
      "symbol": "BTC-USDT",
      "timeframe": "1h"
    }
  ],
  "config": {
    "warm_up_candles": 240,
    "logging": {"output_type": "json"},
    "exchanges": {
      "Binance": {"balance": 10000, "fee_rate": 0.001}
    }
  },
  "start_date": "2023-01-01",
  "finish_date": "2024-01-01",
  "optimize": {
    "strategy_name": "MyStrategy",
    "dna": "default-dna-string",
    "parameters": {
      "rsi_period": [10, 20],
      "tp_rate": [0.01, 0.05]
    }
  }
}
```

## Common Gotchas

### 1. `warm_up_candles` Placement

MUST be in `config` object, not at root level:

```json
// ✅ Correct
{"config": {"warm_up_candles": 240}}

// ❌ Wrong - will be ignored
{"warm_up_candles": 240}
```

### 2. `exchanges` Dict Requires `balance`

Missing balance causes errors:

```json
// ✅ Correct
"exchanges": {"Binance": {"balance": 10000, "fee_rate": 0.001}}

// ❌ Wrong - missing balance
"exchanges": {"Binance": {"fee_rate": 0.001}}
```

### 3. ID Must Be Valid UUID

String must match UUID regex:

```python
import uuid
backtest_id = str(uuid.uuid4())  # Always use uuid module
```

### 4. Route Timeframe Format

Use hyphen format for pairs:

```json
// ✅ Correct
{"symbol": "BTC-USDT", "timeframe": "1h"}

// ❌ Wrong
{"symbol": "BTCUSDT", "timeframe": "1H"}
```

### 5. Date Format

Use `YYYY-MM-DD` string format:

```json
// ✅ Correct
{"start_date": "2023-01-01", "finish_date": "2024-01-01"}

// ❌ Wrong
{"start_date": "2023/01/01"}
```

### 6. Strategy Class Name

Must match class name exactly (case-sensitive):

```json
// If class is `MyStrategy`
{"strategy": "MyStrategy"}  // ✅
{"strategy": "mystrategy"}  // ❌
```
