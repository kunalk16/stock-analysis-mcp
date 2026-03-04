"""Unit tests for PeerCompaniesTool."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tests.conftest import make_mock_client, make_info
from stock_analysis.tools.peer_companies import PeerCompaniesTool


_PEER_QUOTES = [
    {"symbol": "ONGC.NS", "longname": "Oil & Natural Gas Corp", "exchDisp": "NSE"},
    {"symbol": "IOC.NS", "longname": "Indian Oil Corp", "exchDisp": "NSE"},
    {"symbol": "BPCL.NS", "longname": "Bharat Petroleum", "exchDisp": "NSE"},
]


def _make_peer_ticker(market_cap: float = 5e11, industry: str = "Oil & Gas") -> MagicMock:
    t = MagicMock()
    t.info = {"marketCap": market_cap, "industry": industry}
    return t


class TestPeerCompaniesToolRun:

    def _make_client_with_peers(self) -> MagicMock:
        """Client: the reference ticker is RELIANCE.NS; search returns 3 peers."""
        client = make_mock_client(search_results=_PEER_QUOTES)
        # Also make get_ticker return a generic peer ticker for peer info lookups
        peer_ticker = _make_peer_ticker()
        # First call is the reference company, subsequent calls are peers
        original_side_effect = [
            client.get_ticker.return_value,   # reference company
            peer_ticker, peer_ticker, peer_ticker,  # peers
        ]
        client.get_ticker.side_effect = original_side_effect
        return client

    def test_returns_company_name(self):
        client = self._make_client_with_peers()
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["company_name"] == "Reliance Industries Limited"

    def test_returns_industry(self):
        client = self._make_client_with_peers()
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["industry"] == "Oil & Gas Refining & Marketing"

    def test_returns_sector(self):
        client = self._make_client_with_peers()
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        assert result["sector"] == "Energy"

    def test_peers_filtered_to_same_exchange(self):
        client = self._make_client_with_peers()
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        for peer in result["peers"]:
            assert peer["symbol"].endswith(".NS")

    def test_reference_symbol_excluded_from_peers(self):
        # Add the reference symbol to search results
        quotes_with_self = _PEER_QUOTES + [
            {"symbol": "RELIANCE.NS", "longname": "Reliance Industries", "exchDisp": "NSE"}
        ]
        client = make_mock_client(search_results=quotes_with_self)
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        peer_symbols = [p["symbol"] for p in result["peers"]]
        assert "RELIANCE.NS" not in peer_symbols

    def test_error_when_no_industry(self):
        info = make_info(industry="", sector="")
        client = make_mock_client(info=info)
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        assert "error" in result
        assert result["count"] == 0

    def test_search_exception_returns_error(self):
        client = make_mock_client()
        client.search.side_effect = Exception("network error")
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        assert "error" in result

    def test_max_peers_respected(self):
        many_peers = [
            {"symbol": f"X{i}.NS", "longname": f"Co {i}", "exchDisp": "NSE"}
            for i in range(20)
        ]
        client = make_mock_client(search_results=many_peers)
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN", max_peers=5)
        assert result["count"] <= 5

    def test_peer_structure_has_required_keys(self):
        client = self._make_client_with_peers()
        tool = PeerCompaniesTool(client)
        result = tool.run("RELIANCE", country_code="IN")
        if result["count"] > 0:
            peer = result["peers"][0]
            for key in ("symbol", "name", "exchange"):
                assert key in peer
