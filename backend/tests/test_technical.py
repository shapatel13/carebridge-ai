"""Tests for technical analysis module."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.portfolio.analysis.technical import TechnicalAnalyzer, OHLCVData


def create_sample_data(periods: int = 100) -> OHLCVData:
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')
    
    # Create trending data
    base_price = 100
    trend = np.linspace(0, 20, periods)
    noise = np.random.randn(periods) * 2
    
    closes = base_price + trend + noise
    opens = closes + np.random.randn(periods) * 0.5
    highs = np.maximum(opens, closes) + np.abs(np.random.randn(periods)) * 2
    lows = np.minimum(opens, closes) - np.abs(np.random.randn(periods)) * 2
    volumes = np.random.randint(1000000, 10000000, periods)
    
    return OHLCVData(
        timestamps=pd.DatetimeIndex(dates),
        open=pd.Series(opens, index=dates),
        high=pd.Series(highs, index=dates),
        low=pd.Series(lows, index=dates),
        close=pd.Series(closes, index=dates),
        volume=pd.Series(volumes, index=dates),
    )


class TestMovingAverages:
    """Test moving average calculations."""
    
    def test_sma_calculation(self):
        """Test SMA calculation."""
        data = create_sample_data(50)
        analyzer = TechnicalAnalyzer(data)
        
        sma = analyzer.sma(20)
        
        assert len(sma) == len(data.close)
        assert sma.iloc[19] is not None  # First valid value
        assert sma.iloc[18] is None or pd.isna(sma.iloc[18])  # Before window
        
        # Verify calculation
        expected = data.close.iloc[:20].mean()
        assert abs(sma.iloc[19] - expected) < 0.01
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        data = create_sample_data(50)
        analyzer = TechnicalAnalyzer(data)
        
        ema = analyzer.ema(20)
        
        assert len(ema) == len(data.close)
        # EMA should react faster to changes than SMA
        sma = analyzer.sma(20)
        assert ema.iloc[-1] != sma.iloc[-1]


class TestMomentumIndicators:
    """Test momentum indicator calculations."""
    
    def test_rsi_range(self):
        """Test RSI stays within 0-100 range."""
        data = create_sample_data(100)
        analyzer = TechnicalAnalyzer(data)
        
        rsi = analyzer.rsi(14)
        
        valid_rsi = rsi.dropna()
        assert all(valid_rsi >= 0)
        assert all(valid_rsi <= 100)
    
    def test_rsi_overbought(self):
        """Test RSI correctly identifies overbought conditions."""
        # Create strong uptrend
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        closes = pd.Series(np.linspace(100, 150, 50), index=dates)
        
        data = OHLCVData(
            timestamps=pd.DatetimeIndex(dates),
            open=closes,
            high=closes * 1.01,
            low=closes * 0.99,
            close=closes,
            volume=pd.Series([1000000] * 50, index=dates),
        )
        
        analyzer = TechnicalAnalyzer(data)
        rsi = analyzer.rsi(14)
        
        # RSI should be high in strong uptrend
        assert rsi.iloc[-1] > 50
    
    def test_macd_signal(self):
        """Test MACD signal line crossover."""
        data = create_sample_data(100)
        analyzer = TechnicalAnalyzer(data)
        
        macd_line, signal_line, histogram = analyzer.macd()
        
        assert len(macd_line) == len(data.close)
        assert len(signal_line) == len(data.close)
        assert len(histogram) == len(data.close)
        
        # Signal line should be smoother (less volatile) than MACD line
        macd_volatility = macd_line.dropna().std()
        signal_volatility = signal_line.dropna().std()
        assert signal_volatility < macd_volatility


class TestVolatilityIndicators:
    """Test volatility indicators."""
    
    def test_atr_positive(self):
        """Test ATR is always positive."""
        data = create_sample_data(50)
        analyzer = TechnicalAnalyzer(data)
        
        atr = analyzer.atr(14)
        
        valid_atr = atr.dropna()
        assert all(valid_atr > 0)
    
    def test_bollinger_bands_structure(self):
        """Test Bollinger Bands structure."""
        data = create_sample_data(100)
        analyzer = TechnicalAnalyzer(data)
        
        upper, middle, lower = analyzer.bollinger_bands(20)
        
        # Upper should be above middle, middle above lower
        for i in range(len(upper)):
            if not pd.isna(upper.iloc[i]):
                assert upper.iloc[i] >= middle.iloc[i]
                assert middle.iloc[i] >= lower.iloc[i]


class TestTrendIndicators:
    """Test trend indicators."""
    
    def test_adx_range(self):
        """Test ADX stays within 0-100 range."""
        data = create_sample_data(100)
        analyzer = TechnicalAnalyzer(data)
        
        adx, plus_di, minus_di = analyzer.adx(14)
        
        valid_adx = adx.dropna()
        assert all(valid_adx >= 0)
        assert all(valid_adx <= 100)
    
    def test_adx_trend_strength(self):
        """Test ADX in trending market."""
        # Create trending data
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        closes = pd.Series(np.linspace(100, 150, 50), index=dates)
        
        data = OHLCVData(
            timestamps=pd.DatetimeIndex(dates),
            open=closes,
            high=closes * 1.02,
            low=closes * 0.98,
            close=closes,
            volume=pd.Series([1000000] * 50, index=dates),
        )
        
        analyzer = TechnicalAnalyzer(data)
        adx, plus_di, minus_di = analyzer.adx(14)
        
        # ADX should indicate trending market
        assert adx.iloc[-1] > 20


class TestVolumeIndicators:
    """Test volume indicators."""
    
    def test_obv_trend(self):
        """Test OBV follows price trend."""
        # Create uptrend
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        closes = pd.Series(np.linspace(100, 150, 50), index=dates)
        
        data = OHLCVData(
            timestamps=pd.DatetimeIndex(dates),
            open=closes,
            high=closes * 1.01,
            low=closes * 0.99,
            close=closes,
            volume=pd.Series([1000000] * 50, index=dates),
        )
        
        analyzer = TechnicalAnalyzer(data)
        obv = analyzer.obv()
        
        # OBV should be increasing in uptrend
        assert obv.iloc[-1] > obv.iloc[0]


class TestSignalGeneration:
    """Test signal generation."""
    
    def test_signal_validity(self):
        """Test generated signals are valid."""
        data = create_sample_data(100)
        analyzer = TechnicalAnalyzer(data)
        
        signal, strength = analyzer.generate_signal()
        
        valid_signals = ['buy', 'sell', 'hold', 'strong_buy', 'strong_sell']
        assert signal.value in valid_signals
        assert 0 <= strength <= 1
    
    def test_trend_direction(self):
        """Test trend direction detection."""
        data = create_sample_data(100)
        analyzer = TechnicalAnalyzer(data)
        
        direction = analyzer.get_trend_direction()
        
        valid_directions = ['bullish', 'bearish', 'neutral', 'sideways']
        assert direction in valid_directions


class TestCompleteAnalysis:
    """Test complete analysis pipeline."""
    
    def test_full_analysis(self):
        """Test full analysis generates all components."""
        data = create_sample_data(100)
        analyzer = TechnicalAnalyzer(data)
        
        result = analyzer.analyze('TEST')
        
        assert result.symbol == 'TEST'
        assert result.current_price > 0
        assert result.moving_averages.sma_20 is not None
        assert result.momentum.rsi_14 is not None
        assert result.volatility.atr_14 is not None
        assert result.volume.obv is not None
        assert result.trend.adx_14 is not None
        assert result.overall_signal is not None
        assert 0 <= result.signal_strength <= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
