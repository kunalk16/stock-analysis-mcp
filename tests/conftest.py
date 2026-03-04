"""
Shared pytest fixtures for stock-analysis-mcp unit tests.

All fixtures are deterministic (fixed seed) and never touch the network.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from stock_analysis.utils.yfinance_client import YFinanceClient


# ---------------------------------------------------------------------------
# Global safety net: block all real yfinance network calls
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _block_real_yfinance_calls():
    """
    Autouse fixture applied to EVERY test.

    Patches ``yf.Ticker`` and ``yf.Search`` at the source module level so
    that any accidental un-mocked call to yfinance raises ``RuntimeError``
    immediately rather than silently hitting the network.

    Tests in ``test_yfinance_client.py`` override these patches with their
    own inner ``with patch(...)`` context managers, which take precedence
    (patches are a LIFO stack).
    """
    _msg_ticker = (
        "Real yf.Ticker() call detected – wrap this test in "
        "patch('stock_analysis.utils.yfinance_client.yf.Ticker')."
    )
    _msg_search = (
        "Real yf.Search() call detected – wrap this test in "
        "patch('stock_analysis.utils.yfinance_client.yf.Search')."
    )
    with (
        patch(
            "stock_analysis.utils.yfinance_client.yf.Ticker",
            side_effect=RuntimeError(_msg_ticker),
        ),
        patch(
            "stock_analysis.utils.yfinance_client.yf.Search",
            side_effect=RuntimeError(_msg_search),
        ),
    ):
        yield


# ---------------------------------------------------------------------------
# Seeded RNG
# ---------------------------------------------------------------------------
RNG = np.random.default_rng(42)


# ---------------------------------------------------------------------------
# DataFrame factories
# ---------------------------------------------------------------------------

def make_ohlcv(
    n: int = 60,
    start: str = "2024-01-01",
    base_price: float = 2_500.0,
    freq: str = "D",
) -> pd.DataFrame:
    """Return an OHLCV DataFrame with a UTC DatetimeIndex, mimicking yfinance output."""
    idx = pd.date_range(start, periods=n, freq=freq, tz="UTC")
    closes = base_price + np.cumsum(RNG.normal(0, 20, n))
    opens = closes - RNG.uniform(0, 15, n)
    highs = closes + RNG.uniform(0, 20, n)
    lows = opens - RNG.uniform(0, 10, n)
    volumes = RNG.integers(1_000_000, 5_000_000, n)
    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": volumes.astype(float),
        },
        index=idx,
    )


def make_dividends(
    n: int = 6,
    start: str = "2022-01-01",
    amount: float = 15.0,
) -> pd.Series:
    """Return a dividend Series (quarterly payments) with a UTC DatetimeIndex."""
    idx = pd.date_range(start, periods=n, freq="QE", tz="UTC")
    amounts = np.ones(n) * amount
    return pd.Series(amounts, index=idx, name="Dividends")


def make_major_holders() -> pd.DataFrame:
    """Minimal major holders DataFrame matching Yahoo Finance shape."""
    return pd.DataFrame(
        [
            ["55.23%", "% of Shares Held by All Insider"],
            ["23.10%", "% of Shares Held by Institutions"],
            ["21.67%", "% Float Held by Institutions"],
        ]
    )


def make_institutional_holders() -> pd.DataFrame:
    """Minimal institutional holders DataFrame."""
    dates = pd.date_range("2024-01-01", periods=3, freq="QE", tz="UTC")
    return pd.DataFrame(
        {
            "Holder": ["BlackRock Inc.", "Vanguard Group", "StateStreet"],
            "Shares": [10_000_000, 8_500_000, 5_200_000],
            "Date Reported": dates,
            "% Out": [2.5, 2.1, 1.3],
            "Value": [250_000_000, 212_000_000, 130_000_000],
        }
    )


def make_quarterly_income() -> pd.DataFrame:
    """
    Quarterly income statement in yfinance transposed format:
    rows = line items, columns = quarter-end Timestamps.
    """
    quarters = pd.to_datetime(
        ["2024-03-31", "2023-12-31", "2023-09-30", "2023-06-30"]
    )
    return pd.DataFrame(
        {
            quarters[0]: {
                "Total Revenue": 2_500_000_000.0,
                "Gross Profit": 900_000_000.0,
                "Operating Income": 600_000_000.0,
                "EBITDA": 700_000_000.0,
                "Net Income": 450_000_000.0,
                "Basic EPS": 18.5,
            },
            quarters[1]: {
                "Total Revenue": 2_300_000_000.0,
                "Gross Profit": 850_000_000.0,
                "Operating Income": 560_000_000.0,
                "EBITDA": 660_000_000.0,
                "Net Income": 420_000_000.0,
                "Basic EPS": 17.2,
            },
            quarters[2]: {
                "Total Revenue": 2_100_000_000.0,
                "Gross Profit": 780_000_000.0,
                "Operating Income": 510_000_000.0,
                "EBITDA": 610_000_000.0,
                "Net Income": 390_000_000.0,
                "Basic EPS": 16.0,
            },
            quarters[3]: {
                "Total Revenue": 2_000_000_000.0,
                "Gross Profit": 740_000_000.0,
                "Operating Income": 480_000_000.0,
                "EBITDA": 580_000_000.0,
                "Net Income": 370_000_000.0,
                "Basic EPS": 15.2,
            },
        }
    )


def make_quarterly_balance() -> pd.DataFrame:
    """Quarterly balance sheet in yfinance transposed format."""
    quarters = pd.to_datetime(
        ["2024-03-31", "2023-12-31", "2023-09-30", "2023-06-30"]
    )
    return pd.DataFrame(
        {
            quarters[0]: {
                "Total Assets": 10_000_000_000.0,
                "Total Debt": 2_000_000_000.0,
                "Common Stock Equity": 5_000_000_000.0,
            },
            quarters[1]: {
                "Total Assets": 9_800_000_000.0,
                "Total Debt": 2_100_000_000.0,
                "Common Stock Equity": 4_900_000_000.0,
            },
            quarters[2]: {
                "Total Assets": 9_600_000_000.0,
                "Total Debt": 2_200_000_000.0,
                "Common Stock Equity": 4_700_000_000.0,
            },
            quarters[3]: {
                "Total Assets": 9_400_000_000.0,
                "Total Debt": 2_300_000_000.0,
                "Common Stock Equity": 4_600_000_000.0,
            },
        }
    )


# ---------------------------------------------------------------------------
# Info dict factory
# ---------------------------------------------------------------------------

def make_info(
    symbol: str = "RELIANCE.NS",
    currency: str = "INR",
    current_price: float = 2_500.0,
    trailing_eps: float = 90.0,
    book_value: float = 1_200.0,
    market_cap: float = 1_690_000_000_000.0,
    industry: str = "Oil & Gas Refining & Marketing",
    sector: str = "Energy",
    exchange: str = "NSI",
) -> dict:
    return {
        "symbol": symbol,
        "currency": currency,
        "currentPrice": current_price,
        "regularMarketPrice": current_price,
        "trailingEps": trailing_eps,
        "epsTrailingTwelveMonths": trailing_eps,
        "bookValue": book_value,
        "marketCap": market_cap,
        "sharesOutstanding": int(market_cap / current_price),
        "industry": industry,
        "sector": sector,
        "exchange": exchange,
        "longName": "Reliance Industries Limited",
        "shortName": "RELIANCE.NS",
    }


# ---------------------------------------------------------------------------
# Mock YFinanceClient factory
# ---------------------------------------------------------------------------

def make_mock_client(
    ohlcv: pd.DataFrame | None = None,
    info: dict | None = None,
    dividends: pd.Series | None = None,
    major_holders: pd.DataFrame | None = None,
    institutional_holders: pd.DataFrame | None = None,
    mutualfund_holders: pd.DataFrame | None = None,
    quarterly_income: pd.DataFrame | None = None,
    quarterly_balance: pd.DataFrame | None = None,
    search_results: list[dict] | None = None,
    qualified_symbol: str = "RELIANCE.NS",
) -> MagicMock:
    """
    Build a MagicMock that stands in for YFinanceClient.

    ``get_ticker()`` returns a mock ``yf.Ticker``-like object whose
    attributes are populated from the provided DataFrames / dicts.
    ``resolve_symbol()`` returns *qualified_symbol*.
    ``search()`` returns *search_results*.
    """
    _ohlcv = ohlcv if ohlcv is not None else make_ohlcv()
    _info = info if info is not None else make_info()
    _dividends = dividends if dividends is not None else make_dividends()
    _major_holders = major_holders if major_holders is not None else make_major_holders()
    _inst_holders = institutional_holders if institutional_holders is not None else make_institutional_holders()
    _mf_holders = mutualfund_holders if mutualfund_holders is not None else pd.DataFrame()
    _q_income = quarterly_income if quarterly_income is not None else make_quarterly_income()
    _q_balance = quarterly_balance if quarterly_balance is not None else make_quarterly_balance()
    _search = search_results if search_results is not None else []

    mock_ticker = MagicMock()
    mock_ticker.history.return_value = _ohlcv
    mock_ticker.info = _info
    mock_ticker.dividends = _dividends
    mock_ticker.major_holders = _major_holders
    mock_ticker.institutional_holders = _inst_holders
    mock_ticker.mutualfund_holders = _mf_holders
    mock_ticker.quarterly_income_stmt = _q_income
    mock_ticker.quarterly_balance_sheet = _q_balance
    mock_ticker.quarterly_earnings = None  # not always available

    client = MagicMock(spec=YFinanceClient)
    client.get_ticker.return_value = mock_ticker
    client.resolve_symbol.return_value = qualified_symbol
    client.search.return_value = _search

    return client


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ohlcv_df():
    """60-row OHLCV DataFrame."""
    return make_ohlcv()


@pytest.fixture
def mock_client():
    """Default mock YFinanceClient for RELIANCE.NS."""
    return make_mock_client()


@pytest.fixture
def empty_ohlcv():
    """Empty OHLCV DataFrame."""
    return pd.DataFrame(
        columns=["Open", "High", "Low", "Close", "Volume"],
        index=pd.DatetimeIndex([], tz="UTC"),
    )


@pytest.fixture
def mock_client_empty(empty_ohlcv):
    """Mock client whose ticker returns empty history."""
    return make_mock_client(
        ohlcv=empty_ohlcv,
        dividends=pd.Series(dtype=float),
        major_holders=pd.DataFrame(),
        institutional_holders=pd.DataFrame(),
        quarterly_income=pd.DataFrame(),
        quarterly_balance=pd.DataFrame(),
    )
