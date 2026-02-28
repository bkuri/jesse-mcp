"""
Authentication methods for Jesse REST API client.
"""

import logging
import requests

logger = logging.getLogger("jesse-mcp.rest-client")


def authenticate_with_token(session: requests.Session, base_url: str, token: str) -> str:
    """Use a pre-generated API token directly."""
    try:
        session.headers.update({"authorization": token})
        logger.info("✅ Authenticated with Jesse API (using pre-generated token)")
        return token
    except Exception as e:
        logger.error(f"❌ Token configuration failed: {e}")
        raise


def authenticate_with_password(session: requests.Session, base_url: str, password: str) -> str:
    """Authenticate with Jesse API password to obtain a session token."""
    try:
        response = requests.post(
            f"{base_url}/auth/login",
            json={"password": password},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        auth_token = data.get("token") or data.get("auth_token")
        if auth_token:
            session.headers.update({"authorization": auth_token})
            logger.info("✅ Authenticated with Jesse API (via login)")
            return auth_token
        else:
            logger.error(f"❌ No token in login response: {data}")
            raise ValueError(f"No token in login response: {data}")
    except Exception as e:
        logger.error(f"❌ Authentication failed: {e}")
        raise


def verify_connection(session: requests.Session, base_url: str) -> bool:
    """Verify connection to Jesse API."""
    try:
        response = session.get(f"{base_url}/")
        if response.status_code == 401:
            raise ConnectionError("Unauthorized - check JESSE_API_TOKEN")
        if response.status_code != 200:
            raise ConnectionError(f"Jesse API returned {response.status_code}")
        logger.info(f"✅ Connected to Jesse API at {base_url}")
        return True
    except Exception as e:
        logger.error(f"❌ Cannot connect to Jesse API: {e}")
        raise
