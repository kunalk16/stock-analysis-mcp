"""Unit tests for ShareholdingPatternTool."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pandas as pd
import pytest

from stock_analysis.tools.shareholding_pattern import ShareholdingPatternTool
from tests.conftest import make_mock_client


class TestShareholdingPatternToolRun:

    def test_returns_correct_symbol(self, mock_client):
        tool = ShareholdingPatternTool(mock_client)
        result = tool.run("TCS", country_code="IN")
        assert result["symbol"] == "RELIANCE.NS"  # driven by mock

    def test_major_holders_list_returned(self, mock_client):
        tool = ShareholdingPatternTool(mock_client)
        result = tool.run("TCS", country_code="IN")
        assert isinstance(result["major_holders"], list)
        assert len(result["major_holders"]) > 0

    def test_major_holder_has_value_and_description(self, mock_client):
        tool = ShareholdingPatternTool(mock_client)
        result = tool.run("TCS", country_code="IN")
        entry = result["major_holders"][0]
        assert "value" in entry
        assert "description" in entry

    def test_institutional_holders_list_returned(self, mock_client):
        tool = ShareholdingPatternTool(mock_client)
        result = tool.run("TCS", country_code="IN")
        assert isinstance(result["institutional_holders"], list)

    def test_institutional_holder_has_holder_column(self, mock_client):
        tool = ShareholdingPatternTool(mock_client)
        result = tool.run("TCS", country_code="IN")
        if result["institutional_holders"]:
            assert "Holder" in result["institutional_holders"][0]

    def test_mutualfund_holders_returned(self, mock_client):
        tool = ShareholdingPatternTool(mock_client)
        result = tool.run("TCS", country_code="IN")
        assert "mutualfund_holders" in result

    def test_empty_major_holders_returns_list(self, mock_client_empty):
        tool = ShareholdingPatternTool(mock_client_empty)
        result = tool.run("TCS", country_code="IN")
        assert result["major_holders"] == []

    def test_empty_institutional_returns_list(self, mock_client_empty):
        tool = ShareholdingPatternTool(mock_client_empty)
        result = tool.run("TCS", country_code="IN")
        assert result["institutional_holders"] == []

    def test_exception_in_major_holders_adds_error_key(self):
        """
        Verify that an exception raised when accessing major_holders is caught
        gracefully and does not propagate to the caller.

        Uses a dedicated ``MockTicker`` subclass so that ``PropertyMock`` is
        set on a *unique* type rather than the shared ``MagicMock`` class,
        preventing class-level state pollution between tests.
        """

        # Create a unique subclass per test: type(raising_ticker) == MockTicker,
        # not the shared MagicMock, so PropertyMock doesn't bleed into other tests.
        class MockTicker(MagicMock):
            pass

        raising_ticker = MockTicker()
        type(raising_ticker).major_holders = PropertyMock(
            side_effect=RuntimeError("major_holders unavailable")
        )

        mock_client = make_mock_client()
        mock_client.get_ticker.return_value = raising_ticker

        tool = ShareholdingPatternTool(mock_client)
        result = tool.run("TCS", country_code="IN")
        # Tool must catch the exception and not re-raise it
        assert "major_holders" in result
        assert "major_holders_error" in result
