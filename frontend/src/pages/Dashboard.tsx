import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import AppHeader from '../components/AppHeader'
import {
  Plus,
  FileText,
  AlertTriangle,
  Clock,
  CheckCircle,
  Heart,
  HeartOff,
} from 'lucide-react'

interface ConversationSummary {
  id: string
  patient_alias: string
  status: string
  tone_setting: string
  created_at: string
  finalized_at: string | null
  organ_supports: string[] | null
  code_status_discussed: boolean
  family_present: boolean
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/conversations')
      .then((res) => setConversations(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Title + New Button */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-body">Conversations</h2>
            <p className="text-sm text-muted mt-1">
              Manage your ICU serious illness communications
            </p>
          </div>
          <button
            onClick={() => navigate('/new-conversation')}
            className="px-5 py-2.5 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors flex items-center gap-2 shadow-sm"
          >
            <Plus className="w-5 h-5" />
            New Conversation
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy" />
          </div>
        ) : conversations.length === 0 ? (
          /* Empty State */
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-clinical/10 mb-4">
              <FileText className="w-8 h-8 text-clinical" />
            </div>
            <h3 className="text-lg font-semibold text-body mb-2">
              No conversations yet
            </h3>
            <p className="text-muted text-sm mb-6 max-w-md mx-auto">
              Start your first structured communication to generate physician
              notes, family summaries, and risk flags.
            </p>
            <button
              onClick={() => navigate('/new-conversation')}
              className="px-6 py-3 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors inline-flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Start First Conversation
            </button>
          </div>
        ) : (
          /* Conversation Cards */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => navigate(`/conversations/${conv.id}/review`)}
                className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md hover:border-gray-200 transition-all text-left"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-body">
                    {conv.patient_alias}
                  </h3>
                  <span
                    className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      conv.status === 'FINALIZED'
                        ? 'bg-green-50 text-success'
                        : 'bg-amber-50 text-warning'
                    }`}
                  >
                    {conv.status === 'FINALIZED' ? (
                      <span className="flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Finalized
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Draft
                      </span>
                    )}
                  </span>
                </div>
                <div className="text-xs text-muted space-y-1">
                  <p>
                    Tone: {conv.tone_setting} &middot;{' '}
                    {new Date(conv.created_at).toLocaleDateString()}
                  </p>
                  {conv.organ_supports && conv.organ_supports.length > 0 && (
                    <p className="flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3 text-warning" />
                      {conv.organ_supports.length} organ support
                      {conv.organ_supports.length > 1 ? 's' : ''}
                    </p>
                  )}
                  <p className="flex items-center gap-1">
                    {conv.family_present ? (
                      <>
                        <Heart className="w-3 h-3 text-clinical" />
                        Family present
                      </>
                    ) : (
                      <>
                        <HeartOff className="w-3 h-3 text-gray-400" />
                        Family not present
                      </>
                    )}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
