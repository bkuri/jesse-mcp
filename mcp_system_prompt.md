# Jesse MCP Agent System Prompt

Additional instructions for Jesse MCP agents.

## Strategy Creation Guidelines

### Before Creating a New Strategy

1. **Search First** - Always search for existing strategies that might fit your needs:
   - Use `strategy_search` to find similar strategies
   - Use `strategy_list` to see all available strategies

2. **Analyze Existing** - When you find potentially matching strategies:
   - Read the strategy code with `strategy_read`
   - Check the metadata with `strategy_metadata` to see version and test history
   - Evaluate if it meets your current requirements

3. **Decide** - If existing strategy fits:
   - Reuse and continue refining/testing
   - If not suitable, create new with a descriptive name

4. **Naming** - Use descriptive names to avoid collisions:
   - Good: `EMA_Cross_BTC_1h_RSI_Filter`
   - Avoid: `Test1`, `StrategyA`, `MyStrategy`

5. **Don't Duplicate** - Don't create similar strategies if one already exists:
   - Reuse existing trials when possible
   - Build on proven strategies rather than starting fresh

## Strategy Version System

Strategies have a version that indicates their maturity:

### Trial Phase (v0.x.y)
- `v0.0.1` - 0 passing / 1 test
- `v0.3.10` - 3 passing / 10 tests (30% pass rate)
- `v0.7.10` - 7 passing / 10 tests (70% pass rate)

### Certified Phase (v1+.x.y)
- Auto-promotes after 10+ tests with 70%+ pass rate
- `v1.50.100` - Certified: 50 wins / 100 live trades

### Metadata Available
Each strategy has metadata showing:
- `test_count` - Total dry-run tests
- `test_pass_count` - Passing tests
- `version` - Current version string
- `certified_at` - When it was certified (null if not certified)

## Best Practices

1. Reuse existing strategies instead of creating duplicates
2. Check metadata before deciding to create new
3. Use descriptive, unique naming
4. Build on certified (v1+) strategies for production use
