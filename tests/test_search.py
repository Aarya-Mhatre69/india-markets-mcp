import pytest

from india_markets_mcp import core, data

# Shaped like real Yahoo search hits (trimmed): mixed exchanges, a mutual fund, a foreign listing.
YAHOO_HITS = [
    {"symbol": "INFY", "shortname": "Infosys Limited", "exchange": "NYQ", "quoteType": "EQUITY"},
    {"symbol": "INFY.BO", "shortname": "INFOSYS LTD.", "exchange": "BSE", "quoteType": "EQUITY"},
    {"symbol": "INFY.NS", "shortname": "INFOSYS LIMITED", "exchange": "NSI", "quoteType": "EQUITY"},
    {"symbol": "0P0001MMYU.BO", "shortname": "0P0001MMYU.BO", "exchange": "BSE", "quoteType": "MUTUALFUND"},
    {"symbol": "^NSEBANK", "shortname": "NIFTY BANK", "exchange": "NSI", "quoteType": "INDEX"},
    {"symbol": "IOY.MU", "shortname": "Infosys Ltd.", "exchange": "MUN", "quoteType": "EQUITY"},
]


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    data.clear_cache()
    monkeypatch.setattr(data.time, "sleep", lambda s: None)
    yield
    data.clear_cache()


def test_matches_keep_only_indian_listings_and_put_nse_first():
    rows = core.matches_from_quotes(YAHOO_HITS)
    assert [r["yahoo_ticker"] for r in rows] == ["INFY.NS", "^NSEBANK", "INFY.BO"]


def test_nse_symbol_is_usable_directly_in_other_tools():
    rows = core.matches_from_quotes(YAHOO_HITS)
    nse = rows[0]
    assert nse["symbol"] == "INFY" and nse["exchange"] == "NSE" and nse["type"] == "equity"
    assert data.normalize_symbol(nse["symbol"]) == "INFY.NS"
    bse = next(r for r in rows if r["exchange"] == "BSE")
    assert bse["symbol"] == "INFY.BO" and data.normalize_symbol(bse["symbol"]) == "INFY.BO"


def test_matches_respect_limit_and_tolerate_missing_fields():
    assert len(core.matches_from_quotes(YAHOO_HITS, limit=1)) == 1
    assert core.matches_from_quotes([{"exchange": "NSI"}, {"symbol": "X.NS"}, {}]) == []


def test_search_symbol_validates_limit():
    with pytest.raises(ValueError, match="between 1 and 20"):
        core.search_symbol("tcs", limit=0)


def test_search_instruments_returns_empty_list_for_no_hits(monkeypatch):
    monkeypatch.setattr(data, "_download_search", lambda q, n: None)
    assert data.search_instruments("zzzzzzzz") == []


def test_search_instruments_rejects_blank_query():
    with pytest.raises(ValueError, match="must not be empty"):
        data.search_instruments("   ")


def test_search_instruments_is_cached_and_case_insensitive(monkeypatch):
    calls = []
    monkeypatch.setattr(data, "_download_search", lambda q, n: calls.append(q) or YAHOO_HITS)
    data.search_instruments("Infosys")
    data.search_instruments("infosys")
    assert len(calls) == 1


def test_search_instruments_surfaces_upstream_failure(monkeypatch):
    def boom(q, n):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(data, "_download_search", boom)
    with pytest.raises(data.DataSourceError):
        data.search_instruments("infosys")
