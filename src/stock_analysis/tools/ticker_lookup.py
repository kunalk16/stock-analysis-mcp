# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_ticker_for_company
Resolves a company name to its exchange ticker symbol(s).
"""
from __future__ import annotations

from stock_analysis.utils.country_exchange import CountryExchangeMap
from stock_analysis.utils.yfinance_client import YFinanceClient


class TickerLookupTool:
    """
    Converts a human-readable company name (or partial name) into one or
    more ticker symbols using ``yf.Search`` (routed through YFinanceClient
    so the search backend can be replaced in tests).

    Optionally filters results to a specific country / exchange suffix so
    callers receive only tickers relevant to their target market.
    """

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        company_name: str,
        country_code: str | None = None,
        max_results: int = 10,
    ) -> dict:
        """
        Search for tickers matching a company name.

        Args:
            company_name: Full or partial company name (e.g. "Reliance Industries").
            country_code: ISO 3166-1 alpha-2 country code to filter results.
                          Defaults to "IN" (India). Pass "ALL" to return all markets.
            max_results:  Maximum number of results to return. Default 10.

        Returns:
            Dictionary with:
            - ``query``:        Original search query.
            - ``country_code``: Effective country filter.
            - ``matches``:      List of dicts, each containing:
                                ``symbol``, ``name``, ``exchange``, ``type``, ``score``.
            - ``count``:        Number of matches.
        """
        effective_country = (country_code or CountryExchangeMap.DEFAULT_COUNTRY).upper()

        try:
            quotes: list[dict] = self._client.search(
                company_name, max_results=max(max_results * 3, 30)
            )
        except Exception as exc:
            return {
                "query": company_name,
                "country_code": effective_country,
                "matches": [],
                "count": 0,
                "error": str(exc),
            }

        if effective_country != "ALL":
            try:
                suffix = CountryExchangeMap.get_suffix(effective_country)
                # For US stocks suffix is "", so we must check the exchange field
                if suffix:
                    quotes = [q for q in quotes if q.get("symbol", "").endswith(suffix)]
                else:
                    # US – keep symbols without any dot-suffix
                    quotes = [q for q in quotes if "." not in q.get("symbol", "")]
            except ValueError:
                pass  # Unknown country – skip filtering

        matches = [
            {
                "symbol": q.get("symbol", ""),
                "name": q.get("longname") or q.get("shortname") or "",
                "exchange": q.get("exchDisp") or q.get("exchange") or "",
                "type": q.get("typeDisp") or q.get("quoteType") or "",
                "score": round(float(q.get("score", 0)), 4),
            }
            for q in quotes[:max_results]
        ]

        return {
            "query": company_name,
            "country_code": effective_country,
            "matches": matches,
            "count": len(matches),
        }
