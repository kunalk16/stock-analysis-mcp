# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_peer_companies
Lists peer/competitor companies in the same industry as the given ticker.
"""

from __future__ import annotations

from stock_analysis.utils.country_exchange import CountryExchangeMap
from stock_analysis.utils.yfinance_client import YFinanceClient


class PeerCompaniesTool:
    """
    Identifies peer companies for a given stock by:
    1. Reading the ``industry`` and ``sector`` from ``ticker.info``.
    2. Searching yfinance for companies in the same industry.
    3. Filtering results to the same country/exchange suffix.

    Note:
        yfinance does not expose a native "get peers" endpoint.
        This implementation uses ``yf.Search`` and ``ticker.info`` metadata
        as the best available approximation.  For Indian stocks the
        ``ticker.info`` field ``companyOfficers`` is ignored; instead we
        rely on the industry keyword search.
    """

    _MAX_SEARCH_CANDIDATES = 40

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        country_code: str | None = None,
        max_peers: int = 15,
    ) -> dict:
        """
        Fetch peer companies for a stock.

        Args:
            symbol:       Ticker symbol (e.g. "RELIANCE", "AAPL").
            country_code: ISO 3166-1 alpha-2 country code. Defaults to "IN".
            max_peers:    Maximum number of peer companies to return. Default 15.

        Returns:
            Dictionary with:
            - ``symbol``:       Qualified ticker of the reference company.
            - ``company_name``: Name of the reference company.
            - ``industry``:     Industry label.
            - ``sector``:       Sector label.
            - ``country_code``: Effective country filter.
            - ``peers``:        List of dicts: symbol, name, exchange, market_cap.
            - ``count``:        Number of peers found.
        """
        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)
        info: dict = ticker.info or {}

        industry: str = info.get("industry") or ""
        sector: str = info.get("sector") or ""
        company_name: str = info.get("longName") or info.get("shortName") or symbol

        if not industry and not sector:
            return {
                "symbol": qualified,
                "company_name": company_name,
                "industry": industry,
                "sector": sector,
                "country_code": (
                    country_code or CountryExchangeMap.DEFAULT_COUNTRY
                ).upper(),
                "peers": [],
                "count": 0,
                "error": (
                    f"Could not determine industry/sector for '{qualified}'. "
                    "Peer search is unavailable."
                ),
            }

        search_query = industry or sector
        effective_country = (country_code or CountryExchangeMap.DEFAULT_COUNTRY).upper()

        try:
            suffix = CountryExchangeMap.get_suffix(effective_country)
        except ValueError:
            suffix = ""

        try:
            quotes: list[dict] = self._client.search(
                search_query,
                max_results=self._MAX_SEARCH_CANDIDATES,
            )
        except Exception as exc:
            return {
                "symbol": qualified,
                "company_name": company_name,
                "industry": industry,
                "sector": sector,
                "country_code": effective_country,
                "peers": [],
                "count": 0,
                "error": str(exc),
            }

        # Filter by exchange suffix and exclude the queried company itself
        if suffix:
            quotes = [q for q in quotes if q.get("symbol", "").endswith(suffix)]
        else:
            quotes = [q for q in quotes if "." not in q.get("symbol", "")]

        quotes = [q for q in quotes if q.get("symbol", "").upper() != qualified.upper()]

        peers = []
        for q in quotes[:max_peers]:
            sym = q.get("symbol", "")
            try:
                peer_ticker = self._client.get_ticker(sym)
                peer_info = peer_ticker.info or {}
                mkt_cap = peer_info.get("marketCap")
                peer_industry = peer_info.get("industry", "")
            except Exception:
                mkt_cap = None
                peer_industry = ""

            peers.append(
                {
                    "symbol": sym,
                    "name": q.get("longname") or q.get("shortname") or "",
                    "exchange": q.get("exchDisp") or q.get("exchange") or "",
                    "industry": peer_industry,
                    "market_cap": mkt_cap,
                }
            )

        return {
            "symbol": qualified,
            "company_name": company_name,
            "industry": industry,
            "sector": sector,
            "country_code": effective_country,
            "peers": peers,
            "count": len(peers),
        }
