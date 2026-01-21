FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the lockfile and pyproject.toml
COPY pyproject.toml uv.lock ./

# Install the project's dependencies using the lockfile and settings
# Install the project's dependencies using the lockfile and settings
ENV UV_PROJECT_ENVIRONMENT="/.venv"
RUN uv sync --frozen --no-install-project --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/.venv/bin:$PATH"

# Copy the rest of the source code
COPY . .

# Set PYTHONPATH so that `app` module can be found
ENV PYTHONPATH=/app/src

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
