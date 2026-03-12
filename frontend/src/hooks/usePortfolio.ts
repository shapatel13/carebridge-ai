import useSWR from 'swr';
import * as api from '../services/portfolioApi';
import type { TimeFrame, Interval } from '../types/portfolio';

// Fetcher function that extracts data from API response
const fetcher = async <T>(promise: Promise<{ data?: T }>): Promise<T> => {
  const response = await promise;
  if (!response.success) {
    throw new Error(response.message || 'API request failed');
  }
  if (response.data === undefined) {
    throw new Error('No data returned from API');
  }
  return response.data;
};

// Market Data Hooks
export const usePrices = (symbol: string | null, period: TimeFrame = '1y', interval: Interval = '1d') => {
  const { data, error, isLoading, mutate } = useSWR(
    symbol ? ['prices', symbol, period, interval] : null,
    () => fetcher(api.getPrices(symbol!, period, interval)),
    {
      refreshInterval: 60000, // Refresh every minute
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  return { data, error, isLoading, refresh: mutate };
};

export const useQuote = (symbol: string | null) => {
  const { data, error, isLoading, mutate } = useSWR(
    symbol ? ['quote', symbol] : null,
    () => fetcher(api.getQuote(symbol!)),
    {
      refreshInterval: 30000, // Refresh every 30 seconds
      revalidateOnFocus: true,
    }
  );

  return { data, error, isLoading, refresh: mutate };
};

export const useMultipleQuotes = (symbols: string[]) => {
  const { data, error, isLoading, mutate } = useSWR(
    symbols.length > 0 ? ['quotes', symbols.join(',')] : null,
    () => fetcher(api.getMultipleQuotes(symbols)),
    {
      refreshInterval: 30000,
      revalidateOnFocus: true,
    }
  );

  return { data, error, isLoading, refresh: mutate };
};

// Analysis Hooks
export const useTechnicalAnalysis = (symbol: string | null, period: TimeFrame = '1y') => {
  const { data, error, isLoading, mutate } = useSWR(
    symbol ? ['technical', symbol, period] : null,
    () => fetcher(api.getTechnicalAnalysis(symbol!, period)),
    {
      refreshInterval: 60000,
      revalidateOnFocus: false,
    }
  );

  return { analysis: data, error, isLoading, refresh: mutate };
};

export const useFundamentals = (symbol: string | null) => {
  const { data, error, isLoading, mutate } = useSWR(
    symbol ? ['fundamentals', symbol] : null,
    () => fetcher(api.getFundamentals(symbol!)),
    {
      refreshInterval: 3600000, // Refresh every hour
      revalidateOnFocus: false,
    }
  );

  return { fundamentals: data, error, isLoading, refresh: mutate };
};

// Portfolio Hooks
export const usePortfolios = () => {
  const { data, error, isLoading, mutate } = useSWR(
    'portfolios',
    () => fetcher(api.getPortfolios()),
    {
      refreshInterval: 30000,
    }
  );

  return { portfolios: data || [], error, isLoading, refresh: mutate };
};

export const usePortfolio = (id: number | null) => {
  const { data, error, isLoading, mutate } = useSWR(
    id ? ['portfolio', id] : null,
    () => fetcher(api.getPortfolio(id!)),
    {
      refreshInterval: 30000,
    }
  );

  return { portfolio: data, error, isLoading, refresh: mutate };
};

export const useRiskAnalysis = (portfolioId: number | null) => {
  const { data, error, isLoading, mutate } = useSWR(
    portfolioId ? ['risk', portfolioId] : null,
    () => fetcher(api.getRiskAnalysis(portfolioId!)),
    {
      refreshInterval: 300000, // Refresh every 5 minutes
      revalidateOnFocus: false,
    }
  );

  return { risk: data, error, isLoading, refresh: mutate };
};

// AI Analysis Hooks
export const useSymbolAI = (symbol: string | null) => {
  const { data, error, isLoading, mutate } = useSWR(
    symbol ? ['ai-symbol', symbol] : null,
    () => fetcher(api.getSymbolAIAnalysis(symbol!)),
    {
      refreshInterval: 300000,
      revalidateOnFocus: false,
    }
  );

  return { aiAnalysis: data, error, isLoading, refresh: mutate };
};

export const usePortfolioAI = (portfolioId: number | null) => {
  const { data, error, isLoading, mutate } = useSWR(
    portfolioId ? ['ai-portfolio', portfolioId] : null,
    () => fetcher(api.getPortfolioAIAnalysis(portfolioId!)),
    {
      refreshInterval: 300000,
      revalidateOnFocus: false,
    }
  );

  return { aiAnalysis: data, error, isLoading, refresh: mutate };
};

// Health check hook
export const useHealth = () => {
  const { data, error } = useSWR(
    'health',
    () => fetcher(api.getHealth()),
    {
      refreshInterval: 30000,
      shouldRetryOnError: false,
    }
  );

  return { health: data, error, isConnected: !!data };
};
