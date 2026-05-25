#!/usr/bin/env python3
"""
Trading Bot CLI
===============
Command-line interface for the Binance Futures Testnet Trading Bot.
Supports Market, Limit, and Stop-Limit orders with full validation.
"""

import os
import sys

import click
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.client import BinanceClient
from bot.exceptions import (
    AuthenticationError,
    BinanceAPIError,
    NetworkError,
    TradingBotError,
    ValidationError,
)
from bot.logging_config import setup_logging
from bot.orders import OrderManager
from bot.validators import validate_all

load_dotenv()

# ──────────────────────────────────────────────────────────────
# Display Helpers
# ──────────────────────────────────────────────────────────────

BANNER = r"""
  _____ ____      _    ____ ___ _   _  ____   ____   ___ _____
 |_   _|  _ \    / \  |  _ \_ _| \ | |/ ___| | __ ) / _ \_   _|
   | | | |_) |  / _ \ | | | | ||  \| | |  _  |  _ \| | | || |
   | | |  _ <  / ___ \| |_| | || |\  | |_| | | |_) | |_| || |
   |_| |_| \_\/_/   \_\____/___|_| \_|\____| |____/ \___/ |_|

   Binance Futures Testnet  |  USDT-M  |  v1.0.0
"""

W = 57  # box width


def line(char="-"):
    return "+" + char * W + "+"


def row(label, value, label_w=17):
    content = f"  {label:>{label_w}}: {value}"
    return "|" + f"{content:<{W}}" + "|"


def header(title):
    return "|" + f"  {title}".ljust(W) + "|"


def blank():
    return "|" + " " * W + "|"


def print_box(title, rows):
    """Print a clean bordered box with a title and key-value rows."""
    click.echo(line("="))
    click.echo(header(title))
    click.echo(line("-"))
    for label, value in rows:
        click.echo(row(label, value))
    click.echo(line("="))


def status(marker, msg, color="white"):
    """Print a status line: [OK], [..], [!!], [--], [ERROR]"""
    click.echo(click.style(f"  {marker} {msg}", fg=color))


def get_client() -> BinanceClient:
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    return BinanceClient(api_key=api_key, api_secret=api_secret)


# ──────────────────────────────────────────────────────────────
# CLI Group
# ──────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0", prog_name="Trading Bot")
def cli():
    """
    Binance Futures Testnet Trading Bot

    Place Market, Limit, and Stop-Limit orders on Binance Futures Testnet (USDT-M).

    \b
    Examples:
      python main.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
      python main.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500
      python main.py order --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 100000 --stop-price 99000
    """
    pass


# ──────────────────────────────────────────────────────────────
# Order Command
# ──────────────────────────────────────────────────────────────

@cli.command()
@click.option("--symbol", "-s", required=True, type=str,
              help="Trading pair symbol (e.g., BTCUSDT, ETHUSDT).")
@click.option("--side", required=True,
              type=click.Choice(["BUY", "SELL"], case_sensitive=False),
              help="Order side: BUY or SELL.")
@click.option("--type", "order_type", required=True,
              type=click.Choice(["MARKET", "LIMIT", "STOP"], case_sensitive=False),
              help="Order type: MARKET, LIMIT, or STOP (Stop-Limit).")
@click.option("--quantity", "-q", required=True, type=float,
              help="Order quantity (e.g., 0.001 for BTC).")
@click.option("--price", "-p", required=False, type=float, default=None,
              help="Limit price (required for LIMIT and STOP orders).")
@click.option("--stop-price", required=False, type=float, default=None,
              help="Stop trigger price (required for STOP orders).")
def order(symbol, side, order_type, quantity, price, stop_price):
    """Place an order on Binance Futures Testnet."""
    logger = setup_logging(log_dir="logs")

    # Banner
    click.echo(click.style(BANNER, fg="cyan"))

    try:
        # -- Validate --
        status("[..]", "Validating inputs...", "cyan")
        validated = validate_all(
            symbol=symbol, side=side, order_type=order_type,
            quantity=quantity, price=price, stop_price=stop_price,
        )
        status("[OK]", "Input validation passed.", "green")
        click.echo()

        # -- Request Summary --
        summary_rows = [
            ("Symbol", validated["symbol"]),
            ("Side", validated["side"]),
            ("Order Type", validated["order_type"]),
            ("Quantity", str(validated["quantity"])),
        ]
        if validated["price"] is not None:
            summary_rows.append(("Price", str(validated["price"])))
        if validated["stop_price"] is not None:
            summary_rows.append(("Stop Price", str(validated["stop_price"])))

        print_box("ORDER REQUEST", summary_rows)
        click.echo()

        # -- Confirm --
        if not click.confirm(click.style("  --> Confirm and place this order?", fg="yellow"), default=True):
            click.echo()
            status("[--]", "Order cancelled by user.", "red")
            logger.info("Order cancelled by user.")
            return

        click.echo()

        # -- Place Order --
        status("[..]", "Connecting to Binance Futures Testnet...", "cyan")
        client = get_client()
        order_mgr = OrderManager(client)

        status("[..]", "Placing order...", "cyan")
        response = order_mgr.place_order(
            symbol=validated["symbol"], side=validated["side"],
            order_type=validated["order_type"], quantity=validated["quantity"],
            price=validated["price"], stop_price=validated["stop_price"],
        )

        click.echo()

        # -- Response --
        resp_rows = [
            ("Order ID", str(response.get("orderId", "N/A"))),
            ("Symbol", response.get("symbol", "N/A")),
            ("Side", response.get("side", "N/A")),
            ("Type", response.get("type", "N/A")),
            ("Status", response.get("status", "N/A")),
            ("Quantity", response.get("origQty", "N/A")),
            ("Executed Qty", response.get("executedQty", "N/A")),
            ("Price", response.get("price", "N/A")),
            ("Avg Price", response.get("avgPrice", "N/A")),
        ]
        if response.get("stopPrice") and response["stopPrice"] != "0":
            resp_rows.append(("Stop Price", response["stopPrice"]))

        print_box("ORDER RESPONSE", resp_rows)
        click.echo()

        result_status = response.get("status", "UNKNOWN")
        if result_status in ("NEW", "FILLED", "PARTIALLY_FILLED"):
            status("[OK]", f"Order placed successfully. Status: {result_status}", "green")
        else:
            status("[!!]", f"Order status: {result_status}", "yellow")

        logger.info(f"Order completed. Status: {result_status}")

    except ValidationError as e:
        click.echo()
        status("[ERROR]", f"Validation failed: {e}", "red")
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    except AuthenticationError as e:
        click.echo()
        status("[ERROR]", f"Authentication failed: {e}", "red")
        status("      ", "Set BINANCE_API_KEY and BINANCE_API_SECRET in .env", "yellow")
        logger.error(f"Auth failed: {e}")
        sys.exit(1)

    except BinanceAPIError as e:
        click.echo()
        status("[ERROR]", f"API error: {e}", "red")
        logger.error(f"API error: {e}")
        sys.exit(1)

    except NetworkError as e:
        click.echo()
        status("[ERROR]", f"Network error: {e}", "red")
        status("      ", "Check your internet connection and try again.", "yellow")
        logger.error(f"Network error: {e}")
        sys.exit(1)

    except TradingBotError as e:
        click.echo()
        status("[ERROR]", str(e), "red")
        logger.error(str(e))
        sys.exit(1)

    except Exception as e:
        click.echo()
        status("[ERROR]", f"Unexpected: {e}", "red")
        logger.exception(str(e))
        sys.exit(1)


# ──────────────────────────────────────────────────────────────
# Account Info Command
# ──────────────────────────────────────────────────────────────

@cli.command()
def account():
    """Display Binance Futures Testnet account info."""
    logger = setup_logging(log_dir="logs")

    click.echo(click.style(BANNER, fg="cyan"))

    try:
        status("[..]", "Fetching account info...", "cyan")
        client = get_client()
        info = client.get_account_info()

        assets = []
        for asset in info.get("assets", []):
            if float(asset.get("walletBalance", 0)) > 0:
                bal = float(asset["walletBalance"])
                avail = float(asset.get("availableBalance", 0))
                assets.append((asset["asset"], f"{bal:,.4f}  (available: {avail:,.4f})"))

        click.echo()
        if assets:
            print_box("ACCOUNT BALANCES", assets)
        else:
            status("[!!]", "No assets with positive balance found.", "yellow")

        click.echo()

    except TradingBotError as e:
        click.echo()
        status("[ERROR]", str(e), "red")
        logger.error(f"Account info error: {e}")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────
# Price Check Command
# ──────────────────────────────────────────────────────────────

@cli.command()
@click.option("--symbol", "-s", required=True, help="Trading pair symbol (e.g., BTCUSDT).")
def price(symbol):
    """Fetch current price for a trading pair (no API key required)."""
    import requests as req

    logger = setup_logging(log_dir="logs")

    click.echo(click.style(BANNER, fg="cyan"))

    try:
        symbol = symbol.strip().upper()
        status("[..]", f"Fetching {symbol} price...", "cyan")

        resp = req.get(
            "https://testnet.binancefuture.com/fapi/v1/ticker/price",
            params={"symbol": symbol}, timeout=10,
        )
        data = resp.json()

        if resp.status_code != 200 or "code" in data:
            raise TradingBotError(data.get("msg", "Failed to fetch price"))

        current_price = float(data.get("price", 0))
        click.echo()
        print_box("PRICE", [(symbol, f"${current_price:,.2f}")])
        click.echo()
        logger.info(f"Price check: {symbol} = {current_price}")

    except req.exceptions.RequestException as e:
        click.echo()
        status("[ERROR]", f"Network error: {e}", "red")
        logger.error(f"Price check error: {e}")
        sys.exit(1)
    except TradingBotError as e:
        click.echo()
        status("[ERROR]", str(e), "red")
        logger.error(f"Price check error: {e}")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
