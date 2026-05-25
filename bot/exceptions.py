"""
Custom Exceptions
=================
Granular exception hierarchy for clear error handling across layers.
"""


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""
    pass


class ValidationError(TradingBotError):
    """Raised when user input fails validation."""
    pass


class BinanceAPIError(TradingBotError):
    """Raised when Binance API returns an error response."""

    def __init__(self, status_code: int, error_code: int, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(
            f"Binance API Error [{status_code}] (code={error_code}): {message}"
        )


class NetworkError(TradingBotError):
    """Raised on network/connection failures."""
    pass


class AuthenticationError(TradingBotError):
    """Raised when API credentials are missing or invalid."""
    pass
