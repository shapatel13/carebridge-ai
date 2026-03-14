import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useTheme } from '../hooks/useTheme'
import { Stethoscope, LogOut, Sun, Moon } from 'lucide-react'

export default function AppHeader() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { isDark, toggle } = useTheme()

  return (
    <header className="bg-white dark:bg-slate-800 border-b border-gray-200 dark:border-slate-700 sticky top-0 z-10 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
        <div
          className="flex items-center gap-3 cursor-pointer"
          onClick={() => navigate('/dashboard')}
        >
          <Stethoscope className="w-6 h-6 text-navy dark:text-clinical" />
          <h1 className="font-bold text-navy dark:text-clinical text-lg">CareBridge AI</h1>
          {user?.is_demo && (
            <span className="text-xs bg-clinical/10 text-clinical px-2 py-0.5 rounded-full font-medium">
              DEMO
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted dark:text-slate-400 hidden sm:block">{user?.full_name}</span>
          <button
            onClick={toggle}
            className="text-muted hover:text-navy dark:hover:text-clinical transition-colors"
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
          <button
            onClick={() => {
              logout()
              navigate('/login')
            }}
            className="text-muted hover:text-navy dark:hover:text-clinical transition-colors"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  )
}
