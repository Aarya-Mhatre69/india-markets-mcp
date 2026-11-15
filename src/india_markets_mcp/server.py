"""FastMCP server exposing the tools over stdio."""

from __future__ import annotations

from fastmcp import FastMCP

from . import core

mcp = FastMCP(
    "india-markets",
    instructions="Public-data tools for Indian equities (NSE/BSE). Not investment advice.",
)


@mcp.tool
def get_quote(symbol: str) -> dict:
    """Latest close, daily change and 52-week range for an NSE symbol (e.g. RELIANCE, TCS, NIFTY)."""
    return core.get_quote(symbol)


@mcp.tool
def get_signals(symbol: str) -> dict:
    """RSI, volatility, drawdown, 12-1 momentum and a rule-based trend regime for a symbol."""
    return core.get_signals(symbol)


@mcp.tool
def compare_symbols(symbols: list[str], period: str = "1y") -> list[dict]:
    """Rank 2-10 symbols by return over a period (1mo, 6mo, 1y, 2y, 5y), with volatility and drawdown."""
    return core.compare(symbols, period)


@mcp.tool
def get_fundamentals(symbol: str) -> dict:
    """Valuation snapshot: market cap (INR crore), P/E, P/B, ROE, debt/equity, dividend yield, sector."""
    return core.get_fundamentals(symbol)


@mcp.tool
def compare_fundamentals(symbols: list[str]) -> list[dict]:
    """Side-by-side valuation of 2-10 symbols, cheapest trailing P/E first."""
    return core.compare_fundamentals(symbols)


@mcp.tool
def sector_peers(symbol: str) -> dict:
    """Compare a large-cap stock with illustrative same-sector peers: median P/E and P/B and its premium."""
    return core.sector_peers(symbol)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
