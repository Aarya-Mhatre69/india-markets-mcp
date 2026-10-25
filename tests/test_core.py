import numpy as np
import pandas as pd
import pytest

from india_markets_mcp import core, data, indicators


def make_frame(prices, volume=1000):
    idx = pd.bdate_range("2024-01-01", periods=len(prices))
    return pd.DataFrame({"Close": prices, "Volume": volume}, index=idx)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("reliance", "RELIANCE.NS"),
        (" TCS ", "TCS.NS"),
        ("TCS.BO", "TCS.BO"),
        ("^NSEI", "^NSEI"),
        ("nifty", "^NSEI"),
        ("BankNifty", "^NSEBANK"),
    ],
)
def test_normalize_symbol(raw, expected):
    assert data.normalize_symbol(raw) == expected


def test_normalize_symbol_rejects_empty():
    with pytest.raises(ValueError):
        data.normalize_symbol("  ")


def test_rsi_is_100_on_pure_uptrend_and_low_on_downtrend():
    up = pd.Series(np.arange(1, 60, dtype=float))
    assert indicators.rsi(up).iloc[-1] == 100
    assert indicators.rsi(up[::-1].reset_index(drop=True)).iloc[-1] < 5


def test_max_drawdown():
    close = pd.Series([100, 120, 90, 110.0])
    assert indicators.max_drawdown(close) == pytest.approx(-0.25)


def test_regime_uptrend_and_downtrend():
    up = pd.Series(np.linspace(100, 300, 300))
    down = pd.Series(np.linspace(300, 100, 300))
    assert indicators.classify_regime(up)["regime"] == "uptrend"
    assert indicators.classify_regime(down)["regime"] == "downtrend"


def test_regime_needs_200_closes():
    with pytest.raises(ValueError):
        indicators.classify_regime(pd.Series(np.arange(100.0)))


def test_momentum_requires_a_year_of_data():
    assert indicators.momentum_12_1(pd.Series(np.arange(1, 100.0))) is None
    assert indicators.momentum_12_1(pd.Series(np.arange(1, 300.0))) > 0


def test_quote_from_history():
    df = make_frame([100.0] * 299 + [110.0], volume=500)
    q = core.quote_from_history("infy", df)
    assert q["symbol"] == "INFY.NS"
    assert q["close"] == 110.0
    assert q["change_pct"] == 10.0
    assert q["pct_from_52w_high"] == 0.0
    assert q["volume"] == 500


def test_signals_from_history_has_regime_and_rsi_state():
    df = make_frame(np.linspace(100, 300, 400))
    s = core.signals_from_history("TCS", df)
    assert s["regime"] == "uptrend"
    assert s["rsi_state"] == "overbought"
    assert s["momentum_12_1"] > 0


def test_compare_ranks_best_first(monkeypatch):
    frames = {"AAA": make_frame([100, 110.0, 120.0]), "BBB": make_frame([100, 90.0, 80.0])}
    monkeypatch.setattr(data, "fetch_history", lambda s, period="1y", interval="1d": frames[s])
    rows = core.compare(["BBB", "AAA"])
    assert [r["symbol"] for r in rows] == ["AAA.NS", "BBB.NS"]
    assert rows[0]["return_pct"] == 20.0


def test_compare_validates_symbol_count():
    with pytest.raises(ValueError):
        core.compare(["ONLY"])
