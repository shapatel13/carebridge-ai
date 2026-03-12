"""AI-powered analysis and narrative generation.

Supports multiple backends:
- Template-based (default, no dependencies)
- Ollama (local LLM)
- Mock (for testing)
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime

import httpx

from ..models.schemas import (
    AIInsight,
    AIAnalysisResponse,
    TechnicalAnalysis,
    FundamentalAnalysis,
    RiskAnalysis,
)

logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """AI backend configuration."""
    backend: Literal["template", "ollama", "mock"] = "template"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    timeout: float = 30.0


class AIAnalyzer:
    """
    AI-powered analysis generator.
    
    Generates investment insights using either template-based logic
    or local LLM inference via Ollama.
    """
    
    def __init__(self, config: Optional[AIConfig] = None):
        """
        Initialize AI analyzer.
        
        Args:
            config: AI configuration
        """
        self.config = config or AIConfig()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client for Ollama."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def analyze_symbol(
        self,
        symbol: str,
        technical: TechnicalAnalysis,
        fundamental: Optional[FundamentalAnalysis] = None,
    ) -> AIAnalysisResponse:
        """
        Generate AI analysis for a single symbol.
        
        Args:
            symbol: Stock symbol
            technical: Technical analysis results
            fundamental: Fundamental analysis results (optional)
            
        Returns:
            AIAnalysisResponse with insights
        """
        if self.config.backend == "ollama":
            return await self._analyze_with_ollama(symbol, technical, fundamental)
        elif self.config.backend == "mock":
            return self._analyze_mock(symbol, technical, fundamental)
        else:
            return self._analyze_template(symbol, technical, fundamental)
    
    async def analyze_portfolio(
        self,
        portfolio_id: int,
        risk_analysis: RiskAnalysis,
        holdings: List[Any],
    ) -> AIAnalysisResponse:
        """
        Generate AI analysis for a portfolio.
        
        Args:
            portfolio_id: Portfolio identifier
            risk_analysis: Risk analysis results
            holdings: Portfolio holdings
            
        Returns:
            AIAnalysisResponse with insights
        """
        if self.config.backend == "ollama":
            return await self._analyze_portfolio_ollama(portfolio_id, risk_analysis, holdings)
        elif self.config.backend == "mock":
            return self._analyze_portfolio_mock(portfolio_id, risk_analysis, holdings)
        else:
            return self._analyze_portfolio_template(portfolio_id, risk_analysis, holdings)
    
    def _analyze_template(
        self,
        symbol: str,
        technical: TechnicalAnalysis,
        fundamental: Optional[FundamentalAnalysis],
    ) -> AIAnalysisResponse:
        """Generate analysis using rule-based templates."""
        insights = []
        key_risks = []
        opportunities = []
        
        # Technical Analysis Insights
        if technical.overall_signal.value in ['buy', 'strong_buy']:
            insights.append(AIInsight(
                category="technical",
                sentiment="positive",
                confidence=technical.signal_strength,
                title="Bullish Technical Setup",
                description=f"Multiple technical indicators suggest upward momentum. Signal strength: {technical.signal_strength:.0%}",
                action_items=["Monitor for breakout confirmation", "Consider entry on pullback to support"]
            ))
            opportunities.append("Technical indicators showing bullish alignment")
        elif technical.overall_signal.value in ['sell', 'strong_sell']:
            insights.append(AIInsight(
                category="technical",
                sentiment="negative",
                confidence=technical.signal_strength,
                title="Bearish Technical Setup",
                description=f"Technical indicators suggest downward pressure. Signal strength: {technical.signal_strength:.0%}",
                action_items=["Consider reducing position", "Wait for support test before adding"]
            ))
            key_risks.append("Technical momentum indicating bearish trend")
        else:
            insights.append(AIInsight(
                category="technical",
                sentiment="neutral",
                confidence=0.5,
                title="Mixed Technical Signals",
                description="Technical indicators are inconclusive, suggesting consolidation.",
                action_items=["Wait for clearer directional signal"]
            ))
        
        # RSI Insight
        rsi = technical.momentum.rsi_14
        if rsi and rsi > 70:
            insights.append(AIInsight(
                category="technical",
                sentiment="caution",
                confidence=0.7,
                title="Overbought Conditions",
                description=f"RSI at {rsi:.1f} indicates overbought conditions. Potential for pullback.",
                action_items=["Consider taking partial profits", "Set trailing stops"]
            ))
            key_risks.append("Overbought RSI suggests pullback risk")
        elif rsi and rsi < 30:
            insights.append(AIInsight(
                category="technical",
                sentiment="positive",
                confidence=0.6,
                title="Oversold Conditions",
                description=f"RSI at {rsi:.1f} suggests oversold conditions. Potential bounce opportunity.",
                action_items=["Watch for bullish reversal patterns", "Consider gradual accumulation"]
            ))
            opportunities.append("Oversold conditions may present entry opportunity")
        
        # Volatility Insight
        if technical.volatility.historical_volatility_30d:
            hv = technical.volatility.historical_volatility_30d
            if hv > 0.40:
                insights.append(AIInsight(
                    category="risk",
                    sentiment="caution",
                    confidence=0.8,
                    title="Elevated Volatility",
                    description=f"Historical volatility at {hv:.1%} is significantly above market average.",
                    action_items=["Reduce position size", "Consider options strategies for volatility"]
                ))
                key_risks.append(f"High volatility ({hv:.1%}) increases uncertainty")
        
        # Trend Analysis
        adx = technical.trend.adx_14
        if adx and adx > 25:
            trend_strength = "strong"
            insights.append(AIInsight(
                category="technical",
                sentiment="positive" if technical.trend_direction == "bullish" else "negative",
                confidence=min(adx / 50, 1.0),
                title=f"{trend_strength.title()} Trend Detected",
                description=f"ADX at {adx:.1f} indicates {technical.trend_direction} trend strength.",
                action_items=["Trade in direction of trend"]
            ))
        
        # Fundamental Insights
        if fundamental:
            # Valuation check
            pe = fundamental.valuation.trailing_pe
            if pe:
                if pe < 15:
                    insights.append(AIInsight(
                        category="fundamental",
                        sentiment="positive",
                        confidence=0.6,
                        title="Attractive Valuation",
                        description=f"P/E ratio of {pe:.1f} is below market average, suggesting potential value.",
                        action_items=["Compare to industry peers", "Check for value trap indicators"]
                    ))
                    opportunities.append("Low P/E may indicate undervaluation")
                elif pe > 40:
                    insights.append(AIInsight(
                        category="fundamental",
                        sentiment="caution",
                        confidence=0.5,
                        title="Premium Valuation",
                        description=f"P/E ratio of {pe:.1f} suggests premium pricing.",
                        action_items=["Verify growth justifies premium", "Monitor earnings closely"]
                    ))
                    key_risks.append("High P/E requires sustained growth to justify")
            
            # Profitability check
            roe = fundamental.profitability.roe
            if roe and roe > 15:
                insights.append(AIInsight(
                    category="fundamental",
                    sentiment="positive",
                    confidence=0.7,
                    title="Strong Profitability",
                    description=f"ROE of {roe:.1f}% demonstrates efficient capital allocation.",
                    action_items=["Analyze sustainability of returns"]
                ))
            
            # Financial health
            debt_equity = fundamental.financial_health.debt_to_equity
            if debt_equity and debt_equity > 1.0:
                insights.append(AIInsight(
                    category="fundamental",
                    sentiment="caution",
                    confidence=0.6,
                    title="Elevated Leverage",
                    description=f"Debt-to-equity of {debt_equity:.2f} indicates above-average leverage.",
                    action_items=["Review interest coverage ratio", "Monitor debt maturity schedule"]
                ))
                key_risks.append(f"High leverage (D/E: {debt_equity:.2f}) increases financial risk")
        
        # Generate summary
        summary = self._generate_summary(symbol, insights, key_risks, opportunities)
        
        return AIAnalysisResponse(
            symbol=symbol,
            generated_at=datetime.utcnow(),
            insights=insights,
            summary=summary,
            key_risks=key_risks,
            opportunities=opportunities,
            model_used="template",
        )
    
    def _analyze_portfolio_template(
        self,
        portfolio_id: int,
        risk: RiskAnalysis,
        holdings: List[Any],
    ) -> AIAnalysisResponse:
        """Generate portfolio analysis using templates."""
        insights = []
        key_risks = risk.alerts.copy()
        opportunities = []
        
        # Risk level insight
        risk_desc = {
            "low": "The portfolio exhibits conservative risk characteristics suitable for risk-averse investors.",
            "moderate": "The portfolio has balanced risk-return characteristics appropriate for most investors.",
            "high": "The portfolio carries elevated risk and may experience significant volatility.",
            "extreme": "The portfolio has aggressive risk positioning with potential for large drawdowns.",
        }
        
        insights.append(AIInsight(
            category="risk",
            sentiment="neutral" if risk.risk_level.value in ["low", "moderate"] else "caution",
            confidence=0.75,
            title=f"{risk.risk_level.value.title()} Risk Profile",
            description=risk_desc.get(risk.risk_level.value, ""),
            action_items=risk.recommendations,
        ))
        
        # Sharpe ratio insight
        sharpe = risk.metrics.sharpe_ratio
        if sharpe < 0.5:
            insights.append(AIInsight(
                category="risk",
                sentiment="caution",
                confidence=0.7,
                title="Suboptimal Risk-Adjusted Returns",
                description=f"Sharpe ratio of {sharpe:.2f} suggests returns may not adequately compensate for risk taken.",
                action_items=["Review asset allocation", "Consider lower-volatility alternatives"]
            ))
            key_risks.append(f"Low Sharpe ratio ({sharpe:.2f}) indicates poor risk-adjusted performance")
        elif sharpe > 1.5:
            insights.append(AIInsight(
                category="risk",
                sentiment="positive",
                confidence=0.8,
                title="Strong Risk-Adjusted Performance",
                description=f"Sharpe ratio of {sharpe:.2f} indicates efficient risk utilization.",
                action_items=["Maintain current strategy"]
            ))
            opportunities.append("Strong Sharpe ratio demonstrates effective risk management")
        
        # Concentration insight
        top_holding = risk.concentration.top_holding_percent
        if top_holding > 20:
            insights.append(AIInsight(
                category="risk",
                sentiment="caution",
                confidence=0.75,
                title="Concentration Risk",
                description=f"Single holding represents {top_holding:.1f}% of portfolio, creating idiosyncratic risk.",
                action_items=["Consider diversification", "Implement position limits"]
            ))
        
        # Diversification benefit
        hhi = risk.concentration.herfindahl_index
        if hhi > 0.25:
            insights.append(AIInsight(
                category="risk",
                sentiment="caution",
                confidence=0.6,
                title="Limited Diversification",
                description=f"Herfindahl index of {hhi:.3f} indicates concentrated positions may limit diversification benefits.",
                action_items=["Increase number of holdings", "Consider uncorrelated assets"]
            ))
        
        # Generate summary
        summary = f"Portfolio analysis indicates {risk.risk_level.value} risk profile with {len(key_risks)} key risk factors identified. "
        if risk.recommendations:
            summary += f"Recommendations: {'; '.join(risk.recommendations[:2])}"
        
        return AIAnalysisResponse(
            portfolio_id=portfolio_id,
            generated_at=datetime.utcnow(),
            insights=insights,
            summary=summary,
            key_risks=key_risks,
            opportunities=opportunities,
            model_used="template",
        )
    
    async def _analyze_with_ollama(
        self,
        symbol: str,
        technical: TechnicalAnalysis,
        fundamental: Optional[FundamentalAnalysis],
    ) -> AIAnalysisResponse:
        """Generate analysis using Ollama local LLM."""
        try:
            # Build prompt
            prompt = self._build_symbol_prompt(symbol, technical, fundamental)
            
            # Call Ollama
            client = await self._get_client()
            response = await client.post(
                f"{self.config.ollama_url}/api/generate",
                json={
                    "model": self.config.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            # Parse response into structured insights
            insights = self._parse_llm_response(generated_text)
            
            return AIAnalysisResponse(
                symbol=symbol,
                generated_at=datetime.utcnow(),
                insights=insights,
                summary=generated_text[:500] + "..." if len(generated_text) > 500 else generated_text,
                key_risks=[i.description for i in insights if i.sentiment == "caution"],
                opportunities=[i.description for i in insights if i.sentiment == "positive"],
                model_used=f"ollama:{self.config.ollama_model}",
            )
            
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            # Fallback to template
            return self._analyze_template(symbol, technical, fundamental)
    
    def _build_symbol_prompt(
        self,
        symbol: str,
        technical: TechnicalAnalysis,
        fundamental: Optional[FundamentalAnalysis],
    ) -> str:
        """Build prompt for symbol analysis."""
        prompt = f"""Analyze {symbol} as an investment advisor. Provide structured insights.

Technical Analysis:
- Current Price: ${technical.current_price:.2f} ({technical.change_percent:+.2f}%)
- Trend: {technical.trend_direction}
- Signal: {technical.overall_signal.value} (strength: {technical.signal_strength:.0%})
- RSI: {technical.momentum.rsi_14:.1f if technical.momentum.rsi_14 else 'N/A'}
- MACD: {technical.momentum.macd_histogram:.3f if technical.momentum.macd_histogram else 'N/A'}
- Volatility: {technical.volatility.historical_volatility_30d:.1% if technical.volatility.historical_volatility_30d else 'N/A'}
- Support: ${technical.support_resistance.support_1:.2f if technical.support_resistance else 'N/A'}
- Resistance: ${technical.support_resistance.resistance_1:.2f if technical.support_resistance else 'N/A'}
"""
        
        if fundamental:
            prompt += f"""
Fundamental Analysis:
- P/E: {fundamental.valuation.trailing_pe:.1f if fundamental.valuation.trailing_pe else 'N/A'}
- P/B: {fundamental.valuation.price_to_book:.2f if fundamental.valuation.price_to_book else 'N/A'}
- ROE: {fundamental.profitability.roe:.1f}% if fundamental.profitability.roe else 'N/A'}
- Debt/Equity: {fundamental.financial_health.debt_to_equity:.2f if fundamental.financial_health.debt_to_equity else 'N/A'}
- Revenue Growth: {fundamental.growth.revenue_growth_yoy:.1f}% if fundamental.growth.revenue_growth_yoy else 'N/A'
"""
        
        prompt += """
Provide 3-5 key insights in this format:
- Category: [technical/fundamental/risk]
- Sentiment: [positive/negative/caution/neutral]
- Title: Brief title
- Description: 1-2 sentence explanation
- Action: Recommended action

Keep analysis professional and actionable."""
        
        return prompt
    
    def _parse_llm_response(self, text: str) -> List[AIInsight]:
        """Parse LLM response into structured insights."""
        # Simple parsing - in production, use structured output
        insights = []
        lines = text.split('\n')
        
        current_insight = {}
        for line in lines:
            line = line.strip()
            if line.startswith('- Category:') or line.startswith('Category:'):
                if current_insight:
                    insights.append(self._create_insight(current_insight))
                current_insight = {'category': line.split(':', 1)[1].strip()}
            elif line.startswith('- Sentiment:') or line.startswith('Sentiment:'):
                current_insight['sentiment'] = line.split(':', 1)[1].strip()
            elif line.startswith('- Title:') or line.startswith('Title:'):
                current_insight['title'] = line.split(':', 1)[1].strip()
            elif line.startswith('- Description:') or line.startswith('Description:'):
                current_insight['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('- Action:') or line.startswith('Action:'):
                current_insight['action'] = line.split(':', 1)[1].strip()
        
        if current_insight:
            insights.append(self._create_insight(current_insight))
        
        # If parsing failed, create a generic insight
        if not insights:
            insights.append(AIInsight(
                category="analysis",
                sentiment="neutral",
                confidence=0.5,
                title="AI Analysis",
                description=text[:200],
                action_items=[],
            ))
        
        return insights
    
    def _create_insight(self, data: Dict) -> AIInsight:
        """Create AIInsight from parsed data."""
        return AIInsight(
            category=data.get('category', 'analysis'),
            sentiment=data.get('sentiment', 'neutral'),
            confidence=0.7,
            title=data.get('title', 'Analysis'),
            description=data.get('description', ''),
            action_items=[data.get('action', 'Review analysis')] if data.get('action') else [],
        )
    
    def _generate_summary(
        self,
        symbol: str,
        insights: List[AIInsight],
        risks: List[str],
        opportunities: List[str],
    ) -> str:
        """Generate executive summary."""
        sentiment_counts = {}
        for i in insights:
            sentiment_counts[i.sentiment] = sentiment_counts.get(i.sentiment, 0) + 1
        
        dominant = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "neutral"
        
        summary = f"{symbol} analysis shows predominantly {dominant} signals. "
        
        if opportunities:
            summary += f"Key opportunity: {opportunities[0]}. "
        if risks:
            summary += f"Primary risk: {risks[0]}. "
        
        return summary.strip()
    
    def _analyze_mock(
        self,
        symbol: str,
        technical: TechnicalAnalysis,
        fundamental: Optional[FundamentalAnalysis],
    ) -> AIAnalysisResponse:
        """Generate mock analysis for testing."""
        return AIAnalysisResponse(
            symbol=symbol,
            generated_at=datetime.utcnow(),
            insights=[
                AIInsight(
                    category="technical",
                    sentiment="positive",
                    confidence=0.8,
                    title="Mock Technical Insight",
                    description="This is a mock insight for testing purposes.",
                    action_items=["Mock action"],
                )
            ],
            summary=f"Mock analysis for {symbol}",
            key_risks=["Mock risk"],
            opportunities=["Mock opportunity"],
            model_used="mock",
        )
    
    def _analyze_portfolio_mock(
        self,
        portfolio_id: int,
        risk: RiskAnalysis,
        holdings: List[Any],
    ) -> AIAnalysisResponse:
        """Generate mock portfolio analysis."""
        return AIAnalysisResponse(
            portfolio_id=portfolio_id,
            generated_at=datetime.utcnow(),
            insights=[
                AIInsight(
                    category="risk",
                    sentiment="neutral",
                    confidence=0.7,
                    title="Mock Portfolio Insight",
                    description="This is a mock portfolio insight for testing.",
                    action_items=["Mock recommendation"],
                )
            ],
            summary="Mock portfolio analysis",
            key_risks=[],
            opportunities=[],
            model_used="mock",
        )
    
    async def _analyze_portfolio_ollama(
        self,
        portfolio_id: int,
        risk: RiskAnalysis,
        holdings: List[Any],
    ) -> AIAnalysisResponse:
        """Generate portfolio analysis using Ollama."""
        # Similar to symbol analysis, simplified
        return self._analyze_portfolio_template(portfolio_id, risk, holdings)
