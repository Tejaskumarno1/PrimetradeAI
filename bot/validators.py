"""
Input Validators
================
Validates all user-provided order parameters before they reach the API.
Fails fast with clear error messages.
"""

import logging
import re
from typing import Optional

from .exceptions import ValidationError

logger = logging.getLogger("trading_bot.validators")

# Supported values
VALID_SIDES = ("BUY", "SELL")
VALID_ORDER_TYPES = ("MARKET", "LIMIT", "STOP")


def validate_symbol(symbol: str) -> str:
    """
    Validate trading pair symbol.
    
    Rules:
    - Must be non-empty
    - Must be uppercase alphanumeric (e.g., BTCUSDT, ETHUSDT)
    - Must end with a quote asset (USDT, BUSD, etc.)
    
    Args:
        symbol: Trading pair symbol.
    
    Returns:
        Uppercased, validated symbol string.
    
    Raises:
        ValidationError: If symbol format is invalid.
    """
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol cannot be empty.")

    symbol = symbol.strip().upper()

    if not re.match(r"^[A-Z0-9]{2,20}$", symbol):
        raise ValidationError(
            f"Invalid symbol format: '{symbol}'. "
            "Must be uppercase alphanumeric (e.g., BTCUSDT)."
        )

    # Check for common quote assets
    quote_assets = ("USDT", "BUSD", "USD")
    if not any(symbol.endswith(qa) for qa in quote_assets):
        logger.warning(
            f"Symbol '{symbol}' does not end with a common quote asset "
            f"({', '.join(quote_assets)}). Proceeding anyway."
        )

    logger.debug(f"Symbol validated: {symbol}")
    return symbol


def validate_side(side: str) -> str:
    """
    Validate order side (BUY or SELL).
    
    Args:
        side: Order side string.
    
    Returns:
        Uppercased, validated side string.
    
    Raises:
        ValidationError: If side is not BUY or SELL.
    """
    if not side:
        raise ValidationError("Side cannot be empty.")

    side = side.strip().upper()

    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side: '{side}'. Must be one of: {', '.join(VALID_SIDES)}."
        )

    logger.debug(f"Side validated: {side}")
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type (MARKET, LIMIT, or STOP).
    
    Args:
        order_type: Order type string.
    
    Returns:
        Uppercased, validated order type string.
    
    Raises:
        ValidationError: If order type is not supported.
    """
    if not order_type:
        raise ValidationError("Order type cannot be empty.")

    order_type = order_type.strip().upper()

    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type: '{order_type}'. "
            f"Must be one of: {', '.join(VALID_ORDER_TYPES)}."
        )

    logger.debug(f"Order type validated: {order_type}")
    return order_type


def validate_quantity(quantity: float) -> float:
    """
    Validate order quantity.
    
    Rules:
    - Must be a positive number
    - Must be non-zero
    
    Args:
        quantity: Order quantity.
    
    Returns:
        Validated quantity as float.
    
    Raises:
        ValidationError: If quantity is not positive.
    """
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Invalid quantity: must be a number, got '{quantity}'.")

    if quantity <= 0:
        raise ValidationError(f"Quantity must be positive, got {quantity}.")

    logger.debug(f"Quantity validated: {quantity}")
    return quantity


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate order price.
    
    Rules:
    - Required for LIMIT and STOP orders
    - Must be a positive number when provided
    - Ignored for MARKET orders
    
    Args:
        price: Order price (can be None for MARKET).
        order_type: The order type (determines if price is required).
    
    Returns:
        Validated price as float, or None for MARKET orders.
    
    Raises:
        ValidationError: If price is missing for LIMIT/STOP or is not positive.
    """
    requires_price = order_type in ("LIMIT", "STOP")

    if requires_price and price is None:
        raise ValidationError(
            f"Price is required for {order_type} orders."
        )

    if price is not None:
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid price: must be a number, got '{price}'.")

        if price <= 0:
            raise ValidationError(f"Price must be positive, got {price}.")

        logger.debug(f"Price validated: {price}")

    return price


def validate_stop_price(stop_price: Optional[float], order_type: str) -> Optional[float]:
    """
    Validate stop price for Stop-Limit orders.
    
    Args:
        stop_price: Stop trigger price.
        order_type: The order type.
    
    Returns:
        Validated stop price or None.
    
    Raises:
        ValidationError: If stop price is missing for STOP orders.
    """
    if order_type == "STOP" and stop_price is None:
        raise ValidationError("Stop price is required for STOP (Stop-Limit) orders.")

    if stop_price is not None:
        try:
            stop_price = float(stop_price)
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid stop price: must be a number, got '{stop_price}'.")

        if stop_price <= 0:
            raise ValidationError(f"Stop price must be positive, got {stop_price}.")

        logger.debug(f"Stop price validated: {stop_price}")

    return stop_price


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> dict:
    """
    Run all validations and return a clean parameter dict.
    
    Args:
        symbol: Trading pair symbol.
        side: BUY or SELL.
        order_type: MARKET, LIMIT, or STOP.
        quantity: Order quantity.
        price: Order price (required for LIMIT/STOP).
        stop_price: Stop trigger price (required for STOP).
    
    Returns:
        Dict with all validated parameters.
    
    Raises:
        ValidationError: On any validation failure.
    """
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.strip().upper()),
        "stop_price": validate_stop_price(stop_price, order_type.strip().upper()),
    }

    logger.info(f"All inputs validated successfully: {validated}")
    return validated
