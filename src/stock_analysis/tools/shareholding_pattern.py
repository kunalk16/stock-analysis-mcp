# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Tool: get_shareholding_pattern
Returns quarterly shareholding pattern (promoter, FII, DII, public, etc.).
"""

from __future__ import annotations

import pandas as pd

from stock_analysis.utils.yfinance_client import YFinanceClient


class ShareholdingPatternTool:
    """
    Retrieves shareholding / ownership distribution data for a stock using:
    - ``ticker.major_holders``         – high-level % breakdown.
    - ``ticker.institutional_holders`` – top institutional holders with dates.
    - ``ticker.mutualfund_holders``    – top mutual fund holders with dates.

    Note:
        yfinance does not expose a structured quarterly promoter/FII/DII
        series identical to what BSE/NSE publish.  The data returned
        reflects the latest available snapshot from Yahoo Finance, which
        Yahoo refreshes approximately quarterly.
    """

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        country_code: str | None = None,
    ) -> dict:
        """
        Fetch shareholding pattern data.

        Args:
            symbol:       Ticker symbol (e.g. "TCS", "INFY").
            country_code: ISO 3166-1 alpha-2 country code. Defaults to "IN".

        Returns:
            Dictionary with:
            - ``symbol``
            - ``major_holders``:         List of {value, description} rows.
            - ``institutional_holders``: List of top institutional holders.
            - ``mutualfund_holders``:    List of top mutual fund holders.
        """
        ticker = self._client.get_ticker(symbol, country_code)
        qualified = self._client.resolve_symbol(symbol, country_code)

        result: dict = {"symbol": qualified}

        # --- Major holders ---
        try:
            mh: pd.DataFrame = ticker.major_holders
            if mh is not None and not mh.empty:
                mh = mh.reset_index(drop=True)
                # Yahoo Finance returns two columns: value and description
                cols = list(mh.columns)
                result["major_holders"] = [
                    {
                        "value": str(row.iloc[0]),
                        "description": str(row.iloc[1]) if len(cols) > 1 else "",
                    }
                    for _, row in mh.iterrows()
                ]
            else:
                result["major_holders"] = []
        except Exception as exc:
            result["major_holders"] = []
            result["major_holders_error"] = str(exc)

        # --- Institutional holders ---
        try:
            ih: pd.DataFrame = ticker.institutional_holders
            if ih is not None and not ih.empty:
                result["institutional_holders"] = _df_to_records(ih)
            else:
                result["institutional_holders"] = []
        except Exception as exc:
            result["institutional_holders"] = []
            result["institutional_holders_error"] = str(exc)

        # --- Mutual fund holders ---
        try:
            mfh: pd.DataFrame = ticker.mutualfund_holders
            if mfh is not None and not mfh.empty:
                result["mutualfund_holders"] = _df_to_records(mfh)
            else:
                result["mutualfund_holders"] = []
        except Exception as exc:
            result["mutualfund_holders"] = []
            result["mutualfund_holders_error"] = str(exc)

        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to a list of JSON-serialisable dicts."""
    records = []
    for _, row in df.iterrows():
        rec = {}
        for col, val in row.items():
            if pd.isna(val) if not isinstance(val, (list, dict)) else False:
                rec[str(col)] = None
            elif hasattr(val, "isoformat"):
                rec[str(col)] = val.isoformat()
            elif hasattr(val, "item"):  # numpy scalar
                rec[str(col)] = val.item()
            else:
                rec[str(col)] = val
        records.append(rec)
    return records
