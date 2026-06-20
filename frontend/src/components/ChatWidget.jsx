import React, { useState, useEffect, useRef } from 'react'
import { MessageCircle, X, Send, Minimize2, Bot } from 'lucide-react'

const API_BASE = 'http://localhost:8090'

const QUICK_PROMPTS = [
  'অর্ডার ট্র্যাক করুন',
  'রিটার্ন পলিসি',
  'পেমেন্ট সমস্যা',
  'ডেলিভারি কখন?',
]

function ChatWidget({ prefilledMessage = '', onPrefilledUsed }) {
  const [open, setOpen] = useState(false)
  const [minimized, setMinimized] = useState(false)
  const [sessionId] = useState(() => 'widget-' + Math.random().toString(36).substr(2, 9))
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      content: "হ্যালো! আমি ShopBD-এর AI সহকারী। অর্ডার, রিটার্ন, পেমেন্ট — যেকোনো বিষয়ে সাহায্য করতে পারি। কী জানতে চান? (Hello! I'm your ShopBD support assistant. How can I help?)",
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [hasUnread, setHasUnread] = useState(true)
  const [ticketCreated, setTicketCreated] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // When a prefilled message arrives, open the widget and auto-send
  useEffect(() => {
    if (!prefilledMessage) return
    setOpen(true)
    setMinimized(false)
    setHasUnread(false)
    // Small delay so the widget renders before sending
    const t = setTimeout(() => {
      sendMessage(prefilledMessage)
      onPrefilledUsed?.()
    }, 300)
    return () => clearTimeout(t)
  }, [prefilledMessage])

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  useEffect(() => {
    if (open && !minimized) inputRef.current?.focus()
  }, [open, minimized])

  const handleOpen = () => {
    setOpen(true)
    setMinimized(false)
    setHasUnread(false)
  }

  const handleClose = () => {
    setOpen(false)
    setMinimized(false)
  }

  const sendMessage = async (textOverride) => {
    const text = textOverride ?? input.trim()
    if (!text || loading) return
    setInput('')
    setLoading(true)

    setMessages(prev => [
      ...prev,
      { sender: 'user', content: text, timestamp: new Date().toISOString() },
    ])

    try {
      const form = new FormData()
      form.append('message_in', text)
      form.append('session_id', sessionId)
      const res = await fetch(`${API_BASE}/api/chat`, { method: 'POST', body: form })
      const data = await res.json()

      if (data.ticket_escalated && data.ticket_id) {
        setTicketCreated(data.ticket_id)
      }

      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          content: data.answer,
          timestamp: new Date().toISOString(),
          ticket_id: data.ticket_id || null,
        },
      ])
    } catch {
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          content: 'দুঃখিত, একটি সমস্যা হয়েছে। (Sorry, something went wrong.)',
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Chat Panel */}
      {open && (
        <div
          className="flex flex-col rounded-2xl shadow-2xl shadow-black/50 overflow-hidden border border-slate-700/60"
          style={{
            width: 360,
            height: minimized ? 'auto' : 500,
            background: 'rgba(15, 23, 42, 0.97)',
            backdropFilter: 'blur(16px)',
          }}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-accentPurple to-accentPink px-4 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center">
                <Bot size={14} className="text-white" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm leading-none">ShopBD সাপোর্ট</p>
                <p className="text-white/60 text-[10px] mt-0.5 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                  অনলাইন · AI-powered
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setMinimized(m => !m)}
                className="text-white/60 hover:text-white transition p-1"
                title="Minimize"
              >
                <Minimize2 size={14} />
              </button>
              <button onClick={handleClose} className="text-white/60 hover:text-white transition p-1">
                <X size={16} />
              </button>
            </div>
          </div>

          {!minimized && (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex gap-2 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.sender === 'bot' && (
                      <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-accentPurple to-accentPink flex items-center justify-center text-[9px] font-bold shrink-0 mt-0.5 text-white">
                        AI
                      </div>
                    )}
                    <div
                      className={`max-w-[78%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-accentPurple text-white rounded-tr-none'
                          : 'bg-slate-800 text-slate-100 border border-slate-700/60 rounded-tl-none'
                      }`}
                    >
                      {msg.content}
                      {msg.ticket_id && (
                        <p className="mt-1.5 text-[10px] text-amber-400 font-mono">
                          Ticket: {msg.ticket_id}
                        </p>
                      )}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="flex gap-2 justify-start">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-accentPurple to-accentPink flex items-center justify-center text-[9px] font-bold shrink-0 text-white">
                      AI
                    </div>
                    <div className="bg-slate-800 border border-slate-700/60 rounded-xl rounded-tl-none px-3 py-2.5 flex gap-1 items-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {/* Quick prompts (only shown early in conversation) */}
              {messages.length <= 2 && (
                <div className="px-3 pb-2 flex gap-1.5 flex-wrap">
                  {QUICK_PROMPTS.map(q => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q)}
                      disabled={loading}
                      className="text-[10px] px-2.5 py-1 bg-slate-800 hover:bg-accentPurple/20 border border-slate-700 hover:border-accentPurple/40 rounded-full text-slate-300 hover:text-white transition"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}

              {/* Active ticket banner */}
              {ticketCreated && (
                <div className="mx-3 mb-2 px-3 py-2 bg-amber-500/10 border border-amber-500/30 rounded-lg text-[10px] text-amber-300">
                  টিকিট তৈরি হয়েছে: <span className="font-mono font-bold">{ticketCreated}</span>
                </div>
              )}

              {/* Input */}
              <div className="p-3 border-t border-slate-800 flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendMessage()}
                  disabled={loading}
                  placeholder="বাংলা বা English-এ লিখুন..."
                  className="flex-1 bg-slate-800 border border-slate-700 focus:border-accentPurple rounded-lg px-3 py-2 text-xs text-slate-200 placeholder:text-slate-500 outline-none transition"
                />
                <button
                  onClick={() => sendMessage()}
                  disabled={loading || !input.trim()}
                  className="bg-accentPurple hover:bg-accentPurple/80 disabled:opacity-40 text-white p-2 rounded-lg transition"
                >
                  <Send size={14} />
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Bubble toggle */}
      <button
        onClick={open ? handleClose : handleOpen}
        className="w-14 h-14 bg-gradient-to-tr from-accentPurple to-accentPink rounded-full shadow-xl shadow-accentPurple/40 flex items-center justify-center text-white transition-all duration-200 hover:scale-110 active:scale-95 relative"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
        {hasUnread && !open && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 border-2 border-darkBg rounded-full text-[9px] font-bold flex items-center justify-center">
            1
          </span>
        )}
      </button>
    </div>
  )
}

export default ChatWidget
