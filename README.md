# AI Investment Portfolio Analysis System

A professional-grade portfolio analytics platform with hedge fund-level technical and fundamental analysis, powered entirely by free data sources (Yahoo Finance).

## Features

- **Technical Analysis**: 15+ indicators (SMA/EMA, RSI, MACD, Bollinger Bands, ADX, Ichimoku, etc.)
- **Fundamental Analysis**: P/E, ROE, Margins, Growth metrics, Dividend data
- **Risk Analysis**: VaR, CVaR, Sharpe/Sortino ratios, Correlation matrix
- **AI Insights**: Template-based analysis engine (optional Ollama LLM support)
- **Dark Terminal Theme**: Professional dark UI with emerald/rose accents

## Quick Start - ONE COMMAND

```bash
# On any platform (Windows, macOS, Linux)
python start.py
```

That's it! This single command will:
1. Install frontend dependencies (`npm install`)
2. Build the React frontend (`npm run build`)
3. Start the FastAPI server on http://localhost:8000

Access the application at: **http://localhost:8000**

API documentation: **http://localhost:8000/docs**

## Alternative Start Methods

### Python (cross-platform)
```bash
python start.py
```

### Windows
```cmd
start.bat
```

### macOS/Linux
```bash
./start.sh
```

### Manual (for development)
```bash
# Terminal 1 - Frontend dev server
cd frontend
npm install
npm run dev        # Runs on http://localhost:5173

# Terminal 2 - Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

## Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- Install backend dependencies:
  ```bash
  cd backend
  pip install -e .
  # Or manually:
  pip install fastapi uvicorn sqlalchemy aiosqlite pandas numpy scipy httpx
  ```

## Architecture

```
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── portfolio/    # Portfolio analysis modules
│   │   │   ├── analysis/ # TA, fundamentals, risk, AI
│   │   │   ├── api/      # API routes
│   │   │   ├── models/   # Database models
│   │   │   └── services/ # Cache, rate limiter, data fetchers
│   │   ├── main.py       # FastAPI app with static file serving
│   │   └── ...
│   └── pyproject.toml
├── frontend/             # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Data fetching hooks (SWR)
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── start.py              # ONE COMMAND startup script
├── start.sh              # Unix startup script
└── start.bat             # Windows startup script
```

## How It Works

1. **Frontend Build**: Vite builds React app to `frontend/dist/`
2. **Static Serving**: FastAPI serves built files from `frontend/dist/`
3. **API Routes**: All API endpoints at `/api/*` prefix
4. **SPA Routing**: Catch-all route serves `index.html` for client-side routing

## API Endpoints

- `GET /api/portfolio/prices/{symbol}` - Price history
- `GET /api/portfolio/technical/{symbol}` - Technical analysis
- `GET /api/portfolio/fundamentals/{symbol}` - Fundamental data
- `GET /api/portfolio/risk/{portfolio_id}` - Risk analysis
- `GET /api/portfolio/ai/symbol/{symbol}` - AI insights
- `GET /api/health` - Health check

## Configuration

### Environment Variables

Create `.env` in project root:
```bash
# Optional: Custom API URL for frontend dev
VITE_API_URL=http://localhost:8000/api

# Optional: Disable AI features
VITE_ENABLE_AI=true
```

### Cache & Rate Limiting

Edit `backend/app/portfolio/services/cache_manager.py`:
```python
CacheConfig(
    ttl_prices=3600,        # 1 hour
    ttl_fundamentals=86400, # 24 hours
    max_entries=10000,
)
```

Edit `backend/app/portfolio/services/rate_limiter.py`:
```python
RateLimitConfig(
    calls_per_second=2.0,  # Respectful rate limiting
    retry_attempts=3,
)
```

## Data Sources

- **Yahoo Finance**: Free, no API key required (15-min delayed)
- **SQLite Cache**: Local caching with TTL
- **No external API costs**: Everything runs locally

## Development

### Frontend Development
```bash
cd frontend
npm run dev    # Hot reload on http://localhost:5173
```

### Backend Development
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Running Tests
```bash
cd backend
pytest tests/ -v
```

## Troubleshooting

### Port already in use
```bash
# Find and kill process on port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

### Frontend build fails
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Backend dependencies missing
```bash
cd backend
pip install -e .
# Or:
pip install fastapi uvicorn sqlalchemy aiosqlite pandas numpy scipy httpx python-jose passlib
```

## License

MIT License - Free for personal and commercial use.
