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
COPY templates/ ./templates/
COPY config.py .
COPY routes/ ./routes/
COPY auth/ ./auth/
COPY session_manager.py .
COPY utils.py .
COPY adk_chat_graph_ui.py .
COPY adk_chat_sessions.db .
COPY adk_chat_ui_memory.py .
COPY chart_tool.py .
COPY main.py .

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
