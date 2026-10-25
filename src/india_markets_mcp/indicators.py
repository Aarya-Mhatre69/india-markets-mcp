"""Pure pandas indicators. No network access, so everything here is unit-testable."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's RSI. Returns 100 when there are no losses in the window."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.where(loss != 0, 100.0)


def annualised_volatility(close: pd.Series, window: int = 30) -> float:
    returns = close.pct_change().dropna().tail(window)
    return float(returns.std() * np.sqrt(TRADING_DAYS))


def max_drawdown(close: pd.Series) -> float:
    """Largest peak-to-trough fall as a negative fraction (e.g. -0.25)."""
    running_peak = close.cummax()
    return float((close / running_peak - 1).min())


def momentum_12_1(close: pd.Series) -> float | None:
    """Return from ~12 months ago to ~1 month ago, skipping the latest month."""
    if len(close) < 253:
        return None
    return float(close.iloc[-22] / close.iloc[-253] - 1)


def classify_regime(close: pd.Series) -> dict:
    """Rule-based trend regime from price vs the 50/200-day averages.

    Deliberately simple and fully explained in the output, so an agent (or a
    human) can see exactly why a label was chosen.
    """
    if len(close) < 200:
        raise ValueError("need at least 200 daily closes to classify a regime")

    last = float(close.iloc[-1])
    ma50 = float(sma(close, 50).iloc[-1])
    ma200 = float(sma(close, 200).iloc[-1])
    slope200 = float(sma(close, 200).iloc[-1] - sma(close, 200).iloc[-21])

    above50, above200 = last > ma50, last > ma200
    if above50 and above200 and ma50 > ma200:
        label = "uptrend"
    elif not above50 and not above200 and ma50 < ma200:
        label = "downtrend"
    elif above200:
        label = "pullback_in_uptrend"
    else:
        label = "recovery_below_200dma"

    return {
        "regime": label,
        "close": round(last, 2),
        "sma50": round(ma50, 2),
        "sma200": round(ma200, 2),
        "sma200_slope_21d": round(slope200, 2),
        "rules": "uptrend: close>50DMA>200DMA | downtrend: close<50DMA<200DMA | "
        "else pullback if close>200DMA, otherwise recovery",
    }
