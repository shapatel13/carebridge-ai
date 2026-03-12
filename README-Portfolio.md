# AI Investment Portfolio Analysis System

A professional-grade portfolio analytics platform with hedge fund-level technical and fundamental analysis, powered entirely by free data sources.

## Features

### Technical Analysis
- **Moving Averages**: SMA (20/50/100/200), EMA (12/26), VWAP
- **Momentum**: RSI (14), MACD (12/26/9), Stochastic (14,3,3), CCI (20), Williams %R
- **Volatility**: ATR (14), Bollinger Bands (20,2), Keltner Channels, Historical Volatility
- **Volume**: OBV, Relative Volume, Volume Trend
- **Trend**: ADX (14), Parabolic SAR, Ichimoku Cloud
- **Support/Resistance**: Pivot points, S1/S2, R1/R2 levels

### Fundamental Analysis
- **Valuation**: P/E, P/B, P/S, EV/EBITDA, PEG
- **Profitability**: ROE, ROA, ROIC, Margins (Gross/Operating/Profit)
- **Financial Health**: Current/Quick Ratios, Debt/Equity, Interest Coverage
- **Growth**: Revenue/EPS growth (YoY, 3Y CAGR), Analyst estimates
- **Dividend**: Yield, Rate, Payout Ratio, History
- **Ownership**: Insider, Institutional, Short Interest

### Risk Analysis
- **Metrics**: VaR (95%), CVaR, Sharpe Ratio, Sortino Ratio, Max Drawdown, Calmar Ratio
- **Correlation Matrix**: Cross-asset correlation analysis
- **Concentration Risk**: HHI, Top holdings analysis
- **Risk Levels**: Low, Moderate, High, Extreme classification

### AI Insights
- Template-based analysis engine (default)
- Ollama local LLM integration (optional)
- Multi-category insights: Technical, Fundamental, Risk, Sentiment
- Actionable recommendations

## Architecture

```
├── backend/
│   ├── app/portfolio/
│   │   ├── models/          # Database models & schemas
│   │   ├── services/        # Data fetchers, cache, rate limiter
│   │   ├── analysis/        # TA, fundamentals, risk, AI
│   │   └── api/            # FastAPI routes
│   └── tests/              # Unit tests
├── frontend/
│   ├── src/components/portfolio/  # React components
│   ├── src/hooks/         # SWR data hooks
│   ├── src/services/      # API client
│   ├── src/types/         # TypeScript types
│   └── src/utils/         # Formatters
└── data/                  # SQLite cache database
```

## Free Data Sources

1. **Yahoo Finance** (via HTTP API)
   - Price history, real-time quotes
   - Fundamental data
   - No API key required
   - 2 calls/second rate limit (built-in)

## Quick Start

### Backend

```bash
cd backend

# Install dependencies
pip install pandas numpy scipy httpx

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies (already installed)
npm install

# Run dev server
npm run dev
```

Visit: http://localhost:5173/portfolio

## API Endpoints

### Market Data
- `GET /api/portfolio/prices/{symbol}?period=1y&interval=1d`
- `GET /api/portfolio/quote/{symbol}`
- `GET /api/portfolio/quotes?symbols=AAPL,MSFT`

### Analysis
- `GET /api/portfolio/technical/{symbol}` - Full technical analysis
- `GET /api/portfolio/fundamentals/{symbol}` - Full fundamental analysis
- `GET /api/portfolio/risk/{portfolio_id}` - Portfolio risk analysis

### AI
- `GET /api/portfolio/ai/symbol/{symbol}` - AI symbol analysis
- `GET /api/portfolio/ai/portfolio/{portfolio_id}` - AI portfolio analysis

### Portfolios
- `POST /api/portfolio/portfolios` - Create portfolio
- `GET /api/portfolio/portfolios` - List portfolios
- `GET /api/portfolio/portfolios/{id}` - Get portfolio
- `DELETE /api/portfolio/portfolios/{id}` - Delete portfolio

## Configuration

### AI Backend
Edit `backend/app/portfolio/analysis/ai_insights.py`:

```python
AIConfig(
    backend="template",  # Options: "template", "ollama", "mock"
    ollama_url="http://localhost:11434",
    ollama_model="llama3.2",
)
```

### Cache Settings
Edit `backend/app/portfolio/services/cache_manager.py`:

```python
CacheConfig(
    ttl_prices=3600,        # 1 hour
    ttl_fundamentals=86400, # 24 hours
    max_entries=10000,
)
```

### Rate Limiting
Edit `backend/app/portfolio/services/rate_limiter.py`:

```python
RateLimitConfig(
    calls_per_second=2.0,
    retry_attempts=3,
    circuit_failure_threshold=5,
)
```

## Performance

- **SQLite Cache**: Sub-millisecond lookups for cached data
- **SWR Pattern**: Stale-while-revalidate for optimal UX
- **Rate Limiting**: Automatic retry with exponential backoff
- **Circuit Breaker**: Fault tolerance for external APIs

## Security

- No API keys stored in code
- Local-only LLM inference option
- SQLite database with file permissions
- CORS enabled for local development

## Development

### Running Tests
```bash
cd backend
pytest tests/ -v
```

### Adding Indicators
Edit `backend/app/portfolio/analysis/technical.py`:

```python
def my_indicator(self, period: int = 14) -> pd.Series:
    """Custom indicator implementation."""
    # Your calculation here
    return result
```

## License

MIT License - Free for personal and commercial use.
