"""Contract tests for what MCP clients and directories see: tools, schemas, annotations, prompts."""

import asyncio

import pytest
from fastmcp import Client

from india_markets_mcp import data
from india_markets_mcp.server import mcp

EXPECTED_TOOLS = {
    "search_symbol",
    "get_quote",
    "get_signals",
    "compare_symbols",
    "get_fundamentals",
    "compare_fundamentals",
    "sector_peers",
}


def run(coro_fn):
    async def inner():
        async with Client(mcp) as client:
            return await coro_fn(client)

    return asyncio.run(inner())


@pytest.fixture(autouse=True)
def fresh_cache():
    data.clear_cache()
    yield
    data.clear_cache()


def test_exposes_exactly_the_documented_tools():
    tools = run(lambda c: c.list_tools())
    assert {t.name for t in tools} == EXPECTED_TOOLS


def pick(obj, snake, camel):
    """MCP SDK v2 renamed camelCase fields to snake_case; accept either so tests span fastmcp versions."""
    return getattr(obj, snake) if hasattr(obj, snake) else getattr(obj, camel)


def test_every_tool_is_read_only_titled_and_documented():
    for tool in run(lambda c: c.list_tools()):
        assert pick(tool.annotations, "read_only_hint", "readOnlyHint") is True, tool.name
        assert pick(tool.annotations, "destructive_hint", "destructiveHint") is False, tool.name
        assert tool.title, tool.name
        assert len(tool.description) >= 80, f"{tool.name} description is too thin"


def test_every_parameter_has_a_description():
    for tool in run(lambda c: c.list_tools()):
        schema = pick(tool, "input_schema", "inputSchema")
        for name, prop in schema["properties"].items():
            assert prop.get("description"), f"{tool.name}.{name} has no description"


def test_prompts_are_registered_and_render():
    prompts = run(lambda c: c.list_prompts())
    assert {p.name for p in prompts} == {"analyze_stock", "compare_stocks", "market_snapshot"}

    async def render(client):
        return (await client.get_prompt("analyze_stock", {"symbol": "Infosys"})).messages[0].content.text

    text = run(render)
    assert "Infosys" in text and "search_symbol" in text and "Not investment advice" in text


def test_search_symbol_is_callable_through_the_protocol(monkeypatch):
    hits = [{"symbol": "TCS.NS", "shortname": "TATA CONSULTANCY SERV LT", "exchange": "NSI", "quoteType": "EQUITY"}]
    monkeypatch.setattr(data, "_download_search", lambda q, n: hits)

    result = run(lambda c: c.call_tool("search_symbol", {"query": "tata consultancy"}))
    rows = result.data
    assert rows[0]["symbol"] == "TCS" and rows[0]["exchange"] == "NSE"


def test_bad_list_size_error_message_is_stable():
    # The agent skill tells agents to recognise this exact text.
    async def go(client):
        with pytest.raises(Exception, match="provide between 2 and 10 symbols"):
            await client.call_tool("compare_symbols", {"symbols": ["TCS"]})

    run(go)
