import { AlertTriangle, Shield, TrendingDown, BarChart3, Activity } from 'lucide-react';
import type { RiskAnalysis } from '../types/portfolio';
import { formatNumber, formatPercentRaw, getRiskLevelColor } from '../utils/formatters';

interface RiskPanelProps {
  risk: RiskAnalysis;
}

const MetricCard = ({ label, value, suffix = '', warning }: { label: string; value: string; suffix?: string; warning?: boolean }) => (
  <div className={`p-4 rounded-xl border ${warning ? 'bg-rose-500/5 border-rose-500/20' : 'bg-slate-800/50 border-slate-700/50'}`}>
    <div className="text-slate-400 text-xs uppercase tracking-wider mb-1.5">{label}</div>
    <div className={`text-xl font-mono font-semibold ${warning ? 'text-rose-400' : 'text-slate-200'}`}>
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

export const RiskPanel = ({ risk }: RiskPanelProps) => {
  const { metrics, correlation, concentration, alerts, recommendations } = risk;

  return (
    <div className="space-y-6 animate-in">
      {/* Risk Level Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 
                      bg-slate-800/50 rounded-xl border border-slate-700/50">
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8 text-slate-400" />
          <div>
            <div className="text-slate-400 text-sm">Risk Profile</div>
            <div className={`text-2xl font-bold uppercase ${getRiskLevelColor(risk.risk_level).split(' ')[0]}`}>
              {risk.risk_level}
            </div>
          </div>
        </div>
        <div className={`px-4 py-2 rounded-xl border ${getRiskLevelColor(risk.risk_level)}`}>
          <span className="text-sm font-medium">
            {risk.risk_level === 'low' ? 'Conservative' : 
             risk.risk_level === 'moderate' ? 'Balanced' : 
             risk.risk_level === 'high' ? 'Aggressive' : 'Speculative'}
          </span>
        </div>
      </div>

      {/* Core Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard 
          label="Volatility (Annual)" 
          value={formatPercentRaw(metrics.volatility_annual)}
          warning={metrics.volatility_annual > 0.25}
        />
        <MetricCard 
          label="Sharpe Ratio" 
          value={formatNumber(metrics.sharpe_ratio)}
          warning={metrics.sharpe_ratio < 0.5}
        />
        <MetricCard 
          label="Max Drawdown" 
          value={formatPercentRaw(metrics.max_drawdown)}
          warning={metrics.max_drawdown < -0.20}
        />
        <MetricCard label="Sortino Ratio" value={formatNumber(metrics.sortino_ratio)} />
      </div>

      {/* Advanced Metrics */}
      <Section title="Risk Metrics" icon={BarChart3}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="VaR (95%)" value={formatPercentRaw(metrics.var_95)} />
          <MetricCard label="CVaR (95%)" value={formatPercentRaw(metrics.cvar_95)} />
          <MetricCard label="Calmar Ratio" value={formatNumber(metrics.calmar_ratio)} />
          {metrics.beta !== undefined && <MetricCard label="Beta" value={formatNumber(metrics.beta)} />}
          {metrics.alpha !== undefined && <MetricCard label="Alpha" value={formatPercentRaw(metrics.alpha)} />}
          {metrics.treynor_ratio !== undefined && <MetricCard label="Treynor Ratio" value={formatNumber(metrics.treynor_ratio)} />}
        </div>
      </Section>

      {/* Concentration */}
      <Section title="Concentration Analysis" icon={Activity}>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <MetricCard 
            label="Top Holding" 
            value={formatPercentRaw(concentration.top_holding_percent)}
            warning={concentration.top_holding_percent > 20}
          />
          <MetricCard label="Top 5 Holdings" value={formatPercentRaw(concentration.top_5_holdings_percent)} />
          <MetricCard label="HHI Index" value={formatNumber(concentration.herfindahl_index)} />
        </div>
      </Section>

      {/* Correlation Matrix */}
      {correlation.symbols.length > 1 && (
        <Section title="Correlation Matrix" icon={BarChart3}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="text-left text-slate-400 text-sm p-2 sticky left-0 bg-slate-800/30"></th>
                  {correlation.symbols.map((sym) => (
                    <th key={sym} className="text-center text-slate-400 text-sm p-2 font-mono">{sym}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {correlation.matrix.map((row, i) => (
                  <tr key={i}>
                    <td className="text-slate-300 text-sm font-medium p-2 font-mono sticky left-0 bg-slate-800/30">{correlation.symbols[i]}</td>
                    {row.map((val, j) => (
                      <td 
                        key={j} 
                        className={`text-center text-sm p-2 font-mono ${
                          Math.abs(val) > 0.8 ? 'text-rose-400 font-semibold' : 
                          Math.abs(val) < 0.3 ? 'text-emerald-400' : 
                          'text-slate-400'
                        }`}
                      >
                        {val.toFixed(2)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="bg-rose-500/5 rounded-xl p-5 border border-rose-500/20">
          <h3 className="text-lg font-semibold text-rose-400 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Risk Alerts
          </h3>
          <ul className="space-y-2">
            {alerts.map((alert, index) => (
              <li key={index} className="text-sm text-slate-300 flex items-start gap-2">
                <span className="text-rose-400 mt-0.5">•</span>
                {alert}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-emerald-500/5 rounded-xl p-5 border border-emerald-500/20">
          <h3 className="text-lg font-semibold text-emerald-400 mb-4">Recommendations</h3>
          <ul className="space-y-2">
            {recommendations.map((rec, index) => (
              <li key={index} className="text-sm text-slate-300 flex items-start gap-2">
                <span className="text-emerald-400 mt-0.5">→</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
