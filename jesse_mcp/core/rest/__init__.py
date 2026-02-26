"""
Jesse REST API Client module.

Submodules:
- auth: Authentication methods
- backtest: Backtest methods
- candles: Candles management methods
- client: Main JesseRESTClient class
- config: Exchange configuration
- live: Live trading methods
- optimization: Optimization and Monte Carlo methods
"""

from .client import JesseRESTClient, get_jesse_rest_client

__all__ = ["JesseRESTClient", "get_jesse_rest_client"]
