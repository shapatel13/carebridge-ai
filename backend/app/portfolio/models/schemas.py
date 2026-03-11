"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class TimeFrame(str, Enum):
    """Chart timeframes."""
    ONE_DAY = "1d"
    FIVE_DAY = "5d"
    ONE_MONTH = "1mo"
    THREE_MONTH = "3mo"
    SIX_MONTH = "6mo"
    ONE_YEAR = "1y"
    TWO_YEAR = "2y"
    FIVE_YEAR = "5y"
    TEN_YEAR = "10y"
    YTD = "ytd"
    MAX = "max"


class Interval(str, Enum):
    """Data intervals."""
    ONE_MINUTE = "1m"
    TWO_MINUTE = "2m"
    FIVE_MINUTE = "5m"
    FIFTEEN_MINUTE = "15m"
    THIRTY_MINUTE = "30m"
    SIXTY_MINUTE = "60m"
    NINETY_MINUTE = "90m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    FIVE_DAY = "5d"
    ONE_WEEK = "1wk"
    ONE_MONTH = "1mo"
    THREE_MONTH = "3mo"


class SignalType(str, Enum):
    """Technical signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


# =============================================================================
# Price Data Schemas
# =============================================================================

class OHLCVPoint(BaseModel):
    """Single OHLCV data point."""
    model_config = ConfigDict(from_attributes=True)
    
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None


class StockPriceHistory(BaseModel):
    """Stock price history response."""
    symbol: str
    timeframe: TimeFrame
    interval: Interval
    data: List[OHLCVPoint]
    currency: str = "USD"
    timezone: str = "America/New_York"


# =============================================================================
# Technical Analysis Schemas
# =============================================================================

class MovingAverages(BaseModel):
    """Moving average values."""
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_100: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None


class MomentumIndicators(BaseModel):
    """Momentum indicator values."""
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None
    cci_20: Optional[float] = None
    williams_r: Optional[float] = None


class VolatilityIndicators(BaseModel):
    """Volatility indicator values."""
    atr_14: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    bollinger_width: Optional[float] = None
    historical_volatility_30d: Optional[float] = None


class VolumeIndicators(BaseModel):
    """Volume indicator values."""
    obv: Optional[float] = None
    volume_sma_20: Optional[float] = None
    relative_volume: Optional[float] = None
    volume_trend: Optional[str] = None  # "increasing", "decreasing", "neutral"


class TrendIndicators(BaseModel):
    """Trend indicator values."""
    adx_14: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None
    parabolic_sar: Optional[float] = None
    ichimoku_tenkan: Optional[float] = None
    ichimoku_kijun: Optional[float] = None
    ichimoku_senkou_a: Optional[float] = None
    ichimoku_senkou_b: Optional[float] = None


class SupportResistance(BaseModel):
    """Support and resistance levels."""
    pivot: float
    support_1: float
    support_2: float
    resistance_1: float
    resistance_2: float
    recent_highs: List[float] = []
    recent_lows: List[float] = []


class TechnicalAnalysis(BaseModel):
    """Complete technical analysis for a symbol."""
    symbol: str
    timestamp: datetime
    current_price: float
    change_percent: float
    
    moving_averages: MovingAverages
    momentum: MomentumIndicators
    volatility: VolatilityIndicators
    volume: VolumeIndicators
    trend: TrendIndicators
    support_resistance: Optional[SupportResistance] = None
    
    # Composite signals
    overall_signal: SignalType = SignalType.HOLD
    signal_strength: float = Field(..., ge=0, le=1)
    trend_direction: str = "neutral"  # "bullish", "bearish", "neutral", "sideways"
    key_levels: Dict[str, float] = {}


# =============================================================================
# Fundamental Analysis Schemas
# =============================================================================

class CompanyInfo(BaseModel):
    """Basic company information."""
    symbol: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    description: Optional[str] = None


class ValuationMetrics(BaseModel):
    """Valuation ratio metrics."""
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None


class ProfitabilityMetrics(BaseModel):
    """Profitability metrics."""
    roe: Optional[float] = None  # Return on Equity
    roa: Optional[float] = None  # Return on Assets
    roic: Optional[float] = None  # Return on Invested Capital
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
    fcf_yield: Optional[float] = None


class FinancialHealthMetrics(BaseModel):
    """Financial health metrics."""
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    debt_to_assets: Optional[float] = None
    interest_coverage: Optional[float] = None
    operating_cashflow: Optional[float] = None
    free_cashflow: Optional[float] = None


class GrowthMetrics(BaseModel):
    """Growth metrics."""
    revenue_growth_yoy: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None
    revenue_growth_3yr_cagr: Optional[float] = None
    earnings_growth_3yr_cagr: Optional[float] = None
    analyst_revenue_growth_next_yr: Optional[float] = None
    analyst_earnings_growth_next_yr: Optional[float] = None


class DividendInfo(BaseModel):
    """Dividend information."""
    dividend_rate: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    ex_dividend_date: Optional[datetime] = None
    dividend_date: Optional[datetime] = None
    five_year_avg_dividend_yield: Optional[float] = None


class OwnershipInfo(BaseModel):
    """Ownership structure."""
    insider_ownership: Optional[float] = None
    institutional_ownership: Optional[float] = None
    short_percent_float: Optional[float] = None
    short_percent_outstanding: Optional[float] = None
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None


class FundamentalAnalysis(BaseModel):
    """Complete fundamental analysis."""
    symbol: str
    company: CompanyInfo
    valuation: ValuationMetrics
    profitability: ProfitabilityMetrics
    financial_health: FinancialHealthMetrics
    growth: GrowthMetrics
    dividend: DividendInfo
    ownership: OwnershipInfo
    fetched_at: datetime
    data_quality_score: float = Field(..., ge=0, le=1)


# =============================================================================
# Risk Analysis Schemas
# =============================================================================

class RiskMetrics(BaseModel):
    """Portfolio risk metrics."""
    volatility_annual: float
    beta: Optional[float] = None
    alpha: Optional[float] = None
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk (95% confidence)
    cvar_95: float  # Conditional VaR
    calmar_ratio: float
    treynor_ratio: Optional[float] = None


class CorrelationMatrix(BaseModel):
    """Correlation matrix for portfolio holdings."""
    symbols: List[str]
    matrix: List[List[float]]  # 2D correlation matrix


class ConcentrationRisk(BaseModel):
    """Portfolio concentration analysis."""
    top_holding_percent: float
    top_5_holdings_percent: float
    sector_concentration: Dict[str, float]
    herfindahl_index: float  # HHI for concentration measurement


class RiskAnalysis(BaseModel):
    """Complete risk analysis."""
    portfolio_id: int
    risk_level: RiskLevel
    metrics: RiskMetrics
    correlation: CorrelationMatrix
    concentration: ConcentrationRisk
    alerts: List[str] = []
    recommendations: List[str] = []


# =============================================================================
# Portfolio Management Schemas
# =============================================================================

class PortfolioHoldingCreate(BaseModel):
    """Create a new portfolio holding."""
    symbol: str = Field(..., min_length=1, max_length=10)
    shares: Decimal = Field(..., gt=0)
    average_cost: Decimal = Field(..., gt=0)
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator('symbol')
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper()


class PortfolioHoldingResponse(BaseModel):
    """Portfolio holding response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    symbol: str
    shares: Decimal
    average_cost: Decimal
    purchase_date: Optional[datetime]
    notes: Optional[str]
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None
    day_change: Optional[float] = None
    day_change_percent: Optional[float] = None


class PortfolioCreate(BaseModel):
    """Create a new portfolio."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    benchmark_symbol: str = "SPY"
    holdings: List[PortfolioHoldingCreate] = []


class PortfolioResponse(BaseModel):
    """Portfolio response with computed values."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    benchmark_symbol: str
    holdings: List[PortfolioHoldingResponse]
    
    # Computed fields
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_percent: float
    day_change: float
    day_change_percent: float
    cash_allocated: float  # Total cost basis
    cash_available: float = 0  # For future cash tracking


class PortfolioSummary(BaseModel):
    """Brief portfolio summary for list views."""
    id: int
    name: str
    holding_count: int
    total_value: float
    total_pnl_percent: float
    day_change_percent: float


# =============================================================================
# Screener & Watchlist Schemas
# =============================================================================

class ScreenerFilter(BaseModel):
    """Stock screener filter criteria."""
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    pe_min: Optional[float] = None
    pe_max: Optional[float] = None
    pb_min: Optional[float] = None
    pb_max: Optional[float] = None
    dividend_yield_min: Optional[float] = None
    sectors: List[str] = []
    industries: List[str] = []
    rsi_min: Optional[float] = None
    rsi_max: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    volume_min: Optional[int] = None
    revenue_growth_min: Optional[float] = None
    profit_margin_min: Optional[float] = None


class ScreenerResult(BaseModel):
    """Single screener result."""
    symbol: str
    name: str
    price: float
    change_percent: float
    market_cap: Optional[float] = None
    pe_trailing: Optional[float] = None
    dividend_yield: Optional[float] = None
    sector: Optional[str] = None
    rsi_14: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None


class WatchlistItem(BaseModel):
    """Watchlist item with alerts."""
    symbol: str
    added_at: datetime
    target_price_high: Optional[float] = None
    target_price_low: Optional[float] = None
    alert_enabled: bool = False
    notes: Optional[str] = None


# =============================================================================
# AI Analysis Schemas
# =============================================================================

class AIInsight(BaseModel):
    """Single AI-generated insight."""
    category: str  # 'technical', 'fundamental', 'risk', 'sentiment'
    sentiment: str  # 'positive', 'negative', 'neutral', 'caution'
    confidence: float = Field(..., ge=0, le=1)
    title: str
    description: str
    action_items: List[str] = []


class AIAnalysisResponse(BaseModel):
    """AI analysis for a symbol or portfolio."""
    symbol: Optional[str] = None
    portfolio_id: Optional[int] = None
    generated_at: datetime
    insights: List[AIInsight]
    summary: str
    key_risks: List[str]
    opportunities: List[str]
    model_used: str = "template"  # 'ollama', 'template', 'mock'


# =============================================================================
# API Response Wrappers
# =============================================================================

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cached: bool = False
    stale: bool = False


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
