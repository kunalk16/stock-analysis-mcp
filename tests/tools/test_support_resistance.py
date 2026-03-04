"""Unit tests for SupportResistanceTool."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tests.conftest import make_mock_client, make_ohlcv
from stock_analysis.tools.support_resistance import SupportResistanceTool


def make_sinusoidal_ohlcv(n: int = 120, base: float = 1000.0) -> pd.DataFrame:
    """
    Create OHLCV data with a clear sinusoidal pattern so that
    argrelextrema can reliably detect highs and lows.
    """
    idx = pd.date_range("2023-01-01", periods=n, freq="D", tz="UTC")
    t = np.linspace(0, 4 * np.pi, n)
    closes = base + 100 * np.sin(t)
    highs = closes + 15
    lows = closes - 15
    opens = closes - 5
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": 1e6},
        index=idx,
    )


class TestSupportResistanceToolRun:

    def test_returns_correct_symbol(self, mock_client):
        tool = SupportResistanceTool(mock_client)
        result = tool.run("TATASTEEL", country_code="IN")
        assert result["symbol"] == "RELIANCE.NS"

    def test_current_price_is_float(self, mock_client):
        tool = SupportResistanceTool(mock_client)
        result = tool.run("TATASTEEL", country_code="IN")
        assert isinstance(result["current_price"], float)

    def test_pivot_points_structure(self, mock_client):
        tool = SupportResistanceTool(mock_client)
        result = tool.run("TATASTEEL", country_code="IN")
        pp = result["pivot_points"]
        for key in ("pivot", "R1", "R2", "R3", "S1", "S2", "S3"):
            assert key in pp, f"Missing pivot key: {key}"

    def test_pivot_is_float(self, mock_client):
        tool = SupportResistanceTool(mock_client)
        result = tool.run("TATASTEEL", country_code="IN")
        assert isinstance(result["pivot_points"]["pivot"], float)

    def test_resistance_and_support_lists_present(self, mock_client):
        tool = SupportResistanceTool(mock_client)
        result = tool.run("TATASTEEL", country_code="IN")
        assert isinstance(result["resistance_levels"], list)
        assert isinstance(result["support_levels"], list)

    def test_level_structure_has_required_keys(self):
        df = make_sinusoidal_ohlcv(n=120)
        client = make_mock_client(ohlcv=df)
        tool = SupportResistanceTool(client)
        result = tool.run("TATASTEEL", country_code="IN", order=5)
        for level in result["resistance_levels"] + result["support_levels"]:
            assert "price" in level
            assert "touch_count" in level
            assert "type" in level

    def test_resistance_levels_above_or_near_current_price(self):
        df = make_sinusoidal_ohlcv(n=120)
        client = make_mock_client(ohlcv=df)
        tool = SupportResistanceTool(client)
        result = tool.run("TATASTEEL", country_code="IN", order=5)
        tolerance = result["current_price"] * 0.01
        for lvl in result["resistance_levels"]:
            assert lvl["price"] > result["current_price"] - tolerance

    def test_support_levels_below_or_near_current_price(self):
        df = make_sinusoidal_ohlcv(n=120)
        client = make_mock_client(ohlcv=df)
        tool = SupportResistanceTool(client)
        result = tool.run("TATASTEEL", country_code="IN", order=5)
        tolerance = result["current_price"] * 0.01
        for lvl in result["support_levels"]:
            assert lvl["price"] < result["current_price"] + tolerance

    def test_nearest_resistance_is_closest_above(self):
        df = make_sinusoidal_ohlcv(n=120)
        client = make_mock_client(ohlcv=df)
        tool = SupportResistanceTool(client)
        result = tool.run("TATASTEEL", country_code="IN", order=5)
        if result["nearest_resistance"] and result["resistance_levels"]:
            min_resistance = min(result["resistance_levels"], key=lambda x: x["price"])
            assert result["nearest_resistance"]["price"] == min_resistance["price"]

    def test_nearest_support_is_closest_below(self):
        df = make_sinusoidal_ohlcv(n=120)
        client = make_mock_client(ohlcv=df)
        tool = SupportResistanceTool(client)
        result = tool.run("TATASTEEL", country_code="IN", order=5)
        if result["nearest_support"] and result["support_levels"]:
            max_support = max(result["support_levels"], key=lambda x: x["price"])
            assert result["nearest_support"]["price"] == max_support["price"]

    def test_insufficient_data_returns_error(self, mock_client_empty):
        tool = SupportResistanceTool(mock_client_empty)
        result = tool.run("TATASTEEL", country_code="IN")
        assert "error" in result

    def test_touch_count_at_least_one(self):
        df = make_sinusoidal_ohlcv(n=120)
        client = make_mock_client(ohlcv=df)
        tool = SupportResistanceTool(client)
        result = tool.run("TATASTEEL", country_code="IN", order=5)
        for lvl in result["resistance_levels"] + result["support_levels"]:
            assert lvl["touch_count"] >= 1

    def test_pivot_formula_correctness(self):
        """Verify classic pivot = (H + L + C) / 3 from the penultimate candle."""
        n = 10
        df = make_sinusoidal_ohlcv(n=n, base=500.0)
        client = make_mock_client(ohlcv=df)
        tool = SupportResistanceTool(client)
        result = tool.run("X", country_code="IN", order=2)
        prev_high = float(df["High"].iloc[-2])
        prev_low = float(df["Low"].iloc[-2])
        prev_close = float(df["Close"].iloc[-2])
        expected_pivot = round((prev_high + prev_low + prev_close) / 3, 4)
        assert result["pivot_points"]["pivot"] == expected_pivot
