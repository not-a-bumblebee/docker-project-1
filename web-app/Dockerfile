# Stage 1: Build dependencies in system site-packages
FROM python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime Image
FROM python:3.9-slim AS runner
WORKDIR /app

# Copy installed python packages from builder stage's global site-packages
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Create and switch to a non-root user for security
RUN useradd -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
CMD ["python", "app.py"]