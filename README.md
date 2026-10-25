# india-markets-mcp

An [MCP](https://modelcontextprotocol.io) server that lets AI agents (Claude, Cursor, any MCP client) look up
Indian equities and get simple, **transparent** technical signals. Built on public data via
[yfinance](https://github.com/ranaroussi/yfinance) — no API keys.

> Not investment advice. Data comes from Yahoo Finance and can be delayed or wrong.

## Tools

| Tool | What it does |
|---|---|
| `get_quote(symbol)` | Latest close, daily change, 52-week range, volume |
| `get_signals(symbol)` | RSI(14), 30-day volatility, max drawdown, 12-1 momentum, and a rule-based trend regime |
| `compare_symbols(symbols, period)` | Rank 2-10 symbols by return, with volatility and drawdown |

Symbols: `RELIANCE` → `RELIANCE.NS`; `TCS.BO` and `^NSEI` pass through; `NIFTY`, `BANKNIFTY`, `SENSEX` map to indices.

The regime label is deliberately a plain rule (close vs 50/200-day averages) and the output includes the rule text,
so an agent can explain *why* a label was chosen.

## Install and run

```bash
pip install -e .
india-markets-mcp          # starts the server over stdio
```

Claude Desktop / Claude Code config:

```json
{
  "mcpServers": {
    "india-markets": { "command": "india-markets-mcp" }
  }
}
```

## Develop

```bash
pip install -e ".[dev]"
pytest
```

Indicator and tool logic is pure pandas (`indicators.py`, `core.py`) and tested offline; only `data.py` touches the network.

## Roadmap

- Fundamentals (P/E, P/B) and sector comparison
- Optional alternative data sources behind the same interface
- Caching to be kinder to the upstream API

## License

MIT
