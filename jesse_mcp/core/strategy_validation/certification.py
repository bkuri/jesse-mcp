"""
Strategy certification utilities.

Provides functions to decode version strings and check certification status
without requiring metadata.json to exist.
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import Optional

from jesse_mcp.core.strategy_validation.metadata import (
    CERTIFICATION_MIN_TESTS,
    CERTIFICATION_PASS_RATE,
)

logger = logging.getLogger("jesse-mcp.certification")


@dataclass
class CertificationStatus:
    """Decoded certification status from version string."""

    is_certified: bool
    certification_level: int
    test_count: int
    test_pass_count: int
    live_trade_count: int
    live_win_count: int
    pass_rate: float

    @property
    def has_enough_tests(self) -> bool:
        return self.test_count >= CERTIFICATION_MIN_TESTS

    @property
    def meets_pass_rate(self) -> bool:
        return self.pass_rate >= CERTIFICATION_PASS_RATE

    @property
    def should_certify(self) -> bool:
        return self.has_enough_tests and self.meets_pass_rate and not self.is_certified


def decode_version(version: str) -> CertificationStatus:
    """
    Decode a version string to extract certification info.

    Version format:
    - v0.pass_count.test_count (trial/uncertified)
    - v<level>.win_count.trade_count (certified)

    Examples:
        v0.0.0   -> not certified, 0 tests
        v0.7.10  -> not certified, 7/10 passed (70%)
        v1.5.10  -> certified, 5/10 live trades won (50%)
    """
    if not version:
        return CertificationStatus(
            is_certified=False,
            certification_level=0,
            test_count=0,
            test_pass_count=0,
            live_trade_count=0,
            live_win_count=0,
            pass_rate=0.0,
        )

    match = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        logger.warning(f"Invalid version format: {version}")
        return CertificationStatus(
            is_certified=False,
            certification_level=0,
            test_count=0,
            test_pass_count=0,
            live_trade_count=0,
            live_win_count=0,
            pass_rate=0.0,
        )

    level = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))

    if level == 0:
        return CertificationStatus(
            is_certified=False,
            certification_level=0,
            test_count=patch,
            test_pass_count=minor,
            live_trade_count=0,
            live_win_count=0,
            pass_rate=minor / patch if patch > 0 else 0.0,
        )
    else:
        return CertificationStatus(
            is_certified=True,
            certification_level=level,
            test_count=0,
            test_pass_count=0,
            live_trade_count=patch,
            live_win_count=minor,
            pass_rate=minor / patch if patch > 0 else 0.0,
        )


def get_strategy_certification(
    strategy_name: str,
    strategies_path: str,
) -> CertificationStatus:
    """
    Get certification status for a strategy.

    Checks metadata.json first, then falls back to version decoding
    from strategy file if metadata not found.

    Returns:
        CertificationStatus with decoded info
    """
    from jesse_mcp.core.strategy_validation.metadata import load_metadata

    metadata = load_metadata(strategy_name, strategies_path)
    if metadata:
        return decode_version(metadata.version)

    version = _get_version_from_strategy_file(strategy_name, strategies_path)
    return decode_version(version)


def _get_version_from_strategy_file(
    strategy_name: str,
    strategies_path: str,
) -> Optional[str]:
    """
    Try to extract version from strategy __init__.py file.

    Looks for a version string in the format: __version__ = "vX.Y.Z"
    """
    strategy_file = os.path.join(strategies_path, strategy_name, "__init__.py")
    if not os.path.exists(strategy_file):
        return None

    try:
        with open(strategy_file, "r") as f:
            content = f.read()

        match = re.search(r'__version__\s*=\s*["\'](v\d+\.\d+\.\d+)["\']', content)
        if match:
            return match.group(1)
    except Exception as e:
        logger.warning(f"Failed to read strategy file for version: {e}")

    return None


def is_strategy_certified(
    strategy_name: str,
    strategies_path: str,
) -> bool:
    """Check if a strategy is certified."""
    status = get_strategy_certification(strategy_name, strategies_path)
    return status.is_certified


def check_live_trading_allowed(
    strategy_name: str,
    strategies_path: str,
) -> dict:
    """
    Check if live trading is allowed for a strategy.

    Returns:
        dict with:
        - allowed: bool
        - status: CertificationStatus
        - reason: str if not allowed
        - recommendation: str if not allowed
    """
    status = get_strategy_certification(strategy_name, strategies_path)

    if status.is_certified:
        return {
            "allowed": True,
            "status": status,
            "reason": None,
            "recommendation": None,
        }

    if status.test_count == 0:
        return {
            "allowed": False,
            "status": status,
            "reason": "no_tests",
            "recommendation": "Run backtests to test the strategy before live trading",
        }

    if not status.has_enough_tests:
        return {
            "allowed": False,
            "status": status,
            "reason": "insufficient_tests",
            "recommendation": f"Need {CERTIFICATION_MIN_TESTS - status.test_count} more tests (have {status.test_count}/{CERTIFICATION_MIN_TESTS})",
        }

    if not status.meets_pass_rate:
        return {
            "allowed": False,
            "status": status,
            "reason": "insufficient_pass_rate",
            "recommendation": f"Pass rate {status.pass_rate:.0%} is below {CERTIFICATION_PASS_RATE:.0%} threshold ({status.test_pass_count}/{status.test_count} passed)",
        }

    return {
        "allowed": True,
        "status": status,
        "reason": None,
        "recommendation": None,
    }
