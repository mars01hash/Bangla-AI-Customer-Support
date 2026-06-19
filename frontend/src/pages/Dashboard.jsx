import React, { useState, useEffect } from 'react'
import {
  Users, Ticket, Heart, Clock, Upload, ArrowUpRight,
  CheckCircle, RefreshCw, Filter, FileText, Check, AlertTriangle,
  ShoppingBag, Plus, X, Package
} from 'lucide-react'
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, 
  Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend, BarChart, Bar 
} from 'recharts'

function Dashboard({ token, role }) {
  const [activeTab, setActiveTab] = useState('tickets') // 'tickets', 'analytics', 'upload', 'orders'
  
  // Analytics State
  const [summary, setSummary] = useState({
    total_conversations: 0,
    total_tickets: 0,
    avg_response_time_seconds: 1.45,
    resolution_rate: 1.0,
    user_satisfaction_avg: 4.5,
    frequent_faqs: [],
    sentiment_distribution: {},
    language_distribution: {}
  })
  
  const [chartData, setChartData] = useState({
    daily_stats: [],
    sentiment_data: [],
    language_data: []
  })

  // Ticketing State
  const [tickets, setTickets] = useState([])
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  
  // Upload State
  const [uploadFile, setUploadFile] = useState(null)
  const [uploadStatus, setUploadStatus] = useState('')
  const [uploadLoading, setUploadLoading] = useState(false)
  const [chunksCreated, setChunksCreated] = useState(null)

  // Orders State
  const [orders, setOrders] = useState([])
  const [orderStatusFilter, setOrderStatusFilter] = useState('')
  const [showCreateOrder, setShowCreateOrder] = useState(false)
  const [newOrder, setNewOrder] = useState({
    customer_name: '', customer_email: '', items: '', total_amount: '', estimated_delivery: ''
  })
  const [orderFormError, setOrderFormError] = useState('')
  
  // Fetch telemetry and ticket entries
  const fetchTelemetry = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` }
      
      // Fetch summary
      const sumRes = await fetch('http://localhost:8090/api/analytics/summary', { headers })
      if (sumRes.ok) {
        const sumData = await sumRes.json()
        setSummary(sumData)
      }
      
      // Fetch charts
      const chartRes = await fetch('http://localhost:8090/api/analytics/charts', { headers })
      if (chartRes.ok) {
        const cData = await chartRes.json()
        setChartData(cData)
      }
    } catch (err) {
      console.error(err)
    }
  }
  
  const fetchTickets = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` }
      let url = 'http://localhost:8090/api/tickets?'
      if (statusFilter) url += `status=${statusFilter}&`
      if (priorityFilter) url += `priority=${priorityFilter}&`
      
      const ticketsRes = await fetch(url, { headers })
      if (ticketsRes.ok) {
        const tData = await ticketsRes.json()
        setTickets(tData)
      }
    } catch (err) {
      console.error(err)
    }
  }

  const fetchOrders = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` }
      let url = 'http://localhost:8090/api/orders'
      if (orderStatusFilter) url += `?status=${orderStatusFilter}`
      const res = await fetch(url, { headers })
      if (res.ok) setOrders(await res.json())
    } catch (err) {
      console.error(err)
    }
  }

  const handleUpdateOrderStatus = async (orderId, newStatus) => {
    try {
      await fetch(`http://localhost:8090/api/orders/${orderId}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      })
      fetchOrders()
    } catch (err) {
      console.error(err)
    }
  }

  const handleCreateOrder = async (e) => {
    e.preventDefault()
    setOrderFormError('')
    try {
      const payload = {
        customer_name: newOrder.customer_name,
        customer_email: newOrder.customer_email,
        items: newOrder.items.split(',').map(s => s.trim()).filter(Boolean),
        total_amount: parseFloat(newOrder.total_amount) || 0,
        estimated_delivery: newOrder.estimated_delivery || null
      }
      const res = await fetch('http://localhost:8090/api/orders', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to create order')
      }
      setNewOrder({ customer_name: '', customer_email: '', items: '', total_amount: '', estimated_delivery: '' })
      setShowCreateOrder(false)
      fetchOrders()
    } catch (err) {
      setOrderFormError(err.message)
    }
  }

  const handleDeleteOrder = async (orderId) => {
    if (!window.confirm(`Delete order ${orderId}?`)) return
    try {
      await fetch(`http://localhost:8090/api/orders/${orderId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      fetchOrders()
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchTelemetry()
    fetchTickets()
  }, [token, statusFilter, priorityFilter])

  useEffect(() => {
    if (activeTab === 'orders') fetchOrders()
  }, [token, activeTab, orderStatusFilter])

  // Update ticket details (resolve/assign)
  const handleUpdateTicket = async (ticketId, updatePayload) => {
    try {
      const response = await fetch(`http://localhost:8090/api/tickets/${ticketId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updatePayload)
      })
      if (response.ok) {
        fetchTickets()
        fetchTelemetry()
      }
    } catch (err) {
      console.error(err)
    }
  }

  // Handle RAG PDF/CSV/DOCX/TXT upload
  const handleUploadSubmit = async (e) => {
    e.preventDefault()
    if (!uploadFile) return
    
    setUploadLoading(true)
    setUploadStatus('')
    setChunksCreated(null)
    
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      
      const response = await fetch('http://localhost:8090/api/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'File processing failed.')
      }
      
      const data = await response.json()
      setUploadStatus('success')
      setChunksCreated(data.chunks_created)
      setUploadFile(null)
    } catch (err) {
      setUploadStatus(err.message)
    } finally {
      setUploadLoading(false)
    }
  }

  return (
    <div className="flex-1 p-6 space-y-6 bg-gradient-to-br from-darkBg via-slate-900 to-indigo-950/10 overflow-y-auto">
      {/* 1. Header Navigation Dashboard Tabs */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Agent Operation Center</h2>
          <p className="text-sm text-slate-400">Manage support tickets, track user sentiment and seed the AI knowledge system.</p>
        </div>
        
        <div className="flex bg-slate-900/60 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('tickets')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'tickets' ? 'bg-accentPurple text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Open Tickets ({tickets.length})
          </button>
          
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'analytics' ? 'bg-accentPurple text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Insights & Analytics
          </button>
          
          <button
            onClick={() => setActiveTab('orders')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'orders' ? 'bg-accentPurple text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Orders ({orders.length})
          </button>

          {role === 'admin' && (
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
                activeTab === 'upload' ? 'bg-accentPurple text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Seed Knowledge Base
            </button>
          )}
        </div>
      </div>

      {/* 2. Key Metrics Telemetry Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="glass-panel rounded-2xl p-5 flex items-center justify-between">
          <div>
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Chats</span>
            <p className="text-3xl font-bold text-white mt-1">{summary.total_conversations}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-accentPurple/10 border border-accentPurple/20 text-accentPurple flex items-center justify-center">
            <Users size={20} />
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 flex items-center justify-between">
          <div>
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Active Tickets</span>
            <p className="text-3xl font-bold text-white mt-1">{summary.total_tickets}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center justify-center">
            <Ticket size={20} />
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 flex items-center justify-between">
          <div>
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Satisfaction Rating</span>
            <p className="text-3xl font-bold text-white mt-1">{summary.user_satisfaction_avg.toFixed(1)} / 5.0</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <Heart size={20} />
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 flex items-center justify-between">
          <div>
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Resolution Rate</span>
            <p className="text-3xl font-bold text-white mt-1">{Math.round(summary.resolution_rate * 100)}%</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center">
            <Clock size={20} />
          </div>
        </div>
      </div>

      {/* 3. Tab Subview Renderers */}
      
      {/* --- Tab A: Ticket Management Table --- */}
      {activeTab === 'tickets' && (
        <div className="glass-panel rounded-2xl p-6 shadow-xl">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Ticket size={18} className="text-accentPurple" /> Customer Support Queue
            </h3>
            
            {/* Filter selectors */}
            <div className="flex gap-3 w-full sm:w-auto">
              <div className="relative flex-1 sm:flex-none">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded-lg text-xs py-2 pl-9 pr-6 outline-none text-slate-300 focus:border-accentPurple appearance-none"
                >
                  <option value="">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>

              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg text-xs py-2 px-3 outline-none text-slate-300 focus:border-accentPurple"
              >
                <option value="">All Priorities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase tracking-wider pb-3">
                  <th className="py-4">Ticket ID</th>
                  <th>Customer</th>
                  <th>Topic</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Customer Sentiment</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-sm">
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="py-8 text-center text-slate-500">
                      No active tickets found matching current filters.
                    </td>
                  </tr>
                ) : (
                  tickets.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-900/30 transition duration-150">
                      <td className="py-4 font-mono font-bold text-accentPurple">{t.ticket_id}</td>
                      <td>
                        <div>
                          <p className="font-semibold text-slate-200">{t.customer_name}</p>
                          <p className="text-xs text-slate-500">{t.email}</p>
                        </div>
                      </td>
                      <td className="max-w-xs truncate" title={t.description}>
                        <div>
                          <span className="text-xs bg-slate-800 text-slate-400 border border-slate-700 px-2 py-0.5 rounded capitalize">
                            {t.category}
                          </span>
                          <p className="text-xs text-slate-400 mt-1 truncate">{t.description}</p>
                        </div>
                      </td>
                      <td>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                          t.priority === 'urgent' 
                            ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                            : t.priority === 'high'
                            ? 'bg-amber-500/10 border-amber-500/20 text-amber-500'
                            : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                        }`}>
                          {t.priority}
                        </span>
                      </td>
                      <td>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize ${
                          t.status === 'open' 
                            ? 'bg-blue-500/10 text-blue-400'
                            : t.status === 'in_progress'
                            ? 'bg-amber-500/10 text-amber-400'
                            : 'bg-emerald-500/10 text-emerald-400'
                        }`}>
                          {t.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td>
                        <span className={`capitalize ${
                          t.sentiment === 'positive' ? 'text-emerald-400' : t.sentiment === 'negative' ? 'text-rose-500' : 'text-amber-400'
                        }`}>
                          {t.sentiment}
                        </span>
                      </td>
                      <td className="text-right">
                        <div className="flex gap-2 justify-end">
                          {t.status !== 'resolved' && (
                            <button
                              onClick={() => handleUpdateTicket(t.ticket_id, { status: 'resolved' })}
                              className="bg-emerald-500/10 hover:bg-emerald-500 text-emerald-400 hover:text-white border border-emerald-500/20 p-1.5 rounded-lg transition"
                              title="Mark Resolved"
                            >
                              <Check size={14} />
                            </button>
                          )}
                          {t.status === 'open' && (
                            <button
                              onClick={() => handleUpdateTicket(t.ticket_id, { status: 'in_progress' })}
                              className="bg-accentPurple/10 hover:bg-accentPurple text-accentPurple hover:text-white border border-accentPurple/20 px-2 py-1.5 rounded-lg text-xs font-semibold transition"
                            >
                              Start Working
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* --- Tab B: Telemetry Visual Charts --- */}
      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main line trend graph */}
          <div className="glass-panel rounded-2xl p-6 lg:col-span-2 space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Weekly Conversation Trend</h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData.daily_stats}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis dataKey="date" stroke="#94A3B8" fontSize={11} />
                  <YAxis stroke="#94A3B8" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#1E293B', borderColor: '#475569', borderRadius: '12px' }} />
                  <Legend />
                  <Line type="monotone" dataKey="conversations" name="Chats" stroke="#8B5CF6" strokeWidth={3} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="tickets" name="Tickets Created" stroke="#F59E0B" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Sentiment aggregates */}
          <div className="glass-panel rounded-2xl p-6 space-y-4 flex flex-col justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Language Distribution</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData.language_data}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {chartData.language_data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="space-y-2">
              {chartData.language_data.map((l, idx) => (
                <div key={idx} className="flex justify-between items-center text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: l.color }} />
                    <span className="text-slate-300 font-semibold">{l.name}</span>
                  </div>
                  <span className="text-slate-400 font-mono">{l.value}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Frequency FAQs */}
          <div className="glass-panel rounded-2xl p-6 lg:col-span-1 space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Frequently Asked Queries</h3>
            <div className="divide-y divide-slate-800">
              {summary.frequent_faqs.map((faq, idx) => (
                <div key={idx} className="py-3.5 flex justify-between items-center text-xs">
                  <span className="text-slate-300 font-medium truncate max-w-[80%]" title={faq.question}>
                    {faq.question}
                  </span>
                  <span className="bg-slate-800 border border-slate-700 px-2 py-0.5 rounded-full text-slate-400 font-mono">
                    {faq.count} hits
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Sentiment graph */}
          <div className="glass-panel rounded-2xl p-6 lg:col-span-2 space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Customer Sentiment Share</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData.sentiment_data} layout="vertical">
                  <CartesianGrid stroke="#1E293B" strokeDasharray="3 3" />
                  <XAxis type="number" stroke="#94A3B8" fontSize={11} />
                  <YAxis dataKey="name" type="category" stroke="#94A3B8" fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="value" name="Percentage" radius={[0, 8, 8, 0]}>
                    {chartData.sentiment_data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* --- Tab C: Order Management --- */}
      {activeTab === 'orders' && (
        <div className="glass-panel rounded-2xl p-6 shadow-xl space-y-5">
          {/* Header row */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <ShoppingBag size={18} className="text-accentPurple" /> Order Management
            </h3>
            <div className="flex gap-3 flex-wrap">
              <select
                value={orderStatusFilter}
                onChange={(e) => setOrderStatusFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg text-xs py-2 px-3 outline-none text-slate-300 focus:border-accentPurple"
              >
                <option value="">All Statuses</option>
                <option value="processing">Processing</option>
                <option value="shipped">Shipped</option>
                <option value="out_for_delivery">Out for Delivery</option>
                <option value="delivered">Delivered</option>
                <option value="cancelled">Cancelled</option>
              </select>
              <button
                onClick={() => { setShowCreateOrder(v => !v); setOrderFormError('') }}
                className="flex items-center gap-2 bg-accentPurple/10 hover:bg-accentPurple text-accentPurple hover:text-white border border-accentPurple/30 px-3 py-2 rounded-lg text-xs font-semibold transition"
              >
                <Plus size={14} /> New Order
              </button>
            </div>
          </div>

          {/* Create Order Form */}
          {showCreateOrder && (
            <form onSubmit={handleCreateOrder} className="bg-slate-900/60 border border-slate-700 rounded-xl p-5 space-y-4">
              <h4 className="text-sm font-bold text-white flex items-center gap-2"><Package size={14} /> Create New Order</h4>
              {orderFormError && (
                <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">{orderFormError}</p>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Customer Name</label>
                  <input
                    required
                    value={newOrder.customer_name}
                    onChange={e => setNewOrder(p => ({ ...p, customer_name: e.target.value }))}
                    placeholder="e.g. Tahmid Hasan"
                    className="w-full bg-slate-950/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-accentPurple"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Customer Email</label>
                  <input
                    required type="email"
                    value={newOrder.customer_email}
                    onChange={e => setNewOrder(p => ({ ...p, customer_email: e.target.value }))}
                    placeholder="e.g. tahmid@example.com"
                    className="w-full bg-slate-950/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-accentPurple"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Items (comma-separated)</label>
                  <input
                    required
                    value={newOrder.items}
                    onChange={e => setNewOrder(p => ({ ...p, items: e.target.value }))}
                    placeholder="e.g. Blue Panjabi, Prayer Cap"
                    className="w-full bg-slate-950/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-accentPurple"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 mb-1 block">Total Amount (BDT)</label>
                  <input
                    required type="number" min="0" step="0.01"
                    value={newOrder.total_amount}
                    onChange={e => setNewOrder(p => ({ ...p, total_amount: e.target.value }))}
                    placeholder="e.g. 1250.00"
                    className="w-full bg-slate-950/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-accentPurple"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="text-xs text-slate-400 mb-1 block">Estimated Delivery (optional)</label>
                  <input
                    type="date"
                    value={newOrder.estimated_delivery}
                    onChange={e => setNewOrder(p => ({ ...p, estimated_delivery: e.target.value }))}
                    className="w-full bg-slate-950/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-accentPurple"
                  />
                </div>
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowCreateOrder(false)} className="text-xs text-slate-400 hover:text-white px-3 py-2 transition">Cancel</button>
                <button type="submit" className="bg-accentPurple hover:bg-accentPurple/80 text-white text-xs font-semibold px-4 py-2 rounded-lg transition">Create Order</button>
              </div>
            </form>
          )}

          {/* Orders Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-4">Order ID</th>
                  <th>Customer</th>
                  <th>Items</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Est. Delivery</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-sm">
                {orders.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="py-8 text-center text-slate-500">No orders found.</td>
                  </tr>
                ) : orders.map(order => {
                  const statusColors = {
                    processing: 'bg-blue-500/10 text-blue-400',
                    shipped: 'bg-indigo-500/10 text-indigo-400',
                    out_for_delivery: 'bg-amber-500/10 text-amber-400',
                    delivered: 'bg-emerald-500/10 text-emerald-400',
                    cancelled: 'bg-rose-500/10 text-rose-400',
                  }
                  let itemList = []
                  try { itemList = JSON.parse(order.items || '[]') } catch {}
                  return (
                    <tr key={order.id} className="hover:bg-slate-900/30 transition duration-150">
                      <td className="py-4 font-mono font-bold text-accentPurple">{order.order_id}</td>
                      <td>
                        <p className="font-semibold text-slate-200">{order.customer_name}</p>
                        <p className="text-xs text-slate-500">{order.customer_email}</p>
                      </td>
                      <td className="max-w-[180px]">
                        <p className="text-xs text-slate-300 truncate" title={itemList.join(', ')}>{itemList.join(', ') || '—'}</p>
                      </td>
                      <td className="font-mono text-slate-300">৳{order.total_amount?.toFixed(2) ?? '—'}</td>
                      <td>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize ${statusColors[order.status] || 'bg-slate-800 text-slate-400'}`}>
                          {order.status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="text-xs text-slate-400">{order.estimated_delivery || '—'}</td>
                      <td className="text-right">
                        <div className="flex gap-2 justify-end items-center">
                          <select
                            value={order.status}
                            onChange={e => handleUpdateOrderStatus(order.order_id, e.target.value)}
                            className="bg-slate-900 border border-slate-700 rounded-lg text-[10px] py-1 px-2 text-slate-300 outline-none focus:border-accentPurple"
                          >
                            <option value="processing">Processing</option>
                            <option value="shipped">Shipped</option>
                            <option value="out_for_delivery">Out for Delivery</option>
                            <option value="delivered">Delivered</option>
                            <option value="cancelled">Cancelled</option>
                          </select>
                          {role === 'admin' && (
                            <button
                              onClick={() => handleDeleteOrder(order.order_id)}
                              className="bg-rose-500/10 hover:bg-rose-500 text-rose-400 hover:text-white border border-rose-500/20 p-1.5 rounded-lg transition"
                              title="Delete Order"
                            >
                              <X size={13} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* --- Tab D: RAG Document Seeder Ingestion --- */}
      {activeTab === 'upload' && (
        <div className="max-w-2xl mx-auto glass-panel rounded-2xl p-8 space-y-6">
          <div className="text-center">
            <div className="w-12 h-12 rounded-xl bg-accentPurple/10 border border-accentPurple/20 text-accentPurple flex items-center justify-center mx-auto mb-3">
              <Upload size={24} />
            </div>
            <h3 className="text-lg font-bold text-white">Seed Knowledge Base</h3>
            <p className="text-xs text-slate-400 mt-1">
              Upload PDF customer sheets, FAQ CSVs, DOCX user manuals or TXT policies to ingest text chunks into the vector store.
            </p>
          </div>

          {uploadStatus && uploadStatus !== 'success' && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-start gap-3 text-rose-300 text-xs">
              <AlertTriangle className="shrink-0 mt-0.5" size={14} />
              <p>{uploadStatus}</p>
            </div>
          )}

          {uploadStatus === 'success' && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-3 text-emerald-400 text-xs">
              <CheckCircle className="shrink-0 mt-0.5" size={14} />
              <div>
                <p className="font-semibold">Document processed successfully!</p>
                <p className="mt-1">Vector store compiled and saved <span className="font-mono">{chunksCreated}</span> overlapping chunks.</p>
              </div>
            </div>
          )}

          <form onSubmit={handleUploadSubmit} className="space-y-5">
            <div className="border-2 border-dashed border-slate-700/60 hover:border-accentPurple rounded-xl p-8 text-center cursor-pointer transition relative">
              <input
                type="file"
                accept=".pdf,.docx,.txt,.csv"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <FileText className="mx-auto text-slate-500 mb-3" size={36} />
              {uploadFile ? (
                <div className="text-sm font-semibold text-slate-200">
                  {uploadFile.name} <span className="text-xs text-slate-500">({(uploadFile.size / 1024).toFixed(1)} KB)</span>
                </div>
              ) : (
                <div className="text-xs text-slate-500 leading-normal">
                  Click or drag file here to upload <br />
                  Supports PDF, DOCX, CSV, or TXT (Max 5MB)
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={uploadLoading || !uploadFile}
              className="w-full bg-gradient-to-r from-accentPurple to-accentPurple/80 hover:from-accentPurple hover:to-accentPurple/95 disabled:opacity-50 text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 transition"
            >
              {uploadLoading ? (
                <>
                  <RefreshCw className="animate-spin" size={16} />
                  Chunking and Embedding Text...
                </>
              ) : (
                'Ingest File'
              )}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}

export default Dashboard
