"""
Enhanced SMA Crossover Strategy with Risk Management
Agent A Strategy Development Implementation
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import json


class EnhancedSMAStrategy:
    """
    Enhanced Simple Moving Average Crossover Strategy with advanced risk management
    and optimization capabilities for Agent A development workflow.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy with configuration parameters

        Args:
            config: Strategy configuration dictionary
        """
        # Default configuration
        self.config = config or self._get_default_config()

        # Strategy parameters
        self.sma_fast = self.config.get("sma_fast", 20)
        self.sma_slow = self.config.get("sma_slow", 50)
        self.signal_threshold = self.config.get("signal_threshold", 0.001)

        # Risk management parameters
        self.position_size = self.config.get("position_size", 0.02)
        self.stop_loss_pct = self.config.get("stop_loss_pct", 0.02)
        self.take_profit_pct = self.config.get("take_profit_pct", 0.04)
        self.max_drawdown = self.config.get("max_drawdown", 0.15)
        self.leverage = self.config.get("leverage", 1.0)

        # Additional filters
        self.volume_filter = self.config.get("volume_filter", True)
        self.volatility_filter = self.config.get("volatility_filter", True)
        self.trend_filter = self.config.get("trend_filter", True)

        # State tracking
        self.current_position = None
        self.entry_price = None
        self.unrealized_pnl = 0.0
        self.peak_equity = 0.0
        self.current_drawdown = 0.0

        # Performance tracking
        self.trades = []
        self.equity_curve = []
        self.signals_generated = []

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default strategy configuration"""
        return {
            "sma_fast": 20,
            "sma_slow": 50,
            "signal_threshold": 0.001,
            "position_size": 0.02,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.04,
            "max_drawdown": 0.15,
            "leverage": 1.0,
            "volume_filter": True,
            "volatility_filter": True,
            "trend_filter": True,
            "min_volume_periods": 20,
            "volatility_threshold": 0.02,
            "trend_lookback": 100,
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        """
        Validate strategy parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.sma_fast >= self.sma_slow:
            return False, "Fast SMA period must be less than slow SMA period"

        if self.sma_fast < 5 or self.sma_slow > 200:
            return False, "SMA periods out of reasonable range (5-200)"

        if self.position_size <= 0 or self.position_size > 0.1:
            return False, "Position size must be between 0 and 10%"

        if self.stop_loss_pct <= 0 or self.stop_loss_pct > 0.1:
            return False, "Stop loss must be between 0 and 10%"

        if self.take_profit_pct <= 0 or self.take_profit_pct > 0.2:
            return False, "Take profit must be between 0 and 20%"

        return True, "Parameters valid"

    def calculate_indicators(self, candles: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Calculate technical indicators

        Args:
            candles: OHLCV candle data

        Returns:
            Dictionary with calculated indicators
        """
        if len(candles) < max(self.sma_slow, 100):
            return {}

        close_prices = candles[:, 4]
        volumes = candles[:, 5] if candles.shape[1] > 5 else np.ones(len(close_prices))
        high_prices = candles[:, 2]
        low_prices = candles[:, 3]

        indicators = {}

        # SMAs
        indicators["sma_fast"] = self._calculate_sma(close_prices, self.sma_fast)
        indicators["sma_slow"] = self._calculate_sma(close_prices, self.sma_slow)

        # Volume indicators
        if self.volume_filter:
            indicators["volume_sma"] = self._calculate_sma(volumes, 20)
            indicators["volume_ratio"] = volumes / indicators["volume_sma"]

        # Volatility indicators
        if self.volatility_filter:
            indicators["atr"] = self._calculate_atr(
                high_prices, low_prices, close_prices, 14
            )
            indicators["volatility"] = indicators["atr"] / close_prices

        # Trend indicators
        if self.trend_filter:
            indicators["trend_sma"] = self._calculate_sma(close_prices, 100)
            indicators["price_vs_trend"] = (
                close_prices - indicators["trend_sma"]
            ) / indicators["trend_sma"]

        return indicators

    def generate_signals(self, candles: np.ndarray) -> Dict[str, Any]:
        """
        Generate trading signals based on indicators

        Args:
            candles: OHLCV candle data

        Returns:
            Signal dictionary with recommendation and confidence
        """
        indicators = self.calculate_indicators(candles)

        if not indicators:
            return {"action": "hold", "confidence": 0.0, "reason": "Insufficient data"}

        current_price = candles[-1, 4]

        # Basic SMA crossover signal
        sma_fast_current = indicators["sma_fast"][-1]
        sma_slow_current = indicators["sma_slow"][-1]
        sma_fast_prev = (
            indicators["sma_fast"][-2]
            if len(indicators["sma_fast"]) > 1
            else sma_fast_current
        )
        sma_slow_prev = (
            indicators["sma_slow"][-2]
            if len(indicators["sma_slow"]) > 1
            else sma_slow_current
        )

        # Detect crossover
        bullish_crossover = (sma_fast_prev <= sma_slow_prev) and (
            sma_fast_current > sma_slow_current
        )
        bearish_crossover = (sma_fast_prev >= sma_slow_prev) and (
            sma_fast_current < sma_slow_current
        )

        # Calculate signal strength
        signal_strength = abs(sma_fast_current - sma_slow_current) / sma_slow_current

        # Apply filters
        filter_passed = self._apply_filters(candles, indicators)

        # Risk check
        risk_ok = self._check_risk_constraints()

        if not filter_passed:
            return {"action": "hold", "confidence": 0.0, "reason": "Filters not passed"}

        if not risk_ok:
            return {
                "action": "hold",
                "confidence": 0.0,
                "reason": "Risk constraints violated",
            }

        # Generate signal
        if bullish_crossover and signal_strength > self.signal_threshold:
            return {
                "action": "long",
                "confidence": min(signal_strength * 100, 95.0),
                "reason": f"Bullish SMA crossover (strength: {signal_strength:.4f})",
            }
        elif bearish_crossover and signal_strength > self.signal_threshold:
            return {
                "action": "short",
                "confidence": min(signal_strength * 100, 95.0),
                "reason": f"Bearish SMA crossover (strength: {signal_strength:.4f})",
            }

        return {"action": "hold", "confidence": 0.0, "reason": "No clear signal"}

    def _apply_filters(
        self, candles: np.ndarray, indicators: Dict[str, np.ndarray]
    ) -> bool:
        """Apply additional filters to signals"""
        current_idx = len(candles) - 1

        # Volume filter
        if self.volume_filter and "volume_ratio" in indicators:
            if indicators["volume_ratio"][current_idx] < 1.2:
                return False

        # Volatility filter
        if self.volatility_filter and "volatility" in indicators:
            if indicators["volatility"][current_idx] < self.config.get(
                "volatility_threshold", 0.02
            ):
                return False

        # Trend filter
        if self.trend_filter and "price_vs_trend" in indicators:
            trend_lookback = self.config.get("trend_lookback", 100)
            if current_idx >= trend_lookback:
                trend_direction = np.mean(
                    indicators["price_vs_trend"][-trend_lookback:]
                )
                if abs(trend_direction) < 0.01:  # Weak trend
                    return False

        return True

    def _check_risk_constraints(self) -> bool:
        """Check if current position meets risk constraints"""
        if self.current_drawdown > self.max_drawdown:
            return False

        return True

    def execute_trade(
        self, signal: Dict[str, Any], current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Execute trade based on signal

        Args:
            signal: Trading signal
            current_price: Current price

        Returns:
            Trade execution details or None
        """
        if signal["action"] == "hold":
            return None

        trade = {
            "action": signal["action"],
            "price": current_price,
            "size": self.position_size,
            "stop_loss": None,
            "take_profit": None,
            "confidence": signal["confidence"],
            "reason": signal["reason"],
            "timestamp": datetime.now().isoformat(),
        }

        if signal["action"] == "long":
            trade["stop_loss"] = current_price * (1 - self.stop_loss_pct)
            trade["take_profit"] = current_price * (1 + self.take_profit_pct)
        elif signal["action"] == "short":
            trade["stop_loss"] = current_price * (1 + self.stop_loss_pct)
            trade["take_profit"] = current_price * (1 - self.take_profit_pct)

        # Update position tracking
        self.current_position = signal["action"]
        self.entry_price = current_price

        # Record trade
        self.trades.append(trade)

        return trade

    def update_position(self, current_price: float) -> Optional[Dict[str, Any]]:
        """
        Update existing position and check for exit conditions

        Args:
            current_price: Current price

        Returns:
            Exit signal or None
        """
        if self.current_position is None or self.entry_price is None:
            return None

        # Calculate unrealized P&L
        if self.current_position == "long":
            self.unrealized_pnl = (current_price - self.entry_price) / self.entry_price
        else:  # short
            self.unrealized_pnl = (self.entry_price - current_price) / self.entry_price

        # Check exit conditions
        exit_signal = None

        if self.current_position == "long":
            if current_price <= self.entry_price * (1 - self.stop_loss_pct):
                exit_signal = {
                    "action": "exit_long",
                    "reason": "Stop loss hit",
                    "price": current_price,
                }
            elif current_price >= self.entry_price * (1 + self.take_profit_pct):
                exit_signal = {
                    "action": "exit_long",
                    "reason": "Take profit hit",
                    "price": current_price,
                }
        else:  # short
            if current_price >= self.entry_price * (1 + self.stop_loss_pct):
                exit_signal = {
                    "action": "exit_short",
                    "reason": "Stop loss hit",
                    "price": current_price,
                }
            elif current_price <= self.entry_price * (1 - self.take_profit_pct):
                exit_signal = {
                    "action": "exit_short",
                    "reason": "Take profit hit",
                    "price": current_price,
                }

        # Update drawdown
        self._update_drawdown(current_price)

        return exit_signal

    def _update_drawdown(self, current_price: float):
        """Update maximum drawdown tracking"""
        if self.current_position and self.entry_price:
            current_equity = self.entry_price * (1 + self.unrealized_pnl)

            if current_equity > self.peak_equity:
                self.peak_equity = current_equity

            self.current_drawdown = (
                self.peak_equity - current_equity
            ) / self.peak_equity

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate and return performance metrics"""
        if not self.trades:
            return {}

        total_trades = len(self.trades)
        winning_trades = sum(1 for trade in self.trades if trade.get("pnl", 0) > 0)

        metrics = {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": total_trades - winning_trades,
            "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
            "current_drawdown": self.current_drawdown,
            "max_drawdown": self.max_drawdown,
            "leverage": self.leverage,
            "position_size": self.position_size,
        }

        return metrics

    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        sma = np.full(len(prices), np.nan)
        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1 : i + 1])
        return sma

    def _calculate_atr(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int
    ) -> np.ndarray:
        """Calculate Average True Range"""
        tr = np.zeros(len(high))

        for i in range(1, len(high)):
            high_low = high[i] - low[i]
            high_close = abs(high[i] - close[i - 1])
            low_close = abs(low[i] - close[i - 1])
            tr[i] = max(high_low, high_close, low_close)

        atr = np.full(len(tr), np.nan)
        for i in range(period, len(tr)):
            atr[i] = np.mean(tr[i - period + 1 : i + 1])

        return atr

    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy state to dictionary"""
        return {
            "config": self.config,
            "current_position": self.current_position,
            "entry_price": self.entry_price,
            "unrealized_pnl": self.unrealized_pnl,
            "peak_equity": self.peak_equity,
            "current_drawdown": self.current_drawdown,
            "trades": self.trades,
            "performance_metrics": self.get_performance_metrics(),
        }

    def save_state(self, filepath: str):
        """Save strategy state to file"""
        state = self.to_dict()
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self, filepath: str):
        """Load strategy state from file"""
        with open(filepath, "r") as f:
            state = json.load(f)

        self.config = state.get("config", self._get_default_config())
        self.current_position = state.get("current_position")
        self.entry_price = state.get("entry_price")
        self.unrealized_pnl = state.get("unrealized_pnl", 0.0)
        self.peak_equity = state.get("peak_equity", 0.0)
        self.current_drawdown = state.get("current_drawdown", 0.0)
        self.trades = state.get("trades", [])
