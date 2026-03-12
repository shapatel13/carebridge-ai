import { 
  Activity, 
  TrendingUp, 
  BarChart3, 
  Gauge,
  Target,
  Zap
} from 'lucide-react';
import type { TechnicalAnalysis } from '../types/portfolio';
import { 
  formatNumber, 
  formatPercentRaw, 
  getSignalColor, 
  getSignalBgColor,
} from '../utils/formatters';

interface TechnicalPanelProps {
  analysis: TechnicalAnalysis;
}

const IndicatorCard = ({ 
  label, 
  value, 
  suffix = '', 
  trend,
}: { 
  label: string; 
  value: string | number; 
  suffix?: string;
  trend?: 'up' | 'down' | 'neutral';
}) => (
  <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 hover:border-slate-600/50 transition-colors">
    <div className="text-slate-400 text-xs uppercase tracking-wider mb-1.5">{label}</div>
    <div className={`text-xl font-mono font-semibold ${
      trend === 'up' ? 'text-emerald-400' : 
      trend === 'down' ? 'text-rose-400' : 
      'text-slate-200'
    }`}>
      {value}{suffix}
    </div>
  </div>
);

const Section = ({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) => (
  <div className="bg-slate-800/30 rounded-xl p-5 border border-slate-700/30">
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-5 h-5 text-emerald-400" />
      <h3 className="text-lg font-semibold text-slate-200">{title}</h3>
    </div>
    {children}
  </div>
);

export const TechnicalPanel = ({ analysis }: TechnicalPanelProps) => {
  const { momentum, volatility, trend, volume, moving_averages, support_resistance } = analysis;

  const getRsiTrend = (rsi?: number): 'up' | 'down' | 'neutral' => {
    if (!rsi) return 'neutral';
    if (rsi > 70) return 'down';
    if (rsi < 30) return 'up';
    return 'neutral';
  };

  const getMacdTrend = (hist?: number): 'up' | 'down' | 'neutral' => {
    if (!hist) return 'neutral';
    return hist > 0 ? 'up' : 'down';
  };

  return (
    <div className="space-y-6 animate-in">
      {/* Signal Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 
                      bg-slate-800/50 rounded-xl border border-slate-700/50">
        <div>
          <div className="text-slate-400 text-sm mb-1">Overall Signal</div>
          <div className={`text-2xl font-bold uppercase tracking-wide ${getSignalColor(analysis.overall_signal)}`}>
            {analysis.overall_signal.replace('_', ' ')}
          </div>
        </div>
        <div className="text-left sm:text-right">
          <div className="text-slate-400 text-sm mb-1">Signal Strength</div>
          <div className="text-2xl font-mono font-bold text-slate-200">
            {formatPercentRaw(analysis.signal_strength * 100, 0)}
          </div>
        </div>
        <div className={`px-5 py-2.5 rounded-xl border ${getSignalBgColor(analysis.overall_signal)}`}>
          <Activity className="w-6 h-6" />
        </div>
      </div>

      {/* Price Info */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <IndicatorCard 
          label="Current Price" 
          value={`$${formatNumber(analysis.current_price)}`} 
        />
        <IndicatorCard 
          label="Change" 
          value={formatPercentRaw(analysis.change_percent)}
          trend={analysis.change_percent > 0 ? 'up' : analysis.change_percent < 0 ? 'down' : 'neutral'}
        />
        <IndicatorCard 
          label="Trend" 
          value={analysis.trend_direction} 
        />
        <IndicatorCard 
          label="ADX (Trend Strength)" 
          value={formatNumber(trend.adx_14)}
        />
      </div>

      {/* Momentum Section */}
      <Section title="Momentum" icon={Zap}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <IndicatorCard 
            label="RSI (14)" 
            value={formatNumber(momentum.rsi_14)}
            trend={getRsiTrend(momentum.rsi_14)}
          />
          <IndicatorCard 
            label="MACD Histogram" 
            value={formatNumber(momentum.macd_histogram)}
            trend={getMacdTrend(momentum.macd_histogram)}
          />
          <IndicatorCard 
            label="Stochastic %K" 
            value={formatNumber(momentum.stochastic_k)}
          />
          <IndicatorCard 
            label="CCI (20)" 
            value={formatNumber(momentum.cci_20)}
          />
        </div>
      </Section>

      {/* Moving Averages */}
      <Section title="Moving Averages" icon={TrendingUp}>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <IndicatorCard label="SMA 20" value={`$${formatNumber(moving_averages.sma_20)}`} />
          <IndicatorCard label="SMA 50" value={`$${formatNumber(moving_averages.sma_50)}`} />
          <IndicatorCard label="SMA 200" value={`$${formatNumber(moving_averages.sma_200)}`} />
          <IndicatorCard label="EMA 12" value={`$${formatNumber(moving_averages.ema_12)}`} />
          <IndicatorCard label="EMA 26" value={`$${formatNumber(moving_averages.ema_26)}`} />
          <IndicatorCard label="VWAP" value={`$${formatNumber(analysis.key_levels.vwap)}`} />
        </div>
      </Section>

      {/* Volatility */}
      <Section title="Volatility" icon={BarChart3}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <IndicatorCard label="ATR (14)" value={`$${formatNumber(volatility.atr_14)}`} />
          <IndicatorCard label="Historical Vol" value={formatPercentRaw(volatility.historical_volatility_30d)} />
          <IndicatorCard label="BB Upper" value={`$${formatNumber(volatility.bollinger_upper)}`} />
          <IndicatorCard label="BB Lower" value={`$${formatNumber(volatility.bollinger_lower)}`} />
        </div>
      </Section>

      {/* Support/Resistance */}
      {support_resistance && (
        <Section title="Support & Resistance" icon={Target}>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <IndicatorCard label="R2" value={`$${formatNumber(support_resistance.resistance_2)}`} />
            <IndicatorCard label="R1" value={`$${formatNumber(support_resistance.resistance_1)}`} />
            <IndicatorCard label="Pivot" value={`$${formatNumber(support_resistance.pivot)}`} />
            <IndicatorCard label="S1" value={`$${formatNumber(support_resistance.support_1)}`} />
            <IndicatorCard label="S2" value={`$${formatNumber(support_resistance.support_2)}`} />
          </div>
        </Section>
      )}

      {/* Volume */}
      <Section title="Volume" icon={Gauge}>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <IndicatorCard label="OBV" value={formatNumber(volume.obv, 0)} />
          <IndicatorCard label="Relative Vol" value={formatNumber(volume.relative_volume)} />
          <IndicatorCard label="Volume Trend" value={volume.volume_trend || 'N/A'} />
        </div>
      </Section>
    </div>
  );
};
