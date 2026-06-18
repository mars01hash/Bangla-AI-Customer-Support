import React, { useState, useEffect } from 'react'
import CustomerChat from './pages/CustomerChat.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import { Terminal, Shield, LogOut, MessageSquare } from 'lucide-react'

function App() {
  const [page, setPage] = useState('chat') // 'chat', 'login', 'dashboard'
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [role, setRole] = useState(localStorage.getItem('role') || '')
  const [userEmail, setUserEmail] = useState(localStorage.getItem('email') || '')

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token)
      localStorage.setItem('role', role)
      localStorage.setItem('email', userEmail)
    } else {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('email')
    }
  }, [token, role, userEmail])

  const handleLogout = () => {
    setToken('')
    setRole('')
    setUserEmail('')
    setPage('chat')
  }

  return (
    <div className="min-h-screen bg-darkBg text-slate-100 flex flex-col font-outfit">
      {/* Global Navigation Bar */}
      <header className="glass-panel sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setPage('chat')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-accentPurple to-accentPink flex items-center justify-center font-bold text-white shadow-lg shadow-accentPurple/25">
            🇧🇩
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Bangla Support AI
            </h1>
            <p className="text-xs text-slate-400 font-medium">Enterprise Multilingual RAG</p>
          </div>
        </div>

        <nav className="flex items-center gap-4">
          <button
            onClick={() => setPage('chat')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
              page === 'chat'
                ? 'bg-accentPurple/20 text-accentPurple border border-accentPurple/30'
                : 'text-slate-300 hover:text-white hover:bg-slate-800'
            }`}
          >
            <MessageSquare size={16} />
            Customer Support
          </button>

          {token && (role === 'admin' || role === 'agent') ? (
            <>
              <button
                onClick={() => setPage('dashboard')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
                  page === 'dashboard'
                    ? 'bg-accentPurple/20 text-accentPurple border border-accentPurple/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Shield size={16} />
                Agent Dashboard
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all duration-300"
              >
                <LogOut size={16} />
                Logout
              </button>
            </>
          ) : (
            <button
              onClick={() => setPage('login')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
                page === 'login'
                  ? 'bg-accentPurple/20 text-accentPurple border border-accentPurple/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Shield size={16} />
              Agent Portal
            </button>
          )}
        </nav>
      </header>

      {/* Main Viewport Routing */}
      <main className="flex-1 flex flex-col">
        {page === 'chat' && <CustomerChat />}
        {page === 'login' && (
          <Login
            onLoginSuccess={(jwtToken, userRole, email) => {
              setToken(jwtToken)
              setRole(userRole)
              setUserEmail(email)
              setPage('dashboard')
            }}
          />
        )}
        {page === 'dashboard' && <Dashboard token={token} role={role} />}
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-slate-800 text-center text-xs text-slate-500 bg-slate-950/20">
        &copy; 2026 Bangla AI Customer Support Platform. Built with FastAPI, LangGraph, ChromaDB, and React.
      </footer>
    </div>
  )
}

export default App
