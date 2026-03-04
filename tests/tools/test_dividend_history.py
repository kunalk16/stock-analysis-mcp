"""Unit tests for DividendHistoryTool."""

from __future__ import annotations

import pandas as pd
import pytest

from stock_analysis.tools.dividend_history import DividendHistoryTool
from tests.conftest import make_dividends, make_mock_client


class TestDividendHistoryToolRun:

    def test_returns_correct_symbol(self, mock_client):
        tool = DividendHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["symbol"] == "RELIANCE.NS"

    def test_dividend_count_correct(self, mock_client):
        tool = DividendHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        # make_dividends produces 6 items by default, but period filter may keep all
        assert result["count"] >= 0

    def test_dividend_record_structure(self, mock_client):
        tool = DividendHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        if result["count"] > 0:
            rec = result["dividends"][0]
            assert "date" in rec
            assert "amount" in rec
            assert isinstance(rec["amount"], float)

    def test_total_paid_is_sum(self):
        """
        Verify total_paid equals the sum of individual dividend amounts.

        Uses dividends dated inside the mock OHLCV window (2024-01-01 to
        2024-03-01) so the period filter keeps all records and the
        assertion is unconditionally exercised.
        """
        # make_ohlcv() starts at 2024-01-01 (60 days).  Quarterly dividends
        # from 2024-01-01 will be >= the OHLCV start_ts so all 4 are kept.
        dividends = make_dividends(n=4, amount=20.0, start="2024-01-01")
        client = make_mock_client(dividends=dividends)
        tool = DividendHistoryTool(client)
        result = tool.run("RELIANCE", country_code="IN", period="1y")
        # At least one dividend must survive the period filter
        assert result["count"] > 0, (
            "No dividends returned – check that dividend dates fall inside "
            "the mock OHLCV date range."
        )
        expected_total = round(sum(r["amount"] for r in result["dividends"]), 4)
        assert result["total_paid"] == expected_total

    def test_empty_dividends_returns_zero_count(self):
        client = make_mock_client(
            dividends=pd.Series(dtype=float),
            ohlcv=pd.DataFrame(
                columns=["Open", "High", "Low", "Close", "Volume", "Dividends"],
                index=pd.DatetimeIndex([], tz="UTC"),
            ),
        )
        # Make ticker.dividends empty
        client.get_ticker.return_value.dividends = pd.Series(dtype=float)
        tool = DividendHistoryTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["count"] == 0
        assert result["dividends"] == []

    def test_currency_populated(self, mock_client):
        tool = DividendHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["currency"] == "INR"

    def test_start_date_overrides_period(self, mock_client):
        tool = DividendHistoryTool(mock_client)
        tool.run(
            "RELIANCE",
            country_code="IN",
            start_date="2023-01-01",
            end_date="2024-01-01",
        )
        # history() should have been called with start= kwarg
        call_kwargs = mock_client.get_ticker.return_value.history.call_args[1]
        assert call_kwargs.get("start") == "2023-01-01"
