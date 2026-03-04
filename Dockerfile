# ── Build stage ──────────────────────────────────────────────────────────────
# python:3.10-slim (Debian/glibc) is used instead of Alpine because numpy,
# scipy and pandas ship pre-built manylinux wheels that require glibc.
# On Alpine (musl libc) pip would fall back to compiling from source, needing
# a full GCC toolchain and producing a larger final image.
FROM python:3.10-slim AS builder

WORKDIR /app

# Create a virtual environment isolated from the system Python
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip first so we get the latest manylinux wheel resolver
RUN pip install --upgrade --no-cache-dir pip setuptools wheel

# Copy only the files needed to resolve & install dependencies.
# Doing this before copying source lets Docker cache the expensive layer.
COPY requirements.txt pyproject.toml ./
COPY src/ ./src/

# All heavy deps (numpy, scipy, pandas) install via pre-built manylinux wheels —
# no compiler required. -e . installs the package via pyproject.toml.
RUN pip install --no-cache-dir -e .


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

WORKDIR /app

# Copy the fully-populated venv from the builder
COPY --from=builder /opt/venv /opt/venv

# Copy the application source
COPY src/ ./src/

ENV PATH="/opt/venv/bin:$PATH"

# ── Transport configuration ───────────────────────────────────────────────────
# Override MCP_TRANSPORT to 'stdio' if you attach the container via stdin/stdout.
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000

# Expose the SSE port so host-machine MCP clients can connect.
EXPOSE 8000

# Use the console_scripts entry point defined in pyproject.toml.
CMD ["stock-analysis-mcp"]
