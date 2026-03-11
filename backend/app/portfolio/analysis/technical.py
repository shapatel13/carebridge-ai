"""Technical analysis module - pure Python/NumPy implementation.

Implements comprehensive technical indicators without TA-Lib dependency.
All calculations use pandas/numpy for performance.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

import numpy as np
import pandas as pd

from ..models.schemas import (
    TechnicalAnalysis,
    MovingAverages,
    MomentumIndicators,
    VolatilityIndicators,
    VolumeIndicators,
    TrendIndicators,
    SupportResistance,
    SignalType,
)

logger = logging.getLogger(__name__)


@dataclass
class OHLCVData:
    """Container for OHLCV data."""
    timestamps: pd.DatetimeIndex
    open: pd.Series
    high: pd.Series
    low: pd.Series
    close: pd.Series
    volume: pd.Series
    
    @property
    def df(self) -> pd.DataFrame:
        """Return as DataFrame."""
        return pd.DataFrame({
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
        }, index=self.timestamps)
    
    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> "OHLCVData":
        """Create from list of OHLCV dictionaries."""
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()
        
        return cls(
            timestamps=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            volume=df['volume'],
        )


class TechnicalAnalyzer:
    """
    Technical analysis engine implementing hedge fund-grade indicators.
    
    All calculations are vectorized using NumPy/Pandas for efficiency.
    No external TA library dependencies.
    """
    
    def __init__(self, data: OHLCVData):
        """
        Initialize analyzer with OHLCV data.
        
        Args:
            data: OHLCV data container
        """
        self.data = data
        self.df = data.df
        
    # =========================================================================
    # Moving Averages
    # =========================================================================
    
    def sma(self, period: int) -> pd.Series:
        """Simple Moving Average."""
        return self.df['close'].rolling(window=period, min_periods=period).mean()
    
    def ema(self, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return self.df['close'].ewm(span=period, adjust=False, min_periods=period).mean()
    
    def vwma(self, period: int) -> pd.Series:
        """Volume Weighted Moving Average."""
        typical_price = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        return (typical_price * self.df['volume']).rolling(window=period).sum() / \
               self.df['volume'].rolling(window=period).sum()
    
    def vwap(self, anchor: str = 'D') -> pd.Series:
        """
        Volume Weighted Average Price.
        
        Args:
            anchor: Time anchor ('D'=daily, 'W'=weekly, 'M'=monthly)
        """
        df = self.df.copy()
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Group by anchor period
        df['grouper'] = df.index.to_period(anchor)
        df['cum_vwap'] = (typical_price * df['volume']).groupby(df['grouper']).cumsum()
        df['cum_vol'] = df['volume'].groupby(df['grouper']).cumsum()
        
        return df['cum_vwap'] / df['cum_vol']
    
    # =========================================================================
    # Momentum Indicators
    # =========================================================================
    
    def rsi(self, period: int = 14) -> pd.Series:
        """
        Relative Strength Index.
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        """
        delta = self.df['close'].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = (-delta.where(delta < 0, 0))
        
        avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def macd(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence).
        
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = self.ema(fast)
        ema_slow = self.ema(slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def stochastic(
        self,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator.
        
        %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
        %D = SMA of %K
        """
        lowest_low = self.df['low'].rolling(window=k_period, min_periods=k_period).min()
        highest_high = self.df['high'].rolling(window=k_period, min_periods=k_period).max()
        
        k = 100 * (self.df['close'] - lowest_low) / (highest_high - lowest_low)
        k = k.rolling(window=smooth_k, min_periods=smooth_k).mean()  # Smooth %K
        d = k.rolling(window=d_period, min_periods=d_period).mean()
        
        return k, d
    
    def cci(self, period: int = 20) -> pd.Series:
        """
        Commodity Channel Index.
        
        CCI = (Typical Price - SMA of TP) / (0.015 * Mean Deviation)
        """
        tp = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        sma_tp = tp.rolling(window=period, min_periods=period).mean()
        mean_dev = tp.rolling(window=period, min_periods=period).apply(
            lambda x: np.abs(x - x.mean()).mean(), raw=True
        )
        
        cci = (tp - sma_tp) / (0.015 * mean_dev)
        return cci
    
    def williams_r(self, period: int = 14) -> pd.Series:
        """
        Williams %R.
        
        %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
        """
        highest_high = self.df['high'].rolling(window=period, min_periods=period).max()
        lowest_low = self.df['low'].rolling(window=period, min_periods=period).min()
        
        williams_r = (highest_high - self.df['close']) / (highest_high - lowest_low) * -100
        return williams_r
    
    # =========================================================================
    # Volatility Indicators
    # =========================================================================
    
    def atr(self, period: int = 14) -> pd.Series:
        """
        Average True Range.
        
        TR = max(high-low, |high-prev_close|, |low-prev_close|)
        ATR = EMA of TR
        """
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
        
        return atr
    
    def bollinger_bands(
        self,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands.
        
        Middle = SMA
        Upper = Middle + (std_dev * StdDev)
        Lower = Middle - (std_dev * StdDev)
        """
        middle = self.sma(period)
        std = self.df['close'].rolling(window=period, min_periods=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return upper, middle, lower
    
    def keltner_channels(
        self,
        ema_period: int = 20,
        atr_period: int = 14,
        multiplier: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Keltner Channels.
        
        Middle = EMA
        Upper = Middle + (multiplier * ATR)
        Lower = Middle - (multiplier * ATR)
        """
        middle = self.ema(ema_period)
        atr_val = self.atr(atr_period)
        
        upper = middle + (multiplier * atr_val)
        lower = middle - (multiplier * atr_val)
        
        return upper, middle, lower
    
    def historical_volatility(self, period: int = 30, annualize: bool = True) -> pd.Series:
        """
        Historical Volatility.
        
        Standard deviation of log returns, optionally annualized.
        """
        log_returns = np.log(self.df['close'] / self.df['close'].shift(1))
        volatility = log_returns.rolling(window=period, min_periods=period).std()
        
        if annualize:
            volatility *= np.sqrt(252)  # Annualize assuming 252 trading days
        
        return volatility
    
    # =========================================================================
    # Volume Indicators
    # =========================================================================
    
    def obv(self) -> pd.Series:
        """
        On-Balance Volume.
        
        OBV = Previous OBV + Volume if Close > Previous Close
        OBV = Previous OBV - Volume if Close < Previous Close
        OBV = Previous OBV if Close == Previous Close
        """
        close = self.df['close']
        volume = self.df['volume']
        
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def relative_volume(self, period: int = 20) -> pd.Series:
        """Relative volume (current volume / average volume)."""
        avg_volume = self.df['volume'].rolling(window=period, min_periods=period).mean()
        return self.df['volume'] / avg_volume
    
    def volume_trend(self, period: int = 5) -> str:
        """
        Determine volume trend.
        
        Returns:
            'increasing', 'decreasing', or 'neutral'
        """
        recent = self.df['volume'].tail(period)
        if len(recent) < 3:
            return "neutral"
        
        # Linear regression slope
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent.values, 1)[0]
        
        avg_vol = recent.mean()
        threshold = avg_vol * 0.05  # 5% threshold
        
        if slope > threshold:
            return "increasing"
        elif slope < -threshold:
            return "decreasing"
        return "neutral"
    
    # =========================================================================
    # Trend Indicators
    # =========================================================================
    
    def adx(self, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Average Directional Index.
        
        Returns:
            Tuple of (ADX, +DI, -DI)
        """
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        # True Range
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        # Smoothed values
        atr_val = self.atr(period)
        
        plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_val
        minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_val
        
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        
        return adx, plus_di, minus_di
    
    def parabolic_sar(
        self,
        af_start: float = 0.02,
        af_increment: float = 0.02,
        af_max: float = 0.2
    ) -> pd.Series:
        """
        Parabolic Stop and Reverse.
        
        Complex iterative calculation for SAR.
        """
        high = self.df['high'].values
        low = self.df['low'].values
        close = self.df['close'].values
        n = len(close)
        
        sar = np.zeros(n)
        trend = np.zeros(n)  # 1 for uptrend, -1 for downtrend
        ep = np.zeros(n)  # Extreme point
        af = np.zeros(n)  # Acceleration factor
        
        # Initialize
        trend[0] = 1 if close[0] > close[1] if len(close) > 1 else 1 else -1
        sar[0] = low[0] if trend[0] == 1 else high[0]
        ep[0] = high[0] if trend[0] == 1 else low[0]
        af[0] = af_start
        
        for i in range(1, n):
            # Calculate SAR
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
            
            # Check for trend reversal
            if trend[i-1] == 1:  # Uptrend
                if low[i] < sar[i]:  # Reverse to downtrend
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af[i] = af_start
                else:
                    trend[i] = 1
                    ep[i] = max(high[i], ep[i-1])
                    af[i] = min(af_max, af[i-1] + af_increment) if ep[i] != ep[i-1] else af[i-1]
                    sar[i] = max(sar[i], low[i-1], low[max(0, i-2)])
            else:  # Downtrend
                if high[i] > sar[i]:  # Reverse to uptrend
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af[i] = af_start
                else:
                    trend[i] = -1
                    ep[i] = min(low[i], ep[i-1])
                    af[i] = min(af_max, af[i-1] + af_increment) if ep[i] != ep[i-1] else af[i-1]
                    sar[i] = min(sar[i], high[i-1], high[max(0, i-2)])
        
        return pd.Series(sar, index=self.df.index)
    
    def ichimoku_cloud(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26
    ) -> Dict[str, pd.Series]:
        """
        Ichimoku Cloud indicator.
        
        Returns dict with:
        - tenkan_sen (Conversion Line)
        - kijun_sen (Base Line)
        - senkou_span_a (Leading Span A)
        - senkou_span_b (Leading Span B)
        - chikou_span (Lagging Span)
        """
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        
        # Tenkan-sen (Conversion Line): (Highest High + Lowest Low) / 2 for 9 periods
        tenkan_sen = (high.rolling(window=tenkan_period).max() + 
                      low.rolling(window=tenkan_period).min()) / 2
        
        # Kijun-sen (Base Line): (Highest High + Lowest Low) / 2 for 26 periods
        kijun_sen = (high.rolling(window=kijun_period).max() + 
                     low.rolling(window=kijun_period).min()) / 2
        
        # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, shifted forward 26 periods
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
        
        # Senkou Span B (Leading Span B): (Highest High + Lowest Low) / 2 for 52 periods, shifted forward 26
        senkou_span_b = ((high.rolling(window=senkou_b_period).max() + 
                          low.rolling(window=senkou_b_period).min()) / 2).shift(displacement)
        
        # Chikou Span (Lagging Span): Close price shifted back 26 periods
        chikou_span = close.shift(-displacement)
        
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span,
        }
    
    # =========================================================================
    # Support/Resistance
    # =========================================================================
    
    def pivot_points(self, method: str = 'standard') -> SupportResistance:
        """
        Calculate pivot points and support/resistance levels.
        
        Args:
            method: 'standard' or 'fibonacci'
        """
        last = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else last
        
        high = prev['high']
        low = prev['low']
        close = prev['close']
        
        if method == 'standard':
            pivot = (high + low + close) / 3
            s1 = (2 * pivot) - high
            s2 = pivot - (high - low)
            r1 = (2 * pivot) - low
            r2 = pivot + (high - low)
        else:  # fibonacci
            pivot = (high + low + close) / 3
            s1 = pivot - 0.382 * (high - low)
            s2 = pivot - 0.618 * (high - low)
            r1 = pivot + 0.382 * (high - low)
            r2 = pivot + 0.618 * (high - low)
        
        # Find recent highs and lows (last 20 periods)
        recent = self.df.tail(20)
        recent_highs = recent['high'].nlargest(3).tolist()
        recent_lows = recent['low'].nsmallest(3).tolist()
        
        return SupportResistance(
            pivot=round(pivot, 4),
            support_1=round(s1, 4),
            support_2=round(s2, 4),
            resistance_1=round(r1, 4),
            resistance_2=round(r2, 4),
            recent_highs=[round(h, 4) for h in recent_highs],
            recent_lows=[round(l, 4) for l in recent_lows],
        )
    
    # =========================================================================
    # Signal Generation
    # =========================================================================
    
    def generate_signal(self) -> Tuple[SignalType, float]:
        """
        Generate composite trading signal based on multiple indicators.
        
        Returns:
            Tuple of (SignalType, strength) where strength is 0-1
        """
        if len(self.df) < 50:
            return SignalType.HOLD, 0.0
        
        scores = []
        
        # 1. Moving Average Alignment (30%)
        price = self.df['close'].iloc[-1]
        sma20 = self.sma(20).iloc[-1]
        sma50 = self.sma(50).iloc[-1]
        
        if price > sma20 > sma50:
            scores.append(0.3)
        elif price < sma20 < sma50:
            scores.append(-0.3)
        else:
            scores.append(0)
        
        # 2. RSI (20%)
        rsi = self.rsi(14).iloc[-1]
        if rsi < 30:
            scores.append(0.2)  # Oversold - bullish
        elif rsi > 70:
            scores.append(-0.2)  # Overbought - bearish
        else:
            scores.append(0)
        
        # 3. MACD (20%)
        macd_line, signal_line, hist = self.macd()
        if macd_line.iloc[-1] > signal_line.iloc[-1] and hist.iloc[-1] > hist.iloc[-2]:
            scores.append(0.2)
        elif macd_line.iloc[-1] < signal_line.iloc[-1] and hist.iloc[-1] < hist.iloc[-2]:
            scores.append(-0.2)
        else:
            scores.append(0)
        
        # 4. ADX Trend Strength (15%)
        adx, plus_di, minus_di = self.adx(14)
        if adx.iloc[-1] > 25:
            if plus_di.iloc[-1] > minus_di.iloc[-1]:
                scores.append(0.15)
            else:
                scores.append(-0.15)
        else:
            scores.append(0)
        
        # 5. Volume Confirmation (15%)
        rel_vol = self.relative_volume(20).iloc[-1]
        price_change = self.df['close'].pct_change().iloc[-1]
        if rel_vol > 1.5:
            if price_change > 0:
                scores.append(0.15)
            else:
                scores.append(-0.15)
        else:
            scores.append(0)
        
        # Calculate total score
        total_score = sum(scores)
        strength = min(abs(total_score), 1.0)
        
        # Determine signal type
        if total_score >= 0.6:
            return SignalType.STRONG_BUY, strength
        elif total_score >= 0.3:
            return SignalType.BUY, strength
        elif total_score <= -0.6:
            return SignalType.STRONG_SELL, strength
        elif total_score <= -0.3:
            return SignalType.SELL, strength
        else:
            return SignalType.HOLD, strength
    
    def get_trend_direction(self) -> str:
        """
        Determine overall trend direction.
        
        Returns:
            'bullish', 'bearish', 'neutral', or 'sideways'
        """
        if len(self.df) < 50:
            return "neutral"
        
        # Check moving average alignment
        price = self.df['close'].iloc[-1]
        sma20 = self.sma(20).iloc[-1]
        sma50 = self.sma(50).iloc[-1]
        
        # ADX for trend strength
        adx_val = self.adx(14)[0].iloc[-1]
        
        if adx_val < 20:
            return "sideways"
        
        if price > sma20 > sma50:
            return "bullish"
        elif price < sma20 < sma50:
            return "bearish"
        
        return "neutral"
    
    # =========================================================================
    # Main Analysis Method
    # =========================================================================
    
    def analyze(self, symbol: str) -> TechnicalAnalysis:
        """
        Perform complete technical analysis.
        
        Args:
            symbol: Stock symbol for reference
            
        Returns:
            TechnicalAnalysis object with all indicators
        """
        if len(self.df) < 20:
            raise ValueError("Insufficient data for analysis (need at least 20 periods)")
        
        # Current price info
        current_price = self.df['close'].iloc[-1]
        prev_price = self.df['close'].iloc[-2] if len(self.df) > 1 else current_price
        change_pct = (current_price - prev_price) / prev_price * 100
        
        # Moving Averages
        ma = MovingAverages(
            sma_20=self.sma(20).iloc[-1] if len(self.df) >= 20 else None,
            sma_50=self.sma(50).iloc[-1] if len(self.df) >= 50 else None,
            sma_100=self.sma(100).iloc[-1] if len(self.df) >= 100 else None,
            sma_200=self.sma(200).iloc[-1] if len(self.df) >= 200 else None,
            ema_12=self.ema(12).iloc[-1] if len(self.df) >= 12 else None,
            ema_26=self.ema(26).iloc[-1] if len(self.df) >= 26 else None,
        )
        
        # Momentum
        macd_line, signal_line, hist = self.macd()
        stoch_k, stoch_d = self.stochastic()
        
        momentum = MomentumIndicators(
            rsi_14=self.rsi(14).iloc[-1],
            macd_line=macd_line.iloc[-1],
            macd_signal=signal_line.iloc[-1],
            macd_histogram=hist.iloc[-1],
            stochastic_k=stoch_k.iloc[-1],
            stochastic_d=stoch_d.iloc[-1],
            cci_20=self.cci(20).iloc[-1] if len(self.df) >= 20 else None,
            williams_r=self.williams_r(14).iloc[-1],
        )
        
        # Volatility
        bb_upper, bb_middle, bb_lower = self.bollinger_bands()
        atr_val = self.atr(14)
        
        volatility = VolatilityIndicators(
            atr_14=atr_val.iloc[-1],
            bollinger_upper=bb_upper.iloc[-1],
            bollinger_middle=bb_middle.iloc[-1],
            bollinger_lower=bb_lower.iloc[-1],
            bollinger_width=(bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1] if bb_middle.iloc[-1] else None,
            historical_volatility_30d=self.historical_volatility(30).iloc[-1] if len(self.df) >= 30 else None,
        )
        
        # Volume
        volume = VolumeIndicators(
            obv=self.obv().iloc[-1],
            volume_sma_20=self.df['volume'].rolling(20).mean().iloc[-1],
            relative_volume=self.relative_volume(20).iloc[-1],
            volume_trend=self.volume_trend(),
        )
        
        # Trend
        adx_val, plus_di, minus_di = self.adx(14)
        ichimoku = self.ichimoku_cloud()
        
        trend = TrendIndicators(
            adx_14=adx_val.iloc[-1],
            plus_di=plus_di.iloc[-1],
            minus_di=minus_di.iloc[-1],
            parabolic_sar=self.parabolic_sar().iloc[-1],
            ichimoku_tenkan=ichimoku['tenkan_sen'].iloc[-1],
            ichimoku_kijun=ichimoku['kijun_sen'].iloc[-1],
            ichimoku_senkou_a=ichimoku['senkou_span_a'].iloc[-1],
            ichimoku_senkou_b=ichimoku['senkou_span_b'].iloc[-1],
        )
        
        # Support/Resistance
        sr = self.pivot_points()
        
        # Signal
        signal, strength = self.generate_signal()
        trend_dir = self.get_trend_direction()
        
        # Key levels
        key_levels = {
            's1': sr.support_1,
            's2': sr.support_2,
            'pivot': sr.pivot,
            'r1': sr.resistance_1,
            'r2': sr.resistance_2,
            'vwap': self.vwap().iloc[-1],
        }
        
        return TechnicalAnalysis(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            current_price=round(current_price, 4),
            change_percent=round(change_pct, 4),
            moving_averages=ma,
            momentum=momentum,
            volatility=volatility,
            volume=volume,
            trend=trend,
            support_resistance=sr,
            overall_signal=signal,
            signal_strength=round(strength, 4),
            trend_direction=trend_dir,
            key_levels={k: round(v, 4) if v is not None else None for k, v in key_levels.items()},
        )
