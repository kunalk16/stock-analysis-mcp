# Copilot Instructions for stock-analysis-mcp

## Project Overview

This is a Python MCP (Model Context Protocol) server that exposes financial analysis tools powered by yfinance. It supports 35+ country markets (default: India/NSE) and communicates over stdio or SSE transport.

**Stack:** Python 3.10+, FastMCP, yfinance, pandas, numpy, scipy

## Architecture

- **`src/stock_analysis/server.py`** — MCP server entry point. Creates a single shared `YFinanceClient`, instantiates all tool classes with it, and registers MCP tools via `@mcp.tool()` decorators. All tool calls are wrapped in `_safe_run()` which serialises results to JSON and catches exceptions.
- **`src/stock_analysis/tools/`** — One module per MCP tool (10 tool classes). Each follows the same pattern.
- **`src/stock_analysis/utils/`** — Shared helpers: `YFinanceClient` (yfinance wrapper with caching) and `CountryExchangeMap` (country code → ticker suffix mapping).
- **`tests/`** — Mirrors the `src/` structure. All tests are fully offline.

## Coding Conventions

### General

- **Python version:** 3.10+ — use modern syntax (`str | None`, `list[dict]`, not `Optional[str]`, `List[Dict]`).
- **Future annotations:** Every source file starts with `from __future__ import annotations`.
- **Formatting:** Black (default settings, ~88 char line length) + isort (`--profile black`). Both are enforced in CI.
- **Quotes:** Double quotes for strings (Black default).
- **Indentation:** 4 spaces.

### Imports

- Always use **absolute imports** (`from stock_analysis.tools.dma import DMATool`), never relative.
- Group in PEP 8 order: `__future__` → stdlib → third-party → local, separated by blank lines.
- Minimal use of `typing` — prefer built-in generics (`dict`, `list`) and `|` union syntax.

### Naming

- **Modules:** `snake_case` (e.g., `price_history.py`, `yfinance_client.py`).
- **Classes:** `PascalCase` (e.g., `PriceHistoryTool`, `YFinanceClient`).
- **Functions/methods:** `snake_case` (e.g., `get_price_history`, `_cluster_levels`).
- **Constants:** `SCREAMING_SNAKE_CASE` (e.g., `DEFAULT_COUNTRY`, `_CLUSTER_TOLERANCE`).
- **Private members:** Leading underscore (`self._client`, `_safe_run()`).

### Docstrings

- **Style:** Google-style with `Args:` and `Returns:` sections.
- Every module has a top-level docstring describing the tool/utility.
- Every public class and method has a docstring.

### Type Annotations

- Full type hints on all function signatures and return types.
- Use `str | None` (not `Optional[str]`), `dict` (not `Dict`), `list[dict]` (not `List[Dict]`).
- Return types are always annotated (e.g., `-> dict:`, `-> str:`, `-> None:`).

## Tool Class Pattern

Every tool in `src/stock_analysis/tools/` follows this pattern:

```python
from __future__ import annotations

import pandas as pd

from stock_analysis.utils.yfinance_client import YFinanceClient


class ExampleTool:
    """Brief description of what this tool does."""

    def __init__(self, client: YFinanceClient) -> None:
        self._client = client

    def run(
        self,
        symbol: str,
        country_code: str | None = None,
        # ... other parameters with defaults
    ) -> dict:
        """
        Describe what this method does.

        Args:
            symbol:       Ticker symbol (e.g., "RELIANCE", "AAPL").
            country_code: ISO country code. Default "IN" (India NSE).

        Returns:
            Dictionary with the result data and an "error" key on failure.
        """
        qualified = self._client.resolve_symbol(symbol, country_code)
        ticker = self._client.get_ticker(symbol, country_code)

        # ... implementation ...

        return {
            "symbol": qualified,
            # ... result fields
        }
```

**Key rules for tools:**
- Constructor takes `YFinanceClient` via dependency injection.
- Primary method is always `run()`, returning a `dict`.
- On failure, return a dict with an `"error"` key (not raising exceptions).
- Round financial floats to 4 decimal places: `round(float(val), 4)`.
- Serialise dates as ISO strings: `str(idx.date() if hasattr(idx, "date") else idx)`.
- When data is empty, return the expected structure with empty collections and an `"error"` message.

## Registering Tools in the Server

When adding a new tool to `server.py`:

1. Import the tool class.
2. Instantiate it with the shared `_client` at module level.
3. Register a `@mcp.tool()` function that delegates to `_safe_run(tool_instance.run, ...)`.
4. The `@mcp.tool()` function should have a detailed docstring — this becomes the tool description visible to MCP clients.

## Error Handling

- **Tool level:** Return a dict with `"error"` key for validation failures or empty data. Do input validation early and return immediately on failure.
- **Server level:** `_safe_run()` wraps all tool calls in a try/except, serialising any uncaught exception (with traceback) to JSON.
- **No custom exceptions** — rely on built-in exceptions and graceful dict returns.

## JSON Serialisation

All tool output is serialised via:

```python
json.dumps(result, default=str, ensure_ascii=False, indent=2)
```

- `default=str` handles non-serialisable types (e.g., pandas Timestamps).
- `ensure_ascii=False` preserves UTF-8.
- `indent=2` for readable output.

## Testing Conventions

### Structure

- Tests mirror the source tree: `tests/tools/test_<tool>.py`, `tests/utils/test_<util>.py`.
- Test classes are named `Test<ToolName>Run` (e.g., `TestPriceHistoryToolRun`).
- Test methods are named `test_<behaviour>` (e.g., `test_returns_correct_symbol`).

### Network Isolation

An `autouse` fixture in `tests/conftest.py` patches `yf.Ticker` and `yf.Search` to raise `RuntimeError` if called. This guarantees **no real network calls** in any test. Tests override with inner `patch()` contexts or by using mock clients.

### Mocking

- Use the `make_mock_client()` factory from `conftest.py` to build a `MagicMock` standing in for `YFinanceClient`.
- Common fixtures: `mock_client` (default RELIANCE.NS data), `mock_client_empty` (empty data), `ohlcv_df` (60-row OHLCV DataFrame).
- DataFrame factories (`make_ohlcv`, `make_dividends`, etc.) use a seeded RNG (`np.random.default_rng(42)`) for reproducibility.

### Assertions

- Use plain `assert` statements (no custom matchers).
- Check key presence: `assert "error" in result`.
- Check types: `assert isinstance(result["close"], float)`.
- Verify mock calls: `mock_client.get_ticker.return_value.history.assert_called_once()`.

### Running Tests

```bash
pytest                                          # all tests
pytest tests/tools/test_dma.py -v               # specific file
pytest --cov=stock_analysis --cov-report=term-missing  # with coverage
```

## CI/CD

- **Linting** (`lint.yml`): Runs `black --check` and `isort --check --profile black` on PRs.
- **Tests** (`unit-tests.yml`): Runs `pytest tests/ --tb=short -q` on PRs with Python 3.10.

## Utilities Reference

- **`YFinanceClient`**: Thin caching wrapper around yfinance. Methods: `get_ticker(symbol, country_code)`, `resolve_symbol(symbol, country_code)`, `search(query, max_results)`, `clear_cache()`.
- **`CountryExchangeMap`**: Stateless utility class (all `@classmethod`). Maps ISO country codes to yfinance ticker suffixes. Methods: `get_suffix(country_code)`, `build_ticker(symbol, country_code)`, `list_supported_countries()`. Default country is `"IN"` (India NSE).

## Docker

- Multi-stage build with `python:3.10-slim`.
- Runtime defaults: `MCP_TRANSPORT=sse`, `MCP_HOST=0.0.0.0`, `MCP_PORT=8000`.
- Configurable via environment variables.
