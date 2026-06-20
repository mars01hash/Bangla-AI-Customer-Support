import React, { useState, useEffect, useCallback } from 'react'
import {
  Store, Key, Code2, Book, Users, Ticket, Settings, Plus, Trash2,
  RefreshCw, Copy, Check, CheckCircle, ChevronRight, Shield,
  BarChart2, MessageSquare, Globe, Palette, X, AlertCircle,
} from 'lucide-react'

const API = 'http://localhost:8090'

const TICKET_STATUS_CLS = {
  open:        'bg-rose-500/10 text-rose-400 border border-rose-500/20',
  in_progress: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
  resolved:    'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  closed:      'bg-slate-700 text-slate-400',
}

function StatCard({ label, value, icon: Icon, color = 'text-accentPurple' }) {
  return (
    <div className="glass-panel rounded-xl p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center ${color}`}><Icon size={18}/></div>
      <div><p className="text-2xl font-bold text-white">{value}</p><p className="text-xs text-slate-400">{label}</p></div>
    </div>
  )
}

const inputCls = 'w-full bg-slate-800 border border-slate-700 focus:border-accentPurple rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none transition'

export default function StoreAdminPanel({ token }) {
  const [tab, setTab]       = useState('overview')
  const [store, setStore]   = useState(null)
  const [stats, setStats]   = useState(null)
  const [kb, setKb]         = useState([])
  const [agents, setAgents] = useState([])
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [embedCode, setEmbedCode] = useState(null)

  // KB form
  const [showKbForm, setShowKbForm] = useState(false)
  const [kbForm, setKbForm]         = useState({ question: '', answer: '', category: 'general' })
  const [kbErr, setKbErr]           = useState('')

  // Agent form
  const [showAgentForm, setShowAgentForm] = useState(false)
  const [agentForm, setAgentForm]         = useState({ email: '', full_name: '', password: '' })
  const [agentErr, setAgentErr]           = useState('')

  // Settings form
  const [settingsForm, setSettingsForm]   = useState({ widget_color: '#6366f1', welcome_message: '' })
  const [settingsSaved, setSettingsSaved] = useState(false)

  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  const fetchAll = useCallback(async () => {
    setLoading(true)
    try {
      const [storeRes, statsRes, kbRes, agentsRes, ticketsRes, embedRes] = await Promise.all([
        fetch(`${API}/api/my-store`, { headers }),
        fetch(`${API}/api/my-store/stats`, { headers }),
        fetch(`${API}/api/my-store/knowledge`, { headers }),
        fetch(`${API}/api/my-store/agents`, { headers }),
        fetch(`${API}/api/tickets`, { headers }),
        fetch(`${API}/api/my-store/embed-code`, { headers }),
      ])
      if (storeRes.ok) {
        const s = await storeRes.json()
        setStore(s)
        setSettingsForm({ widget_color: s.widget_color, welcome_message: s.welcome_message })
      }
      if (statsRes.ok)   setStats(await statsRes.json())
      if (kbRes.ok)      setKb(await kbRes.json())
      if (agentsRes.ok)  setAgents(await agentsRes.json())
      if (ticketsRes.ok) setTickets(await ticketsRes.json())
      if (embedRes.ok)   setEmbedCode(await embedRes.json())
    } finally { setLoading(false) }
  }, [token])

  useEffect(() => { fetchAll() }, [fetchAll])

  const addKbEntry = async () => {
    if (!kbForm.question.trim() || !kbForm.answer.trim()) { setKbErr('Question and answer are required'); return }
    setKbErr('')
    const res = await fetch(`${API}/api/my-store/knowledge`, { method: 'POST', headers, body: JSON.stringify(kbForm) })
    if (res.ok) {
      setShowKbForm(false)
      setKbForm({ question: '', answer: '', category: 'general' })
      fetchAll()
    } else {
      const err = await res.json()
      setKbErr(err.detail || 'Failed')
    }
  }

  const deleteKbEntry = async (id) => {
    await fetch(`${API}/api/my-store/knowledge/${id}`, { method: 'DELETE', headers })
    setKb(prev => prev.filter(e => e.id !== id))
  }

  const addAgent = async () => {
    if (!agentForm.email || !agentForm.full_name || !agentForm.password) { setAgentErr('All fields required'); return }
    setAgentErr('')
    const res = await fetch(`${API}/api/my-store/agents`, { method: 'POST', headers, body: JSON.stringify(agentForm) })
    if (res.ok) {
      setShowAgentForm(false)
      setAgentForm({ email: '', full_name: '', password: '' })
      fetchAll()
    } else {
      const err = await res.json()
      setAgentErr(err.detail || 'Failed')
    }
  }

  const removeAgent = async (id, name) => {
    if (!window.confirm(`Remove agent "${name}"?`)) return
    await fetch(`${API}/api/my-store/agents/${id}`, { method: 'DELETE', headers })
    setAgents(prev => prev.filter(a => a.id !== id))
  }

  const saveSettings = async () => {
    const res = await fetch(`${API}/api/my-store`, { method: 'PUT', headers, body: JSON.stringify(settingsForm) })
    if (res.ok) { setSettingsSaved(true); setTimeout(() => setSettingsSaved(false), 2000); fetchAll() }
  }

  const updateTicketStatus = async (ticket_id, newStatus) => {
    const res = await fetch(`${API}/api/tickets/${ticket_id}`, { method: 'PUT', headers, body: JSON.stringify({ status: newStatus }) })
    if (res.ok) setTickets(prev => prev.map(t => t.ticket_id === ticket_id ? { ...t, status: newStatus } : t))
  }

  const copyEmbed = () => {
    navigator.clipboard.writeText(embedCode?.embed_snippet || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const TABS = [
    { id: 'overview', label: 'Overview',       icon: BarChart2 },
    { id: 'kb',       label: 'Knowledge Base', icon: Book      },
    { id: 'embed',    label: 'Embed Code',     icon: Code2     },
    { id: 'agents',   label: 'Agents',         icon: Users     },
    { id: 'tickets',  label: 'Tickets',        icon: Ticket    },
    { id: 'settings', label: 'Settings',       icon: Settings  },
  ]

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-xl"
          style={{ backgroundColor: (store?.widget_color || '#6366f1') + '33', border: `1.5px solid ${store?.widget_color || '#6366f1'}55` }}>
          {store ? store.name[0] : <Store size={22} className="text-accentPurple" />}
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">{store?.name || 'My Store'}</h1>
          <p className="text-sm text-slate-400 flex items-center gap-1">
            <Globe size={12}/>{store?.domain || 'No domain set'}
            &nbsp;·&nbsp;
            <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
              store?.plan === 'pro' ? 'bg-accentPurple/20 text-accentPurple border border-accentPurple/30'
              : store?.plan === 'enterprise' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              : 'bg-slate-700 text-slate-400'
            }`}>{(store?.plan || 'free').toUpperCase()}</span>
          </p>
        </div>
        <button onClick={fetchAll} className="ml-auto p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-900/50 p-1 rounded-xl flex-wrap">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition ${
              tab === t.id ? 'bg-accentPurple text-white' : 'text-slate-400 hover:text-white'
            }`}>
            <t.icon size={13}/>{t.label}
          </button>
        ))}
      </div>

      {/* ── Overview ── */}
      {tab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <StatCard label="Open Tickets"   value={stats?.open_tickets ?? '…'}   icon={Ticket}       color="text-rose-400" />
            <StatCard label="Total Tickets"  value={stats?.total_tickets ?? '…'}  icon={Ticket}       color="text-amber-400" />
            <StatCard label="Conversations"  value={stats?.conversations ?? '…'}  icon={MessageSquare} color="text-accentPurple" />
            <StatCard label="KB Entries"     value={stats?.kb_entries ?? '…'}     icon={Book}         color="text-emerald-400" />
            <StatCard label="Agents"         value={stats?.agents ?? '…'}         icon={Shield}       color="text-blue-400" />
          </div>
          <div className="glass-panel rounded-2xl p-5">
            <h3 className="font-bold text-white mb-3 text-sm">Quick Start</h3>
            <div className="space-y-2 text-sm text-slate-400">
              {[
                { step: 1, label: 'Add your FAQ entries to the Knowledge Base', done: (stats?.kb_entries ?? 0) > 0, tab: 'kb' },
                { step: 2, label: 'Copy the embed code and paste into your website', done: false, tab: 'embed' },
                { step: 3, label: 'Invite support agents to handle tickets', done: (stats?.agents ?? 0) > 0, tab: 'agents' },
              ].map(s => (
                <div key={s.step} className="flex items-center gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${s.done ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                    {s.done ? '✓' : s.step}
                  </div>
                  <span className={s.done ? 'line-through text-slate-600' : ''}>{s.label}</span>
                  {!s.done && (
                    <button onClick={() => setTab(s.tab)} className="ml-auto text-xs text-accentPurple hover:underline flex items-center gap-1">
                      Go <ChevronRight size={11}/>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Knowledge Base ── */}
      {tab === 'kb' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-white">Knowledge Base</h2>
              <p className="text-xs text-slate-400 mt-0.5">FAQ entries your chatbot uses to answer customer questions.</p>
            </div>
            <button onClick={() => setShowKbForm(true)}
              className="flex items-center gap-2 bg-accentPurple hover:bg-accentPurple/90 text-white px-4 py-2 rounded-lg text-sm font-semibold transition">
              <Plus size={15}/> Add Entry
            </button>
          </div>

          {showKbForm && (
            <div className="glass-panel rounded-2xl p-5 mb-4 border border-accentPurple/30 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-white text-sm">New Knowledge Entry</h3>
                <button onClick={() => setShowKbForm(false)} className="text-slate-400 hover:text-white"><X size={16}/></button>
              </div>
              {kbErr && <p className="text-rose-400 text-xs">{kbErr}</p>}
              <div>
                <label className="text-xs font-semibold text-slate-400 mb-1 block">Question</label>
                <input value={kbForm.question} onChange={e => setKbForm(f => ({ ...f, question: e.target.value }))}
                  placeholder="e.g. কতদিনে ডেলিভারি হয়?" className={inputCls} />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 mb-1 block">Answer</label>
                <textarea rows={3} value={kbForm.answer} onChange={e => setKbForm(f => ({ ...f, answer: e.target.value }))}
                  placeholder="Write the full answer here…" className={inputCls + ' resize-none'} />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 mb-1 block">Category</label>
                <select value={kbForm.category} onChange={e => setKbForm(f => ({ ...f, category: e.target.value }))}
                  className={inputCls}>
                  {['general','delivery','payment','returns','product','policy'].map(c => (
                    <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setShowKbForm(false)} className="px-4 py-2 text-sm text-slate-400 border border-slate-700 rounded-lg hover:text-white transition">Cancel</button>
                <button onClick={addKbEntry} className="px-4 py-2 bg-accentPurple text-white text-sm font-semibold rounded-lg hover:bg-accentPurple/90 transition">Save Entry</button>
              </div>
            </div>
          )}

          {kb.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              <Book size={48} className="mx-auto mb-3 opacity-30"/>
              <p>No entries yet. Add your first FAQ entry.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {kb.map(entry => (
                <div key={entry.id} className="glass-panel rounded-xl p-4 flex gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] bg-accentPurple/15 text-accentPurple border border-accentPurple/25 px-2 py-0.5 rounded-full font-semibold">{entry.category}</span>
                    </div>
                    <p className="text-sm font-semibold text-white mb-1">Q: {entry.question}</p>
                    <p className="text-xs text-slate-400 line-clamp-2">A: {entry.answer}</p>
                  </div>
                  <button onClick={() => deleteKbEntry(entry.id)} className="p-1.5 text-slate-500 hover:text-rose-400 transition shrink-0 self-start mt-1">
                    <Trash2 size={14}/>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Embed Code ── */}
      {tab === 'embed' && (
        <div className="space-y-6">
          <div>
            <h2 className="font-bold text-white mb-1">Embed Your Chatbot</h2>
            <p className="text-sm text-slate-400">Copy this snippet and paste it before the <code className="text-accentPurple">&lt;/body&gt;</code> tag on your website.</p>
          </div>

          <div className="glass-panel rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2"><Key size={14} className="text-accentPurple"/> Your API Key</h3>
            </div>
            <div className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2 border border-slate-700">
              <code className="text-xs font-mono text-emerald-400 flex-1 truncate">{embedCode?.api_key || '…'}</code>
              <button onClick={() => { navigator.clipboard.writeText(embedCode?.api_key || ''); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
                className="text-slate-400 hover:text-white transition shrink-0">
                {copied ? <Check size={14} className="text-emerald-400"/> : <Copy size={14}/>}
              </button>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2"><Code2 size={14} className="text-accentPurple"/> Embed Snippet</h3>
              <button onClick={copyEmbed}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  copied ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-accentPurple/10 text-accentPurple border border-accentPurple/30 hover:bg-accentPurple/20'
                }`}>
                {copied ? <><Check size={12}/>Copied!</> : <><Copy size={12}/>Copy Code</>}
              </button>
            </div>
            <pre className="text-[11px] font-mono text-slate-300 bg-slate-900 rounded-xl p-4 overflow-x-auto whitespace-pre-wrap break-all leading-relaxed">
              {embedCode?.embed_snippet || '…'}
            </pre>
          </div>

          <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4 text-sm text-blue-300">
            <p className="font-semibold mb-2">How it works</p>
            <ul className="text-xs space-y-1 text-blue-300/80 list-disc list-inside">
              <li>The widget authenticates using your API key — each request is scoped to your store.</li>
              <li>The chatbot uses only your Knowledge Base entries to answer questions.</li>
              <li>If it can't find an answer, it asks clarifying questions or raises a ticket.</li>
              <li>Tickets appear in your Agent Dashboard filtered to your store only.</li>
            </ul>
          </div>
        </div>
      )}

      {/* ── Agents ── */}
      {tab === 'agents' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-white">Support Agents</h2>
              <p className="text-xs text-slate-400 mt-0.5">Agents can view and respond to your store's support tickets.</p>
            </div>
            <button onClick={() => setShowAgentForm(true)}
              className="flex items-center gap-2 bg-accentPurple hover:bg-accentPurple/90 text-white px-4 py-2 rounded-lg text-sm font-semibold transition">
              <Plus size={15}/> Invite Agent
            </button>
          </div>

          {showAgentForm && (
            <div className="glass-panel rounded-2xl p-5 mb-4 border border-accentPurple/30 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-white text-sm">Add Support Agent</h3>
                <button onClick={() => setShowAgentForm(false)} className="text-slate-400 hover:text-white"><X size={16}/></button>
              </div>
              {agentErr && <p className="text-rose-400 text-xs">{agentErr}</p>}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { key: 'full_name', label: 'Full Name', placeholder: 'Rahat Ahmed' },
                  { key: 'email',     label: 'Email',     placeholder: 'agent@yourstore.com', type: 'email' },
                  { key: 'password',  label: 'Password',  placeholder: '••••••••', type: 'password' },
                ].map(f => (
                  <div key={f.key}>
                    <label className="text-xs font-semibold text-slate-400 mb-1 block">{f.label}</label>
                    <input type={f.type || 'text'} value={agentForm[f.key]} placeholder={f.placeholder}
                      onChange={e => setAgentForm(p => ({ ...p, [f.key]: e.target.value }))}
                      className={inputCls} />
                  </div>
                ))}
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setShowAgentForm(false)} className="px-4 py-2 text-sm text-slate-400 border border-slate-700 rounded-lg hover:text-white transition">Cancel</button>
                <button onClick={addAgent} className="px-4 py-2 bg-accentPurple text-white text-sm font-semibold rounded-lg hover:bg-accentPurple/90 transition">Add Agent</button>
              </div>
            </div>
          )}

          {agents.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              <Users size={48} className="mx-auto mb-3 opacity-30"/>
              <p>No agents yet. Invite your first support agent.</p>
            </div>
          ) : (
            <div className="glass-panel rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500 text-xs uppercase tracking-wider">
                    {['Name', 'Email', 'Status', ''].map(h => (
                      <th key={h} className="text-left px-4 py-3 font-semibold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {agents.map(a => (
                    <tr key={a.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
                      <td className="px-4 py-3 font-semibold text-white">{a.full_name}</td>
                      <td className="px-4 py-3 text-slate-400 text-xs font-mono">{a.email}</td>
                      <td className="px-4 py-3">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${a.is_active ? 'text-emerald-400' : 'text-rose-400'}`}>
                          ● {a.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <button onClick={() => removeAgent(a.id, a.full_name)} className="p-1.5 text-slate-500 hover:text-rose-400 transition">
                          <Trash2 size={14}/>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Tickets ── */}
      {tab === 'tickets' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-white">Support Tickets ({tickets.length})</h2>
            <button onClick={fetchAll} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
              <RefreshCw size={15}/>
            </button>
          </div>
          {tickets.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              <Ticket size={48} className="mx-auto mb-3 opacity-30"/><p>No tickets yet.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {tickets.map(t => (
                <div key={t.ticket_id} className="glass-panel rounded-xl p-4 flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="font-mono text-xs text-accentPurple font-bold">{t.ticket_id}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${TICKET_STATUS_CLS[t.status] || ''}`}>{t.status}</span>
                      <span className="text-[10px] text-slate-500">{t.category}</span>
                    </div>
                    <p className="text-sm text-white font-semibold truncate">{t.customer_name}</p>
                    <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{t.description}</p>
                  </div>
                  <select value={t.status}
                    onChange={e => updateTicketStatus(t.ticket_id, e.target.value)}
                    className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-300 outline-none shrink-0">
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Settings ── */}
      {tab === 'settings' && (
        <div className="max-w-lg space-y-6">
          <div>
            <h2 className="font-bold text-white mb-1">Widget Settings</h2>
            <p className="text-xs text-slate-400">Customize how your chatbot looks and greets customers.</p>
          </div>

          <div className="glass-panel rounded-2xl p-6 space-y-5">
            <div>
              <label className="text-xs font-semibold text-slate-400 mb-1.5 block">Widget Color</label>
              <div className="flex items-center gap-3">
                <input type="color" value={settingsForm.widget_color}
                  onChange={e => setSettingsForm(f => ({ ...f, widget_color: e.target.value }))}
                  className="w-12 h-12 rounded-xl border border-slate-700 bg-slate-800 cursor-pointer" />
                <div>
                  <p className="text-sm font-mono text-slate-200">{settingsForm.widget_color}</p>
                  <p className="text-xs text-slate-500">Chat button and header color</p>
                </div>
                <div className="ml-auto w-10 h-10 rounded-full flex items-center justify-center text-white text-lg shadow-lg"
                  style={{ background: settingsForm.widget_color }}>💬</div>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 mb-1.5 block">Welcome Message</label>
              <textarea rows={3} value={settingsForm.welcome_message}
                onChange={e => setSettingsForm(f => ({ ...f, welcome_message: e.target.value }))}
                placeholder="e.g. Hello! How can I help you today?"
                className={inputCls + ' resize-none'} />
              <p className="text-xs text-slate-500 mt-1">Shown when customers first open the chat widget.</p>
            </div>

            <button onClick={saveSettings}
              className={`w-full py-3 rounded-xl font-bold text-sm transition flex items-center justify-center gap-2 ${
                settingsSaved ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-accentPurple hover:bg-accentPurple/90 text-white'
              }`}>
              {settingsSaved ? <><CheckCircle size={16}/>Saved!</> : 'Save Settings'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
