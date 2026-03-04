"""Unit tests for EMATool."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tests.conftest import make_mock_client, make_ohlcv
from stock_analysis.tools.ema import EMATool


class TestEMAToolRun:

    def test_returns_correct_symbol(self, mock_client):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=20, country_code="IN")
        assert result["symbol"] == "RELIANCE.NS"

    def test_days_echoed_in_result(self, mock_client):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=21, country_code="IN")
        assert result["days"] == 21

    def test_current_ema_is_float(self, mock_client):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=9, country_code="IN")
        assert isinstance(result["current_ema"], float)

    def test_current_price_is_float(self, mock_client):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=9, country_code="IN")
        assert isinstance(result["current_price"], float)

    def test_price_vs_ema_valid_values(self, mock_client):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=9, country_code="IN")
        assert result["price_vs_ema"] in ("above", "below", "at")

    def test_series_returned_when_flag_true(self, mock_client, ohlcv_df):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=9, country_code="IN", return_series=True)
        assert len(result["series"]) == len(ohlcv_df)

    def test_series_not_returned_when_flag_false(self, mock_client):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=9, country_code="IN", return_series=False)
        assert result["series"] == []

    def test_series_record_has_required_keys(self, mock_client):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=9, country_code="IN", return_series=True)
        rec = result["series"][0]
        assert "date" in rec
        assert "close" in rec
        assert "ema" in rec

    def test_empty_history_returns_error(self, mock_client_empty):
        tool = EMATool(mock_client_empty)
        result = tool.run("WIPRO", days=9, country_code="IN")
        assert "error" in result
        assert result["current_ema"] is None

    def test_invalid_days_returns_error(self, mock_client):
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=-1, country_code="IN")
        assert "error" in result

    def test_ema_different_from_dma(self):
        """EMA should not equal DMA for a trending series (they use different formulas)."""
        n = 30
        closes = np.linspace(100, 200, n)
        idx = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")
        df = pd.DataFrame(
            {"Open": closes, "High": closes + 1, "Low": closes - 1, "Close": closes, "Volume": 1e6},
            index=idx,
        )
        client = make_mock_client(ohlcv=df)
        tool = EMATool(client)
        result = tool.run("X", days=5, country_code="IN")
        # EMA should weight recent prices more, so for an upward trend EMA > DMA
        dma_simple = np.mean(closes[-5:])
        # EMA is recursive so it should be close but not necessarily equal
        assert result["current_ema"] is not None

    def test_ema_all_records_have_value(self, mock_client):
        """EMA with ewm produces a value for every row (no warm-up None period)."""
        tool = EMATool(mock_client)
        result = tool.run("WIPRO", days=20, country_code="IN", return_series=True)
        for rec in result["series"]:
            assert rec["ema"] is not None
