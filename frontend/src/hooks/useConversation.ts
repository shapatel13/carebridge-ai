import { create } from 'zustand'
import api from '../lib/api'

interface Segment {
  id: string
  text: string
  confidence: number
  segment_order: number
}

interface GeneratedOutput {
  id: string
  conversation_id: string
  physician_note: Record<string, string>
  family_summary: string
  risk_flags: Array<{
    type: string
    severity: string
    message: string
    suggestion: string
  }>
  created_at: string
}

interface Conversation {
  id: string
  patient_alias: string
  physician_id: string
  hospital_id: string
  status: string
  tone_setting: string
  risk_calibration: number
  participants: string[] | null
  organ_supports: string[] | null
  code_status_discussed: boolean
  family_present: boolean
  language: string
  code_status_change: string | null
  surrogate_name: string | null
  surrogate_relationship: string | null
  family_questions: string[] | null
  clinician_annotations: string[] | null
  created_at: string
  finalized_at: string | null
}

interface ConversationState {
  conversation: Conversation | null
  segments: Segment[]
  output: GeneratedOutput | null
  loading: boolean
  generating: boolean

  createConversation: (data: Partial<Conversation>) => Promise<string>
  loadConversation: (id: string) => Promise<void>
  updateConversation: (id: string, data: Partial<Conversation>) => Promise<void>
  addSegment: (conversationId: string, text: string) => Promise<void>
  generateOutput: (conversationId: string) => Promise<void>
  finalizeConversation: (conversationId: string) => Promise<void>
  reset: () => void
}

export const useConversation = create<ConversationState>((set, get) => ({
  conversation: null,
  segments: [],
  output: null,
  loading: false,
  generating: false,

  createConversation: async (data) => {
    const res = await api.post('/conversations', data)
    set({ conversation: res.data, segments: [], output: null })
    return res.data.id
  },

  loadConversation: async (id) => {
    set({ loading: true })
    const res = await api.get(`/conversations/${id}`)
    set({
      conversation: res.data.conversation,
      segments: res.data.segments,
      output: res.data.output,
      loading: false,
    })
  },

  updateConversation: async (id, data) => {
    const res = await api.patch(`/conversations/${id}`, data)
    set({ conversation: res.data })
  },

  addSegment: async (conversationId, text) => {
    const res = await api.post(`/conversations/${conversationId}/segments`, { text })
    set((state) => ({ segments: [...state.segments, res.data] }))
  },

  generateOutput: async (conversationId) => {
    set({ generating: true })
    try {
      const res = await api.post(`/conversations/${conversationId}/generate`)
      set({ output: res.data, generating: false })
    } catch (e) {
      set({ generating: false })
      throw e
    }
  },

  finalizeConversation: async (conversationId) => {
    const res = await api.post(`/conversations/${conversationId}/finalize`)
    set({ conversation: res.data })
  },

  reset: () => {
    set({ conversation: null, segments: [], output: null, loading: false, generating: false })
  },
}))
