from jesse.strategies import Strategy
import numpy as np


class SmaCrossover(Strategy):
    """
    Simple Moving Average Crossover Strategy
    Goes long when fast EMA crosses above slow EMA
    Goes short when fast EMA crosses below slow EMA
    """

    def __init__(self):
        super().__init__()
        self.ema_fast = 10
        self.ema_slow = 30
        self.position_size = 0.02  # 2% of portfolio
        self.stop_loss_pct = 0.02  # 2% stop loss
        self.take_profit_pct = 0.04  # 4% take profit

    def hyperparameters(self):
        return [
            {"name": "ema_fast", "default": 10, "min": 5, "max": 20},
            {"name": "ema_slow", "default": 30, "min": 20, "max": 50},
            {"name": "position_size", "default": 0.02, "min": 0.01, "max": 0.1},
            {"name": "stop_loss_pct", "default": 0.02, "min": 0.01, "max": 0.05},
            {"name": "take_profit_pct", "default": 0.04, "min": 0.02, "max": 0.1},
        ]

    def should_long(self) -> bool:
        if len(self.candles) < self.ema_slow:
            return False

        fast_ema = self._calculate_ema(self.ema_fast)
        slow_ema = self._calculate_ema(self.ema_slow)

        # Buy signal when fast EMA crosses above slow EMA
        return fast_ema[-1] > slow_ema[-1] and fast_ema[-2] <= slow_ema[-2]

    def should_short(self) -> bool:
        if len(self.candles) < self.ema_slow:
            return False

        fast_ema = self._calculate_ema(self.ema_fast)
        slow_ema = self._calculate_ema(self.ema_slow)

        # Sell signal when fast EMA crosses below slow EMA
        return fast_ema[-1] < slow_ema[-1] and fast_ema[-2] >= slow_ema[-2]

    def go_long(self):
        qty = self.balance * self.position_size / self.close
        self.buy = qty, self.price
        self.stop_loss = qty, self.price * (1 - self.stop_loss_pct)
        self.take_profit = qty, self.price * (1 + self.take_profit_pct)

    def go_short(self):
        qty = self.balance * self.position_size / self.close
        self.sell = qty, self.price
        self.stop_loss = qty, self.price * (1 + self.stop_loss_pct)
        self.take_profit = qty, self.price * (1 - self.take_profit_pct)

    def should_cancel_entry(self):
        return True

    def _calculate_ema(self, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        if len(self.candles) < period:
            return np.full(len(self.candles), np.nan)

        close_prices = self.candles[:, 2]  # Close prices are at index 2
        ema = np.zeros(len(close_prices))
        ema[0] = close_prices[0]

        multiplier = 2 / (period + 1)

        for i in range(1, len(close_prices)):
            if not np.isnan(close_prices[i]):
                ema[i] = (close_prices[i] - ema[i - 1]) * multiplier + ema[i - 1]
            else:
                ema[i] = ema[i - 1]

        return ema

    def update_position(self):
        # Close long position if short signal appears
        if self.is_long and self.should_short():
            self.liquidate()
        # Close short position if long signal appears
        elif self.is_short and self.should_long():
            self.liquidate()
