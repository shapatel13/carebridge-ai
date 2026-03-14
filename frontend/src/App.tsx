import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { useTheme } from './hooks/useTheme'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import NewConversation from './pages/NewConversation'
import ConversationReview from './pages/ConversationReview'
import ConversationSuccess from './pages/ConversationSuccess'
import ShiftHandoff from './pages/ShiftHandoff'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy" />
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function App() {
  const { fetchUser } = useAuth()
  const { isDark } = useTheme()

  useEffect(() => {
    fetchUser()
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
  }, [isDark])

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/new-conversation"
        element={
          <ProtectedRoute>
            <NewConversation />
          </ProtectedRoute>
        }
      />
      <Route
        path="/conversations/:id/review"
        element={
          <ProtectedRoute>
            <ConversationReview />
          </ProtectedRoute>
        }
      />
      <Route
        path="/conversations/:id/success"
        element={
          <ProtectedRoute>
            <ConversationSuccess />
          </ProtectedRoute>
        }
      />
      <Route
        path="/shift-handoff"
        element={
          <ProtectedRoute>
            <ShiftHandoff />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
