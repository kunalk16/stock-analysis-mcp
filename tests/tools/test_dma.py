"""Unit tests for DMATool."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stock_analysis.tools.dma import DMATool
from tests.conftest import make_mock_client, make_ohlcv


class TestDMAToolRun:

    def test_returns_correct_symbol(self, mock_client):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=20, country_code="IN")
        assert result["symbol"] == "RELIANCE.NS"

    def test_days_echoed_in_result(self, mock_client):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=50, country_code="IN")
        assert result["days"] == 50

    def test_current_dma_is_float(self, mock_client):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=10, country_code="IN")
        assert isinstance(result["current_dma"], float)

    def test_current_price_is_float(self, mock_client):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=10, country_code="IN")
        assert isinstance(result["current_price"], float)

    def test_price_vs_dma_above_or_below(self, mock_client):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=10, country_code="IN")
        assert result["price_vs_dma"] in ("above", "below", "at")

    def test_series_returned_when_flag_true(self, mock_client, ohlcv_df):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=5, country_code="IN", return_series=True)
        assert len(result["series"]) > 0

    def test_series_not_returned_when_flag_false(self, mock_client):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=5, country_code="IN", return_series=False)
        assert result["series"] == []

    def test_series_record_structure(self, mock_client):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=5, country_code="IN", return_series=True)
        if result["series"]:
            rec = result["series"][-1]
            assert "date" in rec
            assert "close" in rec
            assert "dma" in rec

    def test_dma_none_before_window_filled(self, mock_client, ohlcv_df):
        """DMA should be None for the first (days-1) rows in the series."""
        days = 10
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=days, country_code="IN", return_series=True)
        # First (days-1) records should have dma=None
        early = result["series"][: days - 1]
        assert all(r["dma"] is None for r in early)

    def test_empty_history_returns_error(self, mock_client_empty):
        tool = DMATool(mock_client_empty)
        result = tool.run("RELIANCE", days=20, country_code="IN")
        assert "error" in result
        assert result["current_dma"] is None

    def test_invalid_days_returns_error(self, mock_client):
        tool = DMATool(mock_client)
        result = tool.run("RELIANCE", days=0, country_code="IN")
        assert "error" in result

    def test_200_dma_returns_none_dma_for_short_data(self):
        """When data is shorter than the DMA window, current_dma should be None."""
        short_df = make_ohlcv(n=30)
        client = make_mock_client(ohlcv=short_df)
        tool = DMATool(client)
        result = tool.run("RELIANCE", days=200, country_code="IN")
        assert result["current_dma"] is None

    def test_dma_value_mathematically_correct(self):
        """DMA[N] == average of last N closes."""
        n = 30
        closes = np.linspace(100, 200, n)
        idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
        df = pd.DataFrame(
            {
                "Open": closes,
                "High": closes + 1,
                "Low": closes - 1,
                "Close": closes,
                "Volume": 1e6,
            },
            index=idx,
        )
        client = make_mock_client(ohlcv=df)
        tool = DMATool(client)
        days = 5
        result = tool.run("X", days=days, country_code="IN")
        expected_dma = round(float(np.mean(closes[-days:])), 4)
        assert result["current_dma"] == expected_dma
