# syntax=docker/dockerfile:1.6
#
# CareBridge AI — production container.
# Multi-stage build: Node compiles the React/Vite frontend; Python serves it
# alongside the FastAPI backend on a single port.
#
# Used by Render.com (and any other Docker host). Locally you'd still use
# `python start.py` for dev — this image is for deployments.

# ─── Stage 1: build the React frontend ───────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# Install deps first (layer caches as long as package files don't change)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Now copy the rest and build
COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Python backend + bundled frontend ──────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# System deps for bcrypt / cryptography wheels (slim image is bare)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

# Backend source + editable install (uses pyproject.toml)
COPY backend/ ./backend/
RUN pip install --no-cache-dir -e ./backend

# Bring the built frontend across — backend/app/main.py looks for /app/frontend/dist
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Render injects $PORT; default to 8000 for local `docker run`
ENV PORT=8000
EXPOSE 8000

WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
