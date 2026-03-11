import { Building2, TrendingUp, DollarSign, PieChart, Users, Activity } from 'lucide-react';
import type { FundamentalAnalysis } from '../types/portfolio';
import { formatNumber, formatPercentRaw, formatCompactNumber, formatCurrency } from '../utils/formatters';

interface FundamentalPanelProps {
  fundamentals: FundamentalAnalysis;
}

const MetricCard = ({ label, value, subtext }: { label: string; value: string; subtext?: string }) => (
  <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 hover:border-slate-600/50 transition-colors">
    <div className="text-slate-400 text-xs uppercase tracking-wider mb-1.5">{label}</div>
    <div className="text-xl font-mono font-semibold text-slate-200">{value}</div>
    {subtext && <div className="text-slate-500 text-xs mt-1">{subtext}</div>}
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

export const FundamentalPanel = ({ fundamentals }: FundamentalPanelProps) => {
  const { company, valuation, profitability, financial_health, growth, dividend, ownership } = fundamentals;

  return (
    <div className="space-y-6 animate-in">
      {/* Company Header */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-slate-100">{company.name}</h2>
            <div className="flex flex-wrap items-center gap-2 mt-2 text-sm text-slate-400">
              <span className="bg-slate-700 px-2.5 py-1 rounded-lg font-mono">{company.symbol}</span>
              {company.sector && <span>{company.sector}</span>}
              {company.industry && <span className="text-slate-600">•</span>}
              {company.industry && <span>{company.industry}</span>}
              {company.country && <span className="text-slate-600">•</span>}
              {company.country && <span>{company.country}</span>}
            </div>
          </div>
          {company.employees && (
            <div className="text-right">
              <div className="text-slate-400 text-sm">Employees</div>
              <div className="text-lg font-mono text-slate-200">
                {formatCompactNumber(company.employees)}
              </div>
            </div>
          )}
        </div>
        {company.description && (
          <p className="text-slate-400 text-sm mt-4 leading-relaxed line-clamp-3">{company.description}</p>
        )}
      </div>

      {/* Valuation */}
      <Section title="Valuation" icon={DollarSign}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Market Cap" value={formatCompactNumber(valuation.market_cap)} />
          <MetricCard 
            label="P/E (Trailing)" 
            value={formatNumber(valuation.trailing_pe)}
            subtext={valuation.forward_pe ? `Forward: ${formatNumber(valuation.forward_pe)}` : undefined}
          />
          <MetricCard label="P/B Ratio" value={formatNumber(valuation.price_to_book)} />
          <MetricCard label="EV/EBITDA" value={formatNumber(valuation.ev_to_ebitda)} />
        </div>
      </Section>

      {/* Profitability */}
      <Section title="Profitability" icon={TrendingUp}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="ROE" value={formatPercentRaw(profitability.roe)} />
          <MetricCard label="ROA" value={formatPercentRaw(profitability.roa)} />
          <MetricCard label="Gross Margin" value={formatPercentRaw(profitability.gross_margin)} />
          <MetricCard label="Operating Margin" value={formatPercentRaw(profitability.operating_margin)} />
        </div>
      </Section>

      {/* Financial Health */}
      <Section title="Financial Health" icon={Activity}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Current Ratio" value={formatNumber(financial_health.current_ratio)} />
          <MetricCard label="Quick Ratio" value={formatNumber(financial_health.quick_ratio)} />
          <MetricCard label="Debt/Equity" value={formatNumber(financial_health.debt_to_equity)} />
          <MetricCard label="Interest Coverage" value={formatNumber(financial_health.interest_coverage)} />
        </div>
      </Section>

      {/* Growth */}
      <Section title="Growth" icon={TrendingUp}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Revenue Growth (YoY)" value={formatPercentRaw(growth.revenue_growth_yoy)} />
          <MetricCard label="Earnings Growth (YoY)" value={formatPercentRaw(growth.earnings_growth_yoy)} />
          <MetricCard label="3Y Rev CAGR" value={formatPercentRaw(growth.revenue_growth_3yr_cagr)} />
          <MetricCard label="3Y EPS CAGR" value={formatPercentRaw(growth.earnings_growth_3yr_cagr)} />
        </div>
      </Section>

      {/* Dividend */}
      {(dividend.dividend_yield !== undefined && (dividend.dividend_yield ?? 0) > 0) && (
        <Section title="Dividend" icon={PieChart}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="Dividend Yield" value={formatPercentRaw(dividend.dividend_yield)} />
            <MetricCard label="Dividend Rate" value={formatCurrency(dividend.dividend_rate)} />
            <MetricCard label="Payout Ratio" value={formatPercentRaw(dividend.payout_ratio)} />
            <MetricCard label="5Y Avg Yield" value={formatPercentRaw(dividend.five_year_avg_dividend_yield)} />
          </div>
        </Section>
      )}

      {/* Ownership */}
      <Section title="Ownership" icon={Users}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Insider Ownership" value={formatPercentRaw(ownership.insider_ownership)} />
          <MetricCard label="Institutional" value={formatPercentRaw(ownership.institutional_ownership)} />
          <MetricCard label="Short % Float" value={formatPercentRaw(ownership.short_percent_float)} />
          <MetricCard label="Shares Outstanding" value={formatCompactNumber(ownership.shares_outstanding)} />
        </div>
      </Section>

      {/* Data Quality */}
      <div className="flex items-center justify-between text-sm text-slate-400 bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
        <span>Data Quality Score</span>
        <div className="flex items-center gap-3">
          <div className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-emerald-500 rounded-full transition-all"
              style={{ width: `${fundamentals.data_quality_score * 100}%` }}
            />
          </div>
          <span className="font-mono text-slate-200">{formatPercentRaw(fundamentals.data_quality_score * 100)}</span>
        </div>
      </div>
    </div>
  );
};
