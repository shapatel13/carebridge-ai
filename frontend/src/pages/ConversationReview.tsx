import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useConversation } from '../hooks/useConversation'
import { useAuth } from '../hooks/useAuth'
import AppHeader from '../components/AppHeader'
import RiskTimeline from '../components/RiskTimeline'
import { generateFamilySummaryPdf } from '../lib/generatePdf'
import { getReadabilityGrade, gradeSeverity } from '../lib/readability'
import CommunicationScorecard from '../components/CommunicationScorecard'
import {
  FileText,
  Heart,
  HeartOff,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  CheckCircle,
  Pencil,
  Download,
  BookOpen,
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

  // Comparison state
  const [previousOutput, setPreviousOutput] = useState<{ summary: string; tone: string } | null>(null)
  const [showComparison, setShowComparison] = useState(false)

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

  const handleDownloadPdf = () => {
    if (!output || !conversation) return
    generateFamilySummaryPdf({
      hospitalName: 'Metro General Hospital',
      physicianName: user?.full_name || 'Physician',
      patientAlias: conversation.patient_alias,
      familySummary: editedSummary || output.family_summary,
      date: new Date(output.created_at).toLocaleDateString(),
      language: conversation.language,
    })
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors">
        <AppHeader />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <div className="mb-6">
            <div className="h-7 w-48 skeleton-pulse rounded mb-2" />
            <div className="h-4 w-64 skeleton-pulse rounded" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 p-6">
              <div className="h-5 w-32 skeleton-pulse rounded mb-4" />
              <div className="space-y-3">
                <div className="h-4 w-full skeleton-pulse rounded" />
                <div className="h-4 w-full skeleton-pulse rounded" />
                <div className="h-4 w-3/4 skeleton-pulse rounded" />
                <div className="h-4 w-full skeleton-pulse rounded" />
                <div className="h-4 w-5/6 skeleton-pulse rounded" />
              </div>
            </div>
            <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 p-6">
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
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900">
        <p className="text-muted dark:text-slate-400">Conversation or output not found.</p>
      </div>
    )
  }

  // Readability — language-aware
  const { grade: readabilityGrade, source: readabilitySource } = getReadabilityGrade(
    editedSummary || output.family_summary,
    conversation.language,
    output.readability_grade,
  )
  const readabilitySeverity = gradeSeverity(readabilityGrade)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors">
      <AppHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Title */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-body dark:text-slate-100">
              Review: {conversation.patient_alias}
            </h2>
            <p className="text-sm text-muted dark:text-slate-400 mt-1 flex items-center gap-2 flex-wrap">
              Generated {new Date(output.created_at).toLocaleString()} &middot;
              Tone: {conversation.tone_setting}
              {conversation.family_present ? (
                <span className="inline-flex items-center gap-1 text-xs bg-clinical/10 text-clinical px-2 py-0.5 rounded-full font-medium">
                  <Heart className="w-3 h-3" /> Family Present
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs bg-navy/10 text-navy dark:bg-slate-700 dark:text-slate-300 px-2 py-0.5 rounded-full font-medium">
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
          <span className="text-sm text-muted dark:text-slate-400">Regenerate with tone:</span>
          {['optimistic', 'neutral', 'concerned'].map((t) => (
            <button
              key={t}
              onClick={async () => {
                if (!id || !output) return
                setRegenerating(true)
                // Save current output before regenerating
                setPreviousOutput({
                  summary: editedSummary || output.family_summary,
                  tone: conversation.tone_setting,
                })
                try {
                  await updateConversation(id, { tone_setting: t })
                  await generateOutput(id)
                  await loadConversation(id)
                  setShowComparison(true)
                } catch (err: any) {
                  alert('Failed to regenerate')
                  setPreviousOutput(null)
                } finally {
                  setRegenerating(false)
                }
              }}
              disabled={regenerating}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                conversation.tone_setting === t
                  ? 'bg-navy text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600'
              } disabled:opacity-50`}
            >
              {t === 'optimistic' ? '🌤️ Hopeful' : t === 'neutral' ? '📋 Neutral' : '⚠️ Concerned'}
            </button>
          ))}
          {regenerating && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-navy" />}
        </div>

        {/* Side-by-side comparison */}
        {showComparison && previousOutput && output && (
          <div className="mb-6 bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 overflow-hidden transition-colors">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700 flex items-center justify-between bg-gradient-to-r from-clinical/5 to-navy/5 dark:from-clinical/10 dark:to-navy/10">
              <h3 className="font-bold text-body dark:text-slate-100">Tone Comparison</h3>
              <button
                onClick={() => setShowComparison(false)}
                className="text-xs text-muted dark:text-slate-400 hover:text-body dark:hover:text-slate-200 transition-colors"
              >
                Dismiss
              </button>
            </div>
            <div className="grid grid-cols-2 divide-x divide-gray-100 dark:divide-slate-700">
              <div className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs font-medium bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-slate-300 px-2 py-0.5 rounded-full">
                    Previous: {previousOutput.tone}
                  </span>
                </div>
                <p className="text-sm text-body dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
                  {previousOutput.summary}
                </p>
              </div>
              <div className="p-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xs font-medium bg-navy text-white px-2 py-0.5 rounded-full">
                    Current: {conversation.tone_setting}
                  </span>
                </div>
                <p className="text-sm text-body dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
                  {editedSummary || output.family_summary}
                </p>
              </div>
            </div>
            <div className="px-6 py-3 border-t border-gray-100 dark:border-slate-700 flex justify-end gap-2">
              <button
                onClick={() => {
                  setEditedSummary(previousOutput.summary)
                  setShowComparison(false)
                  setPreviousOutput(null)
                }}
                className="px-4 py-2 text-xs font-medium border border-gray-200 dark:border-slate-600 rounded-lg text-muted dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
              >
                Revert to Previous
              </button>
              <button
                onClick={() => {
                  setShowComparison(false)
                  setPreviousOutput(null)
                }}
                className="px-4 py-2 text-xs font-medium bg-navy text-white rounded-lg hover:bg-navy-dark transition-colors"
              >
                Keep New
              </button>
            </div>
          </div>
        )}

        {/* AI Communication Insights */}
        {output.ai_insights?.communication_scores && (
          <CommunicationScorecard insights={output.ai_insights as any} />
        )}

        {/* Risk Timeline */}
        <RiskTimeline flags={output.risk_flags} />

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Family Summary */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 overflow-hidden transition-colors">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700 flex items-center gap-2 bg-gradient-to-r from-clinical/5 to-transparent dark:from-clinical/10">
              <Heart className="w-5 h-5 text-clinical" />
              <h3 className="font-bold text-body dark:text-slate-100">Family Summary</h3>
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
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100 text-sm resize-none focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
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
                      className="px-4 py-2 border border-gray-200 dark:border-slate-600 text-xs font-medium rounded-lg text-muted dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  className="prose prose-sm dark:prose-invert max-w-none text-body dark:text-slate-200 leading-relaxed whitespace-pre-wrap cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-700 rounded-lg p-2 -m-2 transition-colors"
                  onClick={() => { setEditedSummary(editedSummary || output.family_summary); setEditingSummary(true) }}
                  title="Click to edit"
                >
                  {editedSummary || output.family_summary}
                </div>
              )}
              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-700 flex items-center justify-between">
                <p className="text-xs text-muted dark:text-slate-400 italic">
                  Family-friendly reading level target: Grade 6 or below
                </p>
                <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${
                  readabilitySeverity === 'green' ? 'bg-green-50 text-success dark:bg-green-900/30 dark:text-green-400' :
                  readabilitySeverity === 'yellow' ? 'bg-amber-50 text-warning dark:bg-amber-900/30 dark:text-amber-400' :
                  'bg-red-50 text-danger dark:bg-red-900/30 dark:text-red-400'
                }`}>
                  <BookOpen className="w-3 h-3" />
                  Grade {readabilityGrade}
                  {readabilitySource === 'ai-assessed' && (
                    <span className="ml-1 text-[10px] bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-300 px-1.5 py-0.5 rounded-full font-bold">AI</span>
                  )}
                </span>
              </div>
            </div>
          </div>

          {/* Physician Note */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 overflow-hidden transition-colors">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-700 flex items-center justify-between bg-gradient-to-r from-navy/5 to-transparent dark:from-navy/10">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-navy dark:text-clinical" />
                <h3 className="font-bold text-body dark:text-slate-100">Physician Note</h3>
              </div>
              <button
                onClick={copyPhysicianNote}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-navy/5 hover:bg-navy/10 dark:bg-slate-700 dark:hover:bg-slate-600 text-navy dark:text-slate-200 transition-colors"
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
            <div className="divide-y divide-gray-50 dark:divide-slate-700">
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
                      <span className="text-sm font-semibold text-navy dark:text-clinical">
                        {section.label}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-muted" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-muted" />
                      )}
                    </button>
                    {isExpanded && (
                      <p className="pb-4 text-sm text-body dark:text-slate-300 leading-relaxed">
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
            className="px-6 py-3 border border-gray-200 dark:border-slate-600 rounded-xl text-sm font-medium text-muted dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 inline mr-1" />
            Edit Inputs
          </button>
          <button
            onClick={handleDownloadPdf}
            className="px-6 py-3 border border-clinical rounded-xl text-sm font-medium text-clinical hover:bg-clinical/5 transition-colors flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Download PDF
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
