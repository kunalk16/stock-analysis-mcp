"""Unit tests for YFinanceClient."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from stock_analysis.utils.yfinance_client import YFinanceClient


class TestGetTicker:
    def test_returns_ticker_object(self):
        with patch("stock_analysis.utils.yfinance_client.yf.Ticker") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = YFinanceClient()
            ticker = client.get_ticker("RELIANCE", "IN")
            mock_cls.assert_called_once_with("RELIANCE.NS")
            assert ticker is mock_cls.return_value

    def test_caches_ticker(self):
        with patch("stock_analysis.utils.yfinance_client.yf.Ticker") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = YFinanceClient()
            t1 = client.get_ticker("RELIANCE", "IN")
            t2 = client.get_ticker("RELIANCE", "IN")
            assert t1 is t2
            mock_cls.assert_called_once()  # not twice

    def test_different_symbols_not_cached_together(self):
        with patch("stock_analysis.utils.yfinance_client.yf.Ticker") as mock_cls:
            mock_cls.side_effect = [MagicMock(), MagicMock()]
            client = YFinanceClient()
            t1 = client.get_ticker("RELIANCE", "IN")
            t2 = client.get_ticker("TCS", "IN")
            assert t1 is not t2
            assert mock_cls.call_count == 2

    def test_us_ticker_no_suffix(self):
        with patch("stock_analysis.utils.yfinance_client.yf.Ticker") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = YFinanceClient()
            client.get_ticker("AAPL", "US")
            mock_cls.assert_called_once_with("AAPL")

    def test_clear_cache(self):
        with patch("stock_analysis.utils.yfinance_client.yf.Ticker") as mock_cls:
            mock_cls.side_effect = [MagicMock(), MagicMock()]
            client = YFinanceClient()
            client.get_ticker("RELIANCE", "IN")
            client.clear_cache()
            client.get_ticker("RELIANCE", "IN")
            assert mock_cls.call_count == 2


class TestResolveSymbol:
    def test_resolves_india(self):
        client = YFinanceClient()
        assert client.resolve_symbol("RELIANCE", "IN") == "RELIANCE.NS"

    def test_resolves_us(self):
        client = YFinanceClient()
        assert client.resolve_symbol("AAPL", "US") == "AAPL"


class TestSearch:
    def test_returns_quotes(self):
        mock_result = MagicMock()
        mock_result.quotes = [{"symbol": "RELIANCE.NS", "shortname": "Reliance"}]
        with patch("stock_analysis.utils.yfinance_client.yf.Search", return_value=mock_result):
            client = YFinanceClient()
            results = client.search("Reliance")
            assert len(results) == 1
            assert results[0]["symbol"] == "RELIANCE.NS"

    def test_returns_empty_on_exception(self):
        with patch(
            "stock_analysis.utils.yfinance_client.yf.Search",
            side_effect=Exception("network error"),
        ):
            client = YFinanceClient()
            results = client.search("Reliance")
            assert results == []

    def test_returns_empty_when_quotes_none(self):
        mock_result = MagicMock()
        mock_result.quotes = None
        with patch("stock_analysis.utils.yfinance_client.yf.Search", return_value=mock_result):
            client = YFinanceClient()
            results = client.search("Reliance")
            assert results == []
