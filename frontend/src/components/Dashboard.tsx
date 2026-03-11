import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { 
  LayoutDashboard, 
  TrendingUp, 
  PieChart, 
  Shield, 
  Brain,
  Settings,
  Menu,
  X,
  Loader2,
  AlertCircle,
  Activity
} from 'lucide-react';
import { usePrices, useTechnicalAnalysis, useFundamentals, useSymbolAI, useHealth } from '../hooks/usePortfolio';
import { SymbolSearch } from './SymbolSearch';
import { PriceChart } from './PriceChart';
import { TechnicalPanel } from './TechnicalPanel';
import { FundamentalPanel } from './FundamentalPanel';
import { RiskPanel } from './RiskPanel';
import { AIInsightsPanel } from './AIInsightsPanel';
import type { TimeFrame, TabType } from '../types/portfolio';

const TIMEFRAMES: { label: string; value: TimeFrame }[] = [
  { label: '1D', value: '1d' },
  { label: '1W', value: '5d' },
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' },
];

const NAV_ITEMS: { id: TabType; label: string; icon: React.ElementType }[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'technical', label: 'Technical', icon: TrendingUp },
  { id: 'fundamental', label: 'Fundamental', icon: PieChart },
  { id: 'risk', label: 'Risk', icon: Shield },
  { id: 'ai', label: 'AI Analysis', icon: Brain },
];

export const Dashboard = () => {
  const { symbol: urlSymbol } = useParams<{ symbol: string }>();
  const [selectedSymbol, setSelectedSymbol] = useState<string>(urlSymbol || 'AAPL');
  const [timeframe, setTimeframe] = useState<TimeFrame>('1y');
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Fetch data
  const { data: prices, isLoading: pricesLoading, error: pricesError } = usePrices(selectedSymbol, timeframe);
  const { analysis: technical, isLoading: techLoading } = useTechnicalAnalysis(selectedSymbol, timeframe);
  const { fundamentals, isLoading: fundLoading } = useFundamentals(selectedSymbol);
  const { aiAnalysis, isLoading: aiLoading } = useSymbolAI(selectedSymbol);
  const { isConnected, error: healthError } = useHealth();

  const isLoading = pricesLoading || techLoading || fundLoading || aiLoading;

  const handleSymbolSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    window.history.replaceState(null, '', `/symbol/${symbol}`);
  };

  const renderContent = () => {
    if (healthError) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-200 mb-2">Backend Not Connected</h3>
            <p className="text-slate-400">Please make sure the backend is running on localhost:8000</p>
          </div>
        </div>
      );
    }

    if (pricesError) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-200 mb-2">Error Loading Data</h3>
            <p className="text-slate-400">Failed to fetch data for {selectedSymbol}</p>
          </div>
        </div>
      );
    }

    switch (activeTab) {
      case 'technical':
        return technical ? <TechnicalPanel analysis={technical} /> : null;
      case 'fundamental':
        return fundamentals ? <FundamentalPanel fundamentals={fundamentals} /> : null;
      case 'risk':
        return (
          <div className="space-y-6">
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
              <h3 className="text-lg font-semibold text-slate-200 mb-2">Risk Analysis</h3>
              <p className="text-slate-400">Risk analysis is available for portfolios. Create a portfolio to see risk metrics.</p>
            </div>
          </div>
        );
      case 'ai':
        return aiAnalysis ? <AIInsightsPanel analysis={aiAnalysis} /> : null;
      default:
        return (
          <div className="space-y-6">
            {/* Chart */}
            <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-200">Price Chart</h3>
                <div className="flex gap-1">
                  {TIMEFRAMES.map((tf) => (
                    <button
                      key={tf.value}
                      onClick={() => setTimeframe(tf.value)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                        timeframe === tf.value
                          ? 'bg-emerald-500 text-white'
                          : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                      }`}
                    >
                      {tf.label}
                    </button>
                  ))}
                </div>
              </div>
              {prices && prices.data.length > 0 ? (
                <PriceChart data={prices.data} technical={technical} />
              ) : (
                <div className="h-96 flex items-center justify-center text-slate-500">
                  {pricesLoading ? (
                    <Loader2 className="w-8 h-8 animate-spin" />
                  ) : (
                    'No data available'
                  )}
                </div>
              )}
            </div>

            {/* Quick Stats */}
            {technical && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <div className="text-slate-400 text-xs uppercase mb-1">Signal</div>
                  <div className={`text-lg font-semibold capitalize ${
                    technical.overall_signal.includes('buy') ? 'text-emerald-400' :
                    technical.overall_signal.includes('sell') ? 'text-rose-400' :
                    'text-amber-400'
                  }`}>
                    {technical.overall_signal.replace('_', ' ')}
                  </div>
                </div>
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <div className="text-slate-400 text-xs uppercase mb-1">Trend</div>
                  <div className="text-lg font-semibold text-slate-200 capitalize">
                    {technical.trend_direction}
                  </div>
                </div>
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <div className="text-slate-400 text-xs uppercase mb-1">RSI (14)</div>
                  <div className="text-lg font-mono text-slate-200">
                    {technical.momentum.rsi_14?.toFixed(2) || 'N/A'}
                  </div>
                </div>
                <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                  <div className="text-slate-400 text-xs uppercase mb-1">Volatility</div>
                  <div className="text-lg font-mono text-slate-200">
                    {technical.volatility.historical_volatility_30d 
                      ? `${(technical.volatility.historical_volatility_30d * 100).toFixed(1)}%`
                      : 'N/A'}
                  </div>
                </div>
              </div>
            )}

            {/* AI Summary */}
            {aiAnalysis && (
              <div className="bg-violet-500/5 rounded-xl p-5 border border-violet-500/20">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-5 h-5 text-violet-400" />
                  <h3 className="font-semibold text-slate-200">AI Summary</h3>
                </div>
                <p className="text-slate-300 text-sm">{aiAnalysis.summary}</p>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Sidebar */}
      <aside 
        className={`fixed left-0 top-0 h-full bg-slate-900 border-r border-slate-800 transition-all duration-300 z-40 ${
          sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'
        }`}
      >
        <div className="p-5 h-full flex flex-col">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg text-slate-100">AlphaTrade</h1>
              <p className="text-xs text-slate-500">AI Portfolio Analytics</p>
            </div>
          </div>

          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg mb-4 text-xs ${
            isConnected ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
          }`}>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
            {isConnected ? 'Connected to API' : 'Backend Offline'}
          </div>

          {/* Search */}
          <div className="mb-6">
            <SymbolSearch onSelect={handleSymbolSelect} value={selectedSymbol} />
          </div>

          {/* Navigation */}
          <nav className="space-y-1 flex-1">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    activeTab === item.id
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="pt-4 border-t border-slate-800">
            <button className="flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-slate-200 w-full rounded-xl hover:bg-slate-800 transition-colors">
              <Settings className="w-5 h-5" />
              <span>Settings</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`transition-all duration-300 ${sidebarOpen ? 'ml-72' : 'ml-0'}`}>
        {/* Header */}
        <header className="sticky top-0 z-30 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 transition-colors"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
              <div>
                <h2 className="text-2xl font-bold text-slate-100">{selectedSymbol}</h2>
                {technical && (
                  <p className="text-sm text-slate-400">
                    ${technical.current_price.toFixed(2)} 
                    <span className={technical.change_percent >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                      {' '}{technical.change_percent >= 0 ? '+' : ''}{technical.change_percent.toFixed(2)}%
                    </span>
                  </p>
                )}
              </div>
            </div>

            {isLoading && (
              <div className="flex items-center gap-2 text-slate-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="text-sm">Loading...</span>
              </div>
            )}
          </div>
        </header>

        {/* Content */}
        <div className="p-6 max-w-7xl mx-auto">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};
