# Copyright (c) 2026 Kunal Karmakar
# SPDX-License-Identifier: MIT

"""
Stock Analysis MCP Server
=========================
Exposes 11 MCP tools (+ 1 utility tool) for financial data retrieval
powered by yfinance.

Default market: India (NSE). Pass ``country_code`` to any tool to target
a different exchange (see CountryExchangeMap for supported codes).

Run with:
    python -m stock_analysis.server          # stdio (default)
    mcp run src/stock_analysis/server.py     # via mcp CLI
"""
from __future__ import annotations

import json
import os
import traceback
from typing import Any

from mcp.server.fastmcp import FastMCP

from stock_analysis.utils.yfinance_client import YFinanceClient
from stock_analysis.utils.country_exchange import CountryExchangeMap
from stock_analysis.tools.price_history import PriceHistoryTool
from stock_analysis.tools.valuation_history import ValuationHistoryTool
from stock_analysis.tools.ticker_lookup import TickerLookupTool
from stock_analysis.tools.peer_companies import PeerCompaniesTool
from stock_analysis.tools.shareholding_pattern import ShareholdingPatternTool
from stock_analysis.tools.dividend_history import DividendHistoryTool
from stock_analysis.tools.quarterly_results import QuarterlyResultsTool
from stock_analysis.tools.dma import DMATool
from stock_analysis.tools.ema import EMATool
from stock_analysis.tools.support_resistance import SupportResistanceTool


# ---------------------------------------------------------------------------
# Server bootstrap
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="stock-analysis",
    instructions=(
        "A financial data server powered by yfinance. "
        "Default market is India (NSE). Supply country_code (e.g. 'US', 'GB', 'JP') "
        "to any tool to query a different exchange. "
        "Pass country_code='ALL' in ticker/peer lookups to search across all markets."
    ),
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8000")),
)

_client = YFinanceClient()

# Instantiate all tool objects once (shared _client for caching)
_price_history = PriceHistoryTool(_client)
_valuation_history = ValuationHistoryTool(_client)
_ticker_lookup = TickerLookupTool(_client)
_peer_companies = PeerCompaniesTool(_client)
_shareholding_pattern = ShareholdingPatternTool(_client)
_dividend_history = DividendHistoryTool(_client)
_quarterly_results = QuarterlyResultsTool(_client)
_dma = DMATool(_client)
_ema = EMATool(_client)
_support_resistance = SupportResistanceTool(_client)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _safe_run(fn, *args, **kwargs) -> str:
    """Run a tool function and serialise the result to JSON, catching all errors."""
    try:
        result: Any = fn(*args, **kwargs)
        return json.dumps(result, default=str, ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001
        return json.dumps(
            {"error": str(exc), "traceback": traceback.format_exc()},
            ensure_ascii=False,
            indent=2,
        )


# ---------------------------------------------------------------------------
# Tool 0 – Utility: list supported countries
# ---------------------------------------------------------------------------

@mcp.tool()
def list_supported_countries() -> str:
    """
    List all supported country codes, their exchange names, and ticker suffixes.

    Use the returned ``code`` values as the ``country_code`` argument in other tools.
    The default country is **India (IN / NSE)**.

    Returns:
        JSON array of {code, name, suffix} objects.
    """
    return json.dumps(CountryExchangeMap.list_supported_countries(), indent=2)


# ---------------------------------------------------------------------------
# Tool 1 – Price History
# ---------------------------------------------------------------------------

@mcp.tool()
def get_price_history(
    symbol: str,
    country_code: str = "IN",
    period: str = "1y",
    interval: str = "1d",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    Fetch historical OHLCV (Open, High, Low, Close, Volume) data for a stock.

    Args:
        symbol:       Ticker symbol. For Indian stocks use the base symbol
                      (e.g. "RELIANCE", "TCS"). For US use "AAPL", "MSFT".
        country_code: Exchange country. Default "IN" (India NSE).
                      Use "US" for NYSE/NASDAQ, "GB" for LSE, etc.
                      Ignored if symbol already contains a dot-suffix.
        period:       Look-back period when start_date is empty.
                      Values: "1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max".
                      Default "1y".
        interval:     Data granularity. Values: "1d","1wk","1mo","1h","15m","5m".
                      Default "1d".
        start_date:   Start date "YYYY-MM-DD". Overrides period when provided.
        end_date:     End date "YYYY-MM-DD". Used with start_date.

    Returns:
        JSON with symbol, currency, list of OHLCV records, and record count.
    """
    return _safe_run(
        _price_history.run,
        symbol=symbol,
        country_code=country_code or None,
        period=period,
        interval=interval,
        start_date=start_date or None,
        end_date=end_date or None,
    )


# ---------------------------------------------------------------------------
# Tool 2 – Valuation History
# ---------------------------------------------------------------------------

@mcp.tool()
def get_valuation_history(
    symbol: str,
    country_code: str = "IN",
    period: str = "1y",
) -> str:
    """
    Retrieve historical valuation metrics: P/E ratio, P/B ratio,
    and approximate market capitalisation over time.

    Note: EPS and book value are point-in-time from yfinance (TTM).
    The P/E and P/B series vary the price while holding fundamentals constant.

    Args:
        symbol:       Ticker symbol (e.g. "HDFCBANK", "MSFT").
        country_code: Exchange country. Default "IN".
        period:       Look-back period. Default "1y".

    Returns:
        JSON with ttm_eps, book_value_per_share, and daily records.
    """
    return _safe_run(
        _valuation_history.run,
        symbol=symbol,
        country_code=country_code or None,
        period=period,
    )


# ---------------------------------------------------------------------------
# Tool 3 – Company Name → Ticker
# ---------------------------------------------------------------------------

@mcp.tool()
def get_ticker_for_company(
    company_name: str,
    country_code: str = "IN",
    max_results: int = 10,
) -> str:
    """
    Convert a company name (or partial name) to its stock ticker symbol(s).

    Args:
        company_name: Full or partial company name (e.g. "Reliance Industries",
                      "Apple", "HDFC Bank").
        country_code: Filter results to this country's exchange. Default "IN".
                      Pass "ALL" to return matches from all markets.
        max_results:  Maximum number of matches to return. Default 10.

    Returns:
        JSON with list of matches (symbol, name, exchange, type, score).
    """
    return _safe_run(
        _ticker_lookup.run,
        company_name=company_name,
        country_code=country_code or None,
        max_results=max_results,
    )


# ---------------------------------------------------------------------------
# Tool 4 – Peer Companies
# ---------------------------------------------------------------------------

@mcp.tool()
def get_peer_companies(
    symbol: str,
    country_code: str = "IN",
    max_peers: int = 15,
) -> str:
    """
    Find peer / competitor companies in the same industry as the given stock.

    Uses the stock's industry and sector metadata to search for similar
    companies on the same exchange.

    Args:
        symbol:       Ticker symbol (e.g. "INFY", "GOOGL").
        country_code: Exchange country. Default "IN".
                      Peers are filtered to the same exchange by default.
        max_peers:    Maximum number of peers to return. Default 15.

    Returns:
        JSON with company name, industry, sector, and list of peers
        (symbol, name, exchange, industry, market_cap).
    """
    return _safe_run(
        _peer_companies.run,
        symbol=symbol,
        country_code=country_code or None,
        max_peers=max_peers,
    )


# ---------------------------------------------------------------------------
# Tool 5 – Shareholding Pattern
# ---------------------------------------------------------------------------

@mcp.tool()
def get_shareholding_pattern(
    symbol: str,
    country_code: str = "IN",
) -> str:
    """
    Retrieve the shareholding / ownership pattern of a stock.

    Returns major holder percentages (promoter, institutions, float) and
    top institutional / mutual fund holders with their position sizes and
    latest filing dates.

    Args:
        symbol:       Ticker symbol (e.g. "TCS", "AAPL").
        country_code: Exchange country. Default "IN".

    Returns:
        JSON with major_holders, institutional_holders, mutualfund_holders.
    """
    return _safe_run(
        _shareholding_pattern.run,
        symbol=symbol,
        country_code=country_code or None,
    )


# ---------------------------------------------------------------------------
# Tool 6 – Dividend History
# ---------------------------------------------------------------------------

@mcp.tool()
def get_dividend_history(
    symbol: str,
    country_code: str = "IN",
    period: str = "5y",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    Retrieve historical dividend payouts for a stock.

    Args:
        symbol:       Ticker symbol (e.g. "COALINDIA", "JNJ").
        country_code: Exchange country. Default "IN".
        period:       Look-back period when start_date is empty. Default "5y".
        start_date:   Start date "YYYY-MM-DD". Overrides period.
        end_date:     End date "YYYY-MM-DD".

    Returns:
        JSON with list of dividends (date, amount), count, and total paid.
    """
    return _safe_run(
        _dividend_history.run,
        symbol=symbol,
        country_code=country_code or None,
        period=period,
        start_date=start_date or None,
        end_date=end_date or None,
    )


# ---------------------------------------------------------------------------
# Tool 7 – Quarterly Results
# ---------------------------------------------------------------------------

@mcp.tool()
def get_quarterly_results(
    symbol: str,
    country_code: str = "IN",
    num_quarters: int = 8,
) -> str:
    """
    Retrieve quarterly financial results for a stock.

    Includes revenue, gross profit, EBITDA, net income, EPS, total debt,
    total equity, and an approximate trailing P/E ratio per quarter.

    Args:
        symbol:        Ticker symbol (e.g. "HDFCBANK", "AMZN").
        country_code:  Exchange country. Default "IN".
        num_quarters:  Number of recent quarters to return. Default 8.

    Returns:
        JSON with list of quarterly records (latest first).
    """
    return _safe_run(
        _quarterly_results.run,
        symbol=symbol,
        country_code=country_code or None,
        num_quarters=num_quarters,
    )


# ---------------------------------------------------------------------------
# Tool 8 – DMA (Simple Moving Average)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_dma(
    symbol: str,
    days: int,
    country_code: str = "IN",
    data_period: str = "2y",
    return_series: bool = True,
) -> str:
    """
    Compute the N-day Simple Moving Average (DMA) for a stock.

    Commonly used as 50-DMA, 200-DMA in Indian market analysis.

    Args:
        symbol:        Ticker symbol (e.g. "NIFTY50.NS", "TATAMOTORS", "AAPL").
        days:          DMA window in days (e.g. 20, 50, 100, 200).
        country_code:  Exchange country. Default "IN".
        data_period:   History period for computation. Default "2y".
                       Use "5y" for very long windows like 200-DMA.
        return_series: Return the full daily series. Default True.

    Returns:
        JSON with current_dma, current_price, price_vs_dma ("above"/"below"/"at"),
        and optionally the full series of {date, close, dma}.
    """
    return _safe_run(
        _dma.run,
        symbol=symbol,
        days=days,
        country_code=country_code or None,
        data_period=data_period,
        return_series=return_series,
    )


# ---------------------------------------------------------------------------
# Tool 9 – EMA (Exponential Moving Average)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_ema(
    symbol: str,
    days: int,
    country_code: str = "IN",
    data_period: str = "2y",
    return_series: bool = True,
) -> str:
    """
    Compute the N-day Exponential Moving Average (EMA) for a stock.

    EMA gives more weight to recent prices than a simple moving average.
    Common spans: 9, 21, 50, 200.

    Args:
        symbol:        Ticker symbol (e.g. "WIPRO", "TSLA").
        days:          EMA span in days (e.g. 9, 21, 50, 200).
        country_code:  Exchange country. Default "IN".
        data_period:   History period for computation. Default "2y".
        return_series: Return the full daily series. Default True.

    Returns:
        JSON with current_ema, current_price, price_vs_ema ("above"/"below"/"at"),
        and optionally the full series of {date, close, ema}.
    """
    return _safe_run(
        _ema.run,
        symbol=symbol,
        days=days,
        country_code=country_code or None,
        data_period=data_period,
        return_series=return_series,
    )


# ---------------------------------------------------------------------------
# Tool 10 – Support & Resistance
# ---------------------------------------------------------------------------

@mcp.tool()
def get_support_resistance(
    symbol: str,
    country_code: str = "IN",
    lookback_period: str = "6mo",
    order: int = 5,
) -> str:
    """
    Identify current support and resistance price levels for a stock.

    Uses swing-high/swing-low detection (scipy argrelextrema) plus
    classic pivot points (P, R1-R3, S1-S3) from the last completed candle.
    Nearby levels are clustered to remove noise.

    Args:
        symbol:          Ticker symbol (e.g. "TATASTEEL", "NVDA").
        country_code:    Exchange country. Default "IN".
        lookback_period: History period for swing detection. Default "6mo".
                         Longer periods give more established levels.
        order:           Sensitivity of swing detection (bars each side).
                         Higher = fewer, stronger levels. Default 5.

    Returns:
        JSON with current_price, pivot_points (P/R1-R3/S1-S3),
        resistance_levels, support_levels (each with price and touch_count),
        nearest_resistance, and nearest_support.
    """
    return _safe_run(
        _support_resistance.run,
        symbol=symbol,
        country_code=country_code or None,
        lookback_period=lookback_period,
        order=order,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server.

    Transport is controlled by the MCP_TRANSPORT environment variable:
      MCP_TRANSPORT  - 'stdio' (default) or 'sse'

    For SSE transport, bind address and port are configured via:
      MCP_HOST  (default: 127.0.0.1 / 0.0.0.0 inside Docker)
      MCP_PORT  (default: 8000)
    These are read at import time and passed to the FastMCP constructor above.
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
