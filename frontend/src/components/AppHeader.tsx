import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Stethoscope, LogOut } from 'lucide-react'

export default function AppHeader() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
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
  )
}
