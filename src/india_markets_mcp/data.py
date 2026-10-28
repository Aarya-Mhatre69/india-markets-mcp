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

_cache: dict[tuple[str, str, str], tuple[float, pd.DataFrame]] = {}


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


def fetch_history(symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV history, cached for a few minutes and retried on failure.

    Raises SymbolNotFoundError if nothing comes back, DataSourceError if the
    upstream keeps failing.
    """
    ticker = normalize_symbol(symbol)
    key = (ticker, period, interval)

    hit = _cache.get(key)
    if hit is not None and time.monotonic() - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]

    last_error: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            df = _download(ticker, period, interval)
        except Exception as exc:  # yfinance raises a wide range of errors
            last_error = exc
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_BACKOFF_SECONDS * 2**attempt)
            continue
        if df is None or df.empty:
            raise SymbolNotFoundError(
                f"no data for {symbol!r} (tried {ticker}). "
                "Use an NSE symbol like RELIANCE, a .BO symbol, or NIFTY/BANKNIFTY/SENSEX."
            )
        _cache[key] = (time.monotonic(), df)
        return df

    raise DataSourceError(
        f"data source failed for {ticker} after {RETRY_ATTEMPTS} attempts: {last_error}"
    )
