"""FastAPI routes for portfolio analysis."""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..models.schemas import (
    APIResponse,
    ErrorResponse,
    TimeFrame,
    Interval,
    StockPriceHistory,
    TechnicalAnalysis,
    FundamentalAnalysis,
    PortfolioCreate,
    PortfolioResponse,
    PortfolioSummary,
    RiskAnalysis,
    AIAnalysisResponse,
    ScreenerFilter,
    ScreenerResult,
)
from ..services.yfinance_client import YFinanceClient, get_yfinance_client
from ..services.cache_manager import CacheManager, get_cache
from ..services.rate_limiter import RateLimiter, get_rate_limiter
from ..analysis.technical import TechnicalAnalyzer, OHLCVData
from ..analysis.fundamentals import FundamentalAnalyzer
from ..analysis.risk import RiskAnalyzer
from ..analysis.ai_insights import AIAnalyzer, AIConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


# =============================================================================
# Dependencies
# =============================================================================

async def get_yf():
    """Get Yahoo Finance client dependency."""
    client = await get_yfinance_client()
    try:
        yield client
    finally:
        await client.close()


def get_analyzer(yf: YFinanceClient = Depends(get_yf)) -> FundamentalAnalyzer:
    """Get fundamental analyzer dependency."""
    return FundamentalAnalyzer(yf)


def get_risk_analyzer(yf: YFinanceClient = Depends(get_yf)) -> RiskAnalyzer:
    """Get risk analyzer dependency."""
    return RiskAnalyzer(yf)


def get_ai_analyzer() -> AIAnalyzer:
    """Get AI analyzer dependency."""
    return AIAnalyzer(AIConfig(backend="template"))


# =============================================================================
# Market Data Routes
# =============================================================================

@router.get("/prices/{symbol}", response_model=APIResponse)
async def get_prices(
    symbol: str,
    period: TimeFrame = TimeFrame.ONE_YEAR,
    interval: Interval = Interval.ONE_DAY,
    yf: YFinanceClient = Depends(get_yf),
):
    """
    Get historical price data for a symbol.
    
    Args:
        symbol: Stock symbol (e.g., AAPL, MSFT)
        period: Time period for data
        interval: Data interval
    """
    try:
        data = await yf.get_price_history(
            symbol.upper(),
            period=period.value,
            interval=interval.value,
        )
        
        ohlcv = yf.parse_ohlcv(data)
        
        if not ohlcv:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        history = StockPriceHistory(
            symbol=symbol.upper(),
            timeframe=period,
            interval=interval,
            data=ohlcv,
        )
        
        return APIResponse(
            success=True,
            data=history.model_dump(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prices for {symbol}: {e}")
        return APIResponse(
            success=False,
            message=f"Failed to fetch prices: {str(e)}",
            stale=True,
        )


@router.get("/quote/{symbol}", response_model=APIResponse)
async def get_quote(
    symbol: str,
    yf: YFinanceClient = Depends(get_yf),
):
    """Get current quote for a symbol."""
    try:
        data = await yf.get_quote(symbol.upper())
        result = data.get("quoteResponse", {}).get("result", [])
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Quote not found for {symbol}")
        
        return APIResponse(success=True, data=result[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        return APIResponse(success=False, message=str(e))


@router.get("/quotes", response_model=APIResponse)
async def get_multiple_quotes(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    yf: YFinanceClient = Depends(get_yf),
):
    """Get quotes for multiple symbols."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        quotes = await yf.get_multiple_quotes(symbol_list)
        
        return APIResponse(success=True, data=quotes)
        
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        return APIResponse(success=False, message=str(e))


# =============================================================================
# Technical Analysis Routes
# =============================================================================

@router.get("/technical/{symbol}", response_model=APIResponse)
async def get_technical_analysis(
    symbol: str,
    period: TimeFrame = TimeFrame.ONE_YEAR,
    yf: YFinanceClient = Depends(get_yf),
):
    """
    Get comprehensive technical analysis for a symbol.
    
    Includes moving averages, momentum indicators, volatility measures,
    volume analysis, and trend indicators.
    """
    try:
        # Fetch price data
        data = await yf.get_price_history(symbol.upper(), period=period.value)
        ohlcv = yf.parse_ohlcv(data)
        
        if len(ohlcv) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data for {symbol}. Need at least 50 periods."
            )
        
        # Perform technical analysis
        ohlcv_data = OHLCVData.from_list(ohlcv)
        analyzer = TechnicalAnalyzer(ohlcv_data)
        analysis = analyzer.analyze(symbol.upper())
        
        return APIResponse(success=True, data=analysis.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in technical analysis for {symbol}: {e}")
        return APIResponse(success=False, message=str(e))


@router.get("/technical/{symbol}/indicators", response_model=APIResponse)
async def get_indicators(
    symbol: str,
    indicators: str = Query(..., description="Comma-separated list: sma,ema,rsi,macd,bollinger"),
    period: int = Query(14, ge=5, le=200),
    yf: YFinanceClient = Depends(get_yf),
):
    """Get specific technical indicators."""
    try:
        data = await yf.get_price_history(symbol.upper())
        ohlcv = yf.parse_ohlcv(data)
        ohlcv_data = OHLCVData.from_list(ohlcv)
        analyzer = TechnicalAnalyzer(ohlcv_data)
        
        requested = [i.strip().lower() for i in indicators.split(",")]
        results = {}
        
        for ind in requested:
            if ind == "sma":
                results["sma"] = analyzer.sma(period).iloc[-1]
            elif ind == "ema":
                results["ema"] = analyzer.ema(period).iloc[-1]
            elif ind == "rsi":
                results["rsi"] = analyzer.rsi(period).iloc[-1]
            elif ind == "macd":
                macd, signal, hist = analyzer.macd()
                results["macd"] = {
                    "macd": macd.iloc[-1],
                    "signal": signal.iloc[-1],
                    "histogram": hist.iloc[-1],
                }
            elif ind == "bollinger":
                upper, middle, lower = analyzer.bollinger_bands(period)
                results["bollinger"] = {
                    "upper": upper.iloc[-1],
                    "middle": middle.iloc[-1],
                    "lower": lower.iloc[-1],
                }
            elif ind == "atr":
                results["atr"] = analyzer.atr(period).iloc[-1]
            elif ind == "adx":
                adx, plus_di, minus_di = analyzer.adx(period)
                results["adx"] = {
                    "adx": adx.iloc[-1],
                    "plus_di": plus_di.iloc[-1],
                    "minus_di": minus_di.iloc[-1],
                }
        
        return APIResponse(success=True, data=results)
        
    except Exception as e:
        logger.error(f"Error calculating indicators for {symbol}: {e}")
        return APIResponse(success=False, message=str(e))


# =============================================================================
# Fundamental Analysis Routes
# =============================================================================

@router.get("/fundamentals/{symbol}", response_model=APIResponse)
async def get_fundamentals(
    symbol: str,
    analyzer: FundamentalAnalyzer = Depends(get_analyzer),
):
    """
    Get comprehensive fundamental analysis.
    
    Includes valuation, profitability, financial health, growth,
    dividend, and ownership metrics.
    """
    try:
        analysis = await analyzer.analyze(symbol.upper())
        return APIResponse(success=True, data=analysis.model_dump())
        
    except Exception as e:
        logger.error(f"Error in fundamental analysis for {symbol}: {e}")
        return APIResponse(success=False, message=str(e))


@router.get("/fundamentals/{symbol}/financials", response_model=APIResponse)
async def get_financial_statements(
    symbol: str,
    statement: str = Query("income", enum=["income", "balance", "cashflow"]),
    yf: YFinanceClient = Depends(get_yf),
):
    """Get financial statement data."""
    try:
        modules = {
            "income": "incomeStatementHistory",
            "balance": "balanceSheetHistory",
            "cashflow": "cashflowStatementHistory",
        }
        
        data = await yf.get_fundamentals(symbol.upper(), modules=[modules[statement]])
        result = data.get("quoteSummary", {}).get("result", [{}])[0]
        
        return APIResponse(success=True, data=result)
        
    except Exception as e:
        logger.error(f"Error fetching financials for {symbol}: {e}")
        return APIResponse(success=False, message=str(e))


# =============================================================================
# Portfolio Routes
# =============================================================================

# In-memory storage for demo (would use database in production)
_portfolios = {}
_next_portfolio_id = 1


@router.post("/portfolios", response_model=APIResponse)
async def create_portfolio(portfolio: PortfolioCreate):
    """Create a new portfolio."""
    global _next_portfolio_id
    
    try:
        portfolio_id = _next_portfolio_id
        _next_portfolio_id += 1
        
        # Create portfolio dict
        p = {
            "id": portfolio_id,
            "name": portfolio.name,
            "description": portfolio.description,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "benchmark_symbol": portfolio.benchmark_symbol,
            "holdings": [],
        }
        
        # Add holdings
        for h in portfolio.holdings:
            p["holdings"].append({
                "id": len(p["holdings"]) + 1,
                "symbol": h.symbol,
                "shares": float(h.shares),
                "average_cost": float(h.average_cost),
                "purchase_date": h.purchase_date,
                "notes": h.notes,
            })
        
        _portfolios[portfolio_id] = p
        
        return APIResponse(
            success=True,
            data={"id": portfolio_id, "message": "Portfolio created"},
        )
        
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        return APIResponse(success=False, message=str(e))


@router.get("/portfolios", response_model=APIResponse)
async def list_portfolios():
    """List all portfolios with summary."""
    try:
        summaries = []
        for p in _portfolios.values():
            summaries.append({
                "id": p["id"],
                "name": p["name"],
                "holding_count": len(p["holdings"]),
                "total_value": 0,  # Would calculate from prices
                "total_pnl_percent": 0,
                "day_change_percent": 0,
            })
        
        return APIResponse(success=True, data=summaries)
        
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.get("/portfolios/{portfolio_id}", response_model=APIResponse)
async def get_portfolio(
    portfolio_id: int,
    yf: YFinanceClient = Depends(get_yf),
):
    """Get portfolio details with current prices."""
    try:
        if portfolio_id not in _portfolios:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        p = _portfolios[portfolio_id]
        
        # Fetch current prices
        symbols = [h["symbol"] for h in p["holdings"]]
        prices = {}
        
        if symbols:
            quotes = await yf.get_multiple_quotes(symbols)
            for symbol in symbols:
                quote = quotes.get(symbol, {})
                prices[symbol] = quote.get("regularMarketPrice", 0)
        
        # Calculate portfolio values
        total_value = 0
        total_cost = 0
        day_change = 0
        
        holdings_response = []
        for h in p["holdings"]:
            current_price = prices.get(h["symbol"], 0)
            market_value = h["shares"] * current_price
            cost_basis = h["shares"] * h["average_cost"]
            
            total_value += market_value
            total_cost += cost_basis
            
            holdings_response.append({
                "id": h["id"],
                "symbol": h["symbol"],
                "shares": h["shares"],
                "average_cost": h["average_cost"],
                "purchase_date": h["purchase_date"],
                "notes": h["notes"],
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": market_value - cost_basis,
                "unrealized_pnl_percent": ((market_value / cost_basis) - 1) * 100 if cost_basis else 0,
            })
        
        total_pnl = total_value - total_cost
        total_pnl_percent = ((total_value / total_cost) - 1) * 100 if total_cost else 0
        
        response = {
            "id": p["id"],
            "name": p["name"],
            "description": p["description"],
            "created_at": p["created_at"],
            "updated_at": p["updated_at"],
            "benchmark_symbol": p["benchmark_symbol"],
            "holdings": holdings_response,
            "total_value": total_value,
            "total_cost": total_cost,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "day_change": day_change,
            "day_change_percent": 0,
        }
        
        return APIResponse(success=True, data=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return APIResponse(success=False, message=str(e))


@router.delete("/portfolios/{portfolio_id}", response_model=APIResponse)
async def delete_portfolio(portfolio_id: int):
    """Delete a portfolio."""
    if portfolio_id not in _portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    del _portfolios[portfolio_id]
    return APIResponse(success=True, data={"message": "Portfolio deleted"})


# =============================================================================
# Risk Analysis Routes
# =============================================================================

@router.get("/risk/{portfolio_id}", response_model=APIResponse)
async def get_risk_analysis(
    portfolio_id: int,
    analyzer: RiskAnalyzer = Depends(get_risk_analyzer),
    yf: YFinanceClient = Depends(get_yf),
):
    """
    Get comprehensive risk analysis for a portfolio.
    
    Includes VaR, CVaR, Sharpe ratio, correlation matrix,
    and concentration metrics.
    """
    try:
        if portfolio_id not in _portfolios:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        p = _portfolios[portfolio_id]
        
        # Create holding objects
        class SimpleHolding:
            def __init__(self, h):
                self.symbol = h["symbol"]
                self.shares = h["shares"]
                self.average_cost = h["average_cost"]
        
        holdings = [SimpleHolding(h) for h in p["holdings"]]
        
        analysis = await analyzer.analyze_portfolio(portfolio_id, holdings)
        
        return APIResponse(success=True, data=analysis.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in risk analysis: {e}")
        return APIResponse(success=False, message=str(e))


# =============================================================================
# AI Analysis Routes
# =============================================================================

@router.get("/ai/symbol/{symbol}", response_model=APIResponse)
async def get_symbol_ai_analysis(
    symbol: str,
    analyzer: FundamentalAnalyzer = Depends(get_analyzer),
    ai: AIAnalyzer = Depends(get_ai_analyzer),
    yf: YFinanceClient = Depends(get_yf),
):
    """
    Get AI-powered analysis for a symbol.
    
    Combines technical and fundamental analysis with AI-generated insights.
    """
    try:
        # Get technical analysis
        data = await yf.get_price_history(symbol.upper())
        ohlcv = yf.parse_ohlcv(data)
        ohlcv_data = OHLCVData.from_list(ohlcv)
        tech_analyzer = TechnicalAnalyzer(ohlcv_data)
        technical = tech_analyzer.analyze(symbol.upper())
        
        # Get fundamental analysis
        try:
            fundamental = await analyzer.analyze(symbol.upper())
        except Exception:
            fundamental = None
        
        # Generate AI insights
        ai_analysis = await ai.analyze_symbol(symbol.upper(), technical, fundamental)
        
        return APIResponse(success=True, data=ai_analysis.model_dump())
        
    except Exception as e:
        logger.error(f"Error in AI analysis for {symbol}: {e}")
        return APIResponse(success=False, message=str(e))


@router.get("/ai/portfolio/{portfolio_id}", response_model=APIResponse)
async def get_portfolio_ai_analysis(
    portfolio_id: int,
    risk_analyzer: RiskAnalyzer = Depends(get_risk_analyzer),
    ai: AIAnalyzer = Depends(get_ai_analyzer),
    yf: YFinanceClient = Depends(get_yf),
):
    """Get AI-powered analysis for a portfolio."""
    try:
        if portfolio_id not in _portfolios:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        p = _portfolios[portfolio_id]
        
        class SimpleHolding:
            def __init__(self, h):
                self.symbol = h["symbol"]
                self.shares = h["shares"]
                self.average_cost = h["average_cost"]
        
        holdings = [SimpleHolding(h) for h in p["holdings"]]
        
        # Get risk analysis
        risk = await risk_analyzer.analyze_portfolio(portfolio_id, holdings)
        
        # Generate AI insights
        ai_analysis = await ai.analyze_portfolio(portfolio_id, risk, holdings)
        
        return APIResponse(success=True, data=ai_analysis.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in portfolio AI analysis: {e}")
        return APIResponse(success=False, message=str(e))


# =============================================================================
# Screener Routes
# =============================================================================

@router.post("/screener", response_model=APIResponse)
async def run_screener(
    filter: ScreenerFilter,
    yf: YFinanceClient = Depends(get_yf),
):
    """Run stock screener with filters."""
    try:
        # For demo, return a few major stocks
        # In production, this would query a database of all stocks
        demo_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "WMT"]
        
        quotes = await yf.get_multiple_quotes(demo_symbols)
        
        results = []
        for symbol, quote in quotes.items():
            try:
                result = ScreenerResult(
                    symbol=symbol,
                    name=quote.get("longName", symbol),
                    price=quote.get("regularMarketPrice", 0),
                    change_percent=quote.get("regularMarketChangePercent", 0),
                    market_cap=quote.get("marketCap"),
                    pe_trailing=quote.get("trailingPE"),
                    dividend_yield=quote.get("dividendYield", 0) * 100 if quote.get("dividendYield") else None,
                    sector=None,
                    rsi_14=None,
                    volume=quote.get("regularMarketVolume"),
                    avg_volume=quote.get("averageDailyVolume3Month"),
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Skipping {symbol} in screener: {e}")
        
        # Apply filters
        filtered = results
        
        if filter.pe_min is not None:
            filtered = [r for r in filtered if r.pe_trailing and r.pe_trailing >= filter.pe_min]
        if filter.pe_max is not None:
            filtered = [r for r in filtered if r.pe_trailing and r.pe_trailing <= filter.pe_max]
        if filter.market_cap_min is not None:
            filtered = [r for r in filtered if r.market_cap and r.market_cap >= filter.market_cap_min]
        
        return APIResponse(success=True, data=[r.model_dump() for r in filtered])
        
    except Exception as e:
        logger.error(f"Error running screener: {e}")
        return APIResponse(success=False, message=str(e))


# =============================================================================
# System Routes
# =============================================================================

@router.get("/health", response_model=APIResponse)
async def health_check():
    """Check API health status."""
    return APIResponse(
        success=True,
        data={
            "status": "healthy",
            "service": "portfolio-analyzer",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@router.get("/cache/stats", response_model=APIResponse)
async def get_cache_stats():
    """Get cache statistics."""
    try:
        cache = get_cache()
        stats = cache.get_stats()
        return APIResponse(success=True, data=stats)
    except Exception as e:
        return APIResponse(success=False, message=str(e))


@router.post("/cache/clear", response_model=APIResponse)
async def clear_cache():
    """Clear all cache entries."""
    try:
        cache = get_cache()
        count = cache.clear_all()
        return APIResponse(
            success=True,
            data={"message": f"Cleared {count} cache entries"},
        )
    except Exception as e:
        return APIResponse(success=False, message=str(e))
