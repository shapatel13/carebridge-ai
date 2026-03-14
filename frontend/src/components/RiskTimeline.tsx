import { useState } from 'react'
import { Shield, AlertTriangle, ChevronDown, ChevronUp, ClipboardCopy, Check } from 'lucide-react'

interface RiskFlag {
  type: string
  severity: string
  message: string
  suggestion: string
}

interface Props {
  flags: RiskFlag[]
}

export default function RiskTimeline({ flags }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<Set<number>>(new Set())
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null)

  // Sort: red first, then yellow
  const sorted = [...flags].sort((a, b) => {
    if (a.severity === 'red' && b.severity !== 'red') return -1
    if (a.severity !== 'red' && b.severity === 'red') return 1
    return 0
  })

  const toggle = (i: number) => {
    setExpandedIdx((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  const copyFollowUp = (suggestion: string, idx: number) => {
    navigator.clipboard.writeText(suggestion)
    setCopiedIdx(idx)
    setTimeout(() => setCopiedIdx(null), 2000)
  }

  if (flags.length === 0) return null

  return (
    <div className="mb-6">
      <h3 className="text-sm font-bold text-body dark:text-slate-100 mb-4 flex items-center gap-2">
        <Shield className="w-4 h-4 text-navy dark:text-clinical" />
        Risk Assessment Timeline
      </h3>
      <div className="relative pl-6">
        {/* Vertical line */}
        <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-gray-200 dark:bg-slate-600" />

        {sorted.map((flag, i) => {
          const isRed = flag.severity === 'red'
          const isExpanded = expandedIdx.has(i)

          return (
            <div key={i} className="relative mb-4 last:mb-0">
              {/* Timeline dot */}
              <div
                className={`absolute -left-6 top-1.5 w-[14px] h-[14px] rounded-full border-2 ${
                  isRed
                    ? 'bg-danger border-danger'
                    : 'bg-warning border-warning'
                }`}
              >
                <div className="absolute inset-0.5 rounded-full bg-white opacity-40" />
              </div>

              {/* Card */}
              <div
                className={`rounded-xl border p-4 transition-all ${
                  isRed
                    ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
                    : 'bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800'
                }`}
              >
                <button
                  onClick={() => toggle(i)}
                  className="w-full flex items-start gap-3 text-left"
                >
                  {isRed ? (
                    <Shield className="w-5 h-5 text-danger mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-warning mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold ${isRed ? 'text-red-800 dark:text-red-300' : 'text-amber-800 dark:text-amber-300'}`}>
                      {flag.message}
                    </p>
                    <span className={`text-[10px] font-medium uppercase tracking-wide ${isRed ? 'text-red-500 dark:text-red-400' : 'text-amber-500 dark:text-amber-400'}`}>
                      {flag.type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-muted flex-shrink-0 mt-0.5" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted flex-shrink-0 mt-0.5" />
                  )}
                </button>

                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-dashed border-current/20 ml-8">
                    <p className={`text-xs ${isRed ? 'text-red-700 dark:text-red-300' : 'text-amber-700 dark:text-amber-300'} mb-2`}>
                      {flag.suggestion}
                    </p>
                    <button
                      onClick={() => copyFollowUp(flag.suggestion, i)}
                      className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-md transition-colors ${
                        isRed
                          ? 'bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-800/50 dark:text-red-300'
                          : 'bg-amber-100 text-amber-700 hover:bg-amber-200 dark:bg-amber-800/50 dark:text-amber-300'
                      }`}
                    >
                      {copiedIdx === i ? (
                        <><Check className="w-3 h-3" /> Copied!</>
                      ) : (
                        <><ClipboardCopy className="w-3 h-3" /> Copy Follow-up</>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
