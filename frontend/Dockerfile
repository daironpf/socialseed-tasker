# =============================================================================
# Stage 1: Build - Install dependencies and build Vue app
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency definitions
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ ./

# Build the Vue application
RUN npm run build

# =============================================================================
# Stage 2: Serve - Nginx to serve the static files
# =============================================================================
FROM nginx:alpine

# Copy custom nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]