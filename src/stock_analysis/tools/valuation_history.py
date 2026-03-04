# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_valuation_history
Returns historical P/E, P/B, EV/EBITDA and related valuation metrics.
"""
from __future__ import annotations

import pandas as pd

from stock_analysis.utils.yfinance_client import YFinanceClient


class ValuationHistoryTool:
    """
    Computes historical valuation metrics by combining daily closing prices
    with trailing EPS / book-value data from yfinance.

    Note:
        yfinance only exposes a point-in-time EPS and book value via
        ``ticker.info``, so the historical P/E and P/B series are
        approximations that hold the fundamental denominator constant
        while varying the price.  For a fully dynamic fundamental series
        you would need a paid data provider.
    """

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        country_code: str | None = None,
        period: str = "1y",
    ) -> dict:
        """
        Retrieve historical valuation data.

        Args:
            symbol:       Ticker symbol.
            country_code: ISO 3166-1 alpha-2 country code. Defaults to "IN".
            period:       Look-back period. Default "1y".

        Returns:
            Dictionary with:
            - ``symbol``
            - ``currency``
            - ``ttm_eps``:          Trailing twelve-month EPS (point-in-time).
            - ``book_value_per_share``: Point-in-time book value per share.
            - ``records``:          List of dicts with date, close, pe_ratio,
                                    pb_ratio, market_cap (approx.)
            - ``count``
        """
        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)

        info: dict = ticker.info or {}
        ttm_eps: float | None = info.get("trailingEps") or info.get("epsTrailingTwelveMonths")
        book_value: float | None = info.get("bookValue")
        shares_outstanding: float | None = (
            info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        )
        currency: str = info.get("currency", "")

        hist: pd.DataFrame = ticker.history(period=period, interval="1d", auto_adjust=True)

        if hist.empty:
            return {
                "symbol": qualified,
                "currency": currency,
                "ttm_eps": ttm_eps,
                "book_value_per_share": book_value,
                "records": [],
                "count": 0,
                "error": f"No price data found for '{qualified}'.",
            }

        records = []
        for idx, row in hist.iterrows():
            close = float(row["Close"])
            pe = round(close / ttm_eps, 2) if ttm_eps and ttm_eps > 0 else None
            pb = round(close / book_value, 2) if book_value and book_value > 0 else None
            mkt_cap = (
                round(close * shares_outstanding, 0)
                if shares_outstanding
                else None
            )
            records.append(
                {
                    "date": str(idx.date() if hasattr(idx, "date") else idx),
                    "close": round(close, 4),
                    "pe_ratio": pe,
                    "pb_ratio": pb,
                    "approx_market_cap": mkt_cap,
                }
            )

        return {
            "symbol": qualified,
            "currency": currency,
            "ttm_eps": ttm_eps,
            "book_value_per_share": book_value,
            "records": records,
            "count": len(records),
        }
