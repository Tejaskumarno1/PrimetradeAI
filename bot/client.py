"""
Binance Futures Testnet Client
==============================
Handles API authentication (HMAC-SHA256 signing), request construction,
and response parsing for the Binance Futures Testnet (USDT-M).
"""

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .exceptions import AuthenticationError, BinanceAPIError, NetworkError

logger = logging.getLogger("trading_bot.client")

# Binance Futures Testnet base URL
DEFAULT_BASE_URL = "https://testnet.binancefuture.com"

# API endpoints
ENDPOINTS = {
    "order": "/fapi/v1/order",
    "exchange_info": "/fapi/v1/exchangeInfo",
    "account": "/fapi/v2/account",
    "ticker_price": "/fapi/v1/ticker/price",
}


class BinanceClient:
    """
    Low-level client for Binance Futures Testnet API.
    
    Handles request signing, HTTP communication, and error translation.
    This class should not contain business logic — only transport.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = DEFAULT_BASE_URL):
        """
        Initialize the Binance client.
        
        Args:
            api_key: Binance Futures Testnet API key.
            api_secret: Binance Futures Testnet API secret.
            base_url: API base URL (defaults to testnet).
        
        Raises:
            AuthenticationError: If credentials are empty.
        """
        if not api_key or not api_secret:
            raise AuthenticationError(
                "API key and secret are required. "
                "Set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file."
            )

        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")

        # Persistent session for connection reuse
        self._session = requests.Session()
        self._session.headers.update({
            "X-MBX-APIKEY": self._api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

        logger.info(f"BinanceClient initialized (base_url={self._base_url})")

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC-SHA256 signature for request parameters.
        
        Args:
            params: Query parameters to sign.
        
        Returns:
            Hex-encoded signature string.
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        logger.debug(f"Generated signature for query: {query_string[:80]}...")
        return signature

    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = True,
    ) -> Dict[str, Any]:
        """
        Send a signed or unsigned request to the Binance API.
        
        Args:
            method: HTTP method (GET, POST, DELETE).
            endpoint: API endpoint path.
            params: Query parameters.
            signed: Whether to add timestamp + HMAC signature.
        
        Returns:
            Parsed JSON response as dict.
        
        Raises:
            BinanceAPIError: On API-level errors (4xx, 5xx with error body).
            NetworkError: On connection/timeout failures.
        """
        url = f"{self._base_url}{endpoint}"
        params = params or {}

        # Add timestamp and signature for signed requests
        if signed:
            params["timestamp"] = self._get_timestamp()
            params["signature"] = self._generate_signature(params)

        logger.debug(f"API Request: {method} {endpoint} | params={self._sanitize_params(params)}")

        try:
            response = self._session.request(
                method=method,
                url=url,
                params=params if method == "GET" else None,
                data=urlencode(params) if method != "GET" else None,
                timeout=10,
            )

            logger.debug(f"API Response: status={response.status_code} | body={response.text[:500]}")

            # Parse response
            try:
                data = response.json()
            except ValueError:
                logger.error(f"Non-JSON response: {response.text[:200]}")
                raise BinanceAPIError(
                    status_code=response.status_code,
                    error_code=-1,
                    message=f"Invalid JSON response: {response.text[:200]}",
                )

            # Check for API errors
            if response.status_code >= 400:
                error_code = data.get("code", -1)
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"API Error: code={error_code}, msg={error_msg}")
                raise BinanceAPIError(
                    status_code=response.status_code,
                    error_code=error_code,
                    message=error_msg,
                )

            return data

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed: {e}")
            raise NetworkError(f"Failed to connect to {self._base_url}: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timed out: {e}")
            raise NetworkError(f"Request timed out: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise NetworkError(f"HTTP request failed: {e}")

    @staticmethod
    def _sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from params for logging."""
        sanitized = dict(params)
        if "signature" in sanitized:
            sanitized["signature"] = "***"
        return sanitized

    # --- Public API Methods ---

    def place_order(self, **params) -> Dict[str, Any]:
        """
        Place an order on Binance Futures.
        
        Args:
            **params: Order parameters (symbol, side, type, quantity, etc.)
        
        Returns:
            Order response dict from Binance.
        """
        logger.info(f"Placing order: {params}")
        return self._request("POST", ENDPOINTS["order"], params, signed=True)

    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange trading rules and symbol information."""
        return self._request("GET", ENDPOINTS["exchange_info"], signed=False)

    def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch current price for a symbol."""
        return self._request("GET", ENDPOINTS["ticker_price"], {"symbol": symbol}, signed=False)

    def get_account_info(self) -> Dict[str, Any]:
        """Fetch account balance and position information."""
        return self._request("GET", ENDPOINTS["account"], signed=True)
