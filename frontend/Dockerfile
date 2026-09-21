# Multi-stage build: compile the Vite/React app with Node, serve the static
# bundle with nginx. Final image is ~25MB and idles at a few MB of RAM.

# --- Stage 1: build ---------------------------------------------------------
FROM node:24-alpine AS build

WORKDIR /app

# Install deps first so this layer is cached until package*.json changes
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Baked in at build time (Vite inlines import.meta.env.VITE_*). The browser
# calls the API directly, so this must be the host-visible address.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Stage 2: serve ---------------------------------------------------------
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
