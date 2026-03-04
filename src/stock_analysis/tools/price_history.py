# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_price_history
Returns OHLCV price history for a stock.
"""

from __future__ import annotations

import pandas as pd

from stock_analysis.utils.yfinance_client import YFinanceClient


class PriceHistoryTool:
    """
    Fetches historical OHLCV (Open, High, Low, Close, Volume) data
    for a given ticker symbol.

    Supports both a convenience *period* argument (e.g. "1y", "6mo") and
    explicit *start_date* / *end_date* date strings ("YYYY-MM-DD").
    """

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        country_code: str | None = None,
        period: str = "1y",
        interval: str = "1d",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        """
        Retrieve OHLCV price history.

        Args:
            symbol:       Ticker symbol (e.g. "RELIANCE" for India, "AAPL" for US).
            country_code: ISO 3166-1 alpha-2 country code. Defaults to "IN" (India).
            period:       yfinance period string – used only when start_date is None.
                          Valid values: "1d","5d","1mo","3mo","6mo","1y","2y",
                          "5y","10y","ytd","max". Default "1y".
            interval:     Data granularity: "1d","1wk","1mo","1h","15m", etc.
                          Default "1d".
            start_date:   Start date "YYYY-MM-DD". Overrides *period* when provided.
            end_date:     End date "YYYY-MM-DD". Used together with *start_date*.

        Returns:
            Dictionary with keys:
            - ``symbol``:     Fully-qualified ticker used.
            - ``currency``:   Currency (from ticker info).
            - ``records``:    List of dicts with date, open, high, low, close, volume.
            - ``count``:      Number of data points returned.
        """
        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)

        if start_date:
            hist: pd.DataFrame = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True,
            )
        else:
            hist = ticker.history(
                period=period,
                interval=interval,
                auto_adjust=True,
            )

        if hist.empty:
            return {
                "symbol": qualified,
                "currency": "",
                "records": [],
                "count": 0,
                "error": f"No price data found for '{qualified}'. "
                "Check the symbol or date range.",
            }

        currency = (ticker.info or {}).get("currency", "")

        records = [
            {
                "date": str(idx.date() if hasattr(idx, "date") else idx),
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(row["Volume"]),
            }
            for idx, row in hist.iterrows()
        ]

        return {
            "symbol": qualified,
            "currency": currency,
            "records": records,
            "count": len(records),
        }
