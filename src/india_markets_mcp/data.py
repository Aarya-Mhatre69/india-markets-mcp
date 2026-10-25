"""Data access. The only module that touches the network (via yfinance)."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

INDEX_ALIASES = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "SENSEX": "^BSESN",
}


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


def fetch_history(symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV history. Raises ValueError if nothing comes back."""
    ticker = normalize_symbol(symbol)
    df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"no data returned for {symbol!r} (tried {ticker})")
    return df
