import { useState, useCallback, useRef, useEffect } from 'react';
import { Search, Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { useMultipleQuotes } from '../hooks/usePortfolio';
import { formatCurrency, formatPercentRaw, getChangeColor } from '../utils/formatters';

interface SymbolSearchProps {
  onSelect: (symbol: string) => void;
  value?: string;
  placeholder?: string;
}

const POPULAR_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'V', 'WMT', 'UNH', 'MA'];

export const SymbolSearch = ({ onSelect, value = '', placeholder = 'Search symbol...' }: SymbolSearchProps) => {
  const [query, setQuery] = useState(value);
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const { data: quotes, isLoading } = useMultipleQuotes(POPULAR_SYMBOLS);

  const filteredSymbols = POPULAR_SYMBOLS.filter(sym => 
    sym.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = useCallback((symbol: string) => {
    onSelect(symbol);
    setQuery(symbol);
    setIsOpen(false);
  }, [onSelect]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value.toUpperCase());
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && query) {
              handleSelect(query.toUpperCase());
            }
          }}
          placeholder={placeholder}
          className="w-full pl-10 pr-10 py-2.5 bg-slate-800 border border-slate-700 rounded-xl text-slate-200 
                     placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 
                     focus:border-emerald-500/50 text-sm transition-all"
        />
        {isLoading ? (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 animate-spin" />
        ) : (
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 hidden md:block">
            ⌘K
          </kbd>
        )}
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl 
                        max-h-80 overflow-y-auto animate-in">
          <div className="p-2 text-xs text-slate-500 uppercase tracking-wider font-medium">
            Popular Symbols
          </div>
          {filteredSymbols.length === 0 && (
            <div className="px-4 py-3 text-sm text-slate-400">
              Press Enter to search &quot;{query}&quot;
            </div>
          )}
          {filteredSymbols.map((symbol) => {
            const quote = quotes?.[symbol];
            const price = quote?.regularMarketPrice as number | undefined;
            const change = quote?.regularMarketChangePercent as number | undefined;
            const name = (quote?.longName || quote?.shortName) as string | undefined;
            
            return (
              <button
                key={symbol}
                onClick={() => handleSelect(symbol)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-700/50 
                           transition-colors border-b border-slate-700/50 last:border-0"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono font-semibold text-slate-200">{symbol}</span>
                  <span className="text-sm text-slate-400 truncate max-w-[120px]">
                    {name}
                  </span>
                </div>
                {price ? (
                  <div className="text-right">
                    <div className="font-mono text-sm text-slate-200">{formatCurrency(price)}</div>
                    {change !== undefined && (
                      <div className={`text-xs flex items-center justify-end gap-0.5 ${getChangeColor(change)}`}>
                        {change > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        {formatPercentRaw(change, 1)}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-slate-500">Loading...</div>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
