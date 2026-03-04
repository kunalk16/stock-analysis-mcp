# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_quarterly_results
Returns quarterly financial data: revenue, net profit, EPS, P/E, etc.
"""
from __future__ import annotations

import pandas as pd

from stock_analysis.utils.yfinance_client import YFinanceClient


class QuarterlyResultsTool:
    """
    Aggregates quarterly financial results from multiple yfinance endpoints:
    - ``ticker.quarterly_income_stmt`` – Revenue, Gross Profit, Net Income.
    - ``ticker.quarterly_earnings``    – EPS per quarter (if available).
    - ``ticker.quarterly_balance_sheet``– Total Assets, Total Debt, Equity.
    - ``ticker.info``                  – Current P/E, forward EPS, etc.

    The resulting records are aligned by quarter-end date so callers get
    one consolidated row per quarter.
    """

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        country_code: str | None = None,
        num_quarters: int = 8,
    ) -> dict:
        """
        Fetch quarterly financial results.

        Args:
            symbol:        Ticker symbol (e.g. "HDFCBANK", "MSFT").
            country_code:  ISO 3166-1 alpha-2 country code. Defaults to "IN".
            num_quarters:  How many recent quarters to return. Default 8.

        Returns:
            Dictionary with:
            - ``symbol``
            - ``currency``
            - ``records``:  List of quarterly dicts (latest first):
                            quarter_end, revenue, gross_profit, net_income,
                            eps, pe_ratio (approx), ebitda, total_debt,
                            total_equity.
            - ``count``
        """
        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)
        info: dict = ticker.info or {}
        currency: str = info.get("currency", "")
        current_price: float | None = info.get("currentPrice") or info.get("regularMarketPrice")

        # ---- Income statement ----
        income_df = self._safe_df(ticker.quarterly_income_stmt)
        # ---- Balance sheet ----
        balance_df = self._safe_df(ticker.quarterly_balance_sheet)
        # ---- Earnings (EPS) ----
        earnings_df = self._safe_df(getattr(ticker, "quarterly_earnings", None))

        # Determine quarters from income statement columns
        if income_df is not None and not income_df.empty:
            quarters = sorted(income_df.columns, reverse=True)[:num_quarters]
        else:
            return {
                "symbol": qualified,
                "currency": currency,
                "records": [],
                "count": 0,
                "error": f"No quarterly financial data found for '{qualified}'.",
            }

        records = []
        for quarter_date in quarters:
            rec: dict = {
                "quarter_end": str(quarter_date.date() if hasattr(quarter_date, "date") else quarter_date),
            }

            # Income statement fields
            rec["revenue"] = self._get_val(income_df, quarter_date, [
                "Total Revenue", "TotalRevenue",
            ])
            rec["gross_profit"] = self._get_val(income_df, quarter_date, [
                "Gross Profit", "GrossProfit",
            ])
            rec["operating_income"] = self._get_val(income_df, quarter_date, [
                "Operating Income", "OperatingIncome", "EBIT",
            ])
            rec["ebitda"] = self._get_val(income_df, quarter_date, [
                "EBITDA", "Normalized EBITDA",
            ])
            rec["net_income"] = self._get_val(income_df, quarter_date, [
                "Net Income", "NetIncome", "Net Income Common Stockholders",
            ])
            rec["eps"] = self._get_val(income_df, quarter_date, [
                "Basic EPS", "Diluted EPS", "EPS",
            ])

            # Balance sheet fields
            rec["total_assets"] = self._get_val(balance_df, quarter_date, [
                "Total Assets", "TotalAssets",
            ])
            rec["total_debt"] = self._get_val(balance_df, quarter_date, [
                "Total Debt", "TotalDebt", "Long Term Debt And Capital Lease Obligation",
            ])
            rec["total_equity"] = self._get_val(balance_df, quarter_date, [
                "Stockholders Equity", "Total Equity Gross Minority Interest",
                "Common Stock Equity",
            ])

            # Approx P/E = current price / (annualised quarterly EPS)
            if rec["eps"] and rec["eps"] != 0 and current_price:
                annualised_eps = rec["eps"] * 4
                rec["approx_pe"] = round(current_price / annualised_eps, 2) if annualised_eps else None
            else:
                rec["approx_pe"] = None

            records.append(rec)

        return {
            "symbol": qualified,
            "currency": currency,
            "records": records,
            "count": len(records),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_df(obj) -> pd.DataFrame | None:
        try:
            if obj is None or (isinstance(obj, pd.DataFrame) and obj.empty):
                return None
            return obj if isinstance(obj, pd.DataFrame) else None
        except Exception:
            return None

    @staticmethod
    def _get_val(
        df: pd.DataFrame | None,
        col,
        row_keys: list[str],
    ) -> float | None:
        """Extract a value from a transposed yfinance financial DataFrame."""
        if df is None or col not in df.columns:
            return None
        for key in row_keys:
            if key in df.index:
                val = df.loc[key, col]
                if pd.notna(val):
                    try:
                        return round(float(val), 4)
                    except (TypeError, ValueError):
                        continue
        return None
