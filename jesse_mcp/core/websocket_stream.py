"""
WebSocket Streaming Client for Jesse API

Provides real-time streaming for backtest progress, optimization trials,
and candle import progress via WebSocket connections.

Configuration (via environment):
- JESSE_WS_URL: WebSocket URL (default: ws://server2:8000/ws)
- JESSE_API_TOKEN: Authentication token for WebSocket connections
"""

import asyncio
import json
import logging
import os
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Union,
)

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection

try:
    import websockets
    import websockets.exceptions

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None  # type: ignore[assignment]

logger = logging.getLogger("jesse-mcp.websocket")

JESSE_WS_URL = os.getenv("JESSE_WS_URL", "ws://server2:8000/ws")
JESSE_API_TOKEN = os.getenv("JESSE_API_TOKEN", "")


class MessageType(str, Enum):
    """WebSocket message types from Jesse"""

    BACKTEST_PROGRESS = "backtest_progress"
    BACKTEST_COMPLETE = "backtest_complete"
    BACKTEST_ERROR = "backtest_error"
    OPTIMIZATION_TRIAL = "optimization_trial"
    OPTIMIZATION_COMPLETE = "optimization_complete"
    OPTIMIZATION_ERROR = "optimization_error"
    CANDLE_IMPORT_PROGRESS = "candle_import_progress"
    CANDLE_IMPORT_COMPLETE = "candle_import_complete"
    CANDLE_IMPORT_ERROR = "candle_import_error"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class SubscriptionType(str, Enum):
    """Subscription channel types"""

    BACKTEST = "backtest"
    OPTIMIZATION = "optimization"
    CANDLE_IMPORT = "candle_import"


class JesseWebSocketClient:
    """Async WebSocket client for Jesse real-time updates

    Provides streaming updates for:
    - Backtest progress (candle processing, trade execution)
    - Optimization trials (parameter combinations, fitness scores)
    - Candle import progress (download status, completion)

    Usage:
        async with JesseWebSocketClient() as client:
            await client.subscribe_backtest("backtest-id-123")
            async for message in client.messages():
                print(message)

    Or with callbacks:
        client = JesseWebSocketClient()
        client.on_message(lambda msg: print(msg))
        await client.connect()
        await client.subscribe_backtest("backtest-id-123")
        # ... later
        await client.close()
    """

    def __init__(
        self,
        ws_url: str = JESSE_WS_URL,
        auth_token: str = JESSE_API_TOKEN,
        reconnect: bool = True,
        reconnect_delay: float = 5.0,
        max_reconnect_attempts: int = 5,
    ):
        """
        Initialize WebSocket client

        Args:
            ws_url: WebSocket URL to connect to
            auth_token: Authentication token (from JESSE_API_TOKEN)
            reconnect: Enable automatic reconnection on disconnect
            reconnect_delay: Seconds to wait between reconnection attempts
            max_reconnect_attempts: Maximum reconnection attempts before giving up
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets library not installed. Install with: pip install websockets"
            )

        self.ws_url = ws_url
        self.auth_token = auth_token
        self.reconnect = reconnect
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts

        self._ws: Optional["ClientConnection"] = None
        self._connected = False
        self._reconnect_count = 0
        self._subscriptions: Set[str] = set()
        self._message_handlers: List[Callable[[Dict[str, Any]], None]] = []
        self._message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._receive_task: Optional[asyncio.Task] = None
        self._running = False

    @property
    def connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._connected and self._ws is not None

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to Jesse

        Returns:
            True if connected successfully, False otherwise
        """
        if self._connected:
            logger.warning("⚠️ WebSocket already connected")
            return True

        try:
            headers = {}
            if self.auth_token:
                headers["authorization"] = self.auth_token

            assert websockets is not None  # for type checker
            self._ws = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )

            self._connected = True
            self._reconnect_count = 0
            self._running = True

            self._receive_task = asyncio.create_task(self._receive_loop())

            logger.info(f"✅ WebSocket connected to {self.ws_url}")

            for subscription in self._subscriptions:
                await self._send_subscription(subscription)

            return True

        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            self._connected = False
            return False

    async def close(self) -> None:
        """Close WebSocket connection and cleanup resources"""
        self._running = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket: {e}")
            self._ws = None

        self._connected = False
        logger.info("🔌 WebSocket connection closed")

    async def _receive_loop(self) -> None:
        """Background task to receive and process messages"""
        while self._running and self._ws:
            try:
                raw_message = await self._ws.recv()
                message = json.loads(raw_message)

                await self._message_queue.put(message)

                for handler in self._message_handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message)
                        else:
                            handler(message)
                    except Exception as e:
                        logger.error(f"❌ Message handler error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                if websockets and isinstance(e, websockets.exceptions.ConnectionClosed):
                    logger.warning("⚠️ WebSocket connection closed by server")
                    if (
                        self.reconnect
                        and self._reconnect_count < self.max_reconnect_attempts
                    ):
                        await self._attempt_reconnect()
                    else:
                        self._running = False
                        break
                else:
                    logger.error(f"❌ WebSocket receive error: {e}")

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect after connection loss"""
        self._reconnect_count += 1
        logger.info(
            f"🔄 Reconnecting ({self._reconnect_count}/{self.max_reconnect_attempts})..."
        )

        await asyncio.sleep(self.reconnect_delay)

        self._connected = False
        self._ws = None

        if await self.connect():
            logger.info("✅ WebSocket reconnected successfully")
        else:
            logger.error("❌ WebSocket reconnection failed")

    async def _send_subscription(self, subscription: str) -> None:
        """Send subscription message to server"""
        if not self._ws:
            return

        message = json.dumps({"action": "subscribe", "channel": subscription})
        await self._ws.send(message)

    async def _send_unsubscription(self, subscription: str) -> None:
        """Send unsubscription message to server"""
        if not self._ws:
            return

        message = json.dumps({"action": "unsubscribe", "channel": subscription})
        await self._ws.send(message)

    async def subscribe_backtest(self, backtest_id: str) -> bool:
        """
        Subscribe to backtest progress updates

        Args:
            backtest_id: UUID of the backtest to subscribe to

        Returns:
            True if subscription sent successfully
        """
        subscription = f"{SubscriptionType.BACKTEST}:{backtest_id}"
        self._subscriptions.add(subscription)

        if self._connected:
            await self._send_subscription(subscription)
            logger.info(f"📡 Subscribed to backtest: {backtest_id}")

        return True

    async def unsubscribe_backtest(self, backtest_id: str) -> bool:
        """
        Unsubscribe from backtest updates

        Args:
            backtest_id: UUID of the backtest to unsubscribe from

        Returns:
            True if unsubscription sent successfully
        """
        subscription = f"{SubscriptionType.BACKTEST}:{backtest_id}"
        self._subscriptions.discard(subscription)

        if self._connected:
            await self._send_unsubscription(subscription)
            logger.info(f"🔇 Unsubscribed from backtest: {backtest_id}")

        return True

    async def subscribe_optimization(self, optimization_id: str) -> bool:
        """
        Subscribe to optimization trial updates

        Args:
            optimization_id: UUID of the optimization to subscribe to

        Returns:
            True if subscription sent successfully
        """
        subscription = f"{SubscriptionType.OPTIMIZATION}:{optimization_id}"
        self._subscriptions.add(subscription)

        if self._connected:
            await self._send_subscription(subscription)
            logger.info(f"📡 Subscribed to optimization: {optimization_id}")

        return True

    async def unsubscribe_optimization(self, optimization_id: str) -> bool:
        """
        Unsubscribe from optimization updates

        Args:
            optimization_id: UUID of the optimization to unsubscribe from

        Returns:
            True if unsubscription sent successfully
        """
        subscription = f"{SubscriptionType.OPTIMIZATION}:{optimization_id}"
        self._subscriptions.discard(subscription)

        if self._connected:
            await self._send_unsubscription(subscription)
            logger.info(f"🔇 Unsubscribed from optimization: {optimization_id}")

        return True

    async def subscribe_candle_import(
        self, exchange: str, symbol: str, timeframe: str
    ) -> bool:
        """
        Subscribe to candle import progress updates

        Args:
            exchange: Exchange name (e.g., "Binance")
            symbol: Trading symbol (e.g., "BTC-USDT")
            timeframe: Candle timeframe (e.g., "1h")

        Returns:
            True if subscription sent successfully
        """
        subscription = (
            f"{SubscriptionType.CANDLE_IMPORT}:{exchange}:{symbol}:{timeframe}"
        )
        self._subscriptions.add(subscription)

        if self._connected:
            await self._send_subscription(subscription)
            logger.info(
                f"📡 Subscribed to candle import: {exchange} {symbol} {timeframe}"
            )

        return True

    async def unsubscribe_candle_import(
        self, exchange: str, symbol: str, timeframe: str
    ) -> bool:
        """
        Unsubscribe from candle import updates

        Args:
            exchange: Exchange name
            symbol: Trading symbol
            timeframe: Candle timeframe

        Returns:
            True if unsubscription sent successfully
        """
        subscription = (
            f"{SubscriptionType.CANDLE_IMPORT}:{exchange}:{symbol}:{timeframe}"
        )
        self._subscriptions.discard(subscription)

        if self._connected:
            await self._send_unsubscription(subscription)
            logger.info(
                f"🔇 Unsubscribed from candle import: {exchange} {symbol} {timeframe}"
            )

        return True

    def on_message(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register a callback for incoming messages

        Args:
            handler: Function to call with each message dict
                     Can be sync or async function
        """
        self._message_handlers.append(handler)

    def remove_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """
        Remove a previously registered message handler

        Args:
            handler: The handler function to remove
        """
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    async def messages(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async generator yielding messages as they arrive

        Yields:
            Dict containing message data

        Usage:
            async for message in client.messages():
                if message["type"] == "backtest_progress":
                    print(f"Progress: {message['progress']}%")
        """
        while self._running:
            try:
                message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                yield message
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ Error getting message: {e}")
                break

    async def wait_for_complete(
        self,
        subscription_id: str,
        timeout: float = 3600.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for a completion message for a specific subscription

        Args:
            subscription_id: ID of backtest/optimization to wait for
            timeout: Maximum seconds to wait (default: 1 hour)

        Returns:
            Completion message dict, or None if timeout
        """
        complete_types = {
            MessageType.BACKTEST_COMPLETE,
            MessageType.OPTIMIZATION_COMPLETE,
            MessageType.CANDLE_IMPORT_COMPLETE,
        }

        try:
            async with asyncio.timeout(timeout):
                async for message in self.messages():
                    msg_type = message.get("type")
                    msg_id = (
                        message.get("id")
                        or message.get("backtest_id")
                        or message.get("optimization_id")
                    )

                    if msg_id == subscription_id and msg_type in complete_types:
                        return message

                    if msg_type == MessageType.ERROR:
                        return message

        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout waiting for completion: {subscription_id}")
            return None

        return None

    async def __aenter__(self) -> "JesseWebSocketClient":
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.close()


class BacktestProgressTracker:
    """Helper class to track backtest progress via WebSocket

    Simplifies tracking progress of a single backtest with callbacks
    for different progress stages.

    Usage:
        async with BacktestProgressTracker(backtest_id) as tracker:
            tracker.on_progress(lambda p: print(f"{p}%"))
            tracker.on_trade(lambda t: print(f"Trade: {t}"))
            await tracker.wait_for_complete()
    """

    def __init__(
        self, backtest_id: str, ws_client: Optional[JesseWebSocketClient] = None
    ):
        """
        Initialize progress tracker

        Args:
            backtest_id: UUID of backtest to track
            ws_client: Existing WebSocket client (creates new one if None)
        """
        self.backtest_id = backtest_id
        self._client = ws_client
        self._owns_client = ws_client is None
        self._progress_handlers: List[Callable[[int], None]] = []
        self._trade_handlers: List[Callable[[Dict], None]] = []
        self._complete_handlers: List[Callable[[Dict], None]] = []
        self._error_handlers: List[Callable[[str], None]] = []

    async def connect(self) -> bool:
        """Connect and subscribe to backtest updates"""
        if self._owns_client:
            self._client = JesseWebSocketClient()
            if not await self._client.connect():
                return False

        assert self._client is not None
        self._client.on_message(self._handle_message)
        await self._client.subscribe_backtest(self.backtest_id)
        return True

    async def close(self) -> None:
        """Close connection if we own the client"""
        if self._owns_client and self._client:
            await self._client.close()

    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Route messages to appropriate handlers"""
        msg_type = message.get("type")
        msg_id = message.get("id") or message.get("backtest_id")

        if msg_id != self.backtest_id:
            return

        if msg_type == MessageType.BACKTEST_PROGRESS:
            progress = message.get("progress", 0)
            for handler in self._progress_handlers:
                handler(progress)

        elif msg_type == MessageType.BACKTEST_COMPLETE:
            for handler in self._complete_handlers:
                handler(message)

        elif msg_type == MessageType.BACKTEST_ERROR:
            error = message.get("error", "Unknown error")
            for handler in self._error_handlers:
                handler(error)

    def on_progress(self, handler: Callable[[int], None]) -> None:
        """Register callback for progress updates (0-100)"""
        self._progress_handlers.append(handler)

    def on_trade(self, handler: Callable[[Dict], None]) -> None:
        """Register callback for trade executions"""
        self._trade_handlers.append(handler)

    def on_complete(self, handler: Callable[[Dict], None]) -> None:
        """Register callback for backtest completion"""
        self._complete_handlers.append(handler)

    def on_error(self, handler: Callable[[str], None]) -> None:
        """Register callback for errors"""
        self._error_handlers.append(handler)

    async def wait_for_complete(
        self, timeout: float = 3600.0
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for backtest to complete

        Args:
            timeout: Maximum seconds to wait

        Returns:
            Completion message or None if timeout
        """
        assert self._client is not None
        return await self._client.wait_for_complete(self.backtest_id, timeout)

    async def __aenter__(self) -> "BacktestProgressTracker":
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.close()


class OptimizationProgressTracker:
    """Helper class to track optimization progress via WebSocket

    Tracks individual trial progress and best parameter updates.

    Usage:
        async with OptimizationProgressTracker(opt_id) as tracker:
            tracker.on_trial(lambda t: print(f"Trial {t['number']}: {t['value']}"))
            tracker.on_best(lambda b: print(f"Best: {b}"))
            result = await tracker.wait_for_complete()
    """

    def __init__(
        self, optimization_id: str, ws_client: Optional[JesseWebSocketClient] = None
    ):
        """
        Initialize optimization tracker

        Args:
            optimization_id: UUID of optimization to track
            ws_client: Existing WebSocket client (creates new one if None)
        """
        self.optimization_id = optimization_id
        self._client = ws_client
        self._owns_client = ws_client is None
        self._trial_handlers: List[Callable[[Dict], None]] = []
        self._best_handlers: List[Callable[[Dict], None]] = []
        self._complete_handlers: List[Callable[[Dict], None]] = []
        self._error_handlers: List[Callable[[str], None]] = []

    async def connect(self) -> bool:
        """Connect and subscribe to optimization updates"""
        if self._owns_client:
            self._client = JesseWebSocketClient()
            if not await self._client.connect():
                return False

        assert self._client is not None
        self._client.on_message(self._handle_message)
        await self._client.subscribe_optimization(self.optimization_id)
        return True

    async def close(self) -> None:
        """Close connection if we own the client"""
        if self._owns_client and self._client:
            await self._client.close()

    def _handle_message(self, message: Dict[str, Any]) -> None:
        """Route messages to appropriate handlers"""
        msg_type = message.get("type")
        msg_id = message.get("id") or message.get("optimization_id")

        if msg_id != self.optimization_id:
            return

        if msg_type == MessageType.OPTIMIZATION_TRIAL:
            for handler in self._trial_handlers:
                handler(message)

            if message.get("is_best"):
                for handler in self._best_handlers:
                    handler(message)

        elif msg_type == MessageType.OPTIMIZATION_COMPLETE:
            for handler in self._complete_handlers:
                handler(message)

        elif msg_type == MessageType.OPTIMIZATION_ERROR:
            error = message.get("error", "Unknown error")
            for handler in self._error_handlers:
                handler(error)

    def on_trial(self, handler: Callable[[Dict], None]) -> None:
        """Register callback for trial completions"""
        self._trial_handlers.append(handler)

    def on_best(self, handler: Callable[[Dict], None]) -> None:
        """Register callback when new best trial found"""
        self._best_handlers.append(handler)

    def on_complete(self, handler: Callable[[Dict], None]) -> None:
        """Register callback for optimization completion"""
        self._complete_handlers.append(handler)

    def on_error(self, handler: Callable[[str], None]) -> None:
        """Register callback for errors"""
        self._error_handlers.append(handler)

    async def wait_for_complete(
        self, timeout: float = 7200.0
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for optimization to complete

        Args:
            timeout: Maximum seconds to wait (default: 2 hours)

        Returns:
            Completion message or None if timeout
        """
        assert self._client is not None
        return await self._client.wait_for_complete(self.optimization_id, timeout)

    async def __aenter__(self) -> "OptimizationProgressTracker":
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.close()


_ws_client_instance: Optional[JesseWebSocketClient] = None


def get_websocket_client() -> JesseWebSocketClient:
    """
    Get or create the global WebSocket client instance

    Returns:
        Shared JesseWebSocketClient instance
    """
    global _ws_client_instance
    if _ws_client_instance is None:
        _ws_client_instance = JesseWebSocketClient()
    return _ws_client_instance


async def close_websocket_client() -> None:
    """Close the global WebSocket client if it exists"""
    global _ws_client_instance
    if _ws_client_instance:
        await _ws_client_instance.close()
        _ws_client_instance = None
