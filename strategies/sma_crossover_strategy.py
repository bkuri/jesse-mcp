# Simple Moving Average Crossover Strategy
import numpy as np
from typing import Dict, Any


class SMACrossoverStrategy:
    def __init__(self, exchange: str, symbol: str, timeframe: str):
        self.exchange = exchange
        self.symbol = symbol
        self.timeframe = timeframe

        # Strategy parameters
        self.ema_fast = 10
        self.ema_slow = 30
        self.position_size = 0.02  # 2% of portfolio
        self.stop_loss = 0.02  # 2% stop loss
        self.take_profit = 0.04  # 4% take profit

    def should_long(self, candles: np.ndarray) -> bool:
        """Check if we should enter a long position"""
        if len(candles) < self.ema_slow:
            return False

        # Calculate EMAs
        close_prices = candles[:, 4]  # Close prices
        ema_fast = self._calculate_ema(close_prices, self.ema_fast)
        ema_slow = self._calculate_ema(close_prices, self.ema_slow)

        # Buy signal when fast EMA crosses above slow EMA
        return ema_fast[-1] > ema_slow[-1]

    def should_short(self, candles: np.ndarray) -> bool:
        """Check if we should enter a short position"""
        if len(candles) < self.ema_slow:
            return False

        # Calculate EMAs
        close_prices = candles[:, 4]  # Close prices
        ema_fast = self._calculate_ema(close_prices, self.ema_fast)
        ema_slow = self._calculate_ema(close_prices, self.ema_slow)

        # Sell signal when fast EMA crosses below slow EMA
        return ema_fast[-1] < ema_slow[-1]

    def should_cancel(self, candles: np.ndarray) -> bool:
        """Check if we should cancel existing orders"""
        return False

    def go_long(self, candles: np.ndarray) -> Dict[str, Any]:
        """Execute long position"""
        return {
            "type": "market",
            "size": self.position_size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
        }

    def go_short(self, candles: np.ndarray) -> Dict[str, Any]:
        """Execute short position"""
        return {
            "type": "market",
            "size": self.position_size,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
        }

    def update_position(self, candles: np.ndarray, position: Dict[str, Any]) -> None:
        """Update existing position"""
        if position["type"] == "long":
            if self.should_short(candles):
                # Close long position
                position["size"] = 0
        elif position["type"] == "short":
            if self.should_long(candles):
                # Close short position
                position["size"] = 0

    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.full(len(prices), np.nan)

        ema = np.zeros(len(prices))
        ema[0] = prices[0]

        multiplier = 2 / (period + 1)

        for i in range(1, len(prices)):
            if not np.isnan(prices[i]):
                ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1]
            else:
                ema[i] = ema[i - 1]

        return ema
