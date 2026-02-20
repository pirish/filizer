# Use a Python base image
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files from the root
COPY pyproject.toml uv.lock ./

# Install dependencies (excluding the project itself first to cache layers)
RUN uv sync --frozen --no-cache --no-install-project

# Copy application code and shared modules
COPY server/ ./server/
COPY common/ ./common/

# Sync the project
RUN uv sync --frozen --no-cache

# Expose the port the app runs on
EXPOSE 8000

# Set PYTHONPATH to include the root directory for 'common' module imports
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uv", "run", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
