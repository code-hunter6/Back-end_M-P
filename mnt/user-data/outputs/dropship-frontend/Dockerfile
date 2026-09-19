# ---------- Stage 1: build ----------
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Vite inlines VITE_* vars at BUILD time, not runtime, so the API URL has to be
# passed in as a build arg here rather than as a container env var later.
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ARG VITE_USE_MOCKS=false
ARG VITE_GA4_MEASUREMENT_ID=
ARG VITE_FB_PIXEL_ID=

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_USE_MOCKS=$VITE_USE_MOCKS \
    VITE_GA4_MEASUREMENT_ID=$VITE_GA4_MEASUREMENT_ID \
    VITE_FB_PIXEL_ID=$VITE_FB_PIXEL_ID

RUN npm run build

# ---------- Stage 2: serve ----------
# Only the built static files ship — node_modules and source never reach production.
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
