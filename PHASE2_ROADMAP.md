# Jesse MCP - Phase 2 Implementation Roadmap

**Status**: Ready to begin  
**Location**: `~/source/jesse-mcp/`  
**Git History**: 3 commits with full history

## Phase 2: Real Jesse Integration

### Objectives
1. Integrate with Jesse's research module
2. Implement real backtest functionality
3. Add strategy management (read/write/validate)
4. Add candle data operations

### Implementation Order

#### 2.1 Jesse Integration Layer (Day 1)
- [ ] Create `jesse_integration.py` module
  - Import Jesse research module safely
  - Wrapper functions for common operations
  - Error handling and validation
  
**Key files to create:**
```python
# jesse_integration.py
from jesse import research
from jesse.strategies import Strategy
import jesse.helpers as jh

class JesseWrapper:
    """Wrapper around Jesse for MCP operations"""
    def __init__(self):
        self.jesse_path = '/srv/containers/jesse'  # or /mnt/nfs/server1/containers/jesse
        
    def backtest(self, ...):
        """Run backtest via research module"""
    
    def get_strategy(self, name):
        """Get strategy source code"""
    
    def list_strategies(self):
        """List available strategies"""
```

#### 2.2 Real Backtest Tool (Day 1-2)
- [ ] Replace `handle_backtest` placeholder with real implementation
- [ ] Parse backtest config from arguments
- [ ] Call `research.backtest()` 
- [ ] Format metrics response
- [ ] Handle errors gracefully

**Example implementation:**
```python
async def handle_backtest(args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        jesse_wrapper = JesseWrapper()
        
        config = {
            'starting_balance': args.get('starting_balance', 10000),
            'fee': args.get('fee', 0.001),
            'type': args.get('exchange_type', 'futures'),
            'futures_leverage': args.get('leverage', 1),
            'exchange': args.get('exchange', 'Binance'),
            'warm_up_candles': 240
        }
        
        routes = [{
            'exchange': args.get('exchange', 'Binance'),
            'strategy': args['strategy'],
            'symbol': args['symbol'],
            'timeframe': args['timeframe']
        }]
        
        # Get candles
        candles = jesse_wrapper.get_candles(
            exchange=config['exchange'],
            symbol=args['symbol'],
            timeframe=args['timeframe'],
            start_date=args['start_date'],
            end_date=args['end_date']
        )
        
        # Run backtest
        result = research.backtest(
            config=config,
            routes=routes,
            candles=candles,
            hyperparameters=args.get('hyperparameters'),
            generate_equity_curve=args.get('include_equity_curve', False),
            generate_trades=args.get('include_trades', False)
        )
        
        return result
        
    except Exception as e:
        return {"error": f"Backtest failed: {str(e)}"}
```

#### 2.3 Strategy Management Tools (Day 2)
- [ ] Implement `handle_strategy_list`
- [ ] Implement `handle_strategy_read`
- [ ] Implement `handle_strategy_validate`
- [ ] Add strategy file parsing

**Operations:**
- Scan `/srv/containers/jesse/strategies/` directory
- Parse Python class structure
- Extract hyperparameters
- Validate syntax before saving

#### 2.4 Candle Data Management (Day 2-3)
- [ ] Implement `candles_import` tool
- [ ] Implement `candles_available` tool
- [ ] Add date range checking
- [ ] Detect gaps in data

**Operations:**
- List available data ranges per symbol/exchange
- Import new candle data from exchanges via `research.import_candles()`
- Check for gaps or missing data

**Supported Exchanges:**
- Binance
- Bitfinex
- Bybit
- Coinbase
- Gate
- Hyperliquid
- Apex

**Implementation Note:**
Jesse already has `research.import_candles()` which downloads directly from exchange APIs:
```python
from jesse import research

result = research.import_candles(
    exchange='Binance',
    symbol='BTC-USDT',
    start_date='2023-01-01',
    show_progressbar=False  # Set to False for MCP
)
```

This means the MCP server CAN autonomously download new candle ranges!

#### 2.5 Testing & Validation (Day 3)
- [ ] Update test suite for real operations
- [ ] Add integration tests
- [ ] Test with actual Jesse container
- [ ] Validate all metrics formatting

### Key Dependencies
- Jesse research module (already available)
- Jesse strategies directory structure
- Jesse database connectivity
- NumPy for data handling
- Pandas for data analysis

### Success Criteria
- ✅ Real backtest returns complete metrics
- ✅ Strategy operations work on actual files
- ✅ Candle data operations functional
- ✅ All error cases handled gracefully
- ✅ Test suite passes with real Jesse
- ✅ Git commits clean and documented

### Next Steps After Phase 2
- Phase 3: Optimization tools (optimize, walk_forward)
- Phase 4: Analysis tools (analyze_results, metrics)
- Phase 5: Monte Carlo & Pairs Trading
- Phase 6: Autonomous workflows
- Phase 7-8: Polish & Production deployment

### Notes
- Jesse is already deployed at `/srv/containers/jesse`
- Alternative mount at `/mnt/nfs/server1/containers/jesse`
- Test data available for 2023 in container
- All tools should be stateless and reusable
