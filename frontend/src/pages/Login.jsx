import React, { useState } from 'react'
import { KeyRound, Mail, AlertCircle, Loader, Crown, Store, Shield, Users } from 'lucide-react'
import { API_BASE } from '../config.js'

const DEMO_ACCOUNTS = [
  { role: 'super_admin', email: 'super@platform.com', pass: 'superpassword123', label: 'Super Admin', icon: Crown, color: 'text-amber-400' },
  { role: 'store_admin', email: 'admin@shopbd.com',   pass: 'storepassword123', label: 'Store Admin (ShopBD)', icon: Store, color: 'text-accentPurple' },
  { role: 'store_admin', email: 'admin@fashionbd.com', pass: 'storepassword123', label: 'Store Admin (FashionBD)', icon: Store, color: 'text-pink-400' },
  { role: 'agent',       email: 'agent@shopbd.com',   pass: 'agentpassword123', label: 'Support Agent', icon: Shield, color: 'text-emerald-400' },
]

function Login({ onLoginSuccess }) {
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('username', email)
      fd.append('password', password)
      const res = await fetch(`${API_BASE}/api/auth/token`, { method: 'POST', body: fd })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Authentication failed.')
      }
      const data = await res.json()
      onLoginSuccess(data.access_token, data.role, email, data.tenant_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (acc) => { setEmail(acc.email); setPassword(acc.pass); setError('') }

  return (
    <div className="flex-1 flex items-center justify-center p-6 bg-gradient-to-br from-darkBg via-slate-900 to-indigo-950/20">
      <div className="glass-panel w-full max-w-md rounded-2xl p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-accentPurple/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-accentPink/20 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-accentPurple/10 border border-accentPurple/20 text-accentPurple flex items-center justify-center mx-auto mb-3">
            <KeyRound size={24} />
          </div>
          <h2 className="text-2xl font-bold text-white">Staff Portal</h2>
          <p className="text-sm text-slate-400 mt-1">Super Admins · Store Admins · Agents</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-2 text-rose-300 text-sm">
            <AlertCircle className="shrink-0 mt-0.5" size={15} /><p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-700/50 focus:border-accentPurple rounded-xl py-2.5 pl-10 pr-4 text-sm text-slate-200 outline-none transition"
                placeholder="staff@yourstore.com" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Password</label>
            <div className="relative">
              <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input type="password" required value={password} onChange={e => setPassword(e.target.value)}
                className="w-full bg-slate-900/60 border border-slate-700/50 focus:border-accentPurple rounded-xl py-2.5 pl-10 pr-4 text-sm text-slate-200 outline-none transition"
                placeholder="••••••••" />
            </div>
          </div>
          <button type="submit" disabled={loading}
            className="w-full bg-gradient-to-r from-accentPurple to-accentPurple/80 hover:opacity-90 disabled:opacity-50 text-white font-semibold py-3 rounded-xl shadow-lg flex items-center justify-center gap-2 transition-all mt-2">
            {loading ? <><Loader className="animate-spin" size={16} />Verifying…</> : 'Sign In'}
          </button>
        </form>

        {/* Demo accounts */}
        <div className="mt-6 pt-5 border-t border-slate-800">
          <p className="text-[11px] text-slate-500 text-center mb-3 font-semibold uppercase tracking-wider">Demo Accounts</p>
          <div className="space-y-1.5">
            {DEMO_ACCOUNTS.map(acc => {
              const Icon = acc.icon
              return (
                <button key={acc.email} onClick={() => fillDemo(acc)}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/40 hover:border-accentPurple/30 text-left transition group">
                  <Icon size={14} className={acc.color} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-200">{acc.label}</p>
                    <p className="text-[10px] text-slate-500 font-mono truncate">{acc.email}</p>
                  </div>
                  <span className="text-[10px] text-slate-600 group-hover:text-accentPurple transition">click to fill</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
