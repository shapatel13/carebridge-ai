import { useState } from 'react'
import { MessageSquare, Plus, X } from 'lucide-react'

const TONE_OPTIONS = [
  { value: 'optimistic', label: 'Hopeful', emoji: '🌤️', desc: 'Emphasize improvements and positive steps' },
  { value: 'neutral', label: 'Neutral', emoji: '📋', desc: 'Present information factually' },
  { value: 'concerned', label: 'Concerned', emoji: '⚠️', desc: 'Acknowledge the serious nature honestly' },
]

interface Props {
  tone: string
  setTone: (v: string) => void
  codeDiscussed: boolean
  setCodeDiscussed: (v: boolean) => void
  annotations: string[]
  setAnnotations: (v: string[]) => void
  familyQuestions: string[]
  setFamilyQuestions: (v: string[]) => void
}

export default function StepClinician({
  tone, setTone,
  codeDiscussed, setCodeDiscussed,
  annotations, setAnnotations,
  familyQuestions, setFamilyQuestions,
}: Props) {
  const [annotationInput, setAnnotationInput] = useState('')
  const [questionInput, setQuestionInput] = useState('')

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
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
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <span className="text-2xl">{t.emoji}</span>
              <div>
                <p className={`text-sm font-semibold ${tone === t.value ? 'text-navy' : 'text-gray-700'}`}>
                  {t.label}
                </p>
                <p className="text-xs text-gray-400">{t.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      <label className="flex items-center gap-3 p-4 rounded-xl border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors">
        <input
          type="checkbox"
          checked={codeDiscussed}
          onChange={(e) => setCodeDiscussed(e.target.checked)}
          className="w-5 h-5 rounded border-gray-300 text-navy focus:ring-navy"
        />
        <span className="text-sm font-medium text-gray-700">Code status was discussed</span>
      </label>

      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
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
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 text-sm focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
            placeholder="Add observation..."
          />
          <button
            type="button"
            onClick={() => { if (annotationInput.trim()) { setAnnotations([...annotations, annotationInput.trim()]); setAnnotationInput('') } }}
            className="px-4 py-3 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {annotations.map((a, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-lg text-xs font-medium">
              {a}
              <button onClick={() => setAnnotations(annotations.filter((_, j) => j !== i))}>
                <X className="w-3 h-3 text-gray-400 hover:text-gray-600" />
              </button>
            </span>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Family Questions</h3>
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
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 text-sm focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
            placeholder="What did the family ask?"
          />
          <button
            type="button"
            onClick={() => { if (questionInput.trim()) { setFamilyQuestions([...familyQuestions, questionInput.trim()]); setQuestionInput('') } }}
            className="px-4 py-3 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {familyQuestions.map((q, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-lg text-xs font-medium">
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
