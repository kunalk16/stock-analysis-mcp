# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Shared yfinance wrapper with lightweight in-process caching.
"""
from __future__ import annotations

import yfinance as yf

from stock_analysis.utils.country_exchange import CountryExchangeMap


class YFinanceClient:
    """
    Thin wrapper around yfinance that:
    - Resolves country-aware ticker symbols via CountryExchangeMap.
    - Caches ``yf.Ticker`` objects per qualified symbol to avoid redundant
      network round-trips within a single MCP request lifecycle.
    - Provides a uniform error-handling surface for all tool classes.
    """

    def __init__(self) -> None:
        self._cache: dict[str, yf.Ticker] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_ticker(
        self,
        symbol: str,
        country_code: str | None = None,
    ) -> yf.Ticker:
        """
        Return a (cached) ``yf.Ticker`` for *symbol*.

        Args:
            symbol:       Raw or fully-qualified ticker symbol.
            country_code: ISO 3166-1 alpha-2 country code. ``None`` → India.

        Returns:
            A ``yf.Ticker`` instance.
        """
        qualified = CountryExchangeMap.build_ticker(symbol, country_code)
        if qualified not in self._cache:
            self._cache[qualified] = yf.Ticker(qualified)
        return self._cache[qualified]

    def resolve_symbol(
        self,
        symbol: str,
        country_code: str | None = None,
    ) -> str:
        """Return the fully-qualified ticker string without creating a Ticker object."""
        return CountryExchangeMap.build_ticker(symbol, country_code)

    def clear_cache(self) -> None:
        """Evict all cached Ticker objects."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Convenience: yf.Search wrapper
    # ------------------------------------------------------------------

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Search yfinance for tickers matching *query*.

        Kept as an instance method so it can be easily patched in tests
        without touching the ``yfinance`` module directly.

        Returns:
            List of quote dicts (may be empty).
        """
        try:
            results = yf.Search(query, max_results=max_results)
            return results.quotes or []
        except Exception:
            return []
