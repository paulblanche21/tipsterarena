# =========================================
# Stage 1: Base Node.js stage for npm dependencies
# =========================================
FROM node:20-slim AS base
WORKDIR /app

# Set npm config to avoid hanging and improve performance
ENV NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_FETCH_TIMEOUT=300000 \
    NPM_CONFIG_FETCH_RETRIES=3

# Copy package files first to leverage Docker cache
COPY package*.json ./
COPY vite.config.mjs ./

# =========================================
# Stage 2: Development stage for Node.js (npm)
# =========================================
FROM base AS development
ENV NODE_ENV=development \
    DJANGO_VITE_DEV_MODE=True

# Install all dependencies (including dev dependencies)
RUN npm install

# Copy the rest of the application
COPY . .

# =========================================
# Stage 3: Production stage for Node.js (npm)
# =========================================
FROM base AS production
ENV NODE_ENV=production \
    DJANGO_VITE_DEV_MODE=False

# Install only production dependencies
RUN npm ci --only=production

# Copy static files
COPY static/ ./static/

# Build static files
RUN npm run build

# =========================================
# Stage 4: Python stage for Django
# =========================================
FROM python:3.11-slim AS python
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python3 manage.py collectstatic --noinput

# =========================================
# Final stage: Combine Python and built static files
# =========================================
FROM python AS final
COPY --from=production /app/static/dist /app/static/dist
ENV PYTHONUNBUFFERED=1
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"] 