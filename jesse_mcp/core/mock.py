"""
Mock Jesse Integration Layer for Development and Testing

Provides realistic mock implementations of Jesse functionality without requiring
the full Jesse framework to be installed. This enables development and testing
of Phase 3 optimization tools without complex dependencies.
"""

import random
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("jesse-mcp.mock")


class MockJesseWrapper:
    """Mock implementation of JesseWrapper for development testing"""

    def __init__(self):
        self.mock_strategies = [
            "SimpleMovingAverage",
            "RSIMeanReversion",
            "MACrossStrategy",
            "BollingerBands",
            "GridTrading",
        ]

        self.mock_exchanges = [
            "Binance",
            "Coinbase",
            "Bybit",
            "Gate",
            "Hyperliquid",
            "Bitfinex",
            "Apex",
        ]

        self.mock_symbols = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "ADA-USDT", "DOT-USDT"]

        self.mock_timeframes = ["1m", "5m", "15m", "1h", "4h", "1D"]

        # Seed for reproducible results
        np.random.seed(42)
        random.seed(42)

    def backtest(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Mock backtest implementation that returns realistic results
        """
        logger.info(f"Mock backtest: {strategy_name} on {symbol} {timeframe}")

        # Simulate processing time
        time.sleep(0.1)

        # Generate realistic mock results
        days = (
            datetime.strptime(end_date, "%Y-%m-%d")
            - datetime.strptime(start_date, "%Y-%m-%d")
        ).days

        # Base performance varies by strategy
        strategy_performance = {
            "SimpleMovingAverage": 0.15,
            "RSIMeanReversion": 0.12,
            "MACrossStrategy": 0.18,
            "BollingerBands": 0.14,
            "GridTrading": 0.08,
        }

        base_return = strategy_performance.get(strategy_name, 0.10)

        # Add some randomness
        total_return = base_return + np.random.normal(0, 0.05)
        sharpe_ratio = np.random.normal(1.2, 0.3)
        max_drawdown = abs(np.random.normal(0.15, 0.05))
        win_rate = np.random.normal(0.55, 0.1)

        # Generate mock trades
        num_trades = int(days * np.random.uniform(0.5, 2.0))
        trades = self._generate_mock_trades(num_trades, win_rate)

        # Generate mock equity curve
        equity_curve = self._generate_mock_equity_curve(
            days, total_return, max_drawdown
        )

        return {
            "strategy": strategy_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "total_return": round(total_return, 4),
            "sharpe_ratio": round(sharpe_ratio, 4),
            "max_drawdown": round(max_drawdown, 4),
            "win_rate": round(win_rate, 4),
            "total_trades": num_trades,
            "trades": trades,
            "equity_curve": equity_curve,
            "starting_balance": kwargs.get("starting_balance", 10000),
            "ending_balance": round(10000 * (1 + total_return), 2),
            "execution_time": round(np.random.uniform(0.5, 2.0), 2),
        }

    def list_strategies(self) -> List[str]:
        """Return list of available mock strategies"""
        return self.mock_strategies.copy()

    def read_strategy(self, strategy_name: str) -> str:
        """Return mock strategy code"""
        mock_code = f"""
# Mock Strategy: {strategy_name}
# This is a simulated strategy implementation for testing

class {strategy_name}:
    def __init__(self):
        self.name = "{strategy_name}"
        self.timeframe = "1h"
        
    def should_long(self):
        # Mock logic for long signals
        return True
        
    def should_short(self):
        # Mock logic for short signals  
        return False
        
    def update_position(self):
        # Mock position management
        pass
        
    def should_cancel(self):
        # Mock exit logic
        return False
"""
        return mock_code.strip()

    def validate_strategy(self, strategy_code: str) -> Dict[str, Any]:
        """Mock strategy validation"""
        # Simulate validation time
        time.sleep(0.05)

        # Basic syntax check
        try:
            compile(strategy_code, "<string>", "exec")
            syntax_valid = True
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax Error: {str(e)}",
                "line": e.lineno if hasattr(e, "lineno") else None,
            }

        # Mock additional validation
        has_class = "class " in strategy_code
        has_methods = any(
            method in strategy_code for method in ["should_long", "should_short"]
        )

        if not has_class:
            return {
                "valid": False,
                "error": "Strategy must contain a class definition",
                "line": None,
            }

        if not has_methods:
            return {
                "valid": False,
                "error": "Strategy must implement required methods (should_long, should_short)",
                "line": None,
            }

        return {
            "valid": True,
            "error": None,
            "line": None,
            "warnings": [
                "Using mock validation - real Jesse validation may be stricter"
            ],
        }

    def import_candles(
        self, exchange: str, symbol: str, timeframe: str, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Mock candle import"""
        logger.info(f"Mock import: {exchange} {symbol} {timeframe}")

        # Simulate download time
        time.sleep(0.2)

        # Calculate number of candles
        days = (
            datetime.strptime(end_date, "%Y-%m-%d")
            - datetime.strptime(start_date, "%Y-%m-%d")
        ).days

        timeframe_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "1h": 60,
            "4h": 240,
            "1D": 1440,
        }
        minutes = timeframe_minutes.get(timeframe, 60)
        num_candles = int((days * 24 * 60) / minutes)

        # Generate mock candle data
        base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100
        candles = self._generate_mock_candles(num_candles, base_price)

        return {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "candles_imported": len(candles),
            "file_path": f"/mock/data/{exchange}/{symbol}-{timeframe}.csv",
            "file_size_mb": round(len(candles) * 0.0001, 2),
            "download_time": round(np.random.uniform(1.0, 5.0), 2),
        }

    def _generate_mock_trades(
        self, num_trades: int, win_rate: float
    ) -> List[Dict[str, Any]]:
        """Generate realistic mock trades"""
        trades = []
        for i in range(num_trades):
            is_win = random.random() < win_rate

            if is_win:
                pnl = round(np.random.uniform(0.5, 3.0), 2)
                entry_price = round(np.random.uniform(100, 1000), 2)
                exit_price = round(entry_price * (1 + pnl / 100), 2)
            else:
                pnl = round(np.random.uniform(-2.0, -0.5), 2)
                entry_price = round(np.random.uniform(100, 1000), 2)
                exit_price = round(entry_price * (1 + pnl / 100), 2)

            trade_date = datetime.now() - timedelta(days=random.randint(1, 365))

            trades.append(
                {
                    "id": i + 1,
                    "entry_date": trade_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "exit_date": (
                        trade_date + timedelta(hours=random.randint(1, 48))
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "quantity": round(np.random.uniform(0.1, 2.0), 4),
                    "pnl": pnl,
                    "pnl_percent": pnl,
                    "type": random.choice(["long", "short"]),
                    "fee": round(abs(entry_price * 0.001), 4),
                }
            )

        return trades

    def _generate_mock_equity_curve(
        self, days: int, total_return: float, max_drawdown: float
    ) -> List[Dict[str, Any]]:
        """Generate realistic mock equity curve"""
        equity_points = []
        current_equity = 10000
        peak_equity = 10000

        # Generate daily equity points
        for day in range(days + 1):
            # Add some daily volatility
            daily_return = np.random.normal(total_return / days, 0.02)
            current_equity *= 1 + daily_return

            # Track peak for drawdown calculation
            if current_equity > peak_equity:
                peak_equity = current_equity

            # Calculate current drawdown
            current_drawdown = (peak_equity - current_equity) / peak_equity

            equity_points.append(
                {
                    "date": (datetime.now() - timedelta(days=days - day)).strftime(
                        "%Y-%m-%d"
                    ),
                    "equity": round(current_equity, 2),
                    "return": round(daily_return * 100, 4),
                    "drawdown": round(current_drawdown * 100, 4),
                }
            )

        return equity_points

    def _generate_mock_candles(
        self, num_candles: int, base_price: float
    ) -> List[Dict[str, Any]]:
        """Generate realistic mock candle data"""
        candles = []
        current_price = base_price

        for i in range(num_candles):
            # Generate OHLC with some randomness
            open_price = current_price
            high_price = open_price * (1 + np.random.uniform(0, 0.02))
            low_price = open_price * (1 - np.random.uniform(0, 0.02))
            close_price = open_price + np.random.normal(0, base_price * 0.001)
            volume = np.random.uniform(100, 10000)

            # Ensure OHLC relationships are valid
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            candles.append(
                {
                    "timestamp": int(
                        (
                            datetime.now() - timedelta(minutes=num_candles - i)
                        ).timestamp()
                    ),
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": round(volume, 2),
                }
            )

            current_price = close_price

        return candles


# Mock wrapper instance for testing
mock_wrapper = MockJesseWrapper()


def get_mock_jesse_wrapper():
    """Get mock Jesse wrapper instance"""
    return mock_wrapper
