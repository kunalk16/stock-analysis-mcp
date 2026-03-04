# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_dma
Returns the Simple Moving Average (DMA) for a given number of days.
"""
from __future__ import annotations

import pandas as pd

from stock_analysis.utils.yfinance_client import YFinanceClient


class DMATool:
    """
    Computes the N-day Simple Moving Average (SMA / DMA) of a stock's
    closing price.

    ``dma`` stands for "Day Moving Average" – commonly used terminology
    in Indian markets (e.g. 50-DMA, 200-DMA).
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
        Compute the N-day DMA (Simple Moving Average).

        Args:
            symbol:        Ticker symbol (e.g. "NIFTY50.NS", "AAPL").
            days:          Number of days for the moving average window (e.g. 50, 200).
            country_code:  ISO 3166-1 alpha-2 country code. Defaults to "IN".
            data_period:   History period to fetch for computation. Default "2y".
                           Increase for very long windows (e.g. "5y" for 200-DMA).
            return_series: Whether to return the full DMA series. Default True.

        Returns:
            Dictionary with:
            - ``symbol``
            - ``days``:            The DMA window requested.
            - ``current_dma``:     The most recent DMA value.
            - ``current_price``:   Latest closing price.
            - ``price_vs_dma``:    "above" | "below" | "at" relative to DMA.
            - ``series``:          List of {date, close, dma} (if return_series=True).
            - ``count``
        """
        if days < 1:
            return {"error": "'days' must be a positive integer."}

        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)

        hist: pd.DataFrame = ticker.history(period=data_period, interval="1d", auto_adjust=True)

        if hist.empty:
            return {
                "symbol": qualified,
                "days": days,
                "current_dma": None,
                "current_price": None,
                "price_vs_dma": None,
                "series": [],
                "count": 0,
                "error": f"No price data found for '{qualified}'.",
            }

        close: pd.Series = hist["Close"]
        dma: pd.Series = close.rolling(window=days, min_periods=days).mean()

        current_price = round(float(close.iloc[-1]), 4)
        current_dma_val = dma.dropna().iloc[-1] if not dma.dropna().empty else None
        current_dma = round(float(current_dma_val), 4) if current_dma_val is not None else None

        if current_dma is not None:
            diff = current_price - current_dma
            if abs(diff) / current_dma < 0.001:
                price_vs_dma = "at"
            elif diff > 0:
                price_vs_dma = "above"
            else:
                price_vs_dma = "below"
        else:
            price_vs_dma = None

        series: list[dict] = []
        if return_series:
            combined = pd.DataFrame({"close": close, "dma": dma}).dropna(subset=["close"])
            for idx, row in combined.iterrows():
                dma_val = row["dma"]
                series.append(
                    {
                        "date": str(idx.date() if hasattr(idx, "date") else idx),
                        "close": round(float(row["close"]), 4),
                        "dma": round(float(dma_val), 4) if pd.notna(dma_val) else None,
                    }
                )

        return {
            "symbol": qualified,
            "days": days,
            "current_dma": current_dma,
            "current_price": current_price,
            "price_vs_dma": price_vs_dma,
            "series": series,
            "count": len(series),
        }
