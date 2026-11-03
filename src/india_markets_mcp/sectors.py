"""Illustrative large-cap peer groups for NSE stocks.

These are hand-picked, widely held names grouped for comparison. They are NOT an
official classification (NSE/BSE/Yahoo use different schemes) and will drift over
time as companies list, merge or demerge. Edit freely.
"""

from __future__ import annotations

PEER_GROUPS: dict[str, list[str]] = {
    "it_services": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM"],
    "private_banks": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "INDUSINDBK"],
    "public_banks": ["SBIN", "BANKBARODA", "PNB", "CANBK"],
    "nbfc_insurance": ["BAJFINANCE", "BAJAJFINSV", "SBILIFE", "HDFCLIFE"],
    "oil_gas_energy": ["RELIANCE", "ONGC", "BPCL", "IOC"],
    "power_utilities": ["NTPC", "POWERGRID", "TATAPOWER"],
    "autos": ["MARUTI", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
    "fmcg": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM"],
    "pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB"],
    "metals": ["TATASTEEL", "JSWSTEEL", "HINDALCO"],
    "cement_infra": ["ULTRACEMCO", "GRASIM", "LT"],
}


def _bare(symbol: str) -> str:
    s = symbol.strip().upper()
    for suffix in (".NS", ".BO"):
        if s.endswith(suffix):
            return s[: -len(suffix)]
    return s


def find_group(symbol: str) -> tuple[str, list[str]]:
    """Return (group name, all members) for a symbol, or raise ValueError."""
    bare = _bare(symbol)
    for name, members in PEER_GROUPS.items():
        if bare in members:
            return name, list(members)
    raise ValueError(
        f"{symbol!r} is not in the built-in peer groups. "
        f"Groups: {', '.join(PEER_GROUPS)}. Use compare_fundamentals with your own list instead."
    )
