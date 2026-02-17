## JESSE FRAMEWORK KNOWLEDGE

### Backtesting Engine
- Jesse's native backtesting capabilities with configurable timeframes
- Performance metrics calculation: Sharpe ratio, Sortino ratio, max drawdown, win rate
- Walk-forward analysis and out-of-sample testing

### Statistical Analysis
- Hypothesis testing for strategy improvements
- Bootstrap resampling for confidence intervals
- Correlation analysis with heatmap visualization

### Monte Carlo Simulation
- 10,000+ simulation runs for robustness testing and confidence interval analysis
- Distribution analysis of returns and risk metrics

### Performance Properties
- `self.metrics` - Access to complete backtest results
- `self.trades` - Trade-by-trade analysis data
- `self.daily_balances` - Portfolio value evolution for metrics calculation
- `self.position` - Position object with comprehensive trade information
- Methods: Access current position details for risk management and exit decisions
- `self.candles` - Returns all candles for current trading route
- Primary usage: Technical indicator calculations
- `self.get_candles(exchange: str, symbol: str, timeframe: str)` - Fetches candles for any exchange, symbol, and timeframe
- `self.price` - Current/closing price of current candle
- Alias: close_price, current_candle[2] - Usage: Entry/exit price calculations and indicator references
- `self.index` - Counter for strategy execution iterations
- Usage: Periodic actions, time-based exits, performance tracking
- Methods: before(), should_long(), go_long(), update_position(), liquidate() - Execution order: before() → filters → should_long/should_short → go_long/go_short → update_position() → after()

### Strategy Workflow on Every Candle
```
On every candle:
    before()
    if has_open_position:
        update_position() # update position including stop loss and take profit updates, or even liquidating position
    else:
        if has_active_orders:
            if should_cancel_entry():
                # cancels remaining orders automatically
        else:
            if should_long():
                go_long()
            if should_short():
                go_short()
            if filters_pass():
                submit_entry_orders()
    after()
```

### Debugging and Interactive Charts
- Debug Mode: Enable in backtest options for detailed logging
- Chart Methods: add_line_to_candle_chart(), add_horizontal_line_to_candle_chart(), add_extra_line_chart()
- Example Logging: self.log(f'Current PNL: {self.position.pnl_percentage}')
- Chart Usage: Visualize indicators, entry/exit points, support/resistance levels

### Hyperparameters and Optimization
- `hyperparameters()` method: Return list of parameter dictionaries
- Parameter Types: int, float, categorical
- Optimization Methods: Genetic algorithms, Bayesian optimization
- DNA Usage: Apply optimized parameter sets via dna() method
- Sequential vs current value access for indicators
- Proper validation period selection

### Example Strategy Structure
```python
class ExampleStrategy(Strategy):
    @property
    def sma(self):
        return ta.sma(self.candles, 20)
    
    def should_long(self) -> bool:
        return self.sma > self.candles[-2][2] # Price above 20-period SMA
    
    def go_long(self):
        entry = self.price
        stop = entry - ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(self.available_margin, 2, entry, stop)
        self.buy = qty, entry
```

### Backtesting Engine
- Jesse's native backtesting capabilities with configurable timeframes
- Performance metrics calculation: Sharpe ratio, Sortino ratio, max drawdown, win rate
- Walk-forward analysis and out-of-sample testing

### Statistical Analysis
- Hypothesis testing for strategy improvements
- Bootstrap resampling for confidence intervals
- Correlation analysis with heatmap visualization

### Monte Carlo Simulation
- 10,000+ simulation runs for robustness testing and confidence interval analysis
- Distribution analysis of returns and risk metrics

### Performance Properties
- `self.metrics` - Access to complete backtest results
- `self.trades` - Trade-by-trade analysis data
- `self.daily_balances` - Portfolio value evolution for metrics calculation
- `self.position` - Position object with comprehensive trade information
- Methods: Access current position details for risk management and exit decisions
- `self.candles` - Returns all candles for current trading route
- Primary usage: Technical indicator calculations
- `self.get_candles(exchange: str, symbol: str, timeframe: str)` - Fetches candles for any exchange, symbol, and timeframe
- `self.price` - Current/closing price of current candle
- Alias: close_price, current_candle[2] - Usage: Entry/exit price calculations and indicator references
- `self.index` - Counter for strategy execution iterations
- Usage: Periodic actions, time-based exits, performance tracking
- Methods: before(), should_long(), go_long(), update_position(), liquidate() - Execution order: before() → filters → should_long/should_short → go_long/go_short → update_position() → after()

### Strategy Workflow on Every Candle
```
On every candle:
    before()
    if has_open_position:
        update_position() # update position including stop loss and take profit updates, or even liquidating position
    else:
        if has_active_orders:
            if should_cancel_entry():
                # cancels remaining orders automatically
        else:
            if should_long():
                go_long()
            if should_short():
                go_short()
            if filters_pass():
                submit_entry_orders()
    after()
```

### Debugging and Interactive Charts
- Debug Mode: Enable in backtest options for detailed logging
- Chart Methods: add_line_to_candle_chart(), add_horizontal_line_to_candle_chart(), add_extra_line_chart()
- Example Logging: self.log(f'Current PNL: {self.position.pnl_percentage}')
- Chart Usage: Visualize indicators, entry/exit points, support/resistance levels

### Hyperparameters and Optimization
- `hyperparameters()` method: Return list of parameter dictionaries
- Parameter Types: int, float, categorical
- Optimization Methods: Genetic algorithms, Bayesian optimization
- DNA Usage: Apply optimized parameter sets via dna() method
- Sequential vs current value access for indicators
- Proper validation period selection

### Analysis Methods
- Regime detection using rolling windows
- Statistical significance testing (t-tests, chi-square)
- Performance attribution analysis

---

**Focus**: Transform subjective trading decisions into data-driven strategy selection through rigorous backtesting and statistical validation.