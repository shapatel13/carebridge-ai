import { api } from './api';
import type {
  APIResponse,
  StockPriceHistory,
  TechnicalAnalysis,
  FundamentalAnalysis,
  Portfolio,
  RiskAnalysis,
  AIAnalysis,
  ScreenerResult,
  TimeFrame,
  Interval,
} from '../types/portfolio';

// Market Data
export const getPrices = async (
  symbol: string,
  period: TimeFrame = '1y',
  interval: Interval = '1d'
): Promise<APIResponse<StockPriceHistory>> => {
  const response = await api.get(`/portfolio/prices/${symbol}`, {
    params: { period, interval },
  });
  return response.data;
};

export const getQuote = async (symbol: string): Promise<APIResponse<unknown>> => {
  const response = await api.get(`/portfolio/quote/${symbol}`);
  return response.data;
};

export const getMultipleQuotes = async (symbols: string[]): Promise<APIResponse<Record<string, unknown>>> => {
  const response = await api.get('/portfolio/quotes', {
    params: { symbols: symbols.join(',') },
  });
  return response.data;
};

// Technical Analysis
export const getTechnicalAnalysis = async (
  symbol: string,
  period: TimeFrame = '1y'
): Promise<APIResponse<TechnicalAnalysis>> => {
  const response = await api.get(`/portfolio/technical/${symbol}`, {
    params: { period },
  });
  return response.data;
};

export const getIndicators = async (
  symbol: string,
  indicators: string[],
  period: number = 14
): Promise<APIResponse<Record<string, unknown>>> => {
  const response = await api.get(`/portfolio/technical/${symbol}/indicators`, {
    params: { indicators: indicators.join(','), period },
  });
  return response.data;
};

// Fundamental Analysis
export const getFundamentals = async (symbol: string): Promise<APIResponse<FundamentalAnalysis>> => {
  const response = await api.get(`/portfolio/fundamentals/${symbol}`);
  return response.data;
};

// Portfolio Management
export const createPortfolio = async (data: {
  name: string;
  description?: string;
  benchmark_symbol?: string;
  holdings: Array<{
    symbol: string;
    shares: number;
    average_cost: number;
    purchase_date?: string;
    notes?: string;
  }>;
}): Promise<APIResponse<{ id: number; message: string }>> => {
  const response = await api.post('/portfolio/portfolios', data);
  return response.data;
};

export const getPortfolios = async (): Promise<APIResponse<Array<{
  id: number;
  name: string;
  holding_count: number;
  total_value: number;
  total_pnl_percent: number;
  day_change_percent: number;
}>>> => {
  const response = await api.get('/portfolio/portfolios');
  return response.data;
};

export const getPortfolio = async (id: number): Promise<APIResponse<Portfolio>> => {
  const response = await api.get(`/portfolio/portfolios/${id}`);
  return response.data;
};

export const deletePortfolio = async (id: number): Promise<APIResponse<{ message: string }>> => {
  const response = await api.delete(`/portfolio/portfolios/${id}`);
  return response.data;
};

// Risk Analysis
export const getRiskAnalysis = async (portfolioId: number): Promise<APIResponse<RiskAnalysis>> => {
  const response = await api.get(`/portfolio/risk/${portfolioId}`);
  return response.data;
};

// AI Analysis
export const getSymbolAIAnalysis = async (symbol: string): Promise<APIResponse<AIAnalysis>> => {
  const response = await api.get(`/portfolio/ai/symbol/${symbol}`);
  return response.data;
};

export const getPortfolioAIAnalysis = async (portfolioId: number): Promise<APIResponse<AIAnalysis>> => {
  const response = await api.get(`/portfolio/ai/portfolio/${portfolioId}`);
  return response.data;
};

// Screener
export const runScreener = async (filters: {
  pe_min?: number;
  pe_max?: number;
  market_cap_min?: number;
  market_cap_max?: number;
  dividend_yield_min?: number;
  sectors?: string[];
}): Promise<APIResponse<ScreenerResult[]>> => {
  const response = await api.post('/portfolio/screener', filters);
  return response.data;
};

// System
export const getCacheStats = async (): Promise<APIResponse<unknown>> => {
  const response = await api.get('/portfolio/cache/stats');
  return response.data;
};

export const clearCache = async (): Promise<APIResponse<{ message: string }>> => {
  const response = await api.post('/portfolio/cache/clear');
  return response.data;
};

export const getHealth = async (): Promise<APIResponse<{ status: string; service: string; version: string; timestamp: string }>> => {
  const response = await api.get('/portfolio/health');
  return response.data;
};
