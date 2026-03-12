import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Plus } from 'lucide-react'

interface Props {
  segments: string[]
  setSegments: (v: string[]) => void
}

export default function StepConversation({ segments, setSegments }: Props) {
  const [transcript, setTranscript] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const recognition = useRef<any>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [segments])

  const startRecording = () => {
    try {
      const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      if (!SR) return
      recognition.current = new SR()
      recognition.current.continuous = true
      recognition.current.interimResults = true
      recognition.current.lang = 'en-US'
      recognition.current.onresult = (event: any) => {
        let interim = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            setSegments([...segments, t.trim()])
          } else {
            interim = t
          }
        }
        setTranscript(interim)
      }
      recognition.current.onerror = (e: any) => {
        if (e.error !== 'no-speech') setIsRecording(false)
      }
      recognition.current.onend = () => {
        if (recognition.current) {
          try { recognition.current.start() } catch {}
        }
      }
      recognition.current.start()
      setIsRecording(true)
    } catch {}
  }

  const stopRecording = () => {
    setIsRecording(false)
    if (recognition.current) { recognition.current.stop(); recognition.current = null }
    if (transcript.trim()) { setSegments([...segments, transcript.trim()]); setTranscript('') }
  }

  const addManualText = () => {
    if (transcript.trim()) { setSegments([...segments, transcript.trim()]); setTranscript('') }
  }

  const wordCount = [...segments, transcript].join(' ').split(/\s+/).filter(Boolean).length

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex flex-col items-center mb-6">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`w-24 h-24 rounded-full flex items-center justify-center transition-all shadow-lg ${
            isRecording ? 'bg-danger hover:bg-red-600' : 'bg-navy hover:bg-navy-dark'
          }`}
        >
          {isRecording ? <Square className="w-10 h-10 text-white" /> : <Mic className="w-10 h-10 text-white" />}
        </button>
        {isRecording && (
          <div className="flex items-center gap-1 mt-3">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="w-1 h-6 bg-danger rounded-full waveform-bar"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        )}
        <p className="text-xs text-muted mt-3">
          {isRecording ? 'Recording... click to stop' : 'Click to record, or type below'}
        </p>
      </div>

      <div
        ref={scrollRef}
        className="bg-gray-50 rounded-2xl p-6 min-h-[250px] max-h-[400px] overflow-y-auto space-y-2 border border-gray-100"
      >
        {segments.length === 0 && !transcript && (
          <p className="text-muted text-sm italic text-center py-8">
            Your conversation transcript will appear here...
          </p>
        )}
        {segments.map((seg, i) => (
          <p key={i} className="text-sm text-body leading-relaxed">{seg}</p>
        ))}
        {transcript && <p className="text-sm text-muted italic">{transcript}</p>}
      </div>

      <div className="flex justify-end mt-2">
        <span className="text-xs text-muted bg-gray-100 px-2 py-1 rounded-full">
          {wordCount} word{wordCount !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="mt-4 flex gap-2">
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); addManualText() }
          }}
          placeholder="Type conversation text here..."
          className="flex-1 px-4 py-3 rounded-xl border border-gray-200 text-sm resize-none focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none"
          rows={3}
          disabled={isRecording}
        />
        <button
          onClick={addManualText}
          disabled={!transcript.trim() || isRecording}
          className="px-4 py-3 bg-clinical text-white rounded-xl text-sm font-medium hover:bg-clinical-dark disabled:opacity-40 transition-colors self-end"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
