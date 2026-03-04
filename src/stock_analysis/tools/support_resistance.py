# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_support_resistance
Identifies current support and resistance levels for a stock.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from stock_analysis.utils.yfinance_client import YFinanceClient


class SupportResistanceTool:
    """
    Detects significant support and resistance price levels using a
    combination of:

    1. **Local swing highs/lows** – identified via ``scipy.signal.argrelextrema``
       on the daily OHLCV series.
    2. **Round-number clustering** – nearby levels are merged when within
       a configurable tolerance (default 0.5 % of current price) to avoid
       noise.
    3. **Pivot Points** (Classic formula) – daily pivot, S1/S2/S3, R1/R2/R3
       calculated from the most recent completed candle.

    Levels are ranked by how many times price has touched / reversed near them.
    """

    _DEFAULT_ORDER = 5          # bars on each side for swing detection
    _CLUSTER_TOLERANCE = 0.005  # 0.5 % price band for merging nearby levels

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        country_code: str | None = None,
        lookback_period: str = "6mo",
        order: int = 5,
    ) -> dict:
        """
        Compute current support and resistance levels.

        Args:
            symbol:          Ticker symbol (e.g. "TATASTEEL", "NVDA").
            country_code:    ISO 3166-1 alpha-2 country code. Defaults to "IN".
            lookback_period: History period used for swing detection. Default "6mo".
            order:           Number of bars on each side required to qualify a
                             local extremum. Higher = fewer, more significant levels.

        Returns:
            Dictionary with:
            - ``symbol``
            - ``current_price``
            - ``pivot_points``:   Classic pivot, R1-R3, S1-S3 from last candle.
            - ``resistance_levels``: Sorted list of resistance zones (price > current).
            - ``support_levels``:    Sorted list of support zones (price < current).
              Each level dict: {price, touch_count, type}.
            - ``nearest_resistance``: Closest resistance level above current price.
            - ``nearest_support``:    Closest support level below current price.
        """
        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)

        hist: pd.DataFrame = ticker.history(period=lookback_period, interval="1d", auto_adjust=True)

        if hist.empty or len(hist) < (order * 2 + 1):
            return {
                "symbol": qualified,
                "current_price": None,
                "pivot_points": {},
                "resistance_levels": [],
                "support_levels": [],
                "nearest_resistance": None,
                "nearest_support": None,
                "error": f"Insufficient price data for '{qualified}'.",
            }

        close: np.ndarray = hist["Close"].values
        high: np.ndarray = hist["High"].values
        low: np.ndarray = hist["Low"].values

        current_price = round(float(close[-1]), 4)
        tolerance = current_price * self._CLUSTER_TOLERANCE

        # ---- Swing highs and lows ----
        resistance_idx = argrelextrema(high, np.greater_equal, order=order)[0]
        support_idx = argrelextrema(low, np.less_equal, order=order)[0]

        raw_resistance = [float(high[i]) for i in resistance_idx]
        raw_support = [float(low[i]) for i in support_idx]

        resistance_levels = self._cluster_levels(raw_resistance, tolerance, "resistance")
        support_levels = self._cluster_levels(raw_support, tolerance, "support")

        # Only keep levels on the correct side of current price
        resistance_levels = [
            lvl for lvl in resistance_levels if lvl["price"] > current_price - tolerance
        ]
        support_levels = [
            lvl for lvl in support_levels if lvl["price"] < current_price + tolerance
        ]

        resistance_levels.sort(key=lambda x: x["price"])
        support_levels.sort(key=lambda x: x["price"], reverse=True)

        nearest_resistance = resistance_levels[0] if resistance_levels else None
        nearest_support = support_levels[0] if support_levels else None

        # ---- Classic Pivot Points (last completed candle) ----
        prev_high = float(high[-2]) if len(high) >= 2 else float(high[-1])
        prev_low = float(low[-2]) if len(low) >= 2 else float(low[-1])
        prev_close = float(close[-2]) if len(close) >= 2 else float(close[-1])

        pivot = round((prev_high + prev_low + prev_close) / 3, 4)
        r1 = round(2 * pivot - prev_low, 4)
        r2 = round(pivot + (prev_high - prev_low), 4)
        r3 = round(prev_high + 2 * (pivot - prev_low), 4)
        s1 = round(2 * pivot - prev_high, 4)
        s2 = round(pivot - (prev_high - prev_low), 4)
        s3 = round(prev_low - 2 * (prev_high - pivot), 4)

        return {
            "symbol": qualified,
            "current_price": current_price,
            "pivot_points": {
                "pivot": pivot,
                "R1": r1, "R2": r2, "R3": r3,
                "S1": s1, "S2": s2, "S3": s3,
            },
            "resistance_levels": resistance_levels,
            "support_levels": support_levels,
            "nearest_resistance": nearest_resistance,
            "nearest_support": nearest_support,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cluster_levels(
        prices: list[float],
        tolerance: float,
        level_type: str,
    ) -> list[dict]:
        """
        Merge nearby price levels within *tolerance* into a single cluster.

        Returns a list of dicts sorted by price, each with the mean price of
        the cluster and the number of times price visited that zone.
        """
        if not prices:
            return []

        prices_sorted = sorted(prices)
        clusters: list[list[float]] = []
        current_cluster: list[float] = [prices_sorted[0]]

        for price in prices_sorted[1:]:
            if price - current_cluster[-1] <= tolerance:
                current_cluster.append(price)
            else:
                clusters.append(current_cluster)
                current_cluster = [price]
        clusters.append(current_cluster)

        result = []
        for cluster in clusters:
            result.append(
                {
                    "price": round(float(np.mean(cluster)), 4),
                    "touch_count": len(cluster),
                    "type": level_type,
                }
            )
        return result
