"""Tool logic. Takes price frames in, returns JSON-friendly dicts out."""

from __future__ import annotations

import statistics

import pandas as pd

from . import data, indicators, sectors


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


_EXCHANGES = {"NSI": "NSE", "BSE": "BSE"}
_TYPES = {"EQUITY", "INDEX", "ETF"}


def matches_from_quotes(quotes: list[dict], limit: int = 8) -> list[dict]:
    """Keep NSE/BSE equities, indices and ETFs; NSE first. `symbol` works directly in the other tools."""
    rows = []
    for q in quotes:
        exchange = _EXCHANGES.get(q.get("exchange"))
        ticker = q.get("symbol")
        kind = str(q.get("quoteType") or "").upper()
        if not exchange or not ticker or kind not in _TYPES:
            continue
        rows.append(
            {
                "symbol": ticker[:-3] if ticker.endswith(".NS") else ticker,
                "yahoo_ticker": ticker,
                "name": q.get("shortname") or q.get("longname"),
                "exchange": exchange,
                "type": kind.lower(),
            }
        )
    rows.sort(key=lambda r: r["exchange"] != "NSE")  # stable: keeps Yahoo's relevance order within each exchange
    return rows[:limit]


def search_symbol(query: str, limit: int = 8) -> list[dict]:
    if not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    return matches_from_quotes(data.search_instruments(query), limit)


def get_quote(symbol: str) -> dict:
    return quote_from_history(symbol, data.fetch_history(symbol, period="1y"))


def get_signals(symbol: str) -> dict:
    return signals_from_history(symbol, data.fetch_history(symbol, period="2y"))


def compare(symbols: list[str], period: str = "1y") -> list[dict]:
    if not 2 <= len(symbols) <= 10:
        raise ValueError("provide between 2 and 10 symbols")
    return compare_from_histories({s: data.fetch_history(s, period=period) for s in symbols})


def _num(info: dict, key: str, digits: int = 2) -> float | None:
    value = info.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(float(value), digits)


def _dividend_yield_pct(info: dict) -> float | None:
    """Indicated yield = annual dividend per share / price, as a percentage.

    Computed rather than read from Yahoo's `dividendYield`, whose unit (fraction vs percent)
    has changed between yfinance versions. Missing inputs give None, never a guess.
    """
    rate = info.get("dividendRate")
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    for v in (rate, price):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
    return round(rate / price * 100, 2) if price > 0 else None


def fundamentals_from_info(symbol: str, info: dict) -> dict:
    """Valuation snapshot. Missing fields (common for loss-making or new listings) are None."""
    cap = info.get("marketCap")
    return {
        "symbol": data.normalize_symbol(symbol),
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency"),
        "market_cap_crore": round(cap / 1e7, 0) if isinstance(cap, (int, float)) else None,
        "pe_trailing": _num(info, "trailingPE"),
        "pe_forward": _num(info, "forwardPE"),
        "pb": _num(info, "priceToBook"),
        "roe_pct": None if _num(info, "returnOnEquity", 4) is None else round(info["returnOnEquity"] * 100, 1),
        "debt_to_equity": _num(info, "debtToEquity"),
        "dividend_yield_pct": _dividend_yield_pct(info),
    }


def compare_fundamentals_from_infos(infos: dict[str, dict]) -> list[dict]:
    """Rows sorted by trailing P/E ascending; stocks without a P/E go last."""
    rows = [fundamentals_from_info(sym, info) for sym, info in infos.items()]
    return sorted(rows, key=lambda r: (r["pe_trailing"] is None, r["pe_trailing"] or 0))


def sector_view_from_infos(symbol: str, group: str, infos: dict[str, dict]) -> dict:
    """Place one stock against its peers' median P/E and P/B."""
    rows = compare_fundamentals_from_infos(infos)
    target = data.normalize_symbol(symbol)
    peers = [r for r in rows if r["symbol"] != target]

    def median(key: str) -> float | None:
        values = [r[key] for r in peers if r[key] is not None]
        return round(statistics.median(values), 2) if values else None

    def premium(own: float | None, med: float | None) -> float | None:
        return None if own is None or not med else round((own / med - 1) * 100, 1)

    me = next(r for r in rows if r["symbol"] == target)
    return {
        "symbol": target,
        "peer_group": group,
        "peer_median_pe": median("pe_trailing"),
        "peer_median_pb": median("pb"),
        "pe_premium_to_peers_pct": premium(me["pe_trailing"], median("pe_trailing")),
        "pb_premium_to_peers_pct": premium(me["pb"], median("pb")),
        "table": rows,
        "note": "Peer groups are illustrative large-cap names, not an official classification.",
    }


def get_fundamentals(symbol: str) -> dict:
    return fundamentals_from_info(symbol, data.fetch_info(symbol))


def compare_fundamentals(symbols: list[str]) -> list[dict]:
    if not 2 <= len(symbols) <= 10:
        raise ValueError("provide between 2 and 10 symbols")
    return compare_fundamentals_from_infos({s: data.fetch_info(s) for s in symbols})


def sector_peers(symbol: str) -> dict:
    group, members = sectors.find_group(symbol)
    target = data.normalize_symbol(symbol)
    # keep the upstream call count bounded: the stock itself plus up to 5 peers
    peers = [m for m in members if data.normalize_symbol(m) != target]

    infos = {symbol: data.fetch_info(symbol)}
    skipped = []
    for peer in peers:
        if len(infos) == 6:
            break
        try:
            infos[peer] = data.fetch_info(peer)
        except data.SymbolNotFoundError:
            skipped.append(peer)  # stale or delisted peer: don't fail the whole comparison

    view = sector_view_from_infos(symbol, group, infos)
    if skipped:
        view["skipped_peers"] = skipped
    return view
