import { create } from 'zustand'
import api from '../lib/api'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  hospital_id: string
  hospital_name: string | null
  is_demo: boolean
}

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  demoLogin: () => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  loading: true,

  login: async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password })
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    const userRes = await api.get('/auth/me')
    set({ user: userRes.data })
  },

  demoLogin: async () => {
    const res = await api.post('/auth/demo')
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    const userRes = await api.get('/auth/me')
    set({ user: userRes.data })
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null })
  },

  fetchUser: async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        set({ user: null, loading: false })
        return
      }
      const res = await api.get('/auth/me')
      set({ user: res.data, loading: false })
    } catch {
      set({ user: null, loading: false })
    }
  },
}))
