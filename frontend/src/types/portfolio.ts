export interface OHLCVPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjusted_close?: number;
}

export interface StockPriceHistory {
  symbol: string;
  timeframe: string;
  interval: string;
  data: OHLCVPoint[];
  currency: string;
  timezone: string;
}

export interface MovingAverages {
  sma_20?: number;
  sma_50?: number;
  sma_100?: number;
  sma_200?: number;
  ema_12?: number;
  ema_26?: number;
}

export interface MomentumIndicators {
  rsi_14?: number;
  macd_line?: number;
  macd_signal?: number;
  macd_histogram?: number;
  stochastic_k?: number;
  stochastic_d?: number;
  cci_20?: number;
  williams_r?: number;
}

export interface VolatilityIndicators {
  atr_14?: number;
  bollinger_upper?: number;
  bollinger_middle?: number;
  bollinger_lower?: number;
  bollinger_width?: number;
  historical_volatility_30d?: number;
}

export interface VolumeIndicators {
  obv?: number;
  volume_sma_20?: number;
  relative_volume?: number;
  volume_trend?: string;
}

export interface TrendIndicators {
  adx_14?: number;
  plus_di?: number;
  minus_di?: number;
  parabolic_sar?: number;
  ichimoku_tenkan?: number;
  ichimoku_kijun?: number;
  ichimoku_senkou_a?: number;
  ichimoku_senkou_b?: number;
}

export interface SupportResistance {
  pivot: number;
  support_1: number;
  support_2: number;
  resistance_1: number;
  resistance_2: number;
  recent_highs: number[];
  recent_lows: number[];
}

export type SignalType = 'buy' | 'sell' | 'hold' | 'strong_buy' | 'strong_sell';

export interface TechnicalAnalysis {
  symbol: string;
  timestamp: string;
  current_price: number;
  change_percent: number;
  moving_averages: MovingAverages;
  momentum: MomentumIndicators;
  volatility: VolatilityIndicators;
  volume: VolumeIndicators;
  trend: TrendIndicators;
  support_resistance?: SupportResistance;
  overall_signal: SignalType;
  signal_strength: number;
  trend_direction: 'bullish' | 'bearish' | 'neutral' | 'sideways';
  key_levels: Record<string, number | null>;
}

export interface CompanyInfo {
  symbol: string;
  name: string;
  sector?: string;
  industry?: string;
  country?: string;
  website?: string;
  employees?: number;
  description?: string;
}

export interface ValuationMetrics {
  market_cap?: number;
  enterprise_value?: number;
  trailing_pe?: number;
  forward_pe?: number;
  peg_ratio?: number;
  price_to_book?: number;
  price_to_sales?: number;
  ev_to_ebitda?: number;
  ev_to_revenue?: number;
}

export interface ProfitabilityMetrics {
  roe?: number;
  roa?: number;
  roic?: number;
  gross_margin?: number;
  operating_margin?: number;
  profit_margin?: number;
  ebitda_margin?: number;
  fcf_yield?: number;
}

export interface FinancialHealthMetrics {
  current_ratio?: number;
  quick_ratio?: number;
  debt_to_equity?: number;
  debt_to_assets?: number;
  interest_coverage?: number;
  operating_cashflow?: number;
  free_cashflow?: number;
}

export interface GrowthMetrics {
  revenue_growth_yoy?: number;
  earnings_growth_yoy?: number;
  revenue_growth_3yr_cagr?: number;
  earnings_growth_3yr_cagr?: number;
  analyst_revenue_growth_next_yr?: number;
  analyst_earnings_growth_next_yr?: number;
}

export interface DividendInfo {
  dividend_rate?: number;
  dividend_yield?: number;
  payout_ratio?: number;
  ex_dividend_date?: string;
  dividend_date?: string;
  five_year_avg_dividend_yield?: number;
}

export interface OwnershipInfo {
  insider_ownership?: number;
  institutional_ownership?: number;
  short_percent_float?: number;
  short_percent_outstanding?: number;
  shares_outstanding?: number;
  float_shares?: number;
}

export interface FundamentalAnalysis {
  symbol: string;
  company: CompanyInfo;
  valuation: ValuationMetrics;
  profitability: ProfitabilityMetrics;
  financial_health: FinancialHealthMetrics;
  growth: GrowthMetrics;
  dividend: DividendInfo;
  ownership: OwnershipInfo;
  fetched_at: string;
  data_quality_score: number;
}

export interface RiskMetrics {
  volatility_annual: number;
  beta?: number;
  alpha?: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  var_95: number;
  cvar_95: number;
  calmar_ratio: number;
  treynor_ratio?: number;
}

export interface CorrelationMatrix {
  symbols: string[];
  matrix: number[][];
}

export interface ConcentrationRisk {
  top_holding_percent: number;
  top_5_holdings_percent: number;
  sector_concentration: Record<string, number>;
  herfindahl_index: number;
}

export type RiskLevel = 'low' | 'moderate' | 'high' | 'extreme';

export interface RiskAnalysis {
  portfolio_id: number;
  risk_level: RiskLevel;
  metrics: RiskMetrics;
  correlation: CorrelationMatrix;
  concentration: ConcentrationRisk;
  alerts: string[];
  recommendations: string[];
}

export interface PortfolioHolding {
  id: number;
  symbol: string;
  shares: number;
  average_cost: number;
  purchase_date?: string;
  notes?: string;
  current_price?: number;
  market_value?: number;
  unrealized_pnl?: number;
  unrealized_pnl_percent?: number;
  day_change?: number;
  day_change_percent?: number;
}

export interface Portfolio {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  benchmark_symbol: string;
  holdings: PortfolioHolding[];
  total_value: number;
  total_cost: number;
  total_pnl: number;
  total_pnl_percent: number;
  day_change: number;
  day_change_percent: number;
}

export interface AIInsight {
  category: string;
  sentiment: 'positive' | 'negative' | 'neutral' | 'caution';
  confidence: number;
  title: string;
  description: string;
  action_items: string[];
}

export interface AIAnalysis {
  symbol?: string;
  portfolio_id?: number;
  generated_at: string;
  insights: AIInsight[];
  summary: string;
  key_risks: string[];
  opportunities: string[];
  model_used: string;
}

export interface APIResponse<T = unknown> {
  success: boolean;
  message?: string;
  data?: T;
  timestamp: string;
  cached?: boolean;
  stale?: boolean;
}

export interface ScreenerResult {
  symbol: string;
  name: string;
  price: number;
  change_percent: number;
  market_cap?: number;
  pe_trailing?: number;
  dividend_yield?: number;
  sector?: string;
  rsi_14?: number;
  volume?: number;
  avg_volume?: number;
}

export type TimeFrame = '1d' | '5d' | '1mo' | '3mo' | '6mo' | '1y' | '2y' | '5y' | '10y' | 'ytd' | 'max';
export type Interval = '1m' | '2m' | '5m' | '15m' | '30m' | '60m' | '90m' | '1h' | '1d' | '5d' | '1wk' | '1mo' | '3mo';
export type TabType = 'overview' | 'technical' | 'fundamental' | 'risk' | 'ai';
