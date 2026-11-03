import numpy as np
import pandas as pd
import pytest

from india_markets_mcp import data, indicators


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    data.clear_cache()
    monkeypatch.setattr(data.time, "sleep", lambda s: None)
    yield
    data.clear_cache()


def frame():
    return pd.DataFrame({"Close": [1.0, 2.0], "Volume": [1, 1]}, index=pd.bdate_range("2024-01-01", periods=2))


def test_cache_avoids_second_download(monkeypatch):
    calls = []
    monkeypatch.setattr(data, "_download", lambda t, p, i: calls.append(t) or frame())
    data.fetch_history("TCS")
    data.fetch_history("tcs")
    assert calls == ["TCS.NS"]


def test_cache_expires(monkeypatch):
    calls = []
    monkeypatch.setattr(data, "_download", lambda t, p, i: calls.append(t) or frame())
    data.fetch_history("TCS")
    monkeypatch.setattr(data, "CACHE_TTL_SECONDS", -1)
    data.fetch_history("TCS")
    assert len(calls) == 2


def test_retries_then_succeeds(monkeypatch):
    attempts = []

    def flaky(t, p, i):
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("rate limited")
        return frame()

    monkeypatch.setattr(data, "_download", flaky)
    assert not data.fetch_history("INFY").empty
    assert len(attempts) == 3


def test_gives_up_with_data_source_error(monkeypatch):
    def boom(t, p, i):
        raise ConnectionError("down")

    monkeypatch.setattr(data, "_download", boom)
    with pytest.raises(data.DataSourceError, match="after 3 attempts"):
        data.fetch_history("INFY")


def test_empty_result_is_not_retried_and_is_symbol_not_found(monkeypatch):
    calls = []
    monkeypatch.setattr(data, "_download", lambda t, p, i: calls.append(1) or pd.DataFrame())
    with pytest.raises(data.SymbolNotFoundError):
        data.fetch_history("NOPE")
    assert len(calls) == 1


def test_regime_flags_falling_200dma_instead_of_calling_it_a_pullback():
    # long decline, then a sharp rally that lifts price above a still-falling 200DMA
    close = pd.Series(np.concatenate([np.linspace(400, 100, 300), np.linspace(100, 240, 25)]))
    out = indicators.classify_regime(close)
    assert out["sma200_slope_21d"] < 0
    assert out["regime"] == "transition_above_falling_200dma"
