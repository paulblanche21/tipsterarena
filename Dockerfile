# Build stage for Node.js dependencies
FROM node:20-slim AS node-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund

# Build stage for Python dependencies
FROM python:3.12-slim AS python-builder
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependencies from builders
COPY --from=python-builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=python-builder /usr/local/bin/ /usr/local/bin/
COPY --from=node-builder /app/node_modules ./node_modules

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=tipsterarena.settings

# Run the application
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "tipsterarena.asgi:application"] 