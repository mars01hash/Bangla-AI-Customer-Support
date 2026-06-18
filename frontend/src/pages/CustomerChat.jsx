import React, { useState, useEffect, useRef } from 'react'
import { Send, Volume2, Mic, CheckCircle, ShieldAlert, Sparkles, BookOpen, ThumbsUp, ThumbsDown } from 'lucide-react'

function CustomerChat() {
  const [sessionId] = useState(() => 'session-' + Math.random().toString(36).substr(2, 9))
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      content: 'হ্যালো! আমি আপনার কাস্টমার সাপোর্ট সহকারী। আজ আপনাকে কীভাবে সাহায্য করতে পারি? (Hello! How can I help you today?)',
      timestamp: new Date().toISOString(),
      confidence_score: 1.0,
      sources: []
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [recording, setRecording] = useState(false)
  
  // Real-time memory variables
  const [language, setLanguage] = useState('bn')
  const [sentiment, setSentiment] = useState('neutral')
  const [escalatedTicket, setEscalatedTicket] = useState(null)
  
  // Feedback tracker
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const [currentSpeechUrl, setCurrentSpeechUrl] = useState(null)

  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputValue.trim()
    if (!text) return

    setInputValue('')
    setError('')
    setLoading(true)

    // Append User message locally
    const userMsg = {
      sender: 'user',
      content: text,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMsg])
    setFeedbackSubmitted(false)

    try {
      const formData = new FormData()
      formData.append('message_in', text)
      formData.append('session_id', sessionId)

      const response = await fetch('http://localhost:8090/api/chat', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) throw new Error('Failed to reach AI Backend.')

      const data = await response.json()
      
      // Update memory panels
      setLanguage(data.language)
      setSentiment(data.sentiment)
      if (data.ticket_escalated && data.ticket_id) {
        setEscalatedTicket({
          id: data.ticket_id,
          category: data.category || 'Customer Inquiries',
          priority: data.sentiment === 'negative' ? 'Urgent' : 'Medium',
          status: 'Open'
        })
      }

      // Append Bot message
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          content: data.answer,
          timestamp: new Date().toISOString(),
          confidence_score: data.confidence_score,
          sources: data.sources || []
        }
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          content: 'দুঃখিত, ব্যাকএন্ডের সাথে সংযোগ স্থাপন করা যাচ্ছে না। অনুগ্রহ করে নিশ্চিত করুন যে FastAPI সার্ভারটি চালু আছে।',
          timestamp: new Date().toISOString(),
          confidence_score: 0.0,
          sources: []
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  // Text to Speech caller
  const handleTTS = async (text, lang) => {
    try {
      const formData = new FormData()
      formData.append('text', text)
      formData.append('lang', lang)

      const response = await fetch('http://localhost:8090/api/voice/tts', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || 'mock-token'}`
        },
        body: formData
      })

      if (!response.ok) return
      
      const blob = await response.blob()
      const audioUrl = URL.createObjectURL(blob)
      if (currentSpeechUrl) URL.revokeObjectURL(currentSpeechUrl)
      setCurrentSpeechUrl(audioUrl)
      
      const audio = new Audio(audioUrl)
      audio.play()
    } catch (err) {
      console.error("Audio generation failed: ", err)
    }
  }

  // Simulated Voice transcription STT
  const handleSTT = async () => {
    setRecording(true)
    setTimeout(async () => {
      setRecording(false)
      try {
        const fileData = new FormData()
        // Provide dummy wave header shell
        const blob = new Blob([new Uint8Array(100)], { type: 'audio/wav' })
        fileData.append('file', blob, 'recording.wav')

        const response = await fetch('http://localhost:8090/api/voice/stt', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || 'mock-token'}`
          },
          body: fileData
        })

        if (response.ok) {
          const data = await response.json()
          setInputValue(data.transcription)
        }
      } catch (err) {
        console.error("Audio STT translation failed: ", err)
      }
    }, 2000)
  }

  const handleFeedback = async (rating) => {
    try {
      await fetch('http://localhost:8090/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          rating: rating,
          comment: "Customer rating"
        })
      })
      setFeedbackSubmitted(true)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="flex-1 flex overflow-hidden max-h-[calc(100vh-73px)]">
      {/* 1. Sidebar Panel (Memory and Profile Diagnostics) */}
      <aside className="w-80 border-r border-slate-800 bg-slate-900/40 p-6 flex flex-col gap-6 shrink-0 hidden md:flex">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
            Real-Time Platform Context
          </h3>
          <div className="space-y-3">
            <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-3">
              <p className="text-[10px] text-slate-500 font-mono">SESSION ID</p>
              <p className="text-sm font-semibold text-slate-300 font-mono mt-0.5">{sessionId}</p>
            </div>
            <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-3 flex justify-between items-center">
              <div>
                <p className="text-[10px] text-slate-500 font-mono">LANGUAGE DETECTED</p>
                <p className="text-sm font-semibold text-slate-300 capitalize mt-0.5">{language}</p>
              </div>
              <span className="w-2.5 h-2.5 rounded-full bg-accentPurple shadow-lg shadow-accentPurple/50" />
            </div>
            <div className="bg-slate-950/40 border border-slate-800 rounded-xl p-3 flex justify-between items-center">
              <div>
                <p className="text-[10px] text-slate-500 font-mono">CUSTOMER SENTIMENT</p>
                <p className="text-sm font-semibold text-slate-300 capitalize mt-0.5">{sentiment}</p>
              </div>
              <span className={`w-2.5 h-2.5 rounded-full ${
                sentiment === 'positive' ? 'bg-emerald-400' : sentiment === 'negative' ? 'bg-rose-500' : 'bg-amber-400'
              }`} />
            </div>
          </div>
        </div>

        {escalatedTicket && (
          <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-5 flex flex-col gap-3">
            <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
              <ShieldAlert size={18} />
              <h4>Ticket Escalated</h4>
            </div>
            <p className="text-xs text-rose-300/80">
              The agent has automatically registered an issue ticket to human support due to query complexity or sentiment score.
            </p>
            <div className="space-y-1 bg-slate-950/30 p-3 rounded-lg text-xs font-mono">
              <p><span className="text-slate-500">ID:</span> {escalatedTicket.id}</p>
              <p><span className="text-slate-500">TYPE:</span> {escalatedTicket.category}</p>
              <p><span className="text-slate-500">PRIORITY:</span> {escalatedTicket.priority}</p>
              <p><span className="text-slate-500">STATUS:</span> {escalatedTicket.status}</p>
            </div>
          </div>
        )}

        <div className="mt-auto bg-gradient-to-br from-accentPurple/10 to-transparent border border-accentPurple/10 rounded-2xl p-5 text-xs text-slate-400 leading-relaxed">
          <Sparkles className="text-accentPurple mb-2 animate-bounce" size={16} />
          Try asking: <br />
          <span className="italic text-slate-300">"আমার অর্ডার কোথায়?"</span> or <br />
          <span className="italic text-slate-300">"পেমেন্ট পলিসি নিয়ে অভিযোগ আছে।"</span>
        </div>
      </aside>

      {/* 2. Main Chat Thread Viewport */}
      <section className="flex-1 flex flex-col bg-slate-950/20 relative">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-3 max-w-[80%] ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
            >
              {msg.sender === 'bot' && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-accentPurple to-accentPink flex items-center justify-center text-xs font-bold shadow-md shrink-0">
                  AI
                </div>
              )}

              <div className="space-y-2">
                <div className={`p-4 rounded-2xl text-sm leading-relaxed border ${
                  msg.sender === 'user'
                    ? 'bg-accentPurple border-accentPurple/20 text-white rounded-tr-none'
                    : 'bg-slate-900/90 border-slate-800 text-slate-100 rounded-tl-none'
                }`}>
                  <p>{msg.content}</p>
                </div>

                {msg.sender === 'bot' && (
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 pl-1">
                    {msg.confidence_score !== undefined && (
                      <span className={`px-2 py-0.5 rounded border ${
                        msg.confidence_score >= 0.7 
                          ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                          : msg.confidence_score >= 0.4
                          ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                          : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                      }`}>
                        Confidence: {Math.round(msg.confidence_score * 100)}%
                      </span>
                    )}

                    <button
                      onClick={() => handleTTS(msg.content, language)}
                      className="hover:text-white flex items-center gap-1 transition"
                      title="Listen to translation"
                    >
                      <Volume2 size={14} />
                      Speak
                    </button>

                    {msg.sources && msg.sources.length > 0 && (
                      <div className="flex items-center gap-1 select-none">
                        <BookOpen size={14} />
                        <span>Citations:</span>
                        {msg.sources.map((s, sIdx) => (
                          <span 
                            key={sIdx}
                            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 px-1.5 py-0.5 rounded text-[10px] cursor-pointer text-slate-300 font-mono transition"
                            title={s.snippet}
                          >
                            {s.source}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 max-w-[80%] mr-auto items-center">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-accentPurple to-accentPink flex items-center justify-center text-xs font-bold shadow-md shrink-0">
                AI
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl rounded-tl-none flex gap-1 items-center shrink-0">
                <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 3. Feedback and Input Section */}
        <div className="p-6 border-t border-slate-800 bg-slate-900/20 backdrop-blur-md flex flex-col gap-4">
          {/* Post-turn evaluation widget */}
          {messages.length > 2 && messages[messages.length - 1].sender === 'bot' && (
            <div className="flex items-center justify-between text-xs border border-slate-800/60 bg-slate-900/40 rounded-xl px-4 py-3 self-center max-w-lg w-full transition-all duration-300">
              {feedbackSubmitted ? (
                <div className="flex items-center gap-2 text-emerald-400 font-semibold mx-auto">
                  <CheckCircle size={14} />
                  <span>আপনার রেটিং দেওয়ার জন্য ধন্যবাদ! (Thanks for rating!)</span>
                </div>
              ) : (
                <>
                  <span className="text-slate-400">এই উত্তরটি কি সাহায্য করেছে? (Was this helpful?)</span>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleFeedback(5)}
                      className="hover:text-emerald-400 text-slate-400 p-1 flex items-center gap-1 transition"
                    >
                      <ThumbsUp size={14} /> Yes
                    </button>
                    <button
                      onClick={() => handleFeedback(1)}
                      className="hover:text-rose-400 text-slate-400 p-1 flex items-center gap-1 transition"
                    >
                      <ThumbsDown size={14} /> No
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={handleSTT}
              className={`p-4 rounded-xl border flex items-center justify-center transition-all duration-300 ${
                recording
                  ? 'bg-rose-500/20 border-rose-500 text-rose-500 record-pulse'
                  : 'bg-slate-900 border-slate-700/60 hover:bg-slate-800 text-slate-400 hover:text-white'
              }`}
              title="Speak in Bangla/English"
            >
              <Mic size={20} />
            </button>

            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="বাংলা বা ইংরেজিতে আপনার প্রশ্নটি লিখুন... (Write your question here...)"
              className="flex-1 bg-slate-900/80 border border-slate-700/60 focus:border-accentPurple rounded-xl px-5 outline-none text-slate-200 text-sm placeholder:text-slate-500 transition-all duration-300"
            />

            <button
              onClick={() => handleSendMessage()}
              className="bg-accentPurple hover:bg-accentPurple/90 text-white p-4 rounded-xl shadow-lg shadow-accentPurple/10 flex items-center justify-center transition-all duration-300"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

export default CustomerChat
