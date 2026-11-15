---
name: india-markets
description: Look up and compare Indian (NSE/BSE) listed stocks and indices such as RELIANCE, TCS, HDFCBANK, NIFTY, BANKNIFTY and SENSEX. Use when the user asks for a quote, price trend, RSI, volatility, drawdown, valuation (P/E, P/B, market cap), a comparison of Indian stocks, or how a stock sits against its sector peers. Requires the india-markets MCP server. Reports data only; never gives buy/sell advice.
---

# Indian markets research

Use the `india-markets` MCP tools to answer questions about Indian equities from public data.
This skill reports facts and simple, rule-based signals. It is **not investment advice**.

## Tool map

| The user wants... | Call |
|---|---|
| Latest price, day change, 52-week range | `get_quote` |
| Trend, RSI, volatility, drawdown, momentum | `get_signals` |
| Which of several stocks returned more | `compare_symbols` |
| Valuation of one stock (P/E, P/B, ROE, market cap) | `get_fundamentals` |
| Valuation of several stocks side by side | `compare_fundamentals` |
| Is a large-cap cheap or expensive vs its sector | `sector_peers` |

Symbols: pass NSE tickers without a suffix (`RELIANCE`, `TCS`). `NIFTY`, `BANKNIFTY` and `SENSEX` are indices.
Use `.BO` for BSE (`TCS.BO`). A company name is not a ticker: resolve it yourself first (for example "Infosys" is `INFY`).

## Workflow

1. Pick the narrowest tool that answers the question. Do not call every tool by default.
2. For a "tell me about X" request, call `get_quote`, `get_signals` and `get_fundamentals` for X, then summarise.
3. For "is X cheap/expensive", use `sector_peers` and state the peer group is illustrative.
4. For "which is better" between 2 to 10 stocks, use `compare_symbols` for performance and `compare_fundamentals` for valuation. Say which you used.
5. If a tool fails, read the error message (you will see text, not an exception class):
   - "no data for ..." means the symbol is wrong: fix it or ask the user.
   - "data source failed ... after 3 attempts" means the upstream source is down or rate-limiting: say so and offer to retry later.
   - "is not in the built-in peer groups" (from `sector_peers`) means use `compare_fundamentals` with a peer list you choose, and say so.
   - "provide between 2 and 10 symbols" means adjust the list.
   Never invent numbers to fill a gap.

## Reading the output

- `market_cap_crore` is in INR crore (1 crore = 10 million rupees). Do not present it as dollars.
- `null` means the field is unavailable (loss-making company, new listing, gap in the source). Say "not available"; never estimate it.
- `roe_pct` and `dividend_yield_pct` are percentages already. `debt_to_equity` is as reported by the source.
- `rsi_state`: above 70 "overbought", below 30 "oversold". These are momentum labels, not predictions.
- `regime` is a rule on the 50- and 200-day averages and the 200-day slope. The output includes the rule text. Relay the reason, for example "price is above a falling 200-day average", rather than just the label.
- `transition_above_falling_200dma` means price is above its 200-day average but that average is still falling. Describe it as mixed, not as an uptrend.
- `sector_peers` compares against a hand-picked list of large caps, not an official sector index. Peer medians use only peers that returned data (`skipped_peers` lists any that did not).
- Data comes from Yahoo Finance via an unofficial library. It can be delayed or wrong. Mention the `as_of` date.

## Guardrails (always apply)

- Do not tell the user to buy, sell, hold, or "accept/avoid" a stock, and do not give price targets or return forecasts.
  If asked "should I buy X?", give the relevant facts and signals, explain what they do and do not tell, and say the decision is theirs.
  For personal advice, point them to a SEBI-registered investment adviser.
- Do not describe a signal as predictive ("RSI is 74 so it will fall"). Describe what it measures.
- Do not use this data for live trading decisions or order placement; it has no execution and may lag.
- Always end an analysis with a one-line note: "Data from public sources, may be delayed or inaccurate. Not investment advice."

## Answer format

Lead with the direct answer in one or two sentences. Then a compact table of the numbers used, with the `as_of` date.
Keep commentary to what the data shows; note any `null`s or skipped peers.
