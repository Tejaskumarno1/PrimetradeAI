# Project Walkthrough -- How The Trading Bot Works

A line-by-line breakdown of every file, how they connect, and how data flows
from user input to Binance API and back.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Data Flow Diagram](#2-data-flow-diagram)
3. [File-by-File Breakdown](#3-file-by-file-breakdown)
   - [main.py](#mainpy----entry-point)
   - [cli.py](#clipy----cli-dispatcher)
   - [bot/\_\_init\_\_.py](#bot__init__py----package-marker)
   - [bot/exceptions.py](#botexceptionspy----error-types)
   - [bot/logging_config.py](#botlogging_configpy----log-setup)
   - [bot/validators.py](#botvalidatorspy----input-validation)
   - [bot/orders.py](#botorderspy----order-logic)
   - [bot/client.py](#botclientpy----api-transport)
4. [How an Order Flows Through the System](#4-how-an-order-flows-through-the-system)
5. [Error Handling Chain](#5-error-handling-chain)
6. [Logging Strategy](#6-logging-strategy)
7. [Testing Summary](#7-testing-summary)

---

## 1. Project Overview

```
trading_bot/
├── main.py                  # Entry point -- calls run() which boots CLI
├── cli.py                   # Click CLI -- 3 commands: order, price, account
├── bot/
│   ├── __init__.py          # Package marker with version info
│   ├── exceptions.py        # 5 custom exception classes
│   ├── logging_config.py    # Dual logging: file (DEBUG) + console (silent)
│   ├── validators.py        # 6 validation functions + 1 aggregate
│   ├── orders.py            # OrderManager class -- builds params, calls API
│   └── client.py            # BinanceClient -- HTTP, HMAC signing, errors
├── logs/                    # Auto-generated log files
├── .env.example             # API key template
├── requirements.txt         # 3 dependencies
└── README.md                # Setup and usage docs
```

**Layer separation:**
- `main.py` / `cli.py` = User interface (what the user sees)
- `bot/validators.py` = Input gate (reject bad data before it reaches API)
- `bot/orders.py` = Business logic (build the right params for each order type)
- `bot/client.py` = Transport (HTTP requests, signing, error translation)

---

## 2. Data Flow Diagram

```
User types command
       |
       v
  +---------+     +--------------+     +--------------+     +---------------+
  | main.py | --> |   cli.py     | --> | validators.py| --> |  orders.py    |
  | run()   |     | order()      |     | validate_all |     | place_order() |
  +---------+     +--------------+     +--------------+     +---------------+
                                                                   |
                                                                   v
                                                            +-------------+
                                                            | client.py   |
                                                            | _request()  |
                                                            +-------------+
                                                                   |
                                                                   v
                                                          Binance Testnet API
                                                          POST /fapi/v1/order
                                                                   |
                                                                   v
                                                            JSON response
                                                                   |
                                                                   v
                                                       cli.py formats and
                                                       prints to terminal
```

---

## 3. File-by-File Breakdown

---

### main.py -- Entry Point

**Purpose:** Single entry point. Imports the CLI and runs it.

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```
- Adds the project root to Python's import path so `from cli import cli` works
  regardless of where you run the script from.

```python
from cli import cli

def run():
    cli()
```
- `run()` is the single function that boots the entire application.
- `cli()` is a Click group -- it dispatches to `order`, `price`, or `account`
  based on the subcommand the user typed.

```python
if __name__ == "__main__":
    run()
```
- Standard Python entry point guard. When you run `python main.py order ...`,
  this calls `run()` which calls `cli()` which dispatches to the right command.

---

### cli.py -- CLI Dispatcher

**Purpose:** Defines all user-facing commands, handles display, and catches errors.

**Key sections:**

#### Display Helpers (lines 35-77)

```python
BANNER = r"""
  _____ ____      _    ____ ___ _   _  ____   ____   ___ _____
 |_   _|  _ \    / \  |  _ \_ _| \ | |/ ___| | __ ) / _ \_   _|
   ...
"""
```
- ASCII art banner shown at the top of every command.

```python
W = 57  # box width

def line(char="-"):
    return "+" + char * W + "+"

def row(label, value, label_w=17):
    content = f"  {label:>{label_w}}: {value}"
    return "|" + f"{content:<{W}}" + "|"
```
- Helper functions that build clean ASCII box-drawing for terminal output.
- `line("=")` produces `+=========...=+`
- `row("Symbol", "BTCUSDT")` produces `|           Symbol: BTCUSDT          |`

```python
def print_box(title, rows):
    click.echo(line("="))
    click.echo(header(title))
    click.echo(line("-"))
    for label, value in rows:
        click.echo(row(label, value))
    click.echo(line("="))
```
- Assembles a complete bordered table for any set of key-value pairs.

#### The `order` Command (lines 111-243)

This is the main command. Step by step:

1. **Setup logging** -- `logger = setup_logging(log_dir="logs")`
2. **Print banner** -- ASCII art header
3. **Validate inputs** -- Calls `validate_all()` which runs 6 validators
4. **Show request summary** -- Builds rows from validated params, prints a box
5. **Ask confirmation** -- `click.confirm()` asks user Y/n before placing
6. **Create client** -- `get_client()` reads API keys from `.env`
7. **Place order** -- `order_mgr.place_order(...)` sends to Binance
8. **Show response** -- Builds rows from API response, prints another box
9. **Error handling** -- 6 `except` blocks catch every possible failure type

#### The `price` Command (lines 288-326)

- Hits the public endpoint `/fapi/v1/ticker/price` directly with `requests.get()`
- Does NOT require API keys (public endpoint)
- Formats the price in a box: `$77,312.50`

#### The `account` Command (lines 250-281)

- Calls `client.get_account_info()` (signed request, needs API keys)
- Loops through assets, shows any with positive balance

---

### bot/\_\_init\_\_.py -- Package Marker

```python
__version__ = "1.0.0"
__author__ = "Tejas"
```
- Makes `bot/` a Python package so `from bot.client import BinanceClient` works.
- Stores version and author metadata.

---

### bot/exceptions.py -- Error Types

**Purpose:** Custom exception hierarchy so each layer can throw and catch
specific error types.

```
TradingBotError (base)
├── ValidationError      -- bad user input (wrong symbol, negative qty, etc.)
├── BinanceAPIError      -- Binance returns 4xx/5xx with error code
│     .status_code       -- HTTP status (400, 401, etc.)
│     .error_code        -- Binance error code (-1102, -2010, etc.)
│     .message           -- Human-readable error message
├── NetworkError         -- connection timeout, DNS failure, etc.
└── AuthenticationError  -- missing or empty API keys
```

**Why this matters:**
- `cli.py` has separate `except` blocks for each type
- Each shows a different error message and tip to the user
- All inherit from `TradingBotError` so there's a catch-all fallback

---

### bot/logging_config.py -- Log Setup

**Purpose:** Creates a logger with two handlers.

```python
logger = logging.getLogger("trading_bot")
```
- All modules use child loggers: `trading_bot.client`, `trading_bot.orders`, etc.
- They all inherit from this root logger.

**File Handler (DEBUG level):**
```python
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
```
- Writes EVERYTHING to `logs/trading_bot_YYYYMMDD_HHMMSS.log`
- Format: `2026-05-25 10:05:01 | DEBUG | trading_bot.client._request:110 | API Request: POST ...`
- Includes: timestamp, level, module, function name, line number, message

**Console Handler (CRITICAL level):**
```python
console_handler.setLevel(logging.CRITICAL)
```
- Set to CRITICAL so NO log lines appear in terminal output
- All user-facing output is handled by `click.echo()` in `cli.py`
- This keeps the terminal output clean and professional

**Duplicate prevention:**
```python
if logger.handlers:
    return logger
```
- If `setup_logging()` is called multiple times (e.g., by different commands),
  it returns the existing logger instead of adding duplicate handlers.

---

### bot/validators.py -- Input Validation

**Purpose:** Fail fast. Reject bad input before it ever reaches the API.

**6 individual validators + 1 aggregate:**

| Function | What it checks | Error example |
|---|---|---|
| `validate_symbol(s)` | Non-empty, alphanumeric, 2-20 chars | `"" -> "Symbol cannot be empty"` |
| `validate_side(s)` | Must be BUY or SELL | `"HOLD" -> "Must be one of: BUY, SELL"` |
| `validate_order_type(t)` | Must be MARKET, LIMIT, or STOP | `"FOK" -> "Must be one of: ..."` |
| `validate_quantity(q)` | Must be positive number | `-1 -> "must be positive"` |
| `validate_price(p, type)` | Required for LIMIT/STOP, must be positive | `None + LIMIT -> "Price is required"` |
| `validate_stop_price(sp, type)` | Required for STOP, must be positive | `None + STOP -> "Stop price is required"` |
| `validate_all(...)` | Runs all 6 above, returns clean dict | Returns `{"symbol": "BTCUSDT", ...}` |

**Key design choice:** Each validator is a pure function that takes input and
returns validated output or raises `ValidationError`. This makes them easy to
test independently.

**Symbol validation detail:**
```python
if not re.match(r"^[A-Z0-9]{2,20}$", symbol):
    raise ValidationError(...)
```
- Regex ensures only uppercase letters and digits, 2-20 characters
- Warns (but allows) symbols that don't end with USDT/BUSD/USD

---

### bot/orders.py -- Order Logic

**Purpose:** Translates validated user input into the exact parameters
Binance API expects, then calls the client.

**`OrderManager.place_order()`:**

```python
params = {
    "symbol": symbol,
    "side": side,
    "type": self._map_order_type(order_type),
    "quantity": str(quantity),
}
```
- Builds the base parameter dict that every order type needs.
- Quantity is converted to string -- Binance API expects string numbers.

```python
if order_type in ("LIMIT", "STOP"):
    params["price"] = str(price)
    params["timeInForce"] = time_in_force  # defaults to "GTC"
```
- LIMIT and STOP orders need a price and timeInForce.
- GTC = Good-Til-Canceled (stays open until filled or manually canceled).

```python
if order_type == "STOP":
    params["stopPrice"] = str(stop_price)
```
- STOP orders additionally need a `stopPrice` -- the trigger price.

Then it calls:
```python
response = self._client.place_order(**params)
```
- Passes all params to `BinanceClient.place_order()` which sends the HTTP request.

**Logging:** Both request summary and response are logged to file via
`_log_order_summary()` and `_log_order_response()`.

---

### bot/client.py -- API Transport

**Purpose:** The lowest layer. Handles HTTP, authentication (HMAC-SHA256),
and error translation. No business logic here.

#### Constructor

```python
self._session = requests.Session()
self._session.headers.update({
    "X-MBX-APIKEY": self._api_key,
    "Content-Type": "application/x-www-form-urlencoded",
})
```
- Creates a persistent HTTP session (connection pooling, faster requests).
- Sets the API key header that Binance requires on every request.

#### HMAC-SHA256 Signing

```python
def _generate_signature(self, params):
    query_string = urlencode(params)
    signature = hmac.new(
        self._api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return signature
```
- Binance requires every signed request to include an HMAC-SHA256 signature.
- Process: take all query params as a URL-encoded string, hash them with
  your secret key, and append the result as a `signature` parameter.

#### Request Flow (`_request` method)

1. Build URL: `https://testnet.binancefuture.com/fapi/v1/order`
2. If signed: add `timestamp` (milliseconds) and `signature`
3. Send request:
   - GET requests: params go in URL query string
   - POST requests: params go in request body (form-encoded)
4. Parse JSON response
5. If status >= 400: extract Binance error code and raise `BinanceAPIError`
6. If connection fails: raise `NetworkError`
7. Return parsed dict

#### Security

```python
def _sanitize_params(params):
    sanitized = dict(params)
    if "signature" in sanitized:
        sanitized["signature"] = "***"
    return sanitized
```
- The signature is masked in log output so it never appears in log files.

---

## 4. How an Order Flows Through the System

Example: `python main.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001`

```
Step 1: main.py
  run() -> cli()

Step 2: cli.py
  Click parses arguments:
    symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.001

Step 3: cli.py -> bot/validators.py
  validate_all() runs:
    validate_symbol("BTCUSDT")    -> "BTCUSDT"   (uppercase, regex match)
    validate_side("BUY")          -> "BUY"        (in allowed list)
    validate_order_type("MARKET") -> "MARKET"     (in allowed list)
    validate_quantity(0.001)      -> 0.001         (positive float)
    validate_price(None, "MARKET")-> None          (not required for MARKET)
    validate_stop_price(None, "MARKET") -> None    (not required for MARKET)
  Returns: {"symbol": "BTCUSDT", "side": "BUY", "order_type": "MARKET", ...}

Step 4: cli.py shows request summary box to user

Step 5: cli.py asks "Confirm and place this order? [Y/n]"

Step 6: cli.py -> bot/client.py
  get_client() reads BINANCE_API_KEY and BINANCE_API_SECRET from .env
  BinanceClient.__init__() creates session with API key header

Step 7: cli.py -> bot/orders.py -> bot/client.py
  OrderManager.place_order() builds params:
    {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": "0.001"}
  
  BinanceClient.place_order() calls _request("POST", "/fapi/v1/order", params)
  
  _request() adds:
    params["timestamp"] = 1779684301000
    params["signature"] = hmac_sha256(all_params, secret_key)
  
  Sends HTTP POST to:
    https://testnet.binancefuture.com/fapi/v1/order
    Body: symbol=BTCUSDT&side=BUY&type=MARKET&quantity=0.001&timestamp=...&signature=...
    Header: X-MBX-APIKEY: your_api_key

Step 8: Binance returns JSON:
  {"orderId": 123456, "status": "FILLED", "executedQty": "0.001", ...}

Step 9: cli.py shows response box with orderId, status, executedQty, avgPrice

Step 10: Log file captures everything (request, response, timestamps)
```

---

## 5. Error Handling Chain

Errors are caught in `cli.py` with this priority:

```
ValidationError       -> "[ERROR] Validation failed: ..."
AuthenticationError   -> "[ERROR] Authentication failed: ..." + tip about .env
BinanceAPIError       -> "[ERROR] API error: Binance API Error [400] ..."
NetworkError          -> "[ERROR] Network error: ..." + tip about internet
TradingBotError       -> "[ERROR] ..." (catch-all for bot errors)
Exception             -> "[ERROR] Unexpected: ..." (catch-all for everything)
```

Each error:
1. Prints a colored message to the terminal via `click.echo()`
2. Logs the full error to the log file via `logger.error()`
3. Exits with code 1 via `sys.exit(1)`

---

## 6. Logging Strategy

| What gets logged | Where | Level |
|---|---|---|
| Validation steps (each field) | File only | DEBUG |
| Validation result (full dict) | File only | INFO |
| API request (method, endpoint, sanitized params) | File only | DEBUG |
| HMAC signature generation | File only | DEBUG |
| API response (status code, body) | File only | DEBUG |
| Order summary (symbol, side, type, qty) | File only | INFO |
| Order response (orderId, status, etc.) | File only | INFO |
| Errors (validation, API, network) | File only | ERROR |
| User-facing output | Terminal only | via click.echo() |

**Design principle:** The log file tells the full story for debugging.
The terminal shows only what the user needs to see.

---

## 7. Testing Summary

**9 integration tests verified:**

| Test | Result |
|---|---|
| HMAC-SHA256 signing produces 64-char hex | PASS |
| Empty API key raises AuthenticationError | PASS |
| API key stored in session headers | PASS |
| Signature masked in log output | PASS |
| Timestamp in milliseconds | PASS |
| OrderManager formatting | PASS |
| Numeric symbols (1INCHUSDT) | PASS |
| Very small quantities (0.00001) | PASS |
| Zero quantity rejected | PASS |

**8 validation tests verified:**

| Test | Result |
|---|---|
| Empty symbol rejected | PASS |
| Invalid side "HOLD" rejected | PASS |
| Missing LIMIT price rejected | PASS |
| Negative quantity rejected | PASS |
| Valid MARKET order passes | PASS |
| Valid LIMIT order passes | PASS |
| Missing STOP price rejected | PASS |
| Valid STOP order passes | PASS |

**No bugs found.** All code is working correctly.
