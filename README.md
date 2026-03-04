# Stock Analysis MCP Server

A Python-based [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes financial analysis tools powered by [yfinance](https://github.com/ranaroussi/yfinance). Connect it to any MCP-compatible client (Claude Desktop, Cursor, VS Code Copilot, etc.) to query stock data across 35+ country markets directly from your AI assistant.

**Default market: India (NSE).** All tools accept a `country_code` parameter to target a different exchange.

---

## Features

| Tool | Description |
|------|-------------|
| `list_supported_countries` | List all 35+ supported country codes and their exchange suffixes |
| `get_price_history` | OHLCV historical data with configurable period and interval |
| `get_valuation_history` | Historical P/E, P/B, and market cap series |
| `get_ticker_for_company` | Resolve a company name to its ticker symbol(s) |
| `get_peer_companies` | Find competitor companies in the same industry |
| `get_shareholding_pattern` | Promoter / institutional / mutual fund ownership breakdown |
| `get_dividend_history` | Historical dividend payouts with totals |
| `get_quarterly_results` | Revenue, EBITDA, net income, EPS, debt, equity per quarter |
| `get_dma` | N-day Simple Moving Average (50-DMA, 200-DMA, etc.) |
| `get_ema` | N-day Exponential Moving Average (9, 21, 50, 200, etc.) |
| `get_support_resistance` | Swing-based support/resistance levels + classic pivot points |

---

## Requirements

- Python 3.10 or higher
- An MCP-compatible client (Claude Desktop, Cursor, VS Code with Copilot, etc.)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/kunalk16/stock-analysis-mcp.git
cd stock-analysis-mcp
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install the package

```bash
pip install -e .
```

This installs the server and all dependencies (`mcp`, `yfinance`, `pandas`, `numpy`, `scipy`).

> **Optional (dev/test dependencies):**
>
> ```bash
> pip install -e ".[dev]"
> ```

---

## Running the Server

The server communicates over **stdio**, which is the standard transport for MCP clients.

```bash
# Using the installed script
stock-analysis-mcp

# Or directly via Python
python -m stock_analysis.server

# Or via the mcp CLI
mcp run src/stock_analysis/server.py
```

---

## Connecting to an MCP Client

### Claude Desktop

Add the following to your `claude_desktop_config.json` (usually at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "stock_analysis.server"]
    }
  }
}
```

> On Windows, use the full path to `.venv\Scripts\python.exe`.

### Cursor

Open **Settings → MCP → Add Server** and enter:

```json
{
  "name": "stock-analysis",
  "command": "python",
  "args": ["-m", "stock_analysis.server"],
  "cwd": "/absolute/path/to/stock-analysis-mcp",
  "env": {
    "VIRTUAL_ENV": "/absolute/path/to/stock-analysis-mcp/.venv"
  }
}
```

---

## Usage Examples

Once connected, you can ask your AI assistant natural language questions like:

```
What is the current 200-DMA for Reliance Industries?
Show me the shareholding pattern for TCS.
What were HDFC Bank's quarterly results for the last 4 quarters?
Find the ticker symbol for Infosys.
What are the support and resistance levels for Tata Motors?
Show me the price history for Apple (US) for the last 6 months.
What is the 50-EMA for NVIDIA?
```

### Country Codes

Pass a `country_code` to any tool to query a different market:

| Code | Exchange |
|------|----------|
| `IN` | India – NSE (default) |
| `IN_BSE` | India – BSE |
| `US` | United States (NYSE / NASDAQ) |
| `GB` | United Kingdom – LSE |
| `DE` | Germany – XETRA |
| `JP` | Japan – Tokyo SE |
| `CN` | China – Shanghai SE |
| `AU` | Australia – ASX |
| `CA` | Canada – TSX |
| ... | Use `list_supported_countries` for the full list |

---

## Project Structure

```
stock-analysis-mcp/
├── pyproject.toml                  # Package metadata and dependencies
├── requirements.txt                # Pinned dev requirements
├── .gitignore
├── src/
│   └── stock_analysis/
│       ├── server.py               # MCP server entry point (11 tools registered)
│       ├── utils/
│       │   ├── country_exchange.py # CountryExchangeMap – 35+ country → suffix mappings
│       │   └── yfinance_client.py  # YFinanceClient – caching wrapper around yfinance
│       └── tools/
│           ├── price_history.py
│           ├── valuation_history.py
│           ├── ticker_lookup.py
│           ├── peer_companies.py
│           ├── shareholding_pattern.py
│           ├── dividend_history.py
│           ├── quarterly_results.py
│           ├── dma.py
│           ├── ema.py
│           └── support_resistance.py
└── tests/
    ├── conftest.py                 # Shared fixtures and mock factories
    ├── utils/
    │   ├── test_country_exchange.py
    │   └── test_yfinance_client.py
    └── tools/
        ├── test_price_history.py
        ├── test_valuation_history.py
        ├── test_ticker_lookup.py
        ├── test_peer_companies.py
        ├── test_shareholding_pattern.py
        ├── test_dividend_history.py
        ├── test_quarterly_results.py
        ├── test_dma.py
        ├── test_ema.py
        └── test_support_resistance.py
```

---

## Running Tests

```bash
# Run all 130 tests
pytest

# With coverage report
pytest --cov=stock_analysis --cov-report=term-missing

# Run a specific test file
pytest tests/tools/test_dma.py -v
```

All tests are fully offline — no real network calls are made to yfinance during test execution. A `pytest` autouse fixture blocks any accidental outbound calls at the yfinance layer.

---

## Architecture

- **`YFinanceClient`** is the single point of contact with yfinance. All 10 tool classes receive it via constructor injection, enabling easy mocking in tests.
- **`CountryExchangeMap`** translates ISO country codes to yfinance ticker suffixes (e.g. `RELIANCE` + `IN` → `RELIANCE.NS`). If a symbol already contains a `.`, it is passed through unchanged.
- **`FastMCP`** (from the `mcp` SDK) handles the protocol layer. Tools are registered as plain Python functions with type-annotated parameters.
- All tool output is serialised to JSON strings for transport.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `mcp[cli]>=1.4.0` | MCP SDK (FastMCP server, stdio transport) |
| `yfinance>=0.2.50` | Market data source |
| `pandas>=2.0.0` | DataFrame manipulation |
| `numpy>=1.26.0` | Numerical operations |
| `scipy>=1.11.0` | Swing high/low detection (`argrelextrema`) for support/resistance |

---

## License

MIT
