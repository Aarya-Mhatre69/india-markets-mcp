"""FastMCP server exposing tools and prompts over stdio."""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from . import core

INSTRUCTIONS = """\
Public-data tools for Indian equities (NSE/BSE). Not investment advice.

How to use:
- Tickers: pass NSE symbols without a suffix (RELIANCE, TCS). Use .BO for BSE (TCS.BO).
  NIFTY, BANKNIFTY and SENSEX are the main indices. If you only have a company name, call search_symbol first.
- Pick the narrowest tool: get_quote (price), get_signals (RSI, volatility, drawdown, trend),
  get_fundamentals (valuation), compare_symbols / compare_fundamentals (2-10 stocks), sector_peers (vs peers).
- Market cap is in INR crore. A null field means "not available"; never estimate it.
- Report facts and the as_of date. Do not give buy/sell/hold advice, price targets or forecasts.
  Data comes from Yahoo Finance via an unofficial library and can be delayed or wrong.
"""

mcp = FastMCP("india-markets", instructions=INSTRUCTIONS)

# Every tool only reads public market data: safe to call freely, repeat, and cache.
READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "destructiveHint": False, "openWorldHint": True}

Symbol = Annotated[
    str,
    Field(description="NSE ticker without suffix (RELIANCE, TCS), a BSE ticker with .BO (TCS.BO), or NIFTY, BANKNIFTY, SENSEX."),
]
Symbols = Annotated[
    list[str],
    Field(description="Between 2 and 10 tickers, in the same formats as a single symbol, for example [\"TCS\", \"INFY\", \"WIPRO\"]."),
]


@mcp.tool(title="Search Indian stocks by name", annotations=READ_ONLY)
def search_symbol(
    query: Annotated[str, Field(description="Company name or partial ticker, for example \"Infosys\", \"HDFC Bank\" or \"nifty bank\".")],
    limit: Annotated[int, Field(description="Maximum number of matches to return.", ge=1, le=20)] = 8,
) -> list[dict]:
    """Find the ticker for a company name. Returns NSE/BSE equities, indices and ETFs, NSE listings first.

    Use this when you only have a name. Each match has `symbol` (pass it straight to the other tools),
    `name`, `exchange` (NSE or BSE) and `type` (equity, index or etf). Returns an empty list when nothing
    matches. Several listings can match one company (for example the Tata Motors demerger), so check the
    names before choosing.
    """
    return core.search_symbol(query, limit)


@mcp.tool(title="Get quote", annotations=READ_ONLY)
def get_quote(symbol: Symbol) -> dict:
    """Latest close, daily change and 52-week range for a stock or index.

    Returns `close`, `change_pct` (vs the previous close), `high_52w`, `low_52w`, `pct_from_52w_high`,
    `volume` and the `as_of` trading date. Prices are in INR (index levels for indices) and end-of-day,
    so they can lag the live market. Raises a clear "no data" error for an unknown ticker.
    """
    return core.get_quote(symbol)


@mcp.tool(title="Get technical signals", annotations=READ_ONLY)
def get_signals(symbol: Symbol) -> dict:
    """RSI(14), 30-day volatility, max drawdown, 12-1 momentum and a rule-based trend regime.

    The `regime` comes from a plain rule on the 50 and 200-day averages and the 200-day slope, and the
    result includes `rules` text explaining it, so relay the reason, not just the label. `rsi_state` is
    overbought (70 or above), oversold (30 or below), or neutral. These describe the past and do not
    predict returns. Volatility and drawdown are fractions (0.25 = 25%).
    """
    return core.get_signals(symbol)


@mcp.tool(title="Compare returns", annotations=READ_ONLY)
def compare_symbols(
    symbols: Symbols,
    period: Annotated[str, Field(description="Look-back window: 1mo, 3mo, 6mo, 1y, 2y or 5y.")] = "1y",
) -> list[dict]:
    """Rank 2 to 10 symbols by total return over a period, best first, with volatility and drawdown.

    Use this for "which did better" questions about price performance. For valuation use
    compare_fundamentals instead. `return_pct` is in percent, adjusted for splits and dividends.
    """
    return core.compare(symbols, period)


@mcp.tool(title="Get fundamentals", annotations=READ_ONLY)
def get_fundamentals(symbol: Symbol) -> dict:
    """Valuation snapshot: market cap, P/E, P/B, ROE, debt/equity, dividend yield, sector and industry.

    `market_cap_crore` is in INR crore (1 crore = 10 million rupees), not dollars. `roe_pct` and
    `dividend_yield_pct` are percentages; the dividend yield is the indicated annual dividend per share
    divided by price. Fields are null when unavailable (loss-making companies, new listings, gaps in the
    source). Treat null as "not available" and never estimate it.
    """
    return core.get_fundamentals(symbol)


@mcp.tool(title="Compare valuations", annotations=READ_ONLY)
def compare_fundamentals(symbols: Symbols) -> list[dict]:
    """Side-by-side valuation of 2 to 10 symbols, cheapest trailing P/E first; stocks without a P/E go last.

    Same fields and units as get_fundamentals. Use this for "which looks cheaper" questions across a list
    you choose. For one stock against its sector use sector_peers.
    """
    return core.compare_fundamentals(symbols)


@mcp.tool(title="Compare with sector peers", annotations=READ_ONLY)
def sector_peers(symbol: Symbol) -> dict:
    """Place a large-cap stock against illustrative same-sector peers: median P/E and P/B and its premium.

    Peers come from a small hand-picked list of large caps (IT services, banks, autos, FMCG, pharma, energy,
    metals and more), not an official sector classification, so say the group is illustrative. The stock and
    up to 5 peers are fetched; peers with no data are listed in `skipped_peers`. If the stock is not in a
    built-in group the error says so; use compare_fundamentals with a peer list you choose instead.
    `pe_premium_to_peers_pct` is positive when the stock is pricier than the peer median.
    """
    return core.sector_peers(symbol)


@mcp.prompt(title="Analyze a stock")
def analyze_stock(
    symbol: Annotated[str, Field(description="Ticker or company name, for example TCS or Reliance.")],
) -> str:
    """A balanced, facts-only briefing on one Indian stock: price, trend, valuation and peers."""
    return (
        f"Give a facts-only briefing on the Indian stock '{symbol}'.\n"
        "1. If this is a company name rather than a ticker, call search_symbol first and pick the right NSE listing.\n"
        "2. Call get_quote, get_signals and get_fundamentals. If it belongs to a sector group, also call sector_peers.\n"
        "3. Lead with one or two sentences answering where the stock stands. Then a compact table of the numbers, "
        "with the as_of date. Market cap is in INR crore. Say 'not available' for null fields.\n"
        "4. Explain the trend regime using the rule text the tool returns. Say the peer group is illustrative.\n"
        "5. Do not give buy, sell or hold advice, price targets or forecasts. End with: "
        "'Data from public sources, may be delayed or inaccurate. Not investment advice.'"
    )


@mcp.prompt(title="Compare stocks")
def compare_stocks(
    symbols: Annotated[str, Field(description="Two to ten tickers or names separated by commas, for example TCS, INFY, WIPRO.")],
) -> str:
    """Compare several Indian stocks on performance and valuation."""
    return (
        f"Compare these Indian stocks: {symbols}.\n"
        "Resolve any company names to tickers with search_symbol. Use compare_symbols for price performance "
        "(1y) and compare_fundamentals for valuation, and say which tool each number came from. "
        "Show one table per tool with the as_of date, note any null values, and keep to facts: "
        "no buy, sell or hold advice. End with: "
        "'Data from public sources, may be delayed or inaccurate. Not investment advice.'"
    )


@mcp.prompt(title="Market snapshot")
def market_snapshot() -> str:
    """Where the main Indian indices stand today."""
    return (
        "Give a short snapshot of the Indian market. Call get_quote for NIFTY, BANKNIFTY and SENSEX, and "
        "get_signals for NIFTY. Report each index level, daily change and distance from its 52-week high, "
        "then one sentence on the NIFTY trend using the regime rule text. Include the as_of date. "
        "Facts only, no forecasts or advice. End with: "
        "'Data from public sources, may be delayed or inaccurate. Not investment advice.'"
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
