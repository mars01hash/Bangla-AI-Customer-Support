import React, { useState } from 'react'
import { KeyRound, Mail, AlertCircle, Loader } from 'lucide-react'

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('agent@example.com')
  const [password, setPassword] = useState('agentpassword123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)

      const response = await fetch('http://localhost:8090/api/auth/token', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Authentication failed. Please verify credentials.')
      }

      const data = await response.json()
      onLoginSuccess(data.access_token, data.role, email)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center p-6 bg-gradient-to-br from-darkBg via-slate-900 to-indigo-950/20">
      <div className="glass-panel w-full max-w-md rounded-2xl p-8 shadow-2xl relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-accentPurple/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-accentPink/20 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-accentPurple/10 border border-accentPurple/20 text-accentPurple flex items-center justify-center mx-auto mb-3">
            <KeyRound size={24} />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Agent Portal Login</h2>
          <p className="text-sm text-slate-400 mt-1">Authorized support staff access only</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3 text-rose-300 text-sm">
            <AlertCircle className="shrink-0 mt-0.5" size={16} />
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-700/50 focus:border-accentPurple rounded-xl py-3 pl-11 pr-4 text-sm text-slate-200 outline-none transition-all duration-300"
                placeholder="agent@example.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Security Password
            </label>
            <div className="relative">
              <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-700/50 focus:border-accentPurple rounded-xl py-3 pl-11 pr-4 text-sm text-slate-200 outline-none transition-all duration-300"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-accentPurple to-accentPurple/80 hover:from-accentPurple hover:to-accentPurple/95 disabled:opacity-50 text-white font-semibold py-3 rounded-xl shadow-lg shadow-accentPurple/20 hover:shadow-accentPurple/30 flex items-center justify-center gap-2 transition-all duration-300 mt-2"
          >
            {loading ? (
              <>
                <Loader className="animate-spin" size={18} />
                Verifying Credentials...
              </>
            ) : (
              'Access Dashboard'
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-slate-800 text-center text-xs text-slate-500">
          <p>Demo accounts (pre-seeded):</p>
          <p className="mt-1 font-mono text-[10px]">
            Agent: agent@example.com / agentpassword123
          </p>
          <p className="font-mono text-[10px]">
            Admin: admin@example.com / adminpassword123
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
