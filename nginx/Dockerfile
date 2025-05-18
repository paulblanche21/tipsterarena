FROM nginx:alpine

# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directory for static files
RUN mkdir -p /app/static /app/media

# Expose port 80
EXPOSE 80 