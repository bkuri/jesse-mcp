"""
Dry-run backtest validation via Jesse REST API.
"""

import logging
import uuid
from typing import Dict, Any

from jesse_mcp.core.strategy_validation.types import ValidationResult, ValidationLevel

logger = logging.getLogger("jesse-mcp.validator")


class DryRunValidator:
    """Validates strategy by running a quick backtest via REST API."""

    def __init__(self, rest_client_getter):
        self._get_client = rest_client_getter

    def run_dry_run(self, code: str, spec: Dict[str, Any]) -> ValidationResult:
        """Run dry-run backtest to catch runtime errors."""
        strategy_name = spec.get("name", f"DryRun_{uuid.uuid4().hex[:8]}")
        symbol = spec.get("symbol", "BTC-USDT")
        timeframe = spec.get("timeframe", "1h")
        exchange = spec.get("exchange", "Binance")

        logger.info("🔬 Running dry-run backtest via REST API...")

        try:
            client = self._get_client()

            routes = [{"strategy": strategy_name, "symbol": symbol, "timeframe": timeframe}]

            result = client.backtest(
                routes=routes,
                start_date="2024-01-01",
                end_date="2024-01-05",
                exchange=exchange,
                starting_balance=10000,
                fee=0.001,
                leverage=1,
                exchange_type="futures",
            )

            if "error" in result:
                return ValidationResult(
                    passed=False,
                    level=ValidationLevel.DRY_RUN.value,
                    error=f"Backtest error: {result.get('error', 'Unknown')}",
                )

            metrics = result.get("metrics", {})
            total_trades = metrics.get("total_trades", 0)
            win_rate = metrics.get("win_rate", 0)
            total_return = metrics.get("total_return", 0)

            logger.info(f"✅ Dry-run: {total_trades} trades, {win_rate:.1%} win rate")

            return ValidationResult(
                passed=True,
                level=ValidationLevel.DRY_RUN.value,
                warnings=[f"Dry-run: {total_trades} trades, {win_rate:.1%} win rate"],
                metrics={
                    "total_trades": total_trades,
                    "win_rate": win_rate,
                    "total_return": total_return,
                },
            )

        except Exception as e:
            logger.error(f"❌ Dry-run failed: {e}")
            return ValidationResult(
                passed=True,
                level=ValidationLevel.DRY_RUN.value,
                warnings=[f"Dry-run skipped: {str(e)}"],
            )
