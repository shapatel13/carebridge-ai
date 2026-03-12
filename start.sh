#!/bin/bash
# AI Investment Portfolio Analysis System - Startup Script (Unix/Linux/macOS)

set -e

echo "================================================================"
echo "  AI Investment Portfolio Analysis System"
echo "================================================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo "[1/4] Checking prerequisites..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm is not installed!"
    exit 1
fi
echo "  Node.js version: $(node --version)"
echo ""

echo "[2/4] Installing frontend dependencies..."
cd "$FRONTEND_DIR"
npm install
echo ""

echo "[3/4] Building frontend..."
npm run build
echo "  Build successful!"
echo ""

echo "[4/4] Starting FastAPI server..."
echo "================================================================"
echo "  Server Ready!"
echo "================================================================"
echo "  Access the app at: http://localhost:8000"
echo "  API docs at: http://localhost:8000/docs"
echo "  Press Ctrl+C to stop"
echo ""

cd "$BACKEND_DIR"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
