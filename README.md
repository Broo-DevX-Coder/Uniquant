# ⚠️ Disclaimer

> UniQuant is an open-source project developed solely for educational and experimental purposes.
Any use of this library for unethical or illegal purposes is strictly prohibited, including but not limited to:
Engaging in pump-and-dump schemes or buying tokens that are questionable under Islamic law (Shariah)
Utilizing this library for futures trading, leveraged trading, or other high-risk financial instruments
Employing this tool in unregulated or illegal markets
The author assumes no responsibility for misuse or violations of legal, ethical, or religious standards.
Users must ensure compliance with all local laws, exchange policies, and religious guidelines.

❌ Project Status: Discontinued

> This project has been discontinued and is no longer maintained.
The reason for stopping development is that more powerful and robust libraries are now available, offering broader support, improved performance, and more flexibility than what this project provides.
Developers are encouraged to explore and adopt those more complete alternatives depending on their specific needs.

# 📘 LBank AsyncClient Usage Guide

This guide explains how to use the `AsyncClient` class for interacting with LBank's spot trading API asynchronously using Python.

## 🧩 Setup

```python
client = AsyncClient(api="YOUR_API_KEY", secret="YOUR_API_SECRET")
```

* `api`: Your public API key from LBank.
* `secret`: Your private API secret.

## 🔁 Session Management

### Option 1: Context manager (recommended)

```python
async with AsyncClient(api, secret) as client:
    # use the client here
```

### Option 2: Manual

```python
client = AsyncClient(api, secret)
# use client functions
await client.close()  # close the session manually
```

## 🌐 Public Methods

### 🔸 `get_all_pairs()`

```python
pairs = await client.get_all_pairs()
```

* **Returns**: A `set` of all spot trading pairs like `{"btc_usdt", "eth_usdt", ...}`.
* **Error Handling**: Raises `RequestCodeError` or `UnknownError` if failed.

### 🔸 `get_pairs_info(symbol: str = None)`

```python
all_info = await client.get_pairs_info()
one_pair_info = await client.get_pairs_info("btc_usdt")
```

* **Returns**: A list of dictionaries containing precision and configuration info per pair.
* **If `symbol` is given**: returns info only for that pair.
* **Error Handling**: Raises `RequestCodeError` or `UnknownError`.

### 🔸 `order_book(code: str, limit: int)`

```python
orderbook = await client.order_book("btc_usdt", 20)
```

* **Arguments**:

  * `code`: trading pair like `btc_usdt`.
  * `limit`: number of entries to fetch.
* **Returns**: Order book data from LBank API.
* **Error Handling**: Raises `RequestCodeError` or `UnknownError`.

## 🔐 Private Method (Authenticated)

### 🔸 `place_order(symbol: str, type_: str, amount: dict, price: dict = None)`

Place a spot order (limit or market).

```python
# Limit order example
await client.place_order(
    symbol="btc_usdt",
    type_="buy_limit",
    amount={"value": 0.01, "checkScal": 6},
    price={"value": 30000, "checkScal": 2}
)

# Market order example
await client.place_order(
    symbol="btc_usdt",
    type_="buy_market",
    amount={"value": 20, "checkScal": 2}
)
```

* **Arguments**:

  * `symbol`: Trading pair (`"btc_usdt"`, etc).
  * `type_`: `"buy_limit"`, `"sell_limit"`, `"buy_market"`, `"sell_market"`.
  * `amount`: Dict with `value` and `checkScal` (decimals).
  * `price`: Only required for limit orders. Dict with `value` and `checkScal`.

* **Returns**: Order response from the LBank server.

* **Error Handling**:

  * `ValueError` if missing or incorrect parameters.
  * `RequestCodeError` or `UnknownError` on request failure.

## ⚠️ Exceptions

These custom exceptions must be defined in `__exeptions__` module:

```python
class RequestCodeError(Exception):
    pass

class UnknownError(Exception):
    pass
```

If not already created, define these to handle API and network issues gracefully.

## 🧪 Notes

* The `generate_sign()` method uses `HMAC-SHA256` on an MD5-encoded string (as required by LBank).
* Make sure to use `await` with all methods since this client is asynchronous.
* Always close the session to avoid memory leaks.


> More things coming soon ...
