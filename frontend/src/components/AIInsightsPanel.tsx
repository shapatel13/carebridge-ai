import { Brain, Lightbulb, AlertTriangle, TrendingUp } from 'lucide-react';
import type { AIAnalysis } from '../types/portfolio';
import { getSentimentColor } from '../utils/formatters';

interface AIInsightsPanelProps {
  analysis: AIAnalysis;
}

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'technical':
      return <TrendingUp className="w-4 h-4" />;
    case 'fundamental':
      return <Lightbulb className="w-4 h-4" />;
    case 'risk':
      return <AlertTriangle className="w-4 h-4" />;
    default:
      return <Brain className="w-4 h-4" />;
  }
};

export const AIInsightsPanel = ({ analysis }: AIInsightsPanelProps) => {
  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-violet-500/10 rounded-xl border border-violet-500/30">
            <Brain className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-200">AI Analysis</h3>
            <p className="text-slate-400 text-sm">Powered by {analysis.model_used}</p>
          </div>
        </div>
        <span className="text-slate-500 text-xs">
          Generated: {new Date(analysis.generated_at).toLocaleString()}
        </span>
      </div>

      {/* Summary */}
      <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50">
        <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">Executive Summary</h4>
        <p className="text-slate-200 leading-relaxed">{analysis.summary}</p>
      </div>

      {/* Insights */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Key Insights</h4>
        {analysis.insights.map((insight, index) => (
          <div
            key={index}
            className={`p-4 rounded-xl border ${getSentimentColor(insight.sentiment)}`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                {getCategoryIcon(insight.category)}
                <span className="font-semibold">{insight.title}</span>
              </div>
              <span className="text-xs opacity-70">
                Confidence: {Math.round(insight.confidence * 100)}%
              </span>
            </div>
            <p className="text-sm mb-3 opacity-90">{insight.description}</p>
            {insight.action_items.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {insight.action_items.map((action, i) => (
                  <span
                    key={i}
                    className="text-xs bg-black/20 px-2.5 py-1 rounded-lg font-medium"
                  >
                    {action}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Risks & Opportunities */}
      <div className="grid md:grid-cols-2 gap-4">
        {analysis.key_risks.length > 0 && (
          <div className="bg-rose-500/5 rounded-xl p-5 border border-rose-500/20">
            <h4 className="text-sm font-medium text-rose-400 uppercase tracking-wider mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Key Risks
            </h4>
            <ul className="space-y-2">
              {analysis.key_risks.map((risk, index) => (
                <li key={index} className="text-sm text-slate-300 flex items-start gap-2">
                  <span className="text-rose-400 mt-0.5">•</span>
                  {risk}
                </li>
              ))}
            </ul>
          </div>
        )}

        {analysis.opportunities.length > 0 && (
          <div className="bg-emerald-500/5 rounded-xl p-5 border border-emerald-500/20">
            <h4 className="text-sm font-medium text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              Opportunities
            </h4>
            <ul className="space-y-2">
              {analysis.opportunities.map((opp, index) => (
                <li key={index} className="text-sm text-slate-300 flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">•</span>
                  {opp}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
