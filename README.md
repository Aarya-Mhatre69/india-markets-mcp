<!-- mcp-name: io.github.Aarya-Mhatre69/india-markets-mcp -->
<div align="center">

# 🇮🇳 india-markets-mcp

**Give your AI agent a live view of the Indian stock market.**
Quotes, transparent technical signals, valuation and sector comparison for NSE/BSE, over [MCP](https://modelcontextprotocol.io). No API keys.

[![CI](https://github.com/Aarya-Mhatre69/india-markets-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Aarya-Mhatre69/india-markets-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/india-markets-mcp.svg)](https://pypi.org/project/india-markets-mcp/)
[![Aarya-Mhatre69/india-markets-mcp MCP server](https://glama.ai/mcp/servers/Aarya-Mhatre69/india-markets-mcp/badges/score.svg)](https://glama.ai/mcp/servers/Aarya-Mhatre69/india-markets-mcp)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![MCP](https://img.shields.io/badge/MCP-server-8A2BE2)
![No API key](https://img.shields.io/badge/API%20key-none-brightgreen)

</div>

<div align="center">

<img src="docs/demo.gif" alt="Demo: asking an AI agent about TCS and getting live NSE data" width="760">

</div>

---

## See it work

> **You:** Can you give me the price of TCS, and is it a good time to buy?
>
> **Agent** *(calls the india-markets tools)*:
> TCS closed at ₹2,407.50 on 13 Nov 2026, down 1.43% on the day. Whether it's a good time to buy is your decision. I can't give buy, sell or hold advice, but here is where the stock stands.
>
> | Metric | Value |
> |---|---|
> | 52-week range | ₹1,961.36 – ₹3,187.34 |
> | Distance from 52-week high | −24.5% |
> | RSI(14) | 50.7 (neutral) |
> | 30-day volatility (annualised) | 32.8% |
> | 50-day / 200-day average | ₹2,287.43 / ₹2,366.05 |
> | Market cap | ₹8,71,055 crore |

*(Condensed from a real session using the bundled skill, so the agent reports facts instead of advice. Numbers move with the market.)*

▶ **[Watch the 20-second version with sound](docs/demo.mp4)**

## Why this one

- **Built for India.** `RELIANCE` just works. `NIFTY`, `BANKNIFTY` and `SENSEX` are first-class. Market cap comes back in **₹ crore**, not dollars.
- **Signals you can audit.** The trend regime is a plain rule on the 50/200-day averages and the 200-day slope, and the tool returns the rule text, so the agent can explain *why*, not just emit a label.
- **Honest about gaps.** Missing data is `null`, never guessed. Unknown tickers and upstream outages raise clear errors.
- **Polite to the data source.** 5-minute cache, 3 retries with backoff, bounded fan-out.
- **Tested offline.** Indicator and tool logic is pure pandas with 53 tests (including contract tests for the tool schemas), run in CI on Linux, macOS and Windows.
- **Comes with an agent skill** that teaches the agent when to use each tool and keeps answers to facts, not buy/sell calls.

## Tools

| Tool | What it does |
|---|---|
| `search_symbol(query)` | Find a ticker from a company name ("Infosys" → `INFY`): NSE/BSE equities, indices and ETFs |
| `get_quote(symbol)` | Latest close, daily change, 52-week range, volume |
| `get_signals(symbol)` | RSI(14), 30-day volatility, max drawdown, 12-1 momentum, rule-based trend regime |
| `compare_symbols(symbols, period)` | Rank 2-10 symbols by return, with volatility and drawdown |
| `get_fundamentals(symbol)` | Market cap (₹ crore), P/E, P/B, ROE, debt/equity, dividend yield, sector |
| `compare_fundamentals(symbols)` | Side-by-side valuation of 2-10 symbols, cheapest P/E first |
| `sector_peers(symbol)` | A large-cap vs hand-picked same-sector peers: median P/E and P/B and its premium or discount |

**Symbols:** `RELIANCE` → `RELIANCE.NS` · `TCS.BO` and `^NSEI` pass through · `NIFTY`, `BANKNIFTY`, `SENSEX` map to the indices.

**Prompts:** clients that support MCP prompts (Claude Desktop shows them as starters) also get `analyze_stock`, `compare_stocks` and `market_snapshot`, ready-made facts-only briefings.

Every tool is read-only and annotated as such, so well-behaved clients can call them without asking for confirmation each time.

## Try asking

- "What's the P/E of Infosys, and how does it compare with Tata Consultancy?" (it looks up the tickers itself)
- "Give me a quick read on HDFCBANK: price, trend and valuation."
- "Rank INFY, TCS, WIPRO and HCLTECH by 1-year return and by P/E."
- "Is Reliance expensive compared with other oil and gas names?"
- "Which of the big private banks has the lowest drawdown this year?"

## Install

**Claude Desktop / Claude Code / Cursor** (any MCP client). The quickest way is [`uvx`](https://docs.astral.sh/uv/), which needs no install step:

```json
{
  "mcpServers": {
    "india-markets": { "command": "uvx", "args": ["india-markets-mcp"] }
  }
}
```

With Claude Code you can register it in one line:

```bash
claude mcp add india-markets -- uvx india-markets-mcp
```

Prefer pip?

```bash
pip install india-markets-mcp
```

then use `"command": "india-markets-mcp"` in the config above. If that command isn't on your PATH, use the full path to the executable (for a venv: `.venv/Scripts/india-markets-mcp.exe` on Windows, `.venv/bin/india-markets-mcp` elsewhere).

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
- [x] Name-to-ticker search, built-in prompts, read-only tool annotations
- [ ] Portfolio view: pass holdings, get concentration, sector mix and drawdown
- [ ] Pluggable data sources behind one interface
- [ ] Nifty 50 screener (oversold + cheap vs peers)

## License

MIT
