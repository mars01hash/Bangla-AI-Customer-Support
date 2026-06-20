import React, { useState } from 'react'
import {
  ShoppingCart, Star, Search, Heart, Truck, Shield, RefreshCw, X, Plus, Minus, Trash2,
  ArrowLeft, CheckCircle, Package, Clock, MapPin, CreditCard,
  ChevronRight, MessageCircle, RotateCcw, ChevronDown, ListOrdered, Loader2,
} from 'lucide-react'
import ChatWidget from '../components/ChatWidget.jsx'

const API = 'http://localhost:8090'
const ORDERS_KEY = 'shopbd_orders'

// ── Data ──────────────────────────────────────────────────────────────────────
const PRODUCTS = [
  { id: 1,  name: 'পাঞ্জাবি',            nameEn: 'Cotton Panjabi',    price: 850,  original: 1200, emoji: '👘', cat: 'পোশাক',        rating: 4.5, reviews: 128, badge: '29% OFF', bt: 'sale' },
  { id: 2,  name: 'জামদানি শাড়ি',        nameEn: 'Jamdani Saree',     price: 2500, original: 3200, emoji: '🥻', cat: 'পোশাক',        rating: 4.8, reviews: 245, badge: 'BESTSELLER', bt: 'best' },
  { id: 3,  name: 'ওয়্যারলেস ইয়ারবাড',  nameEn: 'Wireless Earbuds',  price: 1200, original: 1800, emoji: '🎧', cat: 'ইলেকট্রনিক্স', rating: 4.3, reviews: 89,  badge: 'NEW', bt: 'new' },
  { id: 4,  name: 'স্মার্ট ওয়াচ',        nameEn: 'Smart Watch',       price: 3500, original: 4500, emoji: '⌚', cat: 'ইলেকট্রনিক্স', rating: 4.6, reviews: 312, badge: '22% OFF', bt: 'sale' },
  { id: 5,  name: 'লেদার হ্যান্ডব্যাগ',  nameEn: 'Leather Handbag',   price: 1800, original: 2200, emoji: '👜', cat: 'আনুষাঙ্গিক',  rating: 4.4, reviews: 176, badge: 'TOP RATED', bt: 'best' },
  { id: 6,  name: 'সানগ্লাস',             nameEn: 'UV Sunglasses',     price: 650,  original: 950,  emoji: '🕶️', cat: 'আনুষাঙ্গিক',  rating: 4.1, reviews: 64,  badge: '', bt: '' },
  { id: 7,  name: 'রানিং শু',              nameEn: 'Running Shoes',     price: 2200, original: 2800, emoji: '👟', cat: 'জুতা',         rating: 4.7, reviews: 403, badge: 'HOT', bt: 'best' },
  { id: 8,  name: 'মোবাইল কেস',           nameEn: 'Phone Case',        price: 350,  original: 500,  emoji: '📱', cat: 'আনুষাঙ্গিক',  rating: 4.0, reviews: 52,  badge: '', bt: '' },
  { id: 9,  name: 'সিল্ক শাড়ি',           nameEn: 'Silk Saree',        price: 3200, original: 4000, emoji: '👗', cat: 'পোশাক',        rating: 4.6, reviews: 189, badge: '20% OFF', bt: 'sale' },
  { id: 10, name: 'ব্লুটুথ স্পিকার',      nameEn: 'Bluetooth Speaker', price: 980,  original: 1400, emoji: '🔊', cat: 'ইলেকট্রনিক্স', rating: 4.2, reviews: 73,  badge: 'NEW', bt: 'new' },
  { id: 11, name: 'শোল্ডার ব্যাগ',        nameEn: 'Shoulder Bag',      price: 1250, original: 1800, emoji: '👛', cat: 'আনুষাঙ্গিক',  rating: 4.3, reviews: 94,  badge: '', bt: '' },
  { id: 12, name: 'ক্যাজুয়াল স্নিকার্স', nameEn: 'Casual Sneakers',   price: 1650, original: 2100, emoji: '👞', cat: 'জুতা',         rating: 4.4, reviews: 156, badge: '21% OFF', bt: 'sale' },
]

const CATEGORIES = ['সব', 'পোশাক', 'ইলেকট্রনিক্স', 'আনুষাঙ্গিক', 'জুতা']
const DIVISIONS  = ['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi', 'Khulna', 'Barishal', 'Rangpur', 'Mymensingh']

const DELIVERY_OPTS = [
  { id: 'standard', label: 'স্ট্যান্ডার্ড', desc: '৩-৫ কার্যদিবস', cost: 60,  freeOver: 1000 },
  { id: 'express',  label: 'এক্সপ্রেস',     desc: '১-২ কার্যদিবস', cost: 120, freeOver: 2000 },
]

const PAYMENTS = [
  { id: 'bkash', label: 'bKash',                 emoji: '💳', color: 'text-pink-400',    bg: 'bg-pink-400/10 border-pink-400/40' },
  { id: 'nagad', label: 'Nagad',                 emoji: '🟠', color: 'text-orange-400',  bg: 'bg-orange-400/10 border-orange-400/40' },
  { id: 'card',  label: 'ডেবিট / ক্রেডিট কার্ড', emoji: '💳', color: 'text-blue-400',    bg: 'bg-blue-400/10 border-blue-400/40' },
  { id: 'cod',   label: 'ক্যাশ অন ডেলিভারি',    emoji: '💵', color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/40' },
]

const STATUS_INFO = {
  processing:       { bn: 'প্রক্রিয়াধীন',     emoji: '🔄', cls: 'text-amber-400 bg-amber-400/10 border-amber-400/30' },
  shipped:          { bn: 'শিপড',              emoji: '🚚', cls: 'text-blue-400 bg-blue-400/10 border-blue-400/30' },
  out_for_delivery: { bn: 'ডেলিভারিতে আছে',   emoji: '🏃', cls: 'text-purple-400 bg-purple-400/10 border-purple-400/30' },
  delivered:        { bn: 'ডেলিভারি সম্পন্ন', emoji: '✅', cls: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30' },
  cancelled:        { bn: 'বাতিল',            emoji: '❌', cls: 'text-rose-400 bg-rose-400/10 border-rose-400/30' },
}

// ── Pure helpers ───────────────────────────────────────────────────────────────
function calcDelivCost(subtotal, delivId) {
  const opt = DELIVERY_OPTS.find(d => d.id === delivId)
  return subtotal >= (opt?.freeOver ?? 1000) ? 0 : (opt?.cost ?? 60)
}

function estDelivery(delivId) {
  const days = delivId === 'express' ? 2 : 5
  const d = new Date(); d.setDate(d.getDate() + days)
  return d.toLocaleDateString('bn-BD', { day: 'numeric', month: 'long', year: 'numeric' })
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('bn-BD', { day: 'numeric', month: 'long', year: 'numeric' })
}

// ── Shared micro-components (defined outside any component) ───────────────────
function Stars({ rating }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1,2,3,4,5].map(s => (
        <Star key={s} size={11} className={s <= Math.round(rating) ? 'text-amber-400 fill-amber-400' : 'text-slate-600'} />
      ))}
    </div>
  )
}

function ProductBadge({ text, type }) {
  if (!text) return null
  const cls = type === 'sale' ? 'bg-rose-500 text-white' : type === 'new' ? 'bg-emerald-500 text-white' : 'bg-amber-500 text-black'
  return <span className={`absolute top-2 left-2 text-[10px] font-bold px-2 py-0.5 rounded-full ${cls}`}>{text}</span>
}

function FormField({ label, error, children }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-300 mb-1">{label}</label>
      {children}
      {error && <p className="text-[10px] text-rose-400 mt-1">{error}</p>}
    </div>
  )
}

const inputBase = 'w-full bg-slate-800 border focus:border-accentPurple rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none transition'
function inputCls(hasErr) { return `${inputBase} ${hasErr ? 'border-rose-500' : 'border-slate-700'}` }

// ── OrderSummaryPanel — used by both CheckoutView and PaymentView ─────────────
function OrderSummaryPanel({ cart, subtotal, delivCost, total, delivLabel }) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
      <h4 className="font-bold text-white text-sm border-b border-slate-800 pb-3">অর্ডার সারসংক্ষেপ</h4>
      <div className="space-y-2 max-h-52 overflow-y-auto">
        {cart.map(i => (
          <div key={i.id} className="flex items-center gap-2 text-sm">
            <span className="text-lg">{i.emoji}</span>
            <span className="flex-1 text-slate-300 text-xs">{i.name} ×{i.qty}</span>
            <span className="text-white font-semibold text-xs">৳{(i.price * i.qty).toLocaleString()}</span>
          </div>
        ))}
      </div>
      <div className="border-t border-slate-800 pt-3 space-y-1">
        <div className="flex justify-between text-xs text-slate-400">
          <span>সাবটোটাল</span><span>৳{subtotal.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-xs text-slate-400">
          <span>ডেলিভারি ({delivLabel})</span>
          <span className={delivCost === 0 ? 'text-emerald-400' : ''}>{delivCost === 0 ? 'ফ্রি' : `৳${delivCost}`}</span>
        </div>
        <div className="flex justify-between font-bold text-white pt-2 border-t border-slate-800 text-sm">
          <span>মোট</span><span>৳{total.toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// CheckoutView — own local state so EcommercePage doesn't re-render on typing
// ══════════════════════════════════════════════════════════════════════════════
function CheckoutView({ cart, onBack, onProceed }) {
  const [form, setForm] = useState({
    name: '', email: '', phone: '', division: 'Dhaka', district: '', address: '',
    delivery: 'standard', payment: 'bkash',
  })
  const [err, setErr] = useState({})

  const subtotal  = cart.reduce((s, i) => s + i.price * i.qty, 0)
  const delivCost = calcDelivCost(subtotal, form.delivery)
  const total     = subtotal + delivCost
  const delivOpt  = DELIVERY_OPTS.find(d => d.id === form.delivery)

  const set = (key) => (e) => setForm(f => ({ ...f, [key]: e.target.value }))

  const proceed = () => {
    const e = {}
    if (!form.name.trim())                    e.name = 'নাম দিন'
    if (!form.phone.match(/^01[3-9]\d{8}$/)) e.phone = '১১ সংখ্যার মোবাইল নম্বর দিন'
    if (!form.address.trim())                 e.address = 'ঠিকানা দিন'
    setErr(e)
    if (Object.keys(e).length === 0) onProceed(form, subtotal, delivCost, total)
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <button onClick={onBack} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-6 transition">
        <ArrowLeft size={16} /> ফিরে যান
      </button>
      <h2 className="text-2xl font-bold text-white mb-8">চেকআউট</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">

          {/* Contact */}
          <div className="glass-panel rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-white flex items-center gap-2"><MapPin size={16} className="text-accentPurple" /> যোগাযোগের তথ্য</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="পূর্ণ নাম *" error={err.name}>
                <input className={inputCls(err.name)} placeholder="আপনার নাম" value={form.name} onChange={set('name')} />
              </FormField>
              <FormField label="মোবাইল নম্বর *" error={err.phone}>
                <input className={inputCls(err.phone)} placeholder="01XXXXXXXXX" value={form.phone} onChange={set('phone')} />
              </FormField>
              <FormField label="ইমেইল (ঐচ্ছিক)" error={null}>
                <input className={inputCls(false)} placeholder="receipt@example.com" type="email" value={form.email} onChange={set('email')} />
              </FormField>
            </div>
          </div>

          {/* Address */}
          <div className="glass-panel rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-white flex items-center gap-2"><Truck size={16} className="text-accentPurple" /> ডেলিভারি ঠিকানা</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField label="বিভাগ" error={null}>
                <div className="relative">
                  <select className={inputCls(false) + ' appearance-none pr-8'} value={form.division} onChange={set('division')}>
                    {DIVISIONS.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
                </div>
              </FormField>
              <FormField label="জেলা" error={null}>
                <input className={inputCls(false)} placeholder="জেলার নাম" value={form.district} onChange={set('district')} />
              </FormField>
            </div>
            <FormField label="বিস্তারিত ঠিকানা *" error={err.address}>
              <textarea rows={2} className={inputCls(err.address) + ' resize-none'} placeholder="রাস্তা, বাড়ি/ফ্ল্যাট নম্বর, এলাকা"
                value={form.address} onChange={set('address')} />
            </FormField>
          </div>

          {/* Delivery */}
          <div className="glass-panel rounded-2xl p-6 space-y-3">
            <h3 className="font-bold text-white flex items-center gap-2"><Clock size={16} className="text-accentPurple" /> ডেলিভারি পদ্ধতি</h3>
            {DELIVERY_OPTS.map(d => (
              <label key={d.id} className={`flex items-center gap-4 p-3 rounded-xl border cursor-pointer transition ${
                form.delivery === d.id ? 'border-accentPurple bg-accentPurple/10' : 'border-slate-700 hover:border-slate-600'
              }`}>
                <input type="radio" className="accent-accentPurple" name="delivery" value={d.id}
                  checked={form.delivery === d.id} onChange={() => setForm(f => ({ ...f, delivery: d.id }))} />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-white">{d.label} — {d.desc}</p>
                  <p className="text-xs text-slate-400">
                    {subtotal >= d.freeOver ? 'ফ্রি ডেলিভারি ✓' : `৳${d.cost}`}
                    {subtotal < d.freeOver && <span className="ml-2 text-slate-500">(৳{d.freeOver} এর উপরে ফ্রি)</span>}
                  </p>
                </div>
              </label>
            ))}
          </div>

          {/* Payment method selection */}
          <div className="glass-panel rounded-2xl p-6 space-y-3">
            <h3 className="font-bold text-white flex items-center gap-2"><CreditCard size={16} className="text-accentPurple" /> পেমেন্ট পদ্ধতি</h3>
            <div className="grid grid-cols-2 gap-3">
              {PAYMENTS.map(pm => (
                <label key={pm.id} className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition ${
                  form.payment === pm.id ? `${pm.bg} ${pm.color}` : 'border-slate-700 hover:border-slate-600 text-slate-300'
                }`}>
                  <input type="radio" className="accent-current" name="payment" value={pm.id}
                    checked={form.payment === pm.id} onChange={() => setForm(f => ({ ...f, payment: pm.id }))} />
                  <span className="text-lg">{pm.emoji}</span>
                  <span className="text-sm font-semibold">{pm.label}</span>
                </label>
              ))}
            </div>
          </div>

          <button onClick={proceed}
            className="w-full bg-accentPurple hover:bg-accentPurple/90 text-white py-3.5 rounded-xl font-bold text-sm transition flex items-center justify-center gap-2">
            পেমেন্টে যান <ChevronRight size={18} />
          </button>
        </div>

        <div className="lg:col-span-1">
          <div className="sticky top-36">
            <OrderSummaryPanel cart={cart} subtotal={subtotal} delivCost={delivCost} total={total} delivLabel={delivOpt?.label ?? ''} />
          </div>
        </div>
      </div>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// PaymentView — own local state so EcommercePage doesn't re-render on typing
// ══════════════════════════════════════════════════════════════════════════════
function PaymentView({ form, cart, subtotal, delivCost, total, onBack, onSuccess }) {
  const [stage, setStage] = useState('form') // form | otp | processing
  const [payIn, setPayIn] = useState({ number: '', otp: '', card: '', expiry: '', cvv: '' })
  const [payErr, setPayErr] = useState('')

  const pm = PAYMENTS.find(p => p.id === form.payment)
  const delivOpt = DELIVERY_OPTS.find(d => d.id === form.delivery)

  const setPI = (key) => (e) => setPayIn(p => ({ ...p, [key]: e.target.value }))

  const doPlaceOrder = async () => {
    setStage('processing')
    const estDel = estDelivery(form.delivery)
    const payload = {
      customer_name:  form.name,
      customer_email: form.email.trim() || 'guest@shopbd.com',
      items:          cart.map(i => `${i.name} x${i.qty} (৳${i.price})`),
      total_amount:   total,
      estimated_delivery: estDel,
    }

    let orderId
    try {
      const res  = await fetch(`${API}/api/orders/place`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      })
      const data = await res.json()
      orderId = data.order_id
    } catch {
      orderId = 'ORD-' + Math.random().toString(36).substr(2, 5).toUpperCase()
    }

    const record = {
      order_id:        orderId,
      customer_name:   form.name,
      phone:           form.phone,
      address:         [form.address, form.district, form.division].filter(Boolean).join(', '),
      payment_method:  form.payment,
      delivery_method: form.delivery,
      items:           cart.map(i => ({ ...i })),
      subtotal, delivery_cost: delivCost, total,
      estimated_delivery: estDel,
      placed_at: new Date().toISOString(),
      status: 'processing',
    }
    onSuccess(record)
  }

  const handlePay = async () => {
    setPayErr('')
    const { payment } = form

    if (payment === 'bkash' || payment === 'nagad') {
      if (stage === 'form') {
        if (!payIn.number.match(/^01\d{9}$/)) { setPayErr('সঠিক ১১ সংখ্যার মোবাইল নম্বর দিন'); return }
        setStage('otp')
      } else if (stage === 'otp') {
        if (payIn.otp.length < 4) { setPayErr('OTP দিন'); return }
        await doPlaceOrder()
      }
    } else if (payment === 'card') {
      const cn = payIn.card.replace(/\s/g, '')
      if (!cn.match(/^\d{16}$/))                 { setPayErr('১৬ সংখ্যার কার্ড নম্বর দিন'); return }
      if (!payIn.expiry.match(/^\d{2}\/\d{2}$/)) { setPayErr('MM/YY ফর্ম্যাটে তারিখ দিন'); return }
      if (!payIn.cvv.match(/^\d{3,4}$/))          { setPayErr('CVV দিন'); return }
      await doPlaceOrder()
    } else {
      await doPlaceOrder()
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <button onClick={onBack} disabled={stage === 'processing'}
        className="flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-6 transition disabled:opacity-40">
        <ArrowLeft size={16} /> ফিরে যান
      </button>
      <h2 className="text-2xl font-bold text-white mb-8">পেমেন্ট</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-5">
          {/* Payment method badge */}
          <div className={`rounded-2xl border p-4 ${pm?.bg}`}>
            <p className={`text-base font-bold flex items-center gap-2 ${pm?.color}`}>
              <span className="text-2xl">{pm?.emoji}</span>{pm?.label}
            </p>
            <p className="text-xs text-slate-400 mt-1">মোট: <span className="text-white font-bold">৳{total.toLocaleString()}</span></p>
          </div>

          {stage === 'processing' ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <Loader2 size={44} className="text-accentPurple animate-spin" />
              <p className="text-slate-300 font-semibold">পেমেন্ট প্রক্রিয়া হচ্ছে...</p>
              <p className="text-slate-500 text-xs">দয়া করে অপেক্ষা করুন</p>
            </div>
          ) : (
            <div className="glass-panel rounded-2xl p-6 space-y-5">
              {/* bKash / Nagad */}
              {(form.payment === 'bkash' || form.payment === 'nagad') && (
                stage === 'form' ? (
                  <FormField label={`${pm?.label} নম্বর *`} error={null}>
                    <input className={inputCls(!!payErr)} placeholder="01XXXXXXXXX" maxLength={11}
                      value={payIn.number} onChange={setPI('number')} />
                  </FormField>
                ) : (
                  <div className="space-y-3">
                    <p className="text-sm text-slate-300">
                      <span className="font-semibold text-white">{payIn.number}</span> নম্বরে OTP পাঠানো হয়েছে।
                    </p>
                    <FormField label="OTP / PIN *" error={null}>
                      <input className={inputCls(!!payErr)} placeholder="6-সংখ্যার OTP" maxLength={6}
                        value={payIn.otp} onChange={setPI('otp')} />
                    </FormField>
                    <p className="text-[10px] text-slate-500">এটি ডেমো — যেকোনো সংখ্যা দিন।</p>
                  </div>
                )
              )}

              {/* Card */}
              {form.payment === 'card' && (
                <div className="space-y-4">
                  <FormField label="কার্ড নম্বর *" error={null}>
                    <input className={inputCls(!!payErr)} placeholder="1234 5678 9012 3456" maxLength={19}
                      value={payIn.card}
                      onChange={e => {
                        const v = e.target.value.replace(/\D/g,'').slice(0,16)
                        setPayIn(p => ({ ...p, card: v.replace(/(.{4})/g,'$1 ').trim() }))
                      }} />
                  </FormField>
                  <div className="grid grid-cols-2 gap-4">
                    <FormField label="মেয়াদ (MM/YY) *" error={null}>
                      <input className={inputCls(!!payErr)} placeholder="MM/YY" maxLength={5}
                        value={payIn.expiry}
                        onChange={e => {
                          let v = e.target.value.replace(/\D/g,'').slice(0,4)
                          if (v.length >= 3) v = v.slice(0,2) + '/' + v.slice(2)
                          setPayIn(p => ({ ...p, expiry: v }))
                        }} />
                    </FormField>
                    <FormField label="CVV *" error={null}>
                      <input className={inputCls(!!payErr)} placeholder="•••" maxLength={4} type="password"
                        value={payIn.cvv}
                        onChange={e => setPayIn(p => ({ ...p, cvv: e.target.value.replace(/\D/g,'').slice(0,4) }))} />
                    </FormField>
                  </div>
                  <p className="text-[10px] text-slate-500">ডেমো — আসল কার্ড তথ্য ব্যবহার করবেন না।</p>
                </div>
              )}

              {/* COD */}
              {form.payment === 'cod' && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-4 text-sm text-emerald-300">
                  <p className="font-semibold mb-1">ক্যাশ অন ডেলিভারি</p>
                  <p className="text-xs text-slate-400">পণ্য পাওয়ার সময় ৳{total.toLocaleString()} পরিশোধ করুন।</p>
                </div>
              )}

              {payErr && <p className="text-rose-400 text-xs">{payErr}</p>}

              <button onClick={handlePay}
                className="w-full bg-accentPurple hover:bg-accentPurple/90 text-white py-3.5 rounded-xl font-bold text-sm transition flex items-center justify-center gap-2">
                {form.payment === 'cod'    ? 'অর্ডার নিশ্চিত করুন' :
                 form.payment === 'card'   ? `৳${total.toLocaleString()} পরিশোধ করুন` :
                 stage === 'otp'           ? 'OTP যাচাই করুন' : 'পেমেন্ট করুন'}
                <ChevronRight size={18} />
              </button>
            </div>
          )}
        </div>

        <div className="lg:col-span-1">
          <div className="sticky top-36">
            <OrderSummaryPanel cart={cart} subtotal={subtotal} delivCost={delivCost} total={total} delivLabel={delivOpt?.label ?? ''} />
            <p className="text-center text-[10px] text-slate-500 mt-3 flex items-center justify-center gap-1">
              <Shield size={11} /> ১০০% নিরাপদ পেমেন্ট
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════════
// EcommercePage — main shell, only manages navigation + cart + orders
// ══════════════════════════════════════════════════════════════════════════════
export default function EcommercePage() {
  const [view, setView]   = useState('browse') // browse | checkout | payment | success | orders
  const [cart, setCart]   = useState([])
  const [wish, setWish]   = useState([])
  const [search, setSearch] = useState('')
  const [cat, setCat]     = useState('সব')
  const [cartOpen, setCartOpen] = useState(false)
  const [addedId, setAddedId]   = useState(null)

  // Passed from CheckoutView → stored here → passed to PaymentView
  const [checkoutPayload, setCheckoutPayload] = useState(null) // { form, subtotal, delivCost, total }

  const [placed, setPlaced]       = useState(null)
  const [myOrders, setMyOrders]   = useState(() => {
    try { return JSON.parse(localStorage.getItem(ORDERS_KEY) || '[]') } catch { return [] }
  })
  const [liveStatus, setLiveStatus] = useState({})
  const [fetchingId, setFetchingId] = useState(null)
  const [chatPreset, setChatPreset] = useState('')

  // Cart derived values (used in cart drawer and store nav)
  const subtotalMain  = cart.reduce((s, i) => s + i.price * i.qty, 0)
  const cartCount     = cart.reduce((s, i) => s + i.qty, 0)

  const addToCart = (p) => {
    setCart(prev => {
      const ex = prev.find(i => i.id === p.id)
      return ex ? prev.map(i => i.id === p.id ? { ...i, qty: i.qty + 1 } : i) : [...prev, { ...p, qty: 1 }]
    })
    setAddedId(p.id)
    setTimeout(() => setAddedId(null), 1000)
  }
  const removeFromCart = (id) => setCart(prev => prev.filter(i => i.id !== id))
  const changeQty = (id, d) => setCart(prev => prev.map(i => i.id === id ? { ...i, qty: Math.max(1, i.qty + d) } : i))
  const toggleWish = (id) => setWish(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id])

  const handleCheckoutProceed = (form, subtotal, delivCost, total) => {
    setCheckoutPayload({ form, subtotal, delivCost, total })
    setView('payment')
  }

  const handlePaymentSuccess = (record) => {
    const updated = [record, ...myOrders]
    setMyOrders(updated)
    localStorage.setItem(ORDERS_KEY, JSON.stringify(updated))
    setPlaced(record)
    setCart([])
    setView('success')
  }

  const refreshStatus = async (order_id) => {
    setFetchingId(order_id)
    try {
      const res = await fetch(`${API}/api/orders/track/${order_id}`)
      if (res.ok) {
        const data = await res.json()
        setLiveStatus(prev => ({ ...prev, [order_id]: data.status }))
        setMyOrders(prev => {
          const updated = prev.map(o => o.order_id === order_id ? { ...o, status: data.status } : o)
          localStorage.setItem(ORDERS_KEY, JSON.stringify(updated))
          return updated
        })
      }
    } catch {}
    setFetchingId(null)
  }

  const trackInChat = (order_id) => {
    setChatPreset(`আমার অর্ডার ${order_id} কোথায়? ট্র্যাক করতে চাই।`)
    setCartOpen(false)
  }

  // ── Product filtering (only re-runs when search/cat change) ────────────────
  const filtered = PRODUCTS.filter(p => {
    const okCat    = cat === 'সব' || p.cat === cat
    const okSearch = !search || p.name.includes(search) || p.nameEn.toLowerCase().includes(search.toLowerCase())
    return okCat && okSearch
  })

  return (
    <div className="min-h-screen bg-darkBg">

      {/* Store sticky nav */}
      <header className="glass-panel sticky top-[73px] z-40 px-6 py-3 flex items-center gap-4">
        <button onClick={() => setView('browse')} className="flex items-center gap-2 shrink-0 hover:opacity-80 transition">
          <span className="text-xl">🛍️</span>
          <span className="font-bold text-base bg-gradient-to-r from-accentPurple to-accentPink bg-clip-text text-transparent">ShopBD</span>
        </button>

        {/* Breadcrumb */}
        <div className="text-xs text-slate-500 hidden sm:flex items-center gap-1">
          <button onClick={() => setView('browse')} className="hover:text-white transition">স্টোর</button>
          {view === 'checkout' && <><ChevronRight size={12}/><span className="text-slate-300">চেকআউট</span></>}
          {view === 'payment'  && <><ChevronRight size={12}/><span className="text-slate-500">চেকআউট</span><ChevronRight size={12}/><span className="text-slate-300">পেমেন্ট</span></>}
          {view === 'success'  && <><ChevronRight size={12}/><span className="text-emerald-400">সফল ✓</span></>}
          {view === 'orders'   && <><ChevronRight size={12}/><span className="text-slate-300">আমার অর্ডার</span></>}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button onClick={() => setView('orders')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              view === 'orders' ? 'bg-accentPurple/20 text-accentPurple border border-accentPurple/30' : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}>
            <Package size={14} /> আমার অর্ডার {myOrders.length > 0 && <span className="text-accentPurple">({myOrders.length})</span>}
          </button>
          <button onClick={() => setCartOpen(true)}
            className="relative flex items-center gap-1.5 bg-accentPurple/10 hover:bg-accentPurple/20 border border-accentPurple/30 text-accentPurple px-3 py-1.5 rounded-lg text-xs font-semibold transition">
            <ShoppingCart size={14} /> কার্ট
            {cartCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-accentPink rounded-full text-white text-[9px] font-bold flex items-center justify-center">{cartCount}</span>
            )}
          </button>
        </div>
      </header>

      {/* ── Browse ── */}
      {view === 'browse' && (
        <>
          <div className="px-6 py-4 border-b border-slate-800/60 flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-48 max-w-sm">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="পণ্য খুঁজুন... (Search)"
                className="w-full bg-slate-800 border border-slate-700 focus:border-accentPurple rounded-lg pl-9 pr-8 py-2 text-sm text-slate-200 placeholder:text-slate-500 outline-none transition"
              />
              {search && (
                <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                  <X size={13} />
                </button>
              )}
            </div>
            <div className="flex gap-1.5 flex-wrap">
              {CATEGORIES.map(c => (
                <button key={c} onClick={() => setCat(c)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition ${
                    cat === c ? 'bg-accentPurple text-white' : 'bg-slate-800 border border-slate-700 text-slate-400 hover:text-white'
                  }`}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div className="px-6 py-3 grid grid-cols-3 gap-2 border-b border-slate-800/40 text-xs text-slate-400">
            {[<><Truck size={12} className="text-accentPurple"/> ফ্রি ডেলিভারি ৳1000+</>,
              <><Shield size={12} className="text-accentPurple"/> ১০০% নিরাপদ</>,
              <><RefreshCw size={12} className="text-accentPurple"/> ৭ দিনে রিটার্ন</>
            ].map((f, i) => (
              <div key={i} className="flex items-center gap-1.5">{f}</div>
            ))}
          </div>

          <div className="px-6 py-6">
            <p className="text-sm text-slate-500 mb-5">
              {cat === 'সব' ? 'সব পণ্য' : cat} ({filtered.length}টি)
              {search && <span className="ml-2 text-accentPurple">"{search}"</span>}
            </p>
            {filtered.length === 0 ? (
              <div className="text-center py-20 text-slate-500">
                <p className="text-5xl mb-3">🔍</p><p>কোনো পণ্য পাওয়া যায়নি</p>
                <button onClick={() => { setSearch(''); setCat('সব') }} className="mt-4 text-xs text-accentPurple hover:underline">সব পণ্য দেখুন</button>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                {filtered.map(p => (
                  <div key={p.id} className="glass-panel rounded-2xl overflow-hidden group hover:border-accentPurple/30 transition-all duration-200">
                    <div className="relative bg-slate-800/50 h-36 flex items-center justify-center">
                      <span className="text-5xl group-hover:scale-110 transition-transform duration-300">{p.emoji}</span>
                      <ProductBadge text={p.badge} type={p.bt} />
                      <button onClick={() => toggleWish(p.id)}
                        className="absolute top-2 right-2 w-7 h-7 rounded-full bg-slate-900/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                        <Heart size={13} className={wish.includes(p.id) ? 'fill-rose-500 text-rose-500' : 'text-slate-400'} />
                      </button>
                    </div>
                    <div className="p-3">
                      <p className="text-[10px] text-slate-500 mb-0.5">{p.cat}</p>
                      <h4 className="font-semibold text-xs text-white leading-tight mb-0.5">{p.name}</h4>
                      <p className="text-[10px] text-slate-400 mb-1.5">{p.nameEn}</p>
                      <div className="flex items-center gap-1 mb-1.5">
                        <Stars rating={p.rating} />
                        <span className="text-[9px] text-slate-500">({p.reviews})</span>
                      </div>
                      <div className="flex items-center gap-1.5 mb-2.5">
                        <span className="text-sm font-bold text-white">৳{p.price.toLocaleString()}</span>
                        <span className="text-[10px] text-slate-500 line-through">৳{p.original.toLocaleString()}</span>
                      </div>
                      <button onClick={() => addToCart(p)}
                        className={`w-full py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200 ${
                          addedId === p.id
                            ? 'bg-emerald-500 text-white'
                            : 'bg-accentPurple/10 hover:bg-accentPurple text-accentPurple hover:text-white border border-accentPurple/30 hover:border-transparent'
                        }`}>
                        {addedId === p.id ? '✓ যোগ হয়েছে' : 'কার্টে যোগ করুন'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Checkout (proper component, own state) ── */}
      {view === 'checkout' && (
        <CheckoutView
          cart={cart}
          onBack={() => setView('browse')}
          onProceed={handleCheckoutProceed}
        />
      )}

      {/* ── Payment (proper component, own state) ── */}
      {view === 'payment' && checkoutPayload && (
        <PaymentView
          form={checkoutPayload.form}
          cart={cart}
          subtotal={checkoutPayload.subtotal}
          delivCost={checkoutPayload.delivCost}
          total={checkoutPayload.total}
          onBack={() => setView('checkout')}
          onSuccess={handlePaymentSuccess}
        />
      )}

      {/* ── Success ── */}
      {view === 'success' && placed && (
        <div className="max-w-2xl mx-auto px-6 py-12 text-center">
          <div className="w-20 h-20 rounded-full bg-emerald-500/20 border-2 border-emerald-500/40 flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={40} className="text-emerald-400" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">অর্ডার সম্পন্ন!</h2>
          <p className="text-slate-400 text-sm mb-8">আপনার অর্ডার সফলভাবে গৃহীত হয়েছে।</p>

          <div className="glass-panel rounded-2xl p-6 text-left mb-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-sm">অর্ডার আইডি</span>
              <span className="font-mono font-bold text-accentPurple text-lg">{placed.order_id}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-sm">পেমেন্ট</span>
              <span className="text-white text-sm">{PAYMENTS.find(p => p.id === placed.payment_method)?.label}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-sm">ঠিকানা</span>
              <span className="text-white text-sm text-right max-w-[60%]">{placed.address}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-sm">আনুমানিক ডেলিভারি</span>
              <span className="text-emerald-400 text-sm font-semibold">{placed.estimated_delivery}</span>
            </div>
            <div className="border-t border-slate-800 pt-4 space-y-1">
              {placed.items.map((item, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="text-lg">{item.emoji}</span>
                  <span className="text-slate-300 flex-1">{item.name}</span>
                  <span className="text-white">×{item.qty}</span>
                  <span className="text-white font-semibold">৳{(item.price * item.qty).toLocaleString()}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between font-bold text-lg border-t border-slate-800 pt-3">
              <span className="text-white">মোট পরিশোধ</span>
              <span className="text-white">৳{placed.total.toLocaleString()}</span>
            </div>
          </div>

          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl px-4 py-3 text-xs text-blue-300 mb-6 text-left flex gap-2">
            <Package size={16} className="shrink-0 mt-0.5" />
            <span>অর্ডার আইডি <span className="font-mono font-bold">{placed.order_id}</span> — চ্যাটে যেকোনো সময় ট্র্যাক করুন।</span>
          </div>

          <div className="flex gap-3 flex-col sm:flex-row">
            <button onClick={() => trackInChat(placed.order_id)}
              className="flex-1 bg-accentPurple hover:bg-accentPurple/90 text-white py-3 rounded-xl font-semibold text-sm transition flex items-center justify-center gap-2">
              <MessageCircle size={16} /> চ্যাটে ট্র্যাক করুন
            </button>
            <button onClick={() => setView('orders')}
              className="flex-1 border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white py-3 rounded-xl font-semibold text-sm transition flex items-center justify-center gap-2">
              <ListOrdered size={16} /> আমার অর্ডার
            </button>
            <button onClick={() => setView('browse')}
              className="flex-1 border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white py-3 rounded-xl font-semibold text-sm transition">
              কেনাকাটা চালিয়ে যান
            </button>
          </div>
        </div>
      )}

      {/* ── My Orders ── */}
      {view === 'orders' && (
        <div className="max-w-4xl mx-auto px-6 py-8">
          <button onClick={() => setView('browse')} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-6 transition">
            <ArrowLeft size={16} /> ফিরে যান
          </button>
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Package size={22} className="text-accentPurple" /> আমার অর্ডারসমূহ
          </h2>
          {myOrders.length === 0 ? (
            <div className="text-center py-24 text-slate-500">
              <p className="text-6xl mb-4">📦</p>
              <p className="text-lg font-semibold text-slate-400 mb-2">কোনো অর্ডার নেই</p>
              <button onClick={() => setView('browse')} className="mt-4 bg-accentPurple text-white px-6 py-2.5 rounded-xl font-semibold text-sm hover:bg-accentPurple/90 transition">
                এখনই কিনুন
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {myOrders.map(order => {
                const st = STATUS_INFO[liveStatus[order.order_id] || order.status || 'processing'] || STATUS_INFO.processing
                return (
                  <div key={order.order_id} className="glass-panel rounded-2xl p-5 space-y-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] text-slate-500 mb-0.5">অর্ডার আইডি</p>
                        <p className="font-mono font-bold text-accentPurple text-lg">{order.order_id}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-3 py-1 rounded-full border text-xs font-semibold ${st.cls}`}>
                          {st.emoji} {st.bn}
                        </span>
                        <button onClick={() => refreshStatus(order.order_id)} disabled={fetchingId === order.order_id}
                          className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 hover:border-accentPurple flex items-center justify-center text-slate-400 hover:text-accentPurple transition disabled:opacity-40"
                          title="স্ট্যাটাস রিফ্রেশ">
                          <RotateCcw size={12} className={fetchingId === order.order_id ? 'animate-spin' : ''} />
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div><p className="text-slate-500 mb-0.5">তারিখ</p><p className="text-slate-300">{formatDate(order.placed_at)}</p></div>
                      <div><p className="text-slate-500 mb-0.5">মোট</p><p className="text-white font-bold">৳{order.total.toLocaleString()}</p></div>
                      <div><p className="text-slate-500 mb-0.5">পেমেন্ট</p><p className="text-slate-300">{PAYMENTS.find(p => p.id === order.payment_method)?.label}</p></div>
                      <div><p className="text-slate-500 mb-0.5">ডেলিভারি</p><p className="text-emerald-400">{order.estimated_delivery}</p></div>
                    </div>
                    <div className="bg-slate-900/40 rounded-xl p-3 flex flex-wrap gap-2">
                      {order.items.map((item, i) => (
                        <div key={i} className="flex items-center gap-1.5 bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5">
                          <span className="text-base">{item.emoji}</span>
                          <span className="text-xs text-slate-300">{item.name}</span>
                          <span className="text-[10px] text-slate-500">×{item.qty}</span>
                        </div>
                      ))}
                    </div>
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                      <p className="text-xs text-slate-500 flex items-center gap-1"><MapPin size={11}/> {order.address}</p>
                      <button onClick={() => trackInChat(order.order_id)}
                        className="flex items-center gap-1.5 px-3 py-2 bg-accentPurple/10 hover:bg-accentPurple/20 border border-accentPurple/30 text-accentPurple rounded-lg text-xs font-semibold transition">
                        <MessageCircle size={13}/> চ্যাটে ট্র্যাক করুন
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Cart drawer */}
      {cartOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setCartOpen(false)} />
          <div className="relative w-full max-w-sm bg-slate-900 border-l border-slate-800 flex flex-col h-full shadow-2xl">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
              <h3 className="font-bold text-white flex items-center gap-2">
                <ShoppingCart size={18} className="text-accentPurple" /> আমার কার্ট
                {cartCount > 0 && <span className="bg-accentPurple/20 text-accentPurple border border-accentPurple/30 rounded-full px-2 py-0.5 text-xs">{cartCount}</span>}
              </h3>
              <button onClick={() => setCartOpen(false)} className="text-slate-400 hover:text-white transition"><X size={20}/></button>
            </div>
            <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {cart.length === 0 ? (
                <div className="text-center py-16 text-slate-500"><p className="text-5xl mb-4">🛒</p><p>কার্ট খালি</p></div>
              ) : cart.map(item => (
                <div key={item.id} className="flex gap-3 bg-slate-800/50 border border-slate-700/50 rounded-xl p-3">
                  <div className="w-14 h-14 bg-slate-700/50 rounded-lg flex items-center justify-center text-2xl shrink-0">{item.emoji}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-white truncate">{item.name}</p>
                    <p className="text-xs text-slate-400 mb-2">৳{item.price.toLocaleString()}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <button onClick={() => changeQty(item.id,-1)} className="w-6 h-6 rounded-full bg-slate-700 hover:bg-slate-600 flex items-center justify-center transition"><Minus size={10}/></button>
                        <span className="text-sm font-bold text-white w-4 text-center">{item.qty}</span>
                        <button onClick={() => changeQty(item.id,1)}  className="w-6 h-6 rounded-full bg-slate-700 hover:bg-slate-600 flex items-center justify-center transition"><Plus size={10}/></button>
                      </div>
                      <button onClick={() => removeFromCart(item.id)} className="text-slate-500 hover:text-rose-400 transition"><Trash2 size={14}/></button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {cart.length > 0 && (
              <div className="p-5 border-t border-slate-800 space-y-2">
                <div className="flex justify-between text-sm text-slate-400"><span>সাবটোটাল</span><span className="text-white">৳{subtotalMain.toLocaleString()}</span></div>
                <div className="flex justify-between font-bold text-lg border-t border-slate-700 pt-3">
                  <span className="text-white">মোট</span><span className="text-white">৳{subtotalMain.toLocaleString()}</span>
                </div>
                <button onClick={() => { setCartOpen(false); setView('checkout') }}
                  className="w-full bg-accentPurple hover:bg-accentPurple/90 text-white py-3 rounded-xl font-bold text-sm transition mt-2">
                  চেকআউট করুন →
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <ChatWidget prefilledMessage={chatPreset} onPrefilledUsed={() => setChatPreset('')} />
    </div>
  )
}
