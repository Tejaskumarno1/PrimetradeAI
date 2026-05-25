"""
Order Manager
=============
Business logic for placing and formatting orders.
Translates validated user input into Binance API calls.
"""

import logging
from typing import Any, Dict, Optional

from .client import BinanceClient
from .exceptions import TradingBotError

logger = logging.getLogger("trading_bot.orders")


class OrderManager:
    """
    High-level order placement and formatting.
    
    Uses BinanceClient for API transport and adds:
    - Order parameter construction
    - Response formatting
    - Pre/post order logging
    """

    def __init__(self, client: BinanceClient):
        """
        Initialize with a configured BinanceClient.
        
        Args:
            client: An authenticated BinanceClient instance.
        """
        self._client = client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Place an order on Binance Futures Testnet.
        
        Constructs the appropriate parameter set based on order type and
        delegates to the BinanceClient.
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT).
            side: BUY or SELL.
            order_type: MARKET, LIMIT, or STOP.
            quantity: Order quantity.
            price: Limit price (required for LIMIT and STOP).
            stop_price: Stop trigger price (required for STOP).
            time_in_force: Time in force for LIMIT orders (default: GTC).
        
        Returns:
            Order response dict from Binance API.
        
        Raises:
            TradingBotError: On any order placement failure.
        """
        # Build base params
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": self._map_order_type(order_type),
            "quantity": str(quantity),
        }

        # Add price for LIMIT and STOP orders
        if order_type in ("LIMIT", "STOP"):
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        # Add stop price for STOP orders
        if order_type == "STOP":
            params["stopPrice"] = str(stop_price)

        # Log the order request summary
        self._log_order_summary(params)

        # Place the order
        response = self._client.place_order(**params)

        # Log and return the response
        self._log_order_response(response)
        return response

    @staticmethod
    def _map_order_type(order_type: str) -> str:
        """
        Map user-friendly order type to Binance API type.
        
        Args:
            order_type: MARKET, LIMIT, or STOP.
        
        Returns:
            Binance API order type string.
        """
        mapping = {
            "MARKET": "MARKET",
            "LIMIT": "LIMIT",
            "STOP": "STOP",
        }
        return mapping.get(order_type, order_type)

    @staticmethod
    def _log_order_summary(params: Dict[str, Any]) -> None:
        """Log a formatted order request summary."""
        logger.info("=" * 55)
        logger.info("  ORDER REQUEST SUMMARY")
        logger.info("=" * 55)
        for key, value in params.items():
            logger.info(f"  {key:>15}: {value}")
        logger.info("-" * 55)

    @staticmethod
    def _log_order_response(response: Dict[str, Any]) -> None:
        """Log a formatted order response."""
        logger.info("=" * 55)
        logger.info("  ORDER RESPONSE")
        logger.info("=" * 55)

        # Key fields to display
        display_fields = [
            ("orderId", "Order ID"),
            ("symbol", "Symbol"),
            ("side", "Side"),
            ("type", "Type"),
            ("status", "Status"),
            ("origQty", "Quantity"),
            ("executedQty", "Executed Qty"),
            ("price", "Price"),
            ("avgPrice", "Avg Price"),
            ("stopPrice", "Stop Price"),
            ("timeInForce", "Time in Force"),
            ("updateTime", "Update Time"),
        ]

        for api_key, label in display_fields:
            if api_key in response and response[api_key]:
                logger.info(f"  {label:>15}: {response[api_key]}")

        logger.info("-" * 55)

    @staticmethod
    def format_response(response: Dict[str, Any]) -> str:
        """
        Format order response for CLI display.
        
        Args:
            response: Raw API response dict.
        
        Returns:
            Formatted string for terminal output.
        """
        lines = []
        lines.append("")
        lines.append("+" + "-" * 53 + "+")
        lines.append("|" + "  ORDER RESPONSE".center(53) + "|")
        lines.append("+" + "-" * 53 + "+")

        fields = [
            ("Order ID", response.get("orderId", "N/A")),
            ("Symbol", response.get("symbol", "N/A")),
            ("Side", response.get("side", "N/A")),
            ("Type", response.get("type", "N/A")),
            ("Status", response.get("status", "N/A")),
            ("Quantity", response.get("origQty", "N/A")),
            ("Executed Qty", response.get("executedQty", "N/A")),
            ("Price", response.get("price", "N/A")),
            ("Avg Price", response.get("avgPrice", "N/A")),
        ]

        # Include stop price if present
        if response.get("stopPrice") and response["stopPrice"] != "0":
            fields.append(("Stop Price", response["stopPrice"]))

        for label, value in fields:
            lines.append(f"|  {label:>15}: {str(value):<34}|")

        lines.append("+" + "-" * 53 + "+")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_request_summary(
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> str:
        """
        Format order request parameters for CLI display.
        
        Args:
            symbol: Trading pair.
            side: BUY or SELL.
            order_type: MARKET, LIMIT, or STOP.
            quantity: Order quantity.
            price: Limit price.
            stop_price: Stop trigger price.
        
        Returns:
            Formatted string for terminal output.
        """
        lines = []
        lines.append("")
        lines.append("+" + "-" * 53 + "+")
        lines.append("|" + "  ORDER REQUEST SUMMARY".center(53) + "|")
        lines.append("+" + "-" * 53 + "+")
        lines.append(f"|  {'Symbol':>15}: {symbol:<34}|")
        lines.append(f"|  {'Side':>15}: {side:<34}|")
        lines.append(f"|  {'Order Type':>15}: {order_type:<34}|")
        lines.append(f"|  {'Quantity':>15}: {str(quantity):<34}|")

        if price is not None:
            lines.append(f"|  {'Price':>15}: {str(price):<34}|")

        if stop_price is not None:
            lines.append(f"|  {'Stop Price':>15}: {str(stop_price):<34}|")

        lines.append("+" + "-" * 53 + "+")
        lines.append("")

        return "\n".join(lines)

