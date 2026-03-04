"""Unit tests for ValuationHistoryTool."""
from __future__ import annotations

import pytest

from tests.conftest import make_mock_client, make_info, make_ohlcv
from stock_analysis.tools.valuation_history import ValuationHistoryTool


class TestValuationHistoryToolRun:

    def test_returns_correct_symbol(self, mock_client):
        tool = ValuationHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["symbol"] == "RELIANCE.NS"

    def test_ttm_eps_from_info(self, mock_client):
        tool = ValuationHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["ttm_eps"] == 90.0

    def test_book_value_from_info(self, mock_client):
        tool = ValuationHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["book_value_per_share"] == 1_200.0

    def test_pe_ratio_is_computed(self, mock_client):
        tool = ValuationHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        # Records should all have a non-null pe_ratio since eps > 0
        pe_values = [r["pe_ratio"] for r in result["records"] if r["pe_ratio"] is not None]
        assert len(pe_values) > 0

    def test_pb_ratio_is_computed(self, mock_client):
        tool = ValuationHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        pb_values = [r["pb_ratio"] for r in result["records"] if r["pb_ratio"] is not None]
        assert len(pb_values) > 0

    def test_pe_none_when_eps_zero(self):
        info = make_info(trailing_eps=0.0)
        client = make_mock_client(info=info)
        tool = ValuationHistoryTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        for rec in result["records"]:
            assert rec["pe_ratio"] is None

    def test_approximated_market_cap_present(self, mock_client):
        tool = ValuationHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        caps = [r["approx_market_cap"] for r in result["records"] if r["approx_market_cap"]]
        assert len(caps) > 0

    def test_empty_history_returns_error(self, mock_client_empty):
        tool = ValuationHistoryTool(mock_client_empty)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["records"] == []
        assert "error" in result

    def test_record_has_date_and_close(self, mock_client):
        tool = ValuationHistoryTool(mock_client)
        result = tool.run("RELIANCE", country_code="IN")
        rec = result["records"][0]
        assert "date" in rec
        assert "close" in rec
