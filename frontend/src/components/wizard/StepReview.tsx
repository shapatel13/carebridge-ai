import { ChevronRight, Pencil, Heart, HeartOff } from 'lucide-react'

interface Props {
  patientAlias: string
  familyPresent: boolean
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
  patientAlias, familyPresent, surName, surRelation, organSupports,
  segments, tone, codeDiscussed, annotations, familyQuestions,
  onStepClick, onGenerate, generating,
}: Props) {
  const wordCount = segments.join(' ').split(/\s+/).filter(Boolean).length

  const Section = ({ title, step, children }: { title: string; step: number; children: React.ReactNode }) => (
    <div className="bg-white rounded-xl border border-gray-100 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
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
      <p className="text-center text-sm text-muted mb-6">
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
          {surName && <p><span className="text-muted">Surrogate:</span> {surName} ({surRelation})</p>}
          {organSupports.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {organSupports.map((os, i) => (
                <span key={i} className="px-2 py-0.5 bg-gray-100 rounded text-xs">{os}</span>
              ))}
            </div>
          )}
        </div>
      </Section>

      <Section title="Conversation" step={2}>
        <p className="text-sm text-muted">{segments.length} segment{segments.length !== 1 ? 's' : ''} &middot; {wordCount} words</p>
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

      <button
        onClick={onGenerate}
        disabled={generating}
        className="w-full mt-6 px-8 py-4 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg text-base"
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
