"""Unit tests for TickerLookupTool."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from stock_analysis.tools.ticker_lookup import TickerLookupTool
from stock_analysis.utils.yfinance_client import YFinanceClient


def make_client_with_search(quotes: list[dict]) -> MagicMock:
    client = MagicMock(spec=YFinanceClient)
    client.search.return_value = quotes
    return client


_SAMPLE_QUOTES = [
    {
        "symbol": "RELIANCE.NS",
        "longname": "Reliance Industries Limited",
        "exchDisp": "NSE",
        "typeDisp": "Equity",
        "score": 1724765.0,
    },
    {
        "symbol": "AAPL",
        "longname": "Apple Inc.",
        "exchDisp": "NASDAQ",
        "typeDisp": "Equity",
        "score": 1500000.0,
    },
    {
        "symbol": "REL.BO",
        "longname": "Reliance Industries BSE",
        "exchDisp": "BSE",
        "typeDisp": "Equity",
        "score": 900000.0,
    },
]


class TestTickerLookupToolRun:

    def test_returns_matches_for_india(self):
        client = make_client_with_search(_SAMPLE_QUOTES)
        tool = TickerLookupTool(client)
        result = tool.run("Reliance", country_code="IN")
        # Only .NS suffix should survive for IN
        symbols = [m["symbol"] for m in result["matches"]]
        assert all(s.endswith(".NS") for s in symbols)

    def test_returns_all_for_all_country(self):
        client = make_client_with_search(_SAMPLE_QUOTES)
        tool = TickerLookupTool(client)
        result = tool.run("Reliance", country_code="ALL")
        assert result["count"] == len(_SAMPLE_QUOTES)

    def test_us_filter_keeps_no_dot_symbols(self):
        client = make_client_with_search(_SAMPLE_QUOTES)
        tool = TickerLookupTool(client)
        result = tool.run("Apple", country_code="US")
        symbols = [m["symbol"] for m in result["matches"]]
        for sym in symbols:
            assert "." not in sym

    def test_match_structure(self):
        client = make_client_with_search(_SAMPLE_QUOTES)
        tool = TickerLookupTool(client)
        result = tool.run("Reliance", country_code="ALL")
        match = result["matches"][0]
        for key in ("symbol", "name", "exchange", "type", "score"):
            assert key in match

    def test_search_error_returns_error_key(self):
        client = MagicMock(spec=YFinanceClient)
        client.search.side_effect = Exception("timeout")
        tool = TickerLookupTool(client)
        result = tool.run("Reliance", country_code="IN")
        assert "error" in result
        assert result["count"] == 0

    def test_max_results_respected(self):
        many_quotes = [
            {
                "symbol": f"X{i}.NS",
                "longname": f"Company {i}",
                "exchDisp": "NSE",
                "typeDisp": "Equity",
                "score": float(i),
            }
            for i in range(20)
        ]
        client = make_client_with_search(many_quotes)
        tool = TickerLookupTool(client)
        result = tool.run("X", country_code="IN", max_results=5)
        assert result["count"] <= 5

    def test_query_echoed_in_result(self):
        client = make_client_with_search([])
        tool = TickerLookupTool(client)
        result = tool.run("HDFC Bank", country_code="IN")
        assert result["query"] == "HDFC Bank"

    def test_country_code_echoed_in_result(self):
        client = make_client_with_search([])
        tool = TickerLookupTool(client)
        result = tool.run("HDFC", country_code="IN")
        assert result["country_code"] == "IN"

    def test_default_country_is_india(self):
        client = make_client_with_search([])
        tool = TickerLookupTool(client)
        result = tool.run("HDFC")
        assert result["country_code"] == "IN"
