import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useConversation } from '../hooks/useConversation'
import {
  Mic,
  MicOff,
  Square,
  Plus,
  X,
  ChevronRight,
  LogOut,
  Stethoscope,
  Users,
  MessageSquare,
  AlertTriangle,
} from 'lucide-react'

const TONE_OPTIONS = [
  { value: 'optimistic', label: 'Hopeful', emoji: '🌤️' },
  { value: 'neutral', label: 'Neutral', emoji: '📋' },
  { value: 'concerned', label: 'Concerned', emoji: '⚠️' },
]

const PROMPT_CHIPS = [
  { key: 'organ', label: 'Organ support discussed?', keywords: ['ventilator', 'vasopressor', 'CRRT', 'BiPAP'] },
  { key: 'trajectory', label: 'Trajectory communicated?', keywords: ['prognosis', 'trajectory', 'decline'] },
  { key: 'code', label: 'Code status addressed?', keywords: ['code status', 'DNR', 'DNI', 'resuscitate'] },
  { key: 'surrogate', label: 'Surrogate confirmed?', keywords: [] },
]

export default function NewConversation() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { createConversation, addSegment, generateOutput, segments, generating, reset } =
    useConversation()

  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [localSegments, setLocalSegments] = useState<string[]>([])
  const [tone, setTone] = useState('neutral')
  const [patientAlias, setPatientAlias] = useState('Patient A')
  const [surName, setSurName] = useState('')
  const [surRelation, setSurRelation] = useState('')
  const [codeDiscussed, setCodeDiscussed] = useState(false)
  const [organSupports, setOrganSupports] = useState<string[]>([])
  const [organInput, setOrganInput] = useState('')
  const [annotations, setAnnotations] = useState<string[]>([])
  const [annotationInput, setAnnotationInput] = useState('')
  const [familyQuestions, setFamilyQuestions] = useState<string[]>([])
  const [questionInput, setQuestionInput] = useState('')
  const [dismissedChips, setDismissedChips] = useState<string[]>([])
  const [error, setError] = useState('')

  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const recognition = useRef<any>(null)
  const transcriptRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    reset()
  }, [])

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight
    }
  }, [localSegments])

  const startRecording = async () => {
    try {
      // Use Web Speech API for live transcription
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      if (SpeechRecognition) {
        recognition.current = new SpeechRecognition()
        recognition.current.continuous = true
        recognition.current.interimResults = true
        recognition.current.lang = 'en-US'

        recognition.current.onresult = (event: any) => {
          let interim = ''
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const t = event.results[i][0].transcript
            if (event.results[i].isFinal) {
              setLocalSegments((prev) => [...prev, t.trim()])
            } else {
              interim = t
            }
          }
          setTranscript(interim)
        }

        recognition.current.onerror = (e: any) => {
          console.error('Speech recognition error:', e.error)
          if (e.error !== 'no-speech') {
            setIsRecording(false)
          }
        }

        recognition.current.onend = () => {
          // Restart if still recording
          if (isRecording && recognition.current) {
            try {
              recognition.current.start()
            } catch {}
          }
        }

        recognition.current.start()
      }

      setIsRecording(true)
    } catch (err) {
      setError('Could not access microphone. You can type text manually below.')
    }
  }

  const stopRecording = () => {
    setIsRecording(false)
    if (recognition.current) {
      recognition.current.stop()
      recognition.current = null
    }
    if (transcript.trim()) {
      setLocalSegments((prev) => [...prev, transcript.trim()])
      setTranscript('')
    }
  }

  const addManualText = () => {
    if (transcript.trim()) {
      setLocalSegments((prev) => [...prev, transcript.trim()])
      setTranscript('')
    }
  }

  const handleGenerate = async () => {
    if (localSegments.length === 0 && !transcript.trim()) {
      setError('Please add conversation text before generating.')
      return
    }
    setError('')

    try {
      // Create conversation
      const id = await createConversation({
        patient_alias: patientAlias,
        tone_setting: tone,
        organ_supports: organSupports.length > 0 ? organSupports : null,
        code_status_discussed: codeDiscussed,
        surrogate_name: surName || null,
        surrogate_relationship: surRelation || null,
        family_questions: familyQuestions.length > 0 ? familyQuestions : null,
        clinician_annotations: annotations.length > 0 ? annotations : null,
      } as any)

      // Add all segments
      const allSegments = [...localSegments]
      if (transcript.trim()) allSegments.push(transcript.trim())

      for (const text of allSegments) {
        await addSegment(id, text)
      }

      // Generate
      await generateOutput(id)

      navigate(`/conversations/${id}/review`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to generate. Please try again.')
    }
  }

  // Detect prompt chip triggers
  const allText = [...localSegments, transcript].join(' ').toLowerCase()
  const activeChips = PROMPT_CHIPS.filter((chip) => {
    if (dismissedChips.includes(chip.key)) return false
    if (chip.keywords.length === 0) return !surName // show surrogate if not yet filled
    return chip.keywords.some((kw) => allText.includes(kw.toLowerCase()))
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Stethoscope className="w-6 h-6 text-navy" />
            <h1 className="font-bold text-navy text-lg">CareBridge AI</h1>
            {user?.is_demo && (
              <span className="text-xs bg-clinical/10 text-clinical px-2 py-0.5 rounded-full font-medium">
                DEMO
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted hidden sm:block">{user?.full_name}</span>
            <button
              onClick={() => {
                logout()
                navigate('/login')
              }}
              className="text-muted hover:text-navy transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left Column - Voice & Transcript */}
          <div className="lg:col-span-3 space-y-4">
            {/* Patient Alias */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <label className="block text-sm font-medium text-gray-600 mb-1">
                Patient Identifier (de-identified)
              </label>
              <input
                type="text"
                value={patientAlias}
                onChange={(e) => setPatientAlias(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-clinical focus:ring-1 focus:ring-clinical/20 outline-none"
                placeholder="e.g. Patient A"
              />
            </div>

            {/* Voice Recorder */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-body flex items-center gap-2">
                  <Mic className="w-5 h-5 text-clinical" />
                  Conversation Capture
                </h2>
                {/* Tone Selector */}
                <div className="flex gap-1">
                  {TONE_OPTIONS.map((t) => (
                    <button
                      key={t.value}
                      onClick={() => setTone(t.value)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        tone === t.value
                          ? 'bg-navy text-white shadow-sm'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {t.emoji} {t.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Mic Button */}
              <div className="flex justify-center mb-4">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-lg ${
                    isRecording
                      ? 'bg-danger hover:bg-red-600 animate-pulse'
                      : 'bg-navy hover:bg-navy-dark'
                  }`}
                >
                  {isRecording ? (
                    <Square className="w-8 h-8 text-white" />
                  ) : (
                    <Mic className="w-8 h-8 text-white" />
                  )}
                </button>
              </div>
              <p className="text-center text-xs text-muted mb-4">
                {isRecording
                  ? 'Recording... Click to stop'
                  : 'Click to start voice recording, or type below'}
              </p>

              {/* Transcript Display */}
              <div
                ref={transcriptRef}
                className="bg-gray-50 rounded-lg p-4 min-h-[200px] max-h-[300px] overflow-y-auto scrollbar-thin space-y-2"
              >
                {localSegments.length === 0 && !transcript && (
                  <p className="text-muted text-sm italic">
                    Transcript will appear here as you speak or type...
                  </p>
                )}
                {localSegments.map((seg, i) => (
                  <p key={i} className="text-sm text-body leading-relaxed">
                    {seg}
                  </p>
                ))}
                {transcript && (
                  <p className="text-sm text-muted italic">{transcript}</p>
                )}
              </div>

              {/* Manual text input */}
              <div className="mt-3 flex gap-2">
                <textarea
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      addManualText()
                    }
                  }}
                  placeholder="Type conversation text here (or use voice above)..."
                  className="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm resize-none focus:border-clinical focus:ring-1 focus:ring-clinical/20 outline-none"
                  rows={2}
                  disabled={isRecording}
                />
                <button
                  onClick={addManualText}
                  disabled={!transcript.trim() || isRecording}
                  className="px-4 py-2 bg-clinical text-white rounded-lg text-sm font-medium hover:bg-clinical-dark disabled:opacity-40 transition-colors self-end"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              {/* Prompt Chips */}
              {activeChips.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {activeChips.map((chip) => (
                    <div
                      key={chip.key}
                      className="flex items-center gap-1 px-3 py-1.5 bg-warning/10 border border-warning/30 rounded-full text-xs font-medium text-yellow-800"
                    >
                      <AlertTriangle className="w-3 h-3" />
                      {chip.label}
                      <button
                        onClick={() =>
                          setDismissedChips((prev) => [...prev, chip.key])
                        }
                        className="ml-1 hover:text-yellow-900"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Metadata */}
          <div className="lg:col-span-2 space-y-4">
            {/* Surrogate */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-sm text-body mb-3 flex items-center gap-2">
                <Users className="w-4 h-4 text-clinical" />
                Surrogate Decision Maker
              </h3>
              <input
                type="text"
                value={surName}
                onChange={(e) => setSurName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm mb-2 focus:border-clinical focus:ring-1 focus:ring-clinical/20 outline-none"
                placeholder="Name"
              />
              <input
                type="text"
                value={surRelation}
                onChange={(e) => setSurRelation(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-clinical focus:ring-1 focus:ring-clinical/20 outline-none"
                placeholder="Relationship (e.g., Daughter, healthcare proxy)"
              />
            </div>

            {/* Code Status */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={codeDiscussed}
                  onChange={(e) => setCodeDiscussed(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-navy focus:ring-navy"
                />
                <span className="text-sm font-medium text-body">
                  Code status discussed
                </span>
              </label>
            </div>

            {/* Organ Supports */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-sm text-body mb-2">Organ Supports</h3>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={organInput}
                  onChange={(e) => setOrganInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && organInput.trim()) {
                      setOrganSupports((prev) => [...prev, organInput.trim()])
                      setOrganInput('')
                    }
                  }}
                  className="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-clinical focus:ring-1 focus:ring-clinical/20 outline-none"
                  placeholder="e.g. Mechanical ventilation"
                />
                <button
                  onClick={() => {
                    if (organInput.trim()) {
                      setOrganSupports((prev) => [...prev, organInput.trim()])
                      setOrganInput('')
                    }
                  }}
                  className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="flex flex-wrap gap-1">
                {organSupports.map((os, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs"
                  >
                    {os}
                    <button
                      onClick={() =>
                        setOrganSupports((prev) => prev.filter((_, j) => j !== i))
                      }
                    >
                      <X className="w-3 h-3 text-gray-400 hover:text-gray-600" />
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Clinician Annotations */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-sm text-body mb-2 flex items-center gap-2">
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
                      setAnnotations((prev) => [...prev, annotationInput.trim()])
                      setAnnotationInput('')
                    }
                  }}
                  className="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-clinical focus:ring-1 focus:ring-clinical/20 outline-none"
                  placeholder="Add observation..."
                />
                <button
                  onClick={() => {
                    if (annotationInput.trim()) {
                      setAnnotations((prev) => [...prev, annotationInput.trim()])
                      setAnnotationInput('')
                    }
                  }}
                  className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-1">
                {annotations.map((a, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between px-2 py-1 bg-gray-50 rounded text-xs"
                  >
                    <span>{a}</span>
                    <button
                      onClick={() =>
                        setAnnotations((prev) => prev.filter((_, j) => j !== i))
                      }
                    >
                      <X className="w-3 h-3 text-gray-400 hover:text-gray-600" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Family Questions */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-sm text-body mb-2">Family Questions</h3>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={questionInput}
                  onChange={(e) => setQuestionInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && questionInput.trim()) {
                      setFamilyQuestions((prev) => [...prev, questionInput.trim()])
                      setQuestionInput('')
                    }
                  }}
                  className="flex-1 px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-clinical focus:ring-1 focus:ring-clinical/20 outline-none"
                  placeholder="What did the family ask?"
                />
                <button
                  onClick={() => {
                    if (questionInput.trim()) {
                      setFamilyQuestions((prev) => [...prev, questionInput.trim()])
                      setQuestionInput('')
                    }
                  }}
                  className="px-3 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-1">
                {familyQuestions.map((q, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between px-2 py-1 bg-gray-50 rounded text-xs"
                  >
                    <span>{q}</span>
                    <button
                      onClick={() =>
                        setFamilyQuestions((prev) => prev.filter((_, j) => j !== i))
                      }
                    >
                      <X className="w-3 h-3 text-gray-400 hover:text-gray-600" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 text-sm text-danger bg-red-50 rounded-lg px-4 py-3 max-w-7xl mx-auto">
            {error}
          </div>
        )}

        {/* Generate Button */}
        <div className="mt-6 flex justify-end max-w-7xl mx-auto">
          <button
            onClick={handleGenerate}
            disabled={generating || (localSegments.length === 0 && !transcript.trim())}
            className="px-8 py-3 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors disabled:opacity-50 flex items-center gap-2 shadow-lg"
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Generating...
              </>
            ) : (
              <>
                Generate Structured Communication
                <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  )
}
