import { useState } from 'react'
import {
  Heart,
  Eye,
  ClipboardCheck,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  MessageCircle,
  ArrowRight,
} from 'lucide-react'

interface CommunicationScores {
  empathy: number
  clarity: number
  completeness: number
  overall: number
  empathy_rationale?: string
  clarity_rationale?: string
  completeness_rationale?: string
}

interface Props {
  insights: {
    communication_scores: CommunicationScores
    family_takeaway: string
    next_steps: string[]
  }
}

function ScoreBar({ label, score, icon: Icon, rationale, color }: {
  label: string
  score: number
  icon: React.ComponentType<{ className?: string }>
  rationale?: string
  color: string
}) {
  const pct = Math.min(score * 10, 100)
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-gray-600 dark:text-slate-300 flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5" />
          {label}
        </span>
        <span className={`text-sm font-bold ${color}`}>{score}/10</span>
      </div>
      <div className="h-2 bg-gray-100 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${
            score >= 8 ? 'bg-green-500' : score >= 6 ? 'bg-amber-500' : 'bg-red-500'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {rationale && (
        <p className="text-[11px] text-gray-400 dark:text-slate-500 leading-relaxed">{rationale}</p>
      )}
    </div>
  )
}

export default function CommunicationScorecard({ insights }: Props) {
  const [expanded, setExpanded] = useState(false)
  const { communication_scores: scores, family_takeaway, next_steps } = insights

  const overallColor =
    scores.overall >= 8 ? 'text-green-600 dark:text-green-400' :
    scores.overall >= 6 ? 'text-amber-600 dark:text-amber-400' :
    'text-red-600 dark:text-red-400'

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 overflow-hidden transition-colors mb-6">
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 flex items-center justify-between bg-gradient-to-r from-purple-50 to-clinical/5 dark:from-purple-900/20 dark:to-clinical/10 hover:from-purple-100 dark:hover:from-purple-900/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-clinical flex items-center justify-center">
            <Lightbulb className="w-5 h-5 text-white" />
          </div>
          <div className="text-left">
            <h3 className="font-bold text-body dark:text-slate-100">AI Communication Insights</h3>
            <p className="text-xs text-muted dark:text-slate-400">
              Scorecard, family perception, and next-step prep
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right mr-2">
            <p className="text-[10px] uppercase tracking-wide text-gray-400 dark:text-slate-500">Overall</p>
            <p className={`text-2xl font-black ${overallColor}`}>{scores.overall}</p>
          </div>
          {expanded ? <ChevronUp className="w-5 h-5 text-muted" /> : <ChevronDown className="w-5 h-5 text-muted" />}
        </div>
      </button>

      {expanded && (
        <div className="divide-y divide-gray-100 dark:divide-slate-700">
          {/* Communication Scores */}
          <div className="px-6 py-5">
            <h4 className="text-sm font-semibold text-body dark:text-slate-100 mb-4">Communication Scorecard</h4>
            <div className="space-y-4">
              <ScoreBar
                label="Empathy"
                score={scores.empathy}
                icon={Heart}
                rationale={scores.empathy_rationale}
                color={scores.empathy >= 8 ? 'text-green-600 dark:text-green-400' : scores.empathy >= 6 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}
              />
              <ScoreBar
                label="Clarity"
                score={scores.clarity}
                icon={Eye}
                rationale={scores.clarity_rationale}
                color={scores.clarity >= 8 ? 'text-green-600 dark:text-green-400' : scores.clarity >= 6 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}
              />
              <ScoreBar
                label="Completeness"
                score={scores.completeness}
                icon={ClipboardCheck}
                rationale={scores.completeness_rationale}
                color={scores.completeness >= 8 ? 'text-green-600 dark:text-green-400' : scores.completeness >= 6 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}
              />
            </div>
          </div>

          {/* Family Takeaway */}
          <div className="px-6 py-5">
            <h4 className="text-sm font-semibold text-body dark:text-slate-100 mb-3 flex items-center gap-2">
              <MessageCircle className="w-4 h-4 text-purple-500" />
              What the Family Likely Heard
            </h4>
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4 border border-purple-100 dark:border-purple-800/30">
              <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed italic">
                "{family_takeaway}"
              </p>
            </div>
          </div>

          {/* Next Steps */}
          <div className="px-6 py-5">
            <h4 className="text-sm font-semibold text-body dark:text-slate-100 mb-3 flex items-center gap-2">
              <ArrowRight className="w-4 h-4 text-clinical" />
              Next Conversation Prep
            </h4>
            <ul className="space-y-2.5">
              {next_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-clinical/10 dark:bg-clinical/20 text-clinical text-xs font-bold flex items-center justify-center mt-0.5">
                    {i + 1}
                  </span>
                  <p className="text-sm text-gray-700 dark:text-slate-300 leading-relaxed">{step}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
