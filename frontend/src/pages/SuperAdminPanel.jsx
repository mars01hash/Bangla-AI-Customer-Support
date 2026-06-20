import React, { useState, useEffect, useCallback } from 'react'
import {
  Crown, Plus, Trash2, RefreshCw, Users, Store, Key, Globe,
  CheckCircle, XCircle, ChevronRight, BarChart2, Shield, Edit2, RotateCcw, X,
} from 'lucide-react'

import { API_BASE as API } from '../config.js'

const PLAN_BADGE = {
  free:       'bg-slate-700 text-slate-300',
  pro:        'bg-accentPurple/20 text-accentPurple border border-accentPurple/30',
  enterprise: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
}

const ROLE_BADGE = {
  super_admin: 'bg-amber-500/15 text-amber-400 border border-amber-500/25',
  store_admin: 'bg-accentPurple/15 text-accentPurple border border-accentPurple/25',
  agent:       'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
  customer:    'bg-slate-700 text-slate-400',
}

function StatCard({ label, value, icon: Icon, color = 'text-accentPurple' }) {
  return (
    <div className="glass-panel rounded-xl p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center ${color}`}>
        <Icon size={18} />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-slate-400">{label}</p>
      </div>
    </div>
  )
}

export default function SuperAdminPanel({ token }) {
  const [tab, setTab]           = useState('tenants')
  const [tenants, setTenants]   = useState([])
  const [users, setUsers]       = useState([])
  const [loading, setLoading]   = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [newTenant, setNewTenant] = useState({ name: '', domain: '', plan: 'free', widget_color: '#6366f1' })
  const [formErr, setFormErr]   = useState('')
  const [rotatingKey, setRotatingKey] = useState(null)

  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  const fetchTenants = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/tenants`, { headers })
      if (res.ok) setTenants(await res.json())
    } finally { setLoading(false) }
  }, [token])

  const fetchUsers = useCallback(async () => {
    const res = await fetch(`${API}/api/users`, { headers })
    if (res.ok) setUsers(await res.json())
  }, [token])

  useEffect(() => { fetchTenants(); fetchUsers() }, [fetchTenants, fetchUsers])

  const createTenant = async () => {
    if (!newTenant.name.trim()) { setFormErr('Store name is required'); return }
    setFormErr('')
    const res = await fetch(`${API}/api/tenants`, { method: 'POST', headers, body: JSON.stringify(newTenant) })
    if (res.ok) {
      setShowCreate(false)
      setNewTenant({ name: '', domain: '', plan: 'free', widget_color: '#6366f1' })
      fetchTenants()
    } else {
      const err = await res.json()
      setFormErr(err.detail || 'Failed to create')
    }
  }

  const deleteTenant = async (id, name) => {
    if (!window.confirm(`Delete tenant "${name}"? This will remove all associated data.`)) return
    await fetch(`${API}/api/tenants/${id}`, { method: 'DELETE', headers })
    fetchTenants()
  }

  const rotateKey = async (id) => {
    setRotatingKey(id)
    await fetch(`${API}/api/tenants/${id}/rotate-key`, { method: 'POST', headers })
    await fetchTenants()
    setRotatingKey(null)
  }

  const toggleTenant = async (tenant) => {
    await fetch(`${API}/api/tenants/${tenant.id}`, {
      method: 'PUT', headers, body: JSON.stringify({ is_active: !tenant.is_active }),
    })
    fetchTenants()
  }

  const TABS = [
    { id: 'tenants', label: 'Tenants',    icon: Store },
    { id: 'users',   label: 'All Users',  icon: Users },
  ]

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
          <Crown size={22} className="text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Super Admin Panel</h1>
          <p className="text-sm text-slate-400">Platform-level management — all tenants, all users</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Tenants"  value={tenants.length} icon={Store}  color="text-accentPurple" />
        <StatCard label="Active Tenants" value={tenants.filter(t => t.is_active).length} icon={CheckCircle} color="text-emerald-400" />
        <StatCard label="Total Users"    value={users.length}   icon={Users}  color="text-blue-400" />
        <StatCard label="Store Admins"   value={users.filter(u => u.role === 'store_admin').length} icon={Shield} color="text-amber-400" />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-900/50 p-1 rounded-xl w-fit">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              tab === t.id ? 'bg-accentPurple text-white' : 'text-slate-400 hover:text-white'
            }`}>
            <t.icon size={15} />{t.label}
          </button>
        ))}
      </div>

      {/* ── Tenants Tab ── */}
      {tab === 'tenants' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-white">Registered Stores ({tenants.length})</h2>
            <div className="flex gap-2">
              <button onClick={fetchTenants} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
                <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
              </button>
              <button onClick={() => setShowCreate(true)}
                className="flex items-center gap-2 bg-accentPurple hover:bg-accentPurple/90 text-white px-4 py-2 rounded-lg text-sm font-semibold transition">
                <Plus size={15} /> New Store
              </button>
            </div>
          </div>

          {/* Create tenant form */}
          {showCreate && (
            <div className="glass-panel rounded-2xl p-6 mb-4 border border-accentPurple/30">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white">Add New Store</h3>
                <button onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-white"><X size={18}/></button>
              </div>
              {formErr && <p className="text-rose-400 text-xs mb-3">{formErr}</p>}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                {[
                  { key: 'name',   label: 'Store Name *', placeholder: 'e.g. ShopBD' },
                  { key: 'domain', label: 'Website Domain', placeholder: 'shopbd.com' },
                ].map(f => (
                  <div key={f.key}>
                    <label className="text-xs font-semibold text-slate-400 mb-1 block">{f.label}</label>
                    <input value={newTenant[f.key]} onChange={e => setNewTenant(p => ({ ...p, [f.key]: e.target.value }))}
                      placeholder={f.placeholder}
                      className="w-full bg-slate-800 border border-slate-700 focus:border-accentPurple rounded-lg px-3 py-2 text-sm text-slate-200 outline-none transition" />
                  </div>
                ))}
                <div>
                  <label className="text-xs font-semibold text-slate-400 mb-1 block">Plan</label>
                  <select value={newTenant.plan} onChange={e => setNewTenant(p => ({ ...p, plan: e.target.value }))}
                    className="w-full bg-slate-800 border border-slate-700 focus:border-accentPurple rounded-lg px-3 py-2 text-sm text-slate-200 outline-none transition">
                    <option value="free">Free</option>
                    <option value="pro">Pro</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 mb-1 block">Widget Color</label>
                  <div className="flex items-center gap-2">
                    <input type="color" value={newTenant.widget_color} onChange={e => setNewTenant(p => ({ ...p, widget_color: e.target.value }))}
                      className="w-10 h-10 rounded-lg border border-slate-700 bg-slate-800 cursor-pointer" />
                    <span className="text-sm text-slate-300 font-mono">{newTenant.widget_color}</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-slate-400 hover:text-white border border-slate-700 rounded-lg transition">Cancel</button>
                <button onClick={createTenant} className="px-4 py-2 bg-accentPurple text-white text-sm font-semibold rounded-lg hover:bg-accentPurple/90 transition">Create Store</button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {tenants.map(t => {
              const agents = users.filter(u => u.tenant_id === t.id && u.role === 'agent').length
              const admins = users.filter(u => u.tenant_id === t.id && u.role === 'store_admin').length
              return (
                <div key={t.id} className={`glass-panel rounded-2xl p-5 transition ${!t.is_active ? 'opacity-60' : ''}`}>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg shrink-0"
                        style={{ backgroundColor: t.widget_color + '33', border: `1px solid ${t.widget_color}55` }}>
                        {t.name[0]}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="font-bold text-white">{t.name}</p>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${PLAN_BADGE[t.plan] || PLAN_BADGE.free}`}>
                            {t.plan.toUpperCase()}
                          </span>
                          {t.is_active
                            ? <span className="text-[10px] text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded-full">Active</span>
                            : <span className="text-[10px] text-slate-500 bg-slate-800 border border-slate-700 px-2 py-0.5 rounded-full">Inactive</span>
                          }
                        </div>
                        <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                          <Globe size={10}/>{t.domain || 'No domain set'} &nbsp;·&nbsp; {admins} admin · {agents} agents
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <button onClick={() => toggleTenant(t)} title={t.is_active ? 'Deactivate' : 'Activate'}
                        className={`p-2 rounded-lg border text-xs font-semibold transition ${
                          t.is_active ? 'border-slate-700 text-slate-400 hover:border-rose-500/50 hover:text-rose-400' : 'border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10'
                        }`}>
                        {t.is_active ? <XCircle size={14}/> : <CheckCircle size={14}/>}
                      </button>
                      <button onClick={() => rotateKey(t.id)} title="Rotate API key" disabled={rotatingKey === t.id}
                        className="p-2 rounded-lg border border-slate-700 text-slate-400 hover:text-amber-400 hover:border-amber-500/30 transition disabled:opacity-40">
                        <RotateCcw size={14} className={rotatingKey === t.id ? 'animate-spin' : ''} />
                      </button>
                      <button onClick={() => deleteTenant(t.id, t.name)} title="Delete"
                        className="p-2 rounded-lg border border-slate-700 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 transition">
                        <Trash2 size={14}/>
                      </button>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-800 flex items-center gap-2">
                    <Key size={11} className="text-slate-500"/>
                    <code className="text-[10px] font-mono text-slate-400 flex-1 truncate">{t.api_key}</code>
                    <button onClick={() => navigator.clipboard.writeText(t.api_key)}
                      className="text-[10px] text-accentPurple hover:underline shrink-0">copy</button>
                  </div>
                </div>
              )
            })}
            {tenants.length === 0 && !loading && (
              <div className="text-center py-16 text-slate-500">
                <Store size={48} className="mx-auto mb-3 opacity-30" />
                <p>No tenants yet — create your first store.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Users Tab ── */}
      {tab === 'users' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-white">All Users ({users.length})</h2>
            <button onClick={fetchUsers} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
              <RefreshCw size={15} />
            </button>
          </div>
          <div className="glass-panel rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500 text-xs uppercase tracking-wider">
                  {['Name', 'Email', 'Role', 'Store', 'Status'].map(h => (
                    <th key={h} className="text-left px-4 py-3 font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => {
                  const store = tenants.find(t => t.id === u.tenant_id)
                  return (
                    <tr key={u.id} className={`border-b border-slate-800/50 hover:bg-slate-800/30 transition ${i % 2 === 0 ? '' : 'bg-slate-900/20'}`}>
                      <td className="px-4 py-3 font-semibold text-white">{u.full_name}</td>
                      <td className="px-4 py-3 text-slate-400 text-xs font-mono">{u.email}</td>
                      <td className="px-4 py-3">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${ROLE_BADGE[u.role] || ROLE_BADGE.customer}`}>
                          {u.role.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-xs">{store ? store.name : <span className="text-slate-600">—</span>}</td>
                      <td className="px-4 py-3">
                        {u.is_active
                          ? <span className="text-[10px] text-emerald-400">● Active</span>
                          : <span className="text-[10px] text-rose-400">● Inactive</span>
                        }
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
