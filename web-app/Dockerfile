# Stage 1: install dependencies into an isolated folder
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: minimal runtime image
FROM python:3.12-slim AS runner
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Copy only the installed packages and the application file
COPY --from=builder /install /usr/local
COPY app.py .

# Run as a normal user, not root
RUN useradd -u 1000 appuser
USER appuser

EXPOSE 5000
CMD ["python", "app.py"]