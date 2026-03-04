# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_dividend_history
Returns historical dividend payouts for a stock.
"""
from __future__ import annotations

import pandas as pd

from stock_analysis.utils.yfinance_client import YFinanceClient


class DividendHistoryTool:
    """
    Fetches the complete dividend payout history for a stock using
    ``ticker.dividends`` (a time-indexed pandas Series).
    """

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        country_code: str | None = None,
        period: str = "5y",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Retrieve dividend history.

        Args:
            symbol:       Ticker symbol (e.g. "RELIANCE", "AAPL").
            country_code: ISO 3166-1 alpha-2 country code. Defaults to "IN".
            period:       Look-back period when start_date is not specified.
                          Default "5y".
            start_date:   Start date "YYYY-MM-DD". Overrides *period*.
            end_date:     End date "YYYY-MM-DD". Used together with *start_date*.

        Returns:
            Dictionary with:
            - ``symbol``
            - ``currency``
            - ``dividends``:    List of dicts: date, amount.
            - ``count``
            - ``total_paid``:   Sum of all dividend amounts in the period.
        """
        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)
        info: dict = ticker.info or {}
        currency: str = info.get("currency", "")

        if start_date:
            hist_df: pd.DataFrame = ticker.history(
                start=start_date, end=end_date, auto_adjust=False
            )
            dividends: pd.Series = hist_df.get("Dividends", pd.Series(dtype=float))
            dividends = dividends[dividends > 0]
        else:
            raw: pd.Series = ticker.dividends
            if raw is None or raw.empty:
                return {
                    "symbol": qualified,
                    "currency": currency,
                    "dividends": [],
                    "count": 0,
                    "total_paid": 0,
                }
            # Filter by period by fetching history to get the date range
            period_hist = ticker.history(period=period, auto_adjust=False)
            if not period_hist.empty:
                start_ts = period_hist.index.min()
                dividends = raw[raw.index >= start_ts]
            else:
                dividends = raw

        if dividends is None or dividends.empty:
            return {
                "symbol": qualified,
                "currency": currency,
                "dividends": [],
                "count": 0,
                "total_paid": 0.0,
            }

        records = [
            {
                "date": str(idx.date() if hasattr(idx, "date") else idx),
                "amount": round(float(val), 4),
            }
            for idx, val in dividends.items()
        ]

        return {
            "symbol": qualified,
            "currency": currency,
            "dividends": records,
            "count": len(records),
            "total_paid": round(float(dividends.sum()), 4),
        }
