#!/usr/bin/env python3
"""
Trading Bot - Main Entry Point
===============================
Single entry point that initializes all components and runs the CLI.

Usage:
    python main.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python main.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500
    python main.py order --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 80000 --stop-price 79000
    python main.py price --symbol BTCUSDT
    python main.py account
"""

import os
import sys

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import cli


def run():
    """
    Main entry point for the trading bot application.
    Initializes and runs the Click CLI dispatcher.
    """
    cli()


if __name__ == "__main__":
    run()
