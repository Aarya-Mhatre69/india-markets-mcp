"""Data access. The only module that touches the network (via yfinance)."""

from __future__ import annotations

import logging
import time
import warnings

import pandas as pd
import yfinance as yf

# yfinance logs and warns on stderr; MCP clients surface that as noise.
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", module=r"yfinance(\..*)?")

INDEX_ALIASES = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
}

CACHE_TTL_SECONDS = 300
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.0

_cache: dict[tuple, tuple[float, object]] = {}


class SymbolNotFoundError(ValueError):
    """The upstream source has no data for this symbol."""


class DataSourceError(RuntimeError):
    """The upstream source failed (rate limit, network, schema change)."""


def normalize_symbol(symbol: str) -> str:
    """Map user input to a Yahoo Finance ticker.

    ``RELIANCE`` -> ``RELIANCE.NS``; ``TCS.BO`` and ``^NSEI`` pass through;
    ``NIFTY``/``BANKNIFTY``/``SENSEX`` map to their index tickers.
    """
    s = symbol.strip().upper()
    if not s:
        raise ValueError("symbol must not be empty")
    if s in INDEX_ALIASES:
        return INDEX_ALIASES[s]
    if s.startswith("^") or s.endswith((".NS", ".BO")):
        return s
    return f"{s}.NS"


def clear_cache() -> None:
    _cache.clear()


def _download(ticker: str, period: str, interval: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)


def _cached_fetch(key: tuple, label: str, loader, symbol: str):
    """Cache + retry wrapper. ``loader`` returns a value, or None/empty for "not found"."""
    hit = _cache.get(key)
    if hit is not None and time.monotonic() - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]

    last_error: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            value = loader()
        except Exception as exc:  # yfinance raises a wide range of errors
            last_error = exc
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_BACKOFF_SECONDS * 2**attempt)
            continue
        if value is None or (hasattr(value, "empty") and value.empty):
            raise SymbolNotFoundError(
                f"no data for {symbol!r} (tried {label}). "
                "Use an NSE symbol like RELIANCE, a .BO symbol, or NIFTY/BANKNIFTY/SENSEX."
            )
        _cache[key] = (time.monotonic(), value)
        return value

    raise DataSourceError(
        f"data source failed for {label} after {RETRY_ATTEMPTS} attempts: {last_error}"
    )


def fetch_history(symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV history, cached for a few minutes and retried on failure.

    Raises SymbolNotFoundError if nothing comes back, DataSourceError if the
    upstream keeps failing.
    """
    ticker = normalize_symbol(symbol)
    return _cached_fetch(
        ("history", ticker, period, interval),
        ticker,
        lambda: _download(ticker, period, interval),
        symbol,
    )


def _download_info(ticker: str) -> dict | None:
    info = yf.Ticker(ticker).info
    # Yahoo returns a near-empty dict for unknown tickers.
    return info if info and (info.get("longName") or info.get("shortName")) else None


def fetch_info(symbol: str) -> dict:
    """Company profile and valuation fields (P/E, P/B, market cap...), cached and retried."""
    ticker = normalize_symbol(symbol)
    return _cached_fetch(("info", ticker), ticker, lambda: _download_info(ticker), symbol)
