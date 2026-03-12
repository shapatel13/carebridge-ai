"""Portfolio risk analysis module."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats

from ..models.schemas import (
    RiskMetrics,
    CorrelationMatrix,
    ConcentrationRisk,
    RiskAnalysis,
    RiskLevel,
    PortfolioHolding,
)
from ..services.yfinance_client import YFinanceClient

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    Portfolio risk analysis engine.
    
    Calculates VaR, CVaR, Sharpe ratio, correlation matrices,
    and concentration risk metrics.
    """
    
    def __init__(self, yf_client: Optional[YFinanceClient] = None):
        """
        Initialize risk analyzer.
        
        Args:
            yf_client: Yahoo Finance client for fetching data
        """
        self.yf = yf_client or YFinanceClient()
    
    async def analyze_portfolio(
        self,
        portfolio_id: int,
        holdings: List[Any],  # PortfolioHolding objects
        risk_free_rate: float = 0.045,  # Current approx risk-free rate
        confidence_level: float = 0.95,
    ) -> RiskAnalysis:
        """
        Perform comprehensive risk analysis on portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            holdings: List of portfolio holdings
            risk_free_rate: Annual risk-free rate for Sharpe calc
            confidence_level: Confidence level for VaR/CVaR
            
        Returns:
            RiskAnalysis object
        """
        if not holdings:
            return self._empty_analysis(portfolio_id)
        
        # Fetch historical price data for all holdings
        symbols = [h.symbol for h in holdings]
        price_data = await self._fetch_price_data(symbols)
        
        if not price_data:
            return self._empty_analysis(portfolio_id)
        
        # Calculate portfolio weights
        weights = self._calculate_weights(holdings, price_data)
        
        # Build returns matrix
        returns_df = self._build_returns_matrix(price_data)
        
        if returns_df.empty:
            return self._empty_analysis(portfolio_id)
        
        # Calculate metrics
        metrics = self._calculate_risk_metrics(
            returns_df, weights, risk_free_rate, confidence_level
        )
        
        correlation = self._calculate_correlation(returns_df)
        concentration = self._calculate_concentration(holdings, weights, price_data)
        
        # Determine risk level
        risk_level = self._assess_risk_level(metrics, concentration)
        
        # Generate alerts and recommendations
        alerts = self._generate_alerts(metrics, correlation, concentration, weights)
        recommendations = self._generate_recommendations(
            metrics, correlation, concentration, weights
        )
        
        return RiskAnalysis(
            portfolio_id=portfolio_id,
            risk_level=risk_level,
            metrics=metrics,
            correlation=correlation,
            concentration=concentration,
            alerts=alerts,
            recommendations=recommendations,
        )
    
    async def _fetch_price_data(
        self,
        symbols: List[str],
        period: str = "1y"
    ) -> Dict[str, pd.Series]:
        """
        Fetch historical price data for symbols.
        
        Returns:
            Dictionary mapping symbol to price series
        """
        price_data = {}
        
        for symbol in symbols:
            try:
                data = await self.yf.get_price_history(symbol, period=period)
                ohlcv = self.yf.parse_ohlcv(data)
                
                if ohlcv:
                    # Use adjusted close for accurate returns
                    closes = pd.Series(
                        [p.get('adjusted_close') or p['close'] for p in ohlcv],
                        index=[p['timestamp'] for p in ohlcv]
                    )
                    price_data[symbol] = closes.sort_index()
                    
            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
                continue
        
        return price_data
    
    def _calculate_weights(
        self,
        holdings: List[Any],
        price_data: Dict[str, pd.Series]
    ) -> Dict[str, float]:
        """
        Calculate portfolio weights based on current market values.
        
        Returns:
            Dictionary mapping symbol to weight
        """
        market_values = {}
        
        for holding in holdings:
            if holding.symbol in price_data:
                current_price = price_data[holding.symbol].iloc[-1]
                market_values[holding.symbol] = float(holding.shares) * current_price
        
        total_value = sum(market_values.values())
        
        if total_value == 0:
            return {h.symbol: 1.0 / len(holdings) for h in holdings}
        
        return {
            symbol: value / total_value
            for symbol, value in market_values.items()
        }
    
    def _build_returns_matrix(
        self,
        price_data: Dict[str, pd.Series]
    ) -> pd.DataFrame:
        """
        Build matrix of daily returns.
        
        Returns:
            DataFrame with daily returns for each symbol
        """
        # Align all series to common dates
        df = pd.DataFrame(price_data)
        
        # Calculate daily returns
        returns = df.pct_change().dropna()
        
        return returns
    
    def _calculate_risk_metrics(
        self,
        returns_df: pd.DataFrame,
        weights: Dict[str, float],
        risk_free_rate: float,
        confidence: float,
    ) -> RiskMetrics:
        """
        Calculate portfolio risk metrics.
        
        Args:
            returns_df: DataFrame of daily returns
            weights: Portfolio weights
            risk_free_rate: Annual risk-free rate
            confidence: Confidence level for VaR
            
        Returns:
            RiskMetrics object
        """
        # Filter weights to available symbols
        available_weights = np.array([
            weights.get(col, 0) for col in returns_df.columns
        ])
        available_weights = available_weights / available_weights.sum()  # Renormalize
        
        # Portfolio returns (weighted)
        portfolio_returns = (returns_df * available_weights).sum(axis=1)
        
        # Annualized volatility
        daily_vol = portfolio_returns.std()
        annual_vol = daily_vol * np.sqrt(252)
        
        # Sharpe ratio
        annual_return = portfolio_returns.mean() * 252
        sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_dev = downside_returns.std() * np.sqrt(252)
        sortino = (annual_return - risk_free_rate) / downside_dev if downside_dev > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # VaR (historical simulation)
        var = np.percentile(portfolio_returns, (1 - confidence) * 100)
        annual_var = var * np.sqrt(252)
        
        # CVaR (Expected Shortfall)
        cvar = portfolio_returns[portfolio_returns <= var].mean()
        annual_cvar = cvar * np.sqrt(252) if not pd.isna(cvar) else var * np.sqrt(252)
        
        # Calmar ratio
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Beta and Alpha (relative to SPY if available)
        beta = None
        alpha = None
        treynor = None
        
        if 'SPY' in returns_df.columns:
            spy_returns = returns_df['SPY']
            
            # Calculate beta
            covariance = portfolio_returns.cov(spy_returns)
            spy_variance = spy_returns.var()
            beta = covariance / spy_variance if spy_variance > 0 else 1.0
            
            # Calculate alpha (Jensen's alpha)
            spy_annual_return = spy_returns.mean() * 252
            alpha = annual_return - (risk_free_rate + beta * (spy_annual_return - risk_free_rate))
            
            # Treynor ratio
            treynor = (annual_return - risk_free_rate) / beta if beta != 0 else 0
        
        return RiskMetrics(
            volatility_annual=round(annual_vol, 4),
            beta=round(beta, 4) if beta else None,
            alpha=round(alpha, 4) if alpha else None,
            sharpe_ratio=round(sharpe, 4),
            sortino_ratio=round(sortino, 4),
            max_drawdown=round(max_drawdown, 4),
            var_95=round(annual_var, 4),
            cvar_95=round(annual_cvar, 4),
            calmar_ratio=round(calmar, 4),
            treynor_ratio=round(treynor, 4) if treynor else None,
        )
    
    def _calculate_correlation(self, returns_df: pd.DataFrame) -> CorrelationMatrix:
        """
        Calculate correlation matrix.
        
        Args:
            returns_df: DataFrame of daily returns
            
        Returns:
            CorrelationMatrix object
        """
        corr_matrix = returns_df.corr()
        
        return CorrelationMatrix(
            symbols=list(corr_matrix.columns),
            matrix=corr_matrix.values.tolist(),
        )
    
    def _calculate_concentration(
        self,
        holdings: List[Any],
        weights: Dict[str, float],
        price_data: Dict[str, pd.Series]
    ) -> ConcentrationRisk:
        """
        Calculate concentration risk metrics.
        
        Returns:
            ConcentrationRisk object
        """
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        # Top holding percentage
        top_holding_pct = sorted_weights[0][1] * 100 if sorted_weights else 0
        
        # Top 5 holdings percentage
        top_5_pct = sum(w for _, w in sorted_weights[:5]) * 100
        
        # Herfindahl-Hirschman Index (HHI)
        hhi = sum(w ** 2 for w in weights.values())
        
        # Sector concentration (would need sector data - simplified here)
        # For now, equal distribution assumed
        sector_concentration = {"Unknown": 100.0}
        
        return ConcentrationRisk(
            top_holding_percent=round(top_holding_pct, 2),
            top_5_holdings_percent=round(top_5_pct, 2),
            sector_concentration=sector_concentration,
            herfindahl_index=round(hhi, 4),
        )
    
    def _assess_risk_level(
        self,
        metrics: RiskMetrics,
        concentration: ConcentrationRisk,
    ) -> RiskLevel:
        """
        Assess overall risk level.
        
        Returns:
            RiskLevel enum
        """
        score = 0
        
        # Volatility scoring
        if metrics.volatility_annual < 0.15:
            score += 1
        elif metrics.volatility_annual < 0.25:
            score += 2
        else:
            score += 3
        
        # Max drawdown scoring
        if metrics.max_drawdown > -0.10:
            score += 1
        elif metrics.max_drawdown > -0.20:
            score += 2
        else:
            score += 3
        
        # Concentration scoring
        if concentration.top_holding_percent < 15:
            score += 1
        elif concentration.top_holding_percent < 30:
            score += 2
        else:
            score += 3
        
        # Sharpe ratio (lower is riskier)
        if metrics.sharpe_ratio > 1.0:
            score -= 1
        elif metrics.sharpe_ratio < 0.5:
            score += 1
        
        # Map score to risk level
        if score <= 4:
            return RiskLevel.LOW
        elif score <= 7:
            return RiskLevel.MODERATE
        elif score <= 10:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    def _generate_alerts(
        self,
        metrics: RiskMetrics,
        correlation: CorrelationMatrix,
        concentration: ConcentrationRisk,
        weights: Dict[str, float],
    ) -> List[str]:
        """Generate risk alerts."""
        alerts = []
        
        # Volatility alert
        if metrics.volatility_annual > 0.30:
            alerts.append(f"High volatility: {metrics.volatility_annual:.1%} annualized")
        
        # Drawdown alert
        if metrics.max_drawdown < -0.25:
            alerts.append(f"Significant drawdown risk: {metrics.max_drawdown:.1%}")
        
        # Concentration alert
        if concentration.top_holding_percent > 25:
            alerts.append(f"High concentration: {concentration.top_holding_percent:.1f}% in top holding")
        
        # Correlation alert
        corr_matrix = np.array(correlation.matrix)
        if corr_matrix.size > 0:
            # Find highest off-diagonal correlation
            np.fill_diagonal(corr_matrix, 0)
            max_corr = np.max(np.abs(corr_matrix))
            if max_corr > 0.8:
                alerts.append(f"High correlation detected: {max_corr:.2f} between assets")
        
        # Sharpe ratio alert
        if metrics.sharpe_ratio < 0.5:
            alerts.append(f"Low risk-adjusted returns: Sharpe {metrics.sharpe_ratio:.2f}")
        
        # VaR alert
        if abs(metrics.var_95) > 0.20:
            alerts.append(f"High VaR: Potential {abs(metrics.var_95):.1%} loss at 95% confidence")
        
        return alerts
    
    def _generate_recommendations(
        self,
        metrics: RiskMetrics,
        correlation: CorrelationMatrix,
        concentration: ConcentrationRisk,
        weights: Dict[str, float],
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        # Diversification recommendations
        if concentration.herfindahl_index > 0.3:
            recommendations.append("Consider diversifying to reduce concentration risk")
        
        # Correlation-based recommendations
        corr_matrix = np.array(correlation.matrix)
        if corr_matrix.size > 0:
            np.fill_diagonal(corr_matrix, 0)
            max_corr_idx = np.unravel_index(np.argmax(np.abs(corr_matrix)), corr_matrix.shape)
            if np.abs(corr_matrix[max_corr_idx]) > 0.8:
                sym1 = correlation.symbols[max_corr_idx[0]]
                sym2 = correlation.symbols[max_corr_idx[1]]
                recommendations.append(f"{sym1} and {sym2} are highly correlated - consider consolidating")
        
        # Risk-return optimization
        if metrics.sharpe_ratio < 0.5 and metrics.volatility_annual > 0.20:
            recommendations.append("Portfolio may benefit from lower-risk assets or hedging")
        
        # Rebalancing recommendation
        max_weight = max(weights.values()) if weights else 0
        if max_weight > 0.20:
            recommendations.append("Consider rebalancing to reduce single-name exposure")
        
        return recommendations
    
    def _empty_analysis(self, portfolio_id: int) -> RiskAnalysis:
        """Return empty analysis for portfolio with no data."""
        return RiskAnalysis(
            portfolio_id=portfolio_id,
            risk_level=RiskLevel.LOW,
            metrics=RiskMetrics(
                volatility_annual=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                max_drawdown=0.0,
                var_95=0.0,
                cvar_95=0.0,
                calmar_ratio=0.0,
            ),
            correlation=CorrelationMatrix(symbols=[], matrix=[]),
            concentration=ConcentrationRisk(
                top_holding_percent=0.0,
                top_5_holdings_percent=0.0,
                sector_concentration={},
                herfindahl_index=0.0,
            ),
            alerts=["Portfolio has no holdings with available price data"],
            recommendations=["Add holdings to analyze portfolio risk"],
        )
