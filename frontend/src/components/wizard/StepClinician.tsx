import { useState, useMemo, useEffect } from 'react'
import { MessageSquare, Plus, X, Sparkles } from 'lucide-react'

const TONE_OPTIONS = [
  { value: 'optimistic', label: 'Hopeful', emoji: '🌤️', desc: 'Emphasize improvements and positive steps' },
  { value: 'neutral', label: 'Neutral', emoji: '📋', desc: 'Present information factually' },
  { value: 'concerned', label: 'Concerned', emoji: '⚠️', desc: 'Acknowledge the serious nature honestly' },
]

/* Each suggestion has keywords that are scanned against the transcript.
   If ANY keyword matches, the chip is marked as "detected in transcript". */
const ANNOTATION_SUGGESTIONS: { label: string; keywords: string[] }[] = [
  { label: 'Discussed code status', keywords: ['code status', 'dnr', 'dni', 'full code', 'resuscitation'] },
  { label: 'Goals of care reviewed', keywords: ['goals of care', 'goals-of-care', 'care goals'] },
  { label: 'Palliative care consulted', keywords: ['palliative', 'comfort care', 'hospice'] },
  { label: 'Prognosis discussed honestly', keywords: ['prognosis', 'outlook', 'trajectory', 'likely outcome'] },
  { label: 'Family expressed understanding', keywords: ['family understand', 'family expressed', 'they understand', 'expressed understanding'] },
  { label: 'Surrogate decision-maker identified', keywords: ['surrogate', 'healthcare proxy', 'power of attorney', 'decision maker', 'decision-maker'] },
  { label: 'Emotional support provided', keywords: ['emotional support', 'counseling', 'chaplain', 'social work'] },
  { label: 'Patient wishes clarified', keywords: ['patient wish', 'advance directive', 'living will', 'what he wanted', 'what she wanted', 'prior wishes'] },
  { label: 'Escalation of care discussed', keywords: ['escalation', 'escalate', 'intubation', 'vasopressor', 'dialysis', 'rrt'] },
  { label: 'Comfort measures discussed', keywords: ['comfort measures', 'comfort care', 'symptom management', 'pain management'] },
]

const QUESTION_SUGGESTIONS: { label: string; keywords: string[] }[] = [
  { label: 'Is my loved one in pain?', keywords: ['pain', 'suffering', 'comfortable', 'sedation'] },
  { label: 'What is the prognosis?', keywords: ['prognosis', 'chances', 'outlook', 'what to expect'] },
  { label: 'What are the treatment options?', keywords: ['treatment option', 'options', 'what can we do', 'alternatives'] },
  { label: 'When can we visit?', keywords: ['visit', 'visiting hours', 'can we see'] },
  { label: 'What does code status mean?', keywords: ['code status', 'what does dnr', 'what is full code'] },
  { label: 'Will they recover?', keywords: ['recover', 'get better', 'pull through', 'survive'] },
  { label: 'How long will they be in the ICU?', keywords: ['how long', 'length of stay', 'when can they leave'] },
  { label: 'What happens if we choose comfort care?', keywords: ['comfort care', 'what happens if', 'withdraw'] },
  { label: 'Can they hear us?', keywords: ['can they hear', 'aware', 'conscious', 'know we are here'] },
  { label: 'Who makes decisions if they can\'t?', keywords: ['who decides', 'surrogate', 'proxy', 'decision maker'] },
]

/** Check if transcript text contains any of the keywords */
function matchesTranscript(keywords: string[], transcriptLower: string): boolean {
  return keywords.some((kw) => transcriptLower.includes(kw.toLowerCase()))
}

interface Props {
  tone: string
  setTone: (v: string) => void
  codeDiscussed: boolean
  setCodeDiscussed: (v: boolean) => void
  annotations: string[]
  setAnnotations: (v: string[]) => void
  familyQuestions: string[]
  setFamilyQuestions: (v: string[]) => void
  /** Transcript segments from Step 2, used for smart detection */
  transcriptSegments?: string[]
}

export default function StepClinician({
  tone, setTone,
  codeDiscussed, setCodeDiscussed,
  annotations, setAnnotations,
  familyQuestions, setFamilyQuestions,
  transcriptSegments = [],
}: Props) {
  const [annotationInput, setAnnotationInput] = useState('')
  const [questionInput, setQuestionInput] = useState('')

  // Lowercase transcript for keyword matching
  const transcriptLower = useMemo(
    () => transcriptSegments.join(' ').toLowerCase(),
    [transcriptSegments],
  )

  // Which annotation suggestions are already mentioned in the transcript?
  const detectedAnnotations = useMemo(
    () => new Set(
      ANNOTATION_SUGGESTIONS
        .filter((s) => matchesTranscript(s.keywords, transcriptLower))
        .map((s) => s.label)
    ),
    [transcriptLower],
  )

  // Which question suggestions are already mentioned in the transcript?
  const detectedQuestions = useMemo(
    () => new Set(
      QUESTION_SUGGESTIONS
        .filter((s) => matchesTranscript(s.keywords, transcriptLower))
        .map((s) => s.label)
    ),
    [transcriptLower],
  )

  // Auto-check code status if transcript mentions it (once, on mount)
  useEffect(() => {
    if (!codeDiscussed && transcriptLower && matchesTranscript(['code status', 'dnr', 'dni', 'full code', 'resuscitation'], transcriptLower)) {
      setCodeDiscussed(true)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-3">
          Communication Tone
        </label>
        <div className="space-y-2">
          {TONE_OPTIONS.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => setTone(t.value)}
              className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all text-left ${
                tone === t.value
                  ? 'border-navy bg-navy/5 shadow-sm'
                  : 'border-gray-200 hover:border-gray-300 dark:border-slate-600 dark:hover:border-slate-500'
              }`}
            >
              <span className="text-2xl">{t.emoji}</span>
              <div>
                <p className={`text-sm font-semibold ${tone === t.value ? 'text-navy' : 'text-gray-700'}`}>
                  {t.label}
                </p>
                <p className="text-xs text-gray-400 dark:text-slate-500">{t.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      <label className="flex items-center gap-3 p-4 rounded-xl border border-gray-200 dark:border-slate-600 cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors">
        <input
          type="checkbox"
          checked={codeDiscussed}
          onChange={(e) => setCodeDiscussed(e.target.checked)}
          className="w-5 h-5 rounded border-gray-300 text-navy focus:ring-navy"
        />
        <span className="text-sm font-medium text-gray-700 dark:text-slate-300">Code status was discussed</span>
      </label>

      <div>
        <h3 className="text-sm font-medium text-gray-700 dark:text-slate-300 mb-2 flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-clinical" />
          Clinician Annotations
        </h3>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={annotationInput}
            onChange={(e) => setAnnotationInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && annotationInput.trim()) {
                e.preventDefault()
                setAnnotations([...annotations, annotationInput.trim()])
                setAnnotationInput('')
              }
            }}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 text-sm focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
            placeholder="Add observation or tap a suggestion below..."
          />
          <button
            type="button"
            onClick={() => { if (annotationInput.trim()) { setAnnotations([...annotations, annotationInput.trim()]); setAnnotationInput('') } }}
            className="px-4 py-3 bg-gray-100 dark:bg-slate-700 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        {/* Suggestion chips */}
        <p className="text-[11px] text-gray-400 dark:text-slate-500 mb-1.5">
          <Sparkles className="w-3 h-3 inline -mt-0.5 mr-0.5" />
          Highlighted items were detected in your transcript
        </p>
        <div className="flex flex-wrap gap-1.5 mb-3">
          {ANNOTATION_SUGGESTIONS.filter((s) => !annotations.includes(s.label)).map((s) => {
            const detected = detectedAnnotations.has(s.label)
            return (
              <button
                key={s.label}
                type="button"
                onClick={() => setAnnotations([...annotations, s.label])}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                  detected
                    ? 'border-clinical bg-clinical/15 text-clinical dark:bg-clinical/25 dark:text-clinical'
                    : 'border-dashed border-clinical/40 text-clinical hover:bg-clinical/10 dark:border-clinical/30 dark:text-clinical dark:hover:bg-clinical/20'
                }`}
              >
                + {s.label}
              </button>
            )
          })}
        </div>
        <div className="flex flex-wrap gap-2">
          {annotations.map((a, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-slate-700 rounded-lg text-xs font-medium dark:text-slate-200">
              {a}
              <button onClick={() => setAnnotations(annotations.filter((_, j) => j !== i))}>
                <X className="w-3 h-3 text-gray-400 hover:text-gray-600" />
              </button>
            </span>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Family Questions</h3>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={questionInput}
            onChange={(e) => setQuestionInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && questionInput.trim()) {
                e.preventDefault()
                setFamilyQuestions([...familyQuestions, questionInput.trim()])
                setQuestionInput('')
              }
            }}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 text-sm focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
            placeholder="What did the family ask? Tap a suggestion below..."
          />
          <button
            type="button"
            onClick={() => { if (questionInput.trim()) { setFamilyQuestions([...familyQuestions, questionInput.trim()]); setQuestionInput('') } }}
            className="px-4 py-3 bg-gray-100 dark:bg-slate-700 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        {/* Suggestion chips */}
        <p className="text-[11px] text-gray-400 dark:text-slate-500 mb-1.5">
          <Sparkles className="w-3 h-3 inline -mt-0.5 mr-0.5" />
          Highlighted items were detected in your transcript
        </p>
        <div className="flex flex-wrap gap-1.5 mb-3">
          {QUESTION_SUGGESTIONS.filter((s) => !familyQuestions.includes(s.label)).map((s) => {
            const detected = detectedQuestions.has(s.label)
            return (
              <button
                key={s.label}
                type="button"
                onClick={() => setFamilyQuestions([...familyQuestions, s.label])}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                  detected
                    ? 'border-navy bg-navy/15 text-navy dark:bg-navy/30 dark:text-slate-200'
                    : 'border-dashed border-navy/40 text-navy hover:bg-navy/10 dark:border-slate-500 dark:text-slate-300 dark:hover:bg-slate-700'
                }`}
              >
                + {s.label}
              </button>
            )
          })}
        </div>
        <div className="flex flex-wrap gap-2">
          {familyQuestions.map((q, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-slate-700 rounded-lg text-xs font-medium dark:text-slate-200">
              {q}
              <button onClick={() => setFamilyQuestions(familyQuestions.filter((_, j) => j !== i))}>
                <X className="w-3 h-3 text-gray-400 hover:text-gray-600" />
              </button>
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
