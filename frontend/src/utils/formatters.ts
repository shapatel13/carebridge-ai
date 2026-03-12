export const formatCurrency = (value: number | undefined | null, decimals = 2): string => {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatNumber = (value: number | undefined | null, decimals = 2): string => {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatCompactNumber = (value: number | undefined | null): string => {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(value);
};

export const formatPercent = (value: number | undefined | null, decimals = 2, includeSign = true): string => {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    signDisplay: includeSign ? 'exceptZero' : 'never',
  }).format(value / 100);
};

export const formatPercentRaw = (value: number | undefined | null, decimals = 2, includeSign = true): string => {
  if (value === undefined || value === null || isNaN(value)) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    signDisplay: includeSign ? 'exceptZero' : 'never',
  }).format(value);
};

export const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return 'N/A';
  }
};

export const formatDateTime = (dateString: string | undefined): string => {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'N/A';
  }
};

// Color utilities for signals
export const getSignalColor = (signal: string): string => {
  switch (signal) {
    case 'strong_buy':
    case 'buy':
      return 'text-emerald-400';
    case 'strong_sell':
    case 'sell':
      return 'text-rose-400';
    default:
      return 'text-amber-400';
  }
};

export const getSignalBgColor = (signal: string): string => {
  switch (signal) {
    case 'strong_buy':
      return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    case 'buy':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    case 'strong_sell':
      return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
    case 'sell':
      return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    default:
      return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
  }
};

export const getChangeColor = (value: number | undefined): string => {
  if (value === undefined || value === null) return 'text-slate-400';
  if (value > 0) return 'text-emerald-400';
  if (value < 0) return 'text-rose-400';
  return 'text-slate-400';
};

export const getChangeBgColor = (value: number | undefined): string => {
  if (value === undefined || value === null) return 'bg-slate-500/10';
  if (value > 0) return 'bg-emerald-500/10';
  if (value < 0) return 'bg-rose-500/10';
  return 'bg-slate-500/10';
};

export const getRiskLevelColor = (level: string): string => {
  switch (level) {
    case 'low':
      return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    case 'moderate':
      return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    case 'high':
      return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
    case 'extreme':
      return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    default:
      return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
  }
};

export const getSentimentColor = (sentiment: string): string => {
  switch (sentiment) {
    case 'positive':
      return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    case 'negative':
      return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    case 'caution':
      return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    default:
      return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
  }
};
