import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useConversation } from '../hooks/useConversation'
import { useAuth } from '../hooks/useAuth'
import AppHeader from '../components/AppHeader'
import { generateFamilySummaryPdf } from '../lib/generatePdf'
import {
  CheckCircle,
  Plus,
  FileDown,
  Calendar,
  User,
  AlertTriangle,
} from 'lucide-react'

export default function ConversationSuccess() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { conversation, output, loading, loadConversation } = useConversation()

  useEffect(() => {
    if (id) loadConversation(id)
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy" />
      </div>
    )
  }

  const flagCount = output?.risk_flags?.length || 0

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors">
      <AppHeader />

      <main className="max-w-lg mx-auto px-4 py-16 text-center">
        {/* Success Check */}
        <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-success/10 mb-6">
          <CheckCircle className="w-14 h-14 text-success" />
        </div>

        <h2 className="text-2xl font-bold text-body dark:text-slate-100 mb-2">
          Conversation Logged
        </h2>
        <p className="text-muted dark:text-slate-400 mb-8">
          The conversation has been finalized and saved to the audit trail.
        </p>

        {/* Summary Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-700 p-6 text-left mb-8 transition-colors">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-muted dark:text-slate-400" />
              <div>
                <p className="text-xs text-muted dark:text-slate-400">Date</p>
                <p className="text-sm font-medium text-body dark:text-slate-100">
                  {conversation?.finalized_at
                    ? new Date(conversation.finalized_at).toLocaleString()
                    : new Date().toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <User className="w-5 h-5 text-muted dark:text-slate-400" />
              <div>
                <p className="text-xs text-muted dark:text-slate-400">Provider</p>
                <p className="text-sm font-medium text-body dark:text-slate-100">
                  {user?.full_name}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-muted dark:text-slate-400" />
              <div>
                <p className="text-xs text-muted dark:text-slate-400">Risk Flags Detected</p>
                <p className="text-sm font-medium text-body dark:text-slate-100">
                  {flagCount === 0 ? (
                    <span className="text-success">None</span>
                  ) : (
                    <span className="text-warning">{flagCount} flag{flagCount > 1 ? 's' : ''}</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={() => navigate('/new-conversation')}
            className="w-full px-6 py-3 bg-navy hover:bg-navy-dark text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Start New Conversation
          </button>
          <button
            onClick={() => {
              if (!output || !conversation) return
              generateFamilySummaryPdf({
                hospitalName: 'Metro General Hospital',
                physicianName: user?.full_name || 'Physician',
                patientAlias: conversation.patient_alias,
                familySummary: output.family_summary,
                date: conversation.finalized_at
                  ? new Date(conversation.finalized_at).toLocaleDateString()
                  : new Date().toLocaleDateString(),
                language: conversation.language,
              })
            }}
            className="w-full px-6 py-3 border border-clinical text-clinical font-medium rounded-xl transition-colors hover:bg-clinical/5 flex items-center justify-center gap-2"
          >
            <FileDown className="w-5 h-5" />
            Download Family Summary PDF
          </button>
        </div>
      </main>
    </div>
  )
}
