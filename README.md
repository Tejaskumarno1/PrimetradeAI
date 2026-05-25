# Binance Futures Testnet Trading Bot

A Python CLI application for placing orders on Binance Futures Testnet (USDT-M). Supports Market, Limit, and Stop-Limit orders with structured logging, input validation, and clean error handling.

---

## Features

- **Market Orders** -- Execute immediately at current market price
- **Limit Orders** -- Set a specific price with GTC (Good-Til-Canceled)
- **Stop-Limit Orders** (Bonus) -- Trigger limit orders at a stop price
- **Input Validation** -- Symbol, side, type, quantity, and price checks
- **Structured Logging** -- DEBUG to file, INFO to console
- **Clean CLI** -- Colored output, confirmation prompts, formatted tables
- **Error Handling** -- Custom exceptions for API, network, auth, and validation errors
- **Bonus Utilities** -- Account info and live price check commands

---

## Setup

### 1. Prerequisites

- Python 3.8+
- Binance Futures Testnet account (https://testnet.binancefuture.com/)

### 2. Clone and Install

```bash
git clone <your-repo-url>
cd trading_bot

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Credentials

```bash
# Copy the example env file
cp .env.example .env

# Edit with your Binance Futures Testnet API keys
nano .env
```

Set your credentials:
```
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

> **Important:** Never commit your `.env` file. It is excluded via `.gitignore`.

---

## Usage

All commands are run through `main.py`:

### Place a Market Order

```bash
python main.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a Limit Order

```bash
python main.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3500
```

### Place a Stop-Limit Order (Bonus)

```bash
python main.py order --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 100000 --stop-price 99000
```

### Check Current Price

```bash
python main.py price --symbol BTCUSDT
```

### View Account Info

```bash
python main.py account
```

### Help

```bash
python main.py --help
python main.py order --help
```

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package init + version
│   ├── client.py            # Binance API client (signing, HTTP, errors)
│   ├── orders.py            # Order placement logic + response formatting
│   ├── validators.py        # Input validation (symbol, side, type, qty, price)
│   ├── exceptions.py        # Custom exception hierarchy
│   └── logging_config.py    # Dual logging setup (file + console)
├── logs/                    # Auto-generated log files
│   ├── market_order_*.log
│   └── limit_order_*.log
├── main.py                  # Main entry point (run function)
├── cli.py                   # CLI dispatcher (Click)
├── .env.example             # API credential template
├── .gitignore               # Excludes .env, __pycache__, etc.
├── requirements.txt         # Python dependencies
├── PROJECT_WALKTHROUGH.md   # Detailed breakdown of code & data flow
└── README.md                # This file
```

---

## Architecture

| Layer | File | Responsibility |
|-------|------|---------------|
| **Entry Point** | `main.py` | Single run() function, boots the app |
| **CLI** | `cli.py` | User interaction, input collection, output display |
| **Validation** | `validators.py` | Input sanitization, format checks, error messages |
| **Business Logic** | `orders.py` | Order construction, API param mapping, response formatting |
| **Transport** | `client.py` | HTTP requests, HMAC-SHA256 signing, error translation |
| **Logging** | `logging_config.py` | File handler (DEBUG) + console handler (CRITICAL/silent) |
| **Exceptions** | `exceptions.py` | ValidationError, BinanceAPIError, NetworkError, AuthenticationError |

---

## Sample Output

```
  _____ ____      _    ____ ___ _   _  ____   ____   ___ _____
 |_   _|  _ \    / \  |  _ \_ _| \ | |/ ___| | __ ) / _ \_   _|
   | | | |_) |  / _ \ | | | | ||  \| | |  _  |  _ \| | | || |
   | | |  _ <  / ___ \| |_| | || |\  | |_| | | |_) | |_| || |
   |_| |_| \_\/_/   \_\____/___|_| \_|\____| |____/ \___/ |_|

   Binance Futures Testnet  |  USDT-M  |  v1.0.0

  [..] Validating inputs...
  [OK] Input validation passed.

+=========================================================+
|  ORDER REQUEST                                          |
+---------------------------------------------------------+
|             Symbol: BTCUSDT                             |
|               Side: BUY                                 |
|         Order Type: MARKET                              |
|           Quantity: 0.001                               |
+=========================================================+

  --> Confirm and place this order? [Y/n]: Y

  [..] Connecting to Binance Futures Testnet...
  [..] Placing order...

+=========================================================+
|  ORDER RESPONSE                                         |
+---------------------------------------------------------+
|           Order ID: 123456789                           |
|             Symbol: BTCUSDT                             |
|               Side: BUY                                 |
|               Type: MARKET                              |
|             Status: FILLED                              |
|           Quantity: 0.001                               |
|       Executed Qty: 0.001                               |
|          Avg Price: 67500.00                            |
+=========================================================+

  [OK] Order placed successfully. Status: FILLED
```

---

## Assumptions

1. **Testnet Only** -- This bot is configured exclusively for `https://testnet.binancefuture.com`. Do NOT use with mainnet credentials.
2. **USDT-M Futures** -- Uses the USDT-margined futures API (`/fapi/v1/`).
3. **Time in Force** -- Limit orders default to GTC (Good-Til-Canceled).
4. **No Position Management** -- This bot places individual orders; it does not manage open positions or implement trading strategies.
5. **Testnet Balances** -- Testnet accounts come with virtual funds. No real money is used.
6. **System Clock** -- The signing mechanism relies on timestamps. Ensure your system clock is synchronized (within 1000ms of Binance servers).
7. **API Key Generation** -- Binance has migrated testnet key generation to demo.binance.com. The API base URL (`https://testnet.binancefuture.com`) remains functional for order execution.

---

## Testing

### Pre-included Log Files

Sample log files are included in `logs/` demonstrating:
- `market_order_20260525_100500.log` -- MARKET BUY order on BTCUSDT
- `limit_order_20260525_100530.log` -- LIMIT SELL order on ETHUSDT

### Run with your own credentials

```bash
# Set up your .env file first, then:

# Market order
python main.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit order
python main.py order --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 5000

# Stop-Limit order (bonus)
python main.py order --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 100000 --stop-price 99000

# Check logs
ls logs/
cat logs/*.log
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `requests` | HTTP client for REST API calls |
| `click` | CLI framework with validation and help text |
| `python-dotenv` | Load API credentials from `.env` file |

---

## License

Built as a coding assessment for Primetrade.ai.
