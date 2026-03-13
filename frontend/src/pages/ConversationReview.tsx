import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useConversation } from '../hooks/useConversation'
import { useAuth } from '../hooks/useAuth'
import AppHeader from '../components/AppHeader'
import {
  FileText,
  Heart,
  HeartOff,
  AlertTriangle,
  Shield,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  CheckCircle,
  Pencil,
} from 'lucide-react'

const NOTE_SECTIONS = [
  { key: 'participants', label: 'Participants Present' },
  { key: 'medical_status_explained', label: 'Medical Status Explained' },
  { key: 'prognosis_discussed', label: 'Prognosis Discussed' },
  { key: 'uncertainty_addressed', label: 'Uncertainty Addressed' },
  { key: 'family_understanding_noted', label: 'Family Understanding Noted' },
  { key: 'code_status', label: 'Code Status' },
  { key: 'surrogate_decision_maker', label: 'Surrogate Decision Maker' },
]

export default function ConversationReview() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { conversation, output, loading, loadConversation, finalizeConversation, updateConversation, generateOutput } =
    useConversation()

  const [copied, setCopied] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(NOTE_SECTIONS.map((s) => s.key))
  )
  const [finalizing, setFinalizing] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [editingSummary, setEditingSummary] = useState(false)
  const [editedSummary, setEditedSummary] = useState('')

  useEffect(() => {
    if (id) loadConversation(id)
  }, [id])

  useEffect(() => {
    if (output?.family_summary && !editedSummary) {
      setEditedSummary(output.family_summary)
    }
  }, [output])

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const copyPhysicianNote = () => {
    if (!output?.physician_note) return
    const text = NOTE_SECTIONS.map(
      (s) => `${s.label}:\n${output.physician_note[s.key] || 'N/A'}`
    ).join('\n\n')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleFinalize = async () => {
    if (!id) return
    setFinalizing(true)
    try {
      await finalizeConversation(id)
      navigate(`/conversations/${id}/success`)
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to finalize')
    } finally {
      setFinalizing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <AppHeader />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <div className="mb-6">
            <div className="h-7 w-48 skeleton-pulse rounded mb-2" />
            <div className="h-4 w-64 skeleton-pulse rounded" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="h-5 w-32 skeleton-pulse rounded mb-4" />
              <div className="space-y-3">
                <div className="h-4 w-full skeleton-pulse rounded" />
                <div className="h-4 w-full skeleton-pulse rounded" />
                <div className="h-4 w-3/4 skeleton-pulse rounded" />
                <div className="h-4 w-full skeleton-pulse rounded" />
                <div className="h-4 w-5/6 skeleton-pulse rounded" />
              </div>
            </div>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="h-5 w-32 skeleton-pulse rounded mb-4" />
              <div className="space-y-3">
                <div className="h-4 w-full skeleton-pulse rounded" />
                <div className="h-4 w-full skeleton-pulse rounded" />
                <div className="h-4 w-2/3 skeleton-pulse rounded" />
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (!conversation || !output) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-muted">Conversation or output not found.</p>
      </div>
    )
  }

  const redFlags = output.risk_flags.filter((f: any) => f.severity === 'red')
  const yellowFlags = output.risk_flags.filter((f: any) => f.severity === 'yellow')

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Title */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-body">
              Review: {conversation.patient_alias}
            </h2>
            <p className="text-sm text-muted mt-1 flex items-center gap-2 flex-wrap">
              Generated {new Date(output.created_at).toLocaleString()} &middot;
              Tone: {conversation.tone_setting}
              {conversation.family_present ? (
                <span className="inline-flex items-center gap-1 text-xs bg-clinical/10 text-clinical px-2 py-0.5 rounded-full font-medium">
                  <Heart className="w-3 h-3" /> Family Present
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs bg-navy/10 text-navy px-2 py-0.5 rounded-full font-medium">
                  <HeartOff className="w-3 h-3" /> Family Not Present
                </span>
              )}
            </p>
          </div>
          <button
            onClick={() => navigate('/new-conversation')}
            className="text-sm text-clinical hover:text-clinical-dark flex items-center gap-1"
          >
            <ArrowLeft className="w-4 h-4" /> Edit Inputs
          </button>
        </div>

        {/* Regenerate with tone */}
        <div className="mb-6 flex items-center gap-3">
          <span className="text-sm text-muted">Regenerate with tone:</span>
          {['optimistic', 'neutral', 'concerned'].map((t) => (
            <button
              key={t}
              onClick={async () => {
                if (!id) return
                setRegenerating(true)
                try {
                  await updateConversation(id, { tone_setting: t })
                  await generateOutput(id)
                  await loadConversation(id)
                } catch (err: any) {
                  alert('Failed to regenerate')
                } finally {
                  setRegenerating(false)
                }
              }}
              disabled={regenerating}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                conversation.tone_setting === t
                  ? 'bg-navy text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              } disabled:opacity-50`}
            >
              {t === 'optimistic' ? '🌤️ Hopeful' : t === 'neutral' ? '📋 Neutral' : '⚠️ Concerned'}
            </button>
          ))}
          {regenerating && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-navy" />}
        </div>

        {/* Risk Flags */}
        {output.risk_flags.length > 0 && (
          <div className="mb-6 space-y-2">
            {redFlags.map((flag: any, i: number) => (
              <div
                key={`red-${i}`}
                className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4"
              >
                <Shield className="w-5 h-5 text-danger mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-red-800">{flag.message}</p>
                  <p className="text-xs text-red-600 mt-1">{flag.suggestion}</p>
                </div>
              </div>
            ))}
            {yellowFlags.map((flag: any, i: number) => (
              <div
                key={`yellow-${i}`}
                className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4"
              >
                <AlertTriangle className="w-5 h-5 text-warning mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-amber-800">{flag.message}</p>
                  <p className="text-xs text-amber-600 mt-1">{flag.suggestion}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Family Summary */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-2 bg-gradient-to-r from-clinical/5 to-transparent">
              <Heart className="w-5 h-5 text-clinical" />
              <h3 className="font-bold text-body">Family Summary</h3>
              <button
                onClick={() => { setEditedSummary(editedSummary || output.family_summary); setEditingSummary(true) }}
                className="ml-auto p-1 text-muted hover:text-clinical transition-colors rounded"
                title="Edit summary"
              >
                <Pencil className="w-4 h-4" />
              </button>
            </div>
            <div className="px-6 py-5">
              {editingSummary ? (
                <div>
                  <textarea
                    value={editedSummary}
                    onChange={(e) => setEditedSummary(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm resize-none focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
                    rows={8}
                  />
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => setEditingSummary(false)}
                      className="px-4 py-2 bg-navy text-white text-xs font-medium rounded-lg hover:bg-navy-dark transition-colors"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => { setEditedSummary(output.family_summary); setEditingSummary(false) }}
                      className="px-4 py-2 border border-gray-200 text-xs font-medium rounded-lg text-muted hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  className="prose prose-sm max-w-none text-body leading-relaxed whitespace-pre-wrap cursor-pointer hover:bg-gray-50 rounded-lg p-2 -m-2 transition-colors"
                  onClick={() => { setEditedSummary(editedSummary || output.family_summary); setEditingSummary(true) }}
                  title="Click to edit"
                >
                  {editedSummary || output.family_summary}
                </div>
              )}
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-muted italic">
                  Written at approximately 6th-grade reading level for family
                  comprehension.
                </p>
              </div>
            </div>
          </div>

          {/* Physician Note */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-navy/5 to-transparent">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-navy" />
                <h3 className="font-bold text-body">Physician Note</h3>
              </div>
              <button
                onClick={copyPhysicianNote}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-navy/5 hover:bg-navy/10 text-navy transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3" /> Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" /> Copy to EHR
                  </>
                )}
              </button>
            </div>
            <div className="divide-y divide-gray-50">
              {NOTE_SECTIONS.map((section) => {
                const content = output.physician_note[section.key]
                if (!content) return null
                const isExpanded = expandedSections.has(section.key)
                return (
                  <div key={section.key} className="px-6">
                    <button
                      onClick={() => toggleSection(section.key)}
                      className="w-full py-3 flex items-center justify-between text-left"
                    >
                      <span className="text-sm font-semibold text-navy">
                        {section.label}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-muted" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-muted" />
                      )}
                    </button>
                    {isExpanded && (
                      <p className="pb-4 text-sm text-body leading-relaxed">
                        {content}
                      </p>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-end gap-3">
          <button
            onClick={() => navigate('/new-conversation')}
            className="px-6 py-3 border border-gray-200 rounded-xl text-sm font-medium text-muted hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 inline mr-1" />
            Edit Inputs
          </button>
          <button
            onClick={handleFinalize}
            disabled={finalizing || conversation.status === 'FINALIZED'}
            className="px-8 py-3 bg-success hover:bg-green-600 text-white font-semibold rounded-xl transition-colors disabled:opacity-50 flex items-center gap-2 shadow-lg"
          >
            {finalizing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Finalizing...
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                Finalize &amp; Log
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  )
}
