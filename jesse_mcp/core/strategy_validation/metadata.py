"""
Strategy metadata management.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

logger = logging.getLogger("jesse-mcp.strategy_metadata")

CERTIFICATION_MIN_TESTS = 10
CERTIFICATION_PASS_RATE = 0.70


@dataclass
class StrategyMetadata:
    """Metadata for a strategy tracking its testing and certification status."""

    name: str
    version: str = "v0.0.0"
    test_count: int = 0
    test_pass_count: int = 0
    live_trade_count: int = 0
    live_win_count: int = 0
    certified_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: str(datetime.now()))
    last_test_at: Optional[str] = None
    notes: str = ""

    def __post_init__(self):
        if self.certified_at:
            self.version = self._compute_version()
        elif self.test_count > 0:
            self.version = self._compute_version()

    def _compute_version(self) -> str:
        """Compute version string based on certification status."""
        if self.certified_at:
            cert_level = self._get_certification_level()
            return f"v{cert_level}.{self.live_win_count}.{self.live_trade_count}"
        else:
            return f"v0.{self.test_pass_count}.{self.test_count}"

    def _get_certification_level(self) -> int:
        """Get certification level (how many times certified)."""
        return 1

    def record_test(self, passed: bool) -> None:
        """Record a test result."""
        from datetime import datetime

        self.test_count += 1
        if passed:
            self.test_pass_count += 1
        self.last_test_at = str(datetime.now())
        self.version = self._compute_version()

    def should_certify(self) -> bool:
        """Check if strategy should be auto-certified."""
        if self.certified_at:
            return False
        if self.test_count < CERTIFICATION_MIN_TESTS:
            return False

        pass_rate = self.test_pass_count / self.test_count
        return pass_rate >= CERTIFICATION_PASS_RATE

    def certify(self) -> None:
        """Promote to certified status."""
        from datetime import datetime

        if not self.certified_at:
            self.certified_at = str(datetime.now())
            self.version = self._compute_version()
            logger.info(f"Strategy {self.name} certified: {self.version}")

    def record_live_trade(self, won: bool) -> None:
        """Record a live trade result."""
        self.live_trade_count += 1
        if won:
            self.live_win_count += 1
        if self.certified_at:
            self.version = self._compute_version()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "test_count": self.test_count,
            "test_pass_count": self.test_pass_count,
            "live_trade_count": self.live_trade_count,
            "live_win_count": self.live_win_count,
            "certified_at": self.certified_at,
            "created_at": self.created_at,
            "last_test_at": self.last_test_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyMetadata":
        return cls(**data)


def get_metadata_path(strategy_name: str, strategies_path: str) -> str:
    """Get path to metadata.json for a strategy."""
    return os.path.join(strategies_path, strategy_name, "metadata.json")


def load_metadata(strategy_name: str, strategies_path: str) -> Optional[StrategyMetadata]:
    """Load metadata for a strategy."""
    metadata_path = get_metadata_path(strategy_name, strategies_path)

    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, "r") as f:
            data = json.load(f)
        return StrategyMetadata.from_dict(data)
    except Exception as e:
        logger.warning(f"Failed to load metadata for {strategy_name}: {e}")
        return None


def save_metadata(metadata: StrategyMetadata, strategies_path: str) -> bool:
    """Save metadata for a strategy."""
    metadata_path = get_metadata_path(metadata.name, strategies_path)

    try:
        with open(metadata_path, "w") as f:
            json.dump(metadata.to_dict(), f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save metadata for {metadata.name}: {e}")
        return False


def create_metadata(name: str, strategies_path: str) -> StrategyMetadata:
    """Create new metadata for a strategy."""
    metadata = StrategyMetadata(name=name)
    save_metadata(metadata, strategies_path)
    return metadata


def get_or_create_metadata(name: str, strategies_path: str) -> StrategyMetadata:
    """Get existing metadata or create new if doesn't exist."""
    metadata = load_metadata(name, strategies_path)
    if metadata is None:
        metadata = create_metadata(name, strategies_path)
    return metadata


from datetime import datetime
