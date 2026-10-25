"""Tool logic. Takes price frames in, returns JSON-friendly dicts out."""

from __future__ import annotations

import pandas as pd

from . import data, indicators


def quote_from_history(symbol: str, df: pd.DataFrame) -> dict:
    close = df["Close"]
    last, prev = float(close.iloc[-1]), float(close.iloc[-2])
    window = close.tail(252)
    return {
        "symbol": data.normalize_symbol(symbol),
        "as_of": df.index[-1].strftime("%Y-%m-%d"),
        "close": round(last, 2),
        "change_pct": round((last / prev - 1) * 100, 2),
        "high_52w": round(float(window.max()), 2),
        "low_52w": round(float(window.min()), 2),
        "pct_from_52w_high": round((last / float(window.max()) - 1) * 100, 2),
        "volume": int(df["Volume"].iloc[-1]),
    }


def signals_from_history(symbol: str, df: pd.DataFrame) -> dict:
    close = df["Close"]
    rsi14 = float(indicators.rsi(close).iloc[-1])
    mom = indicators.momentum_12_1(close)
    return {
        "symbol": data.normalize_symbol(symbol),
        "as_of": df.index[-1].strftime("%Y-%m-%d"),
        "rsi14": round(rsi14, 1),
        "rsi_state": "overbought" if rsi14 >= 70 else "oversold" if rsi14 <= 30 else "neutral",
        "volatility_30d_annualised": round(indicators.annualised_volatility(close), 3),
        "max_drawdown_period": round(indicators.max_drawdown(close), 3),
        "momentum_12_1": None if mom is None else round(mom, 3),
        **indicators.classify_regime(close),
    }


def compare_from_histories(frames: dict[str, pd.DataFrame]) -> list[dict]:
    """Total return and volatility over each frame's span, best first."""
    rows = []
    for symbol, df in frames.items():
        close = df["Close"]
        rows.append(
            {
                "symbol": data.normalize_symbol(symbol),
                "return_pct": round((float(close.iloc[-1] / close.iloc[0]) - 1) * 100, 2),
                "volatility_annualised": round(indicators.annualised_volatility(close, len(close)), 3),
                "max_drawdown": round(indicators.max_drawdown(close), 3),
            }
        )
    return sorted(rows, key=lambda r: r["return_pct"], reverse=True)


def get_quote(symbol: str) -> dict:
    return quote_from_history(symbol, data.fetch_history(symbol, period="1y"))


def get_signals(symbol: str) -> dict:
    return signals_from_history(symbol, data.fetch_history(symbol, period="2y"))


def compare(symbols: list[str], period: str = "1y") -> list[dict]:
    if not 2 <= len(symbols) <= 10:
        raise ValueError("provide between 2 and 10 symbols")
    return compare_from_histories({s: data.fetch_history(s, period=period) for s in symbols})
