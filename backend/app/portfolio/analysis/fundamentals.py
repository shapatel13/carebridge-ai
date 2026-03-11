"""Fundamental analysis module - Yahoo Finance + EDGAR hybrid."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..models.schemas import (
    CompanyInfo,
    DividendInfo,
    FundamentalAnalysis,
    FinancialHealthMetrics,
    GrowthMetrics,
    OwnershipInfo,
    ProfitabilityMetrics,
    ValuationMetrics,
)
from ..services.yfinance_client import YFinanceClient
from ..services.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """
    Fundamental analysis engine using Yahoo Finance data.
    
    Extracts and calculates key financial metrics for stock valuation.
    """
    
    def __init__(self, yf_client: Optional[YFinanceClient] = None):
        """
        Initialize fundamental analyzer.
        
        Args:
            yf_client: Yahoo Finance client instance
        """
        self.yf = yf_client or YFinanceClient()
    
    def _safe_get(self, data: Dict, *keys, default=None) -> Any:
        """Safely navigate nested dictionary."""
        for key in keys:
            if not isinstance(data, dict):
                return default
            data = data.get(key, default)
            if data is None:
                return default
        return data
    
    def _parse_number(self, value: Any) -> Optional[float]:
        """Parse numeric value, handling Yahoo's format."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            raw = value.get('raw')
            if raw is not None:
                return float(raw)
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    async def analyze(self, symbol: str) -> FundamentalAnalysis:
        """
        Perform comprehensive fundamental analysis.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            FundamentalAnalysis object
        """
        symbol = symbol.upper().strip()
        
        try:
            # Fetch data
            fundamentals = await self.yf.get_fundamentals(symbol)
            quote = await self.yf.get_quote(symbol)
            
            # Parse components
            result = fundamentals.get('quoteSummary', {}).get('result', [{}])[0]
            quote_result = quote.get('quoteResponse', {}).get('result', [{}])[0]
            
            company = self._parse_company_info(symbol, result, quote_result)
            valuation = self._parse_valuation_metrics(result, quote_result)
            profitability = self._parse_profitability_metrics(result)
            financial_health = self._parse_financial_health(result)
            growth = self._parse_growth_metrics(result)
            dividend = self._parse_dividend_info(result, quote_result)
            ownership = self._parse_ownership(result, quote_result)
            
            # Calculate data quality score
            quality_score = self._calculate_quality_score(
                valuation, profitability, financial_health, growth
            )
            
            return FundamentalAnalysis(
                symbol=symbol,
                company=company,
                valuation=valuation,
                profitability=profitability,
                financial_health=financial_health,
                growth=growth,
                dividend=dividend,
                ownership=ownership,
                fetched_at=datetime.utcnow(),
                data_quality_score=quality_score,
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze fundamentals for {symbol}: {e}")
            raise
    
    def _parse_company_info(
        self,
        symbol: str,
        result: Dict,
        quote: Dict
    ) -> CompanyInfo:
        """Extract company information."""
        profile = result.get('assetProfile', {})
        
        return CompanyInfo(
            symbol=symbol,
            name=quote.get('longName') or quote.get('shortName', symbol),
            sector=profile.get('sector'),
            industry=profile.get('industry'),
            country=profile.get('country'),
            website=profile.get('website'),
            employees=self._parse_number(profile.get('fullTimeEmployees')),
            description=profile.get('longBusinessSummary'),
        )
    
    def _parse_valuation_metrics(
        self,
        result: Dict,
        quote: Dict
    ) -> ValuationMetrics:
        """Extract valuation metrics."""
        stats = result.get('defaultKeyStatistics', {})
        financial = result.get('financialData', {})
        
        market_cap = self._parse_number(quote.get('marketCap'))
        
        # Calculate EV/EBITDA if not directly available
        ev = self._parse_number(stats.get('enterpriseValue'))
        ebitda = self._parse_number(financial.get('ebitda'))
        ev_ebitda = ev / ebitda if ev and ebitda else None
        
        # Calculate EV/Revenue
        revenue = self._parse_number(financial.get('totalRevenue'))
        ev_revenue = ev / revenue if ev and revenue else None
        
        return ValuationMetrics(
            market_cap=market_cap,
            enterprise_value=ev,
            trailing_pe=self._parse_number(quote.get('trailingPE')),
            forward_pe=self._parse_number(quote.get('forwardPE')),
            peg_ratio=self._parse_number(stats.get('pegRatio')),
            price_to_book=self._parse_number(quote.get('priceToBook')),
            price_to_sales=self._parse_number(quote.get('priceToSalesTrailing12Months')),
            ev_to_ebitda=ev_ebitda,
            ev_to_revenue=ev_revenue,
        )
    
    def _parse_profitability_metrics(self, result: Dict) -> ProfitabilityMetrics:
        """Extract profitability metrics."""
        financial = result.get('financialData', {})
        stats = result.get('defaultKeyStatistics', {})
        
        # ROE from stats or calculate
        roe = self._parse_number(stats.get('returnOnEquity'))
        if roe and roe < 1:  # Yahoo sometimes returns as decimal
            roe *= 100
        
        # ROA
        roa = self._parse_number(stats.get('returnOnAssets'))
        if roa and roa < 1:
            roa *= 100
        
        # ROIC - may need to calculate
        roic = self._parse_number(financial.get('returnOnAssets'))  # Fallback
        
        # Margins
        gross_margin = self._parse_number(financial.get('grossMargins'))
        if gross_margin and gross_margin < 1:
            gross_margin *= 100
            
        operating_margin = self._parse_number(financial.get('operatingMargins'))
        if operating_margin and operating_margin < 1:
            operating_margin *= 100
            
        profit_margin = self._parse_number(financial.get('profitMargins'))
        if profit_margin and profit_margin < 1:
            profit_margin *= 100
        
        # EBITDA margin
        ebitda = self._parse_number(financial.get('ebitda'))
        revenue = self._parse_number(financial.get('totalRevenue'))
        ebitda_margin = (ebitda / revenue * 100) if ebitda and revenue else None
        
        # FCF Yield
        fcf = self._parse_number(financial.get('freeCashflow'))
        market_cap = self._parse_number(result.get('price', {}).get('regularMarketMarketCap'))
        fcf_yield = (fcf / market_cap * 100) if fcf and market_cap else None
        
        return ProfitabilityMetrics(
            roe=roe,
            roa=roa,
            roic=roic,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            profit_margin=profit_margin,
            ebitda_margin=ebitda_margin,
            fcf_yield=fcf_yield,
        )
    
    def _parse_financial_health(self, result: Dict) -> FinancialHealthMetrics:
        """Extract financial health metrics."""
        financial = result.get('financialData', {})
        bs = result.get('balanceSheetHistory', {}).get('balanceSheetStatements', [])
        
        # Current financials
        current_ratio = self._parse_number(financial.get('currentRatio'))
        quick_ratio = self._parse_number(financial.get('quickRatio'))
        debt_to_equity = self._parse_number(financial.get('debtToEquity'))
        if debt_to_equity and debt_to_equity > 10:  # Yahoo returns as percentage sometimes
            debt_to_equity /= 100
        
        # Interest coverage
        interest_coverage = self._parse_number(financial.get('interestCoverage'))
        
        # Cash flows
        operating_cf = self._parse_number(financial.get('operatingCashflow'))
        free_cf = self._parse_number(financial.get('freeCashflow'))
        
        # Debt to assets from balance sheet
        debt_to_assets = None
        if bs:
            latest = bs[0]
            total_debt = self._parse_number(latest.get('totalDebt'))
            total_assets = self._parse_number(latest.get('totalAssets'))
            if total_debt and total_assets:
                debt_to_assets = total_debt / total_assets
        
        return FinancialHealthMetrics(
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            debt_to_equity=debt_to_equity,
            debt_to_assets=debt_to_assets,
            interest_coverage=interest_coverage,
            operating_cashflow=operating_cf,
            free_cashflow=free_cf,
        )
    
    def _parse_growth_metrics(self, result: Dict) -> GrowthMetrics:
        """Extract growth metrics."""
        stats = result.get('defaultKeyStatistics', {})
        earnings = result.get('earnings', {})
        earnings_history = result.get('earningsHistory', {}).get('history', [])
        
        # Yahoo's growth estimates
        rev_growth = self._parse_number(stats.get('revenueGrowth'))
        if rev_growth and rev_growth < 1:
            rev_growth *= 100
            
        earnings_growth = self._parse_number(stats.get('earningsGrowth'))
        if earnings_growth and earnings_growth < 1:
            earnings_growth *= 100
        
        # Calculate 3-year CAGR from earnings history
        rev_cagr = None
        earnings_cagr = None
        
        if len(earnings_history) >= 3:
            try:
                # Sort by date
                sorted_history = sorted(
                    earnings_history,
                    key=lambda x: x.get('quarter', ''),
                    reverse=True
                )
                
                # Get EPS values
                eps_values = [
                    self._parse_number(h.get('epsActual'))
                    for h in sorted_history
                    if self._parse_number(h.get('epsActual')) is not None
                ]
                
                if len(eps_values) >= 4:  # At least a year of data
                    # Calculate 3-year CAGR if we have enough data
                    recent = eps_values[0]
                    older = eps_values[-1]
                    if recent and older and older > 0:
                        years = len(eps_values) / 4  # Approximate years
                        earnings_cagr = ((recent / older) ** (1/years) - 1) * 100
                        
            except Exception as e:
                logger.warning(f"Failed to calculate CAGR: {e}")
        
        # Analyst estimates
        earnings_trend = result.get('earningsTrend', {}).get('trend', [])
        analyst_rev_growth = None
        analyst_earnings_growth = None
        
        if earnings_trend:
            for trend in earnings_trend:
                if trend.get('period') == '+1y':
                    growth = self._parse_number(trend.get('growth'))
                    if growth:
                        analyst_earnings_growth = growth * 100 if growth < 1 else growth
                    break
        
        return GrowthMetrics(
            revenue_growth_yoy=rev_growth,
            earnings_growth_yoy=earnings_growth,
            revenue_growth_3yr_cagr=rev_cagr,
            earnings_growth_3yr_cagr=earnings_cagr,
            analyst_revenue_growth_next_yr=analyst_rev_growth,
            analyst_earnings_growth_next_yr=analyst_earnings_growth,
        )
    
    def _parse_dividend_info(self, result: Dict, quote: Dict) -> DividendInfo:
        """Extract dividend information."""
        stats = result.get('defaultKeyStatistics', {})
        calendar = result.get('calendarEvents', {})
        
        # Current dividend
        div_rate = self._parse_number(quote.get('dividendRate'))
        div_yield = self._parse_number(quote.get('dividendYield'))
        if div_yield and div_yield < 1:
            div_yield *= 100
        
        # Payout ratio
        payout = self._parse_number(stats.get('payoutRatio'))
        if payout and payout < 1:
            payout *= 100
        
        # Dates
        ex_date = calendar.get('exDividendDate')
        div_date = calendar.get('dividendDate')
        
        # 5-year average yield
        avg_yield = self._parse_number(stats.get('fiveYearAvgDividendYield'))
        
        return DividendInfo(
            dividend_rate=div_rate,
            dividend_yield=div_yield,
            payout_ratio=payout,
            ex_dividend_date=datetime.fromtimestamp(ex_date) if isinstance(ex_date, (int, float)) else None,
            dividend_date=datetime.fromtimestamp(div_date) if isinstance(div_date, (int, float)) else None,
            five_year_avg_dividend_yield=avg_yield,
        )
    
    def _parse_ownership(self, result: Dict, quote: Dict) -> OwnershipInfo:
        """Extract ownership information."""
        stats = result.get('defaultKeyStatistics', {})
        
        insider = self._parse_number(stats.get('heldPercentInsiders'))
        if insider and insider < 1:
            insider *= 100
            
        institutional = self._parse_number(stats.get('heldPercentInstitutions'))
        if institutional and institutional < 1:
            institutional *= 100
        
        short_float = self._parse_number(stats.get('shortPercentOfFloat'))
        if short_float and short_float < 1:
            short_float *= 100
            
        short_outstanding = self._parse_number(stats.get('shortPercentOutstanding'))
        if short_outstanding and short_outstanding < 1:
            short_outstanding *= 100
        
        shares_out = self._parse_number(quote.get('sharesOutstanding'))
        float_shares = self._parse_number(stats.get('floatShares'))
        
        return OwnershipInfo(
            insider_ownership=insider,
            institutional_ownership=institutional,
            short_percent_float=short_float,
            short_percent_outstanding=short_outstanding,
            shares_outstanding=shares_out,
            float_shares=float_shares,
        )
    
    def _calculate_quality_score(
        self,
        valuation: ValuationMetrics,
        profitability: ProfitabilityMetrics,
        financial_health: FinancialHealthMetrics,
        growth: GrowthMetrics,
    ) -> float:
        """
        Calculate data quality score based on available metrics.
        
        Returns:
            Score between 0 and 1
        """
        total_fields = 0
        filled_fields = 0
        
        # Check each metric object
        for obj in [valuation, profitability, financial_health, growth]:
            for value in obj.model_dump().values():
                total_fields += 1
                if value is not None:
                    filled_fields += 1
        
        return round(filled_fields / total_fields, 2) if total_fields > 0 else 0.0
    
    async def batch_analyze(
        self,
        symbols: List[str]
    ) -> Dict[str, FundamentalAnalysis]:
        """
        Analyze multiple symbols efficiently.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbol to analysis
        """
        results = {}
        
        for symbol in symbols:
            try:
                analysis = await self.analyze(symbol)
                results[symbol] = analysis
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                results[symbol] = None
        
        return results
