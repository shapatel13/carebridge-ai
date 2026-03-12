import { useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Shield, Heart, Activity } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const { user, login, demoLogin } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch {
      setError('Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  const handleDemo = async () => {
    setError('')
    setLoading(true)
    try {
      await demoLogin()
      navigate('/dashboard')
    } catch {
      setError('Demo mode unavailable')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-dark via-navy to-navy-light flex flex-col">
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          {/* Logo & Title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 backdrop-blur mb-4">
              <Heart className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              CareBridge<span className="text-clinical-light"> AI</span>
            </h1>
            <p className="text-blue-200 mt-2 text-sm">
              ICU Serious Illness Communication Platform
            </p>
          </div>

          {/* Login Card */}
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none transition-all text-sm"
                  placeholder="you@hospital.org"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-clinical focus:ring-2 focus:ring-clinical/20 outline-none transition-all text-sm"
                  placeholder="Enter your password"
                  required
                />
              </div>

              {error && (
                <div className="text-sm text-danger bg-red-50 rounded-lg px-4 py-2">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-navy hover:bg-navy-dark text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-white px-3 text-gray-400">or</span>
              </div>
            </div>

            <button
              onClick={handleDemo}
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-clinical to-clinical-light hover:from-clinical-dark hover:to-clinical text-white font-semibold rounded-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Activity className="w-4 h-4" />
              Try Demo Mode (No PHI)
            </button>

            <p className="text-xs text-gray-400 text-center mt-4">
              Demo mode uses synthetic data only. No real patient information.
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-3 gap-4 mt-8">
            {[
              { icon: Activity, label: 'Voice Capture' },
              { icon: Heart, label: 'AI Documentation' },
              { icon: Shield, label: 'Risk Detection' },
            ].map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="text-center text-blue-200/70 text-xs"
              >
                <Icon className="w-5 h-5 mx-auto mb-1 opacity-60" />
                {label}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center pb-6 px-4">
        <p className="text-blue-300/50 text-xs max-w-md mx-auto">
          This tool provides language assistance only and does not replace
          clinical judgment. All documentation should be reviewed by the
          responsible clinician.
        </p>
      </div>
    </div>
  )
}
