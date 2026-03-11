"""Yahoo Finance data fetcher with caching and rate limiting."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

import httpx

from .cache_manager import CacheManager
from .rate_limiter import RateLimiter, get_rate_limiter

logger = logging.getLogger(__name__)


class YFinanceClient:
    """
    Yahoo Finance data client with caching and rate limiting.
    
    Uses Yahoo Finance API (unofficial) via HTTP requests.
    Implements intelligent caching and respectful rate limiting.
    """
    
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    QUOTE_URL = "https://query2.finance.yahoo.com/v7/finance/quote"
    FUNDAMENTALS_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary"
    
    # Default headers to appear more like a browser
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://finance.yahoo.com/",
    }
    
    def __init__(
        self,
        cache: Optional[CacheManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        timeout: float = 30.0
    ):
        """
        Initialize Yahoo Finance client.
        
        Args:
            cache: Cache manager instance
            rate_limiter: Rate limiter instance
            timeout: Request timeout in seconds
        """
        self.cache = cache or CacheManager()
        self.rate_limiter = rate_limiter or get_rate_limiter()
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.DEFAULT_HEADERS,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _get_cache_key(self, symbol: str, data_type: str, **params) -> str:
        """Generate cache key for request."""
        param_str = ":".join(f"{k}={v}" for k, v in sorted(params.items()))
        return self.cache.get_cache_key("yfinance", data_type, symbol, param_str)
    
    async def _fetch(
        self,
        url: str,
        params: Dict[str, Any],
        service: str = "yfinance"
    ) -> Dict[str, Any]:
        """
        Make rate-limited HTTP request.
        
        Args:
            url: Request URL
            params: Query parameters
            service: Service identifier for rate limiting
            
        Returns:
            JSON response as dictionary
        """
        async def do_request():
            client = await self._get_client()
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        return await self.rate_limiter.call_with_retry(do_request, service)
    
    async def get_price_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch historical price data.
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            use_cache: Whether to use cached data
            
        Returns:
            Price history data with OHLCV
        """
        symbol = symbol.upper().strip()
        cache_key = self._get_cache_key(symbol, "prices", period=period, interval=interval)
        
        # Check cache
        if use_cache:
            cached, is_stale = self.cache.get(cache_key, allow_stale=True)
            if cached and not is_stale:
                logger.debug(f"Cache hit for {symbol} prices")
                return cached
        
        # Fetch from API
        params = {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "events": "div,splits",
            "includeAdjustedClose": "true",
        }
        
        try:
            data = await self._fetch(self.BASE_URL, params, "yfinance_prices")
            
            # Validate response
            if not data or "chart" not in data or "result" not in data["chart"]:
                raise ValueError(f"Invalid response for {symbol}")
            
            result = data["chart"]["result"]
            if not result:
                raise ValueError(f"No data available for {symbol}")
            
            # Cache the result
            if use_cache:
                self.cache.set(cache_key, data, "yfinance_prices")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch prices for {symbol}: {e}")
            # Return cached data even if stale
            if use_cache:
                cached, _ = self.cache.get(cache_key, allow_stale=True)
                if cached:
                    logger.warning(f"Returning stale cache for {symbol}")
                    return cached
            raise
    
    async def get_quote(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get current quote for symbol.
        
        Args:
            symbol: Stock symbol
            use_cache: Whether to use cached data
            
        Returns:
            Quote data
        """
        symbol = symbol.upper().strip()
        cache_key = self._get_cache_key(symbol, "quote")
        
        # Check cache (shorter TTL for quotes)
        if use_cache:
            cached, is_stale = self.cache.get(cache_key, allow_stale=True)
            if cached and not is_stale:
                return cached
        
        params = {"symbols": symbol}
        
        try:
            data = await self._fetch(self.QUOTE_URL, params, "yfinance_quote")
            
            if not data or "quoteResponse" not in data:
                raise ValueError(f"Invalid quote response for {symbol}")
            
            result = data["quoteResponse"]["result"]
            if not result:
                raise ValueError(f"No quote data for {symbol}")
            
            # Cache with shorter TTL (5 minutes)
            if use_cache:
                self.cache.set(cache_key, data, "yfinance_quote", ttl=300)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch quote for {symbol}: {e}")
            if use_cache:
                cached, _ = self.cache.get(cache_key, allow_stale=True)
                if cached:
                    return cached
            raise
    
    async def get_fundamentals(
        self,
        symbol: str,
        modules: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch fundamental data.
        
        Args:
            symbol: Stock symbol
            modules: Data modules to fetch (defaults to common ones)
            use_cache: Whether to use cached data
            
        Returns:
            Fundamental data
        """
        symbol = symbol.upper().strip()
        cache_key = self._get_cache_key(symbol, "fundamentals", modules=",".join(modules or []))
        
        if use_cache:
            cached, is_stale = self.cache.get(cache_key, allow_stale=True)
            if cached and not is_stale:
                return cached
        
        # Default modules if not specified
        if modules is None:
            modules = [
                "assetProfile",
                "financialData",
                "defaultKeyStatistics",
                "incomeStatementHistory",
                "balanceSheetHistory",
                "cashflowStatementHistory",
                "earnings",
                "earningsHistory",
                "calendarEvents",
                "esgScores",
                "secFilings",
            ]
        
        params = {
            "symbol": symbol,
            "modules": ",".join(modules),
        }
        
        try:
            data = await self._fetch(self.FUNDAMENTALS_URL, params, "yfinance_fundamentals")
            
            if not data or "quoteSummary" not in data:
                raise ValueError(f"Invalid fundamentals response for {symbol}")
            
            result = data["quoteSummary"]["result"]
            if not result:
                raise ValueError(f"No fundamentals data for {symbol}")
            
            if use_cache:
                self.cache.set(cache_key, data, "yfinance_fundamentals")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {symbol}: {e}")
            if use_cache:
                cached, _ = self.cache.get(cache_key, allow_stale=True)
                if cached:
                    return cached
            raise
    
    async def get_multiple_quotes(
        self,
        symbols: List[str],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get quotes for multiple symbols efficiently.
        
        Args:
            symbols: List of stock symbols
            use_cache: Whether to use cached data
            
        Returns:
            Dictionary mapping symbol to quote data
        """
        # Yahoo Finance supports up to ~100 symbols in one request
        symbols_str = ",".join(s.upper().strip() for s in symbols)
        cache_key = self._get_cache_key("batch", "quotes", symbols=symbols_str)
        
        if use_cache:
            cached, is_stale = self.cache.get(cache_key, allow_stale=True)
            if cached and not is_stale:
                return cached
        
        params = {"symbols": symbols_str}
        
        try:
            data = await self._fetch(self.QUOTE_URL, params, "yfinance_quotes")
            
            result = data.get("quoteResponse", {}).get("result", [])
            quotes = {item["symbol"]: item for item in result}
            
            if use_cache:
                self.cache.set(cache_key, quotes, "yfinance_quotes", ttl=300)
            
            return quotes
            
        except Exception as e:
            logger.error(f"Failed to fetch batch quotes: {e}")
            # Fallback to individual requests
            logger.info("Falling back to individual quote requests")
            results = {}
            for symbol in symbols:
                try:
                    quote_data = await self.get_quote(symbol, use_cache=use_cache)
                    result = quote_data.get("quoteResponse", {}).get("result", [])
                    if result:
                        results[symbol] = result[0]
                except Exception as inner_e:
                    logger.warning(f"Failed to fetch quote for {symbol}: {inner_e}")
            return results
    
    def parse_ohlcv(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse OHLCV data from Yahoo Finance response.
        
        Args:
            data: Raw API response
            
        Returns:
            List of OHLCV data points
        """
        result = data.get("chart", {}).get("result", [{}])[0]
        
        timestamps = result.get("timestamp", [])
        quote = result.get("indicators", {}).get("quote", [{}])[0]
        adjclose = result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [])
        
        ohlcv_data = []
        for i, ts in enumerate(timestamps):
            if ts is None:
                continue
                
            point = {
                "timestamp": datetime.fromtimestamp(ts),
                "open": quote.get("open", [])[i] if i < len(quote.get("open", [])) else None,
                "high": quote.get("high", [])[i] if i < len(quote.get("high", [])) else None,
                "low": quote.get("low", [])[i] if i < len(quote.get("low", [])) else None,
                "close": quote.get("close", [])[i] if i < len(quote.get("close", [])) else None,
                "volume": quote.get("volume", [])[i] if i < len(quote.get("volume", [])) else None,
                "adjusted_close": adjclose[i] if i < len(adjclose) else None,
            }
            
            # Skip incomplete data points
            if all(v is not None for v in [point["open"], point["high"], point["low"], point["close"]]):
                ohlcv_data.append(point)
        
        return ohlcv_data


# Global client instance
_client_instance: Optional[YFinanceClient] = None


async def get_yfinance_client(
    cache: Optional[CacheManager] = None,
    rate_limiter: Optional[RateLimiter] = None
) -> YFinanceClient:
    """Get or create global Yahoo Finance client."""
    global _client_instance
    if _client_instance is None:
        _client_instance = YFinanceClient(cache, rate_limiter)
    return _client_instance
