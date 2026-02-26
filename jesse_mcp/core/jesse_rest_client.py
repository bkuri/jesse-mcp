"""
Jesse REST API Client - Backward compatibility module.

This module has been refactored into jesse_mcp.core.rest package.
Please use the new import paths:

    from jesse_mcp.core.rest import JesseRESTClient, get_jesse_rest_client

Or:

    from jesse_mcp.core import JesseRESTClient, get_jesse_rest_client
"""

from jesse_mcp.core.rest import JesseRESTClient, get_jesse_rest_client

__all__ = ["JesseRESTClient", "get_jesse_rest_client"]
