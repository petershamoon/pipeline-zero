# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Declare build-time args for Vite MSAL configuration.
# These are baked into the bundle at build time — they must be passed
# as --build-arg in the docker build command (not as Container App env vars).
ARG VITE_ENTRA_CLIENT_ID=""
ARG VITE_ENTRA_AUTHORITY=""
ARG VITE_ENTRA_REDIRECT_URI=""
ARG VITE_API_URL=""

# Expose as ENV so Vite's import.meta.env picks them up during the build
ENV VITE_ENTRA_CLIENT_ID=$VITE_ENTRA_CLIENT_ID
ENV VITE_ENTRA_AUTHORITY=$VITE_ENTRA_AUTHORITY
ENV VITE_ENTRA_REDIRECT_URI=$VITE_ENTRA_REDIRECT_URI
ENV VITE_API_URL=$VITE_API_URL

COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:1.27-alpine
RUN adduser -D -g '' appuser
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Run as non-root
RUN chown -R appuser:appuser /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d
RUN touch /var/run/nginx.pid && chown appuser:appuser /var/run/nginx.pid
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["wget", "--spider", "-q", "http://localhost:3000/health"]
CMD ["nginx", "-g", "daemon off;"]
