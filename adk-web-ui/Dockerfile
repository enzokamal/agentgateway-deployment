# --------------------------
# Base image
# --------------------------
FROM python:3.11-slim

# --------------------------
# Set working directory
# --------------------------
WORKDIR /app

# --------------------------
# Install system dependencies
# --------------------------
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir uv
# --------------------------
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

# --------------------------
# Copy application files
# --------------------------
COPY run.py .
COPY app.py . 
COPY app/ ./app/
COPY templates/ ./templates/
COPY config.py .

# --------------------------
# Create non-root user
# --------------------------
RUN useradd -m -u 1000 appuser
USER appuser

# --------------------------
# Expose port if needed (optional)
# --------------------------
EXPOSE 5000

# --------------------------
# Add virtualenv bin to PATH
# --------------------------
ENV PATH="/app/.venv/bin:$PATH"

# --------------------------
# Entrypoint
# --------------------------
CMD ["uv", "run", "python", "app.py"]
