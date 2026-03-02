FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy workspace root files first for dependency resolution
COPY pyproject.toml uv.lock ./

# Copy the server sub-package
COPY python_oauth_server/ ./python_oauth_server/

# Copy the compliance suite (needed for uv workspace resolution)
COPY compliance_suite/pyproject.toml ./compliance_suite/pyproject.toml
COPY compliance_suite/src/ ./compliance_suite/src/

# Install all dependencies using the lockfile
RUN uv sync --frozen --package python-oauth-server

# Set working directory to the server package
WORKDIR /app/python_oauth_server

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
