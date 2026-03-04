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

## Running with Docker

The Docker image uses a multi-stage build (`python:3.10-slim`) and starts the server in **SSE mode**, making it accessible over HTTP from your host machine.

### 1. Build the image

```bash
docker build -t stock-analysis-mcp .
```

### 2. Run the container

```bash
docker run -p 8000:8000 stock-analysis-mcp
```

The MCP server is now reachable at **`http://localhost:8000/sse`**.

> The container defaults to `MCP_TRANSPORT=sse`, `MCP_HOST=0.0.0.0`, and `MCP_PORT=8000`. Override any of these via `-e` if needed:
>
> ```bash
> docker run -p 9000:9000 -e MCP_PORT=9000 stock-analysis-mcp
> ```

---

## Connecting to an MCP Client

### VS Code (GitHub Copilot) — Docker / SSE

> Make sure the container is running (`docker run -p 8000:8000 stock-analysis-mcp`) before following these steps.

1. Open the **Command Palette** (`Ctrl+Shift+P`).
2. Run **`MCP: Add Server`**.
3. Select **`HTTP (SSE)`** as the server type.
4. Enter the URL: `http://localhost:8000/sse`
5. When prompted for a name, enter `stock-analysis`.
6. Choose whether to save it to **User settings** (available in all workspaces) or **Workspace settings** (current project only).
7. Open **Copilot Chat** (`Ctrl+Alt+I`), switch to **Agent mode**, and click the **Tools** button (🔧) to verify the stock analysis tools appear.

> If the tools don't appear, open the Command Palette and run **`MCP: Start Server`** → select `stock-analysis`.

### Claude Desktop — Docker / SSE

Add the following to your `claude_desktop_config.json`:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "stock-analysis": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

Restart Claude Desktop after saving. The server will appear in the tools list.

---

## Connecting to an MCP Client (local / stdio)

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

### VS Code (GitHub Copilot) — local

1. Open the **Command Palette** (`Ctrl+Shift+P`).
2. Run **`MCP: Add Server`**.
3. Select **`Command (stdio)`** as the server type.
4. Enter the command: full path to `.venv\Scripts\python.exe` (Windows) or `.venv/bin/python` (macOS/Linux).
5. When prompted for arguments, enter `-m stock_analysis.server`.
6. Give the server a name, e.g. `stock-analysis`.

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
├── pyproject.toml          # Package metadata and dependencies
├── requirements.txt        # Dev requirements
├── Dockerfile              # Multi-stage Docker build (SSE transport)
├── src/
│   └── stock_analysis/
│       ├── server.py       # MCP server entry point
│       ├── utils/          # Shared helpers (yfinance client, country/exchange map)
│       └── tools/          # One module per MCP tool
└── tests/
    ├── conftest.py         # Shared fixtures and mock factories
    ├── utils/              # Tests for utility modules
    └── tools/              # Tests for each tool module
```

---

## Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=stock_analysis --cov-report=term-missing

# Run a specific test file
pytest tests/tools/test_dma.py -v
```

All tests are fully offline — no real network calls are made to yfinance during test execution. A `pytest` autouse fixture blocks any accidental outbound calls at the yfinance layer.

---

## Architecture

- **`YFinanceClient`** is the single point of contact with yfinance. All tool classes receive it via constructor injection, enabling easy mocking in tests.
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
