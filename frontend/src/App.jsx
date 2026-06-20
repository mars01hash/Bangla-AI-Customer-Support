import React, { useState, useEffect } from 'react'
import CustomerChat from './pages/CustomerChat.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import EcommercePage from './pages/EcommercePage.jsx'
import SuperAdminPanel from './pages/SuperAdminPanel.jsx'
import StoreAdminPanel from './pages/StoreAdminPanel.jsx'
import { Terminal, Shield, LogOut, MessageSquare, ShoppingBag, Crown, Store } from 'lucide-react'

function App() {
  const [page, setPage]           = useState('store')
  const [token, setToken]         = useState(localStorage.getItem('token') || '')
  const [role, setRole]           = useState(localStorage.getItem('role') || '')
  const [tenantId, setTenantId]   = useState(localStorage.getItem('tenant_id') || '')
  const [userEmail, setUserEmail] = useState(localStorage.getItem('email') || '')

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token)
      localStorage.setItem('role', role)
      localStorage.setItem('tenant_id', tenantId)
      localStorage.setItem('email', userEmail)
    } else {
      ['token', 'role', 'tenant_id', 'email'].forEach(k => localStorage.removeItem(k))
    }
  }, [token, role, tenantId, userEmail])

  const handleLogout = () => {
    setToken(''); setRole(''); setTenantId(''); setUserEmail('')
    setPage('store')
  }

  const handleLoginSuccess = (jwt, userRole, email, tId) => {
    setToken(jwt); setRole(userRole); setUserEmail(email); setTenantId(tId || '')
    if (userRole === 'super_admin')  setPage('superadmin')
    else if (userRole === 'store_admin') setPage('storeadmin')
    else if (userRole === 'agent')   setPage('dashboard')
    else                             setPage('store')
  }

  const isStaff = role === 'super_admin' || role === 'store_admin' || role === 'agent'

  const NavBtn = ({ target, icon: Icon, label, extra = '' }) => (
    <button onClick={() => setPage(target)}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
        page === target
          ? 'bg-accentPurple/20 text-accentPurple border border-accentPurple/30'
          : `text-slate-300 hover:text-white hover:bg-slate-800 ${extra}`
      }`}>
      <Icon size={16} />{label}
    </button>
  )

  return (
    <div className="min-h-screen bg-darkBg text-slate-100 flex flex-col font-outfit">
      <header className="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setPage('store')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-accentPurple to-accentPink flex items-center justify-center font-bold text-white shadow-lg shadow-accentPurple/25">
            🇧🇩
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Bangla Support AI
            </h1>
            <p className="text-xs text-slate-400 font-medium">Multi-tenant Chatbot Platform</p>
          </div>
        </div>

        <nav className="flex items-center gap-2 flex-wrap justify-end">
          <NavBtn target="store"  icon={ShoppingBag}    label="ShopBD Store" />
          <NavBtn target="chat"   icon={MessageSquare}   label="Support Chat" />

          {token && role === 'super_admin' && (
            <NavBtn target="superadmin" icon={Crown} label="Super Admin" />
          )}
          {token && role === 'store_admin' && (
            <NavBtn target="storeadmin" icon={Store} label="My Store" />
          )}
          {token && (role === 'agent' || role === 'store_admin') && (
            <NavBtn target="dashboard" icon={Shield} label="Agent Dashboard" />
          )}

          {isStaff ? (
            <button onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all duration-300">
              <LogOut size={16} /> Logout
            </button>
          ) : (
            <NavBtn target="login" icon={Shield} label="Staff Portal" />
          )}
        </nav>
      </header>

      <main className="flex-1 flex flex-col">
        {page === 'store'      && <EcommercePage />}
        {page === 'chat'       && <CustomerChat />}
        {page === 'login'      && <Login onLoginSuccess={handleLoginSuccess} />}
        {page === 'superadmin' && <SuperAdminPanel token={token} />}
        {page === 'storeadmin' && <StoreAdminPanel token={token} tenantId={tenantId} />}
        {page === 'dashboard'  && <Dashboard token={token} role={role} />}
      </main>

      <footer className="py-6 border-t border-slate-800 text-center text-xs text-slate-500 bg-slate-950/20">
        &copy; 2026 Bangla AI Customer Support Platform &mdash; Multi-tenant SaaS Edition
      </footer>
    </div>
  )
}

export default App
