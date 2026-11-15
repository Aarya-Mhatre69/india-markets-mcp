<div align="center">

# 🇮🇳 india-markets-mcp

**Give your AI agent a live view of the Indian stock market.**
Quotes, transparent technical signals, valuation and sector comparison for NSE/BSE, over [MCP](https://modelcontextprotocol.io). No API keys.

[![CI](https://github.com/Aarya-Mhatre69/india-markets-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Aarya-Mhatre69/india-markets-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![MCP](https://img.shields.io/badge/MCP-server-8A2BE2)
![No API key](https://img.shields.io/badge/API%20key-none-brightgreen)

</div>

---

## See it work

> **You:** How is TCS doing, and does it look cheap versus its IT peers?
>
> **Claude** *(calls `get_quote`, `get_signals`, `sector_peers`)*:
> TCS closed at ₹2,407.50, down 1.43% on the day and 24.5% below its 52-week high. RSI is 50.7 (neutral). Price sits above a still-falling 200-day average, so the trend is **mixed, not an uptrend**. Against the illustrative IT peer group it trades at a P/E premium to the peer median.
>
> | Metric | Value |
> |---|---|
> | 52-week range | ₹1,961.36 – ₹3,187.34 |
> | 30-day volatility (annualised) | 32.8% |
> | Market cap | ₹8,71,055 crore |
>
> *Data from public sources, may be delayed or inaccurate. Not investment advice.*

*(Example output from a real session; numbers move with the market.)*

## Why this one

- **Built for India.** `RELIANCE` just works. `NIFTY`, `BANKNIFTY` and `SENSEX` are first-class. Market cap comes back in **₹ crore**, not dollars.
- **Signals you can audit.** The trend regime is a plain rule on the 50/200-day averages and the 200-day slope, and the tool returns the rule text, so the agent can explain *why*, not just emit a label.
- **Honest about gaps.** Missing data is `null`, never guessed. Unknown tickers and upstream outages raise clear errors.
- **Polite to the data source.** 5-minute cache, 3 retries with backoff, bounded fan-out.
- **Tested offline.** Indicator and tool logic is pure pandas with 34 tests, run in CI on Linux, macOS and Windows.
- **Comes with an agent skill** that teaches the agent when to use each tool and keeps answers to facts, not buy/sell calls.

## Tools

| Tool | What it does |
|---|---|
| `get_quote(symbol)` | Latest close, daily change, 52-week range, volume |
| `get_signals(symbol)` | RSI(14), 30-day volatility, max drawdown, 12-1 momentum, rule-based trend regime |
| `compare_symbols(symbols, period)` | Rank 2-10 symbols by return, with volatility and drawdown |
| `get_fundamentals(symbol)` | Market cap (₹ crore), P/E, P/B, ROE, debt/equity, dividend yield, sector |
| `compare_fundamentals(symbols)` | Side-by-side valuation of 2-10 symbols, cheapest P/E first |
| `sector_peers(symbol)` | A large-cap vs hand-picked same-sector peers: median P/E and P/B and its premium or discount |

**Symbols:** `RELIANCE` → `RELIANCE.NS` · `TCS.BO` and `^NSEI` pass through · `NIFTY`, `BANKNIFTY`, `SENSEX` map to the indices.

## Try asking

- "Give me a quick read on HDFCBANK: price, trend and valuation."
- "Rank INFY, TCS, WIPRO and HCLTECH by 1-year return and by P/E."
- "Is Reliance expensive compared with other oil and gas names?"
- "Which of the big private banks has the lowest drawdown this year?"

## Install

**Claude Desktop / Claude Code / Cursor** (any MCP client). Install, then add the server:

```bash
pip install git+https://github.com/Aarya-Mhatre69/india-markets-mcp
```

```json
{
  "mcpServers": {
    "india-markets": { "command": "india-markets-mcp" }
  }
}
```

With Claude Code you can register it in one line:

```bash
claude mcp add india-markets -- india-markets-mcp
```

If the command isn't on your PATH, use the full path to the executable (for a venv: `.venv/Scripts/india-markets-mcp.exe` on Windows, `.venv/bin/india-markets-mcp` elsewhere).

### Optional: the agent skill

`skills/india-markets/SKILL.md` teaches an agent which tool to pick, how to read units and `null`s, and to stay on facts (no buy/sell advice, ends with a disclaimer). Copy the folder into `.claude/skills/` (Claude Code) or your agent's skills directory.

## How it works

```
 your agent ──MCP──▶ server.py ──▶ core.py ──▶ indicators.py   (pure pandas, tested offline)
                                      │
                                      └──▶ data.py ──▶ yfinance (cache + retry)   ← only network code
```

Only `data.py` touches the network, so everything else is deterministic and easy to test.

## Good to know

- **Not investment advice.** Signals describe the past; they do not predict.
- Data comes from Yahoo Finance via the unofficial `yfinance` library. It can be delayed, rate-limited or wrong, and Yahoo's terms limit commercial use. Fine for research and learning, not for trading systems.
- Fundamentals can be `null` (loss-making companies, new listings, gaps in the source).
- `sector_peers` uses a small hand-picked list in [`sectors.py`](src/india_markets_mcp/sectors.py), not an official classification. Edit it if you disagree with a grouping.

## Develop

```bash
git clone https://github.com/Aarya-Mhatre69/india-markets-mcp
cd india-markets-mcp
pip install -e ".[dev]"
pytest
```

Contributions welcome: new peer groups, a better data source behind the same interface, more indicators. Open an issue first for anything big.

## Roadmap

- [x] Quotes, signals, comparison
- [x] Fundamentals and sector peers
- [x] Caching, retries, CI, agent skill
- [ ] Portfolio view: pass holdings, get concentration, sector mix and drawdown
- [ ] Pluggable data sources behind one interface
- [ ] Nifty 50 screener (oversold + cheap vs peers)

## License

MIT
