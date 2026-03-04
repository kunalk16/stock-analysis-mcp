"""Unit tests for QuarterlyResultsTool."""

from __future__ import annotations

import pandas as pd
import pytest

from stock_analysis.tools.quarterly_results import QuarterlyResultsTool
from tests.conftest import (
    make_info,
    make_mock_client,
    make_quarterly_balance,
    make_quarterly_income,
)


class TestQuarterlyResultsToolRun:

    def test_returns_correct_symbol(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        assert result["symbol"] == "RELIANCE.NS"

    def test_currency_populated(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        assert result["currency"] == "INR"

    def test_record_count_equals_num_quarters(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN", num_quarters=4)
        assert result["count"] == 4

    def test_revenue_is_populated(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        revenues = [r["revenue"] for r in result["records"] if r["revenue"] is not None]
        assert len(revenues) > 0
        assert revenues[0] == 2_500_000_000.0

    def test_net_income_is_populated(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        incomes = [
            r["net_income"] for r in result["records"] if r["net_income"] is not None
        ]
        assert len(incomes) > 0

    def test_eps_is_populated(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        eps_vals = [r["eps"] for r in result["records"] if r["eps"] is not None]
        assert len(eps_vals) > 0
        assert eps_vals[0] == 18.5

    def test_approx_pe_computed_from_eps_and_price(self, mock_client):
        # current_price=2500, latest eps=18.5 → annualised=74 → pe = 2500/74 ≈ 33.78
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        pe = result["records"][0]["approx_pe"]
        assert pe is not None
        assert abs(pe - (2500.0 / (18.5 * 4))) < 0.1

    def test_total_debt_populated(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        debts = [
            r["total_debt"] for r in result["records"] if r["total_debt"] is not None
        ]
        assert len(debts) > 0

    def test_empty_income_stmt_returns_error(self, mock_client_empty):
        tool = QuarterlyResultsTool(mock_client_empty)
        result = tool.run("HDFCBANK", country_code="IN")
        assert result["records"] == []
        assert "error" in result

    def test_records_latest_first(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        dates = [r["quarter_end"] for r in result["records"]]
        assert dates == sorted(dates, reverse=True)

    def test_record_fields_present(self, mock_client):
        tool = QuarterlyResultsTool(mock_client)
        result = tool.run("HDFCBANK", country_code="IN")
        rec = result["records"][0]
        expected_keys = [
            "quarter_end",
            "revenue",
            "gross_profit",
            "operating_income",
            "ebitda",
            "net_income",
            "eps",
            "total_assets",
            "total_debt",
            "total_equity",
            "approx_pe",
        ]
        for key in expected_keys:
            assert key in rec, f"Missing key: {key}"
