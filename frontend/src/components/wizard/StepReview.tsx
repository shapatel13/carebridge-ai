import { ChevronRight, Pencil, Heart, HeartOff, Globe, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'

const LANGUAGE_LABELS: Record<string, string> = {
  english: '🇺🇸 English',
  spanish: '🇪🇸 Español',
  chinese: '🇨🇳 中文',
  vietnamese: '🇻🇳 Tiếng Việt',
  arabic: '🇸🇦 العربية',
  korean: '🇰🇷 한국어',
}

interface Props {
  patientAlias: string
  familyPresent: boolean
  language: string
  surName: string
  surRelation: string
  organSupports: string[]
  segments: string[]
  tone: string
  codeDiscussed: boolean
  annotations: string[]
  familyQuestions: string[]
  onStepClick: (step: number) => void
  onGenerate: () => void
  generating: boolean
}

export default function StepReview({
  patientAlias, familyPresent, language, surName, surRelation, organSupports,
  segments, tone, codeDiscussed, annotations, familyQuestions,
  onStepClick, onGenerate, generating,
}: Props) {
  const wordCount = segments.join(' ').split(/\s+/).filter(Boolean).length

  const transcriptText = segments.join(' ').toLowerCase()
  const PROGNOSIS_RX = /prognos|weeks?|months?|trajector|surviv|terminal|end.of.life|dying|guarded|grave|reversib|deteriorat|outcome/
  const readinessItems = [
    { label: 'Prognosis discussed in transcript', ok: PROGNOSIS_RX.test(transcriptText) },
    { label: 'Code status decision recorded', ok: codeDiscussed },
    { label: 'Family questions captured', ok: familyQuestions.length > 0 || /\?/.test(transcriptText) },
    { label: 'Decision-maker (surrogate) identified', ok: !!surName.trim() },
    { label: 'Transcript ≥ 200 words', ok: wordCount >= 200 },
    { label: 'Clinical annotations added', ok: annotations.length > 0 },
  ]
  const gaps = readinessItems.filter((i) => !i.ok)

  const Section = ({ title, step, children }: { title: string; step: number; children: React.ReactNode }) => (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-slate-700 p-5 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">{title}</h3>
        <button
          onClick={() => onStepClick(step)}
          className="text-xs text-clinical hover:text-clinical-dark flex items-center gap-1 font-medium"
        >
          <Pencil className="w-3 h-3" /> Edit
        </button>
      </div>
      {children}
    </div>
  )

  return (
    <div className="max-w-lg mx-auto space-y-4">
      <p className="text-center text-sm text-muted dark:text-slate-400 mb-6">
        Review your inputs before generating documentation.
      </p>

      <Section title="Patient & People" step={1}>
        <div className="space-y-2 text-sm">
          <p><span className="text-muted">Patient:</span> <span className="font-medium">{patientAlias}</span></p>
          <p className="flex items-center gap-2">
            <span className="text-muted">Family:</span>
            {familyPresent ? (
              <span className="inline-flex items-center gap-1 text-clinical font-medium">
                <Heart className="w-3.5 h-3.5" /> Present
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-navy font-medium">
                <HeartOff className="w-3.5 h-3.5" /> Not present
              </span>
            )}
          </p>
          <p className="flex items-center gap-2">
            <span className="text-muted">Language:</span>
            <span className="inline-flex items-center gap-1 font-medium">
              <Globe className="w-3.5 h-3.5 text-clinical" /> {LANGUAGE_LABELS[language] || language}
            </span>
          </p>
          {surName && <p><span className="text-muted">Surrogate:</span> {surName} ({surRelation})</p>}
          {organSupports.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {organSupports.map((os, i) => (
                <span key={i} className="px-2 py-0.5 bg-gray-100 dark:bg-slate-700 rounded text-xs dark:text-slate-300">{os}</span>
              ))}
            </div>
          )}
        </div>
      </Section>

      <Section title="Conversation" step={2}>
        <p className="text-sm text-muted dark:text-slate-400">{segments.length} segment{segments.length !== 1 ? 's' : ''} &middot; {wordCount} words</p>
        {segments.length > 0 && (
          <p className="text-xs text-gray-400 mt-1 line-clamp-2">{segments[0]}</p>
        )}
      </Section>

      <Section title="Clinician Notes" step={3}>
        <div className="space-y-2 text-sm">
          <p><span className="text-muted">Tone:</span> <span className="font-medium capitalize">{tone}</span></p>
          <p><span className="text-muted">Code status discussed:</span> {codeDiscussed ? 'Yes' : 'No'}</p>
          {annotations.length > 0 && <p><span className="text-muted">Annotations:</span> {annotations.length}</p>}
          {familyQuestions.length > 0 && <p><span className="text-muted">Family questions:</span> {familyQuestions.length}</p>}
        </div>
      </Section>

      <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-100 dark:border-slate-700 p-5 transition-colors">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">Documentation Readiness</h3>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              gaps.length === 0
                ? 'bg-green-50 text-success dark:bg-green-950/40 dark:text-green-300'
                : gaps.length <= 2
                ? 'bg-amber-50 text-warning dark:bg-amber-950/40 dark:text-amber-300'
                : 'bg-red-50 text-danger dark:bg-red-950/40 dark:text-red-300'
            }`}
          >
            {readinessItems.length - gaps.length}/{readinessItems.length} complete
          </span>
        </div>
        <ul className="space-y-1.5">
          {readinessItems.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              {item.ok ? (
                <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-4 h-4 text-gray-300 dark:text-slate-600 flex-shrink-0 mt-0.5" />
              )}
              <span className={item.ok ? 'text-body dark:text-slate-200' : 'text-muted dark:text-slate-400'}>
                {item.label}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {gaps.length > 0 && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900">
          <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-amber-900 dark:text-amber-200">
              {gaps.length} gap{gaps.length !== 1 ? 's' : ''} detected — these will likely appear as risk flags.
            </p>
            <p className="text-xs text-amber-800 dark:text-amber-300 mt-1">
              You can generate anyway, or go back and add the missing details for a stronger note.
            </p>
          </div>
        </div>
      )}

      <button
        onClick={onGenerate}
        disabled={generating}
        className="w-full mt-2 px-8 py-4 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg text-base"
      >
        {generating ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
            Generating...
          </>
        ) : (
          <>
            Generate Communication
            <ChevronRight className="w-5 h-5" />
          </>
        )}
      </button>
    </div>
  )
}
