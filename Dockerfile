# Build stage for Node.js dependencies
FROM node:20-slim AS node-builder
WORKDIR /app

# Set npm config to avoid hanging
ENV NPM_CONFIG_LOGLEVEL=warn
ENV NPM_CONFIG_FETCH_TIMEOUT=300000
ENV NPM_CONFIG_FETCH_RETRIES=3

# Copy only package files first to leverage Docker cache
COPY package*.json ./
COPY vite.config.mjs ./

# Install dependencies with specific flags for better performance
RUN npm install --no-audit --no-fund --prefer-offline --legacy-peer-deps --network-timeout=300000

# Copy static files and build
COPY static/ ./static/
RUN npm run build

# Build stage for Python dependencies
FROM python:3.12-slim AS python-builder
WORKDIR /app

# Set pip configuration for better caching and performance
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_EXTRA_INDEX_URL=https://pypi.org/simple \
    PIP_INDEX_URL=https://pypi.org/simple

# Install build dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with optimized flags
RUN pip install --no-cache-dir -r requirements.txt --timeout=100 \
    --compile \
    --no-deps \
    --prefer-binary \
    --only-binary=:all:

# Final stage
FROM python:3.12-slim
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=tipsterarena.settings

# Install runtime dependencies and create directories in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/media /app/staticfiles

# Copy files from previous stages
COPY --from=python-builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=node-builder /app/static/dist/ ./static/dist/
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run the application
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "tipsterarena.asgi:application"] 