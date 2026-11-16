import pytest

from india_markets_mcp import core, data, sectors


@pytest.fixture(autouse=True)
def fresh_cache(monkeypatch):
    data.clear_cache()
    monkeypatch.setattr(data.time, "sleep", lambda s: None)
    yield
    data.clear_cache()


def info(name, pe=None, pb=None, cap=None, **extra):
    d = {"longName": name, "trailingPE": pe, "priceToBook": pb, "marketCap": cap, "currency": "INR"}
    d.update(extra)
    return {k: v for k, v in d.items() if v is not None}


def test_fundamentals_converts_units_and_keeps_missing_as_none():
    out = core.fundamentals_from_info(
        "tcs",
        info("TCS", pe=17.5, pb=7.6, cap=9.04e12, returnOnEquity=0.4557, sector="Technology"),
    )
    assert out["symbol"] == "TCS.NS"
    assert out["market_cap_crore"] == 904000.0
    assert out["roe_pct"] == 45.6
    assert out["pe_forward"] is None
    assert out["dividend_yield_pct"] is None


def test_dividend_yield_is_computed_from_rate_and_price_not_yahoos_ambiguous_field():
    # Yahoo's dividendYield has been a fraction in some yfinance versions and a percent in others
    for yahoo_field in (0.0199, 1.99):
        out = core.fundamentals_from_info("tcs", info("TCS", dividendYield=yahoo_field, dividendRate=48.0, currentPrice=2422.0))
        assert out["dividend_yield_pct"] == 1.98


def test_dividend_yield_is_none_when_inputs_missing_or_invalid():
    assert core.fundamentals_from_info("x", info("X", dividendYield=1.5))["dividend_yield_pct"] is None
    assert core.fundamentals_from_info("x", info("X", dividendRate=5.0, currentPrice=0))["dividend_yield_pct"] is None
    assert core.fundamentals_from_info("x", info("X", dividendRate=True, currentPrice=100))["dividend_yield_pct"] is None


def test_compare_sorts_by_pe_with_missing_pe_last():
    infos = {
        "AAA": info("A", pe=30),
        "BBB": info("B"),  # loss-making, no P/E
        "CCC": info("C", pe=12),
    }
    assert [r["symbol"] for r in core.compare_fundamentals_from_infos(infos)] == [
        "CCC.NS",
        "AAA.NS",
        "BBB.NS",
    ]


def test_sector_view_median_and_premium():
    infos = {
        "TCS": info("TCS", pe=24, pb=8),
        "INFY": info("INFY", pe=20, pb=6),
        "WIPRO": info("WIPRO", pe=16, pb=4),
        "HCLTECH": info("HCL", pe=22, pb=5),
    }
    view = core.sector_view_from_infos("TCS", "it_services", infos)
    assert view["peer_median_pe"] == 20.0
    assert view["pe_premium_to_peers_pct"] == 20.0
    assert view["peer_median_pb"] == 5.0
    assert view["pb_premium_to_peers_pct"] == 60.0
    assert len(view["table"]) == 4


def test_sector_view_handles_peers_without_pe():
    infos = {"TCS": info("TCS", pe=24), "INFY": info("INFY")}
    view = core.sector_view_from_infos("TCS", "it_services", infos)
    assert view["peer_median_pe"] is None
    assert view["pe_premium_to_peers_pct"] is None


def test_find_group_is_case_and_suffix_insensitive():
    name, members = sectors.find_group("infy.ns")
    assert name == "it_services"
    assert "TCS" in members


def test_find_group_unknown_symbol_lists_groups():
    with pytest.raises(ValueError, match="it_services"):
        sectors.find_group("NOTINANYGROUP")


def test_peer_groups_have_no_duplicate_symbols():
    seen = [s for members in sectors.PEER_GROUPS.values() for s in members]
    assert len(seen) == len(set(seen))


BIG_GROUP = {"big": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH"]}


def test_sector_peers_bounds_upstream_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(sectors, "PEER_GROUPS", BIG_GROUP)
    monkeypatch.setattr(data, "fetch_info", lambda s: calls.append(s) or info(s, pe=10, pb=2))
    core.sector_peers("AAA")
    assert len(calls) == 6  # the stock plus at most 5 peers


def test_sector_peers_skips_stale_peer_and_reports_it(monkeypatch):
    def fake(s):
        if s == "INFY":
            raise data.SymbolNotFoundError("gone")
        return info(s, pe=10, pb=2)

    monkeypatch.setattr(sectors, "PEER_GROUPS", {"it": ["TCS", "INFY", "WIPRO", "TECHM"]})
    monkeypatch.setattr(data, "fetch_info", fake)
    view = core.sector_peers("TCS")
    assert view["skipped_peers"] == ["INFY"]
    assert "INFY.NS" not in [r["symbol"] for r in view["table"]]
    assert len(view["table"]) == 3


def test_sector_peers_still_fails_if_the_target_itself_is_unknown(monkeypatch):
    def fake(s):
        raise data.SymbolNotFoundError("gone")

    monkeypatch.setattr(data, "fetch_info", fake)
    with pytest.raises(data.SymbolNotFoundError):
        core.sector_peers("TCS")


def test_fetch_info_unknown_symbol_raises_not_found(monkeypatch):
    monkeypatch.setattr(data, "_download_info", lambda t: None)
    with pytest.raises(data.SymbolNotFoundError):
        data.fetch_info("NOPE")


def test_fetch_info_is_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(data, "_download_info", lambda t: calls.append(t) or {"longName": "X"})
    data.fetch_info("TCS")
    data.fetch_info("tcs")
    assert calls == ["TCS.NS"]
