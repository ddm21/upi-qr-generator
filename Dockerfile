# Multi-stage build for a lean runtime image
FROM python:3.12-slim AS builder
WORKDIR /app

# Install Python dependencies into an isolated prefix
COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY main.py ./
COPY assets ./assets

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
