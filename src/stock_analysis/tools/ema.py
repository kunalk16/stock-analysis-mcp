# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_ema
Returns the Exponential Moving Average (EMA) for a given number of days.
"""

from __future__ import annotations

import pandas as pd

from stock_analysis.utils.yfinance_client import YFinanceClient


class EMATool:
    """
    Computes the N-day Exponential Moving Average (EMA) of a stock's
    closing price using ``pandas.ewm(span=N, adjust=False)``.

    EMA gives more weight to recent prices compared to a simple DMA,
    making it more responsive to new information.
    """

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        days: int,
        country_code: str | None = None,
        data_period: str = "2y",
        return_series: bool = True,
    ) -> dict:
        """
        Compute the N-day EMA.

        Args:
            symbol:        Ticker symbol (e.g. "WIPRO", "TSLA").
            days:          EMA span in days (e.g. 9, 21, 50, 200).
            country_code:  ISO 3166-1 alpha-2 country code. Defaults to "IN".
            data_period:   History period to fetch. Default "2y".
            return_series: Return full EMA series. Default True.

        Returns:
            Dictionary with:
            - ``symbol``
            - ``days``:          The EMA span requested.
            - ``current_ema``:   Most recent EMA value.
            - ``current_price``: Latest closing price.
            - ``price_vs_ema``:  "above" | "below" | "at" relative to EMA.
            - ``series``:        List of {date, close, ema} (if return_series=True).
            - ``count``
        """
        if days < 1:
            return {"error": "'days' must be a positive integer."}

        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)

        hist: pd.DataFrame = ticker.history(
            period=data_period, interval="1d", auto_adjust=True
        )

        if hist.empty:
            return {
                "symbol": qualified,
                "days": days,
                "current_ema": None,
                "current_price": None,
                "price_vs_ema": None,
                "series": [],
                "count": 0,
                "error": f"No price data found for '{qualified}'.",
            }

        close: pd.Series = hist["Close"]
        # adjust=False mirrors the standard EMA formula used by trading platforms
        ema: pd.Series = close.ewm(span=days, adjust=False).mean()

        current_price = round(float(close.iloc[-1]), 4)
        current_ema = round(float(ema.iloc[-1]), 4)

        diff = current_price - current_ema
        if abs(diff) / current_ema < 0.001:
            price_vs_ema = "at"
        elif diff > 0:
            price_vs_ema = "above"
        else:
            price_vs_ema = "below"

        series: list[dict] = []
        if return_series:
            for idx, (c, e) in enumerate(zip(close, ema)):
                date_idx = close.index[idx]
                series.append(
                    {
                        "date": str(
                            date_idx.date() if hasattr(date_idx, "date") else date_idx
                        ),
                        "close": round(float(c), 4),
                        "ema": round(float(e), 4),
                    }
                )

        return {
            "symbol": qualified,
            "days": days,
            "current_ema": current_ema,
            "current_price": current_price,
            "price_vs_ema": price_vs_ema,
            "series": series,
            "count": len(series),
        }
