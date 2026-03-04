"""Unit tests for PriceHistoryTool."""

from __future__ import annotations

import pandas as pd
import pytest

from stock_analysis.tools.price_history import PriceHistoryTool
from tests.conftest import make_mock_client, make_ohlcv


class TestPriceHistoryToolRun:
    """Happy-path and edge-case tests for PriceHistoryTool.run()."""

    def test_returns_correct_symbol(self, mock_client):
        tool = PriceHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["symbol"] == "RELIANCE.NS"

    def test_record_count_matches_dataframe(self, mock_client, ohlcv_df):
        tool = PriceHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["count"] == len(ohlcv_df)

    def test_record_structure(self, mock_client):
        tool = PriceHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        record = result["records"][0]
        for key in ("date", "open", "high", "low", "close", "volume"):
            assert key in record

    def test_currency_populated_from_info(self, mock_client):
        tool = PriceHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["currency"] == "INR"

    def test_uses_period_by_default(self, mock_client):
        tool = PriceHistoryTool(mock_client)
        tool.run("RELIANCE", country_code="IN", period="6mo")
        mock_client.get_ticker.return_value.history.assert_called_once()
        call_kwargs = mock_client.get_ticker.return_value.history.call_args[1]
        assert call_kwargs.get("period") == "6mo"

    def test_uses_start_date_when_provided(self, mock_client):
        tool = PriceHistoryTool(mock_client)
        tool.run("RELIANCE", country_code="IN", start_date="2024-01-01")
        call_kwargs = mock_client.get_ticker.return_value.history.call_args[1]
        assert call_kwargs.get("start") == "2024-01-01"

    def test_uses_interval(self, mock_client):
        tool = PriceHistoryTool(mock_client)
        tool.run("RELIANCE", country_code="IN", interval="1wk")
        call_kwargs = mock_client.get_ticker.return_value.history.call_args[1]
        assert call_kwargs.get("interval") == "1wk"

    def test_empty_dataframe_returns_error(self, mock_client_empty):
        tool = PriceHistoryTool(mock_client_empty)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["count"] == 0
        assert result["records"] == []
        assert "error" in result

    def test_numeric_values_are_floats(self, mock_client):
        tool = PriceHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        record = result["records"][0]
        assert isinstance(record["close"], float)
        assert isinstance(record["volume"], int)

    def test_us_stock_no_suffix(self):
        client = make_mock_client(
            qualified_symbol="AAPL",
            info={"currency": "USD", "currentPrice": 185.0},
        )
        tool = PriceHistoryTool(client)
        result = tool.run("AAPL", country_code="US")
        assert result["symbol"] == "AAPL"
        assert result["currency"] == "USD"
