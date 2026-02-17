"""
Jesse-compatible Enhanced SMA Strategy
Optimized for Agent A development workflow
"""

from jesse import utils
from jesse.strategies import Strategy
import numpy as np


class EnhancedSMA(Strategy):
    """
    Enhanced Simple Moving Average Crossover Strategy with advanced risk management
    Jesse-compatible implementation for Agent A optimization
    """

    def __init__(self):
        super().__init__()

        # Strategy parameters
        self.sma_fast = self.hp("sma_fast", 20)
        self.sma_slow = self.hp("sma_slow", 50)
        self.signal_threshold = self.hp("signal_threshold", 0.001)

        # Risk management parameters
        self.position_size = self.hp("position_size", 0.02)
        self.stop_loss_pct = self.hp("stop_loss_pct", 0.02)
        self.take_profit_pct = self.hp("take_profit_pct", 0.04)

        # Additional filters
        self.volume_filter = self.hp("volume_filter", True)
        self.volatility_filter = self.hp("volatility_filter", True)
        self.trend_filter = self.hp("trend_filter", True)

        # State tracking
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None

    def hyperparameters(self):
        """Define hyperparameter space for optimization"""
        return [
            ("sma_fast", int, 10, 30),
            ("sma_slow", int, 40, 100),
            ("signal_threshold", float, 0.0005, 0.005),
            ("position_size", float, 0.01, 0.05),
            ("stop_loss_pct", float, 0.01, 0.05),
            ("take_profit_pct", float, 0.02, 0.08),
            ("volume_filter", bool, [True, False]),
            ("volatility_filter", bool, [True, False]),
            ("trend_filter", bool, [True, False]),
        ]

    def should_long(self) -> bool:
        """Check if we should enter a long position"""
        if len(self.candles) < self.sma_slow:
            return False

        # Calculate SMAs
        sma_fast = self.sma(self.sma_fast)
        sma_slow = self.sma(self.sma_slow)

        # Detect bullish crossover
        if sma_fast[-1] > sma_slow[-1] and sma_fast[-2] <= sma_slow[-2]:
            # Calculate signal strength
            signal_strength = abs(sma_fast[-1] - sma_slow[-1]) / sma_slow[-1]

            if signal_strength > self.signal_threshold:
                # Apply filters
                if self._apply_filters():
                    return True

        return False

    def should_short(self) -> bool:
        """Check if we should enter a short position"""
        if len(self.candles) < self.sma_slow:
            return False

        # Calculate SMAs
        sma_fast = self.sma(self.sma_fast)
        sma_slow = self.sma(self.sma_slow)

        # Detect bearish crossover
        if sma_fast[-1] < sma_slow[-1] and sma_fast[-2] >= sma_slow[-2]:
            # Calculate signal strength
            signal_strength = abs(sma_fast[-1] - sma_slow[-1]) / sma_slow[-1]

            if signal_strength > self.signal_threshold:
                # Apply filters
                if self._apply_filters():
                    return True

        return False

    def should_cancel(self) -> bool:
        """Check if we should cancel existing orders"""
        return False

    def go_long(self):
        """Execute long position"""
        # Calculate position size based on risk
        qty = utils.size_to_qty(self.position_size, self.price, self.fee_rate)

        # Set stop loss and take profit
        self.entry_price = self.price
        self.stop_loss = self.price * (1 - self.stop_loss_pct)
        self.take_profit = self.price * (1 + self.take_profit_pct)

        # Place order
        self.buy = qty, self.price
        self.stop_loss = qty, self.stop_loss
        self.take_profit = qty, self.take_profit

    def go_short(self):
        """Execute short position"""
        # Calculate position size based on risk
        qty = utils.size_to_qty(self.position_size, self.price, self.fee_rate)

        # Set stop loss and take profit
        self.entry_price = self.price
        self.stop_loss = self.price * (1 + self.stop_loss_pct)
        self.take_profit = self.price * (1 - self.take_profit_pct)

        # Place order
        self.sell = qty, self.price
        self.stop_loss = qty, self.stop_loss
        self.take_profit = qty, self.take_profit

    def _apply_filters(self) -> bool:
        """Apply additional filters to signals"""
        current_candle = self.candles[-1]

        # Volume filter
        if self.volume_filter:
            volume_sma = self.sma(20, source="volume")
            if current_candle[5] < volume_sma[-1] * 1.2:  # Volume below 1.2x average
                return False

        # Volatility filter
        if self.volatility_filter:
            atr = self.atr(14)
            volatility = atr[-1] / self.price
            if volatility < 0.02:  # Low volatility
                return False

        # Trend filter
        if self.trend_filter:
            trend_sma = self.sma(100)
            if abs(self.price - trend_sma[-1]) / trend_sma[-1] < 0.01:  # Weak trend
                return False

        return True

    def update_position(self):
        """Update existing position logic if needed"""
        # Position updates are handled by Jesse's built-in stop loss/take profit
        pass

    def on_route_open_position(self, strategy):
        """Called when position is opened"""
        pass

    def on_route_close_position(self, strategy):
        """Called when position is closed"""
        pass

    def on_route_canceled(self, strategy):
        """Called when route is canceled"""
        pass

    def terminate(self):
        """Called when strategy is terminated"""
        pass
